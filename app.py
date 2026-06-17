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
    conn.close()
    return f"""
    <div style="max-width: 700px; margin: 40px auto; font-family: Arial;">
        <h2>Welcome, {student['full_name']}</h2>
        <p><strong>Semester:</strong> {student['semester']}</p>
        <p><strong>Payment Plan:</strong> {student['payment_plan']}</p>
        <p><strong>Contractor:</strong> {student['contractor_name'] if 'contractor_name' in student.keys() else 'N/A'}</p>
        <br>
        <a href="/logout">Logout</a>
    </div>
    """

# ==================== CONTRACTOR DASHBOARD ====================
@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor":
        return redirect(url_for("login"))
    email = session.get("identifier")
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE email LIKE ?", ('%' + email + '%',)).fetchall()
    conn.close()
    html = f"<h2>Contractor Dashboard</h2><p>Showing students for: {email}</p>"
    if students:
        for s in students:
            html += f"<p>{s['full_name']} - {s['email']}</p>"
    else:
        html += "<p>No students found.</p>"
    html += "<br><a href='/logout'>Logout</a>"
    return html

# ==================== INSTRUCTOR DASHBOARD ====================
@app.route("/instructor")
def instructor_dashboard():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))
    return """
    <div style="max-width: 700px; margin: 40px auto; font-family: Arial;">
        <h2>Instructor Dashboard</h2>
        <p>Welcome! You can add grades and hours here (coming soon).</p>
        <br>
        <a href="/logout">Logout</a>
    </div>
    """

# ==================== ENROLL + SUCCESS + STUDENTS (same as before) ====================
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
