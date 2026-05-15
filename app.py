from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
import mysql.connector
from datetime import date

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────────────────────────────────────


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            port=Config.MYSQL_PORT
        )
        return conn
    except mysql.connector.Error as e:
        print("Database Error:", e)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all_departments():
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments ORDER BY department_name ASC")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def fetch_all_students():
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students ORDER BY name ASC")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def fetch_all_courses():
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses ORDER BY course_name ASC")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


# ─────────────────────────────────────────────────────────────────────────────
# INDEX
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return render_template('dashboard.html', totals={}, recent_students=[])

    cursor = conn.cursor(dictionary=True)
    totals = {"students": 0, "teachers": 0, "departments": 0,
              "courses": 0, "enrollments": 0, "fees": 0}
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM students")
        totals["students"] = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM teachers")
        totals["teachers"] = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM departments")
        totals["departments"] = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM courses")
        totals["courses"] = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM enrollments")
        totals["enrollments"] = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM fees")
        totals["fees"] = cursor.fetchone()["total"]
        cursor.execute("""
            SELECT s.roll_no, s.name, d.department_name
            FROM students s
            LEFT JOIN departments d ON s.department_id = d.department_id
            ORDER BY s.student_id DESC LIMIT 5
        """)
        recent_students = cursor.fetchall()
    except Exception as e:
        flash(f"Error loading dashboard: {e}", "danger")
        recent_students = []
    finally:
        cursor.close()
        conn.close()

    return render_template('dashboard.html', totals=totals, recent_students=recent_students)


# ─────────────────────────────────────────────────────────────────────────────
# STUDENTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/students')
def students():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return render_template('students.html', students=[], search=search)

    cursor = conn.cursor(dictionary=True)
    try:
        if search:
            value = f"%{search}%"
            cursor.execute("""
                SELECT s.*, d.department_name
                FROM students s
                LEFT JOIN departments d ON s.department_id = d.department_id
                WHERE s.name LIKE %s OR s.roll_no LIKE %s
                   OR s.email LIKE %s OR CAST(s.student_id AS CHAR) LIKE %s
                ORDER BY s.student_id DESC
            """, (value, value, value, value))
        else:
            cursor.execute("""
                SELECT s.*, d.department_name
                FROM students s
                LEFT JOIN departments d ON s.department_id = d.department_id
                ORDER BY s.student_id DESC
            """)
        students_list = cursor.fetchall()
    except Exception as e:
        flash(f"Error fetching students: {e}", "danger")
        students_list = []
    finally:
        cursor.close()
        conn.close()

    return render_template('students.html', students=students_list, search=search)


@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    departments = fetch_all_departments()
    if request.method == 'POST':
        roll_no       = request.form['roll_no']
        name          = request.form['name']
        email         = request.form['email']
        phone         = request.form.get('phone')
        gender        = request.form.get('gender')
        date_of_birth = request.form.get('date_of_birth') or None
        semester      = request.form['semester']
        department_id = request.form['department_id']
        address       = request.form.get('address')
        admission_date = date.today()

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed.", "danger")
            return render_template('add_student.html', departments=departments)

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO students
                (roll_no, name, email, phone, gender, date_of_birth, address, department_id, semester, admission_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (roll_no, name, email, phone, gender, date_of_birth, address, department_id, semester, admission_date))
            conn.commit()
            flash("Student added successfully.", "success")
            return redirect(url_for('students'))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding student: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('add_student.html', departments=departments)


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('students'))

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        departments = fetch_all_departments()
        if not student:
            flash("Student not found.", "warning")
            return redirect(url_for('students'))

        if request.method == 'POST':
            cursor.execute("""
                UPDATE students
                SET roll_no=%s, name=%s, email=%s, phone=%s, gender=%s,
                    date_of_birth=%s, semester=%s, department_id=%s, address=%s
                WHERE student_id=%s
            """, (request.form['roll_no'], request.form['name'], request.form['email'],
                  request.form.get('phone'), request.form.get('gender'),
                  request.form.get('date_of_birth') or None, request.form['semester'],
                  request.form['department_id'], request.form.get('address'), student_id))
            conn.commit()
            flash("Student updated successfully.", "success")
            return redirect(url_for('students'))
    except Exception as e:
        conn.rollback()
        flash(f"Error updating student: {e}", "danger")
        student = {}
        departments = fetch_all_departments()
    finally:
        cursor.close()
        conn.close()

    return render_template('edit_student.html', student=student, departments=departments)


@app.route('/students/delete/<int:student_id>')
def delete_student(student_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('students'))
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        conn.commit()
        flash("Student deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting student: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('students'))


# ─────────────────────────────────────────────────────────────────────────────
# TEACHERS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/teachers')
def teachers():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return render_template('teachers.html', teachers=[])
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.*, d.department_name
            FROM teachers t
            LEFT JOIN departments d ON t.department_id = d.department_id
            ORDER BY t.teacher_id DESC
        """)
        teachers_list = cursor.fetchall()
    except Exception as e:
        flash(f"Error fetching teachers: {e}", "danger")
        teachers_list = []
    finally:
        cursor.close()
        conn.close()
    return render_template('teachers.html', teachers=teachers_list)


@app.route('/teachers/add', methods=['GET', 'POST'])
def add_teacher():
    departments = fetch_all_departments()
    if request.method == 'POST':
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed.", "danger")
            return render_template('add_teacher.html', departments=departments)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO teachers (name, email, phone, department_id, designation, qualification)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (request.form['name'], request.form['email'], request.form.get('phone'),
                  request.form['department_id'], request.form['designation'],
                  request.form.get('qualification')))
            conn.commit()
            flash("Teacher added successfully.", "success")
            return redirect(url_for('teachers'))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding teacher: {e}", "danger")
        finally:
            cursor.close()
            conn.close()
    return render_template('add_teacher.html', departments=departments)


@app.route('/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('teachers'))
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM teachers WHERE teacher_id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        departments = fetch_all_departments()
        if not teacher:
            flash("Teacher not found.", "warning")
            return redirect(url_for('teachers'))
        if request.method == 'POST':
            cursor.execute("""
                UPDATE teachers
                SET name=%s, email=%s, phone=%s, department_id=%s, designation=%s, qualification=%s
                WHERE teacher_id=%s
            """, (request.form['name'], request.form['email'], request.form.get('phone'),
                  request.form['department_id'], request.form['designation'],
                  request.form.get('qualification'), teacher_id))
            conn.commit()
            flash("Teacher updated successfully.", "success")
            return redirect(url_for('teachers'))
    except Exception as e:
        conn.rollback()
        flash(f"Error updating teacher: {e}", "danger")
        teacher = {}
        departments = fetch_all_departments()
    finally:
        cursor.close()
        conn.close()
    return render_template('edit_teacher.html', teacher=teacher, departments=departments)


@app.route('/teachers/delete/<int:teacher_id>')
def delete_teacher(teacher_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('teachers'))
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM teachers WHERE teacher_id = %s", (teacher_id,))
        conn.commit()
        flash("Teacher deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting teacher: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('teachers'))


# ─────────────────────────────────────────────────────────────────────────────
# DEPARTMENTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/departments')
def departments():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return render_template('departments.html', departments=[])
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM departments ORDER BY department_id DESC")
        departments_list = cursor.fetchall()
    except Exception as e:
        flash(f"Error fetching departments: {e}", "danger")
        departments_list = []
    finally:
        cursor.close()
        conn.close()
    return render_template('departments.html', departments=departments_list)


@app.route('/departments/add', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed.", "danger")
            return render_template('add_department.html')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO departments (department_name, hod_name) VALUES (%s, %s)",
                           (request.form['department_name'], request.form.get('hod_name')))
            conn.commit()
            flash("Department added successfully.", "success")
            return redirect(url_for('departments'))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding department: {e}", "danger")
        finally:
            cursor.close()
            conn.close()
    return render_template('add_department.html')


@app.route('/departments/edit/<int:department_id>', methods=['GET', 'POST'])
def edit_department(department_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('departments'))
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM departments WHERE department_id = %s", (department_id,))
        department = cursor.fetchone()
        if not department:
            flash("Department not found.", "warning")
            return redirect(url_for('departments'))
        if request.method == 'POST':
            cursor.execute("""
                UPDATE departments SET department_name=%s, hod_name=%s WHERE department_id=%s
            """, (request.form['department_name'], request.form.get('hod_name'), department_id))
            conn.commit()
            flash("Department updated successfully.", "success")
            return redirect(url_for('departments'))
    except Exception as e:
        conn.rollback()
        flash(f"Error updating department: {e}", "danger")
        department = {}
    finally:
        cursor.close()
        conn.close()
    return render_template('edit_department.html', department=department)


@app.route('/departments/delete/<int:department_id>')
def delete_department(department_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('departments'))
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM departments WHERE department_id = %s", (department_id,))
        conn.commit()
        flash("Department deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting department: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('departments'))


# ─────────────────────────────────────────────────────────────────────────────
# COURSES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/courses')
def courses():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return render_template('courses.html', courses=[], search=search)
    cursor = conn.cursor(dictionary=True)
    try:
        if search:
            value = f"%{search}%"
            cursor.execute("""
                SELECT c.*, d.department_name FROM courses c
                LEFT JOIN departments d ON c.department_id = d.department_id
                WHERE c.course_name LIKE %s OR c.course_code LIKE %s
                ORDER BY c.course_id DESC
            """, (value, value))
        else:
            cursor.execute("""
                SELECT c.*, d.department_name FROM courses c
                LEFT JOIN departments d ON c.department_id = d.department_id
                ORDER BY c.course_id DESC
            """)
        courses_list = cursor.fetchall()
    except Exception as e:
        flash(f"Error fetching courses: {e}", "danger")
        courses_list = []
    finally:
        cursor.close()
        conn.close()
    return render_template('courses.html', courses=courses_list, search=search)


@app.route('/courses/add', methods=['GET', 'POST'])
def add_course():
    departments = fetch_all_departments()
    if request.method == 'POST':
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed.", "danger")
            return render_template('add_course.html', departments=departments)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO courses (course_code, course_name, credits, department_id, semester)
                VALUES (%s, %s, %s, %s, %s)
            """, (request.form['course_code'], request.form['course_name'],
                  request.form['credits'], request.form['department_id'], request.form['semester']))
            conn.commit()
            flash("Course added successfully.", "success")
            return redirect(url_for('courses'))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding course: {e}", "danger")
        finally:
            cursor.close()
            conn.close()
    return render_template('add_course.html', departments=departments)


@app.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('courses'))
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
        course = cursor.fetchone()
        departments = fetch_all_departments()
        if not course:
            flash("Course not found.", "warning")
            return redirect(url_for('courses'))
        if request.method == 'POST':
            cursor.execute("""
                UPDATE courses SET course_code=%s, course_name=%s, credits=%s, semester=%s, department_id=%s
                WHERE course_id=%s
            """, (request.form['course_code'], request.form['course_name'],
                  request.form['credits'], request.form['semester'],
                  request.form['department_id'], course_id))
            conn.commit()
            flash("Course updated successfully.", "success")
            return redirect(url_for('courses'))
    except Exception as e:
        conn.rollback()
        flash(f"Error updating course: {e}", "danger")
        course = {}
        departments = fetch_all_departments()
    finally:
        cursor.close()
        conn.close()
    return render_template('edit_course.html', course=course, departments=departments)


@app.route('/courses/delete/<int:course_id>')
def delete_course(course_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('courses'))
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
        conn.commit()
        flash("Course deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting course: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('courses'))


# ─────────────────────────────────────────────────────────────────────────────
# MARKS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/marks', methods=['GET', 'POST'])
def marks():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return render_template('marks.html', marks=[], students=[], courses=[])

    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            student_id  = request.form['student_id']
            course_id   = request.form['course_id']
            marks_value = request.form['marks']

            if course_id == 'other':
                other_name = request.form.get('other_course_name')
                other_code = request.form.get('other_course_code')
                if other_name and other_code:
                    cursor.execute("""
                        INSERT INTO courses (course_code, course_name, credits, semester)
                        VALUES (%s, %s, 4, 1)
                    """, (other_code, other_name))
                    conn.commit()
                    course_id = cursor.lastrowid
                    flash(f"New course '{other_name}' created successfully.", "info")
                else:
                    flash("Course name and code are required for 'Other' subjects.", "danger")
                    return redirect(url_for('marks'))

            # Auto-enroll if not already enrolled
            cursor.execute("""
                INSERT IGNORE INTO enrollments (student_id, course_id, session_year)
                VALUES (%s, %s, %s)
            """, (student_id, course_id, str(date.today().year)))
            conn.commit()

            cursor.execute("SELECT mark_id FROM marks WHERE student_id = %s AND course_id = %s",
                           (student_id, course_id))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("UPDATE marks SET marks = %s WHERE student_id = %s AND course_id = %s",
                               (marks_value, student_id, course_id))
                flash("Marks already existed, so they were updated successfully.", "success")
            else:
                cursor.execute("INSERT INTO marks (student_id, course_id, marks) VALUES (%s, %s, %s)",
                               (student_id, course_id, marks_value))
                flash("Marks added successfully.", "success")

            conn.commit()
            return redirect(url_for('marks'))

        cursor.execute("""
            SELECT m.*, s.name AS student_name, c.course_name
            FROM marks m
            JOIN students s ON m.student_id = s.student_id
            JOIN courses c ON m.course_id = c.course_id
            ORDER BY m.mark_id DESC
        """)
        marks_list    = cursor.fetchall()
        students_list = fetch_all_students()
        courses_list  = fetch_all_courses()

    except Exception as e:
        conn.rollback()
        flash(f"Error in marks module: {e}", "danger")
        marks_list    = []
        students_list = fetch_all_students()
        courses_list  = fetch_all_courses()
    finally:
        cursor.close()
        conn.close()

    return render_template('marks.html', marks=marks_list, students=students_list, courses=courses_list)


@app.route('/marks/delete/<int:mark_id>')
def delete_marks(mark_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('marks'))
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM marks WHERE mark_id = %s", (mark_id,))
        conn.commit()
        flash("Marks deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting marks: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('marks'))


# ─────────────────────────────────────────────────────────────────────────────
# FEES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/fees', methods=['GET', 'POST'])
def fees():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return render_template('fees.html', fees=[], students=[])

    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            student_id   = request.form['student_id']
            total_fee    = float(request.form['total_fee'])
            paid_amount  = float(request.form['paid_amount'])
            payment_date = request.form.get('payment_date') or date.today()
            status = "Paid" if paid_amount >= total_fee else ("Partial" if paid_amount > 0 else "Unpaid")

            cursor.execute("""
                INSERT INTO fees (student_id, total_fee, paid_amount, payment_date, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (student_id, total_fee, paid_amount, payment_date, status))
            conn.commit()
            flash("Fee record added successfully.", "success")
            return redirect(url_for('fees'))

        cursor.execute("""
            SELECT f.*, s.name AS student_name
            FROM fees f
            JOIN students s ON f.student_id = s.student_id
            ORDER BY f.fee_id DESC
        """)
        fees_list     = cursor.fetchall()
        students_list = fetch_all_students()
    except Exception as e:
        conn.rollback()
        flash(f"Error in fee module: {e}", "danger")
        fees_list     = []
        students_list = fetch_all_students()
    finally:
        cursor.close()
        conn.close()

    return render_template('fees.html', fees=fees_list, students=students_list)


@app.route('/fees/edit/<int:fee_id>', methods=['GET', 'POST'])
def edit_fee(fee_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('fees'))
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM fees WHERE fee_id = %s", (fee_id,))
        fee = cursor.fetchone()
        students_list = fetch_all_students()
        if not fee:
            flash("Fee record not found.", "warning")
            return redirect(url_for('fees'))
        if request.method == 'POST':
            total_fee    = float(request.form['total_fee'])
            paid_amount  = float(request.form['paid_amount'])
            payment_date = request.form.get('payment_date') or date.today()
            status = "Paid" if paid_amount >= total_fee else ("Partial" if paid_amount > 0 else "Unpaid")
            cursor.execute("""
                UPDATE fees
                SET student_id=%s, total_fee=%s, paid_amount=%s, payment_date=%s, status=%s
                WHERE fee_id=%s
            """, (request.form['student_id'], total_fee, paid_amount, payment_date, status, fee_id))
            conn.commit()
            flash("Fee record updated successfully.", "success")
            return redirect(url_for('fees'))
    except Exception as e:
        conn.rollback()
        flash(f"Error updating fee record: {e}", "danger")
        fee = {}
        students_list = fetch_all_students()
    finally:
        cursor.close()
        conn.close()
    return render_template('edit_fee.html', fee=fee, students=students_list)


@app.route('/fees/delete/<int:fee_id>')
def delete_fee(fee_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('fees'))
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM fees WHERE fee_id = %s", (fee_id,))
        conn.commit()
        flash("Fee record deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting fee record: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('fees'))


# ─────────────────────────────────────────────────────────────────────────────
# REPORT CARD
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/report-card')
def report_card():
    selected_id   = request.args.get('student_id', type=int)
    students_list = fetch_all_students()
    student = None
    courses_list = []
    fees_list    = []

    if selected_id:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM students WHERE student_id = %s", (selected_id,))
                student = cursor.fetchone()
                cursor.execute("""
                    SELECT course_name, marks, grade FROM ReportCard
                    WHERE student_id = %s ORDER BY course_name ASC
                """, (selected_id,))
                courses_list = cursor.fetchall()
                cursor.execute("""
                    SELECT total_fee, paid_amount, due_amount, status
                    FROM fees WHERE student_id = %s ORDER BY fee_id DESC
                """, (selected_id,))
                fees_list = cursor.fetchall()
            except Exception as e:
                flash(f"Error generating report card: {e}", "danger")
            finally:
                cursor.close()
                conn.close()
        else:
            flash("Database connection failed.", "danger")

    return render_template('report_card.html', students=students_list,
                           student=student, courses=courses_list,
                           fees=fees_list, selected_id=selected_id)


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("CollegeHub running on http://127.0.0.1:5000")
    app.run(debug=True)