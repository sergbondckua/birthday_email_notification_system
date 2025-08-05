from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import EmailTemplate, Employee
from app import db
from services.email_service import EmailService

templates_bp = Blueprint("templates", __name__)


@templates_bp.route("/", methods=["GET"])
@login_required
def get_templates():
    """Отримати всі шаблони"""
    try:
        templates = EmailTemplate.query.order_by(
            EmailTemplate.created_at.desc()
        ).all()

        return (
            jsonify(
                {
                    "templates": [
                        {
                            "id": template.id,
                            "name": template.name,
                            "subject": template.subject,
                            "template_text": template.template_text,
                            "is_active": template.is_active,
                            "created_at": template.created_at.isoformat(),
                        }
                        for template in templates
                    ]
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Помилка отримання шаблонів: {str(e)}"}), 500


@templates_bp.route("/", methods=["POST"])
@login_required
def create_template():
    """Створити новий шаблон"""
    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        subject = data.get("subject", "").strip()
        template_text = data.get("template_text", "").strip()
        is_active = data.get("is_active", False)

        # Валідація
        if not name or not subject or not template_text:
            return jsonify({"error": "Всі поля обов'язкові"}), 400

        if len(name) < 3:
            return (
                jsonify({"error": "Назва повинна містити мінімум 3 символи"}),
                400,
            )

        # Якщо новий шаблон активний, деактивуємо інші
        if is_active:
            EmailTemplate.query.update({"is_active": False})

        # Створення шаблону
        template = EmailTemplate(
            name=name,
            subject=subject,
            template_text=template_text,
            is_active=is_active,
        )

        db.session.add(template)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Шаблон успішно створений",
                    "template": {
                        "id": template.id,
                        "name": template.name,
                        "subject": template.subject,
                        "template_text": template.template_text,
                        "is_active": template.is_active,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Помилка створення шаблону: {str(e)}"}), 500


@templates_bp.route("/<int:template_id>", methods=["PUT"])
@login_required
def update_template(template_id):
    """Оновити шаблон"""
    try:
        template = EmailTemplate.query.get_or_404(template_id)
        data = request.get_json()

        name = data.get("name", template.name).strip()
        subject = data.get("subject", template.subject).strip()
        template_text = data.get(
            "template_text", template.template_text
        ).strip()
        is_active = data.get("is_active", template.is_active)

        # Валідація
        if not name or not subject or not template_text:
            return jsonify({"error": "Всі поля обов'язкові"}), 400

        # Якщо шаблон стає активним, деактивуємо інші
        if is_active and not template.is_active:
            EmailTemplate.query.filter(EmailTemplate.id != template_id).update(
                {"is_active": False}
            )

        # Оновлення
        template.name = name
        template.subject = subject
        template.template_text = template_text
        template.is_active = is_active

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Шаблон успішно оновлений",
                    "template": {
                        "id": template.id,
                        "name": template.name,
                        "subject": template.subject,
                        "template_text": template.template_text,
                        "is_active": template.is_active,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Помилка оновлення шаблону: {str(e)}"}), 500


@templates_bp.route("/<int:template_id>", methods=["DELETE"])
@login_required
def delete_template(template_id):
    """Видалити шаблон"""
    try:
        template = EmailTemplate.query.get_or_404(template_id)

        if template.is_active:
            return (
                jsonify({"error": "Неможливо видалити активний шаблон"}),
                400,
            )

        db.session.delete(template)
        db.session.commit()

        return jsonify({"message": "Шаблон успішно видалений"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Помилка видалення шаблону: {str(e)}"}), 500


@templates_bp.route("/<int:template_id>/preview", methods=["POST"])
@login_required
def preview_template(template_id):
    """Попередній перегляд шаблону"""
    try:
        template = EmailTemplate.query.get_or_404(template_id)
        data = request.get_json()
        employee_id = data.get("employee_id")

        if not employee_id:
            # Використовуємо першого співробітника для прикладу
            employee = Employee.query.first()
            if not employee:
                return (
                    jsonify(
                        {
                            "error": "Немає співробітників для попереднього перегляду"
                        }
                    ),
                    400,
                )
        else:
            employee = Employee.query.get_or_404(employee_id)

        # Форматування шаблону
        formatted_subject = EmailService.format_template(
            template.subject, employee
        )
        formatted_text = EmailService.format_template(
            template.template_text, employee
        )

        return (
            jsonify(
                {
                    "preview": {
                        "subject": formatted_subject,
                        "body": formatted_text,
                        "employee_used": {
                            "id": employee.id,
                            "full_name": employee.full_name,
                            "birth_date": employee.birth_date.strftime(
                                "%d.%m.%Y"
                            ),
                        },
                    }
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Помилка попереднього перегляду: {str(e)}"}),
            500,
        )


@templates_bp.route("/<int:template_id>/activate", methods=["POST"])
@login_required
def activate_template(template_id):
    """Активувати шаблон"""
    try:
        template = EmailTemplate.query.get_or_404(template_id)

        # Деактивуємо всі інші шаблони
        EmailTemplate.query.update({"is_active": False})

        # Активуємо поточний
        template.is_active = True
        db.session.commit()

        return jsonify({"message": "Шаблон успішно активований"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Помилка активації шаблону: {str(e)}"}), 500
