from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models import Admin, AdminRole
from app import db
from utils.validators import Validators
import re

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Авторизація адміністратора"""
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "Всі поля обов'язкові"}), 400

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            return (
                jsonify(
                    {
                        "message": "Успішна авторизація",
                        "user": {
                            "id": admin.id,
                            "username": admin.username,
                            "role": admin.role.value,
                        },
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Невірні дані для входу"}), 401

    except Exception as e:
        return jsonify({"error": f"Помилка авторизації: {str(e)}"}), 500


@auth_bp.route("/register", methods=["POST"])
@login_required
def register():
    """Реєстрація нового адміністратора (тільки для super_admin)"""
    try:
        if not current_user.has_role(AdminRole.SUPER_ADMIN):
            return jsonify({"error": "Недостатньо прав"}), 403

        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        role = data.get("role", "admin")

        # Валідація
        if not username or not password:
            return jsonify({"error": "Всі поля обов'язкові"}), 400

        if len(username) < 3:
            return (
                jsonify(
                    {
                        "error": "Ім'я користувача повинно містити мінімум 3 символи"
                    }
                ),
                400,
            )

        if len(password) < 6:
            return (
                jsonify(
                    {"error": "Пароль повинен містити мінімум 6 символів"}
                ),
                400,
            )

        # Перевірка унікальності
        if Admin.query.filter_by(username=username).first():
            return (
                jsonify({"error": "Користувач з таким ім'ям вже існує"}),
                409,
            )

        # Створення адміністратора
        admin_role = (
            AdminRole.SUPER_ADMIN if role == "super_admin" else AdminRole.ADMIN
        )
        admin = Admin(username=username, role=admin_role)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Адміністратор успішно створений",
                    "admin": {
                        "id": admin.id,
                        "username": admin.username,
                        "role": admin.role.value,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Помилка реєстрації: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Вихід з системи"""
    logout_user()
    return jsonify({"message": "Успішний вихід"}), 200


@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """Отримати інформацію про поточного користувача"""
    return (
        jsonify(
            {
                "user": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "role": current_user.role.value,
                    "created_at": current_user.created_at.isoformat(),
                }
            }
        ),
        200,
    )
