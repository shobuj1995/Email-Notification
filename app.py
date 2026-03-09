from flask import Flask, render_template, request, redirect, session, jsonify
from flask_migrate import Migrate
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from models import db, User, Task
from utils.email_service import send_email

from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)


# ============================
# Register
# ============================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already registered. Please login."

        hashed_password = generate_password_hash(password)

        new_user = User(
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ============================
# Login
# ============================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["email"] = user.email

            return redirect("/dashboard")

        else:
            return "Invalid login"

    return render_template("login.html")


# ============================
# Logout
# ============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ============================
# Dashboard
# ============================
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    now = datetime.now()

    tasks = Task.query.filter(
        Task.user_id == session["user_id"]
    ).order_by(Task.task_time.asc()).all()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        now=now
    )


# ============================
# Add Task (Multiple Emails)
# ============================
@app.route("/add_task", methods=["POST"])
def add_task():

    if "user_id" not in session:
        return redirect("/login")

    title = request.form["title"]

    description = request.form["description"]   # NEW LINE

    emails_raw = request.form.get("assigned_emails", "")

    # Convert comma separated emails → list
    email_list = [e.strip() for e in emails_raw.split(",") if e.strip()]

    import json
    assigned_emails_json = json.dumps(email_list)

    task_time = datetime.strptime(
        request.form["task_time"],
        "%Y-%m-%dT%H:%M"
    )

    new_task = Task(
        title=title,
        description=description,   # NEW LINE
        assigned_emails=assigned_emails_json,
        task_time=task_time,
        user_id=session["user_id"]
    )

    db.session.add(new_task)
    db.session.commit()

    return redirect("/dashboard")


# ============================
# Tasks Due API
# ============================
@app.route("/tasks_due")
def tasks_due():

    if "user_id" not in session:
        return jsonify([])

    now = datetime.now()

    tasks = Task.query.filter(
        Task.completed == False,
        Task.task_time <= now,
        Task.user_id == session["user_id"]
    ).all()

    result = [{"title": task.title} for task in tasks]

    return jsonify(result)


# ============================
# Delete Task
# ============================
@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):

    if "user_id" not in session:
        return redirect("/login")

    task = Task.query.get(task_id)

    if task and task.user_id == session["user_id"]:
        db.session.delete(task)
        db.session.commit()

    return redirect("/dashboard")


# ============================
# Edit Task
# ============================
@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):

    if "user_id" not in session:
        return redirect("/login")

    task = Task.query.get(task_id)

    if not task or task.user_id != session["user_id"]:
        return redirect("/dashboard")

    if request.method == "POST":

        task.title = request.form["title"]
        task.description = request.form.get("description", "")

        emails_raw = request.form.get("assigned_emails", "")
        email_list = [e.strip() for e in emails_raw.split(",") if e.strip()]

        task.assigned_emails = json.dumps(email_list)

        task.task_time = datetime.strptime(
            request.form["task_time"],
            "%Y-%m-%dT%H:%M"
        )

        db.session.commit()

        return redirect("/dashboard")

    email_list = json.loads(task.assigned_emails)
    emails_string = ", ".join(email_list)

    return render_template("edit_task.html", task=task, emails_string=emails_string)


# ============================
# Notification Scheduler
# ============================
def check_and_send_notifications():

    with app.app_context():

        now = datetime.now(timezone.utc)

        tasks = Task.query.filter(
            Task.completed == False,
            Task.task_time <= now
        ).all()

        for task in tasks:

            try:
                due_time_str = task.task_time.strftime("%Y-%m-%d %H:%M UTC")

                message = (
                    "This is a reminder that your task is now due.\n\n"
                    f"Task: {task.title}\n"
                    f"Due time: {due_time_str}\n\n"
                    "Please complete it soon."
                )

                # Parse JSON email list
                emails = json.loads(task.assigned_emails or "[]")

                send_email(
                    emails,
                    "Task Due Reminder",
                    message
                )

                task.completed = True

            except Exception as e:
                print(f"Failed to send email for task {task.id}: {e}")

        db.session.commit()


# ============================
# Scheduler Setup
# ============================
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_notifications, 'interval', seconds=10)
scheduler.start()


# ============================
# Run App
# ============================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)