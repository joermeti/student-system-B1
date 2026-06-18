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

# ==================== HOME ====================
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

    return """
    <div class="max-w-2xl mx-auto mt-10 bg-white p-10 rounded-3xl shadow-xl border">
        <h2 class="text-3xl font-semibold mb-8">Enroll New Student</h2>
        <form method="POST" class="space-y-5">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                    <label class="block text-sm mb-1 text-gray-600">Full Name *</label>
                    <input type="text" name="full_name" required class="w-full border rounded-2xl px-4 py-3">
                </div>
                <div>
                    <label class="block text-sm mb-1 text-gray-600">Email *</label>
                    <input type="email" name="email" required class="w-full border rounded-2xl px-4 py-3">
                </div>
            </div>
            <div>
                <label class="block text-sm mb-1 text-gray-600">Phone</label>
                <input type="text" name="phone" class="w-full border rounded-2xl px-4 py-3">
            </div>
            <div>
                <label class="block text-sm mb-1 text-gray-600">Program *</label>
                <select name="program" required class="w-full border rounded-2xl px-4 py-3">
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
                <label class="block text-sm mb-1 text-gray-600">Payment Plan</label>
                <input type="text" name="payment_plan" value="Interest-Free 5-Month Plan" class="w-full border rounded-2xl px-4 py-3">
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                    <label class="block text-sm mb-1 text-gray-600">Contractor Name</label>
                    <input type="text" name="contractor_name" class="w-full border rounded-2xl px-4 py-3">
                </div>
                <div>
                    <label class="block text-sm mb-1 text-gray-600">Contractor Email</label>
                    <input type="email" name="contractor_email" class="w-full border rounded-2xl px-4 py-3">
                </div>
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
            <a href="/login" class="text-emerald-600 hover:underline">Go to Login</a>
        </div>
    </div>
    """


# ==================== INSTRUCTOR REGISTRATION ====================
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

    return """
    <div class="max-w-md mx-auto mt-20 bg-white p-10 rounded-3xl shadow-xl border">
        <h2 class="text-3xl font-semibold mb-8 text-center">Register as Instructor</h2>
        <form method="POST" class="space-y-6">
            <div>
                <label class="block text-sm mb-2 text-gray-600 font-medium">Choose Username</label>
                <input type="text" name="username" required class="w-full border border-gray-300 rounded-2xl px-5 py-4 text-lg">
            </div>
            <div>
                <label class="block text-sm mb-2 text-gray-600 font-medium">Choose Password</label>
                <input type="password" name="password" required class="w-full border border-gray-300 rounded-2xl px-5 py-4 text-lg">
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-4 rounded-2xl text-lg font-medium">
                Create Account
            </button>
        </form>
        <div class="mt-6 text-center">
            <a href="/login" class="text-emerald-600 hover:underline text-sm">Back to Login</a>
        </div>
    </div>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

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
    conn.close()

    if not student:
        return redirect(url_for("login"))

    return f"""
    <div class="max-w-4xl mx-auto mt-10 px-6">
        <h2 class="text-3xl font-semibold">Welcome, {student['full_name']}!</h2>
        <div class="mt-8 bg-white border rounded-3xl p-8">
            <h3 class="font-semibold text-lg mb-4">Your Information</h3>
            <p><strong>Program:</strong> {student['program']}</p>
            <p><strong>Payment Plan:</strong> {student['payment_plan']}</p>
        </div>
        <div class="mt-6">
            <a href="/logout" class="text-red-600 hover:underline">Logout</a>
        </div>
    </div>
    """

# ==================== CONTRACTOR DASHBOARD ====================
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
        html += "<p>No students found for this contractor email.</p>"
    html += "<br><a href='/logout' class='text-red-600'>Logout</a>"
    return html

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
                UPDATE grades_hours 
                SET module_name = ?, grade = ?, hours_attended = ?
                WHERE id = ?
            """, (module_name, grade, hours, edit_id))
            conn.commit()
            flash("Record updated successfully.")
        else:
            conn.execute("""
                INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                request.form.get("student_id"),
                request.form.get("module_name"),
                request.form.get("grade"),
                request.form.get("hours_attended") or 0,
                session.get("identifier", "Instructor"),
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
            conn.commit()
            flash("Record saved!")

    html = f"""
    <div class="max-w-6xl mx-auto mt-8 px-6">
        <div class="flex justify-between items-center mb-8">
            <h2 class="text-3xl font-semibold">Instructor Dashboard</h2>
            <div class="space-x-4">
                <a href="/change_password" class="text-emerald-600 hover:underline">Change Password</a>
                <a href="/logout" class="text-red-600 hover:underline">Logout</a>
            </div>
        </div>
    """

    for s in students:
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()

        html += f"""
        <div class="bg-white border rounded-3xl p-8 mb-8 shadow-sm">
            <h3 class="text-2xl font-semibold mb-6">{s['full_name']}</h3>

            <form method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <input type="hidden" name="student_id" value="{s['id']}">
                <input type="text" name="module_name" placeholder="Module / Class" class="border rounded-2xl px-4 py-3">
                <input type="text" name="grade" placeholder="Grade" class="border rounded-2xl px-4 py-3">
                <input type="number" name="hours_attended" placeholder="Hours" class="border rounded-2xl px-4 py-3">
                <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl">Save New Record</button>
            </form>
        """

        if grades:
            html += """
            <div>
                <h4 class="font-medium mb-3 text-gray-700">Previous Records</h4>
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b text-left text-gray-500">
                            <th class="py-2">Module</th>
                            <th>Grade</th>
                            <th>Hours</th>
                            <th>Date</th>
                            <th style="width: 140px;"></th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for g in grades:
                html += f"""
                    <tr class="border-b">
                        <td class="py-3">{g['module_name'] or '-'}</td>
                        <td>{g['grade'] or '-'}</td>
                        <td>{g['hours_attended'] or '-'}</td>
                        <td class="text-gray-500">{g['recorded_date']}</td>
                        <td>
                            <form method="POST" class="inline">
                                <input type="hidden" name="edit_id" value="{g['id']}">
                                <input type="text" name="edit_module_name" value="{g['module_name'] or ''}" class="border rounded px-2 py-1 text-sm w-28">
                                <input type="text" name="edit_grade" value="{g['grade'] or ''}" class="border rounded px-2 py-1 text-sm w-16">
                                <input type="number" name="edit_hours_attended" value="{g['hours_attended'] or ''}" class="border rounded px-2 py-1 text-sm w-16">
                                <button type="submit" class="text-emerald-600 hover:text-emerald-700 text-sm ml-1">Save</button>
                            </form>
                            <form method="POST" class="inline ml-2">
                                <input type="hidden" name="delete_id" value="{g['id']}">
                                <button type="submit" class="text-red-600 hover:text-red-700 text-sm">Delete</button>
                            </form>
                        </td>
                    </tr>
                """
            html += "</tbody></table></div>"
        else:
            html += "<p class='text-gray-500 text-sm mt-2'>No records yet.</p>"

        html += "</div>"

    conn.close()
    html += "</div>"
    return html

# ==================== CHANGE PASSWORD ====================
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if session.get("role") != "instructor":
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            flash("All fields are required.")
            return redirect(url_for("change_password"))

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

    return """
    <div class="max-w-md mx-auto mt-10 bg-white p-10 rounded-3xl shadow-xl border">
        <h2 class="text-3xl font-semibold mb-8">Change Password</h2>
        <form method="POST" class="space-y-5">
            <div>
                <label class="block text-sm mb-1 text-gray-600">Current Password</label>
                <input type="password" name="current_password" required class="w-full border rounded-2xl px-4 py-3">
            </div>
            <div>
                <label class="block text-sm mb-1 text-gray-600">New Password</label>
                <input type="password" name="new_password" required class="w-full border rounded-2xl px-4 py-3">
            </div>
            <div>
                <label class="block text-sm mb-1 text-gray-600">Confirm New Password</label>
                <input type="password" name="confirm_password" required class="w-full border rounded-2xl px-4 py-3">
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-3 rounded-2xl font-medium mt-4">
                Change Password
            </button>
        </form>
        <div class="mt-6">
            <a href="/instructor" class="text-emerald-600 hover:underline">Back to Dashboard</a>
        </div>
    </div>
    """

if __name__ == "__main__":
    app.run(debug=True)
