from app import create_app, db, celery
from models import Admin, AdminRole

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
