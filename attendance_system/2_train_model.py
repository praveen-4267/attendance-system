"""
2_train_model.py
STEP 2 of the workflow.

Reads all images inside dataset/<student_id>_<name>/ folders,
trains an OpenCV LBPH face recognizer, and saves:
  - trainer.yml        (the trained model)

Run this after registering all students, and again any time
you register a NEW student.
"""

import cv2
import os
import numpy as np

DATASET_DIR = "dataset"
TRAINER_FILE = "trainer.yml"


def prepare_training_data():
    faces = []
    labels = []

    for folder_name in os.listdir(DATASET_DIR):
        folder_path = os.path.join(DATASET_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue

        # folder name format: <student_id>_<name>
        student_id = int(folder_name.split("_")[0])

        for image_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, image_name)
            gray_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if gray_img is None:
                continue
            faces.append(gray_img)
            labels.append(student_id)

    return faces, labels


def main():
    print("Reading dataset...")
    faces, labels = prepare_training_data()

    if len(faces) == 0:
        print("No training data found. Run 1_register_student.py first.")
        return

    print(f"Training on {len(faces)} images from {len(set(labels))} students...")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    recognizer.save(TRAINER_FILE)

    print(f"Training complete. Model saved as '{TRAINER_FILE}'.")
    print("Now run 3_take_attendance.py to start marking attendance.")


if __name__ == "__main__":
    main()
