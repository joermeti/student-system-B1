from flask import Flask, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "rmeti-secret-2026"

def get_db():
    conn = sqlite3.connect("rmeti_portal.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            program TEXT,
            payment_plan TEXT,
            contractor_name TEXT,
            contractor_email TEXT,
            enrollment_date TEXT
        )
    """)
    c.execute("""
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==================== MASTER LAYOUT (Fixes missing CSS and Logo) ====================
def get_header(title=""):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>RMETI - {title}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            /* Force 3x larger base font size and strict 1/2 inch spacing everywhere */
            html {{ font-size: 24px; }}
            .input-box {{ border: 2px solid #cbd5e1; border-radius: 12px; padding: 20px; width: 100%; font-size: 1.5rem; margin-bottom: 48px; }}
            .btn-green {{ background-color: #166534; color: white; padding: 24px 48px; border-radius: 16px; font-size: 1.8rem; font-weight: bold; cursor: pointer; display: inline-block; text-align: center; }}
            .btn-dark {{ background-color: #1f2937; color: white; padding: 24px 48px; border-radius: 16px; font-size: 1.8rem; font-weight: bold; cursor: pointer; display: inline-block; text-align: center; }}
        </style>
    </head>
    <body class="bg-gray-50 text-gray-900 min-h-screen">
        
        <div class="bg-white shadow-md border-b-4 border-green-800" style="margin-bottom: 48px;">
            <div class="max-w-7xl mx-auto px-12 py-10 flex justify-between items-center">
                <div>
                    <h1 class="text-7xl font-bold tracking-tight" style="color: #166534;">RMETI</h1>
                    <p class="text-3xl text-gray-600 mt-4">Rocky Mountain Electrical Training Institute</p>
                </div>
                <div>
                    <img src="/static/rmeti-logo.png" onerror="this.src='/static/logo.jpg'" alt="RMETI Logo" class="w-auto" style="height: 120px;">
                </div>
            </div>
        </div>

        <div class="max-w-7xl mx-auto px-12 pb-24">
    """

FOOTER = """
        </div>
    </body>
    </html>
"""

# ==================== HOME ====================
@app.route("/")
def home():
    html = get_header("Home")
    html += """
        <div class="flex gap-12" style="margin-top: 48px;">
            <a href="/enroll" class="btn-green">Enroll Student</a>
            <a href="/login" class="btn-dark">Login</a>
        </div>
    """
    return html + FOOTER

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
            return redirect(url_for("enroll"))

        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO students (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            return redirect(url_for("success"))
        except sqlite3.IntegrityError:
            pass # Email exists
        finally:
            conn.close()

    html = get_header("Enroll")
    html += """
        <div class="bg-white p-12 rounded-3xl shadow-lg border">
            <h2 class="text-5xl font-semibold" style="margin-bottom: 48px;">Enroll New Student</h2>
            <form method="POST">
                <div class="grid grid-cols-2 gap-12">
                    <div>
                        <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Full Name *</label>
                        <input type="text" name="full_name" required class="input-box">
                    </div>
                    <div>
                        <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Email *</label>
                        <input type="email" name="email" required class="input-box">
                    </div>
                </div>
                
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Phone</label>
                <input type="text" name="phone" class="input-box">
                
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Program *</label>
                <select name="program" required class="input-box bg-white">
                    <option value="">-- Select Program --</option>
                    <option>Fast Track Journeyman semester 1</option>
                    <option>Fast Track Journeyman semester 2</option>
                    <option>Main Program semester 1</option>
                    <option>Main Program semester 2</option>
                    <option>Main Program semester 3</option>
                    <option>Main Program semester 4</option>
                </select>

                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Payment Plan</label>
                <input type="text" name="payment_plan" value="Interest-Free 5-Month Plan" class="input-box">
                
                <div class="grid grid-cols-2 gap-12">
                    <div>
                        <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Contractor Name</label>
                        <input type="text" name="contractor_name" class="input-box">
                    </div>
                    <div>
                        <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Contractor Email</label>
                        <input type="email" name="contractor_email" class="input-box">
                    </div>
                </div>
                
                <button type="submit" class="btn-green w-full" style="margin-top: 48px;">Enroll Student</button>
            </form>
        </div>
    """
    return html + FOOTER

@app.route("/success")
def success():
    html = get_header("Success")
    html += """
        <div class="text-center" style="margin-top: 48px;">
            <h2 class="text-6xl font-semibold" style="color: #166534; margin-bottom: 48px;">Enrollment Successful!</h2>
            <div class="flex justify-center gap-12">
                <a href="/enroll" class="text-3xl text-green-700 hover:underline">Enroll Another</a>
                <a href="/login" class="text-3xl text-green-700 hover:underline">Go to Login</a>
            </div>
        </div>
    """
    return html + FOOTER

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
                return redirect(url_for("login"))
        elif role == "student":
            conn = get_db()
            student = conn.execute("SELECT * FROM students WHERE email = ?", (identifier,)).fetchone()
            conn.close()
            if student:
                session["student_id"] = student["id"]
            else:
                return redirect(url_for("login"))

        session["role"] = role
        session["identifier"] = identifier
        return redirect(url_for(f"{role}_dashboard"))

    html = get_header("Login")
    html += """
        <div class="bg-white p-12 rounded-3xl shadow-lg border max-w-4xl mx-auto">
            <h2 class="text-5xl font-semibold text-center" style="margin-bottom: 48px;">Login</h2>
            <form method="POST">
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">I am a</label>
                <select name="role" id="role" class="input-box bg-white" onchange="togglePassword()">
                    <option value="student">Student</option>
                    <option value="contractor">Contractor</option>
                    <option value="instructor">Instructor</option>
                </select>
                
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Email or Username</label>
                <input type="text" name="identifier" required class="input-box">
                
                <div id="passwordField" style="display: none;">
                    <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Password</label>
                    <input type="password" name="password" class="input-box">
                </div>
                
                <button type="submit" class="btn-green w-full" style="margin-top: 24px;">Login</button>
            </form>
            
            <div class="text-center" style="margin-top: 48px;">
                <a href="/register_instructor" class="text-3xl text-green-700 hover:underline">Register as Instructor</a>
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
    return html + FOOTER

# ==================== REGISTRATION & PASSWORDS ====================
@app.route("/register_instructor", methods=["GET", "POST"])
def register_instructor():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            conn = get_db()
            try:
                conn.execute("INSERT INTO instructors (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                pass
            finally:
                conn.close()
    
    html = get_header("Instructor Registration")
    html += """
        <div class="bg-white p-12 rounded-3xl shadow-lg border max-w-4xl mx-auto">
            <h2 class="text-5xl font-semibold text-center" style="margin-bottom: 48px;">Register as Instructor</h2>
            <form method="POST">
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Choose Username</label>
                <input type="text" name="username" required class="input-box">
                
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Choose Password</label>
                <input type="password" name="password" required class="input-box">
                
                <button type="submit" class="btn-green w-full">Create Account</button>
            </form>
        </div>
    """
    return html + FOOTER

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if session.get("role") != "instructor": return redirect(url_for("login"))
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        if new_password == request.form.get("confirm_password"):
            conn = get_db()
            conn.execute("UPDATE instructors SET password = ? WHERE username = ? AND password = ?", (new_password, session["identifier"], current_password))
            conn.commit()
            conn.close()
            return redirect(url_for("instructor_dashboard"))
    
    html = get_header("Change Password")
    html += """
        <div class="bg-white p-12 rounded-3xl shadow-lg border max-w-4xl mx-auto">
            <h2 class="text-5xl font-semibold" style="margin-bottom: 48px;">Change Password</h2>
            <form method="POST">
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Current Password</label>
                <input type="password" name="current_password" required class="input-box">
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">New Password</label>
                <input type="password" name="new_password" required class="input-box">
                <label class="block text-3xl font-medium text-gray-700" style="margin-bottom: 24px;">Confirm New Password</label>
                <input type="password" name="confirm_password" required class="input-box">
                <button type="submit" class="btn-green w-full">Change Password</button>
            </form>
        </div>
    """
    return html + FOOTER

# ==================== DASHBOARDS ====================
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student": return redirect(url_for("login"))
    
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (session["student_id"],)).fetchone()
    grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (session["student_id"],)).fetchall()
    conn.close()

    if not student: return redirect(url_for("login"))

    html = get_header("Student Dashboard")
    html += f"""
        <div class="flex justify-between items-center" style="margin-bottom: 48px;">
            <h2 class="text-5xl font-semibold">Welcome, {student['full_name']}</h2>
            <a href="/logout" class="text-4xl text-red-600 hover:underline">Logout</a>
        </div>
        
        <div class="bg-white border rounded-3xl p-12 shadow-sm" style="margin-bottom: 48px;">
            <h3 class="text-4xl font-semibold" style="margin-bottom: 32px;">Your Information</h3>
            <p class="text-3xl" style="margin-bottom: 24px;"><strong>Program:</strong> {student['program']}</p>
            <p class="text-3xl"><strong>Payment Plan:</strong> {student['payment_plan']}</p>
        </div>

        <div class="bg-white border rounded-3xl p-12 shadow-sm">
            <h3 class="text-4xl font-semibold" style="margin-bottom: 48px;">Your Grades & Hours</h3>
    """
    if grades:
        html += """<table class="w-full text-left text-3xl"><tr class="border-b-4"><th class="pb-6">Module</th><th class="pb-6">Grade</th><th class="pb-6">Hours</th><th class="pb-6">Date</th></tr>"""
        for g in grades:
            html += f"<tr class="border-b"><td class="py-8">{g['module_name']}</td><td class="py-8">{g['grade']}</td><td class="py-8">{g['hours_attended']}</td><td class="py-8 text-gray-500">{g['recorded_date']}</td></tr>"
        html += "</table>"
    else:
        html += "<p class='text-3xl text-gray-500'>No grades recorded yet.</p>"
        
    return html + "</div>" + FOOTER

@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor": return redirect(url_for("login"))
    
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name", (session["identifier"],)).fetchall()
    
    html = get_header("Contractor Dashboard")
    html += f"""
        <div class="flex justify-between items-center" style="margin-bottom: 48px;">
            <h2 class="text-5xl font-semibold">Your Apprentices</h2>
            <a href="/logout" class="text-4xl text-red-600 hover:underline">Logout</a>
        </div>
    """
    if students:
        for s in students:
            grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
            html += f"""
            <div class="bg-white border rounded-3xl p-12 shadow-sm" style="margin-bottom: 48px;">
                <h3 class="text-4xl font-semibold" style="margin-bottom: 48px; color: #166534;">{s['full_name']} — {s['program']}</h3>
            """
            if grades:
                html += """<table class="w-full text-left text-3xl"><tr class="border-b-4"><th class="pb-6">Module</th><th class="pb-6">Grade</th><th class="pb-6">Hours</th><th class="pb-6">Date</th></tr>"""
                for g in grades:
                    html += f"<tr class="border-b"><td class="py-8">{g['module_name']}</td><td class="py-8">{g['grade']}</td><td class="py-8">{g['hours_attended']}</td><td class="py-8 text-gray-500">{g['recorded_date']}</td></tr>"
                html += "</table>"
            else:
                html += "<p class='text-3xl text-gray-500'>No grades recorded yet.</p>"
            html += "</div>"
    else:
        html += "<p class='text-4xl'>No students found.</p>"
        
    conn.close()
    return html + FOOTER

@app.route("/instructor", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get("role") != "instructor": return redirect(url_for("login"))
    conn = get_db()
    
    if request.method == "POST":
        if "delete_id" in request.form:
            conn.execute("DELETE FROM grades_hours WHERE id = ?", (request.form.get("delete_id"),))
        elif "edit_id" in request.form:
            conn.execute("UPDATE grades_hours SET module_name = ?, grade = ?, hours_attended = ? WHERE id = ?", 
                         (request.form.get("edit_module_name"), request.form.get("edit_grade"), request.form.get("edit_hours_attended") or 0, request.form.get("edit_id")))
        else:
            conn.execute("INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date) VALUES (?, ?, ?, ?, ?, ?)", 
                         (request.form.get("student_id"), request.form.get("module_name"), request.form.get("grade"), request.form.get("hours_attended") or 0, session.get("identifier"), datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

    students = conn.execute("SELECT * FROM students ORDER BY program, full_name").fetchall()
    
    html = get_header("Instructor Dashboard")
    html += """
        <div class="flex justify-between items-center" style="margin-bottom: 64px;">
            <h2 class="text-5xl font-semibold">Instructor Dashboard</h2>
            <div class="flex gap-12">
                <a href="/change_password" class="text-4xl text-green-700 hover:underline">Change Password</a>
                <a href="/logout" class="text-4xl text-red-600 hover:underline">Logout</a>
            </div>
        </div>
    """
    
    for s in students:
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
        html += f"""
        <div class="bg-white border rounded-3xl p-12 shadow-lg" style="margin-bottom: 64px;">
            <h3 class="text-4xl font-bold" style="margin-bottom: 24px; color: #166534;">{s['full_name']}</h3>
            <p class="text-3xl text-gray-500" style="margin-bottom: 48px;">{s['program']}</p>
            
            <form method="POST" class="grid grid-cols-4 gap-8 bg-gray-50 p-8 rounded-2xl border" style="margin-bottom: 48px;">
                <input type="hidden" name="student_id" value="{s['id']}">
                <input type="text" name="module_name" placeholder="Class/Module" class="border p-6 rounded-xl text-3xl w-full">
                <input type="text" name="grade" placeholder="Grade" class="border p-6 rounded-xl text-3xl w-full">
                <input type="number" name="hours_attended" placeholder="Hours" class="border p-6 rounded-xl text-3xl w-full">
                <button type="submit" class="bg-green-700 text-white rounded-xl text-3xl font-bold hover:bg-green-800">Add Record</button>
            </form>
        """
        if grades:
            html += """<table class="w-full text-left text-3xl"><tr class="border-b-4"><th class="pb-6">Module</th><th class="pb-6">Grade</th><th class="pb-6">Hours</th><th class="pb-6">Actions</th></tr>"""
            for g in grades:
                html += f"""
                <tr class="border-b">
                    <td class="py-8">
                        <form method="POST" class="flex gap-4">
                            <input type="hidden" name="edit_id" value="{g['id']}">
                            <input type="text" name="edit_module_name" value="{g['module_name']}" class="border p-4 rounded-xl w-64">
                    </td>
                    <td class="py-8"><input type="text" name="edit_grade" value="{g['grade']}" class="border p-4 rounded-xl w-32"></td>
                    <td class="py-8"><input type="number" name="edit_hours_attended" value="{g['hours_attended']}" class="border p-4 rounded-xl w-32"></td>
                    <td class="py-8 flex gap-6">
                            <button type="submit" class="text-green-700 font-bold hover:underline">Save</button>
                        </form>
                        <form method="POST">
                            <input type="hidden" name="delete_id" value="{g['id']}">
                            <button type="submit" class="text-red-600 font-bold hover:underline">Delete</button>
                        </form>
                    </td>
                </tr>
                """
            html += "</table>"
        html += "</div>"
        
    conn.close()
    return html + FOOTER

if __name__ == "__main__":
    app.run(debug=True)
