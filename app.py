import os
import secrets
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.message import EmailMessage
from urllib.parse import quote

from flask import Flask, request, redirect, url_for, flash, session, get_flashed_messages
import stripe
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__, static_folder='static', static_url_path='/static')

# ==================== SECURITY / SESSION CONFIG ====================
# Never ship a hardcoded secret key. If FLASK_SECRET_KEY isn't set we generate a
# random one for this run (sessions reset on restart, which is fine in dev).
SECRET = os.environ.get("FLASK_SECRET_KEY")
if not SECRET:
    SECRET = secrets.token_hex(32)
    print("[WARNING] FLASK_SECRET_KEY not set - using a temporary random key. "
          "Sessions will reset on restart. Set FLASK_SECRET_KEY for production.")
app.secret_key = SECRET

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,                                  # JS can't read the cookie
    SESSION_COOKIE_SAMESITE="Lax",                                 # basic CSRF mitigation
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",  # set =1 behind HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

# ==================== RATE LIMITER ====================
# In-memory storage is fine for a single dev server. For production behind
# multiple workers, point storage_uri at Redis, e.g. "redis://localhost:6379".
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
)

@app.errorhandler(429)
def ratelimit_handler(e):
    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-14 max-w-xl mx-auto text-center mt-12">
        <h2 class="text-3xl font-bold text-red-700 mb-4">Too Many Attempts</h2>
        <p class="text-gray-600 text-lg mb-8">You've made too many requests in a short time. Please wait a few minutes and try again.</p>
        <a href="/" class="btn-dark">Back to Home</a>
    </div>
    """
    return render_page("Slow Down", content), 429

# ==================== STRIPE CONFIGURATION ====================
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# ==================== EMAIL ====================
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or "no-reply@rmeti.local")

def send_email(to_address, subject, body):
    """Send a plain-text email. If SMTP isn't configured, log it to the console
    so the verification/reset flows are still testable in development."""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD):
        print("=" * 64)
        print(f"[DEV EMAIL]  To: {to_address}")
        print(f"[DEV EMAIL]  Subject: {subject}")
        print("-" * 64)
        print(body)
        print("=" * 64)
        return True

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_address
        msg.set_content(body)

        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            server.starttls()
        try:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        finally:
            server.quit()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

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
    c.execute("""CREATE TABLE IF NOT EXISTS instructors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        is_verified INTEGER DEFAULT 0,
        verify_code_hash TEXT,
        verify_expiry TEXT,
        verify_attempts INTEGER DEFAULT 0,
        reset_token_hash TEXT,
        reset_expiry TEXT,
        created_date TEXT
    )""")
    c.execute("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount_paid TEXT, status TEXT, date_recorded TEXT)")
    conn.commit()
    conn.close()
    migrate_db()

def migrate_db():
    """Add any missing instructor columns for databases created before the
    email-verification feature existed."""
    conn = get_db()
    c = conn.cursor()
    existing = {row[1] for row in c.execute("PRAGMA table_info(instructors)").fetchall()}
    needed = {
        "full_name": "TEXT",
        "email": "TEXT",
        "password": "TEXT",
        "is_verified": "INTEGER DEFAULT 0",
        "verify_code_hash": "TEXT",
        "verify_expiry": "TEXT",
        "verify_attempts": "INTEGER DEFAULT 0",
        "reset_token_hash": "TEXT",
        "reset_expiry": "TEXT",
        "created_date": "TEXT",
    }
    for col, decl in needed.items():
        if col not in existing:
            c.execute(f"ALTER TABLE instructors ADD COLUMN {col} {decl}")
    # Enforce email uniqueness even on migrated tables (NULLs stay distinct in SQLite).
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_instructor_email ON instructors(email)")
    conn.commit()
    conn.close()

init_db()

# ==================== SECURITY HELPERS ====================
def gen_code():
    """Cryptographically-random 6-digit verification code."""
    return f"{secrets.randbelow(1000000):06d}"

def is_expired(expiry_str):
    if not expiry_str:
        return True
    try:
        return datetime.now() > datetime.fromisoformat(expiry_str)
    except Exception:
        return True

def valid_email(email):
    # Deliberately simple: a real address gets verified by the code email anyway.
    return "@" in email and "." in email.split("@")[-1] and len(email) <= 254

def password_problem(pw):
    if len(pw) < 8:
        return "Password must be at least 8 characters long."
    return None

def instructor_names(conn):
    """email -> display name lookup so students/contractors see names, not emails."""
    rows = conn.execute("SELECT email, full_name FROM instructors").fetchall()
    return {r["email"]: (r["full_name"] or r["email"]) for r in rows}

# ==================== MASTER LAYOUT ENGINE ====================
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

# ==================== ENROLL & STRIPE REDIRECT ====================
@app.route("/enroll", methods=["GET", "POST"])
@limiter.limit("20 per hour", methods=["POST"])
def enroll():
    if request.method == "POST":
        full_name = request.form.get("full_name").strip()
        email = request.form.get("email").strip()
        program = request.form.get("program").strip()
        payment_plan = request.form.get("payment_plan").strip()

        conn = get_db()
        try:
            cursor = conn.cursor()

            # 1. CHECK IF STUDENT ALREADY EXISTS (Fixes the Stripe Back-Out Bug)
            existing = cursor.execute("SELECT id FROM students WHERE email = ?", (email,)).fetchone()

            if existing:
                student_id = existing['id']
                cursor.execute("""
                    UPDATE students
                    SET full_name=?, phone=?, program=?, payment_plan=?, contractor_name=?, contractor_email=?, enrollment_date=?
                    WHERE id=?
                """, (full_name, request.form.get("phone").strip(), program, payment_plan,
                      request.form.get("contractor_name").strip(), request.form.get("contractor_email").strip(), datetime.now().strftime("%Y-%m-%d"), student_id))
            else:
                cursor.execute("""
                    INSERT INTO students (full_name, email, phone, program, payment_plan, contractor_name, contractor_email, enrollment_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (full_name, email, request.form.get("phone").strip(), program, payment_plan,
                      request.form.get("contractor_name").strip(), request.form.get("contractor_email").strip(), datetime.now().strftime("%Y-%m-%d")))
                student_id = cursor.lastrowid

            conn.commit()

            # 2. DETERMINE COST
            total_cost = 2400
            if "Fast Track" in program:
                total_cost = 2900

            # 3. BUILD STRIPE CHECKOUT
            if "Paid in Full" in payment_plan:
                payment_amount_cents = total_cost * 100
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    customer_email=email,
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': payment_amount_cents,
                            'product_data': {
                                'name': f'RMETI Tuition - {program}',
                                'description': f'One-Time Payment: {payment_plan}',
                            },
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    client_reference_id=str(student_id),
                    success_url=request.host_url + 'payment_success?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.host_url + 'enroll',
                )
            else:
                try:
                    months = int(payment_plan.split('-')[0])
                    monthly_payment = total_cost / months
                    payment_amount_cents = int(monthly_payment * 100)
                except Exception:
                    payment_amount_cents = 50000
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    customer_email=email,
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': payment_amount_cents,
                            'recurring': {'interval': 'month'},
                            'product_data': {
                                'name': f'RMETI Tuition - {program}',
                                'description': f'Monthly Auto-Pay: {payment_plan}',
                            },
                        },
                        'quantity': 1,
                    }],
                    mode='subscription',
                    client_reference_id=str(student_id),
                    success_url=request.host_url + 'payment_success?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.host_url + 'enroll',
                )

            return redirect(checkout_session.url, code=303)

        except Exception as e:
            flash(f"Payment Gateway Error: Please ensure Stripe API keys are configured properly. Error details: {str(e)}")
            return redirect(url_for("enroll"))
        finally:
            conn.close()

    # ========== GET: show the enrollment form ==========
    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-10 md:p-12 max-w-2xl mx-auto mt-8">
        <h2 class="text-3xl font-bold text-emerald-800 mb-8 text-center">Student Enrollment</h2>
        <form method="POST" class="space-y-6">
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Full Name</label>
                <input type="text" name="full_name" required class="input-std">
            </div>
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Email</label>
                <input type="email" name="email" required class="input-std">
            </div>
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Phone</label>
                <input type="tel" name="phone" required class="input-std">
            </div>
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Program</label>
                <select name="program" required class="input-std bg-white">
                    <option value="Standard Apprenticeship">Standard Apprenticeship</option>
                    <option value="Fast Track Apprenticeship">Fast Track Apprenticeship</option>
                </select>
            </div>
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Payment Plan</label>
                <select name="payment_plan" required class="input-std bg-white">
                    <option value="Paid in Full">Paid in Full</option>
                    <option value="6-month">6-Month Plan</option>
                    <option value="12-month">12-Month Plan</option>
                    <option value="24-month">24-Month Plan</option>
                </select>
            </div>
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Contractor / Employer Name</label>
                <input type="text" name="contractor_name" required class="input-std">
            </div>
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Contractor / Employer Email</label>
                <input type="email" name="contractor_email" required class="input-std">
            </div>
            <div class="pt-4">
                <button type="submit" class="btn-green w-full py-4 text-xl">Continue to Payment</button>
            </div>
        </form>
        <div class="mt-8 text-center"><a href="/" class="text-gray-500 hover:text-emerald-700 font-medium hover:underline text-lg">Back to Home</a></div>
    </div>
    """
    return render_page("Enroll", content)

# ==================== PAYMENT SUCCESS ====================
@app.route("/payment_success")
def payment_success():
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('home'))

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        student_id = checkout_session.client_reference_id
        amount_paid = f"${checkout_session.amount_total / 100:.2f}"

        conn = get_db()
        exists = conn.execute("SELECT id FROM payments WHERE student_id = ? AND date_recorded = ? AND amount_paid = ?",
                              (student_id, datetime.now().strftime("%Y-%m-%d"), amount_paid)).fetchone()
        if not exists:
            conn.execute("INSERT INTO payments (student_id, amount_paid, status, date_recorded) VALUES (?, ?, ?, ?)",
                         (student_id, amount_paid, "Paid", datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
        conn.close()
    except Exception as e:
        flash("There was an issue verifying your payment, but your enrollment was saved. Please contact administration.")
        return redirect(url_for("home"))

    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-14 max-w-2xl mx-auto text-center mt-12">
        <h2 class="text-4xl md:text-5xl font-bold text-emerald-700 mb-6">Payment & Enrollment Successful!</h2>
        <p class="text-gray-600 text-xl mb-10">Your transaction has been securely processed and recorded.</p>
        <div class="flex justify-center">
            <a href="/login" class="bg-gray-800 hover:bg-gray-900 text-white font-bold px-8 py-3 rounded-lg text-xl transition">Go to Login Portal</a>
        </div>
    </div>
    """
    return render_page("Success", content)

# ==================== LOGIN ====================
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        role = request.form.get('role', '')
        idnt = request.form.get('identifier', '').strip()
        conn = get_db()

        if role == "instructor":
            email = idnt.lower()
            inst = conn.execute("SELECT * FROM instructors WHERE email = ?", (email,)).fetchone()
            conn.close()
            if inst and inst['password'] and check_password_hash(inst['password'], request.form.get('password', '')):
                if not inst['is_verified']:
                    session['pending_email'] = email
                    flash("Please verify your email before logging in. Enter the code we sent you.")
                    return redirect(url_for('verify_instructor'))
                session.update({'role': role, 'identifier': email})
                return redirect(url_for('instructor_dashboard'))
            flash("Invalid instructor credentials.")

        elif role == "student":
            s = conn.execute("SELECT * FROM students WHERE email = ?", (idnt.lower(),)).fetchone()
            conn.close()
            if s:
                session.update({'role': role, 'identifier': idnt.lower(), 'student_id': s['id']})
                return redirect(url_for('student_dashboard'))
            flash("No student found with that email address.")

        elif role == "contractor":
            conn.close()
            session.update({'role': role, 'identifier': idnt.lower()})
            return redirect(url_for('contractor_dashboard'))

        else:
            conn.close()
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
                <label class="block text-base font-bold text-gray-700 mb-2">Email Address</label>
                <input type="email" name="identifier" required class="input-std">
            </div>
            <div id="passwordField" style="display: none;">
                <label class="block text-base font-bold text-gray-700 mb-2">Password</label>
                <input type="password" name="password" class="input-std">
                <div class="mt-2 text-right">
                    <a href="/forgot_password" class="text-emerald-600 font-semibold hover:underline text-base">Forgot password?</a>
                </div>
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
@limiter.limit("5 per hour", methods=["POST"])
def register_instructor():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            flash("Please fill in your name, email, and a password.")
            return redirect(url_for("register_instructor"))
        if not valid_email(email):
            flash("Please enter a valid email address.")
            return redirect(url_for("register_instructor"))
        pw_err = password_problem(password)
        if pw_err:
            flash(pw_err)
            return redirect(url_for("register_instructor"))

        conn = get_db()
        try:
            existing = conn.execute("SELECT id, is_verified FROM instructors WHERE email = ?", (email,)).fetchone()
            code = gen_code()
            code_hash = generate_password_hash(code)
            expiry = (datetime.now() + timedelta(minutes=15)).isoformat()
            hashed_pw = generate_password_hash(password)

            if existing and existing["is_verified"]:
                conn.close()
                flash("An account with that email already exists. Please log in or use 'Forgot password'.")
                return redirect(url_for("login"))
            elif existing:
                # Unverified signup that was never completed: refresh details + new code.
                conn.execute("""UPDATE instructors
                                SET full_name=?, password=?, verify_code_hash=?, verify_expiry=?, verify_attempts=0
                                WHERE email=?""",
                             (full_name, hashed_pw, code_hash, expiry, email))
            else:
                conn.execute("""INSERT INTO instructors
                                (full_name, email, password, is_verified, verify_code_hash, verify_expiry, verify_attempts, created_date)
                                VALUES (?, ?, ?, 0, ?, ?, 0, ?)""",
                             (full_name, email, hashed_pw, code_hash, expiry, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
        finally:
            conn.close()

        send_email(
            email,
            "Verify your RMETI instructor account",
            f"Hello {full_name},\n\n"
            f"Your RMETI verification code is: {code}\n\n"
            f"Enter this code on the verification page to activate your account. "
            f"It expires in 15 minutes.\n\n"
            f"If you didn't request this, you can ignore this email."
        )
        session['pending_email'] = email
        flash("We've emailed you a 6-digit verification code. Enter it below to activate your account.")
        return redirect(url_for("verify_instructor"))

    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-10 md:p-12 max-w-md mx-auto mt-12">
        <h2 class="text-3xl font-bold text-emerald-800 mb-8 text-center">Instructor Registration</h2>
        <form method="POST" class="space-y-6">
            <div><label class="block text-base font-bold text-gray-700 mb-2">Full Name</label><input type="text" name="full_name" required class="input-std"></div>
            <div><label class="block text-base font-bold text-gray-700 mb-2">Email Address</label><input type="email" name="email" required class="input-std"></div>
            <div><label class="block text-base font-bold text-gray-700 mb-2">Choose Password</label><input type="password" name="password" required minlength="8" class="input-std"><p class="text-sm text-gray-500 mt-2">At least 8 characters.</p></div>
            <div class="pt-4"><button type="submit" class="btn-green w-full py-4 text-xl">Create Account</button></div>
        </form>
        <div class="mt-8 text-center"><a href="/login" class="text-gray-500 hover:text-emerald-700 font-medium hover:underline text-lg">Back to Login</a></div>
    </div>
    """
    return render_page("Register", content)

# ==================== EMAIL VERIFICATION ====================
@app.route("/verify_instructor", methods=["GET", "POST"])
@limiter.limit("15 per hour", methods=["POST"])
def verify_instructor():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        code = request.form.get("code", "").strip()

        conn = get_db()
        inst = conn.execute("SELECT * FROM instructors WHERE email = ?", (email,)).fetchone()

        if not inst:
            conn.close()
            flash("No pending registration was found for that email.")
            return redirect(url_for("verify_instructor"))
        if inst["is_verified"]:
            conn.close()
            flash("This account is already verified. Please log in.")
            return redirect(url_for("login"))
        if (inst["verify_attempts"] or 0) >= 5:
            conn.close()
            flash("Too many incorrect attempts. Please register again to receive a fresh code.")
            return redirect(url_for("register_instructor"))
        if is_expired(inst["verify_expiry"]):
            conn.close()
            flash("That code has expired. Please register again to receive a new one.")
            return redirect(url_for("register_instructor"))

        if inst["verify_code_hash"] and check_password_hash(inst["verify_code_hash"], code):
            conn.execute("""UPDATE instructors
                            SET is_verified=1, verify_code_hash=NULL, verify_expiry=NULL, verify_attempts=0
                            WHERE email=?""", (email,))
            conn.commit()
            conn.close()
            session.pop('pending_email', None)
            flash("Email verified! Your account is now active. Please log in.")
            return redirect(url_for("login"))
        else:
            conn.execute("UPDATE instructors SET verify_attempts = COALESCE(verify_attempts, 0) + 1 WHERE email=?", (email,))
            conn.commit()
            conn.close()
            flash("Incorrect code. Please check your email and try again.")
            return redirect(url_for("verify_instructor"))

    prefill = session.get('pending_email', '')
    content = f"""
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-10 md:p-12 max-w-md mx-auto mt-12">
        <h2 class="text-3xl font-bold text-emerald-800 mb-4 text-center">Verify Your Email</h2>
        <p class="text-gray-600 text-center mb-8 text-lg">Enter the 6-digit code we sent to your email.</p>
        <form method="POST" class="space-y-6">
            <div><label class="block text-base font-bold text-gray-700 mb-2">Email Address</label><input type="email" name="email" value="{prefill}" required class="input-std"></div>
            <div><label class="block text-base font-bold text-gray-700 mb-2">Verification Code</label><input type="text" name="code" inputmode="numeric" pattern="[0-9]*" maxlength="6" required class="input-std text-center tracking-[0.5em] text-2xl font-bold"></div>
            <div class="pt-4"><button type="submit" class="btn-green w-full py-4 text-xl">Verify Account</button></div>
        </form>
        <div class="mt-8 text-center space-y-2">
            <a href="/register_instructor" class="block text-emerald-600 font-semibold hover:underline text-base">Didn't get a code? Register again to resend</a>
            <a href="/login" class="block text-gray-500 hover:text-emerald-700 font-medium hover:underline text-base">Back to Login</a>
        </div>
    </div>
    """
    return render_page("Verify Email", content)

# ==================== FORGOT PASSWORD ====================
@app.route("/forgot_password", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        conn = get_db()
        inst = conn.execute("SELECT id FROM instructors WHERE email = ? AND is_verified = 1", (email,)).fetchone()
        if inst:
            token = secrets.token_urlsafe(32)
            token_hash = generate_password_hash(token)
            expiry = (datetime.now() + timedelta(minutes=30)).isoformat()
            conn.execute("UPDATE instructors SET reset_token_hash=?, reset_expiry=? WHERE email=?",
                         (token_hash, expiry, email))
            conn.commit()
            base = request.host_url.rstrip('/')
            reset_link = f"{base}{url_for('reset_password')}?email={quote(email)}&token={token}"
            send_email(
                email,
                "Reset your RMETI password",
                f"Hello,\n\n"
                f"We received a request to reset your RMETI instructor password.\n\n"
                f"Reset your password here (link expires in 30 minutes):\n{reset_link}\n\n"
                f"If you didn't request this, you can safely ignore this email - "
                f"your password won't change."
            )
        conn.close()
        # Same response whether or not the email exists (prevents account enumeration).
        flash("If a verified account exists for that email, we've sent a password reset link.")
        return redirect(url_for("login"))

    content = """
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-10 md:p-12 max-w-md mx-auto mt-12">
        <h2 class="text-3xl font-bold text-emerald-800 mb-4 text-center">Reset Your Password</h2>
        <p class="text-gray-600 text-center mb-8 text-lg">Enter your account email and we'll send you a reset link.</p>
        <form method="POST" class="space-y-6">
            <div><label class="block text-base font-bold text-gray-700 mb-2">Email Address</label><input type="email" name="email" required class="input-std"></div>
            <div class="pt-4"><button type="submit" class="btn-green w-full py-4 text-xl">Send Reset Link</button></div>
        </form>
        <div class="mt-8 text-center"><a href="/login" class="text-gray-500 hover:text-emerald-700 font-medium hover:underline text-lg">Back to Login</a></div>
    </div>
    """
    return render_page("Forgot Password", content)

# ==================== RESET PASSWORD ====================
@app.route("/reset_password", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        token = request.form.get("token", "").strip()
        new_password = request.form.get("new_password", "")

        conn = get_db()
        inst = conn.execute("SELECT * FROM instructors WHERE email = ?", (email,)).fetchone()

        if (not inst or not inst["reset_token_hash"] or is_expired(inst["reset_expiry"])
                or not check_password_hash(inst["reset_token_hash"], token)):
            conn.close()
            flash("This reset link is invalid or has expired. Please request a new one.")
            return redirect(url_for("forgot_password"))

        pw_err = password_problem(new_password)
        if pw_err:
            conn.close()
            flash(pw_err)
            return redirect(url_for("reset_password", email=email, token=token))

        conn.execute("""UPDATE instructors
                        SET password=?, reset_token_hash=NULL, reset_expiry=NULL
                        WHERE email=?""",
                     (generate_password_hash(new_password), email))
        conn.commit()
        conn.close()
        flash("Your password has been reset. Please log in with your new password.")
        return redirect(url_for("login"))

    email = request.args.get("email", "")
    token = request.args.get("token", "")
    content = f"""
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-10 md:p-12 max-w-md mx-auto mt-12">
        <h2 class="text-3xl font-bold text-emerald-800 mb-8 text-center">Set a New Password</h2>
        <form method="POST" class="space-y-6">
            <input type="hidden" name="email" value="{email}">
            <input type="hidden" name="token" value="{token}">
            <div><label class="block text-base font-bold text-gray-700 mb-2">New Password</label><input type="password" name="new_password" required minlength="8" class="input-std"><p class="text-sm text-gray-500 mt-2">At least 8 characters.</p></div>
            <div class="pt-4"><button type="submit" class="btn-green w-full py-4 text-xl">Update Password</button></div>
        </form>
        <div class="mt-8 text-center"><a href="/login" class="text-gray-500 hover:text-emerald-700 font-medium hover:underline text-lg">Back to Login</a></div>
    </div>
    """
    return render_page("Reset Password", content)

# ==================== INSTRUCTOR SETTINGS ====================
@app.route("/instructor_settings", methods=["GET", "POST"])
def instructor_settings():
    if session.get('role') != 'instructor':
        return redirect(url_for('login'))
    email = session.get('identifier')
    conn = get_db()

    if request.method == "POST":
        if "update_profile" in request.form:
            new_name = request.form.get("new_name", "").strip()
            new_password = request.form.get("new_password", "").strip()

            if new_password:
                pw_err = password_problem(new_password)
                if pw_err:
                    conn.close()
                    flash(pw_err)
                    return redirect(url_for("instructor_settings"))
                conn.execute("UPDATE instructors SET full_name=?, password=? WHERE email=?",
                             (new_name, generate_password_hash(new_password), email))
            else:
                conn.execute("UPDATE instructors SET full_name=? WHERE email=?", (new_name, email))
            conn.commit()
            conn.close()
            flash("Profile updated successfully.")
            return redirect(url_for("instructor_dashboard"))

        elif "delete_account" in request.form:
            conn.execute("DELETE FROM instructors WHERE email=?", (email,))
            conn.commit()
            conn.close()
            session.clear()
            flash("Instructor account deleted permanently.")
            return redirect(url_for("home"))

    inst = conn.execute("SELECT * FROM instructors WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not inst:
        session.clear()
        return redirect(url_for('login'))

    content = f"""
    <div class="bg-white border border-gray-200 shadow-sm rounded-2xl p-10 md:p-12 max-w-lg mx-auto mt-12">
        <h2 class="text-3xl font-bold text-emerald-800 mb-8 border-b pb-4">Instructor Settings</h2>
        <form method="POST" class="space-y-6 mb-10">
            <input type="hidden" name="update_profile" value="1">
            <div>
                <label class="block text-base font-bold text-gray-700 mb-2">Email Address</label>
                <input type="text" value="{inst['email']}" disabled class="input-std bg-gray-100 text-gray-500 cursor-not-allowed">
                <p class="text-sm text-gray-500 mt-2">Your email is used to sign in and can't be changed here.</p>
            </div>
            <div><label class="block text-base font-bold text-gray-700 mb-2">Display Name</label><input type="text" name="new_name" value="{inst['full_name'] or ''}" required class="input-std"></div>
            <div><label class="block text-base font-bold text-gray-700 mb-2">Update Password</label><input type="password" name="new_password" minlength="8" placeholder="Leave blank to keep current password" class="input-std"></div>
            <div class="pt-4"><button type="submit" class="btn-green w-full py-4 text-xl">Save Changes</button></div>
        </form>
        <div class="mt-10 text-center"><a href="/instructor_dashboard" class="text-gray-500 hover:text-emerald-700 font-medium hover:underline text-lg">Back to Dashboard</a></div>
    </div>
    """
    return render_page("Instructor Settings", content)

# ==================== STUDENT DASHBOARD ====================
@app.route("/student_dashboard")
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    conn = get_db()
    s = conn.execute("SELECT * FROM students WHERE id = ?", (session.get('student_id'),)).fetchone()
    if not s:
        conn.close()
        return redirect(url_for('login'))

    grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
    payments = conn.execute("SELECT * FROM payments WHERE student_id = ? ORDER BY id DESC", (s['id'],)).fetchall()
    names = instructor_names(conn)
    conn.close()

    html = f"""
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <h2 class="text-3xl md:text-4xl font-bold text-emerald-800">Welcome, {s['full_name']}</h2>
        <a href="/logout" class="text-red-600 font-bold hover:underline bg-red-50 px-6 py-3 rounded-lg border border-red-100 text-lg">Logout</a>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div class="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
            <h3 class="text-2xl font-bold text-gray-800 mb-6 border-b pb-3">Enrollment Status</h3>
            <p class="text-lg mb-2"><strong>Program:</strong> {s['program']}</p>
            <p class="text-lg"><strong>Payment Plan:</strong> {s['payment_plan']}</p>
        </div>
        <div class="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
            <h3 class="text-2xl font-bold text-gray-800 mb-6 border-b pb-3">Payment History</h3>
    """
    if payments:
        html += "<ul class='space-y-3'>"
        for p in payments:
            html += f"<li class='flex justify-between items-center text-lg'><span class='text-gray-600'>{p['date_recorded']}</span> <span class='font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded'>{p['amount_paid']} - {p['status']}</span></li>"
        html += "</ul>"
    else:
        html += "<p class='text-gray-500 italic text-lg'>No recorded payments.</p>"

    html += """</div></div>
    <div class="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
        <h3 class="text-2xl font-bold text-gray-800 mb-6 border-b pb-3">Academic Record</h3>
    """
    if grades:
        html += """
        <div class="overflow-x-auto">
            <table class='w-full text-left text-lg'>
                <tr class='border-b-2 border-gray-200 bg-gray-50 text-gray-700'>
                    <th class='py-3 px-4 font-bold'>Module / Class</th>
                    <th class='py-3 px-4 font-bold'>Instructor</th>
                    <th class='py-3 px-4 font-bold'>Grade</th>
                    <th class='py-3 px-4 font-bold'>Hours</th>
                    <th class='py-3 px-4 font-bold'>Date</th>
                </tr>
        """
        for g in grades:
            instr = names.get(g['recorded_by'], g['recorded_by'])
            html += f"<tr class='border-b hover:bg-gray-50 transition'><td class='py-3 px-4'>{g['module_name']}</td><td class='py-3 px-4 text-emerald-700 font-semibold'>{instr}</td><td class='py-3 px-4 font-bold text-gray-900'>{g['grade']}</td><td class='py-3 px-4 font-medium'>{g['hours_attended']}</td><td class='py-3 px-4 text-gray-500 text-sm'>{g['recorded_date']}</td></tr>"
        html += "</table></div>"
    else:
        html += "<p class='text-gray-500 italic text-lg'>No grades recorded yet.</p>"
    html += "</div>"
    return render_page("Student Dashboard", html)

# ==================== CONTRACTOR DASHBOARD ====================
@app.route("/contractor_dashboard")
def contractor_dashboard():
    if session.get('role') != 'contractor':
        return redirect(url_for('login'))
    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE contractor_email = ? ORDER BY full_name", (session['identifier'],)).fetchall()
    names = instructor_names(conn)

    html = f"""
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <h2 class="text-3xl md:text-4xl font-bold text-emerald-800">Your Apprentices</h2>
        <a href="/logout" class="text-red-600 font-bold hover:underline bg-red-50 px-6 py-3 rounded-lg border border-red-100 text-lg">Logout</a>
    </div>
    """
    if not students:
        html += "<div class='bg-white p-8 rounded-2xl border border-gray-200 shadow-sm'><p class='text-lg text-gray-600'>No apprentices found for your email address.</p></div>"

    for s in students:
        html += f"<div class='bg-white border border-gray-200 rounded-2xl p-8 mb-8 shadow-sm'><h3 class='text-2xl font-bold text-gray-800 mb-2'>{s['full_name']}</h3><p class='text-emerald-700 font-bold text-lg mb-6'>{s['program']}</p>"
        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? ORDER BY recorded_date DESC", (s['id'],)).fetchall()
        if grades:
            html += "<div class='overflow-x-auto border rounded-lg border-gray-200'><table class='w-full text-left text-base'><tr class='border-b-2 border-gray-200 bg-gray-50 text-gray-700'><th class='py-3 px-4 font-bold'>Module / Class</th><th class='py-3 px-4 font-bold'>Instructor</th><th class='py-3 px-4 font-bold'>Grade</th><th class='py-3 px-4 font-bold'>Hours</th><th class='py-3 px-4 font-bold'>Date</th></tr>"
            for g in grades:
                instr = names.get(g['recorded_by'], g['recorded_by'])
                html += f"<tr class='border-b hover:bg-gray-50 transition'><td class='py-3 px-4'>{g['module_name']}</td><td class='py-3 px-4 text-emerald-700 font-semibold'>{instr}</td><td class='py-3 px-4 font-bold text-gray-900'>{g['grade']}</td><td class='py-3 px-4 font-medium'>{g['hours_attended']}</td><td class='py-3 px-4 text-gray-500 text-sm'>{g['recorded_date']}</td></tr>"
            html += "</table></div></div>"
        else:
            html += "<p class='text-gray-500 italic text-base'>No grades recorded yet.</p></div>"
    conn.close()
    return render_page("Contractor Dashboard", html)

# ==================== INSTRUCTOR DASHBOARD ====================
@app.route("/instructor_dashboard", methods=["GET", "POST"])
def instructor_dashboard():
    if session.get('role') != 'instructor':
        return redirect(url_for('login'))
    instructor_name = session.get('identifier')
    conn = get_db()

    if request.method == "POST":
        # DELETE STUDENT ENTIRELY
        if "delete_student_id" in request.form:
            student_id = request.form['delete_student_id']
            conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.execute("DELETE FROM grades_hours WHERE student_id = ?", (student_id,))
            conn.execute("DELETE FROM payments WHERE student_id = ?", (student_id,))
            flash("Student has been completely removed from the system.")

        # EDIT STUDENT INFO
        elif "edit_student_id" in request.form:
            try:
                conn.execute("UPDATE students SET full_name=?, email=?, program=?, payment_plan=? WHERE id=?",
                             (request.form['edit_s_name'], request.form['edit_s_email'], request.form['edit_s_program'], request.form['edit_s_plan'], request.form['edit_student_id']))
                flash("Student information updated successfully.")
            except sqlite3.IntegrityError:
                flash("Error: That email address is already in use by another student.")

        # DELETE GRADE
        elif "delete_id" in request.form:
            conn.execute("DELETE FROM grades_hours WHERE id = ? AND recorded_by = ?", (request.form['delete_id'], instructor_name))

        # EDIT GRADE
        elif "edit_id" in request.form:
            conn.execute("UPDATE grades_hours SET module_name=?, grade=?, hours_attended=? WHERE id=? AND recorded_by = ?",
                         (request.form['edit_module_name'], request.form['edit_grade'], request.form['edit_hours_attended'], request.form['edit_id'], instructor_name))

        # ADD GRADE
        elif "mod" in request.form:
            conn.execute("INSERT INTO grades_hours (student_id, module_name, grade, hours_attended, recorded_by, recorded_date) VALUES (?,?,?,?,?,?)",
                         (request.form['student_id'], request.form['mod'], request.form['grd'], request.form['hrs'], instructor_name, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

    students = conn.execute("SELECT * FROM students ORDER BY program, full_name").fetchall()

    html = """
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <h2 class="text-3xl md:text-4xl font-bold text-emerald-800">Instructor Dashboard</h2>
        <div class="flex gap-4 w-full md:w-auto">
            <a href="/instructor_settings" class="text-emerald-700 font-bold hover:underline bg-emerald-50 px-6 py-3 rounded-lg border border-emerald-100 text-lg w-full md:w-auto text-center">Settings</a>
            <a href="/logout" class="text-red-600 font-bold hover:underline bg-red-50 px-6 py-3 rounded-lg border border-red-100 text-lg w-full md:w-auto text-center">Logout</a>
        </div>
    </div>
    """
    for s in students:
        html += f"""
        <div class="bg-white border border-gray-200 rounded-2xl p-8 mb-10 shadow-sm">

            <div class="flex flex-col md:flex-row justify-between items-start mb-6 border-b border-gray-100 pb-4">
                <div>
                    <h3 class="text-2xl font-bold text-gray-800 mb-1">{s['full_name']}</h3>
                    <p class="text-lg text-emerald-700 font-medium">{s['program']} <span class="text-gray-400 mx-2">|</span> <span class="text-gray-600 text-base">{s['email']}</span> <span class="text-gray-400 mx-2">|</span> <span class="text-gray-800 font-bold text-base">{s['phone']}</span></p>
                </div>
                <div class="flex gap-3 mt-4 md:mt-0">
                    <button onclick="document.getElementById('edit-form-{s['id']}').classList.toggle('hidden')" class="bg-gray-50 hover:bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm font-bold border border-gray-200 transition">Edit Info</button>
                    <form method="POST" onsubmit="return confirm('WARNING: Are you sure you want to permanently delete this student and all of their grades?');" class="inline">
                        <input type="hidden" name="delete_student_id" value="{s['id']}">
                        <button type="submit" class="bg-red-50 hover:bg-red-100 text-red-600 px-4 py-2 rounded-lg text-sm font-bold border border-red-200 transition">Remove Student</button>
                    </form>
                </div>
            </div>

            <div id="edit-form-{s['id']}" class="hidden bg-gray-50 p-6 rounded-xl border border-gray-200 mb-8">
                <form method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input type="hidden" name="edit_student_id" value="{s['id']}">
                    <div><label class="block text-sm font-bold text-gray-700 mb-1">Full Name</label><input type="text" name="edit_s_name" value="{s['full_name']}" class="input-std py-2 text-base"></div>
                    <div><label class="block text-sm font-bold text-gray-700 mb-1">Email</label><input type="email" name="edit_s_email" value="{s['email']}" class="input-std py-2 text-base"></div>
                    <div><label class="block text-sm font-bold text-gray-700 mb-1">Program</label><input type="text" name="edit_s_program" value="{s['program']}" class="input-std py-2 text-base"></div>
                    <div><label class="block text-sm font-bold text-gray-700 mb-1">Payment Plan</label><input type="text" name="edit_s_plan" value="{s['payment_plan']}" class="input-std py-2 text-base"></div>
                    <div class="md:col-span-2 pt-2"><button type="submit" class="btn-green w-full py-2">Save Student Information</button></div>
                </form>
            </div>

            <form method='POST' class="flex flex-col md:flex-row gap-4 bg-emerald-50 p-5 rounded-xl mb-6 items-end border border-emerald-100">
                <input type='hidden' name='student_id' value='{s['id']}'>
                <div class="w-full md:flex-grow"><label class="block text-xs font-bold text-emerald-800 uppercase mb-2">Module / Class</label><input name='mod' required class="input-std py-2 text-base"></div>
                <div class="w-full md:w-28"><label class="block text-xs font-bold text-emerald-800 uppercase mb-2">Grade</label><input name='grd' required class="input-std py-2 text-base text-center"></div>
                <div class="w-full md:w-28"><label class="block text-xs font-bold text-emerald-800 uppercase mb-2">Hours</label><input type="number" name='hrs' required class="input-std py-2 text-base text-center"></div>
                <button type='submit' class='btn-green py-2 px-6 text-base w-full md:w-auto mb-1'>+ Add Grade</button>
            </form>
        """

        grades = conn.execute("SELECT * FROM grades_hours WHERE student_id = ? AND recorded_by = ? ORDER BY recorded_date DESC", (s['id'], instructor_name)).fetchall()

        if grades:
            html += """
            <div class="overflow-x-auto border rounded-lg border-gray-200">
                <table class='w-full text-left text-base'>
                    <tr class='border-b-2 border-gray-200 bg-gray-50 text-gray-700'>
                        <th class='py-3 px-4 font-bold'>Module</th>
                        <th class='py-3 px-4 font-bold text-center'>Grade</th>
                        <th class='py-3 px-4 font-bold text-center'>Hours</th>
                        <th class='py-3 px-4 font-bold text-right'>Action</th>
                    </tr>
            """
            for g in grades:
                html += f"""
                <tr class='border-b hover:bg-gray-50 transition'>
                    <td class='py-2 px-3'>
                        <form method='POST' class="flex flex-col sm:flex-row items-center gap-2 justify-end w-full">
                            <input type='hidden' name='edit_id' value='{g['id']}'>
                            <input name='edit_module_name' value='{g['module_name']}' class='border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:border-emerald-500 focus:outline-none'>
                    </td>
                    <td class='py-2 px-3'><input name='edit_grade' value='{g['grade']}' class='border border-gray-300 rounded px-2 py-1.5 text-sm w-16 text-center focus:border-emerald-500 focus:outline-none'></td>
                    <td class='py-2 px-3'><input type='number' name='edit_hours_attended' value='{g['hours_attended']}' class='border border-gray-300 rounded px-2 py-1.5 text-sm w-16 text-center focus:border-emerald-500 focus:outline-none'></td>
                    <td class='py-2 px-3 text-right whitespace-nowrap'>
                            <button type='submit' class='text-emerald-700 font-bold hover:underline px-3 py-1.5 bg-emerald-50 rounded border border-emerald-100 mr-1 text-sm'>Save</button>
                        </form>
                        <form method='POST' class="inline">
                            <input type='hidden' name='delete_id' value='{g['id']}'>
                            <button type='submit' class='text-red-600 font-bold hover:underline px-3 py-1.5 bg-red-50 rounded border border-red-100 text-sm'>Del</button>
                        </form>
                    </td>
                </tr>"""
            html += "</table></div>"
        else:
            html += "<p class='text-gray-500 italic text-base mt-2'>No records submitted by you yet.</p>"
        html += "</div>"

    conn.close()
    return render_page("Instructor Dashboard", html)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=False)
