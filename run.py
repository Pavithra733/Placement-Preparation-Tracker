from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# MySQL connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root@123",   # <-- put your MySQL password here
        database="placement_tracker"
    )

# HOME PAGE + FILTER + SORT + PROGRESS
@app.route('/')
def home():
    db = get_db_connection()
    cursor = db.cursor()

    # Get filter values from URL
    difficulty = request.args.get('difficulty', '')
    status = request.args.get('status', '')
    platform = request.args.get('platform', '')
    sort = request.args.get('sort', '')

    # Base query
    query = "SELECT * FROM problems WHERE 1=1"
    values = []

    # Apply filters
    if difficulty:
        query += " AND difficulty = %s"
        values.append(difficulty)

    if status:
        query += " AND status = %s"
        values.append(status)

    if platform:
        query += " AND platform LIKE %s"
        values.append(f"%{platform}%")

    # Apply sorting
    if sort == "newest":
        query += " ORDER BY id DESC"
    elif sort == "oldest":
        query += " ORDER BY id ASC"
    elif sort == "solved":
        query += " ORDER BY CASE WHEN status='Solved' THEN 1 ELSE 2 END"
    elif sort == "not_started":
        query += " ORDER BY CASE WHEN status='Not Started' THEN 1 ELSE 2 END"

    # Execute query
    cursor.execute(query, tuple(values))
    problems = cursor.fetchall()

    # Dashboard counts
    cursor.execute("SELECT COUNT(*) FROM problems")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM problems WHERE status='Solved'")
    solved_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM problems WHERE status='In Progress'")
    in_progress_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM problems WHERE status='Not Started'")
    not_started_count = cursor.fetchone()[0]

    # Solved percentage
    if total_count > 0:
        solved_percentage = int((solved_count / total_count) * 100)
    else:
        solved_percentage = 0

    cursor.close()
    db.close()

    return render_template(
        'index.html',
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

# ADD PROBLEM
@app.route('/add', methods=['POST'])
def add_problem():
    problem_name = request.form['problem_name']
    difficulty = request.form['difficulty']
    platform = request.form['platform']
    status = request.form['status']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO problems (problem_name, difficulty, platform, status) VALUES (%s, %s, %s, %s)",
        (problem_name, difficulty, platform, status)
    )
    db.commit()
    cursor.close()
    db.close()

    return redirect('/')

# DELETE PROBLEM
@app.route('/delete/<int:id>')
def delete_problem(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM problems WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()

    return redirect('/')

# EDIT PAGE
@app.route('/edit/<int:id>')
def edit_problem(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM problems WHERE id=%s", (id,))
    problem = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template('edit.html', problem=problem)

# UPDATE PROBLEM
@app.route('/update/<int:id>', methods=['POST'])
def update_problem(id):
    problem_name = request.form['problem_name']
    difficulty = request.form['difficulty']
    platform = request.form['platform']
    status = request.form['status']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE problems SET problem_name=%s, difficulty=%s, platform=%s, status=%s WHERE id=%s",
        (problem_name, difficulty, platform, status, id)
    )
    db.commit()
    cursor.close()
    db.close()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)