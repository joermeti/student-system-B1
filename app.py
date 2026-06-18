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

# ==================== MASTER LAYOUT (3x Sizing, Spacing & Logo) ====================
def get_header(title=""):
    # The onerror tag acts as a fallback to pull directly from GitHub if Render drops the static file
    logo_img = """<img src="/static/rmeti-logo.png" onerror="this.onerror=null; this.src='https://raw.githubusercontent.com/joermeti/student-system-B1/main/static/rmeti-logo.png';" alt="RMETI Logo" style="height: 160px; width: auto;">"""
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>RMETI - {title}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            /* Force 3x larger base font size and strict 1/2 inch spacing everywhere */
            html {{ font-size: 28px; }}
            body {{ background-color: #f9fafb; color: #111827; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; line-height: 2; }}
            
            h1 {{ font-size: 4rem; line-height: 1.2; }}
            h2 {{ font-size: 3rem; margin-bottom: 48px; color: #166534; }}
            h3 {{ font-size: 2.5rem; margin-bottom: 36px; }}
            p, label, td, th, option {{ font-size: 1.6rem; margin-bottom: 24px; }}
            
            .input-box {{ border: 3px solid #cbd5e1; border-radius: 16px; padding: 24px; width: 100%; font-size: 1.8rem; margin-bottom: 48px; background-color: white; }}
            .input-box:focus {{ outline: none; border-color: #166534; }}
            
            .btn-green {{ background-color: #166534; color: white; padding: 24px 48px; border-radius: 16px; font-size: 2rem; font-weight: bold; cursor: pointer; display: inline-block; text-align: center; border: none; }}
            .btn-green:hover {{ background-color: #14532d; }}
            
            .btn-dark {{ background-color: #1f2937; color: white; padding: 24px 48px; border-radius: 16px; font-size: 2rem; font-weight: bold; cursor: pointer; display: inline-block; text-align: center; border: none; }}
            .btn-dark:hover {{ background-color: #111827; }}
            
            .container-box {{ background-white; padding: 48px; border-radius: 24px; shadow-xl; border: 2px solid #e2e8f0; margin-bottom: 48px; background-color: white; }}
        </style>
    </head>
    <body class="min-h-screen flex flex-col">
        
        <header class="bg-white shadow-md border-b-8 border-green-800" style="margin-bottom: 64px;">
            <div class="max-w-7xl mx-auto px-12 py-10 flex justify-between items-center">
                <div>
                    <h1 class="font-bold tracking-tight" style="color: #166534;">RMETI</h1>
                    <p class="text-gray-600 mt-4" style="font-size: 2rem;">Rocky Mountain Electrical Training Institute</p>
                </div>
                <div>
                    {logo_img}
                </div>
            </div>
        </header>

        <main class="max-w-7xl mx-auto px-12 pb-24 w-full flex-grow">
    """

FOOTER = """
        </main>
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
        <div class="container-box">
            <h2>Enroll New Student</h2>
            <form method="POST">
                <div class="grid grid-cols-2 gap-12">
                    <div>
                        <label class="block font-medium text-gray-700">Full Name *</label>
                        <input type="text" name="full_name" required class="input-box">
                    </div>
                    <div>
                        <label class="block font-medium text-gray-700">Email *</label>
                        <input type="email" name="email" required class="input-box">
                    </div>
                </div>
                
                <label class="block font-medium text-gray-700">Phone</label>
                <input type="text" name="phone" class="input-box">
                
                <label class="block font-medium text-gray-700">Program *</label>
                <select name="program" required class="input-box">
                    <option value="">-- Select Program --</option>
                    <option>Fast Track Journeyman semester 1</option>
                    <option>Fast Track Journeyman semester 2</option>
                    <option>Main Program semester 1</option>
                    <option>Main Program semester 2</option>
                    <option>Main Program semester 3</option>
                    <option>Main Program semester 4</option>
                </select>

                <label class="block font-medium text-gray-700">Payment Plan</label>
                <select name="payment_plan" required class="input-box">
                    <option value="">-- Select Payment Plan --</option>
                    <optgroup label="Fast Track Journeyman">
                        <option>4-Month Payment Plan</option>
                        <option>5-Month Payment Plan</option>
                        <option>6-Month Payment Plan</option>
                    </optgroup>
                    <optgroup label="Main Program">
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
                
                <div class="grid grid-cols-2 gap-12">
                    <div>
                        <label class="block font-medium text-gray-700">Contractor Name</label>
                        <input type="text" name="contractor_name" class="input-box">
                    </div>
                    <div>
                        <label class="block font-medium text-gray-700">Contractor Email</label>
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
            <h2 style="color: #166534; font-size: 4rem;">Enrollment Successful!</h2>
            <div class="flex justify-center gap-12 mt-12">
                <a href="/enroll" class="text-green-700 hover:underline" style="font-size: 2rem;">Enroll Another</a>
                <a href="/login" class="text-green-700 hover:underline" style="font-size: 2rem;">Go to Login</a>
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
        <div class="container-box max-w-4xl mx-auto">
            <h2 class="text-center">Login</h2>
            <form method="POST">
                <label class="block font-medium text-gray-700">I am a</label>
                <select name="role" id="role" class="input-box" onchange="togglePassword()">
                    <option value="student">Student</option>
                    <option value="contractor">Contractor</option>
                    <option value="instructor">Instructor</option>
                </select>
                
                <label class="block font-medium text-gray-700">Email or Username</label>
                <input type="text" name="identifier" required class="input-box">
                
                <div id="passwordField" style="display: none;">
                    <label class="block font-medium text-gray-700">Password</label>
                    <input type="password" name="password" class="input-box">
                </div>
                
                <button type="submit" class="btn-green w-full" style="margin-top: 24px;">Login</button>
            </form>
            
            <div class="text-center" style="margin-top: 64px;">
                <a href="/register_instructor" class="text-green-700 hover:underline" style="font-size: 1.8rem;">Register as Instructor</a>
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
        <div class="container-box max-w-4xl mx-auto">
            <h2 class="text-center">Register as Instructor</h2>
            <form method="POST">
                <label class="block font-medium text-gray-700">Choose Username</label>
                <input type="text" name="username" required class="input-box">
                
                <label class="block font-medium text-gray-700">Choose Password</label>
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
        <div class="container-box max-w-4xl mx-auto">
            <h2>Change Password</h2>
            <form method="POST">
                <label class="block font-medium text-gray-700">Current Password</label>
                <input type="password" name="current_password" required class="input-box">
                <label class="block font-medium text-gray-700">New Password</label>
                <input type="password" name="new_password" required class="input-box">
                <label class="block font-medium text-gray-700">Confirm New Password</label>
                <input type="password" name="confirm_password" required class="input-box">
                <button type="submit" class="btn-green w-full">Change Password</button>
            </form>
            <div style="margin-top: 48px;">
                <a href="/instructor" class="text-green-700 hover:underline" style="font-size: 1.8rem;">Back to Dashboard</a>
            </div>
        </div>
    """
    return html + FOOTER

# ==================== STUDENT DASHBOARD (Restricted View) ====================
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student": return redirect(url_for("login"))
    
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (session["student_id"],)).fetchone()
    conn.close()

    if not student: return redirect(url_for("login"))

    html = get_header("Student Dashboard")
    html += f"""
        <div class="flex justify-between items-center" style="margin-bottom: 64px;">
            <h2>Welcome, {student['full_name']}</h2>
            <a href="/logout" class="text-red-600 hover:underline" style="font-size: 2rem;">Logout</a>
        </div>
        
        <div class="container-box">
            <h3>Your Information</h3>
            <p><strong>Program:</strong> {student['program']}</p>
            <p><strong>Payment Plan:</strong> {student['payment_plan']}</p>
            <p><strong>Contractor:</strong> {student['contractor_name'] or 'N/A'}</p>
        </div>
    """
    return html + FOOTER

# ==================== CONTRACTOR DASHBOARD (Restricted View) ====================
@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor": return redirect(url_for("login"))
    
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name", (session["identifier"],)).fetchall()
    
    html = get_header("Contractor Dashboard")
    html += f"""
        <div class="flex justify-between items-center" style="margin-bottom: 64px;">
            <h2>Your Apprentices</h2>
            <a href="/logout" class="text-red-600 hover:underline" style="font-size: 2rem;">Logout</a>
        </div>
    """
    if students:
        for s in students:
            html += f"""
            <div class="container-box">
                <h3 style="color: #166534; margin-bottom: 12px;">{s['full_name']}</h3>
                <p><strong>Program:</strong> {s['program']}</p>
            </div>
            """
    else:
        html += "<p>No students found.</p>"
        
    conn.close()
    return html + FOOTER

# ==================== INSTRUCTOR DASHBOARD (Full Access) ====================
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
            <h2>Instructor Dashboard</h2>
            <div class="flex gap-12">
                <a href="/change_password" class="text-green-700 hover:underline" style="font-size: 2rem;">Change Password</a>
                <a href="/logout" class="text-red-600 hover:underline" style="font-size: 2rem;">Logout</a>
            </div>
        </div>
    """
    
    for s in students:
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
        html += f"""
        <div class="container-box">
            <h3 style="color: #166534; margin-bottom: 12px;">{s['full_name']}</h3>
            <p style="color: #64748b; margin-bottom: 48px;">{s['program']}</p>
            
            <form method="POST" class="grid grid-cols-4 gap-8 bg-gray-50 p-10 rounded-2xl border" style="margin-bottom: 48px;">
                <input type="hidden" name="student_id" value="{s['id']}">
                <input type="text" name="module_name" placeholder="Class/Module" class="border p-6 rounded-xl w-full" style="font-size: 1.6rem;">
                <input type="text" name="grade" placeholder="Grade" class="border p-6 rounded-xl w-full" style="font-size: 1.6rem;">
                <input type="number" name="hours_attended" placeholder="Hours" class="border p-6 rounded-xl w-full" style="font-size: 1.6rem;">
                <button type="submit" class="bg-green-700 text-white rounded-xl font-bold hover:bg-green-800" style="font-size: 1.8rem;">Add Record</button>
            </form>
        """
        if grades:
            html += """<table class="w-full text-left" style="font-size: 1.6rem;"><tr class="border-b-4"><th class="pb-6">Module</th><th class="pb-6">Grade</th><th class="pb-6">Hours</th><th class="pb-6">Actions</th></tr>"""
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
