from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    description = db.Column(db.Text)

    assigned_emails = db.Column(db.Text, default="[]", nullable=False)

    task_time = db.Column(db.DateTime)

    completed = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))