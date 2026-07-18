"""
1_register_student.py
STEP 1 of the workflow.

Registers a new student by:
  1. Asking for their details (ID, name, roll no, class)
  2. Capturing ~50 face images via webcam
  3. Saving them to dataset/<student_id>_<name>/

Run this once per student before training the model.
"""

import cv2
import os
from database import init_db, add_student

FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
DATASET_DIR = "dataset"
NUM_SAMPLES = 50  # number of face images to capture per student


def capture_faces(student_id, name):
    folder_path = os.path.join(DATASET_DIR, f"{student_id}_{name}")
    os.makedirs(folder_path, exist_ok=True)

    cam = cv2.VideoCapture(0)
    cam.set(3, 640)
    cam.set(4, 480)

    count = 0
    print("\nLook at the camera. Capturing face samples... Press 'q' to stop early.\n")

    while count < NUM_SAMPLES:
        ret, frame = cam.read()
        if not ret:
            print("Failed to access camera.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            count += 1
            face_img = gray[y:y + h, x:x + w]
            file_path = os.path.join(folder_path, f"{count}.jpg")
            cv2.imwrite(file_path, face_img)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Samples: {count}/{NUM_SAMPLES}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Registering Student - Press q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if count >= NUM_SAMPLES:
            break

    cam.release()
    cv2.destroyAllWindows()
    print(f"\nCaptured {count} images for {name} (ID: {student_id}).")


def main():
    init_db()

    print("=== Register New Student ===")
    student_id = input("Enter unique Student ID (number): ").strip()
    name = input("Enter Student Name: ").strip()
    roll_no = input("Enter Roll Number: ").strip()
    class_name = input("Enter Class/Section: ").strip()

    if not student_id.isdigit():
        print("Student ID must be numeric. Exiting.")
        return

    try:
        add_student(int(student_id), name, roll_no, class_name)
    except Exception as e:
        print(f"Could not add student to database (maybe duplicate ID/roll no): {e}")
        return

    capture_faces(student_id, name.replace(" ", "_"))
    print("\nRegistration complete. Now run 2_train_model.py to train the recognizer.")


if __name__ == "__main__":
    main()
