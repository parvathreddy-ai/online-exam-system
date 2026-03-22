from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'online_exam'

mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        vtu = request.form['vtu']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM users WHERE vtu_no=%s AND password=%s",
            (vtu, password)
        )
        user = cur.fetchone()
        cur.close()

        if user:
            session['user'] = user[1]
            session['role'] = user[4]

            if user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))

        else:
            return "Invalid Credentials"

    return render_template('login.html')


@app.route('/admin')
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    cur = mysql.connection.cursor()

    # Fetch exams
    cur.execute("SELECT * FROM exams")
    exams = cur.fetchall()

    # Fetch results with student names
    cur.execute("""
        SELECT users.name, exams.subject, results.score, 
               results.total_marks, results.percentage
        FROM results
        JOIN users ON results.user_id = users.user_id
        JOIN exams ON results.exam_id = exams.exam_id
    """)
    results = cur.fetchall()

    cur.close()

    return render_template("admin.html", exams=exams, results=results)


@app.route('/student')
def student_dashboard():
    if 'user' not in session or session.get('role') != 'student':
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM exams")
    exams = cur.fetchall()
    cur.close()

    return render_template('student.html', exams=exams)


@app.route('/create_exam', methods=['POST'])
def create_exam():
    subject = request.form['subject']
    duration = request.form['duration']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO exams (subject, duration) VALUES (%s, %s)", (subject, duration))
    mysql.connection.commit()
    cur.close()

    return "Exam Created Successfully 🔥"

@app.route('/create_exam_page')
def create_exam_page():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')
    return render_template('create_exam.html')

@app.route('/add_question', methods=['POST'])
def add_question():
    exam_id = request.form['exam_id']
    question_text = request.form['question_text']
    option1 = request.form['option1']
    option2 = request.form['option2']
    option3 = request.form['option3']
    option4 = request.form['option4']
    correct_answer = request.form['correct_answer']

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO questions 
        (exam_id, question_text, option1, option2, option3, option4, correct_answer)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (exam_id, question_text, option1, option2, option3, option4, correct_answer))
    
    mysql.connection.commit()
    cur.close()

    return "Question Added Successfully 🔥"

@app.route('/add_question_page')
def add_question_page():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM exams")
    exams = cur.fetchall()
    cur.close()

    return render_template('add_questions.html', exams=exams)

@app.route('/exam/<int:exam_id>')
def take_exam(exam_id):
    if 'user' not in session or session.get('role') != 'student':
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM questions WHERE exam_id=%s", (exam_id,))
    questions = cur.fetchall()

    cur.execute("SELECT duration FROM exams WHERE exam_id=%s", (exam_id,))
    exam = cur.fetchone()

    cur.close()

    return render_template('exam.html', questions=questions, duration=exam[0], exam_id=exam_id)



@app.route('/submit_exam/<int:exam_id>', methods=['POST'])
def submit_exam(exam_id):

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM questions WHERE exam_id=%s", (exam_id,))
    questions = cur.fetchall()

    score = 0
    total = len(questions)

    for q in questions:
        question_id = q[0]
        correct_answer = q[7]

        selected = request.form.get(f"q{question_id}")

        if selected == correct_answer:
            score += 1

    percentage = (score / total) * 100 if total > 0 else 0

    # Get current logged-in user
    cur.execute("SELECT user_id FROM users WHERE name=%s", (session['user'],))
    user = cur.fetchone()

    user_id = user[0]

    # Insert into results table
    cur.execute("""
        INSERT INTO results (user_id, exam_id, score, total_marks, percentage)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, exam_id, score, total, percentage))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('result_page', score=score, total=total, percentage=percentage))



@app.route('/result')
def result_page():
    score = request.args.get('score')
    total = request.args.get('total')
    percentage = request.args.get('percentage')

    return render_template('result.html', score=score, total=total, percentage=percentage)

@app.route('/view_results')
def view_results():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT users.name, users.vtu_no, exams.subject,
               results.score, results.total_marks, results.percentage
        FROM results
        JOIN users ON results.user_id = users.user_id
        JOIN exams ON results.exam_id = exams.exam_id
    """)
    results = cur.fetchall()
    cur.close()

    return render_template('view_results.html', results=results)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/add_multiple_questions', methods=['POST'])
def add_multiple_questions():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    exam_id = request.form['exam_id']
    questions = request.form.getlist('question_text[]')
    option1 = request.form.getlist('option1[]')
    option2 = request.form.getlist('option2[]')
    option3 = request.form.getlist('option3[]')
    option4 = request.form.getlist('option4[]')
    correct = request.form.getlist('correct_answer[]')

    cur = mysql.connection.cursor()

    for i in range(len(questions)):
        cur.execute("""
            INSERT INTO questions
            (exam_id, question_text, option1, option2, option3, option4, correct_answer)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            exam_id,
            questions[i],
            option1[i],
            option2[i],
            option3[i],
            option4[i],
            correct[i]
        ))

    mysql.connection.commit()
    cur.close()

    return redirect('/admin')



@app.route('/instructions/<int:exam_id>')
def instructions(exam_id):
    if 'user' not in session or session.get('role') != 'student':
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute("SELECT duration FROM exams WHERE exam_id=%s", (exam_id,))
    exam = cur.fetchone()
    cur.close()

    return render_template("instructions.html",
                           exam_id=exam_id,
                           duration=exam[0])





if __name__ == '__main__':
    app.run(debug=True)