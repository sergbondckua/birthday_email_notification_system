from datetime import date
from typing import List

from app import db
from services.email_service import EmailService
from models import Employee


class BirthdayService:
    """Сервіс для роботи з днем народження"""

    def __init__(self):
        self.email_service = EmailService()

    @staticmethod
    def get_upcoming_birthdays(days_ahead: int = 7) -> List[Employee]:
        """Отримати найближчі дні народження"""
        today = date.today()
        upcoming = []

        for employee in Employee.query.all():
            # Створюємо дату ДН для поточного року
            try:
                birthday_this_year = employee.birth_date.replace(
                    year=today.year
                )
            except ValueError:  # 29 лютого
                birthday_this_year = employee.birth_date.replace(
                    year=today.year, day=28
                )

            # Якщо ДН вже був цього року, беремо наступний рік
            if birthday_this_year < today:
                try:
                    birthday_this_year = employee.birth_date.replace(
                        year=today.year + 1
                    )
                except ValueError:
                    birthday_this_year = employee.birth_date.replace(
                        year=today.year + 1, day=28
                    )

            # Розраховуємо кількість днів до ДН
            days_until = (birthday_this_year - today).days

            # Якщо кількість днів до ДН менша або дорівнює days_ahead додаємо співробітника
            if 0 <= days_until <= days_ahead:
                upcoming.append(
                    {
                        "employee": employee,
                        "birthday_date": birthday_this_year,
                        "days_until": days_until,
                    }
                )

        return sorted(
            upcoming, key=lambda x: x["days_until"]
        )  # Сортуємо за кількістю днів

    @staticmethod
    def get_birthdays_for_month(year: int, month: int) -> List[Employee]:
        """Отримати всі ДН для конкретного місяця"""

        # Отримати всіх співробітників
        employees = Employee.query.filter(
            db.extract("month", Employee.birth_date) == month
        ).all()

        birthdays = []
        for employee in employees:
            try:
                birthday_date = employee.birth_date.replace(year=year)
            except ValueError:
                birthday_date = employee.birth_date.replace(year=year, day=28)

            birthdays.append(
                {
                    "employee": employee,
                    "date": birthday_date,
                    "day": birthday_date.day,
                }
            )

        return sorted(birthdays, key=lambda x: x["day"])

    def get_notification_calendar(self, year: int, month: int) -> dict:
        """Отримати календар з датами повідомлень"""

        birthdays = self.get_birthdays_for_month(year, month)
        notifications = {}

        for birthday in birthdays:
            notification_date = self.email_service.get_notification_date(
                birthday["employee"].birth_date, year
            )

            if notification_date.month == month:
                day = notification_date.day
                if day not in notifications:
                    notifications[day] = []
                notifications[day].append(
                    {
                        "employee": birthday["employee"],
                        "birthday_date": birthday["date"],
                    }
                )

        return notifications

    @staticmethod
    def get_birthday_employees(today: date) -> List[Employee]:
        """Отримати співробітників з ДН в конкретну дату"""
        return Employee.query.filter(
            db.extract("month", Employee.birth_date) == today.month,
            db.extract("day", Employee.birth_date) == today.day,
        ).all()
