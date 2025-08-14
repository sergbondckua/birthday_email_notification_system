from typing import Dict, Any, List

from datetime import date

from services.email_service import EmailService
from models import EmailTemplate
from app import create_app, celery
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery.task
def send_daily_birthday_notifications() -> List[Dict[str, Any]] | str:
    """Щоденна задача для відправки повідомлень про ДН"""

    app = create_app()

    with app.app_context():
        try:
            today = date.today()
            logger.info("Запуск щоденної перевірки ДН %s", today)
            email_service = EmailService()

            # Отримати активний шаблон
            active_template = EmailTemplate.query.filter_by(
                is_active=True
            ).first()
            if not active_template:
                logger.warning(
                    "Не знайдено активного шаблону листа, створіть новий або активізуєте існуючий"
                )
                return "Не знайдено активного шаблону"

            # Отримати співробітників для повідомлення про їх ДН
            employees_to_notify = email_service.get_employees_for_notification(
                today
            )

            if not employees_to_notify:
                logger.info("Немає найближчих ДН для нагадування")
                return "Немає найближчих ДН для нагадування"

            results = []
            for employee in employees_to_notify:
                success, message = email_service.send_birthday_notification(
                    employee, active_template
                )

                if success:
                    logger.info(
                        "Успішно відправлено нагадування про ДН %s",
                        employee.full_name,
                    )
                else:
                    logger.error(
                        "Помилка відправки нагадування про ДН %s: %s",
                        employee.full_name,
                        message,
                    )

                results.append(
                    {
                        "employee": employee.full_name,
                        "success": success,
                        "message": message,
                    }
                )

            return results

        except Exception as e:
            logger.error(
                "Помилка в щоденній задачі: %s", str(e), exc_info=True
            )
            return f"Помилка: {str(e)}"


@celery.task(bind=True, max_retries=1)
def retry_failed_email(self, employee_id: int, template_id: int) -> str:
    """Повторна спроба відправки email"""

    app = create_app()

    with app.app_context():
        try:
            from models import Employee, EmailTemplate

            employee = Employee.query.get(employee_id)
            template = EmailTemplate.query.get(template_id)

            if not employee or not template:
                return "Співробітник або шаблон не знайдені"

            success, message = EmailService().send_birthday_notification(
                employee, template
            )

            if not success and self.request.retries < self.max_retries:
                logger.warning(
                    "Повторна спроба %d для %s",
                    self.request.retries + 1,
                    employee.full_name,
                )
                raise self.retry(countdown=300)  # Повторити

            return message

        except Exception as e:
            logger.error(
                "Помилка в повторній спробі: %s", str(e), exc_info=True
            )
            if self.request.retries < self.max_retries:
                raise self.retry(countdown=300)
            return f"Помилка після всіх спроб: {str(e)}"
