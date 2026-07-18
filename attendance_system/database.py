"""
database.py
Handles all SQLite operations for the Automated Attendance System.
Creates two tables:
  - students   : stores registered student info
  - attendance : stores daily attendance logs
"""

import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    """Create tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            class_name TEXT,
            registered_on TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
    """)

    conn.commit()
    conn.close()


def add_student(student_id, name, roll_no, class_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (student_id, name, roll_no, class_name, registered_on) VALUES (?, ?, ?, ?, ?)",
        (student_id, name, roll_no, class_name, datetime.now().strftime("%Y-%m-%d")),
    )
    conn.commit()
    conn.close()


def get_student_name(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Unknown"


def already_marked_today(student_id):
    """Prevents duplicate attendance entries for the same student on the same day."""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT 1 FROM attendance WHERE student_id = ? AND date = ?",
        (student_id, today),
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def mark_attendance(student_id):
    """Insert a new attendance record if not already marked today."""
    if already_marked_today(student_id):
        return False

    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute(
        "INSERT INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)",
        (student_id, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), "Present"),
    )
    conn.commit()
    conn.close()
    return True


def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, name, roll_no, class_name FROM students")
    rows = cursor.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print("Database initialized: attendance.db (tables: students, attendance)")
