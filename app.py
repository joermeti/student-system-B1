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
        <h2 class="text-3xl font-semibold mb-8 text-center">Login</h2>
        
        <form method="POST" class="space-y-6">
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
                <input type="text" name="identifier" required 
                       class="w-full border border-gray-300 rounded-2xl px-5 py-4 text-lg focus:outline-none focus:border-emerald-500">
            </div>

            <button type="submit" 
                    class="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-4 rounded-2xl text-lg font-medium mt-4">
                Login
            </button>
        </form>
    </div>
    """
