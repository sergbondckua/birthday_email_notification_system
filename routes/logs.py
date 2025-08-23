from datetime import datetime, timedelta
import pytz
from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required

from app import db
from models import EmailLog

logs_bp = Blueprint("logs", __name__)


def convert_to_local_time(utc_datetime):
    """Конвертує UTC час в локальний часовий пояс згідно з налаштуваннями додатку."""
    local_tz = pytz.timezone(current_app.config["TIMEZONE"])

    if utc_datetime.tzinfo is None:
        # Якщо дата без часового поясу, припускаємо що це UTC
        utc_datetime = pytz.utc.localize(utc_datetime)
    elif utc_datetime.tzinfo != pytz.utc:
        # Конвертуємо в UTC спочатку
        utc_datetime = utc_datetime.astimezone(pytz.utc)

    # Конвертуємо в локальний час
    return utc_datetime.astimezone(local_tz)


@logs_bp.route("/", methods=["GET"])
@login_required
def logs_page():
    """Відобразити сторінку логів та статистики."""
    return render_template("logs.html")


@logs_bp.route("/api/logs", methods=["GET"])
@login_required
def get_logs():
    """API: Отримати логи розсилки з фільтрацією та пагінацією."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 15, type=int)
        status = request.args.get("status", "").strip()
        date_from_str = request.args.get("date_from", "").strip()
        date_to_str = request.args.get("date_to", "").strip()

        query = EmailLog.query

        if status:
            query = query.filter(EmailLog.status == status)

        if date_from_str:
            try:
                # Парсимо дату як локальну і конвертуємо в UTC для запиту
                local_tz = pytz.timezone(current_app.config["TIMEZONE"])
                from_date = datetime.strptime(date_from_str, "%Y-%m-%d")
                from_date_local = local_tz.localize(from_date)
                from_date_utc = from_date_local.astimezone(pytz.utc)
                query = query.filter(EmailLog.sent_date >= from_date_utc)
            except ValueError:
                pass

        if date_to_str:
            try:
                local_tz = pytz.timezone(current_app.config["TIMEZONE"])
                to_date = datetime.strptime(
                    date_to_str, "%Y-%m-%d"
                ) + timedelta(days=1)
                to_date_local = local_tz.localize(to_date)
                to_date_utc = to_date_local.astimezone(pytz.utc)
                query = query.filter(EmailLog.sent_date < to_date_utc)
            except ValueError:
                pass

        query = query.order_by(EmailLog.sent_date.desc())
        paginated_logs = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        logs_data = [
            {
                "id": log.id,
                "employee": (
                    {
                        "full_name": log.employee.full_name,
                        "email": log.employee.email,
                    }
                    if log.employee
                    else None
                ),
                "template": (
                    {"name": log.template.name} if log.template else None
                ),
                # Конвертуємо час в локальний часовий пояс
                "sent_date": convert_to_local_time(log.sent_date).strftime(
                    "%d.%m.%Y %H:%M"
                ),
                "recipients_count": log.recipients_count,
                "status": log.status,
                "error_message": log.error_message,
            }
            for log in paginated_logs.items
        ]

        return (
            jsonify(
                {
                    "logs": logs_data,
                    "total": paginated_logs.total,
                    "pages": paginated_logs.pages,
                    "current_page": page,
                    "has_next": paginated_logs.has_next,
                    "has_prev": paginated_logs.has_prev,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Помилка отримання логів: {str(e)}"}), 500


@logs_bp.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    """API: Отримати статистику розсилки."""
    try:
        # Отримуємо дату 30 днів в тому локальному часовому поясі
        local_tz = pytz.timezone(current_app.config["TIMEZONE"])
        thirty_days_ago = datetime.now(local_tz) - timedelta(days=30)
        thirty_days_ago_utc = thirty_days_ago.astimezone(pytz.utc)

        total_sent = EmailLog.query.filter(EmailLog.status == "sent").count()
        total_failed = EmailLog.query.filter(
            EmailLog.status == "failed"
        ).count()

        total_recipients = (
            db.session.query(db.func.sum(EmailLog.recipients_count))
            .filter(EmailLog.status == "sent")
            .scalar()
            or 0
        )

        # Для статистики по днях конвертуємо час в локальний часовий пояс
        daily_stats_raw = (
            db.session.query(
                EmailLog.sent_date,
                db.func.count(EmailLog.id).label("count"),
            )
            .filter(
                EmailLog.sent_date >= thirty_days_ago_utc,
                EmailLog.status == "sent",
            )
            .order_by(EmailLog.sent_date)
            .all()
        )

        # Групуємо по датах в локальному часовому поясі
        daily_stats_dict = {}
        for stat in daily_stats_raw:
            local_date = convert_to_local_time(stat.sent_date).date()
            if local_date in daily_stats_dict:
                daily_stats_dict[local_date] += stat.count
            else:
                daily_stats_dict[local_date] = stat.count

        daily_stats = [
            {"date": date.strftime("%Y-%m-%d"), "emails_sent": count}
            for date, count in sorted(daily_stats_dict.items())
        ]

        success_rate = (
            round((total_sent / (total_sent + total_failed) * 100), 2)
            if (total_sent + total_failed) > 0
            else 100
        )

        return (
            jsonify(
                {
                    "stats": {
                        "total_sent": total_sent,
                        "total_failed": total_failed,
                        "total_recipients": int(total_recipients),
                        "success_rate": success_rate,
                    },
                    "daily_stats": daily_stats,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Помилка отримання статистики: {str(e)}"}),
            500,
        )
