# Student Attendance & Marks Management System

A Flask web application for managing student attendance, marks, and performance with AI-assisted features.

## Problem Understanding

Educational institutions need an efficient way to:
- Maintain student records (Roll No, Name, Semester)
- Track daily attendance (Present/Absent) and calculate attendance percentage
- Record and analyze marks for subjects
- Generate reports for teachers and administrators
- Identify students with low attendance or weak performance early

Manual record-keeping is time-consuming, error-prone, and makes it difficult to spot patterns or generate insights quickly.

## AI Solution Approach

This system uses AI-assisted logic for faster development, validation, and basic analytics:

1. **Validation logic** — AI-inspired roll number validation (alphanumeric format, length checks)
2. **Attendance shortage warning** — Rule-based remarks flagging students below 75% (e.g., "Warning: May affect eligibility")
3. **Sample data generation** — Auto-generate realistic student data using Faker for testing
4. **Performance remarks** — Automatic feedback based on marks (e.g., "Good", "Average", "Needs Improvement")

These features reduce manual checks, speed up data entry, and provide instant actionable insights.

## Tools/Technologies Used

- **Python 3.8+** — Backend logic
- **Flask** — Web framework
- **SQLite** — Database for persistent storage
- **Faker** — Generate sample student data
- **Bootstrap 5** — Frontend UI and responsive design
- **Jinja2** — Server-side templating (via Flask)

## Expected Outcome

- A working web application where teachers can manage students, mark attendance, and enter marks
- Automated attendance percentage and performance remarks for each student
- Overall and monthly reports for quick review and decision-making
- Faster workflow with validation, warnings, and sample data generation

---

## Features

### 1. Student Management
- Add student details (Roll No, Name, Semester)
- Display student list
- Delete students

### 2. Attendance Management
- Mark attendance (Present/Absent) for today or past dates
- Calculate attendance percentage for each student
- **Load** — Pick a date and load the form (when attendance not yet taken)
- **Update** — Edit saved attendance (when attendance already taken)
- No attendance on Sunday — Validation blocks marking attendance for Sundays

### 3. Performance Management
- Enter marks for one subject (0–100)
- Calculate average marks for the class

### 4. Reports
- **Overall Report** — Student-wise summary: Roll No, Name, Semester, Attendance %, Status, Marks, Performance
- **Monthly Report** — Date-wise attendance for any month (P/A for each student per date)

### 5. AI-Assisted Features
- **Roll number validation** — Validates format (3–15 alphanumeric chars, hyphens allowed)
- **Attendance shortage warning** — Flags students below 75% with remarks (e.g., "Warning: Below 75%")
- **Auto-generate sample data** — Uses Faker to generate sample students
- **Performance remarks** — Provides feedback (e.g., "Good", "Average", "Needs Improvement")

## Setup

### Prerequisites
- Python 3.8+

### Installation

1. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # source venv/bin/activate   # Linux/Mac
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open http://127.0.0.1:5000 in your browser.

## Usage

1. **Add students** — Go to Students, fill the form, or use "Generate Students" for sample data.
2. **Mark attendance** — Go to Attendance, pick a date, click **Load**, set Present/Absent for each student, then Save.
3. **Edit attendance** — For dates with saved attendance, click **Update**, change as needed, then Save.
4. **Enter marks** — Go to Marks, enter marks (0–100) for each student, then Save.
5. **View reports** — Use **Reports** in the nav:
   - **Overall Report** — Student-wise summary
   - **Monthly Report** — Select a month for date-wise attendance

Data is stored in SQLite (`attendance.db`).

## Project Structure

```
Attendance/
├── app.py                  # Flask application
├── requirements.txt        # Dependencies
├── attendance.db           # SQLite database (created on first run)
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── students.html
│   ├── attendance.html
│   ├── marks.html
│   ├── overall_report.html
│   └── attendance_report.html
└── README.md
```
