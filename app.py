from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from celery import Celery
from config import Config

# Ініціалізація розширень
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
celery = Celery()


def create_app(config_class: Config = Config) -> Flask:
    """ Функція створення Flask-додатку """

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ініціалізація розширень з app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Налаштування Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Будь ласка, увійдіть для доступу до цієї сторінки.'
    login_manager.login_message_category = 'info'

    # Ініціалізація Celery
    celery.conf.update(app.config)

    # Реєстрація блюпринтів
    from routes.auth import auth_bp
    from routes.employees import employees_bp
    from routes.templates import templates_bp
    from routes.logs import logs_bp
    from routes.settings import settings_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    app.register_blueprint(logs_bp, url_prefix='/logs')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(dashboard_bp, url_prefix='/')

    # Створення таблиць БД
    with app.app_context():
        db.create_all()

    return app