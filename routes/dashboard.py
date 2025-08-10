from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from services.birthday_service import BirthdayService
from models import Employee, EmailTemplate, EmailLog
from datetime import date

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
@login_required
def dashboard():
    """Головна сторінка з оглядом"""
    try:
        # Отримуємо всі необхідні дані
        upcoming_birthdays = BirthdayService.get_upcoming_birthdays(
            days_ahead=14
        )
        today_birthdays = BirthdayService.get_birthday_employees(date.today())
        current_month_birthdays = BirthdayService.get_birthdays_for_month(
            date.today().year, date.today().month)

        # Збираємо статистику
        stats = {
            "total_employees": Employee.query.count(),
            "active_templates": EmailTemplate.query.filter_by(
                is_active=True
            ).count(),
            "total_templates": EmailTemplate.query.count(),
            "monthly_emails": EmailLog.query.filter(
                EmailLog.sent_date >= date.today().replace(day=1),
                EmailLog.status == "sent",
            ).count(),
            "today_birthdays_count": len(today_birthdays),
            "monthly_birthdays_count": len(current_month_birthdays),
        }

        # Рендеримо HTML-шаблон, передаючи в нього дані
        return render_template(
            "dashboard.html",
            stats=stats,
            upcoming_birthdays=upcoming_birthdays,
            today_birthdays=today_birthdays,
        )

    except Exception as e:
        # У разі помилки можна показати сторінку з помилкою
        return render_template("error.html", error_message=str(e)), 500


@dashboard_bp.route("/calendar/<int:year>/<int:month>", methods=["GET"])
@login_required
def calendar_data(year, month):
    """Дані календаря для конкретного місяця (API Endpoint)"""
    try:
        birthdays = BirthdayService.get_birthdays_for_month(year, month)

        # Форматуємо дані для JSON
        birthdays_data = [
            {
                "day": item["day"],
                "employee_name": item["employee"].full_name,
            }
            for item in birthdays
        ]
        return (
            jsonify(
                {"year": year, "month": month, "birthdays": birthdays_data}
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Помилка завантаження календаря: {str(e)}"}),
            500,
        )
