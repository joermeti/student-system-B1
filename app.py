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
    <div style="max-width: 700px; margin: 50px auto; font-family: Arial, sans-serif;">
        <h1 style="color: #166534;">RMETI Student Portal</h1>
        <p style="font-size: 18px;">Rocky Mountain Electrical Training Institute</p>
        <br>
        <a href="/enroll" style="background-color: #166534; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin-right: 10px;">Enroll New Student</a>
        <a href="/students" style="background-color: #374151; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">View All Students</a>
    </div>
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
    <div style="max-width: 600px; margin: 40px auto; font-family: Arial, sans-serif;">
        <h2>Student Enrollment Form</h2>
        <form method="POST" style="background: #f9fafb; padding: 30px; border-radius: 12px;">
            <label>Full Name</label><br>
            <input type="text" name="full_name" required style="width: 100%; padding: 10px; margin-bottom: 15px;"><br>
            
            <label>Email Address</label><br>
            <input type="email" name="email" required style="width: 100%; padding: 10px; margin-bottom: 15px;"><br>
            
            <label>Phone Number</label><br>
            <input type="text" name="phone" style="width: 100%; padding: 10px; margin-bottom: 15px;"><br>
            
            <label>Semester</label><br>
            <input type="text" name="semester" value="Fall 2026" style="width: 100%; padding: 10px; margin-bottom: 15px;"><br>
            
            <label>Payment Plan</label><br>
            <input type="text" name="payment_plan" value="Interest-Free 5-Month Plan" style="width: 100%; padding: 10px; margin-bottom: 20px;"><br>
            
            <button type="submit" style="background-color: #166534; color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 16px;">Enroll Student</button>
        </form>
        <p style="margin-top: 20px;"><a href="/">← Back to Home</a></p>
    </div>
    """

@app.route("/success")
def success():
    return """
    <div style="max-width: 600px; margin: 80px auto; text-align: center; font-family: Arial;">
        <h2 style="color: #166534;">Enrollment Successful!</h2>
        <p>The student has been added to the system.</p>
        <br>
        <a href="/enroll" style="margin-right: 15px;">Enroll Another Student</a>
        <a href="/students">View All Students</a>
    </div>
    """

@app.route("/students")
def students():
    conn = get_db()
    all_students = conn.execute("SELECT * FROM students ORDER BY enrollment_date DESC").fetchall()
    conn.close()

    html = """
    <div style="max-width: 1000px; margin: 40px auto; font-family: Arial;">
        <h2>Enrolled Students</h2>
        <p><a href="/">← Back to Home</a></p>
    """
    if not all_students:
        html += "<p>No students enrolled yet.</p>"
    else:
        html += """
        <table border="1" cellpadding="12" cellspacing="0" style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #166534; color: white;">
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Semester</th>
                <th>Payment Plan</th>
                <th>Enrolled On</th>
            </tr>
        """
        for s in all_students:
            html += f"""
            <tr>
                <td>{s['full_name']}</td>
                <td>{s['email']}</td>
                <td>{s['phone']}</td>
                <td>{s['semester']}</td>
                <td>{s['payment_plan']}</td>
                <td>{s['enrollment_date']}</td>
            </tr>
            """
        html += "</table>"
    html += "</div>"
    return html

if __name__ == "__main__":
    app.run()
