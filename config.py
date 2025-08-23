from environs import Env

# Прочитайте змінні середовища
env = Env()
env.read_env()


class Config:
    """Клас конфігурації Flask додатку."""

    DEBUG = True

    SECRET_KEY = (
        env.str("SECRET_KEY") or "JJJHou8u^8556@(*5CCHHnvhvggvgfccf!"
    )
    SQLALCHEMY_DATABASE_URI = (
        env.str("DATABASE_URL") or "sqlite:///birthday_app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Налаштування пошти
    MAIL_SERVER = env.str("MAIL_SERVER")
    MAIL_PORT = env.int("MAIL_PORT") or 587
    MAIL_USE_TLS = env.bool("MAIL_USE_TLS")
    MAIL_USE_SSL = env.bool("MAIL_USE_SSL")
    MAIL_USERNAME = env.str("MAIL_USERNAME")
    MAIL_PASSWORD = env.str("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = env.str("MAIL_DEFAULT_SENDER")

    # Налаштування Celery
    broker_url = (
        env.str("CELERY_BROKER_URL") or "redis://localhost:6379/0"
    )
    result_backend = (
        env.str("CELERY_RESULT_BACKEND") or "redis://localhost:6379/0"
    )

    # Часова зона
    TIMEZONE = env.str("TIMEZONE") or "Europe/Kyiv"

    # Налаштування Email відправлення
    EMAIL_SEND_TIME = env.int("EMAIL_SEND_TIME")
    RETRY_ATTEMPTS = env.int("RETRY_ATTEMPTS")
    RETRY_DELAY = env.int("RETRY_DELAY")

    # Налаштування сесій
    SESSION_COOKIE_HTTPONLY = True  # Заборонити доступ до кук через JavaScript
    SESSION_COOKIE_SECURE = False  # Передавати куки тільки через HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
