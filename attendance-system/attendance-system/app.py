import os
import cv2
import numpy as np
import sqlite3
import base64
import io
import csv
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
TRAINER_DIR = os.path.join(BASE_DIR, "trainer")
TRAINER_FILE = os.path.join(TRAINER_DIR, "trainer.yml")
DB_FILE = os.path.join(BASE_DIR, "attendance.db")
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(TRAINER_DIR, exist_ok=True)

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            roll TEXT NOT NULL,
            att_date TEXT NOT NULL,
            att_time TEXT NOT NULL,
            UNIQUE(student_id, att_date),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)
    conn.commit()
    conn.close()


init_db()


def decode_image(data_url):
    header, encoded = data_url.split(",", 1)
    binary = base64.b64decode(encoded)
    arr = np.frombuffer(binary, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


@app.route("/")
def index():
    conn = get_db()
    student_count = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    today = date.today().isoformat()
    today_count = conn.execute(
        "SELECT COUNT(*) c FROM attendance WHERE att_date = ?", (today,)
    ).fetchone()["c"]
    conn.close()
    trained = os.path.exists(TRAINER_FILE)
    return render_template("index.html", student_count=student_count,
                            today_count=today_count, trained=trained)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll = request.form.get("roll", "").strip()
        if not name or not roll:
            flash("Name and Roll number are required", "danger")
            return redirect(url_for("register"))

        conn = get_db()
        existing = conn.execute("SELECT * FROM students WHERE roll = ?", (roll,)).fetchone()
        if existing:
            student_id = existing["id"]
        else:
            cur = conn.execute(
                "INSERT INTO students (roll, name, created_at) VALUES (?, ?, ?)",
                (roll, name, datetime.now().isoformat())
            )
            conn.commit()
            student_id = cur.lastrowid
        conn.close()

        return render_template("capture.html", student_id=student_id, name=name, roll=roll)

    return render_template("register.html")


@app.route("/capture_frame", methods=["POST"])
def capture_frame():
    data = request.get_json()
    student_id = data.get("student_id")
    image_data = data.get("image")
    index = data.get("index", 0)

    img = decode_image(image_data)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))

    if len(faces) == 0:
        return jsonify({"success": False, "message": "No face detected"})

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face_img = gray[y:y + h, x:x + w]
    face_img = cv2.resize(face_img, (200, 200))

    student_dir = os.path.join(DATASET_DIR, str(student_id))
    os.makedirs(student_dir, exist_ok=True)
    file_path = os.path.join(student_dir, f"{index}.jpg")
    cv2.imwrite(file_path, face_img)

    saved_count = len(os.listdir(student_dir))
    return jsonify({"success": True, "count": saved_count})


@app.route("/train", methods=["GET", "POST"])
def train():
    faces = []
    labels = []

    for student_id in os.listdir(DATASET_DIR):
        student_dir = os.path.join(DATASET_DIR, student_id)
        if not os.path.isdir(student_dir):
            continue
        for img_name in os.listdir(student_dir):
            img_path = os.path.join(student_dir, img_name)
            gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if gray is None:
                continue
            faces.append(gray)
            labels.append(int(student_id))

    if len(faces) == 0:
        flash("No training data found. Please register students first.", "danger")
        return redirect(url_for("index"))

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    recognizer.save(TRAINER_FILE)

    flash(f"Model trained successfully on {len(set(labels))} student(s), {len(faces)} images.", "success")
    return redirect(url_for("index"))


@app.route("/attendance")
def attendance_page():
    if not os.path.exists(TRAINER_FILE):
        flash("Please train the model before marking attendance.", "danger")
        return redirect(url_for("index"))
    return render_template("attendance.html")


@app.route("/mark", methods=["POST"])
def mark():
    if not os.path.exists(TRAINER_FILE):
        return jsonify({"success": False, "message": "Model not trained"})

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_FILE)

    data = request.get_json()
    img = decode_image(data.get("image"))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))

    if len(faces) == 0:
        return jsonify({"success": False, "message": "No face detected"})

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face_img = cv2.resize(gray[y:y + h, x:x + w], (200, 200))

    label, confidence = recognizer.predict(face_img)

    # Lower confidence value = better match in LBPH
    if confidence > 70:
        return jsonify({"success": False, "message": "Face not recognized"})

    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (label,)).fetchone()
    if not student:
        conn.close()
        return jsonify({"success": False, "message": "Unknown student"})

    today = date.today().isoformat()
    now_time = datetime.now().strftime("%H:%M:%S")

    existing = conn.execute(
        "SELECT * FROM attendance WHERE student_id = ? AND att_date = ?",
        (student["id"], today)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({
            "success": True,
            "already_marked": True,
            "name": student["name"],
            "roll": student["roll"]
        })

    conn.execute(
        "INSERT INTO attendance (student_id, name, roll, att_date, att_time) VALUES (?, ?, ?, ?, ?)",
        (student["id"], student["name"], student["roll"], today, now_time)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "already_marked": False,
        "name": student["name"],
        "roll": student["roll"],
        "confidence": round(float(confidence), 2)
    })


@app.route("/records")
def records():
    selected_date = request.args.get("date", date.today().isoformat())
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM attendance WHERE att_date = ? ORDER BY att_time",
        (selected_date,)
    ).fetchall()
    conn.close()
    return render_template("records.html", rows=rows, selected_date=selected_date)


@app.route("/export")
def export_csv():
    selected_date = request.args.get("date", date.today().isoformat())
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM attendance WHERE att_date = ? ORDER BY att_time",
        (selected_date,)
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll", "Name", "Date", "Time"])
    for r in rows:
        writer.writerow([r["roll"], r["name"], r["att_date"], r["att_time"]])

    output.seek(0)
    return app.response_class(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_{selected_date}.csv"}
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
