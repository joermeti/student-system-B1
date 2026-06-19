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
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        program TEXT,
        payment_plan TEXT,
        contractor_name TEXT,
        contractor_email TEXT,
        enrollment_date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS grades_hours (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        module_name TEXT,
        grade TEXT,
        hours_attended INTEGER,
        recorded_by TEXT,
        recorded_date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS instructors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

# ====================== HOME ======================
@app.route("/")
def home():
    return '''
    <div class="max-w-6xl mx-auto px-12 py-16">
        <div class="flex justify-between items-center mb-20">
            <div>
                <h1 class="text-7xl font-bold text-emerald-700 tracking-tight">RMETI</h1>
                <p class="text-4xl text-gray-700 mt-4">Rocky Mountain Electrical Training Institute</p>
            </div>
            <img src="/static/logo.png" class="h-32 w-auto" alt="RMETI Logo">
        </div>
        <div class="flex gap-8">
            <a href="/enroll" class="bg-emerald-600 hover:bg-emerald-700 text-white px-16 py-8 rounded-3xl text-4xl font-semibold">Enroll Student</a>
            <a href="/login" class="bg-gray-900 hover:bg-black text-white px-16 py-8 rounded-3xl text-4xl font-semibold">Login</a>
        </div>
    </div>
    '''

# ====================== ENROLL ======================
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
            conn.execute("""INSERT INTO students (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            return redirect(url_for("success"))
        except sqlite3.IntegrityError:
            flash("A student with this email already exists.")
        finally:
            conn.close()

    return '''
    <div class="max-w-4xl mx-auto mt-12 px-12">
        <div class="flex justify-between items-center mb-16">
            <h2 class="text-6xl font-semibold">Enroll New Student</h2>
            <img src="/static/logo.png" class="h-24 w-auto">
        </div>
        <form method="POST" class="space-y-12 bg-white p-16 rounded-3xl border-2">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-12">
                <div>
                    <label class="block text-3xl mb-4">Full Name *</label>
                    <input type="text" name="full_name" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
                </div>
                <div>
                    <label class="block text-3xl mb-4">Email *</label>
                    <input type="email" name="email" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
                </div>
            </div>
            <div>
                <label class="block text-3xl mb-4">Phone</label>
                <input type="text" name="phone" class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
            </div>
            <div>
                <label class="block text-3xl mb-4">Program *</label>
                <select name="program" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
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
                <label class="block text-3xl mb-4">Payment Plan</label>
                <input type="text" name="payment_plan" value="Interest-Free 5-Month Plan" class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-12">
                <div>
                    <label class="block text-3xl mb-4">Contractor Name</label>
                    <input type="text" name="contractor_name" class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
                </div>
                <div>
                    <label class="block text-3xl mb-4">Contractor Email</label>
                    <input type="email" name="contractor_email" class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
                </div>
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-10 rounded-3xl text-4xl font-semibold">Enroll Student</button>
        </form>
    </div>
    '''

@app.route("/success")
def success():
    return '''
    <div class="max-w-md mx-auto mt-32 text-center">
        <h2 class="text-6xl font-semibold text-emerald-700">Enrollment Successful!</h2>
        <div class="mt-16 text-3xl space-x-8">
            <a href="/enroll" class="text-emerald-600 hover:underline">Enroll Another</a>
            <a href="/login" class="text-emerald-600 hover:underline">Go to Login</a>
        </div>
    </div>
    '''

# ====================== LOGIN ======================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        if role == "instructor":
            instructor = conn.execute("SELECT * FROM instructors WHERE username = ?", (identifier,)).fetchone()
            if not instructor or instructor["password"] != password:
                flash("Invalid instructor username or password.")
                conn.close()
                return redirect(url_for("login"))
        else:
            student = conn.execute("SELECT * FROM students WHERE email = ?", (identifier,)).fetchone()
            if student:
                session["student_id"] = student["id"]
            else:
                flash("No student found with that email address.")
                conn.close()
                return redirect(url_for("login"))
        conn.close()

        session["role"] = role
        session["identifier"] = identifier
        return redirect(url_for(f"{role}_dashboard"))

    return '''
    <div class="max-w-2xl mx-auto mt-20 px-12">
        <div class="flex justify-between items-center mb-16">
            <h2 class="text-6xl font-semibold">Login</h2>
            <img src="/static/logo.png" class="h-24 w-auto">
        </div>
        <form method="POST" class="space-y-12 bg-white p-16 rounded-3xl border-2">
            <div>
                <label class="block text-3xl mb-5">I am a</label>
                <select name="role" id="role" class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl" onchange="togglePassword()">
                    <option value="student">Student</option>
                    <option value="contractor">Contractor</option>
                    <option value="instructor">Instructor</option>
                </select>
            </div>
            <div>
                <label class="block text-3xl mb-5">Email or Username</label>
                <input type="text" name="identifier" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
            </div>
            <div id="passwordField" style="display:none;">
                <label class="block text-3xl mb-5">Password</label>
                <input type="password" name="password" class="w-full border-2 border-gray-300 rounded-3xl px-8 py-8 text-3xl">
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-10 rounded-3xl text-4xl font-semibold">Login</button>
        </form>
        <div class="mt-10 text-center">
            <a href="/register_instructor" class="text-emerald-600 hover:underline text-3xl">Register as Instructor</a>
        </div>
    </div>
    <script>
        function togglePassword() {
            document.getElementById('passwordField').style.display = (document.getElementById('role').value === 'instructor') ? 'block' : 'none';
        }
        window.onload = togglePassword;
    </script>
    '''

# ====================== REGISTER INSTRUCTOR ======================
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
    return '''
    <div class="max-w-lg mx-auto mt-16 px-12">
        <div class="flex justify-between items-center mb-12">
            <h2 class="text-6xl font-semibold">Register as Instructor</h2>
            <img src="/static/logo.png" class="h-20 w-auto">
        </div>
        <form method="POST" class="space-y-10 bg-white p-12 rounded-3xl border-2">
            <div>
                <label class="block text-3xl mb-4">Choose Username</label>
                <input type="text" name="username" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-7 text-3xl">
            </div>
            <div>
                <label class="block text-3xl mb-4">Choose Password</label>
                <input type="password" name="password" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-7 text-3xl">
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-8 rounded-3xl text-3xl font-semibold">Create Account</button>
        </form>
        <div class="mt-8 text-center">
            <a href="/login" class="text-emerald-600 hover:underline text-3xl">Back to Login</a>
        </div>
    </div>
    '''

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ====================== CHANGE PASSWORD ======================
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
    return '''
    <div class="max-w-lg mx-auto mt-12 px-12">
        <h2 class="text-6xl font-semibold mb-12">Change Password</h2>
        <form method="POST" class="space-y-10 bg-white p-12 rounded-3xl border-2">
            <div><label class="block text-3xl mb-4">Current Password</label>
                <input type="password" name="current_password" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-7 text-3xl"></div>
            <div><label class="block text-3xl mb-4">New Password</label>
                <input type="password" name="new_password" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-7 text-3xl"></div>
            <div><label class="block text-3xl mb-4">Confirm New Password</label>
                <input type="password" name="confirm_password" required class="w-full border-2 border-gray-300 rounded-3xl px-8 py-7 text-3xl"></div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-8 rounded-3xl text-3xl font-semibold">Change Password</button>
        </form>
        <div class="mt-8"><a href="/instructor" class="text-emerald-600 hover:underline text-3xl">Back to Dashboard</a></div>
    </div>
    '''

# ====================== STUDENT DASHBOARD ======================
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student" or not session.get("student_id"):
        return redirect(url_for("login"))
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (session["student_id"],)).fetchone()
    grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (session["student_id"],)).fetchall()
    conn.close()
    if not student:
        return redirect(url_for("login"))

    html = f'''
    <div class="max-w-6xl mx-auto mt-10 px-12">
        <div class="flex justify-between items-center mb-12">
            <h2 class="text-6xl font-semibold">Welcome, {student["full_name"]}!</h2>
            <img src="/static/logo.png" class="h-20 w-auto">
        </div>
        <div class="bg-white border-2 rounded-3xl p-12 mb-12">
            <h3 class="text-4xl font-semibold mb-8">Your Information</h3>
            <div class="text-3xl space-y-3">
                <p><strong>Program:</strong> {student["program"]}</p>
                <p><strong>Payment Plan:</strong> {student["payment_plan"]}</p>
            </div>
        </div>
        <div class="bg-white border-2 rounded-3xl p-12">
            <h3 class="text-4xl font-semibold mb-8">Your Grades & Hours</h3>
    '''
    if grades:
        html += '<table class="w-full text-2xl"><thead><tr class="border-b text-left text-gray-600"><th class="py-5">Module</th><th>Grade</th><th>Hours</th><th>Date</th></tr></thead><tbody>'
        for g in grades:
            html += f'<tr class="border-b"><td class="py-5">{g["module_name"] or "-"}</td><td>{g["grade"] or "-"}</td><td>{g["hours_attended"] or "-"}</td><td class="text-gray-500">{g["recorded_date"]}</td></tr>'
        html += '</tbody></table>'
    else:
        html += '<p class="text-3xl text-gray-500">No grades recorded yet.</p>'
    html += '''
        </div>
        <div class="mt-12"><a href="/logout" class="text-red-600 hover:underline text-3xl">Logout</a></div>
    </div>
    '''
    return html

# ====================== CONTRACTOR DASHBOARD ======================
@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor":
        return redirect(url_for("login"))
    email = session.get("identifier")
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name", (email,)).fetchall()
    html = f'''
    <div class="max-w-6xl mx-auto mt-10 px-12">
        <div class="flex justify-between items-center mb-12">
            <h2 class="text-6xl font-semibold">Your Apprentices</h2>
            <img src="/static/logo.png" class="h-20 w-auto">
        </div>
    '''
    if students:
        for s in students:
            grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s["id"],)).fetchall()
            html += f'''
            <div class="bg-white border-2 rounded-3xl p-12 mb-12">
                <h3 class="text-4xl font-semibold mb-8">{s["full_name"]} — {s["program"]}</h3>
            '''
            if grades:
                html += '<table class="w-full text-2xl"><thead><tr class="border-b text-left text-gray-600"><th class="py-5">Module</th><th>Grade</th><th>Hours</th><th>Date</th></tr></thead><tbody>'
                for g in grades:
                    html += f'<tr class="border-b"><td class="py-5">{g["module_name"] or "-"}</td><td>{g["grade"] or "-"}</td><td>{g["hours_attended"] or "-"}</td><td class="text-gray-500">{g["recorded_date"]}</td></tr>'
                html += '</tbody></table>'
            else:
                html += '<p class="text-3xl text-gray-500">No grades recorded yet.</p>'
            html += '</div>'
    else:
        html += '<p class="text-3xl">No students found for this contractor email.</p>'
    html += '''
        <div class="mt-12"><a href="/logout" class="text-red-600 hover:underline text-3xl">Logout</a></div>
    </div>
    '''
    conn.close()
    return html

# ====================== INSTRUCTOR DASHBOARD ======================
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
            conn.execute("UPDATE grades_hours SET module_name=?, grade=?, hours_attended=? WHERE id=?", 
                        (request.form.get("edit_module_name"), request.form.get("edit_grade"), request.form.get("edit_hours_attended") or 0, edit_id))
            conn.commit()
            flash("Record updated.")
        else:
            conn.execute("""
                INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (request.form.get("student_id"), request.form.get("module_name"), request.form.get("grade"), 
                  request.form.get("hours_attended") or 0, session.get("identifier", "Instructor"), datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            flash("Record saved!")

    html = f'''
    <div class="max-w-7xl mx-auto mt-8 px-12">
        <div class="flex justify-between items-center mb-12">
            <h2 class="text-6xl font-semibold">Instructor Dashboard</h2>
            <div class="flex items-center gap-10">
                <img src="/static/logo.png" class="h-20 w-auto">
                <a href="/change_password" class="text-emerald-600 hover:underline text-3xl">Change Password</a>
                <a href="/logout" class="text-red-600 hover:underline text-3xl">Logout</a>
            </div>
        </div>
    '''
    for s in students:
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s["id"],)).fetchall()
        html += f'''
        <div class="bg-white border-2 rounded-3xl p-12 mb-12">
            <h3 class="text-4xl font-semibold mb-10">{s["full_name"]}</h3>
            <form method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
                <input type="hidden" name="student_id" value="{s["id"]}">
                <input type="text" name="module_name" placeholder="Module / Class" class="border-2 border-gray-300 rounded-3xl px-8 py-6 text-2xl">
                <input type="text" name="grade" placeholder="Grade" class="border-2 border-gray-300 rounded-3xl px-8 py-6 text-2xl">
                <input type="number" name="hours_attended" placeholder="Hours" class="border-2 border-gray-300 rounded-3xl px-8 py-6 text-2xl">
                <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white rounded-3xl text-2xl font-semibold">Save New Record</button>
            </form>
        '''
        if grades:
            html += '<div><h4 class="text-3xl font-semibold mb-6 text-gray-700">Previous Records</h4><table class="w-full text-2xl"><thead><tr class="border-b text-left text-gray-600"><th class="py-5">Module</th><th>Grade</th><th>Hours</th><th>Date</th><th style="width:260px;"></th></tr></thead><tbody>'
            for g in grades:
                html += f'''
                    <tr class="border-b">
                        <td class="py-5">{g["module_name"] or "-"}</td>
                        <td>{g["grade"] or "-"}</td>
                        <td>{g["hours_attended"] or "-"}</td>
                        <td class="text-gray-500">{g["recorded_date"]}</td>
                        <td>
                            <form method="POST" class="inline">
                                <input type="hidden" name="edit_id" value="{g["id"]}">
                                <input type="text" name="edit_module_name" value="{g["module_name"] or ""}" class="border rounded-2xl px-4 py-3 text-xl w-36">
                                <input type="text" name="edit_grade" value="{g["grade"] or ""}" class="border rounded-2xl px-4 py-3 text-xl w-24">
                                <input type="number" name="edit_hours_attended" value="{g["hours_attended"] or ""}" class="border rounded-2xl px-4 py-3 text-xl w-24">
                                <button type="submit" class="text-emerald-600 hover:text-emerald-700 ml-3 text-xl">Save</button>
                            </form>
                            <form method="POST" class="inline ml-4">
                                <input type="hidden" name="delete_id" value="{g["id"]}">
                                <button type="submit" class="text-red-600 hover:text-red-700 text-xl">Delete</button>
                            </form>
                        </td>
                    </tr>
                '''
            html += '</tbody></table></div>'
        else:
            html += '<p class="text-2xl text-gray-500 mt-2">No records yet for this student.</p>'
        html += '</div>'
    conn.close()
    html += '</div>'
    return html

if __name__ == "__main__":
    app.run(debug=True)
