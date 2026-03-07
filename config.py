import os
class Config:
    # Correct key name for SQLAlchemy
    SQLALCHEMY_DATABASE_URI = "postgresql://todo_user:StrongPassword123@localhost:5432/todo_app_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for sessions and CSRF protection
    SECRET_KEY = os.environ.get("SECRET_KEY") or "secret123"
