from flask import Blueprint, jsonify
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
        # Найближчі дні народження
        upcoming_birthdays = BirthdayService.get_upcoming_birthdays(14)

        # Загальна статистика
        total_employees = Employee.query.count()
        active_templates = EmailTemplate.query.filter_by(
            is_active=True
        ).count()

        # Статистика розсилки за поточний місяць
        current_month_start = date.today().replace(day=1)
        monthly_emails = EmailLog.query.filter(
            EmailLog.sent_date >= current_month_start,
            EmailLog.status == "sent",
        ).count()

        # Дні народження сьогодні
        today = date.today()
        today_birthdays = BirthdayService.get_birthday_employees(today)

        return (
            jsonify(
                {
                    "dashboard": {
                        "stats": {
                            "total_employees": total_employees,
                            "active_templates": active_templates,
                            "monthly_emails": monthly_emails,
                            "today_birthdays": len(today_birthdays),
                        },
                        "upcoming_birthdays": [
                            {
                                "employee": {
                                    "id": item["employee"].id,
                                    "full_name": item["employee"].full_name,
                                    "email": item["employee"].email,
                                },
                                "birthday_date": item[
                                    "birthday_date"
                                ].isoformat(),
                                "days_until": item["days_until"],
                            }
                            for item in upcoming_birthdays
                        ],
                        "today_birthdays": [
                            {
                                "id": emp.id,
                                "full_name": emp.full_name,
                                "email": emp.email,
                                "birth_date": emp.birth_date.isoformat(),
                            }
                            for emp in today_birthdays
                        ],
                    }
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Помилка завантаження дашборду: {str(e)}"}),
            500,
        )


@dashboard_bp.route("/calendar/<int:year>/<int:month>", methods=["GET"])
@login_required
def calendar_data(year, month):
    """Дані календаря для конкретного місяця"""
    try:
        birthday_service = BirthdayService()
        # Дні народження цього місяця
        birthdays = birthday_service.get_birthdays_for_month(year, month)

        # Дні повідомлень
        notifications = birthday_service.get_notification_calendar(year, month)

        return (
            jsonify(
                {
                    "calendar": {
                        "year": year,
                        "month": month,
                        "birthdays": [
                            {
                                "employee": {
                                    "id": item["employee"].id,
                                    "full_name": item["employee"].full_name,
                                    "email": item["employee"].email,
                                },
                                "date": item["date"].isoformat(),
                                "day": item["day"],
                            }
                            for item in birthdays
                        ],
                        "notifications": {
                            str(day): [
                                {
                                    "employee": {
                                        "id": item["employee"].id,
                                        "full_name": item[
                                            "employee"
                                        ].full_name,
                                    },
                                    "birthday_date": item[
                                        "birthday_date"
                                    ].isoformat(),
                                }
                                for item in items
                            ]
                            for day, items in notifications.items()
                        },
                    }
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Помилка завантаження календаря: {str(e)}"}),
            500,
        )
