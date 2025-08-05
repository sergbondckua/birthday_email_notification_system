from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app import create_app
from models import AdminRole

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/smtp", methods=["GET"])
@login_required
def get_smtp_settings():
    """Отримати поточні SMTP налаштування"""
    if not current_user.has_role(AdminRole.SUPER_ADMIN):
        return jsonify({"error": "Недостатньо прав"}), 403

    return (
        jsonify(
            {
                "smtp": {
                    "server": current_app.config.get("MAIL_SERVER", ""),
                    "port": current_app.config.get("MAIL_PORT", 587),
                    "use_tls": current_app.config.get("MAIL_USE_TLS", True),
                    "username": current_app.config.get("MAIL_USERNAME", ""),
                    "default_sender": current_app.config.get(
                        "MAIL_DEFAULT_SENDER", ""
                    ),
                }
            }
        ),
        200,
    )


@settings_bp.route("/smtp", methods=["POST"])
@login_required
def update_smtp_settings():
    """Оновити SMTP налаштування"""
    if not current_user.has_role(AdminRole.SUPER_ADMIN):
        return jsonify({"error": "Недостатньо прав"}), 403

    try:
        data = request.get_json()

        # Валідація
        required_fields = [
            "server",
            "port",
            "username",
            "password",
            "default_sender",
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Поле {field} обов'язкове"}), 400

        # Оновлення конфігурації (в реальному додатку це має зберігатися в БД або .env файлі)
        current_app.config["MAIL_SERVER"] = data["server"]
        current_app.config["MAIL_PORT"] = int(data["port"])
        current_app.config["MAIL_USE_TLS"] = data.get("use_tls", True)
        current_app.config["MAIL_USERNAME"] = data["username"]
        current_app.config["MAIL_PASSWORD"] = data["password"]
        current_app.config["MAIL_DEFAULT_SENDER"] = data["default_sender"]

        return jsonify({"message": "SMTP налаштування успішно оновлені"}), 200

    except Exception as e:
        return (
            jsonify({"error": f"Помилка оновлення налаштувань: {str(e)}"}),
            500,
        )


@settings_bp.route("/test-email", methods=["POST"])
@login_required
def test_email():
    """Тестова відправка email"""
    if not current_user.has_role(AdminRole.SUPER_ADMIN):
        return jsonify({"error": "Недостатньо прав"}), 403

    try:
        from flask_mail import Message
        from app import mail

        data = request.get_json()
        test_email = data.get("email")

        if not test_email:
            return jsonify({"error": "Email для тесту не вказаний"}), 400

        # Створення тестового повідомлення
        msg = Message(
            subject="Тестове повідомлення Birthday App",
            recipients=[test_email],
            body="Це тестове повідомлення для перевірки налаштувань SMTP.",
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
        )

        mail.send(msg)

        return (
            jsonify({"message": "Тестове повідомлення успішно відправлено"}),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "error": f"Помилка відправки тестового повідомлення: {str(e)}"
                }
            ),
            500,
        )


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
