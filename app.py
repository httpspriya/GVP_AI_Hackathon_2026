"""
Student Attendance & Marks Management System
A Flask web application with AI-assisted features.
"""

import sqlite3
import re
import calendar
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from faker import Faker

app = Flask(__name__)
app.secret_key = 'attendance-system-secret-key-2025'
fake = Faker()

DATABASE = 'attendance.db'


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            semester INTEGER NOT NULL,
            marks REAL DEFAULT 0,
            total_attendance INTEGER DEFAULT 0,
            total_classes INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
    """)
    conn.commit()
    conn.close()


# ============== AI-ASSISTED VALIDATION ==============
def validate_roll_number(roll_no):
    """
    AI-inspired validation: Roll number should be alphanumeric,
    3-15 chars, optionally with dashes (e.g., CS101, 2024-CS-001).
    """
    pattern = r'^[A-Za-z0-9\-]{3,15}$'
    if not roll_no or not roll_no.strip():
        return False, "Roll number cannot be empty."
    if not re.match(pattern, roll_no.strip()):
        return False, "Roll number must be 3-15 alphanumeric characters (hyphens allowed)."
    return True, "Valid roll number."


def get_attendance_remark(percentage):
    """
    AI-inspired: Suggest attendance shortage warning (below 75%).
    """
    if percentage >= 90:
        return "Excellent", "success"
    elif percentage >= 75:
        return "Good - Meets requirement", "info"
    elif percentage >= 60:
        return "Warning: Below 75% - May affect eligibility", "warning"
    else:
        return "Critical: Below 60% - Immediate attention needed", "danger"


def get_performance_remark(marks):
    """
    AI-inspired: Provide simple performance remarks.
    """
    if marks >= 90:
        return "Excellent"
    elif marks >= 80:
        return "Very Good"
    elif marks >= 70:
        return "Good"
    elif marks >= 60:
        return "Average"
    elif marks >= 40:
        return "Needs Improvement"
    else:
        return "Poor - Requires Support"


def generate_sample_students(count=5):
    """
    AI-assisted: Auto-generate sample student data.
    """
    students = []
    used_rolls = set()
    for i in range(count):
        roll_no = f"CS{fake.random_int(1000, 9999)}"
        while roll_no in used_rolls:
            roll_no = f"CS{fake.random_int(1000, 9999)}"
        used_rolls.add(roll_no)
        students.append({
            'roll_no': roll_no,
            'name': fake.name(),
            'semester': fake.random_int(1, 8)
        })
    return students


# ============== ROUTES ==============

@app.route('/')
def index():
    """Home page with dashboard overview."""
    conn = get_db()
    students = conn.execute('SELECT * FROM students ORDER BY roll_no').fetchall()
    conn.close()

    # Calculate summary stats
    total_students = len(students)
    low_attendance = 0
    for s in students:
        pct = (s['total_attendance'] / s['total_classes'] * 100) if s['total_classes'] > 0 else 0
        if pct < 75 and s['total_classes'] > 0:
            low_attendance += 1

    return render_template('index.html', students=students,
                           total_students=total_students,
                           low_attendance=low_attendance)


@app.route('/students', methods=['GET', 'POST'])
def students():
    """Add and display students."""
    if request.method == 'POST':
        roll_no = request.form.get('roll_no', '').strip()
        name = request.form.get('name', '').strip()
        semester = request.form.get('semester', '')

        # AI-assisted validation
        valid, msg = validate_roll_number(roll_no)
        if not valid:
            flash(msg, 'error')
            return redirect(url_for('students'))

        try:
            semester = int(semester)
            if semester < 1 or semester > 8:
                flash("Semester must be between 1 and 8.", 'error')
                return redirect(url_for('students'))
        except ValueError:
            flash("Invalid semester.", 'error')
            return redirect(url_for('students'))

        if not name:
            flash("Name cannot be empty.", 'error')
            return redirect(url_for('students'))

        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO students (roll_no, name, semester) VALUES (?, ?, ?)',
                (roll_no.upper(), name, semester)
            )
            conn.commit()
            flash(f"Student {roll_no} added successfully!", 'success')
        except sqlite3.IntegrityError:
            flash(f"Roll number {roll_no} already exists.", 'error')
        conn.close()
        return redirect(url_for('students'))

    conn = get_db()
    students_list = conn.execute('SELECT * FROM students ORDER BY roll_no').fetchall()
    conn.close()
    return render_template('students.html', students=students_list)


@app.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Delete a student."""
    conn = get_db()
    conn.execute('DELETE FROM attendance_records WHERE student_id = ?', (student_id,))
    conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    flash("Student deleted.", 'success')
    return redirect(url_for('students'))


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    """Mark and view attendance."""
    conn = get_db()
    students_list = conn.execute('SELECT * FROM students ORDER BY roll_no').fetchall()
    conn.close()

    if request.method == 'POST':
        today_str = datetime.now().strftime('%Y-%m-%d')
        date_str = request.form.get('date', today_str)

        # Validation: No future dates (allow today and past only)
        if date_str > today_str:
            flash("Cannot mark attendance for future dates.", 'error')
            return redirect(url_for('attendance'))

        # Validation: No attendance on Sunday
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            if dt.weekday() == 6:  # Sunday = 6
                flash("Attendance cannot be marked for Sunday.", 'error')
                return redirect(url_for('attendance'))
        except ValueError:
            pass

        conn = get_db()
        # If attendance already exists, revert totals before updating (edit mode)
        existing_records = conn.execute(
            'SELECT student_id, status FROM attendance_records WHERE date = ?', (date_str,)
        ).fetchall()
        if existing_records:
            for r in existing_records:
                conn.execute(
                    'UPDATE students SET total_classes = total_classes - 1 WHERE id = ?',
                    (r['student_id'],)
                )
                if r['status'] == 'present':
                    conn.execute(
                        'UPDATE students SET total_attendance = total_attendance - 1 WHERE id = ?',
                        (r['student_id'],)
                    )
            conn.execute('DELETE FROM attendance_records WHERE date = ?', (date_str,))

        for student in students_list:
            status = request.form.get(f'status_{student["id"]}', 'absent')
            conn.execute(
                'INSERT INTO attendance_records (date, student_id, status) VALUES (?, ?, ?)',
                (date_str, student['id'], status)
            )
            if status == 'present':
                conn.execute(
                    'UPDATE students SET total_attendance = total_attendance + 1 WHERE id = ?',
                    (student['id'],)
                )
            conn.execute(
                'UPDATE students SET total_classes = total_classes + 1 WHERE id = ?',
                (student['id'],)
            )
        conn.commit()
        conn.close()
        flash(f"Attendance saved for {date_str}.", 'success')
        return redirect(url_for('attendance'))

    # Build student list with attendance % and AI remarks
    students_with_pct = []
    for s in students_list:
        pct = (s['total_attendance'] / s['total_classes'] * 100) if s['total_classes'] > 0 else 0
        remark, remark_class = get_attendance_remark(pct)
        students_with_pct.append({
            **dict(s),
            'attendance_pct': round(pct, 1),
            'attendance_remark': remark,
            'remark_class': remark_class
        })

    today = datetime.now().strftime('%Y-%m-%d')
    selected_date = request.args.get('date', today)
    if selected_date > today:
        selected_date = today
    conn = get_db()
    attendance_taken_for_date = conn.execute(
        'SELECT COUNT(*) FROM attendance_records WHERE date = ?', (selected_date,)
    ).fetchone()[0] > 0
    # Fetch existing attendance for edit mode (pre-fill form)
    existing_attendance = {}
    if attendance_taken_for_date:
        records = conn.execute(
            'SELECT student_id, status FROM attendance_records WHERE date = ?',
            (selected_date,)
        ).fetchall()
        existing_attendance = {r['student_id']: r['status'] for r in records}
    edit_mode = bool(request.args.get('edit')) and attendance_taken_for_date
    # Check if selected date is Sunday
    try:
        is_sunday = datetime.strptime(selected_date, '%Y-%m-%d').weekday() == 6
    except ValueError:
        is_sunday = False
    conn.close()
    return render_template('attendance.html', students=students_with_pct, today=today,
                           selected_date=selected_date,
                           attendance_taken_for_date=attendance_taken_for_date,
                           edit_mode=edit_mode,
                           existing_attendance=existing_attendance,
                           is_sunday=is_sunday)


@app.route('/marks', methods=['GET', 'POST'])
def marks():
    """Enter and view marks."""
    conn = get_db()
    students_list = conn.execute('SELECT * FROM students ORDER BY roll_no').fetchall()
    conn.close()

    if request.method == 'POST':
        conn = get_db()
        for student in students_list:
            mark_str = request.form.get(f'marks_{student["id"]}', '0')
            try:
                marks_val = float(mark_str)
                marks_val = max(0, min(100, marks_val))
            except ValueError:
                marks_val = 0
            conn.execute('UPDATE students SET marks = ? WHERE id = ?', (marks_val, student['id']))
        conn.commit()
        conn.close()
        flash("Marks updated.", 'success')
        return redirect(url_for('marks'))

    # Add performance remarks
    total_marks = sum(s['marks'] for s in students_list)
    avg_marks = round(total_marks / len(students_list), 1) if students_list else 0
    students_with_remarks = []
    for s in students_list:
        remark = get_performance_remark(s['marks'])
        students_with_remarks.append({**dict(s), 'remark': remark})

    return render_template('marks.html', students=students_with_remarks, avg_marks=avg_marks)


@app.route('/reports/overall')
def overall_report():
    """Overall report - student-wise summary."""
    conn = get_db()
    students_list = conn.execute('SELECT * FROM students ORDER BY roll_no').fetchall()
    conn.close()

    report_rows = []
    for s in students_list:
        att_pct = (s['total_attendance'] / s['total_classes'] * 100) if s['total_classes'] > 0 else 0
        att_remark, att_class = get_attendance_remark(att_pct)
        perf_remark = get_performance_remark(s['marks'])
        report_rows.append({
            'roll_no': s['roll_no'],
            'name': s['name'],
            'semester': s['semester'],
            'total_attendance': s['total_attendance'],
            'total_classes': s['total_classes'],
            'attendance_pct': round(att_pct, 1),
            'attendance_remark': att_remark,
            'remark_class': att_class,
            'marks': s['marks'],
            'performance_remark': perf_remark,
        })

    return render_template('overall_report.html', students=report_rows)


@app.route('/attendance/report')
def attendance_report():
    """One month attendance report - date-wise for every student."""
    # Get month from query param (default: current month)
    month_param = request.args.get('month', '')
    today = date.today()
    try:
        if month_param:
            year, month = map(int, month_param.split('-'))
        else:
            year, month = today.year, today.month
        if month < 1 or month > 12:
            year, month = today.year, today.month
    except (ValueError, AttributeError):
        year, month = today.year, today.month

    _, num_days = calendar.monthrange(year, month)
    dates_in_month = [date(year, month, d).strftime('%Y-%m-%d') for d in range(1, num_days + 1)]

    conn = get_db()
    students_list = conn.execute('SELECT * FROM students ORDER BY roll_no').fetchall()
    # Build {date: {student_id: status}}
    records = conn.execute(
        'SELECT date, student_id, status FROM attendance_records WHERE date >= ? AND date <= ?',
        (dates_in_month[0], dates_in_month[-1])
    ).fetchall()
    conn.close()

    # attendance_map[date][student_id] = 'present' | 'absent'
    attendance_map = {d: {} for d in dates_in_month}
    for r in records:
        attendance_map[r['date']][r['student_id']] = r['status']

    # Monthly percentage per student: {student_id: (present, total)}
    monthly_pct = {}
    for s in students_list:
        sid = s['id']
        present = sum(1 for d in dates_in_month if attendance_map[d].get(sid) == 'present')
        total = sum(1 for d in dates_in_month if attendance_map[d].get(sid) in ('present', 'absent'))
        monthly_pct[sid] = (present, total)

    return render_template('attendance_report.html',
                           students=students_list,
                           dates=dates_in_month,
                           attendance_map=attendance_map,
                           monthly_pct=monthly_pct,
                           year=year, month=month,
                           month_name=datetime(year, month, 1).strftime('%B %Y'))


@app.route('/ai/generate-sample', methods=['POST'])
def ai_generate_sample():
    """AI-assisted: Generate sample student data."""
    count = request.form.get('count', 5)
    try:
        count = min(10, max(1, int(count)))
    except ValueError:
        count = 5

    sample = generate_sample_students(count)
    conn = get_db()
    added = 0
    for s in sample:
        try:
            conn.execute(
                'INSERT INTO students (roll_no, name, semester) VALUES (?, ?, ?)',
                (s['roll_no'], s['name'], s['semester'])
            )
            added += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    flash(f"Generated and added {added} sample student(s).", 'success')
    return redirect(url_for('students'))


@app.route('/api/validate-roll', methods=['POST'])
def api_validate_roll():
    """API endpoint for roll number validation."""
    data = request.get_json() or {}
    roll_no = data.get('roll_no', '')
    valid, msg = validate_roll_number(roll_no)
    return jsonify({'valid': valid, 'message': msg})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
