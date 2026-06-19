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

# ==================== MASTER LAYOUT ENGINE (LOCKED DESIGN) ====================
def render_page(title, content):
    messages = get_flashed_messages()
    flash_html = ""
    if messages:
        flash_html = '<div class="mb-8 space-y-3">'
        for msg in messages:
            flash_html += f'<div class="bg-emerald-50 border-l-4 border-emerald-600 text-emerald-800 p-5 rounded-lg shadow-sm font-semibold text-lg">{msg}</div>'
        flash_html += '</div>'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RMETI - {title}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .font-castellar {{ font-family: 'Castellar', 'Times New Roman', serif; letter-spacing: 0.05em; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 1.125rem; line-height: 1.75; }}
            h1, h2, h3, h4 {{ line-height: 1.3; }}
            .btn-green {{ background-color: #166534; color: white; padding: 0.875rem 1.75rem; border-radius: 0.5rem; font-weight: 600; font-size: 1.125rem; transition: background-color 0.2s; display: inline-block; text-align: center; border: none; cursor: pointer; }}
            .btn-green:hover {{ background-color: #14532d; }}
            .btn-dark {{ background-color: #1f2937; color: white; padding: 0.875rem 1.75rem; border-radius: 0.5rem; font-weight: 600; font-size: 1.125rem; transition: background-color 0.2s; display: inline-block; text-align: center; border: none; cursor: pointer; }}
            .btn-dark:hover {{ background-color: #111827; }}
            .input-std {{ width: 100%; border: 1px solid #d1d5db; border-radius: 0.5rem; padding: 0.875rem 1rem; outline: none; background-color: #fff; transition: all 0.2s; font-size: 1.125rem; }}
            .input-std:focus {{ border-color: #166534; box-shadow: 0 0 0 2px rgba(22, 101, 52, 0.2); }}
            optgroup {{ font-weight: 700; color: #166534; font-size: 1.125rem; }}
        </style>
    </head>
    <body class="bg-gray-50 text-gray-800 min-h-screen flex flex-col">
        <header class="bg-white shadow-md border-b-4 border-emerald-800">
            <div class="max-w-6xl mx-auto px-6 py-6 flex justify-between items-center">
                <a href="/" class="hover:opacity-80 transition block">
                    <h1 class="font-castellar text-4xl md:text-5xl font-bold text-emerald-800 leading-none">RMETI</h1>
                    <p class="text-base text-gray-500 font-medium mt-1 tracking-wide">Rocky Mountain Electrical Training Institute</p>
                </a>
                <div>
                    <img src="/static/logo.jpg" onerror="this.style.display='none';" alt="RMETI Logo" class="h-16 w-auto object-contain">
                </div>
            </div>
        </header>
        <main class="flex-grow max-w-6xl mx-auto px-6 py-12 w-full">
            {flash_html}
            {content}
        </main>
    </body>
    </html>
    """

# ==================== HOME ====================
@app.route("/")
def home():
    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-12 mt-8 max-w-4xl mx-auto text-center">
        <h2 class="text-3xl md:text-4xl font-bold text-gray-800 mb-6">Welcome to the RMETI Portal</h2>
        <p class="text-gray-600 mb-12 text-xl">Manage enrollments, track progress, and view apprenticeship details securely.</p>
        <div class="flex flex-col sm:flex-row gap-6 justify-center">
            <a href="/enroll" class="btn-green text-xl px-10 py-4 shadow-md">Enroll New Student</a>
            <a href="/login" class="bg-gray-800 hover:bg-gray-900 text-white font-semibold text-xl px-10 py-4 rounded-lg shadow-md transition">Login to Portal</a>
        </div>
    </div>
    """
    return render_page("Home", content)

# ==================== ENROLL ====================
@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO students (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (request.form.get("full_name").strip(), request.form.get("email").strip(), request.form.get("phone").strip(), 
                  request.form.get("program").strip(), request.form.get("payment_plan").strip(), request.form.get("contractor_name").strip(), 
                  request.form.get("contractor_email").strip(), datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            flash("Student enrolled successfully!")
            return redirect(url_for("success"))
        except sqlite3.IntegrityError:
            flash("A student with this email already exists.")
        finally:
            conn.close()

    content = """
    <div class="max-w-4xl mx-auto">
        <div class="bg-emerald-800 rounded-t-2xl p-8 text-center shadow-md">
            <h2 class="text-3xl md:text-4xl font-bold text-white">Student Enrollment Application</h2>
            <p class="text-emerald-100 mt-3 text-lg font-medium">Complete the form below to register for RMETI courses.</p>
        </div>
        <div class="bg-white border border-gray-200 border-t-0 shadow-lg rounded-b-2xl p-10 md:p-12">
            <form method="POST" class="space-y-10">
                <div>
                    <h3 class="text-2xl font-bold text-emerald-800 border-b-2 border-emerald-100 pb-3 mb-6">1. Personal Information</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div><label class="block text-base font-bold text-gray-700 mb-2">Full Name *</label><input type="text" name="full_name" required class="input-std"></div>
                        <div><label class="block text-base font-bold text-gray-700 mb-2">Email Address *</label><input type="email" name="email" required class="input-std"></div>
                        <div class="md:col-span-2"><label class="block text-base font-bold text-gray-700 mb-2">Phone Number</label><input type="text" name="phone" class="input-std md:w-1/2"></div>
                    </div>
                </div>
                <div>
                    <h3 class="text-2xl font-bold text-emerald-800 border-b-2 border-emerald-100 pb-3 mb-6">2. Program Details</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <label class="block text-base font-bold text-gray-700 mb-2">Select Program *</label>
                            <select name="program" required class="input-std bg-white">
                                <option value="">-- Choose a Course --</option>
                                <option>Fast Track Journeyman semester 1</option><option>Fast Track Journeyman semester 2</option>
                                <option>Main Program semester 1</option><option>Main Program semester 2</option>
                                <option>Main Program semester 3</option><option>Main Program semester 4</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-base font-bold text-gray-700 mb-2">Payment Plan *</label>
                            <select name="payment_plan" required class="input-std bg-white">
                                <option value="">-- Choose a Plan --</option>
                                <optgroup label="Fast Track Course">
                                    <option>4-Month Payment Plan</option><option>5-Month Payment Plan</option>
                                    <option>6-Month Payment Plan</option><option>Paid in Full</option>
                                </optgroup>
                                <optgroup label="Main Program Course">
                                    <option>4-Month Payment Plan</option><option>5-Month Payment Plan</option>
                                    <option>6-Month Payment Plan</option><option>7-Month Payment Plan</option>
                                    <option>8-Month Payment Plan</option><option>9-Month Payment Plan</option>
                                    <option>10-Month Payment Plan</option><option>11-Month Payment Plan</option>
                                    <option>12-Month Payment Plan</option><option>Paid in Full</option>
                                </optgroup>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="bg-gray-50 p-8 rounded-xl border border-gray-200">
                    <h3 class="text-xl font-bold text-gray-800 mb-6">3. Contractor Information <span class="text-base font-normal text-gray-500">(If applicable)</span></h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div><label class="block text-base font-bold text-gray-700 mb-2">Contractor Name</label><input type="text" name="contractor_name" class="input-std bg-white"></div>
                        <div><label class="block text-base font-bold text-gray-700 mb-2">Contractor Email</label><input type="email" name="contractor_email" class="input-std bg-white"></div>
                    </div>
                </div>
                <div class="pt-6">
                    <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-2xl py-5 rounded-xl shadow-md transition">Submit Enrollment Application</button>
                </div>
            </form>
        </div>
    </div>
    """
    return render_page("Enroll", content)

@app.route("/success")
def success():
    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-14 max-w-2xl mx-auto text-center mt-12">
        <h2 class="text-4xl md:text-5xl font-bold text-emerald-700 mb-10">Enrollment Successful!</h2>
        <div class="flex flex-col sm:flex-row gap-8 justify-center">
            <a href="/enroll" class="text-emerald-700 font-bold hover:underline text-xl">Enroll Another Student</a>
            <span class="hidden sm:inline text-gray-300 text-xl">|</span>
            <a href="/login" class="text-gray-800 font-bold hover:underline text-xl">Go to Login Portal</a>
        </div>
    </div>
    """
    return render_page("Success", content)

# ==================== LOGIN ====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role, idnt = request.form['role'], request.form['identifier'].strip()
        conn = get_db()
        
        if role == "instructor":
            inst = conn.execute("SELECT * FROM instructors WHERE username = ?", (idnt,)).fetchone()
            conn.close()
            if inst and inst['password'] == request.form['password']:
                session.update({'role': role, 'identifier': idnt})
                return redirect(url_for('instructor_dashboard'))
            flash("Invalid instructor credentials.")
            
        elif role == "student":
            s = conn.execute("SELECT * FROM students WHERE email = ?", (idnt,)).fetchone()
            conn.close()
            if s:
                session.update({'role': role, 'identifier': idnt, 'student_id': s['id']})
                return redirect(url_for('student_dashboard'))
            flash("No student found with that email address.")
            
        elif role == "contractor":
            # Just log them in if they select contractor (they will see an empty dashboard if they have no students)
            conn.close()
            session.update({'role': role, 'identifier': idnt})
            return redirect(url_for('contractor_dashboard'))
            
        return redirect(url_for('login'))
            
    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-10 md:p-12 max-w-md mx-auto mt-12">
        <h2 class="text-3xl font-bold text-emerald-800 mb-8 text-center">Secure Login</h2>
        <form method="POST" class="space-y-6">
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">I am a</label>
                <select name="role" id="role" class="input-std bg-white" onchange="togglePassword()">
                    <option value="student">Student</option>
                    <option value="contractor">Contractor</option>
                    <option value="instructor">Instructor</option>
                </select>
            </div>
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Email or Username</label>
                <input type="text" name="identifier" required class="input-std">
            </div>
            <div id="passwordField" style="display: none;">
                <label class="block text-base font-bold text-gray-700 mb-2">Password</label>
                <input type="password" name="password" class="input-std">
            </div>
            <div class="pt-4">
                <button type="submit" class="btn-green w-full py-4 text-xl">Sign In</button>
            </div>
        </form>
        <div class="mt-8 text-center pt-6 border-t border-gray-100">
            <a href="/register_instructor" class="text-emerald-600 font-semibold hover:underline text-lg">Register as Instructor</a>
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

# ==================== INSTRUCTOR REGISTRATION ====================
@app.route("/register_instructor", methods=["GET", "POST"])
def register_instructor():
    if request.method == "POST":
        conn = get_db()
        try:
            conn.execute("INSERT INTO instructors (username, password) VALUES (?, ?)", (request.form['username'], request.form['password']))
            conn.commit()
            flash("Account created! Please log in.")
            return redirect(url_for("login"))
        except:
            flash("Username taken.")
        finally:
            conn.close()

    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-10 md:p-12 max-w-md mx-auto mt-12">
        <h2 class="text-3xl font-bold text-emerald-800 mb-8 text-center">Instructor Registration</h2>
        <form method="POST" class="space-y-6">
            <div><label class="block text-base font-bold text-gray-700 mb-2">Choose Username</label><input type="text" name="username" required class="input-std"></div>
            <div><label class="block text-base font-bold text-gray-700 mb-2">Choose Password</label><input type="password" name="password" required class="input-std"></div>
            <div class="pt-4"><button type="submit" class="btn-green w-full py-4 text-xl">Create Account</button></div>
        </form>
        <div class="mt-8 text-center"><a href="/login" class="text-gray-500 hover:text-emerald-700 font-medium hover:underline text-lg">Back to Login</a></div>
    </div>
    """
    return render_page("Register", content)

# ==================== STUDENT DASHBOARD ====================
@app.route("/student_dashboard")
def student_dashboard():
    if session.get('role') != 'student': return redirect(url_for('login'))
    conn = get_db()
    s = conn.execute("SELECT * FROM students WHERE id = ?", (session.get('student_id'),)).fetchone()
    if not s:
        conn.close()
        return redirect(url_for('login'))
    
    # Students see ALL grades from ALL instructors
    grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
    conn.close()
    
    html = f"""
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <h2 class="text-3xl md:text-4xl font-bold text-emerald-800">Welcome, {s['full_name']}</h2>
        <a href="/logout" class="text-red-600 font-bold hover:underline bg-red-50 px-6 py-3 rounded-lg border border-red-100 text-lg">Logout</a>
    </div>
    
    <div class="bg-white border border-gray-200 rounded-2xl p-8 mb-8 shadow-sm">
        <h3 class="text-2xl font-bold text-gray-800 mb-6 border-b pb-3">Enrollment Status</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-lg">
            <p><strong>Program:</strong> {s['program']}</p>
            <p><strong>Payment Plan:</strong> {s['payment_plan']}</p>
        </div>
    </div>
    
    <div class="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
        <h3 class="text-2xl font-bold text-gray-800 mb-6 border-b pb-3">Academic Record</h3>
    """
    if grades:
        html += """
        <div class="overflow-x-auto">
            <table class='w-full text-left text-lg'>
                <tr class='border-b-2 border-gray-200 bg-gray-50 text-gray-700'>
                    <th class='p-4 font-bold'>Module / Class</th>
                    <th class='p-4 font-bold'>Instructor</th>
                    <th class='p-4 font-bold'>Grade</th>
                    <th class='p-4 font-bold'>Hours</th>
                    <th class='p-4 font-bold'>Date</th>
                </tr>
        """
        for g in grades:
            html += f"""
                <tr class='border-b hover:bg-gray-50 transition'>
                    <td class='p-4'>{g['module_name']}</td>
                    <td class='p-4 text-emerald-700 font-semibold'>{g['recorded_by']}</td>
                    <td class='p-4 font-bold text-gray-900'>{g['grade']}</td>
                    <td class='p-4 font-medium'>{g['hours_attended']}</td>
                    <td class='p-4 text-gray-500 text-base'>{g['recorded_date']}</td>
                </tr>
            """
        html += "</table></div>"
    else:
        html += "<p class='text-gray-500 italic text-lg'>No grades recorded yet.</p>"
    html += "</div>"
    
    return render_page("Student Dashboard", html)

# ==================== CONTRACTOR DASHBOARD ====================
@app.route("/contractor_dashboard")
def contractor_dashboard():
    if session.get('role') != 'contractor': return redirect(url_for('login'))
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name", (session['identifier'],)).fetchall()
    
    html = f"""
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <h2 class="text-3xl md:text-4xl font-bold text-emerald-800">Your Apprentices</h2>
        <a href="/logout" class="text-red-600 font-bold hover:underline bg-red-50 px-6 py-3 rounded-lg border border-red-100 text-lg">Logout</a>
    </div>
    """
    if not students:
        html += "<div class='bg-white p-8 rounded-2xl border border-gray-200 shadow-sm'><p class='text-lg text-gray-600'>No apprentices found for your email address.</p></div>"
        
    for s in students:
        html += f"""
        <div class="bg-white border border-gray-200 rounded-2xl p-8 mb-8 shadow-sm">
            <h3 class='text-2xl font-bold text-gray-800 mb-2'>{s['full_name']}</h3>
            <p class='text-emerald-700 font-bold text-lg mb-6'>{s['program']}</p>
        """
        # Contractors see ALL grades from ALL instructors
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
        if grades:
            html += """
            <div class="overflow-x-auto">
                <table class='w-full text-left text-lg'>
                    <tr class='border-b-2 border-gray-200 bg-gray-50 text-gray-700'>
                        <th class='p-4 font-bold'>Module / Class</th>
                        <th class='p-4 font-bold'>Instructor</th>
                        <th class='p-4 font-bold'>Grade</th>
                        <th class='p-4 font-bold'>Hours</th>
                        <th class='p-4 font-bold'>Date</th>
                    </tr>
            """
            for g in grades: 
                html += f"""
                <tr class='border-b hover:bg-gray-50 transition'>
                    <td class='p-4'>{g['module_name']}</td>
                    <td class='p-4 text-emerald-700 font-semibold'>{g['recorded_by']}</td>
                    <td class='p-4 font-bold text-gray-900'>{g['grade']}</td>
                    <td class='p-4 font-medium'>{g['hours_attended']}</td>
                    <td class='p-4 text-gray-500 text-base'>{g['recorded_date']}</td>
                </tr>
                """
            html += "</table></div></div>"
        else:
            html += "<p class='text-gray-500 italic text-lg'>No grades recorded yet.</p></div>"
    conn.close()
    return render_page("Contractor Dashboard", html)

# ==================== INSTRUCTOR DASHBOARD (PRIVACY WALL) ====================
@app.route("/instructor_dashboard", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get('role') != 'instructor': return redirect(url_for('login'))
    instructor_name = session.get('identifier')
    conn = get_db()
    
    if request.method == "POST":
        if "delete_id" in request.form:
            conn.execute("DELETE FROM grades_hours WHERE id = ? AND recorded_by = ?", (request.form['delete_id'], instructor_name))
        elif "edit_id" in request.form:
            conn.execute("UPDATE grades_hours SET module_name=?, grade=?, hours_attended=? WHERE id=? AND recorded_by = ?", 
                         (request.form['edit_module_name'], request.form['edit_grade'], request.form['edit_hours_attended'], request.form['edit_id'], instructor_name))
        else:
            conn.execute("INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date) VALUES (?,?,?,?,?,?)", 
                         (request.form['student_id'], request.form['mod'], request.form['grd'], request.form['hrs'], instructor_name, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

    students = conn.execute("SELECT * FROM students ORDER BY program, full_name").fetchall()
    
    html = """
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <h2 class="text-3xl md:text-4xl font-bold text-emerald-800">Instructor Dashboard</h2>
        <a href="/logout" class="text-red-600 font-bold hover:underline bg-red-50 px-6 py-3 rounded-lg border border-red-100 text-lg">Logout</a>
    </div>
    <div class="mb-8 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
        <p class="text-emerald-800 font-semibold">Privacy Notice: You will only see and edit the grades and hours that you have personally submitted.</p>
    </div>
    """
    for s in students:
        html += f"""
        <div class="bg-white border border-gray-200 rounded-2xl p-8 mb-10 shadow-sm">
            <h3 class="text-2xl font-bold text-gray-800 mb-1">{s['full_name']}</h3>
            <p class="text-lg text-emerald-700 font-medium mb-8">{s['program']}</p>
            
            <form method='POST' class="flex flex-col md:flex-row gap-6 bg-emerald-50 p-6 rounded-xl mb-8 items-end border border-emerald-100">
                <input type='hidden' name='student_id' value='{s['id']}'>
                <div class="w-full md:flex-grow"><label class="block text-sm font-bold text-emerald-800 uppercase mb-2">Module / Class</label><input name='mod' required class="input-std"></div>
                <div class="w-full md:w-32"><label class="block text-sm font-bold text-emerald-800 uppercase mb-2">Grade</label><input name='grd' required class="input-std"></div>
                <div class="w-full md:w-32"><label class="block text-sm font-bold text-emerald-800 uppercase mb-2">Hours</label><input type="number" name='hrs' required class="input-std"></div>
                <button type='submit' class='btn-green py-3 px-6 text-lg w-full md:w-auto'>+ Add Record</button>
            </form>
        """
        
        # INSTRUCTOR PRIVACY WALL: Query explicitly filters by recorded_by
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? AND recorded_by = ? ORDER BY recorded_date DESC", (s['id'], instructor_name)).fetchall()
        
        if grades:
            html += """
            <div class="overflow-x-auto">
                <table class='w-full text-left text-lg'>
                    <tr class='border-b-2 border-gray-200 bg-gray-50 text-gray-700'>
                        <th class='p-4 font-bold'>Module</th>
                        <th class='p-4 font-bold'>Grade</th>
                        <th class='p-4 font-bold'>Hours</th>
                        <th class='p-4 font-bold text-right'>Action</th>
                    </tr>
            """
            for g in grades:
                html += f"""
                <tr class='border-b hover:bg-gray-50 transition'>
                    <td class='p-3'>
                        <form method='POST' class="flex flex-col sm:flex-row items-start sm:items-center gap-4 justify-end">
                            <input type='hidden' name='edit_id' value='{g['id']}'>
                            <input name='edit_module_name' value='{g['module_name']}' class='border border-gray-300 rounded px-3 py-2 w-full'>
                    </td>
                    <td class='p-3'><input name='edit_grade' value='{g['grade']}' class='border border-gray-300 rounded px-3 py-2 w-20 text-center'></td>
                    <td class='p-3'><input type='number' name='edit_hours_attended' value='{g['hours_attended']}' class='border border-gray-300 rounded px-3 py-2 w-20 text-center'></td>
                    <td class='p-3 text-right whitespace-nowrap'>
                            <button type='submit' class='text-emerald-700 font-bold hover:underline px-3 py-2 bg-emerald-50 rounded border border-emerald-100 mr-2'>Save</button>
                        </form>
                        <form method='POST' class="inline">
                            <input type='hidden' name='delete_id' value='{g['id']}'>
                            <button type='submit' class='text-red-600 font-bold hover:underline px-3 py-2 bg-red-50 rounded border border-red-100'>Del</button>
                        </form>
                    </td>
                </tr>"""
            html += "</table></div>"
        html += "</div>"
    
    conn.close()
    return render_page("Instructor Dashboard", html)

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('home'))

if __name__ == "__main__": app.run(debug=True)
