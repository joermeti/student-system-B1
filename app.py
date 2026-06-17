"""
RMETI Student Portal - Simple Flask Prototype
Features:
- Student enrollment form (info + semester + payment plan)
- Instructor can add grades & hours attended
- Students can view their own record + grades/hours
- Contractors can view their apprentices + grades/hours
- Role-based simple access

Run with: python app.py
Then visit http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "rmeti-secret-key-change-in-production"  # Change this in real use

DB_PATH = "rmeti_portal.db"

# ---------------- Database Setup ----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Students table
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            address TEXT,
            contractor_name TEXT,
            contractor_email TEXT,
            semester TEXT NOT NULL,
            payment_plan TEXT NOT NULL,
            enrollment_date TEXT,
            status TEXT DEFAULT 'Active'
        )
    """)

    # Grades & Hours table (Instructors add this)
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            semester TEXT NOT NULL,
            module_name TEXT,
            grade TEXT,
            hours_attended INTEGER,
            recorded_by TEXT,
            recorded_date TEXT,
            notes TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ---------------- Helper Functions ----------------
def get_student_by_email(email):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
    conn.close()
    return student

def get_students_by_contractor(contractor_email):
    conn = get_db()
    students = conn.execute(
        "SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name",
        (contractor_email,)
    ).fetchall()
    conn.close()
    return students

def get_grades_for_student(student_id):
    conn = get_db()
    grades = conn.execute(
        "SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC",
        (student_id,)
    ).fetchall()
    conn.close()
    return grades

# ---------------- Routes ----------------

@app.route("/")
def index():
    return render_template("index.html")

# ---------- Student Enrollment Form ----------
@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        contractor_name = request.form.get("contractor_name")
        contractor_email = request.form.get("contractor_email")
        semester = request.form.get("semester")
        payment_plan = request.form.get("payment_plan")

        if not full_name or not email or not semester or not payment_plan:
            flash("Please fill out all required fields.", "error")
            return redirect(url_for("enroll"))

        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO students 
                (full_name, email, phone, address, contractor_name, contractor_email, semester, payment_plan, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                full_name, email, phone, address,
                contractor_name, contractor_email,
                semester, payment_plan,
                datetime.now().strftime("%Y-%m-%d")
            ))
            conn.commit()
            flash("Student enrolled successfully!", "success")
            return redirect(url_for("enroll_success"))
        except sqlite3.IntegrityError:
            flash("A student with this email already exists.", "error")
        finally:
            conn.close()

    # Semester options (customize as needed)
    semesters = ["Fall 2026", "Spring 2027", "Summer 2027", "Fall 2027"]
    payment_plans = [
        "Full Payment",
        "Interest-Free 5-Month Plan",
        "Interest-Free 10-Month Plan",
        "Monthly Payment Plan"
    ]

    return render_template("enroll.html", semesters=semesters, payment_plans=payment_plans)

@app.route("/enroll/success")
def enroll_success():
    return render_template("enroll_success.html")

# ---------- Simple Role Selection / Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        identifier = request.form.get("identifier")  # email for student/contractor, name for instructor

        session["role"] = role
        session["identifier"] = identifier

        if role == "student":
            student = get_student_by_email(identifier)
            if student:
                session["student_id"] = student["id"]
                return redirect(url_for("student_dashboard"))
            else:
                flash("No student found with that email.", "error")
        elif role == "contractor":
            return redirect(url_for("contractor_dashboard"))
        elif role == "instructor":
            return redirect(url_for("instructor_dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ---------- Student Dashboard ----------
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("login"))

    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    grades = get_grades_for_student(student_id)
    conn.close()

    return render_template("student_dashboard.html", student=student, grades=grades)

# ---------- Contractor Dashboard ----------
@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor":
        return redirect(url_for("login"))

    contractor_email = session.get("identifier")
    students = get_students_by_contractor(contractor_email)

    # Get grades for each student
    student_data = []
    for s in students:
        grades = get_grades_for_student(s["id"])
        student_data.append({
            "student": s,
            "grades": grades
        })

    return render_template("contractor_dashboard.html", student_data=student_data, contractor_email=contractor_email)

# ---------- Instructor Dashboard ----------
@app.route("/instructor", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        semester = request.form.get("semester")
        module_name = request.form.get("module_name")
        grade = request.form.get("grade")
        hours = request.form.get("hours_attended")
        notes = request.form.get("notes")
        instructor_name = session.get("identifier", "Instructor")

        if student_id and semester:
            conn.execute("""
                INSERT INTO grades_hours 
                (student_id, semester, module_name, grade, hours_attended, recorded_by, recorded_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_id, semester, module_name, grade, hours,
                instructor_name, datetime.now().strftime("%Y-%m-%d %H:%M"), notes
            ))
            conn.commit()
            flash("Grade and hours recorded successfully!", "success")

    # Get all students for instructor to choose from
    students = conn.execute("SELECT id, full_name, semester FROM students ORDER BY full_name").fetchall()
    conn.close()

    semesters = ["Fall 2026", "Spring 2027", "Summer 2027", "Fall 2027"]

    return render_template("instructor_dashboard.html", students=students, semesters=semesters)

# ---------- Run App ----------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
