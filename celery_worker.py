from celery.schedules import crontab

from app import create_app, celery

from tasks import celery_tasks  # імпортуємо, щоб зареєструвати задачі

# Ініціалізація Flask app та контекст
flask_app = create_app()
flask_app.app_context().push()

# Налаштування розкладу для celery beat
celery.conf.beat_schedule = {
    "daily-birthday-check": {
        "task": "tasks.celery_tasks.send_daily_birthday_notifications",
        "schedule": crontab(
            minute="17", hour="23" # hour=flask_app.config.get("EMAIL_SEND_TIME")
        ),  # час запуску
    },
}

# Налаштування часової зони
celery.conf.timezone = flask_app.config.get("TIMEZONE", "UTC")
