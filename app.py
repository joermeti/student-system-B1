from flask import Flask, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "rmeti-secret-2026"

def get_db():
    conn = sqlite3.connect("rmeti_portal.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            semester TEXT,
            payment_plan TEXT,
            enrollment_date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return """
    <h1>RMETI Student Portal</h1>
    <p><a href='/enroll'>Enroll a New Student</a></p>
    """

@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        semester = request.form.get("semester")
        payment_plan = request.form.get("payment_plan")

        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO students (full_name, email, phone, semester, payment_plan, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (full_name, email, phone, semester, payment_plan, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            flash("Student enrolled successfully!")
            return redirect(url_for("success"))
        except sqlite3.IntegrityError:
            flash("This email is already registered.")
        finally:
            conn.close()

    return """
    <h2>Student Enrollment Form</h2>
    <form method="POST">
        Full Name: <input type="text" name="full_name" required><br><br>
        Email: <input type="email" name="email" required><br><br>
        Phone: <input type="text" name="phone"><br><br>
        Semester: <input type="text" name="semester" value="Fall 2026"><br><br>
        Payment Plan: <input type="text" name="payment_plan" value="Interest-Free 5-Month Plan"><br><br>
        <button type="submit">Enroll Student</button>
    </form>
    """

@app.route("/success")
def success():
    return "<h2>Enrollment Successful!</h2><p><a href='/enroll'>Enroll another student</a></p>"

if __name__ == "__main__":
    app.run()
