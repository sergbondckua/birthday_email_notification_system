from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import EmailLog, Employee, EmailTemplate
from app import db
from datetime import datetime, timedelta

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/", methods=["GET"])
@login_required
def get_logs():
    """Отримати логи розсилки"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status", "").strip()
        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()

        query = EmailLog.query

        # Фільтрація за статусом
        if status:
            query = query.filter(EmailLog.status == status)

        # Фільтрація за датою
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(EmailLog.sent_date >= from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(
                    days=1
                )
                query = query.filter(EmailLog.sent_date < to_date)
            except ValueError:
                pass

        # Сортування за датою (новіші спочатку)
        query = query.order_by(EmailLog.sent_date.desc())

        # Пагінація
        logs = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "logs": [
                        {
                            "id": log.id,
                            "employee": (
                                {
                                    "id": log.employee.id,
                                    "full_name": log.employee.full_name,
                                    "email": log.employee.email,
                                }
                                if log.employee
                                else None
                            ),
                            "template": (
                                {
                                    "id": log.template.id,
                                    "name": log.template.name,
                                }
                                if log.template
                                else None
                            ),
                            "sent_date": log.sent_date.isoformat(),
                            "recipients_count": log.recipients_count,
                            "status": log.status,
                            "error_message": log.error_message,
                        }
                        for log in logs.items
                    ],
                    "total": logs.total,
                    "pages": logs.pages,
                    "current_page": page,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Помилка отримання логів: {str(e)}"}), 500


@logs_bp.route("/stats", methods=["GET"])
@login_required
def get_stats():
    """Отримати статистику розсилки"""
    try:
        # Статистика за останні 30 днів
        thirty_days_ago = datetime.now() - timedelta(days=30)

        total_sent = EmailLog.query.filter(
            EmailLog.sent_date >= thirty_days_ago, EmailLog.status == "sent"
        ).count()

        total_failed = EmailLog.query.filter(
            EmailLog.sent_date >= thirty_days_ago, EmailLog.status == "failed"
        ).count()

        total_recipients = (
            db.session.query(db.func.sum(EmailLog.recipients_count))
            .filter(
                EmailLog.sent_date >= thirty_days_ago,
                EmailLog.status == "sent",
            )
            .scalar()
            or 0
        )

        # Статистика по дням
        daily_stats = (
            db.session.query(
                db.func.date(EmailLog.sent_date).label("date"),
                db.func.count(EmailLog.id).label("count"),
                db.func.sum(EmailLog.recipients_count).label("recipients"),
            )
            .filter(
                EmailLog.sent_date >= thirty_days_ago,
                EmailLog.status == "sent",
            )
            .group_by(db.func.date(EmailLog.sent_date))
            .order_by("date")
            .all()
        )

        return (
            jsonify(
                {
                    "stats": {
                        "total_sent": total_sent,
                        "total_failed": total_failed,
                        "total_recipients": total_recipients,
                        "success_rate": (
                            round(
                                (
                                    total_sent
                                    / (total_sent + total_failed)
                                    * 100
                                ),
                                2,
                            )
                            if (total_sent + total_failed) > 0
                            else 0
                        ),
                    },
                    "daily_stats": [
                        {
                            "date": stat.date.isoformat(),
                            "emails_sent": stat.count,
                            "recipients": stat.recipients or 0,
                        }
                        for stat in daily_stats
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Помилка отримання статистики: {str(e)}"}),
            500,
        )
