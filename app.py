from flask import Flask, request, redirect, url_for, flash, session
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS grades_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            module_name TEXT,
            grade TEXT,
            hours_attended INTEGER,
            recorded_by TEXT,
            recorded_date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==================== HOME + LOGIN (same as before) ====================
@app.route("/")
def home():
    return """
    <div style="max-width:700px;margin:50px auto;font-family:Arial;">
        <h1 style="color:#166534;">RMETI Student Portal</h1>
        <a href="/enroll" style="background:#166534;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;">Enroll Student</a>
        <a href="/login" style="background:#374151;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;margin-left:10px;">Login</a>
    </div>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        identifier = request.form.get("identifier")
        session["role"] = role
        session["identifier"] = identifier

        if role == "student":
            conn = get_db()
            student = conn.execute("SELECT * FROM students WHERE email = ?", (identifier,)).fetchone()
            conn.close()
            if student:
                session["student_id"] = student["id"]
                return redirect(url_for("student_dashboard"))
            flash("Student not found.")
            return redirect(url_for("login"))
        return redirect(url_for(f"{role}_dashboard"))

    return """
    <div style="max-width:400px;margin:60px auto;font-family:Arial;">
        <h2>Login</h2>
        <form method="POST">
            <select name="role" style="width:100%;padding:10px;margin-bottom:15px;">
                <option value="student">Student</option>
                <option value="contractor">Contractor</option>
                <option value="instructor">Instructor</option>
            </select><br>
            <input type="text" name="identifier" placeholder="Email or Name" required style="width:100%;padding:10px;margin-bottom:20px;"><br>
            <button type="submit" style="background:#166534;color:white;padding:12px 30px;border:none;border-radius:8px;">Login</button>
        </form>
    </div>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return "<h2>Student Dashboard</h2><a href='/logout'>Logout</a>"

@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor":
        return redirect(url_for("login"))
    return "<h2>Contractor Dashboard</h2><a href='/logout'>Logout</a>"

# ==================== INSTRUCTOR DASHBOARD (with history) ====================
@app.route("/instructor", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))

    conn = get_db()
    students = conn.execute("SELECT * FROM students ORDER BY full_name").fetchall()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        module_name = request.form.get("module_name")
        grade = request.form.get("grade")
        hours = request.form.get("hours_attended") or 0
        instructor_name = session.get("identifier", "Instructor")

        conn.execute("""
            INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, module_name, grade, hours, instructor_name, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        flash("Record saved!")

    html = """
    <div style="max-width:1100px;margin:30px auto;font-family:Arial;">
        <h2>Instructor Dashboard</h2>
        <p>Add grades and hours. Previously recorded entries are shown below each student.</p>
    """

    for s in students:
        # Get grades for this student
        grades = conn.execute("""
            SELECT * FROM grades_hours 
            WHERE student_id = ? 
            ORDER BY recorded_date DESC
        """, (s['id'],)).fetchall()

        html += f"""
        <div style="border:1px solid #ddd; padding:20px; margin-bottom:25px; border-radius:10px;">
            <strong style="font-size:18px;">{s['full_name']}</strong> — {s['semester']}<br><br>

            <!-- Add new record form -->
            <form method="POST" style="margin-bottom:20px;">
                <input type="hidden" name="student_id" value="{s['id']}">
                Module: <input type="text" name="module_name" placeholder="e.g. NEC Chapter 1" style="width:220px;">
                Grade: <input type="text" name="grade" placeholder="A / 92" style="width:100px;">
                Hours: <input type="number" name="hours_attended" placeholder="8" style="width:70px;">
                <button type="submit" style="background:#166534;color:white;padding:6px 16px;border:none;border-radius:6px;margin-left:10px;">Save</button>
            </form>
        """

        # Show history of grades
        if grades:
            html += "<strong>Previous Records:</strong><br>"
            html += "<table border='1' cellpadding='8' style='border-collapse:collapse; width:100%; margin-top:8px;'>"
            html += "<tr style='background:#f3f4f6;'><th>Module</th><th>Grade</th><th>Hours</th><th>Date</th><th>Recorded By</th></tr>"
            for g in grades:
                html += f"""
                <tr>
                    <td>{g['module_name'] or '-'}</td>
                    <td>{g['grade'] or '-'}</td>
                    <td>{g['hours_attended'] or '-'}</td>
                    <td>{g['recorded_date']}</td>
                    <td>{g['recorded_by']}</td>
                </tr>
                """
            html += "</table>"
        else:
            html += "<em>No grades recorded yet for this student.</em>"

        html += "</div>"

    conn.close()
    html += "<br><a href='/logout'>Logout</a></div>"
    return html

# ==================== ENROLL ====================
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
            flash("Email already exists.")
        finally:
            conn.close()

    return """
    <div style="max-width:600px;margin:40px auto;font-family:Arial;">
        <h2>Enroll Student</h2>
        <form method="POST">
            Full Name: <input type="text" name="full_name" required><br><br>
            Email: <input type="email" name="email" required><br><br>
            Phone: <input type="text" name="phone"><br><br>
            Semester: <input type="text" name="semester" value="Fall 2026"><br><br>
            Payment Plan: <input type="text" name="payment_plan" value="Interest-Free 5-Month Plan"><br><br>
            <button type="submit">Enroll</button>
        </form>
    </div>
    """

@app.route("/success")
def success():
    return "<h2>Success!</h2><a href='/enroll'>Enroll more</a> | <a href='/instructor'>Instructor Page</a>"

if __name__ == "__main__":
    app.run()
