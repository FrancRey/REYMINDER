import os
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "reyminder.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("REYMINDER_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("REYMINDER_SECRET_KEY environment variable is required.")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                reset_token TEXT,
                reset_expires TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                notes TEXT DEFAULT '',
                category TEXT NOT NULL DEFAULT 'Personal',
                due_at TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

init_db()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_now():
    return {"current_year": datetime.now().year}

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please complete all required fields.", "error")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            try:
                with get_db() as db:
                    db.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password))
                    )
                flash("Account created. You can now log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("An account with that email already exists.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        with get_db() as db:
            user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if user:
                token = secrets.token_urlsafe(32)
                expires = datetime.now().timestamp() + 1800
                expiry_text = datetime.fromtimestamp(expires).isoformat(timespec="seconds")
                db.execute(
                    "UPDATE users SET reset_token = ?, reset_expires = ? WHERE id = ?",
                    (token, expiry_text, user["id"])
                )
                # Local classroom demo only: token appears in terminal, not sent by email.
                print("\\n[REYMINDER DEMO] Password reset link (local testing only):")
                print(f"http://127.0.0.1:5000/reset-password/{token}\\n")
        flash("If that email is registered, a reset link has been generated for the local demo. Check the VS Code terminal.", "info")
        return redirect(url_for("forgot_password"))
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE reset_token = ?", (token,)).fetchone()
    valid = False
    if user and user["reset_expires"]:
        try:
            valid = datetime.fromisoformat(user["reset_expires"]).timestamp() > datetime.now().timestamp()
        except ValueError:
            valid = False
    if not valid:
        flash("That reset link is invalid or expired. Request a new one.", "error")
        return redirect(url_for("forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            with get_db() as db:
                db.execute(
                    "UPDATE users SET password_hash = ?, reset_token = NULL, reset_expires = NULL WHERE id = ?",
                    (generate_password_hash(password), user["id"])
                )
            flash("Password updated. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("reset_password.html")

@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM reminders WHERE user_id = ? ORDER BY completed ASC, due_at ASC",
            (session["user_id"],)
        ).fetchall()
    reminders = [dict(row) for row in rows]
    total = len(reminders)
    completed = sum(1 for r in reminders if r["completed"])
    upcoming = [r for r in reminders if not r["completed"]][:5]
    return render_template("dashboard.html", reminders=reminders, total=total,
                           completed=completed, upcoming=upcoming)

@app.route("/reminders", methods=["POST"])
@login_required
def create_reminder():
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip()
    category = request.form.get("category", "Personal").strip()
    due_at = request.form.get("due_at", "").strip()
    if not title or not due_at:
        flash("Please enter a reminder title and date/time.", "error")
        return redirect(url_for("dashboard"))
    try:
        # HTML datetime-local format is accepted; store consistently as entered.
        datetime.fromisoformat(due_at)
    except ValueError:
        flash("Please choose a valid date and time.", "error")
        return redirect(url_for("dashboard"))
    with get_db() as db:
        db.execute(
            "INSERT INTO reminders (user_id, title, notes, category, due_at) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], title, notes, category, due_at)
        )
    flash("Reminder saved.", "success")
    return redirect(url_for("dashboard"))

@app.route("/reminders/<int:reminder_id>/toggle", methods=["POST"])
@login_required
def toggle_reminder(reminder_id):
    with get_db() as db:
        reminder = db.execute(
            "SELECT completed FROM reminders WHERE id = ? AND user_id = ?",
            (reminder_id, session["user_id"])
        ).fetchone()
        if reminder:
            db.execute(
                "UPDATE reminders SET completed = ? WHERE id = ? AND user_id = ?",
                (0 if reminder["completed"] else 1, reminder_id, session["user_id"])
            )
    return redirect(url_for("dashboard"))

@app.route("/reminders/<int:reminder_id>/delete", methods=["POST"])
@login_required
def delete_reminder(reminder_id):
    with get_db() as db:
        db.execute("DELETE FROM reminders WHERE id = ? AND user_id = ?",
                   (reminder_id, session["user_id"]))
    flash("Reminder deleted.", "info")
    return redirect(url_for("dashboard"))

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
