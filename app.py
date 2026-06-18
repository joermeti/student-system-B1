from flask import Flask, request, redirect, url_for, flash, session, get_flashed_messages
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "secret_key"
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db()
        conn.execute('''CREATE TABLE IF NOT EXISTS students
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      full_name TEXT, 
                      email TEXT UNIQUE, 
                      password TEXT, 
                      contractor_email TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS instructors
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      full_name TEXT, 
                      email TEXT UNIQUE, 
                      password TEXT, 
                      role TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS grades_hours
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      student_id INTEGER,
                      module_name TEXT,
                      grade TEXT,
                      hours_attended INTEGER,
                      recorded_by TEXT,
                      recorded_date TEXT,
                      FOREIGN KEY(student_id) REFERENCES students(id))''')
        conn.commit()
        conn.close()

init_db()

# ==================== MASTER LAYOUT ENGINE ====================
def get_header(title="Portal"):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RMETI - {title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; color: #1f2937; }}
        .btn-green {{ background-color: #166534; color: white; padding: 0.6rem 1.2rem; border-radius: 0.375rem; font-weight: 600; text-align: center; display: inline-block; cursor: pointer; border: none; transition: background-color 0.2s; }}
        .btn-green:hover {{ background-color: #14532d; }}
        .btn-dark {{ background-color: #1f2937; color: white; padding: 0.6rem 1.2rem; border-radius: 0.375rem; font-weight: 600; text-align: center; display: inline-block; cursor: pointer; border: none; transition: background-color 0.2s; }}
        .btn-dark:hover {{ background-color: #111827; }}
        .input-box {{ width: 100%; border: 1px solid #d1d5db; border-radius: 0.375rem; padding: 0.6rem 0.75rem; outline: none; font-size: 1rem; background-color: #fff; }}
        .input-box:focus {{ border-color: #166534; box-shadow: 0 0 0 1px #166534; }}
        .card {{ background-color: white; border-radius: 0.5rem; padding: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e5e7eb; margin-bottom: 1.5rem; }}
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <header class="bg-white shadow border-b-4 border-green-800">
        <div class="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-bold text-green-800 tracking-tight">RMETI</h1>
                <p class="text-sm text-gray-600 font-medium">Rocky Mountain Electrical Training Institute</p>
            </div>
            <div>
                <img src="/static/rmeti-logo.png" onerror="this.onerror=null; this.src='/static/logo.jpg';" alt="RMETI Logo" class="h-16 w-auto">
            </div>
        </div>
    </header>
    <main class="flex-grow max-w-5xl mx-auto px-6 py-10 w-full">
"""

FOOTER = """
    </main>
    <footer class="bg-gray-800 text-white py-6 mt-10">
        <div class="max-w-5xl mx-auto px-6 text-center">
            <p>&copy; 2024 Rocky Mountain Electrical Training Institute. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
"""

def render_page(title, content):
    return get_header(title) + content + FOOTER

@app.route("/")
def home():
    content = f"""
    <div class="text-center py-12">
        <h2 class="text-4xl font-extrabold text-gray-900 mb-6">Welcome to the RMETI Student Portal</h2>
        <p class="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">Access your grades, track your hours, and manage your electrical training records in one secure location.</p>
        <div class="flex justify-center gap-4">
            <a href="{url_for('login')}" class="btn-green text-lg px-8 py-3">Login to Dashboard</a>
            <a href="{url_for('register_student')}" class="btn-dark text-lg px-8 py-3">Register as Student</a>
        </div>
    </div>
    """
    return render_page("Welcome", content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        conn = get_db()
        
        # Check students
        student = conn.execute("SELECT * FROM students WHERE email = ? AND password = ?", (email, password)).fetchone()
        if student:
            session["role"] = "student"
            session["student_id"] = student["id"]
            session["name"] = student["full_name"]
            conn.close()
            return redirect(url_for("student_dashboard"))
            
        # Check instructors/contractors
        instructor = conn.execute("SELECT * FROM instructors WHERE email = ? AND password = ?", (email, password)).fetchone()
        if instructor:
            session["role"] = instructor["role"]
            session["identifier"] = instructor["email"]
            session["name"] = instructor["full_name"]
            conn.close()
            if instructor["role"] == "contractor":
                return redirect(url_for("contractor_dashboard"))
            return redirect(url_for("instructor_dashboard"))
            
        conn.close()
        flash("Invalid credentials")
    
    content = f"""
    <div class="max-w-md mx-auto card">
        <h2 class="text-2xl font-bold mb-6 text-center">Sign In</h2>
        <form method="POST">
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Email Address</label>
                <input type="email" name="email" class="input-box" required>
            </div>
            <div class="mb-6">
                <label class="block text-sm font-bold mb-2">Password</label>
                <input type="password" name="password" class="input-box" required>
            </div>
            <button type="submit" class="btn-green w-full py-3">Login</button>
        </form>
    </div>
    """
    return render_page("Login", content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        c_email = request.form.get("contractor_email")
        conn = get_db()
        try:
            conn.execute("INSERT INTO students (full_name, email, password, contractor_email) VALUES (?, ?, ?, ?)",
                         (name, email, password, c_email))
            conn.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for("login"))
        except:
            flash("Email already exists")
        finally:
            conn.close()
    
    content = f"""
    <div class="max-w-md mx-auto card">
        <h2 class="text-2xl font-bold mb-6 text-center">Student Registration</h2>
        <form method="POST">
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Full Name</label>
                <input type="text" name="full_name" class="input-box" required>
            </div>
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Email Address</label>
                <input type="email" name="email" class="input-box" required>
            </div>
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Password</label>
                <input type="password" name="password" class="input-box" required>
            </div>
            <div class="mb-6">
                <label class="block text-sm font-bold mb-2">Contractor Email (Optional)</label>
                <input type="email" name="contractor_email" class="input-box">
            </div>
            <button type="submit" class="btn-green w-full">Register</button>
        </form>
    </div>
    """
    return render_page("Student Registration", content)

@app.route("/register_instructor", methods=["GET", "POST"])
def register_instructor():
    if request.method == "POST":
        name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        conn = get_db()
        try:
            conn.execute("INSERT INTO instructors (full_name, email, password, role) VALUES (?, ?, ?, ?)",
                         (name, email, password, role))
            conn.commit()
            flash("Registration successful!")
            return redirect(url_for("login"))
        except:
            flash("Error during registration")
        finally:
            conn.close()
            
    content = f"""
    <div class="max-w-md mx-auto card">
        <h2 class="text-2xl font-bold mb-6 text-center">Staff Registration</h2>
        <form method="POST">
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Full Name</label>
                <input type="text" name="full_name" class="input-box" required>
            </div>
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Email Address</label>
                <input type="email" name="email" class="input-box" required>
            </div>
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Password</label>
                <input type="password" name="password" class="input-box" required>
            </div>
            <div class="mb-6">
                <label class="block text-sm font-bold mb-2">Role</label>
                <select name="role" class="input-box">
                    <option value="instructor">Instructor</option>
                    <option value="contractor">Contractor</option>
                </select>
            </div>
            <button type="submit" class="btn-green w-full">Register</button>
        </form>
    </div>
    """
    return render_page("Staff Registration", content)

@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    student_id = session.get("student_id")
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    # QUERY GRADES AND HOURS
    grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (student_id,)).fetchall()
    conn.close()
    
    grade_rows = ""
    for g in grades:
        grade_rows += f"""
        <tr>
            <td class="px-6 py-4 border-b">{g['module_name']}</td>
            <td class="px-6 py-4 border-b font-bold">{g['grade']}</td>
            <td class="px-6 py-4 border-b">{g['hours_attended']}</td>
            <td class="px-6 py-4 border-b text-sm text-gray-500">{g['recorded_date']}</td>
        </tr>
        """
    
    if not grade_rows:
        grade_rows = "<tr><td colspan='4' class='px-6 py-10 text-center text-gray-500'>No records found yet.</td></tr>"

    content = f"""
    <div class="flex justify-between items-center mb-8">
        <h2 class="text-3xl font-bold">Welcome, {student['full_name']}</h2>
        <a href="{url_for('logout')}" class="btn-dark">Logout</a>
    </div>
    <div class="card">
        <h3 class="text-xl font-bold mb-4 border-b pb-2">Your Academic Records</h3>
        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-gray-50">
                        <th class="px-6 py-3 border-b font-bold text-gray-700">Module</th>
                        <th class="px-6 py-3 border-b font-bold text-gray-700">Grade</th>
                        <th class="px-6 py-3 border-b font-bold text-gray-700">Hours</th>
                        <th class="px-6 py-3 border-b font-bold text-gray-700">Date</th>
                    </tr>
                </thead>
                <tbody>
                    {grade_rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_page("Student Dashboard", content)

@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor":
        return redirect(url_for("login"))
    email = session.get("identifier")
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name", (email,)).fetchall()
    
    student_cards = ""
    for s in students:
        # QUERY GRADES FOR EACH STUDENT
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
        
        grade_list = ""
        for g in grades:
            grade_list += f"""
            <div class="flex justify-between items-center py-2 border-b last:border-0">
                <span class="font-medium">{g['module_name']}</span>
                <span class="text-gray-600">Grade: <span class="font-bold">{g['grade']}</span> | Hours: {g['hours_attended']}</span>
            </div>
            """
        
        if not grade_list:
            grade_list = "<p class='text-gray-400 italic py-2'>No data recorded.</p>"

        student_cards += f"""
        <div class="card p-6 border-l-4 border-green-700">
            <h4 class="text-xl font-bold text-green-900 mb-3">{s['full_name']}</h4>
            <p class="text-sm text-gray-500 mb-4">{s['email']}</p>
            <div class="bg-gray-50 p-4 rounded-md">
                <h5 class="text-xs font-bold uppercase text-gray-400 tracking-wider mb-2">Performance History</h5>
                {grade_list}
            </div>
        </div>
        """
        
    conn.close()
    
    if not student_cards:
        student_cards = "<div class='card text-center py-10 text-gray-500'>No students found linked to your email.</div>"

    content = f"""
    <div class="flex justify-between items-center mb-8">
        <h2 class="text-3xl font-bold">Contractor Portal: {session.get('name')}</h2>
        <a href="{url_for('logout')}" class="btn-dark">Logout</a>
    </div>
    <div class="mb-6">
        <h3 class="text-xl font-semibold text-gray-700">Your Sponsored Students</h3>
        <p class="text-gray-500">Overview of grades and attendance hours for your team.</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {student_cards}
    </div>
    """
    return render_page("Contractor Dashboard", content)

@app.route("/instructor", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))
    
    conn = get_db()
    if request.method == "POST":
        s_id = request.form.get("student_id")
        module = request.form.get("module")
        grade = request.form.get("grade")
        hours = request.form.get("hours")
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        conn.execute("INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date) VALUES (?, ?, ?, ?, ?, ?)",
                     (s_id, module, grade, hours, session.get("name"), date))
        conn.commit()
        flash("Record added successfully!")

    students = conn.execute("SELECT * FROM students ORDER BY full_name").fetchall()
    conn.close()
    
    s_options = "".join([f'<option value="{s["id"]}">{s["full_name"]} ({s["email"]})</option>' for s in students])
    
    content = f"""
    <div class="flex justify-between items-center mb-8">
        <h2 class="text-3xl font-bold">Instructor Console</h2>
        <a href="{url_for('logout')}" class="btn-dark">Logout</a>
    </div>
    <div class="max-w-2xl card">
        <h3 class="text-xl font-bold mb-6">Record New Grades & Hours</h3>
        <form method="POST">
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Select Student</label>
                <select name="student_id" class="input-box" required>
                    {s_options}
                </select>
            </div>
            <div class="mb-4">
                <label class="block text-sm font-bold mb-2">Module Name</label>
                <input type="text" name="module" class="input-box" placeholder="e.g. Electrical Theory 101" required>
            </div>
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div>
                    <label class="block text-sm font-bold mb-2">Grade / Score</label>
                    <input type="text" name="grade" class="input-box" placeholder="e.g. 95% or A" required>
                </div>
                <div>
                    <label class="block text-sm font-bold mb-2">Hours Attended</label>
                    <input type="number" name="hours" class="input-box" placeholder="e.g. 40" required>
                </div>
            </div>
            <button type="submit" class="btn-green w-full py-3">Submit Record</button>
        </form>
    </div>
    """
    return render_page("Instructor Dashboard", content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
