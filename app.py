from flask import Flask, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "rmeti-secret-2026"

# ==================== DATABASE ====================
def get_db():
    conn = sqlite3.connect("rmeti_portal.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT, program TEXT, payment_plan TEXT, contractor_name TEXT, contractor_email TEXT, enrollment_date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS grades_hours (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, module_name TEXT, grade TEXT, hours_attended INTEGER, recorded_by TEXT, recorded_date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS instructors (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)")
    conn.commit()
    conn.close()

init_db()

# ==================== LAYOUT ENGINE ====================
def render_page(title, body):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>RMETI - {title}</title>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <header class="bg-white border-b-4 border-emerald-700 shadow-sm">
            <div class="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold text-emerald-800">RMETI</h1>
                    <p class="text-sm text-gray-500">Student Portal</p>
                </div>
                <img src="/static/logo.jpg" class="h-16 w-auto" alt="Logo">
            </div>
        </header>
        <main class="max-w-6xl mx-auto px-6 py-8">
            {body}
        </main>
    </body>
    </html>
    """

# ==================== ROUTES ====================
@app.route("/")
def home():
    content = """
    <div class="bg-white p-8 rounded-xl shadow border border-gray-100 max-w-2xl mx-auto text-center">
        <h2 class="text-2xl font-bold mb-6">Welcome to RMETI</h2>
        <div class="space-x-4">
            <a href="/enroll" class="bg-emerald-700 text-white px-6 py-3 rounded-lg font-semibold hover:bg-emerald-800">Enroll Student</a>
            <a href="/login" class="bg-gray-800 text-white px-6 py-3 rounded-lg font-semibold hover:bg-black">Login</a>
        </div>
    </div>
    """
    return render_page("Home", content)

@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        f = request.form
        conn = get_db()
        try:
            conn.execute("INSERT INTO students (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, enrollment_date) VALUES (?,?,?,?,?,?,?,?)",
                         (f['full_name'], f['email'], f['phone'], f['program'], f['payment_plan'], f['contractor_name'], f['contractor_email'], datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            return redirect(url_for("success"))
        finally: conn.close()
    
    content = """
    <div class="bg-white p-8 rounded-xl shadow border max-w-2xl mx-auto">
        <h2 class="text-xl font-bold mb-6">Enroll Student</h2>
        <form method="POST" class="space-y-4">
            <input type="text" name="full_name" placeholder="Full Name" required class="w-full p-3 border rounded">
            <input type="email" name="email" placeholder="Email" required class="w-full p-3 border rounded">
            <select name="program" class="w-full p-3 border rounded">
                <option>Fast Track Journeyman semester 1</option><option>Fast Track Journeyman semester 2</option>
                <option>Main Program semester 1</option><option>Main Program semester 2</option>
                <option>Main Program semester 3</option><option>Main Program semester 4</option>
            </select>
            <select name="payment_plan" class="w-full p-3 border rounded">
                <optgroup label="Fast Track"><option>4-Month Plan</option><option>5-Month Plan</option><option>6-Month Plan</option><option>Paid in Full</option></optgroup>
                <optgroup label="Main Program"><option>4-Month Plan</option><option>5-Month Plan</option><option>6-Month Plan</option><option>7-Month Plan</option><option>8-Month Plan</option><option>9-Month Plan</option><option>10-Month Plan</option><option>11-Month Plan</option><option>12-Month Plan</option><option>Paid in Full</option></optgroup>
            </select>
            <button type="submit" class="w-full bg-emerald-700 text-white p-3 rounded font-bold">Enroll</button>
        </form>
    </div>
    """
    return render_page("Enroll", content)

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
            conn = get_db()
            stud = conn.execute("SELECT * FROM students WHERE email = ?", (idnt,)).fetchone()
            conn.close()
            if stud:
                session.update({'role': role, 'student_id': stud['id']})
                return redirect(url_for('student_dashboard'))
        elif role == "contractor":
            session.update({'role': role, 'identifier': idnt})
            return redirect(url_for('contractor_dashboard'))
    return render_page("Login", '<div class="max-w-md mx-auto bg-white p-8 rounded shadow"><h2 class="text-xl font-bold mb-4">Login</h2><form method="POST"><select name="role" class="w-full p-2 border mb-4"><option value="student">Student</option><option value="contractor">Contractor</option><option value="instructor">Instructor</option></select><input type="text" name="identifier" placeholder="ID/Email" class="w-full p-2 border mb-4"><input type="password" name="password" placeholder="Password (Instructors)" class="w-full p-2 border mb-4"><button type="submit" class="w-full bg-emerald-700 text-white p-2 rounded">Login</button></form></div>')

@app.route("/student")
def student_dashboard():
    if session.get('role') != 'student': return redirect(url_for('login'))
    conn = get_db()
    s = conn.execute("SELECT * FROM students WHERE id = ?", (session['student_id'],)).fetchone()
    conn.close()
    return render_page("Dashboard", f'<div class="card"><h2 class="text-xl font-bold mb-4">Welcome {s["full_name"]}</h2><p>Program: {s["program"]}</p><p>Plan: {s["payment_plan"]}</p><a href="/logout">Logout</a></div>')

@app.route("/instructor", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get('role') != 'instructor': return redirect(url_for('login'))
    conn = get_db()
    if request.method == "POST":
        conn.execute("INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date) VALUES (?,?,?,?,?,?)",
                     (request.form['student_id'], request.form['mod'], request.form['grd'], request.form['hrs'], session['identifier'], datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    students = conn.execute("SELECT * FROM students").fetchall()
    html = '<h2 class="text-xl font-bold mb-4">Instructor Dashboard</h2>'
    for s in students:
        html += f'<div class="card"><h3 class="font-bold">{s["full_name"]}</h3><form method="POST"><input type="hidden" name="student_id" value="{s["id"]}"><input name="mod" placeholder="Module"><input name="grd" placeholder="Grade"><input name="hrs" placeholder="Hours"><button type="submit">Save</button></form></div>'
    conn.close()
    return render_page("Instructor", html)

@app.route("/success")
def success(): return render_page("Success", "<h2>Done!</h2><a href='/'>Home</a>")
@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('home'))

if __name__ == "__main__": app.run(debug=True)
