from flask import current_app
from flask_mail import Message
from app import mail, db
from models import Employee, EmailTemplate, EmailLog
from datetime import date, timedelta
import pytz
from typing import List, Tuple


class EmailService:
    """Сервіс для відправки електронних листів"""

    @staticmethod
    def get_timezone():
        """Отримати часову зону з поточного конфігу."""
        return pytz.timezone(current_app.config["TIMEZONE"])

    @staticmethod
    def get_birthday_employees(target_date: date) -> List[Employee]:
        """Отримати співробітників з ДН в конкретну дату"""
        return Employee.query.filter(
            db.extract("month", Employee.birth_date) == target_date.month,
            db.extract("day", Employee.birth_date) == target_date.day,
        ).all()

    @staticmethod
    def get_notification_date(birth_date: date, current_year: int) -> date:
        """Розрахувати дату відправки повідомлення (2 дні до ДН або останній робочий день)"""
        # Створюємо дату ДН для поточного року
        try:
            birthday_this_year = birth_date.replace(year=current_year)
        except ValueError:  # 29 лютого в невисокосному році
            birthday_this_year = birth_date.replace(year=current_year, day=28)

        # 2 дні до ДН
        notification_date = birthday_this_year - timedelta(days=2)

        # Перевіряємо чи не вихідний
        while notification_date.weekday() >= 5:  # 5=субота, 6=неділя
            notification_date -= timedelta(days=1)

        return notification_date

    def get_employees_for_notification(
        self,
        notification_date: date,
    ) -> List[Employee]:
        """Отримати список співробітників для яких потрібно відправити повідомлення"""
        employees_to_notify = []
        current_year = notification_date.year

        all_employees = Employee.query.all()  # Отримати всіх співробітників

        # Знаходимо співробітників, які повинні отримати повідомлення
        for employee in all_employees:
            expected_notification_date = self.get_notification_date(
                employee.birth_date, current_year
            )

            if expected_notification_date == notification_date:
                employees_to_notify.append(employee)

        return employees_to_notify

    @staticmethod
    def format_template(template_text: str, employee: Employee) -> str:
        """Форматування шаблону з плейсхолдерами"""
        formatted_text = template_text.replace("{name}", employee.full_name)
        formatted_date = employee.birth_date.strftime("%d.%m.%Y")
        formatted_text = formatted_text.replace("{date}", formatted_date)
        return formatted_text

    def send_birthday_notification(
        self, employee: Employee, template: EmailTemplate
    ) -> Tuple[bool, str]:
        """Відправити повідомлення про ДН конкретного співробітника"""
        try:
            # Отримати всіх співробітників крім іменинника
            recipients = Employee.query.filter(
                Employee.id != employee.id
            ).all()
            recipient_emails = [emp.email for emp in recipients]

            if not recipient_emails:
                return False, "Немає отримувачів для розсилки"

            # Форматування повідомлення
            formatted_subject = self.format_template(
                template.subject, employee
            )
            formatted_body = self.format_template(
                template.template_text, employee
            )

            # Створення повідомлення
            msg = Message(
                subject=formatted_subject,
                recipients=recipient_emails,
                body=formatted_body,
                sender=current_app.config["MAIL_DEFAULT_SENDER"],
            )

            # Відправка
            mail.send(msg)

            # Логування успішної відправки
            email_log = EmailLog(
                employee_id=employee.id,
                template_id=template.id,
                recipients_count=len(recipient_emails),
                status="sent",
            )
            db.session.add(email_log)
            db.session.commit()

            return (
                True,
                f"Повідомлення відправлено {len(recipient_emails)} співробітникам",
            )

        except Exception as e:
            # Логування помилки
            email_log = EmailLog(
                employee_id=employee.id,
                template_id=template.id,
                recipients_count=0,
                status="failed",
                error_message=str(e),
            )
            db.session.add(email_log)
            db.session.commit()

            return False, f"Помилка відправки: {str(e)}"
