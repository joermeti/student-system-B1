from flask import Flask, request, redirect, url_for, flash, session
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
            program TEXT,
            payment_plan TEXT,
            contractor_name TEXT,
            contractor_email TEXT,
            enrollment_date TEXT
        )
    """)
    conn.execute("""
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
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return """
    <div class="max-w-5xl mx-auto px-6 py-12">
        <div class="flex justify-between items-center mb-10">
            <div>
                <h1 class="text-5xl font-bold tracking-tight text-emerald-700">RMETI</h1>
                <p class="text-xl text-gray-600">Rocky Mountain Electrical Training Institute</p>
            </div>
            <div class="space-x-4">
                <a href="/enroll" class="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-2xl font-medium">Enroll Student</a>
                <a href="/login" class="bg-gray-800 hover:bg-black text-white px-6 py-3 rounded-2xl font-medium">Login</a>
            </div>
        </div>
    </div>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        identifier = request.form.get("identifier")
        session["role"] = role
        session["identifier"] = identifier

        if role == "student":
            conn = get_db()
            student = conn.execute("SELECT * FROM students WHERE email = ?", (identifier,)).fetchone()
            conn.close()
            if student:
                session["student_id"] = student["id"]
                return redirect(url_for("student_dashboard"))
            flash("Student not found.")
            return redirect(url_for("login"))
        return redirect(url_for(f"{role}_dashboard"))

    return """
    <div class="max-w-md mx-auto mt-20 bg-white p-10 rounded-3xl shadow-xl border">
        <h2 class="text-3xl font-semibold mb-10 text-center">Login</h2>
        
        <form method="POST" class="space-y-8">
            <div>
                <label class="block text-sm mb-2 text-gray-600 font-medium">I am a</label>
                <select name="role" class="w-full border border-gray-300 rounded-2xl px-5 py-4 text-lg">
                    <option value="student">Student</option>
                    <option value="contractor">Contractor</option>
                    <option value="instructor">Instructor</option>
                </select>
            </div>

            <div>
                <label class="block text-sm mb-2 text-gray-600 font-medium">Email or Name</label>
                <input type="text" name="identifier" required class="w-full border border-gray-300 rounded-2xl px-5 py-4 text-lg">
            </div>

            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-4 rounded-2xl text-lg font-medium mt-2">Login</button>
        </form>
    </div>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("login"))

    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()

    if not student:
        return redirect(url_for("login"))

    return f"""
    <div class="max-w-4xl mx-auto mt-10 px-6">
        <h2 class="text-3xl font-semibold">Welcome, {student['full_name']}!</h2>
        
        <div class="mt-8 bg-white border rounded-3xl p-8 shadow-sm">
            <h3 class="font-semibold text-lg mb-4">Your Information</h3>
            <div class="space-y-2 text-gray-700">
                <p><span class="font-medium text-gray-500">Program:</span> {student['program']}</p>
                <p><span class="font-medium text-gray-500">Payment Plan:</span> {student['payment_plan']}</p>
            </div>
        </div>

        <div class="mt-6">
            <a href="/logout" class="text-red-600 hover:text-red-700 hover:underline">Logout</a>
        </div>
    </div>
    """
@app.route("/contractor")
def contractor_dashboard():
    if session.get("role") != "contractor":
        return redirect(url_for("login"))
    email = session.get("identifier")
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name", (email,)).fetchall()
    conn.close()
    html = f"<h2 class='text-3xl font-semibold mb-6'>Your Apprentices</h2>"
    if students:
        for s in students:
            html += f"<div class='mb-3'>{s['full_name']} — {s['program']}</div>"
    else:
        html += "<p>No students found.</p>"
    html += "<br><a href='/logout' class='text-red-600'>Logout</a>"
    return html

@app.route("/instructor", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))
    conn = get_db()
    students = conn.execute("SELECT * FROM students ORDER BY program, full_name").fetchall()

    if request.method == "POST":
        if "delete_id" in request.form:
            conn.execute("DELETE FROM grades_hours WHERE id = ?", (request.form.get("delete_id"),))
            conn.commit()
            flash("Record deleted.")
        else:
            conn.execute("""
                INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (request.form.get("student_id"), request.form.get("module_name"), request.form.get("grade"), request.form.get("hours_attended") or 0, session.get("identifier", "Instructor"), datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            flash("Record saved!")

    programs = {}
    for s in students:
        prog = s['program'] or "Unassigned"
        if prog not in programs:
            programs[prog] = []
        programs[prog].append(s)

    html = "<div class='max-w-6xl mx-auto mt-8 px-6'><h2 class='text-3xl font-semibold mb-8'>Instructor Dashboard</h2>"
    for program_name, student_list in programs.items():
        html += f"<h3 class='text-2xl font-semibold mb-4 text-emerald-700'>{program_name}</h3>"
        for s in student_list:
            grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
            html += f"""
            <div class="bg-white border rounded-3xl p-8 mb-6 shadow-sm">
                <h4 class="text-xl font-semibold mb-4">{s['full_name']}</h4>
                <form method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <input type="hidden" name="student_id" value="{s['id']}">
                    <input type="text" name="module_name" placeholder="Module / Class" class="border rounded-2xl px-4 py-3">
                    <input type="text" name="grade" placeholder="Grade" class="border rounded-2xl px-4 py-3">
                    <input type="number" name="hours_attended" placeholder="Hours" class="border rounded-2xl px-4 py-3">
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl">Save Record</button>
                </form>
            """
            if grades:
                html += "<h5 class='font-medium mb-2 text-gray-700'>Previous Records</h5><table class='w-full text-sm'><thead><tr class='border-b text-left text-gray-500'><th class='py-2'>Module</th><th>Grade</th><th>Hours</th><th>Date</th><th></th></tr></thead><tbody>"
                for g in grades:
                    html += f"""<tr class='border-b'><td class='py-3'>{g['module_name'] or '-'}</td><td>{g['grade'] or '-'}</td><td>{g['hours_attended'] or '-'}</td><td class='text-gray-500'>{g['recorded_date']}</td><td><form method='POST' class='inline'><input type='hidden' name='delete_id' value='{g['id']}'><button type='submit' class='text-red-600 hover:text-red-700 text-sm'>Delete</button></form></td></tr>"""
                html += "</tbody></table>"
            else:
                html += "<p class='text-gray-500 text-sm mt-2'>No records yet.</p>"
            html += "</div>"
    conn.close()
    html += "<a href='/logout' class='text-red-600'>Logout</a></div>"
    return html

@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        program = request.form.get("program")
        payment_plan = request.form.get("payment_plan")
        contractor_name = request.form.get("contractor_name")
        contractor_email = request.form.get("contractor_email")

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
            flash("Email already exists.")
        finally:
            conn.close()

    return """
    <div class="max-w-2xl mx-auto mt-10 bg-white p-10 rounded-3xl shadow-xl border">
        <h2 class="text-3xl font-semibold mb-8">Enroll New Student</h2>
        <form method="POST" class="space-y-5">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div><label class="block text-sm mb-1 text-gray-600">Full Name</label><input type="text" name="full_name" required class="w-full border rounded-2xl px-4 py-3"></div>
                <div><label class="block text-sm mb-1 text-gray-600">Email</label><input type="email" name="email" required class="w-full border rounded-2xl px-4 py-3"></div>
            </div>
            <div><label class="block text-sm mb-1 text-gray-600">Phone</label><input type="text" name="phone" class="w-full border rounded-2xl px-4 py-3"></div>
            <div><label class="block text-sm mb-1 text-gray-600">Program</label>
                <select name="program" class="w-full border rounded-2xl px-4 py-3">
                    <option>Fast Track Journeyman semester 1</option>
                    <option>Fast Track Journeyman semester 2</option>
                    <option>Main Program semester 1</option>
                    <option>Main Program semester 2</option>
                    <option>Main Program semester 3</option>
                    <option>Main Program semester 4</option>
                </select>
            </div>
            <div><label class="block text-sm mb-1 text-gray-600">Payment Plan</label><input type="text" name="payment_plan" value="Interest-Free 5-Month Plan" class="w-full border rounded-2xl px-4 py-3"></div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div><label class="block text-sm mb-1 text-gray-600">Contractor Name</label><input type="text" name="contractor_name" class="w-full border rounded-2xl px-4 py-3"></div>
                <div><label class="block text-sm mb-1 text-gray-600">Contractor Email</label><input type="email" name="contractor_email" class="w-full border rounded-2xl px-4 py-3"></div>
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-4 rounded-2xl font-medium mt-4">Enroll Student</button>
        </form>
    </div>
    """

@app.route("/success")
def success():
    return """
    <div class="max-w-md mx-auto mt-16 text-center">
        <h2 class="text-3xl font-semibold text-emerald-700">Enrollment Successful!</h2>
        <div class="mt-8 space-x-4">
            <a href="/enroll" class="text-emerald-600 hover:underline">Enroll Another</a>
            <a href="/instructor" class="text-emerald-600 hover:underline">Go to Instructor Page</a>
        </div>
    </div>
    """

if __name__ == "__main__":
    app.run(debug=True)
