from flask import Flask, render_template, request, redirect, session, send_from_directory,flash,url_for
import sqlite3, os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='frontend')
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db():
    conn = sqlite3.connect('final.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home route
@app.route('/')
def home():
    return render_template('frontpage.html')

# About route (optional, since we use sections on same page)
@app.route('/about')
def about():
    return render_template('frontpage.html')

# Services route (optional, same reason)
@app.route('/services')
def services():
    return render_template('frontpage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM Userr WHERE user_name=? AND password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session['userr_id'] = user['userr_id']
            session['username'] = user['user_name']
            session['type'] = user['type']
            return redirect('/admin' if user['type'] == 'admin' else '/studenthome')
        else:
            msg = 'Invalid credentials'
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        user_type = request.form.get('role', '').lower().strip()
        reg_date = datetime.today().date()

        # Check for empty fields
        if not username or not email or not password or not user_type:
            msg = "⚠️ All fields are required!"
        else:
            conn = sqlite3.connect("final.db")
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO Userr (user_name, email_id, password, type, reg_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, email, password, user_type, reg_date))
                conn.commit()
                msg = "✅ Registered successfully! You can now login."
            except sqlite3.IntegrityError:
                msg = "Username or Email already exists!"
            finally:
                conn.close()

    return render_template('register.html', msg=msg)

@app.route('/admin')
def admin_dashboard():
    if session.get('type') != 'admin':
        return redirect('/login')

    conn = get_db()
    # fetch courses with material and quiz counts
    courses = conn.execute("""
        SELECT c.course_id, c.title, c.description,
               (SELECT COUNT(*) FROM Material m WHERE m.course_id = c.course_id) AS material_count,
               (SELECT COUNT(*) FROM quiz q WHERE q.course_id = c.course_id) AS quiz_count
        FROM Course c
    """).fetchall()

    # get total counts
    total_courses = conn.execute("SELECT COUNT(*) FROM Course").fetchone()[0]
    total_materials = conn.execute("SELECT COUNT(*) FROM Material").fetchone()[0]
    conn.close()

    return render_template(
        'admin_dashboard.html',
        courses=courses,
        total_courses=total_courses,
        total_materials=total_materials
    )

@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    conn = get_db()
    # delete related materials & quizzes first
    conn.execute("DELETE FROM Material WHERE course_id = ?", (course_id,))
    conn.execute("DELETE FROM Quiz WHERE course_id = ?", (course_id,))
    conn.execute("DELETE FROM Course WHERE course_id = ?", (course_id,))
    conn.commit()
    conn.close()
    flash("Course deleted successfully.", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/upload/<int:course_id>', methods=['GET', 'POST'])
def upload_material(course_id):
    if session.get('type') != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['m_title']
        file = request.files['file']

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_type = filename.rsplit('.', 1)[-1].lower()
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT MAX(material_id) FROM Material")
            max_id = cur.fetchone()[0]
            new_id = 1 if max_id is None else max_id + 1

            cur.execute("INSERT INTO Material VALUES (?, ?, ?, ?, ?)",
                        (new_id, course_id, title, file_type, filename))
            conn.commit()
            conn.close()
            
            flash("Material added successfully!", "success")
            
            return redirect(url_for("manage_course", course_id=course_id))
    flash("Failed to add material!", "danger")
    return redirect(url_for("manage_course", course_id=course_id))

    return render_template('upload.html', course_id=course_id)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/addquiz/<int:course_id>', methods=['POST'])
def addquiz(course_id):
    if session.get('type') != 'admin':
        flash("Unauthorized action", "danger")
        return redirect('/login')

    conn = get_db()
    question = request.form['question']
    option1 = request.form['option1']
    option2 = request.form['option2']
    option3 = request.form['option3']
    option4 = request.form['option4']
    correct_option = request.form['correct_option']

    cur = conn.cursor()
    cur.execute("SELECT MAX(qid) FROM quiz")
    max_id = cur.fetchone()[0]
    new_id = 1 if max_id is None else max_id + 1

    cur.execute("""
        INSERT INTO quiz (qid, course_id, question, option1, option2, option3, option4, correct_option)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (new_id, course_id, question, option1, option2, option3, option4, correct_option))
    conn.commit()
    conn.close()

    flash("✅ Quiz question added successfully!", "success")
    return redirect(url_for("manage_course", course_id=course_id,tab="quiz"))

# --- QUIZ DELETE (fix: use final.db + quiz) ---
@app.route('/delete_quiz/<int:course_id>/<int:qid>', methods=['POST'])
def delete_quiz(course_id, qid):
    if session.get('type') != 'admin':
        return redirect('/login')
    conn = get_db()  # final.db
    conn.execute("DELETE FROM quiz WHERE qid=? AND course_id=?", (qid, course_id))
    conn.commit()
    conn.close()
    flash("Quiz deleted successfully!", "success")
    return redirect(url_for('manage_course', course_id=course_id))

@app.route('/course/<int:course_id>/quiz/<int:qid>/edit', methods=['GET', 'POST'])
def edit_quiz(course_id, qid):
    if session.get('type') != 'admin':
        return redirect('/login')

    conn = get_db()

    if request.method == 'POST':
        new_q = request.form.get('question', '').strip()
        option1 = request.form.get('option1', '').strip()
        option2 = request.form.get('option2', '').strip()
        option3 = request.form.get('option3', '').strip()
        option4 = request.form.get('option4', '').strip()
        correct_option = request.form.get('correct_option', '1').strip()

        # Basic guard: ensure correct_option is one of 1..4 (as string or int)
        if correct_option not in ('1', '2', '3', '4'):
            correct_option = '1'

        conn.execute("""
            UPDATE quiz
               SET question=?,
                   option1=?,
                   option2=?,
                   option3=?,
                   option4=?,
                   correct_option=?
             WHERE qid=? AND course_id=?
        """, (new_q, option1, option2, option3, option4, correct_option, qid, course_id))
        conn.commit()
        conn.close()

        flash("Quiz question updated successfully!", "success")
        return redirect(url_for('manage_course', course_id=course_id))

    # GET: load quiz row
    q = conn.execute(
        "SELECT * FROM quiz WHERE qid=? AND course_id=?",
        (qid, course_id)
    ).fetchone()
    conn.close()

    if not q:
        flash("Quiz question not found.", "danger")
        return redirect(url_for('manage_course', course_id=course_id)+ "#quizzes")

    return render_template("edit_quiz.html", q=q, course_id=course_id)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- Student Home ----------------
@app.route('/studenthome')
def student_home():
    if 'username' in session and session['type'] == 'student':
        conn = get_db()

        # student का नाम Userr table से fetch करें
        student = conn.execute(
            "SELECT user_name FROM Userr WHERE user_name = ?",
            (session['username'],)
        ).fetchone()
        student_name = student['user_name'] if student else session['username']

        # Search filter
        keyword = request.args.get('q', '')  
        if keyword:
            courseslist = conn.execute(
                "SELECT * FROM Course WHERE title LIKE ? OR description LIKE ?",
                (f"%{keyword}%", f"%{keyword}%")
            ).fetchall()
        else:
            courseslist = conn.execute("SELECT * FROM Course").fetchall()

        conn.close()

        return render_template(
            'student_home.html',
            courseslist=courseslist,
            keyword=keyword,
            student_name=student_name  # 👈 template में भेजेंगे
        )
    return redirect('/login')


# ---------------- View Course Materials -------------------
@app.route('/course/<int:course_id>')
def view_course(course_id):
    conn = get_db()
    course = conn.execute("SELECT * FROM Course WHERE course_id = ?", (course_id,)).fetchone()
    materials = conn.execute("SELECT * FROM Material WHERE course_id = ?", (course_id,)).fetchall()
    conn.close()

    # Separate videos and pdfs here
    videos = [m for m in materials if m['file_type'] in ('mp4', 'avi', 'mov')]
    pdfs = [m for m in materials if m['file_type'] == 'pdf']

    return render_template(
        'course_details.html',
        course=course,
        videos=videos,
        pdfs=pdfs,
        materials=materials
    )

@app.route('/download/<path:filename>')
def download_material(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# ---------------- Serve Materials ----------------
@app.route('/uploads/<path:filename>')
def serve_material(filename):
    return send_from_directory('uploads', filename)

@app.route('/quiz/<int:course_id>', methods=['GET', 'POST'])
def quiz(course_id):
    conn = get_db()

    if request.method == 'POST':
        questions = conn.execute(
            "SELECT * FROM quiz WHERE course_id = ?", (course_id,)
        ).fetchall()

        score = 0
        total = len(questions)
        results = []

        for q in questions:
            selected = request.form.get(str(q['qid']))
            correct = str(q['correct_option'])

            results.append({
                'question': q['question'],
                'selected': selected,
                'correct': correct,
                'options': [q['option1'], q['option2'], q['option3'], q['option4']],
                'is_correct': selected == correct
            })

            if selected == correct:
                score += 1
        userr_id = session.get('userr_id')  # get user ID from session
        no_of_attempts = 1  # or fetch and increment from DB

        conn.execute("""
            INSERT INTO Result (userr_id, course_id, quiz_id, no_of_attempts, marks)
            VALUES (?, ?, ?, ?, ?)
        """, (userr_id, course_id, None, no_of_attempts, score))
        conn.commit()
        conn.close()

        return render_template(
            'quiz_result.html', results=results, score=score, total=total, course_id=course_id )
    questions = conn.execute(
        "SELECT * FROM quiz WHERE course_id = ?", (course_id,)
    ).fetchall()
    conn.close()
    return render_template('quiz.html', questions=questions, course_id=course_id)

@app.route('/course/<int:course_id>/manage', methods=['GET', 'POST'])
def manage_course(course_id):
    if session.get('type') != 'admin':
        return redirect('/login')

    conn = get_db()
    course = conn.execute("SELECT * FROM Course WHERE course_id = ?", (course_id,)).fetchone()
    materials = conn.execute("SELECT * FROM Material WHERE course_id = ?", (course_id,)).fetchall()
    quizzes = conn.execute("SELECT * FROM quiz WHERE course_id = ?", (course_id,)).fetchall()
    conn.close()

    return render_template("manage_course.html", course=course, materials=materials, quizzes=quizzes)

@app.route("/add_course", methods=["POST"])
def add_course():
    if session.get('type') != 'admin':
        return redirect('/login')

    title = request.form["title"]
    description = request.form["description"]

    conn = get_db()
    conn.execute(
        "INSERT INTO course (title, description) VALUES (?, ?)",
        (title, description),
    )
    conn.commit()
    conn.close()

    flash("✅ Course added successfully!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route('/edit_material/<int:material_id>', methods=['GET', 'POST'])
def edit_material(material_id):
    if session.get('type') != 'admin':
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        new_title = request.form['m_title']

        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            file_type = filename.rsplit('.', 1)[-1].lower()

            # Update both title and file
            cur.execute("""UPDATE Material 
                           SET m_title=?, file_type=?, file_path=? 
                           WHERE material_id=?""",
                        (new_title, file_type, filename, material_id))
        else:
            # Update only title
            cur.execute("UPDATE Material SET m_title=? WHERE material_id=?", (new_title, material_id))

        conn.commit()
        conn.close()
        flash("Material updated successfully!", "success")
        return redirect(request.referrer)

    # GET request → fetch material
    material = conn.execute("SELECT * FROM Material WHERE material_id=?", (material_id,)).fetchone()
    conn.close()
    return render_template('edit_material.html', material=material)

# --- MATERIAL DELETE (align route with template + clean file + redirect correctly) ---
@app.route('/delete_material/<int:course_id>/<int:material_id>', methods=['POST'])
def delete_material(course_id, material_id):
    if session.get('type') != 'admin':
        return redirect('/login')

    conn = get_db()  # final.db
    row = conn.execute(
        "SELECT file_path FROM Material WHERE material_id=? AND course_id=?",
        (material_id, course_id)
    ).fetchone()

    if row:
        file_on_disk = os.path.join(app.config['UPLOAD_FOLDER'], row['file_path'])
        if os.path.exists(file_on_disk):
            try:
                os.remove(file_on_disk)
            except OSError:
                pass  # ignore if file is locked/missing

    conn.execute("DELETE FROM Material WHERE material_id=? AND course_id=?", (material_id, course_id))
    conn.commit()
    conn.close()

    flash("Material deleted successfully!", "danger")
    return redirect(url_for('manage_course', course_id=course_id))
if __name__ == '__main__':
    app.run(debug=True)