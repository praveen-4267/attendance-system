"""
3_take_attendance.py
STEP 3 of the workflow.

Opens the webcam, detects faces in real time, matches them against
the trained model, and marks attendance in the SQLite database
(once per student per day).

Press 'q' to quit.
"""

import cv2
from database import init_db, mark_attendance, get_student_name

TRAINER_FILE = "trainer.yml"
CONFIDENCE_THRESHOLD = 70  # LOWER value = stricter match. Tune this based on testing (typical range 40-80).

FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def main():
    init_db()

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    try:
        recognizer.read(TRAINER_FILE)
    except cv2.error:
        print(f"Could not load '{TRAINER_FILE}'. Run 2_train_model.py first.")
        return

    cam = cv2.VideoCapture(0)
    cam.set(3, 640)
    cam.set(4, 480)

    marked_this_session = set()  # avoid spamming DB calls for the same face every frame

    print("Attendance system running. Press 'q' to stop.\n")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Camera not accessible.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

        for (x, y, w, h) in faces:
            face_roi = gray[y:y + h, x:x + w]
            student_id, confidence = recognizer.predict(face_roi)

            # LBPH: lower confidence value = better match
            if confidence < CONFIDENCE_THRESHOLD:
                name = get_student_name(student_id)
                label = f"{name} ({round(100 - confidence)}%)"
                color = (0, 255, 0)

                if student_id not in marked_this_session:
                    was_marked = mark_attendance(student_id)
                    marked_this_session.add(student_id)
                    if was_marked:
                        print(f"Attendance marked: {name} (ID: {student_id})")
                    else:
                        print(f"{name} already marked present today.")
            else:
                label = "Unknown"
                color = (0, 0, 255)

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Attendance System - Press q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
