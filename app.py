from flask import Flask, render_template, request, redirect, session
from flask_migrate import Migrate
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from flask import jsonify
from config import Config
from models import db, User, Task
from utils.email_service import send_email

from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
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

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already registered. Please login."

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create user
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
            print("Invalid login")

    return render_template("login.html")


# ============================
# Logout ⭐⭐⭐
# ============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ============================
# Dashboard (Protected)
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
# Add Task
# ============================
@app.route("/add_task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect("/login")

    title = request.form["title"]
    assigned_email = request.form["assigned_email"]

    task_time = datetime.strptime(
        request.form["task_time"],
        "%Y-%m-%dT%H:%M"
    )

    new_task = Task(
        title=title,
        assigned_email=assigned_email,
        task_time=task_time,
        user_id=session["user_id"]
    )

    db.session.add(new_task)
    db.session.commit()

    return redirect("/dashboard")

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

    # Don't send email here, just return JSON
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
        task.assigned_email = request.form["assigned_email"]

        task.task_time = datetime.strptime(
            request.form["task_time"],
            "%Y-%m-%dT%H:%M"
        )

        db.session.commit()

        return redirect("/dashboard")

    return render_template("edit_task.html", task=task)

# To test the Email Service manualy
# @app.route("/test_mail")
# def test_mail():
#
#     send_email(
#         "obaydul051@gmail.com",
#         "Manual Test",
#         "Hello Test"
#     )
#
#     return "Test Email Sent"
# # Notification Scheduler
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
                # Simple fixed body with only due time
                due_time_str = task.task_time.strftime("%Y-%m-%d %H:%M UTC")

                message = (
                    f"This is a reminder that your task is now due.\n\n"
                    f"Task: {task.title}\n"
                    f"Due time: {due_time_str}\n\n"
                    f"Please complete it soon."
                )

                send_email(
                    task.assigned_email,
                    "Task Due Reminder",
                    message
                )

                # Still marking as completed (you can remove this line if you don't want it)
                task.completed = True

            except Exception as e:
                print(f"Failed to send email for task {task.id}: {e}")

        db.session.commit()


# Scheduler setup (unchanged)
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_notifications, 'interval', seconds=10)
scheduler.start()

# ============================
# Run App
# ============================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
