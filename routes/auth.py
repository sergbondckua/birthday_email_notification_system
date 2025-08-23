import pytz
from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from models import Admin, AdminRole
from app import db
from utils.validators import Validators
import re

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def login_page():
    """Відобразити сторінку входу"""
    # Якщо користувач вже авторизований, перенаправити на дашборд
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


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
            login_user(admin, remember=True)
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


@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile_page():
    """Відобразити сторінку профілю"""
    return render_template("profile.html")


@auth_bp.route("/api/profile", methods=["GET"])
@login_required
def profile_api():
    """API endpoint для отримання інформації про поточного користувача"""
    local_tz = pytz.timezone(current_app.config["TIMEZONE"])
    return (
        jsonify(
            {
                "user": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "role": current_user.role.value,
                    "created_at": local_tz.localize(
                        current_user.created_at
                    ).isoformat(),
                }
            }
        ),
        200,
    )


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Змінити пароль користувача"""
    try:
        data = request.get_json()
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")

        if not current_password or not new_password:
            return jsonify({"error": "Всі поля обов'язкові"}), 400

        # Перевірити поточний пароль
        if not current_user.check_password(current_password):
            return jsonify({"error": "Невірний поточний пароль"}), 401

        # Валідація нового пароля
        if len(new_password) < 6:
            return (
                jsonify(
                    {
                        "error": "Новий пароль повинен містити мінімум 6 символів"
                    }
                ),
                400,
            )

        # Змінити пароль
        current_user.set_password(new_password)
        db.session.commit()

        return jsonify({"message": "Пароль успішно змінено"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Помилка зміни пароля: {str(e)}"}), 500


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

        # Валідація імені користувача (тільки букви, цифри, підкреслення)
        if not re.match("^[a-zA-Z0-9_]+$", username):
            return (
                jsonify(
                    {
                        "error": "Ім'я користувача може містити тільки букви, цифри та підкреслення"
                    }
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
def logout_api():
    """API вихід з системи"""
    logout_user()
    return jsonify({"message": "Успішний вихід"}), 200


@auth_bp.route("/logout", methods=["GET"])
@login_required
def logout_page():
    """Вихід з системи через GET запит (для форм)"""
    logout_user()
    flash("Ви успішно вийшли з системи", "success")
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/users", methods=["GET"])
@login_required
def list_users():
    """Отримати список всіх користувачів (тільки для super_admin)"""
    try:
        if not current_user.has_role(AdminRole.SUPER_ADMIN):
            return jsonify({"error": "Недостатньо прав"}), 403

        users = Admin.query.all()

        return (
            jsonify(
                {
                    "users": [
                        {
                            "id": user.id,
                            "username": user.username,
                            "role": user.role.value,
                            "created_at": user.created_at.isoformat(),
                            "is_current": user.id == current_user.id,
                        }
                        for user in users
                    ]
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Помилка отримання користувачів: {str(e)}"}),
            500,
        )


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    """Видалити користувача (тільки для super_admin)"""
    try:
        if not current_user.has_role(AdminRole.SUPER_ADMIN):
            return jsonify({"error": "Недостатньо прав"}), 403

        # Не можна видалити самого себе
        if user_id == current_user.id:
            return jsonify({"error": "Не можна видалити власний акаунт"}), 400

        user = Admin.query.get_or_404(user_id)

        # Переконатися, що залишається хоча б один super_admin
        if user.role == AdminRole.SUPER_ADMIN:
            super_admin_count = Admin.query.filter_by(
                role=AdminRole.SUPER_ADMIN
            ).count()
            if super_admin_count <= 1:
                return (
                    jsonify(
                        {
                            "error": "Не можна видалити останнього супер адміністратора"
                        }
                    ),
                    400,
                )

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "Користувача успішно видалено"}), 200

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": f"Помилка видалення користувача: {str(e)}"}),
            500,
        )


# Middleware для перевірки авторизації
@auth_bp.before_app_request
def load_logged_in_user():
    """Завантажити поточного користувача перед кожним запитом"""
    # Цей код буде виконуватися автоматично Flask-Login
    pass


# Обробник для неавторизованих користувачів
@auth_bp.app_errorhandler(401)
def unauthorized(error):
    """Перенаправити неавторизованих користувачів на сторінку входу"""
    if request.is_json:
        return jsonify({"error": "Необхідна авторизація"}), 401
    return redirect(url_for("auth.login_page"))
