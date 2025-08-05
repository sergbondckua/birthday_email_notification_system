from app import create_app, db, celery
from models import Admin, AdminRole

app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
