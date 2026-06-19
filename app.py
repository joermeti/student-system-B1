from flask import Flask, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "rmeti-secret-2026"

def get_db():
    conn = sqlite3.connect("rmeti_portal.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, email TEXT UNIQUE, phone TEXT, program TEXT, payment_plan TEXT, contractor_name TEXT, contractor_email TEXT, enrollment_date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS grades_hours (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, module_name TEXT, grade TEXT, hours_attended INTEGER, recorded_by TEXT, recorded_date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS instructors (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)""")
    conn.commit()
    conn.close()

init_db()

# ==================== HOME ====================
@app.route("/")
def home():
    return """
    <div class="max-w-5xl mx-auto px-6 py-12"><h1 class="text-5xl font-bold text-emerald-700">RMETI Portal</h1>
    <div class="mt-8 space-x-4"><a href="/enroll" class="bg-emerald-600 text-white px-6 py-3 rounded-lg">Enroll Student</a>
    <a href="/login" class="bg-gray-800 text-white px-6 py-3 rounded-lg">Login</a></div></div>
    """

# ==================== ENROLL ====================
@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        conn = get_db()
        try:
            conn.execute("INSERT INTO students (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, enrollment_date) VALUES (?,?,?,?,?,?,?,?)",
                         (request.form['full_name'], request.form['email'], request.form['phone'], request.form['program'], request.form['payment_plan'], request.form['contractor_name'], request.form['contractor_email'], datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            return redirect(url_for("success"))
        finally: conn.close()
    
    return """
    <form method="POST" class="max-w-lg mx-auto space-y-4">
        <input name="full_name" placeholder="Full Name" required class="w-full p-2 border">
        <input name="email" placeholder="Email" required class="w-full p-2 border">
        <select name="program" class="w-full p-2 border">
            <option>Fast Track Journeyman semester 1</option><option>Fast Track Journeyman semester 2</option>
            <option>Main Program semester 1</option><option>Main Program semester 2</option>
            <option>Main Program semester 3</option><option>Main Program semester 4</option>
        </select>
        <select name="payment_plan" class="w-full p-2 border">
            <optgroup label="Fast Track"><option>4-Month Plan</option><option>5-Month Plan</option><option>6-Month Plan</option><option>Paid in Full</option></optgroup>
            <optgroup label="Main Program"><option>4-Month Plan</option><option>5-Month Plan</option><option>6-Month Plan</option><option>7-Month Plan</option><option>8-Month Plan</option><option>9-Month Plan</option><option>10-Month Plan</option><option>11-Month Plan</option><option>12-Month Plan</option><option>Paid in Full</option></optgroup>
        </select>
        <input name="contractor_email" placeholder="Contractor Email" class="w-full p-2 border">
        <button type="submit" class="bg-emerald-700 text-white p-2 w-full">Enroll</button>
    </form>
    """

@app.route("/success")
def success(): return "<h2>Success!</h2><a href='/'>Home</a>"

# ==================== LOGIN & DASHBOARDS ====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form['role']
        idnt = request.form['identifier']
        if role == "instructor":
            conn = get_db()
            inst = conn.execute("SELECT * FROM instructors WHERE username = ?", (idnt,)).fetchone()
            conn.close()
            if inst and inst['password'] == request.form['password']:
                session.update({'role': role, 'identifier': idnt})
                return redirect(url_for('instructor_dashboard'))
        elif role == "student":
            session.update({'role': role, 'identifier': idnt})
            return redirect(url_for('student_dashboard'))
        elif role == "contractor":
            session.update({'role': role, 'identifier': idnt})
            return redirect(url_for('contractor_dashboard'))
    return '<form method="POST"><select name="role"><option value="student">Student</option><option value="contractor">Contractor</option><option value="instructor">Instructor</option></select><input name="identifier"><input type="password" name="password"><button type="submit">Login</button></form>'

@app.route("/student_dashboard")
def student_dashboard():
    conn = get_db()
    s = conn.execute("SELECT * FROM students WHERE email = ?", (session['identifier'],)).fetchone()
    grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ?", (s['id'],)).fetchall() if s else []
    conn.close()
    html = f"<h2>Welcome {s['full_name']}</h2>"
    for g in grades: html += f"<p>{g['module_name']}: {g['grade']} ({g['hours_attended']} hrs)</p>"
    return html + "<a href='/logout'>Logout</a>"

@app.route("/contractor_dashboard")
def contractor_dashboard():
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ?", (session['identifier'],)).fetchall()
    html = "<h2>Your Apprentices</h2>"
    for s in students:
        html += f"<h3>{s['full_name']}</h3>"
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ?", (s['id'],)).fetchall()
        for g in grades: html += f"<p>{g['module_name']}: {g['grade']} ({g['hours_attended']} hrs)</p>"
    conn.close()
    return html + "<a href='/logout'>Logout</a>"

@app.route("/instructor_dashboard", methods=["GET", "POST"])
def instructor_dashboard():
    conn = get_db()
    if request.method == "POST":
        conn.execute("INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date) VALUES (?,?,?,?,?,?)",
                     (request.form['student_id'], request.form['mod'], request.form['grd'], request.form['hrs'], session['identifier'], datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    students = conn.execute("SELECT * FROM students").fetchall()
    html = "<h2>Instructor Dashboard</h2>"
    for s in students:
        html += f"<h3>{s['full_name']} ({s['program']})</h3><form method='POST'><input type='hidden' name='student_id' value='{s['id']}'><input name='mod' placeholder='Module'><input name='grd' placeholder='Grade'><input name='hrs' placeholder='Hours'><button type='submit'>Save</button></form>"
    conn.close()
    return html + "<a href='/logout'>Logout</a>"

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('home'))

if __name__ == "__main__": app.run(debug=True)
