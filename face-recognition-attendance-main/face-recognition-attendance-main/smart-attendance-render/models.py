"""Database access layer for the Smart Attendance System (PostgreSQL)."""
import json
from contextlib import contextmanager
import psycopg2
import psycopg2.errors
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from config import Config

_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=5,
    dsn=Config.DATABASE_URL,
)


@contextmanager
def get_cursor(commit=False):
    conn = _pool.getconn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        _pool.putconn(conn)


# ---------------------------------------------------------------
# Students
# ---------------------------------------------------------------
def create_student(roll_number, name, email, class_id, photo_path, face_encoding, qr_code_value=None):
    encoding_json = json.dumps(face_encoding.tolist()) if face_encoding is not None else None
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO students (roll_number, name, email, class_id, photo_path, face_encoding, qr_code_value)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               RETURNING student_id""",
            (roll_number, name, email, class_id, photo_path, encoding_json, qr_code_value),
        )
        return cur.fetchone()["student_id"]


def get_all_students_with_encodings():
    """Returns list of dicts with parsed numpy-ready encoding lists (for face matching)."""
    with get_cursor() as cur:
        cur.execute("SELECT student_id, roll_number, name, face_encoding FROM students WHERE face_encoding IS NOT NULL")
        rows = cur.fetchall()
    rows = [dict(r) for r in rows]
    for r in rows:
        r["face_encoding"] = json.loads(r["face_encoding"])
    return rows


def get_student(student_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
        return cur.fetchone()


# ---------------------------------------------------------------
# Classes / Sessions
# ---------------------------------------------------------------
def get_or_create_class(class_name):
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT class_id FROM classes WHERE class_name=%s", (class_name,))
        row = cur.fetchone()
        if row:
            return row["class_id"]
        cur.execute(
            "INSERT INTO classes (class_name) VALUES (%s) RETURNING class_id",
            (class_name,),
        )
        return cur.fetchone()["class_id"]


def get_or_create_session(class_id, session_date, period_label="default"):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT session_id FROM sessions WHERE class_id=%s AND session_date=%s AND period_label=%s",
            (class_id, session_date, period_label),
        )
        row = cur.fetchone()
        if row:
            return row["session_id"]
        cur.execute(
            """INSERT INTO sessions (class_id, session_date, period_label)
               VALUES (%s, %s, %s) RETURNING session_id""",
            (class_id, session_date, period_label),
        )
        return cur.fetchone()["session_id"]


# ---------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------
def mark_attendance(student_id, session_id, method="face", confidence=None, status="present"):
    """Idempotent: returns False if the student was already marked for this session.
    Uses ON CONFLICT DO NOTHING + rowcount check instead of catching an
    IntegrityError, since a failed INSERT inside a Postgres transaction
    aborts the whole transaction until rolled back."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO attendance (student_id, session_id, method, confidence, status)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT ON CONSTRAINT uniq_attendance DO NOTHING""",
            (student_id, session_id, method, confidence, status),
        )
        return cur.rowcount > 0


def get_attendance_between(start_date, end_date, class_id=None):
    query = """
        SELECT s.name, s.roll_number, sess.session_date, sess.period_label,
               a.status, a.marked_at, a.method
        FROM attendance a
        JOIN students s ON s.student_id = a.student_id
        JOIN sessions sess ON sess.session_id = a.session_id
        WHERE sess.session_date BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    if class_id:
        query += " AND s.class_id = %s"
        params.append(class_id)
    query += " ORDER BY sess.session_date, s.roll_number"
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_all_students(class_id=None):
    with get_cursor() as cur:
        if class_id:
            cur.execute("SELECT * FROM students WHERE class_id=%s", (class_id,))
        else:
            cur.execute("SELECT * FROM students")
        return cur.fetchall()
