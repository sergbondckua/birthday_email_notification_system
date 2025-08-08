from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required

from app import db
from models import EmailLog

logs_bp = Blueprint("logs", __name__)


# --- Маршрут для відображення HTML-сторінки ---
@logs_bp.route("/", methods=["GET"])
@login_required
def logs_page():
    """Відобразити сторінку логів та статистики."""
    return render_template("logs.html")


# --- API Маршрути ---

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
                from_date = datetime.strptime(date_from_str, "%Y-%m-%d")
                query = query.filter(EmailLog.sent_date >= from_date)
            except ValueError:
                pass  # Ігноруємо невірний формат дати

        if date_to_str:
            try:
                to_date = datetime.strptime(date_to_str, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(EmailLog.sent_date < to_date)
            except ValueError:
                pass  # Ігноруємо невірний формат дати

        query = query.order_by(EmailLog.sent_date.desc())
        paginated_logs = query.paginate(page=page, per_page=per_page, error_out=False)

        logs_data = [
            {
                "id": log.id,
                "employee": {
                    "full_name": log.employee.full_name,
                    "email": log.employee.email,
                } if log.employee else None,
                "template": {"name": log.template.name} if log.template else None,
                "sent_date": log.sent_date.strftime("%d.%m.%Y %H:%M"),
                "recipients_count": log.recipients_count,
                "status": log.status,
                "error_message": log.error_message,
            }
            for log in paginated_logs.items
        ]

        return jsonify({
            "logs": logs_data,
            "total": paginated_logs.total,
            "pages": paginated_logs.pages,
            "current_page": page,
            "has_next": paginated_logs.has_next,
            "has_prev": paginated_logs.has_prev,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Помилка отримання логів: {str(e)}"}), 500


@logs_bp.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    """API: Отримати статистику розсилки."""
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)

        total_sent = EmailLog.query.filter(EmailLog.status == "sent").count()
        total_failed = EmailLog.query.filter(EmailLog.status == "failed").count()

        total_recipients = db.session.query(db.func.sum(EmailLog.recipients_count)).filter(
            EmailLog.status == "sent"
        ).scalar() or 0

        daily_stats = (
            db.session.query(
                db.func.date(EmailLog.sent_date).label("date"),
                db.func.count(EmailLog.id).label("count"),
            )
            .filter(EmailLog.sent_date >= thirty_days_ago, EmailLog.status == "sent")
            .group_by(db.func.date(EmailLog.sent_date))
            .order_by(db.func.date(EmailLog.sent_date))
            .all()
        )

        success_rate = (
            round((total_sent / (total_sent + total_failed) * 100), 2)
            if (total_sent + total_failed) > 0 else 100
        )

        return jsonify({
            "stats": {
                "total_sent": total_sent,
                "total_failed": total_failed,
                "total_recipients": int(total_recipients),
                "success_rate": success_rate,
            },
            "daily_stats": [
                {"date": stat.date.isoformat(), "emails_sent": stat.count}
                for stat in daily_stats
            ],
        }), 200

    except Exception as e:
        return jsonify({"error": f"Помилка отримання статистики: {str(e)}"}), 500
