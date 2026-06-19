from flask import Flask, request, redirect, url_for, flash, session, get_flashed_messages
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
    c.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, email TEXT UNIQUE, phone TEXT, program TEXT, payment_plan TEXT, contractor_name TEXT, contractor_email TEXT, enrollment_date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS grades_hours (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, module_name TEXT, grade TEXT, hours_attended INTEGER, recorded_by TEXT, recorded_date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS instructors (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
    conn.commit()
    conn.close()

init_db()

# ==================== RENDER HELPER ====================
def render_page(title, content):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>RMETI - {title}</title>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <header class="bg-white shadow border-b-4 border-emerald-800">
            <div class="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-emerald-800">RMETI</h1>
                    <p class="text-xs text-gray-500">Apprentice Portal</p>
                </div>
                <img src="/static/logo.jpg" onerror="this.onerror=null; this.src='/static/rmeti-logo.png';" class="h-12 w-auto" alt="Logo">
            </div>
        </header>
        <main class="max-w-5xl mx-auto px-6 py-8">{content}</main>
    </body>
    </html>
    """

# ==================== ROUTES ====================
@app.route("/")
def home():
    content = '<div class="text-center"><h2 class="text-xl mb-4">Welcome to RMETI</h2><a href="/enroll" class="bg-emerald-700 text-white px-4 py-2 rounded">Enroll</a> <a href="/login" class="bg-gray-800 text-white px-4 py-2 rounded">Login</a></div>'
    return render_page("Home", content)

@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        conn = get_db()
        conn.execute("INSERT INTO students (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, enrollment_date) VALUES (?,?,?,?,?,?,?,?)",
                     (request.form['full_name'], request.form['email'], request.form['phone'], request.form['program'], request.form['payment_plan'], request.form['contractor_name'], request.form['contractor_email'], datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        return redirect(url_for("home"))
    
    content = """
    <form method="POST" class="max-w-lg mx-auto bg-white p-6 rounded shadow space-y-3">
        <input name="full_name" placeholder="Full Name" required class="w-full p-2 border rounded">
        <input name="email" placeholder="Email" required class="w-full p-2 border rounded">
        <select name="program" class="w-full p-2 border rounded"><option>Fast Track Journeyman semester 1</option><option>Main Program semester 1</option></select>
        <select name="payment_plan" class="w-full p-2 border rounded">
            <optgroup label="Fast Track"><option>4-Month Plan</option><option>5-Month Plan</option><option>6-Month Plan</option><option>Paid in Full</option></optgroup>
            <optgroup label="Main Program"><option>4-Month Plan to 12-Month Plan</option><option>Paid in Full</option></optgroup>
        </select>
        <input name="contractor_email" placeholder="Contractor Email" class="w-full p-2 border rounded">
        <button type="submit" class="bg-emerald-700 text-white w-full p-2 rounded">Enroll</button>
    </form>
    """
    return render_page("Enroll", content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role, idnt = request.form['role'], request.form['identifier']
        if role == "instructor":
            conn = get_db()
            inst = conn.execute("SELECT * FROM instructors WHERE username = ?", (idnt,)).fetchone()
            conn.close()
            if inst and inst['password'] == request.form['password']:
                session.update({'role': role, 'identifier': idnt})
                return redirect(url_for('instructor_dashboard'))
        else:
            session.update({'role': role, 'identifier': idnt})
            return redirect(url_for(f'{role}_dashboard'))
    return render_page("Login", '<form method="POST" class="max-w-xs mx-auto space-y-3"><select name="role" class="w-full p-2 border"><option value="student">Student</option><option value="contractor">Contractor</option><option value="instructor">Instructor</option></select><input name="identifier" class="w-full p-2 border"><input type="password" name="password" class="w-full p-2 border"><button type="submit" class="w-full bg-emerald-700 text-white p-2 rounded">Login</button></form>')

@app.route("/student_dashboard")
def student_dashboard():
    conn = get_db()
    s = conn.execute("SELECT * FROM students WHERE email = ?", (session['identifier'],)).fetchone()
    grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ?", (s['id'],)).fetchall() if s else []
    conn.close()
    html = f"<h2>Welcome {s['full_name']}</h2>" + "".join([f"<p>{g['module_name']}: {g['grade']} ({g['hours_attended']} hrs)</p>" for g in grades])
    return render_page("Dashboard", html + "<a href='/logout'>Logout</a>")

@app.route("/contractor_dashboard")
def contractor_dashboard():
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ?", (session['identifier'],)).fetchall()
    html = "<h2>Apprentices</h2>"
    for s in students:
        html += f"<h3>{s['full_name']}</h3>" + "".join([f"<p>{g['module_name']}: {g['grade']} ({g['hours_attended']} hrs)</p>" for g in conn.execute("SELECT * FROM grades_hours WHERE student_id = ?", (s['id'],)).fetchall()])
    conn.close()
    return render_page("Contractor", html + "<a href='/logout'>Logout</a>")

@app.route("/instructor_dashboard", methods=["GET", "POST"])
def instructor_dashboard():
    conn = get_db()
    if request.method == "POST":
        conn.execute("INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date) VALUES (?,?,?,?,?,?)", (request.form['student_id'], request.form['mod'], request.form['grd'], request.form['hrs'], session['identifier'], datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    students = conn.execute("SELECT * FROM students").fetchall()
    html = "<h2>Instructor Dashboard</h2>"
    for s in students:
        html += f"<h3>{s['full_name']}</h3><form method='POST'><input type='hidden' name='student_id' value='{s['id']}'><input name='mod' placeholder='Module'><input name='grd' placeholder='Grade'><input name='hrs' placeholder='Hours'><button type='submit'>Save</button></form>"
    conn.close()
    return render_page("Instructor", html + "<a href='/logout'>Logout</a>")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('home'))

if __name__ == "__main__": app.run(debug=True)
