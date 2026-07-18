# Automated Attendance System (Face Recognition) — Rural Schools

A low-cost, offline-first attendance system using a webcam, OpenCV face
recognition (LBPH), and a local SQLite database. Designed to run on a
basic laptop or a Raspberry Pi 4 without needing internet access.

## How it works (workflow)

1. **Register students** — capture face samples, save to database
2. **Train model** — build a recognizer from all registered faces
3. **Take attendance** — live webcam recognizes faces, logs to SQLite
4. **Export report** — generate a CSV for teachers/admins

Everything runs locally. No internet is required at any point — this
makes it suitable for schools with unreliable or no connectivity.

## Setup

1. Install Python 3.9–3.11 (avoid 3.12 — opencv-contrib support can lag)
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure a webcam is connected.

## Usage order

```
python 1_register_student.py     # run once per student
python 2_train_model.py          # run after registering all students
python 3_take_attendance.py      # run every day/session to mark attendance
python 4_export_report.py        # run anytime to export CSV
```

## Files

| File | Purpose |
|---|---|
| `database.py` | SQLite schema + all DB functions |
| `1_register_student.py` | Capture face samples for a new student |
| `2_train_model.py` | Train the LBPH recognizer |
| `3_take_attendance.py` | Live recognition + attendance marking |
| `4_export_report.py` | Export attendance to CSV |
| `attendance.db` | Auto-created SQLite database (students + attendance) |
| `trainer.yml` | Auto-created trained face model |
| `dataset/` | Auto-created folder of captured face images |
| `reports/` | CSV exports land here |

## Tuning tips for your demo

- `CONFIDENCE_THRESHOLD` in `3_take_attendance.py` controls strictness.
  Lower = stricter. If it misidentifies people, lower it (e.g. 50–60).
  If it fails to recognize registered students, raise it slightly.
- Capture face samples in the same lighting conditions you'll test in.
- Ask each student to move their head slightly during registration —
  this gives the model more angles to learn from.

## Ideas to extend for your report (the "rural" differentiator)

- **Offline-first sync**: this system already stores everything locally.
  Add a script that pushes `attendance.db` records to a cloud DB
  (Firebase/MySQL) whenever internet is detected — e.g. check
  connectivity every 30 mins and sync a queue of unsynced rows.
- **Low-cost hardware**: mention in your report that this runs on a
  Raspberry Pi 4 (~₹5000–6000) with a USB webcam, avoiding expensive
  dedicated attendance hardware.
- **SMS fallback**: for zero-internet areas, a GSM module (SIM800L) can
  send a daily attendance summary via SMS instead of syncing online.
- **Power resilience**: note that Raspberry Pi + battery pack/solar
  panel handles rural power cuts — worth a slide in your presentation.
- **Accuracy testing**: test recognition under different lighting/time
  of day and report accuracy % — examiners like real numbers.

## Known limitations to mention honestly in your report

- LBPH is less accurate than deep-learning face recognition (e.g.
  FaceNet/dlib) in poor lighting or with masks — acceptable tradeoff for
  a mini project given easier installation and lower compute needs.
- Works best with one face clearly in frame at a time; group/class
  photos with many faces need more testing and tuning.
