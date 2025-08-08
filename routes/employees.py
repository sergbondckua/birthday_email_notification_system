from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import Employee
from app import db
from utils.validators import Validators
import csv
import io

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("/", methods=["GET"])
@login_required
def employees_page():
    """Відобразити сторінку співробітників"""
    # Якщо це AJAX запит, повертаємо JSON
    if request.headers.get("Content-Type") == "application/json":
        return get_employees_api()

    # Інакше відображаємо HTML сторінку
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get(
            "per_page", 12, type=int
        )  # 12 для красивої сітки 4x3
        search = request.args.get("search", "").strip()

        query = Employee.query

        if search:
            query = query.filter(
                db.or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.email.ilike(f"%{search}%"),
                )
            )

        employees = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return render_template("employees.html", employees=employees)

    except Exception as e:
        # У випадку помилки показуємо порожню сторінку
        return render_template(
            "employees.html", employees=None, error=f"Помилка: {str(e)}"
        )


@employees_bp.route("/api", methods=["GET"])
@login_required
def get_employees_api():
    """API endpoint для отримання списку співробітників"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "").strip()

        query = Employee.query

        if search:
            query = query.filter(
                db.or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.email.ilike(f"%{search}%"),
                )
            )

        employees = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return (
            jsonify(
                {
                    "employees": [
                        {
                            "id": emp.id,
                            "first_name": emp.first_name,
                            "last_name": emp.last_name,
                            "full_name": emp.full_name,
                            "email": emp.email,
                            "birth_date": emp.birth_date.isoformat(),
                            "created_at": emp.created_at.isoformat(),
                        }
                        for emp in employees.items
                    ],
                    "total": employees.total,
                    "pages": employees.pages,
                    "current_page": page,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Помилка отримання співробітників: {str(e)}"}),
            500,
        )


@employees_bp.route("/", methods=["POST"])
@login_required
def create_employee():
    """Створити нового співробітника"""
    try:
        data = request.get_json()
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        email = data.get("email", "").strip().lower()
        birth_date = data.get("birth_date", "").strip()

        # Валідація
        errors = Validators.validate_employee_data(
            first_name, last_name, email, birth_date
        )
        if errors:
            return jsonify({"errors": errors}), 400

        # Перевірка унікальності email
        if Employee.query.filter_by(email=email).first():
            return (
                jsonify({"error": "Співробітник з таким email вже існує"}),
                409,
            )

        # Парсинг дати
        is_valid, parsed_date = Validators.validate_birth_date(birth_date)
        if not is_valid:
            return jsonify({"error": "Некоректна дата народження"}), 400

        # Створення співробітника
        employee = Employee(
            first_name=first_name,
            last_name=last_name,
            email=email,
            birth_date=parsed_date,
        )

        db.session.add(employee)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Співробітник успішно створений",
                    "employee": {
                        "id": employee.id,
                        "first_name": employee.first_name,
                        "last_name": employee.last_name,
                        "full_name": employee.full_name,
                        "email": employee.email,
                        "birth_date": employee.birth_date.isoformat(),
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": f"Помилка створення співробітника: {str(e)}"}),
            500,
        )


@employees_bp.route("/<int:employee_id>", methods=["PUT"])
@login_required
def update_employee(employee_id):
    """Оновити дані співробітника"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        data = request.get_json()

        first_name = data.get("first_name", employee.first_name).strip()
        last_name = data.get("last_name", employee.last_name).strip()
        email = data.get("email", employee.email).strip().lower()
        birth_date = data.get(
            "birth_date", employee.birth_date.strftime("%d.%m.%Y")
        ).strip()

        # Валідація
        errors = Validators.validate_employee_data(
            first_name, last_name, email, birth_date
        )
        if errors:
            return jsonify({"errors": errors}), 400

        # Перевірка унікальності email (крім поточного)
        existing_employee = Employee.query.filter_by(email=email).first()
        if existing_employee and existing_employee.id != employee_id:
            return (
                jsonify({"error": "Співробітник з таким email вже існує"}),
                409,
            )

        # Парсинг дати
        is_valid, parsed_date = Validators.validate_birth_date(birth_date)
        if not is_valid:
            return jsonify({"error": "Некоректна дата народження"}), 400

        # Оновлення даних
        employee.first_name = first_name
        employee.last_name = last_name
        employee.email = email
        employee.birth_date = parsed_date

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Дані співробітника успішно оновлено",
                    "employee": {
                        "id": employee.id,
                        "first_name": employee.first_name,
                        "last_name": employee.last_name,
                        "full_name": employee.full_name,
                        "email": employee.email,
                        "birth_date": employee.birth_date.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": f"Помилка оновлення співробітника: {str(e)}"}),
            500,
        )


@employees_bp.route("/<int:employee_id>", methods=["DELETE"])
@login_required
def delete_employee(employee_id):
    """Видалити співробітника"""
    try:
        employee = Employee.query.get_or_404(employee_id)

        db.session.delete(employee)
        db.session.commit()

        return jsonify({"message": "Співробітник успішно видалений"}), 200

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": f"Помилка видалення співробітника: {str(e)}"}),
            500,
        )


@employees_bp.route("/import", methods=["POST"])
@login_required
def import_employees():
    """Імпорт співробітників з CSV/Excel"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "Файл не надано"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Файл не вибрано"}), 400

        # Перевірка розширення файлу
        filename = file.filename.lower()
        if not (
            filename.endswith(".csv")
            or filename.endswith(".xlsx")
            or filename.endswith(".xls")
        ):
            return (
                jsonify({"error": "Підтримуються тільки CSV та Excel файли"}),
                400,
            )

        created_count = 0
        errors = []

        try:
            # Читання файлу в залежності від типу
            if filename.endswith(".csv"):
                # Читання CSV з правильним кодуванням
                content = file.stream.read()

                # Спроба визначити кодування
                try:
                    decoded_content = content.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        decoded_content = content.decode(
                            "cp1251"
                        )  # Windows кодування
                    except UnicodeDecodeError:
                        decoded_content = content.decode(
                            "utf-8", errors="replace"
                        )

                stream = io.StringIO(decoded_content)

                # Спроба визначити роздільник
                sample = decoded_content[:1024]
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except:
                    delimiter = ","

                csv_input = csv.DictReader(stream, delimiter=delimiter)

            else:  # Excel файли
                import pandas as pd

                df = pd.read_excel(file.stream)
                csv_input = df.to_dict("records")

        except Exception as e:
            return jsonify({"error": f"Помилка читання файлу: {str(e)}"}), 400

        # Валідація заголовків
        required_columns = ["first_name", "last_name", "email", "birth_date"]

        if filename.endswith(".csv"):
            # Для CSV перевіряємо fieldnames
            if not csv_input.fieldnames:
                return (
                    jsonify({"error": "Файл порожній або не має заголовків"}),
                    400,
                )

            actual_columns = [
                col.strip().lower() for col in csv_input.fieldnames if col
            ]

            missing_columns = [
                col for col in required_columns if col not in actual_columns
            ]

            if missing_columns:
                return (
                    jsonify(
                        {
                            "error": f"Відсутні обов'язкові колонки: {', '.join(missing_columns)}"
                        }
                    ),
                    400,
                )
        else:
            # Для Excel перевіряємо перший рядок
            if not csv_input:
                return jsonify({"error": "Файл порожній"}), 400

            actual_columns = [
                col.strip().lower() for col in csv_input[0].keys() if col
            ]
            missing_columns = [
                col for col in required_columns if col not in actual_columns
            ]

            if missing_columns:
                return (
                    jsonify(
                        {
                            "error": f"Відсутні обов'язкові колонки: {', '.join(missing_columns)}"
                        }
                    ),
                    400,
                )

        # Обробка рядків
        employees_to_add = []
        existing_emails = set()

        # Отримуємо всі існуючі emails одним запитом для оптимізації
        all_existing_emails = {
            emp.email for emp in db.session.query(Employee.email).all()
        }

        for row_num, row in enumerate(csv_input, start=2):
            try:
                # Нормалізація ключів для випадку з різними регістрами
                normalized_row = {
                    k.strip().lower(): v
                    for k, v in row.items()
                    if k is not None
                }

                first_name = str(normalized_row.get("first_name", "")).strip()
                last_name = str(normalized_row.get("last_name", "")).strip()
                email = str(normalized_row.get("email", "")).strip().lower()
                birth_date = str(normalized_row.get("birth_date", "")).strip()

                # Пропуск порожніх рядків
                if not any([first_name, last_name, email, birth_date]):
                    continue

                # Валідація рядка
                row_errors = Validators.validate_employee_data(
                    first_name, last_name, email, birth_date
                )
                if row_errors:
                    errors.append(f"Рядок {row_num}: {', '.join(row_errors)}")
                    continue

                # Перевірка унікальності (включаючи поточний batch)
                if email in all_existing_emails or email in existing_emails:
                    errors.append(f"Рядок {row_num}: Email {email} вже існує")
                    continue

                # Парсинг дати
                is_valid, parsed_date = Validators.validate_birth_date(
                    birth_date
                )
                if not is_valid:
                    errors.append(
                        f"Рядок {row_num}: Некоректна дата народження"
                    )
                    continue

                # Додаємо до списку для batch insert
                employees_to_add.append(
                    Employee(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        birth_date=parsed_date,
                    )
                )

                existing_emails.add(email)
                created_count += 1

            except Exception as e:
                errors.append(f"Рядок {row_num}: Помилка обробки - {str(e)}")

        # Batch insert для кращої продуктивності
        if employees_to_add:
            try:
                db.session.bulk_save_objects(employees_to_add)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return (
                    jsonify(
                        {"error": f"Помилка збереження в базу даних: {str(e)}"}
                    ),
                    500,
                )

        # Підготовка результату
        result = {
            "message": f"Імпорт завершено. Створено: {created_count} співробітників",
            "created_count": created_count,
            "total_errors": len(errors),
        }

        # Обмежуємо кількість помилок у відповіді
        if errors:
            result["errors"] = errors[:50]  # Показуємо тільки перші 50 помилок
            if len(errors) > 50:
                result[
                    "message"
                ] += f" (показано перші 50 з {len(errors)} помилок)"

        status_code = 200 if created_count > 0 else 400
        return jsonify(result), status_code

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Загальна помилка імпорту: {str(e)}"}), 500
