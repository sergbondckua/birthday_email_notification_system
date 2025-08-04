from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Enum
import enum


class AdminRole(enum.Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(Enum(AdminRole), nullable=False, default=AdminRole.ADMIN)
    created_at = db.Column(db.DateTime, default=datetime.now())

    # Зв'язки

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        return self.role == role

    def __repr__(self):
        return f"<Admin {self.username}>"


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Зв'язки
    email_logs = db.relationship("EmailLog", backref="employee", lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Employee {self.full_name}>"


class EmailTemplate(db.Model):
    __tablename__ = "email_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(300), nullable=False)
    template_text = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Зв'язки
    email_logs = db.relationship("EmailLog", backref="template", lazy=True)

    def __repr__(self):
        return f"<EmailTemplate {self.name}>"


class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=False
    )
    template_id = db.Column(
        db.Integer, db.ForeignKey("email_templates.id"), nullable=False
    )
    sent_date = db.Column(db.DateTime, default=datetime.utcnow)
    recipients_count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="sent")  # sent, failed, retry
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f"<EmailLog {self.id}>"


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))
