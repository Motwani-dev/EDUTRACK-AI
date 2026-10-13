import sqlite3
from pathlib import Path
import streamlit as st

# SQLite is fine for local demos. For reliable multi-user cloud persistence,
# use a managed PostgreSQL database rather than an ephemeral local file.
DB_PATH = Path(__file__).resolve().parents[1] / "edutrack.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','teacher','student')),
            student_id TEXT,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL,
            attendance_pct REAL NOT NULL DEFAULT 0,
            previous_grade REAL NOT NULL DEFAULT 0,
            internal_marks REAL NOT NULL DEFAULT 0,
            assignment_score REAL NOT NULL DEFAULT 0,
            study_time REAL NOT NULL DEFAULT 2
        );
        CREATE TABLE IF NOT EXISTS marks (
            mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            subject TEXT NOT NULL,
            assessment TEXT NOT NULL,
            score REAL NOT NULL,
            max_score REAL NOT NULL,
            UNIQUE(student_id, subject, assessment)
        );
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            subject TEXT NOT NULL,
            class_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
            UNIQUE(student_id, subject, class_date)
        );
        CREATE TABLE IF NOT EXISTS risk_assessments (
            assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            model_version TEXT NOT NULL,
            risk_probability REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)

def seed_demo_data():
    students = [
        ("STU001", "Aarav Shah", "Computer Engineering", 5, 92, 78, 76, 82, 3),
        ("STU002", "Diya Patel", "Computer Engineering", 5, 61, 52, 48, 55, 1),
        ("STU003", "Rohan Mehta", "Information Technology", 5, 74, 65, 62, 68, 2),
        ("STU004", "Anaya Desai", "Computer Engineering", 5, 88, 85, 81, 90, 4),
        ("STU005", "Kabir Joshi", "Information Technology", 5, 56, 49, 45, 51, 1),
        ("STU006", "Isha Trivedi", "Computer Engineering", 5, 81, 72, 70, 76, 3),
        ("STU007", "Vivaan Mehta", "Information Technology", 5, 69, 59, 57, 62, 2),
        ("STU008", "Mira Shah", "Computer Engineering", 5, 96, 91, 88, 94, 4),
    ]
    with get_connection() as conn:
        for row in students:
            conn.execute(
                """INSERT OR IGNORE INTO students
                (student_id,name,department,semester,attendance_pct,previous_grade,internal_marks,assignment_score,study_time)
                VALUES (?,?,?,?,?,?,?,?,?)""", row
            )
        subjects = ["Python for Data Science", "Database Management", "Computer Networks"]
        for sid, *_ in students:
            for idx, subject in enumerate(subjects):
                score = max(20, min(98, students[int(sid[-1])-1][6] + (idx-1)*4))
                conn.execute(
                    """INSERT OR IGNORE INTO marks(student_id,subject,assessment,score,max_score)
                       VALUES(?,?,?,?,100)""", (sid, subject, "Internal 1", float(score))
                )

def all_students():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM students ORDER BY student_id").fetchall()
    import pandas as pd
    return pd.DataFrame([dict(r) for r in rows])

def get_student(student_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()
    return dict(row) if row else None

def save_student(data, original_id=None):
    values = (
        data["student_id"].strip(), data["name"].strip(), data["department"],
        int(data["semester"]), float(data["attendance_pct"]), float(data["previous_grade"]),
        float(data["internal_marks"]), float(data["assignment_score"]), float(data["study_time"])
    )
    if not values[0] or not values[1]:
        raise ValueError("Student ID and name are required.")
    for key, value in [("attendance", values[4]), ("previous grade", values[5]), ("internal marks", values[6]), ("assignment score", values[7])]:
        if not 0 <= value <= 100:
            raise ValueError(f"{key.title()} must be between 0 and 100.")
    if values[3] < 1 or values[3] > 12:
        raise ValueError("Semester must be between 1 and 12.")
    with get_connection() as conn:
        if original_id and original_id != values[0]:
            conn.execute("DELETE FROM students WHERE student_id=?", (original_id,))
        conn.execute("""
            INSERT INTO students(student_id,name,department,semester,attendance_pct,previous_grade,internal_marks,assignment_score,study_time)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(student_id) DO UPDATE SET
            name=excluded.name, department=excluded.department, semester=excluded.semester,
            attendance_pct=excluded.attendance_pct, previous_grade=excluded.previous_grade,
            internal_marks=excluded.internal_marks, assignment_score=excluded.assignment_score,
            study_time=excluded.study_time
        """, values)

def delete_student(student_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        conn.execute("DELETE FROM users WHERE student_id=?", (student_id,))

def add_mark(student_id, subject, assessment, score, max_score):
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError("Score must be between 0 and the maximum score.")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO marks(student_id,subject,assessment,score,max_score) VALUES(?,?,?,?,?)
            ON CONFLICT(student_id,subject,assessment) DO UPDATE SET score=excluded.score,max_score=excluded.max_score
        """, (student_id, subject, assessment, score, max_score))

def get_marks(student_id=None):
    import pandas as pd
    query = """SELECT m.student_id,s.name,m.subject,m.assessment,m.score,m.max_score,
               ROUND(100.0*m.score/m.max_score,1) AS percentage
               FROM marks m JOIN students s ON s.student_id=m.student_id"""
    params = ()
    if student_id:
        query += " WHERE m.student_id=?"
        params = (student_id,)
    query += " ORDER BY s.name,m.subject"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def record_risk(student_id, probability, version="rules-v1"):
    with get_connection() as conn:
        conn.execute("INSERT INTO risk_assessments(student_id,model_version,risk_probability) VALUES(?,?,?)",
                     (student_id, version, float(probability)))
