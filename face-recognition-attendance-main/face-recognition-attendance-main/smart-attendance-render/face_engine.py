"""Face encoding + recognition logic, built on OpenCV (capture/decode) and
the `face_recognition` library (dlib ResNet embeddings under the hood)."""
import base64
import io
import numpy as np
import cv2
import face_recognition
from config import Config


def decode_base64_image(data_url: str) -> np.ndarray:
    """Convert a data:image/jpeg;base64,... string (from a webcam <canvas>) into an OpenCV BGR image."""
    header, encoded = data_url.split(",", 1) if "," in data_url else (None, data_url)
    img_bytes = base64.b64decode(encoded)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame


def extract_face_encoding(image_bgr: np.ndarray):
    """Detect the largest face in the image and return its 128-d encoding.
    Returns None if no face is found."""
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb, model="hog")  # use "cnn" if GPU available
    if not locations:
        return None, None

    # If multiple faces, pick the largest bounding box (closest to camera)
    def area(loc):
        top, right, bottom, left = loc
        return (bottom - top) * (right - left)
    largest = max(locations, key=area)

    encodings = face_recognition.face_encodings(rgb, known_face_locations=[largest])
    if not encodings:
        return None, None
    return encodings[0], largest


def find_best_match(unknown_encoding, known_students, tolerance=None):
    """known_students: list of dicts with 'student_id', 'name', 'roll_number', 'face_encoding' (list).
    Returns (student_dict, confidence) or (None, 0) if no match within tolerance."""
    if tolerance is None:
        tolerance = Config.FACE_MATCH_TOLERANCE
    if not known_students:
        return None, 0.0

    known_encodings = [np.array(s["face_encoding"]) for s in known_students]
    distances = face_recognition.face_distance(known_encodings, unknown_encoding)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])

    if best_distance <= tolerance:
        confidence = max(0.0, 1.0 - best_distance)  # rough confidence score
        return known_students[best_idx], confidence
    return None, 0.0


def draw_face_box(image_bgr, location, label):
    top, right, bottom, left = location
    cv2.rectangle(image_bgr, (left, top), (right, bottom), (0, 200, 0), 2)
    cv2.putText(image_bgr, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
    return image_bgr
