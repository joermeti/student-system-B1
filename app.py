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
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT,
            program TEXT, payment_plan TEXT, contractor_name TEXT, contractor_email TEXT, enrollment_date TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, module_name TEXT, grade TEXT,
            hours_attended INTEGER, recorded_by TEXT, recorded_date TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==================== MASTER LAYOUT ENGINE ====================
def get_header(title="Portal"):
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RMETI - """ + title + """</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; color: #1f2937; }
            .btn-green { background-color: #166534; color: white; padding: 0.6rem 1.2rem; border-radius: 0.375rem; font-weight: 600; text-align: center; display: inline-block; cursor: pointer; border: none; transition: background-color 0.2s; }
            .btn-green:hover { background-color: #14532d; }
            .btn-dark { background-color: #1f2937; color: white; padding: 0.6rem 1.2rem; border-radius: 0.375rem; font-weight: 600; text-align: center; display: inline-block; cursor: pointer; border: none; transition: background-color 0.2s; }
            .btn-dark:hover { background-color: #111827; }
            .input-box { width: 100%; border: 1px solid #d1d5db; border-radius: 0.375rem; padding: 0.6rem 0.75rem; outline: none; font-size: 1rem; background-color: #fff; }
            .input-box:focus { border-color: #166534; box-shadow: 0 0 0 1px #166534; }
            .card { background-color: white; border-radius: 0.5rem; padding: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e5e7eb; margin-bottom: 1.5rem; }
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
    </body>
    </html>
"""

def render_page(title, body_content):
    messages = get_flashed_messages()
    flash_html = ""
    if messages:
        flash_html = '<div class="mb-6 p-4 bg-green-50 text-green-800 rounded-md border border-green-200 shadow-sm">'
        for msg in messages:
            flash_html += f'<p class="font-medium">{msg}</p>'
        flash_html += '</div>'
    return get_header(title) + flash_html + body_content + FOOTER

# ==================== HOME ====================
@app.route("/")
def home():
    content = """
    <div class="flex justify-between items-center mb-8">
        <h2 class="text-2xl font-semibold text-gray-800">Welcome to the Portal</h2>
        <div class="space-x-3">
            <a href="/enroll" class="btn-green">Enroll Student</a>
            <a href="/login" class="btn-dark">Login</a>
        </div>
    </div>
    <div class="card">
        <p class="text-gray-600">Please select an option above to get started.</p>
    </div>
    """
    return render_page("Home", content)

# ==================== ENROLL ====================
@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        program = request.form.get("program", "").strip()
        payment_plan = request.form.get("payment_plan", "").strip()
        contractor_name = request.form.get("contractor_name", "").strip()
        contractor_email = request.form.get("contractor_email", "").strip()

        if not full_name or not email or not program:
            flash("Full Name, Email, and Program are required.")
            return redirect(url_for("enroll"))

        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO students (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            flash("Student enrolled successfully!")
            return redirect(url_for("success"))
        except sqlite3.IntegrityError:
            flash("A student with this email already exists.")
        finally:
            conn.close()

    content = """
    <div class="card max-w-2xl mx-auto">
        <h2 class="text-xl font-bold text-green-800 mb-6">Enroll New Student</h2>
        <form method="POST" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-1">Full Name *</label>
                    <input type="text" name="full_name" required class="input-box">
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-1">Email *</label>
                    <input type="email" name="email" required class="input-box">
                </div>
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Phone</label>
                <input type="text" name="phone" class="input-box">
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Program *</label>
                <select name="program" required class="input-box bg-white">
                    <option value="">-- Select Program --</option>
                    <option>Fast Track Journeyman semester 1</option>
                    <option>Fast Track Journeyman semester 2</option>
                    <option>Main Program semester 1</option>
                    <option>Main Program semester 2</option>
                    <option>Main Program semester 3</option>
                    <option>Main Program semester 4</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Payment Plan *</label>
                <select name="payment_plan" required class="input-box bg-white">
                    <option value="">-- Select Payment Plan --</option>
                    <optgroup label="Fast Track Journeyman">
                        <option>4-Month Payment Plan</option>
                        <option>5-Month Payment Plan</option>
                        <option>6-Month Payment Plan</option>
                    </optgroup>
                    <optgroup label="Main Program">
                        <option>4-Month Payment Plan</option>
                        <option>5-Month Payment Plan</option>
                        <option>6-Month Payment Plan</option>
                        <option>7-Month Payment Plan</option>
                        <option>8-Month Payment Plan</option>
                        <option>9-Month Payment Plan</option>
                        <option>10-Month Payment Plan</option>
                        <option>11-Month Payment Plan</option>
                        <option>12-Month Payment Plan</option>
                    </optgroup>
                    <optgroup label="Other">
                        <option>Paid In Full</option>
                    </optgroup>
                </select>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-1">Contractor Name</label>
                    <input type="text" name="contractor_name" class="input-box">
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-1">Contractor Email</label>
                    <input type="email" name="contractor_email" class="input-box">
                </div>
            </div>
            <button type="submit" class="btn-green w-full mt-2">Enroll Student</button>
        </form>
    </div>
    """
    return render_page("Enroll", content)

@app.route("/success")
def success():
    content = """
    <div class="card max-w-md mx-auto text-center py-8">
        <h2 class="text-2xl font-bold text-green-700 mb-6">Enrollment Successful!</h2>
        <div class="space-x-4">
            <a href="/enroll" class="text-green-700 hover:underline font-medium">Enroll Another</a>
            <a href="/login" class="text-green-700 hover:underline font-medium">Go to Login</a>
        </div>
    </div>
    """
    return render_page("Success", content)

# ==================== LOGIN ====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        if role == "instructor":
            conn = get_db()
            instructor = conn.execute("SELECT * FROM instructors WHERE username = ?", (identifier,)).fetchone()
            conn.close()
            if not instructor or instructor["password"] != password:
                flash("Invalid instructor username or password.")
                return redirect(url_for("login"))
        elif role == "student":
            conn = get_db()
            student = conn.execute("SELECT * FROM students WHERE email = ?", (identifier,)).fetchone()
            conn.close()
            if student:
                session["student_id"] = student["id"]
            else:
                flash("No student found with that email address.")
                return redirect(url_for("login"))
                
        session["role"] = role
        session["identifier"] = identifier
        return redirect(url_for(f"{role}_dashboard"))

    content = """
    <div class="card max-w-md mx-auto mt-4">
        <h2 class="text-xl font-bold text-green-800 mb-6 text-center">Secure Login</h2>
        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">I am a</label>
                <select name="role" id="role" class="input-box bg-white" onchange="togglePassword()">
                    <option value="student">Student</option>
                    <option value="contractor">Contractor</option>
                    <option value="instructor">Instructor</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Email or Username</label>
                <input type="text" name="identifier" required class="input-box">
            </div>
            <div id="passwordField" style="display: none;">
                <label class="block text-sm font-bold text-gray-700 mb-1">Password</label>
                <input type="password" name="password" class="input-box">
            </div>
            <button type="submit" class="btn-green w-full mt-2">Sign In</button>
        </form>
        <div class="mt-4 text-center">
            <a href="/register_instructor" class="text-sm text-green-700 hover:underline">Register as Instructor</a>
        </div>
    </div>
    <script>
        function togglePassword() {
            const role = document.getElementById('role').value;
            document.getElementById('passwordField').style.display = (role === 'instructor') ? 'block' : 'none';
        }
        window.onload = togglePassword;
    </script>
    """
    return render_page("Login", content)

# ==================== REGISTER & PASSWORD ====================
@app.route("/register_instructor", methods=["GET", "POST"])
def register_instructor():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register_instructor"))
        conn = get_db()
        try:
            conn.execute("INSERT INTO instructors (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Instructor account created successfully!")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username is already taken.")
        finally:
            conn.close()

    content = """
    <div class="card max-w-md mx-auto mt-4">
        <h2 class="text-xl font-bold text-green-800 mb-6 text-center">Register as Instructor</h2>
        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Choose Username</label>
                <input type="text" name="username" required class="input-box">
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Choose Password</label>
                <input type="password" name="password" required class="input-box">
            </div>
            <button type="submit" class="btn-green w-full mt-2">Create Account</button>
        </form>
        <div class="mt-4 text-center">
            <a href="/login" class="text-sm text-green-700 hover:underline">Back to Login</a>
        </div>
    </div>
    """
    return render_page("Register Instructor", content)

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        if new_password != confirm_password:
            flash("New passwords do not match.")
            return redirect(url_for("change_password"))
        conn = get_db()
        instructor = conn.execute("SELECT * FROM instructors WHERE username = ?", (session["identifier"],)).fetchone()
        if not instructor or instructor["password"] != current_password:
            flash("Current password is incorrect.")
            conn.close()
            return redirect(url_for("change_password"))
        conn.execute("UPDATE instructors SET password = ? WHERE username = ?", (new_password, session["identifier"]))
        conn.commit()
        conn.close()
        flash("Password changed successfully!")
        return redirect(url_for("instructor_dashboard"))

    content = """
    <div class="card max-w-md mx-auto mt-4">
        <h2 class="text-xl font-bold text-green-800 mb-6">Change Password</h2>
        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Current Password</label>
                <input type="password" name="current_password" required class="input-box">
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">New Password</label>
                <input type="password" name="new_password" required class="input-box">
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Confirm New Password</label>
                <input type="password" name="confirm_password" required class="input-box">
            </div>
            <button type="submit" class="btn-green w-full mt-2">Change Password</button>
        </form>
        <div class="mt-4 text-center">
            <a href="/instructor" class="text-sm text-green-700 hover:underline">Back to Dashboard</a>
        </div>
    </div>
    """
    return render_page("Change Password", content)

# ==================== STUDENT DASHBOARD ====================
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("login"))
        
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (student_id,)).fetchall()
    conn.close()
    
    if not student:
        return redirect(url_for("login"))

    content = f"""
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-800">Welcome, {student['full_name']}</h2>
        <a href="/logout" class="text-red-600 hover:text-red-800 text-sm font-bold">Logout</a>
    </div>
    
    <div class="card">
        <h3 class="text-lg font-bold text-green-800 border-b pb-2 mb-4">Your Information</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-700">
            <div>
                <p class="text-xs text-gray-500 uppercase font-bold tracking-wide">Program</p>
                <p class="font-medium text-base">{student['program']}</p>
            </div>
            <div>
                <p class="text-xs text-gray-500 uppercase font-bold tracking-wide">Payment Plan</p>
                <p class="font-medium text-base">{student['payment_plan']}</p>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h3 class="text-lg font-bold text-green-800 border-b pb-2 mb-4">Your Grades & Hours</h3>
    """
    if grades:
        content += """
        <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
                <thead>
                    <tr class="bg-gray-100 text-gray-600 border-b">
                        <th class="p-3 font-bold rounded-tl-md">Module / Class</th>
                        <th class="p-3 font-bold">Grade</th>
                        <th class="p-3 font-bold">Hours</th>
                        <th class="p-3 font-bold rounded-tr-md">Date Recorded</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
        """
        for g in grades:
            content += f"""
            <tr class="hover:bg-gray-50">
                <td class="p-3 text-gray-800 font-medium">{g['module_name'] or '-'}</td>
                <td class="p-3 text-gray-800">{g['grade'] or '-'}</td>
                <td class="p-3 text-gray-800">{g['hours_attended'] or '-'}</td>
                <td class="p-3 text-gray-500">{g['recorded_date']}</td>
            </tr>
            """
        content += "</tbody></table></div>"
    else:
        content += "<p class='text-sm text-gray-500 italic'>No grades or hours have been recorded yet.</p>"
    content += "</div>"
    return render_page("Student Dashboard", content)

# ==================== CONTRACTOR DASHBOARD ====================
@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor":
        return redirect(url_for("login"))
    email = session.get("identifier")
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name", (email,)).fetchall()
    
    content = f"""
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-800">Your Apprentices</h2>
        <a href="/logout" class="text-red-600 hover:text-red-800 text-sm font-bold">Logout</a>
    </div>
    """
    if students:
        for s in students:
            grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
            content += f"""
            <div class="card">
                <div class="mb-4 border-b pb-3">
                    <h3 class="text-xl font-bold text-green-800">{s['full_name']}</h3>
                    <p class="text-sm text-gray-600 font-medium">{s['program']}</p>
                </div>
                <h4 class="text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide">Grades & Hours</h4>
            """
            if grades:
                content += """
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm border-t border-l border-r">
                        <thead>
                            <tr class="bg-gray-100 text-gray-600 border-b">
                                <th class="p-2 font-bold">Module / Class</th>
                                <th class="p-2 font-bold">Grade</th>
                                <th class="p-2 font-bold">Hours</th>
                                <th class="p-2 font-bold">Date</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
                """
                for g in grades:
                    content += f"""
                    <tr class="hover:bg-gray-50">
                        <td class="p-2 text-gray-800">{g['module_name'] or '-'}</td>
                        <td class="p-2 text-gray-800">{g['grade'] or '-'}</td>
                        <td class="p-2 text-gray-800">{g['hours_attended'] or '-'}</td>
                        <td class="p-2 text-gray-500 text-xs">{g['recorded_date']}</td>
                    </tr>
                    """
                content += "</tbody></table></div>"
            else:
                content += "<p class='text-sm text-gray-500 italic'>No grades recorded yet for this student.</p>"
            content += "</div>"
    else:
        content += "<div class='card'><p class='text-gray-600'>No apprentices found under this email.</p></div>"
        
    conn.close()
    return render_page("Contractor Dashboard", content)

# ==================== INSTRUCTOR DASHBOARD ====================
@app.route("/instructor", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))
        
    conn = get_db()
    students = conn.execute("SELECT * FROM students ORDER BY full_name").fetchall()
    
    if request.method == "POST":
        if "delete_id" in request.form:
            conn.execute("DELETE FROM grades_hours WHERE id = ?", (request.form.get("delete_id"),))
            conn.commit()
            flash("Record deleted.")
        elif "edit_id" in request.form:
            edit_id = request.form.get("edit_id")
            module_name = request.form.get("edit_module_name")
            grade = request.form.get("edit_grade")
            hours = request.form.get("edit_hours_attended") or 0
            conn.execute("""
                UPDATE grades_hours SET module_name = ?, grade = ?, hours_attended = ? WHERE id = ?
            """, (module_name, grade, hours, edit_id))
            conn.commit()
            flash("Record updated successfully.")
        else:
            conn.execute("""
                INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                request.form.get("student_id"), request.form.get("module_name"), request.form.get("grade"), 
                request.form.get("hours_attended") or 0, session.get("identifier", "Instructor"), 
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
            conn.commit()
            flash("Record saved!")

    content = """
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-800">Instructor Dashboard</h2>
        <div class="space-x-4">
            <a href="/change_password" class="text-green-700 hover:text-green-800 text-sm font-bold">Change Password</a>
            <a href="/logout" class="text-red-600 hover:text-red-800 text-sm font-bold">Logout</a>
        </div>
    </div>
    """
    for s in students:
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
        content += f"""
        <div class="card">
            <div class="mb-4">
                <h3 class="text-xl font-bold text-green-800">{s['full_name']}</h3>
                <p class="text-sm text-gray-600 font-medium">{s['program']}</p>
            </div>
            
            <form method="POST" class="flex flex-wrap items-end gap-3 mb-6 bg-green-50 p-4 rounded-lg border border-green-100">
                <input type="hidden" name="student_id" value="{s['id']}">
                <div class="flex-grow">
                    <label class="block text-xs font-bold text-green-900 mb-1 uppercase tracking-wide">Module / Class</label>
                    <input type="text" name="module_name" placeholder="e.g. NEC Ch 1" class="input-box text-sm py-2">
                </div>
                <div class="w-24">
                    <label class="block text-xs font-bold text-green-900 mb-1 uppercase tracking-wide">Grade</label>
                    <input type="text" name="grade" placeholder="A/92" class="input-box text-sm py-2">
                </div>
                <div class="w-24">
                    <label class="block text-xs font-bold text-green-900 mb-1 uppercase tracking-wide">Hours</label>
                    <input type="number" name="hours_attended" placeholder="8" class="input-box text-sm py-2">
                </div>
                <button type="submit" class="btn-green py-2 h-[38px] flex items-center">Add Record</button>
            </form>
        """
        if grades:
            content += """
            <h4 class="text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">Previous Records</h4>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm border">
                    <thead>
                        <tr class="bg-gray-100 text-gray-600 border-b">
                            <th class="p-2 font-bold">Module</th>
                            <th class="p-2 font-bold">Grade</th>
                            <th class="p-2 font-bold">Hours</th>
                            <th class="p-2 font-bold">Date</th>
                            <th class="p-2 font-bold text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
            """
            for g in grades:
                content += f"""
                <tr class="hover:bg-gray-50">
                    <td class="p-2 text-gray-800">{g['module_name'] or '-'}</td>
                    <td class="p-2 text-gray-800">{g['grade'] or '-'}</td>
                    <td class="p-2 text-gray-800">{g['hours_attended'] or '-'}</td>
                    <td class="p-2 text-gray-500 text-xs">{g['recorded_date']}</td>
                    <td class="p-2 text-right whitespace-nowrap">
                        <form method="POST" class="inline-flex items-center gap-1">
                            <input type="hidden" name="edit_id" value="{g['id']}">
                            <input type="text" name="edit_module_name" value="{g['module_name'] or ''}" class="border border-gray-300 rounded px-1.5 py-1 text-xs w-24" placeholder="Mod">
                            <input type="text" name="edit_grade" value="{g['grade'] or ''}" class="border border-gray-300 rounded px-1.5 py-1 text-xs w-12" placeholder="Gr">
                            <input type="number" name="edit_hours_attended" value="{g['hours_attended'] or ''}" class="border border-gray-300 rounded px-1.5 py-1 text-xs w-12" placeholder="Hr">
                            <button type="submit" class="text-green-600 hover:text-green-800 text-xs font-bold mx-1">Save</button>
                        </form>
                        <form method="POST" class="inline-block ml-1">
                            <input type="hidden" name="delete_id" value="{g['id']}">
                            <button type="submit" class="text-red-600 hover:text-red-800 text-xs font-bold">Del</button>
                        </form>
                    </td>
                </tr>
                """
            content += "</tbody></table></div>"
        else:
            content += "<p class='text-sm text-gray-500 italic'>No records yet.</p>"
        content += "</div>"
        
    conn.close()
    return render_page("Instructor Dashboard", content)

if __name__ == "__main__":
    app.run(debug=True)
