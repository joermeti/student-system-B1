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
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            module_name TEXT,
            hours_attended INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Present',
            recorded_by TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==================== HOME ====================
@app.route("/")
def home():
    return """
    <div style="max-width: 700px; margin: 50px auto; font-family: Arial;">
        <h1 style="color: #166534;">RMETI Student Portal</h1>
        <p style="font-size: 18px;">Rocky Mountain Electrical Training Institute</p>
        <br>
        <a href="/enroll" style="background:#166534; color:white; padding:12px 24px; text-decoration:none; border-radius:8px;">Enroll New Student</a>
        <a href="/login" style="background:#374151; color:white; padding:12px 24px; text-decoration:none; border-radius:8px; margin-left:10px;">Login</a>
    </div>
    """

# ==================== LOGIN ====================
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
            else:
                flash("No student found with that email.")
                return redirect(url_for("login"))

        return redirect(url_for(f"{role}_dashboard"))

    return """
    <div style="max-width: 400px; margin: 60px auto; font-family: Arial;">
        <h2>Login</h2>
        <form method="POST">
            <label>I am a:</label><br>
            <select name="role" style="width:100%; padding:10px; margin-bottom:15px;">
                <option value="student">Student</option>
                <option value="contractor">Electrical Contractor</option>
                <option value="instructor">Instructor</option>
            </select><br>
            <label>Email or Name:</label><br>
            <input type="text" name="identifier" required style="width:100%; padding:10px; margin-bottom:20px;"><br>
            <button type="submit" style="background:#166534; color:white; padding:12px 30px; border:none; border-radius:8px;">Login</button>
        </form>
        <p><a href="/">Back to Home</a></p>
    </div>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ==================== STUDENT DASHBOARD ====================
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    student_id = session.get("student_id")
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    attendance = conn.execute("SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC", (student_id,)).fetchall()
    conn.close()

    html = f"""
    <div style="max-width: 900px; margin: 40px auto; font-family: Arial;">
        <h2>Welcome, {student['full_name']}</h2>
        <p><strong>Semester:</strong> {student['semester']} | <strong>Payment Plan:</strong> {student['payment_plan']}</p>
        <br>
        <h3>Attendance History</h3>
    """
    if attendance:
        html += "<table border='1' cellpadding='10' style='width:100%;'><tr><th>Date</th><th>Module</th><th>Status</th><th>Hours</th></tr>"
        for a in attendance:
            html += f"<tr><td>{a['date']}</td><td>{a['module_name']}</td><td>{a['status']}</td><td>{a['hours_attended']}</td></tr>"
        html += "</table>"
    else:
        html += "<p>No attendance records yet.</p>"
    html += "<br><a href='/logout'>Logout</a></div>"
    return html

# ==================== IMPROVED CONTRACTOR DASHBOARD ====================
@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor":
        return redirect(url_for("login"))
    email = session.get("identifier")
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE email LIKE ?", ('%' + email.split('@')[0] + '%',)).fetchall()

    html = f"""
    <div style="max-width: 1000px; margin: 40px auto; font-family: Arial;">
        <h2>Your Apprentices</h2>
        <p>Showing students sponsored by: <strong>{email}</strong></p>
        <br>
    """

    if students:
        for student in students:
            # Get attendance count for this student
            attendance_count = conn.execute("SELECT COUNT(*) as count FROM attendance WHERE student_id = ?", (student['id'],)).fetchone()['count']
            total_hours = conn.execute("SELECT SUM(hours_attended) as total FROM attendance WHERE student_id = ?", (student['id'],)).fetchone()['total'] or 0

            html += f"""
            <div style="border: 1px solid #ccc; padding: 20px; margin-bottom: 20px; border-radius: 10px;">
                <h3>{student['full_name']}</h3>
                <p><strong>Email:</strong> {student['email']}</p>
                <p><strong>Semester:</strong> {student['semester']} | <strong>Payment Plan:</strong> {student['payment_plan']}</p>
                <p><strong>Attendance Records:</strong> {attendance_count} sessions | <strong>Total Hours:</strong> {total_hours}</p>
            </div>
            """
    else:
        html += "<p>No students found associated with this contractor email.</p>"

    conn.close()
    html += "<br><a href='/logout'>Logout</a></div>"
    return html

# ==================== INSTRUCTOR DASHBOARD ====================
@app.route("/instructor", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))

    conn = get_db()
    students = conn.execute("SELECT id, full_name FROM students").fetchall()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        date = request.form.get("date")
        module_name = request.form.get("module_name")
        hours = request.form.get("hours_attended") or 0
        status = request.form.get("status")
        notes = request.form.get("notes")
        instructor_name = session.get("identifier", "Instructor")

        conn.execute("""
            INSERT INTO attendance (student_id, date, module_name, hours_attended, status, recorded_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, date, module_name, hours, status, instructor_name, notes))
        conn.commit()
        flash("Attendance recorded successfully!")

    conn.close()
    return """
    <div style="max-width: 650px; margin: 40px auto; font-family: Arial;">
        <h2>Instructor - Record Attendance</h2>
        <form method="POST">
            <label>Student:</label><br>
            <select name="student_id" style="width:100%; padding:10px; margin-bottom:15px;">
                {% for s in students %}
                <option value="{{ s['id'] }}">{{ s['full_name'] }}</option>
                {% endfor %}
            </select><br>

            <label>Date:</label><br>
            <input type="date" name="date" style="width:100%; padding:10px; margin-bottom:15px;"><br>

            <label>Module / Class:</label><br>
            <input type="text" name="module_name" style="width:100%; padding:10px; margin-bottom:15px;"><br>

            <label>Hours Attended:</label><br>
            <input type="number" name="hours_attended" value="4" style="width:100%; padding:10px; margin-bottom:15px;"><br>

            <label>Status:</label><br>
            <select name="status" style="width:100%; padding:10px; margin-bottom:15px;">
                <option value="Present">Present</option>
                <option value="Absent">Absent</option>
                <option value="Late">Late</option>
            </select><br>

            <label>Notes:</label><br>
            <textarea name="notes" style="width:100%; padding:10px; margin-bottom:20px;"></textarea><br>

            <button type="submit" style="background:#166534; color:white; padding:12px 30px; border:none; border-radius:8px;">Save Attendance</button>
        </form>
        <br>
        <a href="/logout">Logout</a>
    </div>
    """

# ==================== ENROLL + SUCCESS + STUDENTS ====================
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
    <div style="max-width: 600px; margin: 40px auto; font-family: Arial;">
        <h2>Student Enrollment Form</h2>
        <form method="POST">
            Full Name: <input type="text" name="full_name" required><br><br>
            Email: <input type="email" name="email" required><br><br>
            Phone: <input type="text" name="phone"><br><br>
            Semester: <input type="text" name="semester" value="Fall 2026"><br><br>
            Payment Plan: <input type="text" name="payment_plan" value="Interest-Free 5-Month Plan"><br><br>
            <button type="submit">Enroll Student</button>
        </form>
    </div>
    """

@app.route("/success")
def success():
    return "<h2>Enrollment Successful!</h2><p><a href='/enroll'>Enroll another</a> | <a href='/students'>View Students</a></p>"

@app.route("/students")
def students():
    conn = get_db()
    all_students = conn.execute("SELECT * FROM students ORDER BY enrollment_date DESC").fetchall()
    conn.close()
    html = "<h2>All Enrolled Students</h2>"
    for s in all_students:
        html += f"<p>{s['full_name']} - {s['email']} ({s['semester']})</p>"
    html += "<p><a href='/'>Back</a></p>"
    return html

if __name__ == "__main__":
    app.run()
