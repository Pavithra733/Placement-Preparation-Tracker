from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = "placement_tracker_secret_key"

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root@123",
    database="placement_tracker"
)

cursor = db.cursor()

# -------------------- LOGIN CHECK --------------------
def is_logged_in():
    return "user_id" in session


# -------------------- REGISTER --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            return "Email already registered. Please login."

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        db.commit()
        return redirect("/login")

    return render_template("register.html")


# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect("/")
        else:
            return "Invalid email or password"

    return render_template("login.html")


# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------- HOME PAGE --------------------
@app.route("/", methods=["GET"])
def home():
    if not is_logged_in():
        return redirect("/login")

    difficulty = request.args.get("difficulty", "")
    status = request.args.get("status", "")
    platform = request.args.get("platform", "")
    sort = request.args.get("sort", "")

    user_id = session["user_id"]

    query = "SELECT * FROM problems WHERE user_id = %s"
    values = [user_id]

    if difficulty:
        query += " AND difficulty = %s"
        values.append(difficulty)

    if status:
        query += " AND status = %s"
        values.append(status)

    if platform:
        query += " AND platform LIKE %s"
        values.append(f"%{platform}%")

    if sort == "newest":
        query += " ORDER BY id DESC"
    elif sort == "oldest":
        query += " ORDER BY id ASC"
    elif sort == "solved":
        query += " ORDER BY CASE WHEN status='Solved' THEN 1 ELSE 2 END"
    elif sort == "not_started":
        query += " ORDER BY CASE WHEN status='Not Started' THEN 1 ELSE 2 END"

    # Fetch problems for the logged-in user
    cursor.execute(query, tuple(values))
    problems = cursor.fetchall()

    # Dashboard counts for the logged-in user
    cursor.execute("SELECT COUNT(*) FROM problems WHERE user_id = %s", (user_id,))
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM problems WHERE user_id = %s AND status='Solved'", (user_id,))
    solved_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM problems WHERE user_id = %s AND status='In Progress'", (user_id,))
    in_progress_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM problems WHERE user_id = %s AND status='Not Started'", (user_id,))
    not_started_count = cursor.fetchone()[0]

    solved_percentage = 0
    if total_count > 0:
        solved_percentage = int((solved_count / total_count) * 100)

    return render_template(
        "index.html",
        problems=problems,
        total_count=total_count,
        solved_count=solved_count,
        in_progress_count=in_progress_count,
        not_started_count=not_started_count,
        solved_percentage=solved_percentage,
        selected_difficulty=difficulty,
        selected_status=status,
        selected_platform=platform,
        selected_sort=sort
    )

# -------------------- ADD PROBLEM --------------------
@app.route("/add", methods=["POST"])
def add_problem():
    if not is_logged_in():
        return redirect("/login")

    problem_name = request.form["problem_name"]
    difficulty = request.form["difficulty"]
    platform = request.form["platform"]
    status = request.form["status"]
    user_id = session["user_id"]

    cursor.execute(
        "INSERT INTO problems (problem_name, difficulty, platform, status, user_id) VALUES (%s, %s, %s, %s, %s)",
        (problem_name, difficulty, platform, status, user_id)
    )
    db.commit()
    return redirect("/")


# -------------------- EDIT PAGE --------------------
@app.route("/edit/<int:id>")
def edit_problem(id):
    if not is_logged_in():
        return redirect("/login")

    user_id = session["user_id"]
    cursor.execute("SELECT * FROM problems WHERE id=%s AND user_id=%s", (id, user_id))
    problem = cursor.fetchone()

    if not problem:
        return "Problem not found or access denied"

    return render_template("edit.html", problem=problem)


# -------------------- UPDATE PROBLEM --------------------
@app.route("/update/<int:id>", methods=["POST"])
def update_problem(id):
    if not is_logged_in():
        return redirect("/login")

    user_id = session["user_id"]
    problem_name = request.form["problem_name"]
    difficulty = request.form["difficulty"]
    platform = request.form["platform"]
    status = request.form["status"]

    cursor.execute(
        "UPDATE problems SET problem_name=%s, difficulty=%s, platform=%s, status=%s WHERE id=%s AND user_id=%s",
        (problem_name, difficulty, platform, status, id, user_id)
    )
    db.commit()
    return redirect("/")


# -------------------- DELETE PROBLEM --------------------
@app.route("/delete/<int:id>")
def delete_problem(id):
    if not is_logged_in():
        return redirect("/login")

    user_id = session["user_id"]
    cursor.execute("DELETE FROM problems WHERE id=%s AND user_id=%s", (id, user_id))
    db.commit()
    return redirect("/")
@app.route("/companies")
def companies():
    if not is_logged_in():
        return redirect("/login")

    user_id = session["user_id"]

    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    query = "SELECT * FROM company_applications WHERE user_id=%s"
    values = [user_id]

    if search:
        query += " AND (company_name LIKE %s OR role LIKE %s)"
        values.append(f"%{search}%")
        values.append(f"%{search}%")

    if status_filter:
        query += " AND status=%s"
        values.append(status_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, tuple(values))
    companies = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM company_applications WHERE user_id=%s",
        (user_id,)
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM company_applications WHERE user_id=%s AND status='Applied'",
        (user_id,)
    )
    applied = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM company_applications WHERE user_id=%s AND status='OA Scheduled'",
        (user_id,)
    )
    oa = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM company_applications WHERE user_id=%s AND status='Interview'",
        (user_id,)
    )
    interview = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM company_applications WHERE user_id=%s AND status='Rejected'",
        (user_id,)
    )
    rejected = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM company_applications WHERE user_id=%s AND status='Selected'",
        (user_id,)
    )
    selected = cursor.fetchone()[0]

    return render_template(
        "company.html",
        companies=companies,
        total=total,
        applied=applied,
        oa=oa,
        interview=interview,
        rejected=rejected,
        selected=selected
    )
@app.route("/add_company", methods=["POST"])
def add_company():

    if not is_logged_in():
        return redirect("/login")

    company_name = request.form["company_name"]
    role = request.form["role"]
    application_date = request.form["application_date"]
    status = request.form["status"]
    notes = request.form["notes"]

    user_id = session["user_id"]

    cursor.execute(
        """
        INSERT INTO company_applications
        (company_name, role, application_date, status, notes, user_id)

        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            company_name,
            role,
            application_date,
            status,
            notes,
            user_id
        )
    )

    db.commit()

    return redirect("/companies")
@app.route("/delete_company/<int:id>")
def delete_company(id):
    if not is_logged_in():
        return redirect("/login")

    user_id = session["user_id"]

    cursor.execute(
        "DELETE FROM company_applications WHERE id=%s AND user_id=%s",
        (id, user_id)
    )
    db.commit()

    return redirect("/companies")
@app.route("/edit_company/<int:id>")
def edit_company(id):
    if not is_logged_in():
        return redirect("/login")

    user_id = session["user_id"]

    cursor.execute(
        "SELECT * FROM company_applications WHERE id=%s AND user_id=%s",
        (id, user_id)
    )

    company = cursor.fetchone()

    if not company:
        return "Application not found."

    return render_template("edit_company.html", company=company)
@app.route("/update_company/<int:id>", methods=["POST"])
def update_company(id):
    if not is_logged_in():
        return redirect("/login")

    user_id = session["user_id"]

    company_name = request.form["company_name"]
    role = request.form["role"]
    application_date = request.form["application_date"]
    status = request.form["status"]
    notes = request.form["notes"]

    cursor.execute(
        """
        UPDATE company_applications
        SET company_name=%s,
            role=%s,
            application_date=%s,
            status=%s,
            notes=%s
        WHERE id=%s AND user_id=%s
        """,
        (
            company_name,
            role,
            application_date,
            status,
            notes,
            id,
            user_id
        )
    )

    db.commit()

    return redirect("/companies")
if __name__ == "__main__":
    app.run(debug=True)