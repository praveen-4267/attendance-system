-- Smart Attendance System — PostgreSQL schema (Render)
-- Render creates the database for you when you provision a Postgres
-- instance, so there's no "CREATE DATABASE" step here — just run this
-- against the connection string Render gives you.

-- ---------------------------------------------------------------
-- Classes / sections (a student belongs to one; a session belongs to one)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS classes (
    class_id      SERIAL PRIMARY KEY,
    class_name    VARCHAR(100) NOT NULL,        -- e.g. "CSE-3A"
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------
-- Students
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    student_id      SERIAL PRIMARY KEY,
    roll_number     VARCHAR(30)  NOT NULL UNIQUE,
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(150),
    class_id        INT,
    photo_path      VARCHAR(255),                -- path to reference photo
    face_encoding   TEXT,                         -- JSON-serialized 128-d vector
    qr_code_value   VARCHAR(64) UNIQUE,           -- for QR-based alternative
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_student_class FOREIGN KEY (class_id)
        REFERENCES classes(class_id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------
-- Attendance sessions (one per class period, e.g. "CSE-3A, 2026-07-20, Period 1")
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    session_id    SERIAL PRIMARY KEY,
    class_id      INT NOT NULL,
    session_date  DATE NOT NULL,
    period_label  VARCHAR(50),                   -- e.g. "Period 1", "Morning"
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_class FOREIGN KEY (class_id)
        REFERENCES classes(class_id) ON DELETE CASCADE,
    CONSTRAINT uniq_session UNIQUE (class_id, session_date, period_label)
);

-- ---------------------------------------------------------------
-- Attendance records
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id   SERIAL PRIMARY KEY,
    student_id      INT NOT NULL,
    session_id      INT NOT NULL,
    marked_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(10) NOT NULL DEFAULT 'present'
                        CHECK (status IN ('present', 'absent', 'late')),
    method          VARCHAR(10) NOT NULL DEFAULT 'face'
                        CHECK (method IN ('face', 'qr', 'manual')),
    confidence      REAL,                         -- face match confidence (0-1)
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id)
        REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_attendance_session FOREIGN KEY (session_id)
        REFERENCES sessions(session_id) ON DELETE CASCADE,
    CONSTRAINT uniq_attendance UNIQUE (student_id, session_id)  -- no double-marking
);

-- Helpful indexes for report queries
CREATE INDEX IF NOT EXISTS idx_attendance_date ON sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_student_class ON students(class_id);
