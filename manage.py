"""Flask CLI management script."""

from datetime import datetime

import click
from flask.cli import with_appcontext
from app import create_app, db
from models import Admin, AdminRole, Employee


def create_manage_app():
    """Create Flask app for CLI commands."""
    return create_app()


app = create_manage_app()


@app.cli.command()
@with_appcontext
def init_db():
    """Initialize the database."""
    click.echo("Ініціалізація бази даних ...")
    db.create_all()
    click.echo("База даних успішно ініціалізована!")


@app.cli.command()
@with_appcontext
def drop_db():
    """Drop all database tables."""
    if click.confirm(
        "Ви впевнені, що хочете видалити всі таблиці бази даних?"
    ):
        db.drop_all()
        click.echo("Таблиці баз даних видалено!")


@app.cli.command()
@with_appcontext
def reset_db():
    """Reset database (drop and recreate)."""
    if click.confirm("Ви впевнені, що хочете скинути базу даних?"):
        click.echo("Видалення таблиць...")
        db.drop_all()
        click.echo("Створення таблиць...")
        db.create_all()
        click.echo("База даних успішно скинута!")


@app.cli.command("createsuperuser")
@with_appcontext
def create_superuser():
    """Створити першого супер-адміністратора"""
    username = input("Введіть ім'я користувача: ")
    password = input("Введіть пароль: ")

    admin = Admin(username=username, role=AdminRole.SUPER_ADMIN)
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    print(f"Адміністратор {username} успішно створений!")


@app.cli.command()
@with_appcontext
@click.option("--first-name", prompt="Ім'я", help="Ім'я співробітника")
@click.option("--last-name", prompt="Прізвище", help="Прізвище співробітника")
@click.option("--email", prompt="Email", help="Електронна пошта співробітника")
@click.option(
    "--birth-date",
    prompt="Дата народження (YYYY-MM-DD)",
    help="Дата народження у форматі YYYY-MM-DD",
)
def add_employee(first_name, last_name, email, birth_date):
    """Додати нового співробітника"""

    # Валідація дати народження
    try:
        birth_date_parsed = datetime.strptime(birth_date, "%Y-%m-%d").date()
    except ValueError:
        click.echo(
            "❌ Невірний формат дати! Використовуйте формат YYYY-MM-DD."
        )
        return

    employee = Employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
        birth_date=birth_date_parsed,
    )

    db.session.add(employee)
    db.session.commit()
    print(f"Співробітник {employee.full_name} успішно доданий!")
