import os
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for

from config import Config
import models
import face_engine
import report_generator

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)


@app.route("/")
def index():
    students = models.get_all_students()
    return render_template("index.html", student_count=len(students))


# ---------------------------------------------------------------
# Registration
# ---------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    class_name = request.form.get("class_name", "").strip() or "Unassigned"
    image_data_url = request.form.get("image_data")  # captured from webcam via JS

    if not (roll_number and name and image_data_url):
        return jsonify({"success": False, "message": "Roll number, name, and a photo are required."}), 400

    frame = face_engine.decode_base64_image(image_data_url)
    encoding, location = face_engine.extract_face_encoding(frame)
    if encoding is None:
        return jsonify({"success": False, "message": "No face detected in the photo. Please retake it."}), 422

    photo_filename = f"{roll_number}.jpg"
    photo_path = os.path.join(Config.UPLOAD_FOLDER, photo_filename)
    import cv2
    cv2.imwrite(photo_path, frame)

    class_id = models.get_or_create_class(class_name)
    student_id = models.create_student(
        roll_number=roll_number,
        name=name,
        email=email,
        class_id=class_id,
        photo_path=photo_path,
        face_encoding=encoding,
    )
    return jsonify({"success": True, "message": f"Registered {name} (ID {student_id}).", "student_id": student_id})


# ---------------------------------------------------------------
# Mark attendance (face recognition)
# ---------------------------------------------------------------
@app.route("/mark", methods=["GET"])
def mark_page():
    return render_template("mark_attendance.html")


@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    payload = request.get_json(force=True)
    image_data_url = payload.get("image_data")
    class_name = payload.get("class_name", "Unassigned")
    period_label = payload.get("period_label", "default")

    if not image_data_url:
        return jsonify({"success": False, "message": "No image received."}), 400

    frame = face_engine.decode_base64_image(image_data_url)
    encoding, location = face_engine.extract_face_encoding(frame)
    if encoding is None:
        return jsonify({"success": False, "message": "No face detected. Please face the camera clearly."}), 200

    known_students = models.get_all_students_with_encodings()
    match, confidence = face_engine.find_best_match(encoding, known_students)

    if match is None:
        return jsonify({"success": False, "message": "Face not recognized. Please register first."}), 200

    class_id = models.get_or_create_class(class_name)
    session_id = models.get_or_create_session(class_id, date.today(), period_label)
    newly_marked = models.mark_attendance(
        student_id=match["student_id"], session_id=session_id,
        method="face", confidence=confidence,
    )

    message = (
        f"Welcome {match['name']}! Attendance marked ({confidence:.0%} confidence)."
        if newly_marked else
        f"{match['name']} was already marked present for this session."
    )
    return jsonify({
        "success": True,
        "already_marked": not newly_marked,
        "student_name": match["name"],
        "roll_number": match["roll_number"],
        "confidence": confidence,
        "message": message,
    })


# ---------------------------------------------------------------
# Reports
# ---------------------------------------------------------------
@app.route("/reports", methods=["GET", "POST"])
def reports():
    if request.method == "GET":
        return render_template("reports.html")

    start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
    class_name = request.form.get("class_name", "").strip()
    class_id = models.get_or_create_class(class_name) if class_name else None

    try:
        filepath = report_generator.generate_report(start_date, end_date, class_id)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("reports"))

    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
