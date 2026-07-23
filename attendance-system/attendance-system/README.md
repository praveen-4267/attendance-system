# Face Recognition Attendance System

A mini-project: automated attendance using face recognition (OpenCV LBPH), built with Flask.

## Features
- Register students and capture face samples via webcam (in-browser)
- Train an LBPH face recognition model
- Live webcam-based attendance marking (one entry per student per day)
- View attendance records by date + export as CSV
- Ready to deploy on Render (Procfile + render.yaml included)

## Tech Stack
- Python, Flask
- OpenCV (opencv-contrib-python-headless) for face detection (Haar Cascade) + recognition (LBPH)
- SQLite for storing students & attendance
- Bootstrap 5 for UI
- Plain JS + `getUserMedia` for webcam capture (works on desktop/mobile browsers, no extra libraries)

## Project Structure
```
attendance-system/
├── app.py                # Flask app (all routes)
├── requirements.txt
├── Procfile              # For Render/Heroku start command
├── render.yaml            # Render one-click blueprint
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── capture.html
│   ├── attendance.html
│   └── records.html
└── static/css/style.css
```

## Run Locally

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Visit `http://localhost:5000`. Your browser will ask for camera permission — allow it.

## Usage Flow
1. **Register Student** → enter roll number & name → camera opens and auto-captures ~25 face images.
2. **Train Model** (dashboard button) → trains LBPH recognizer on all registered students.
3. **Mark Attendance** → live camera recognizes faces and logs attendance (once/day/student).
4. **Records** → filter by date, export CSV.

## Push to GitHub

```bash
cd attendance-system
git init
git add .
git commit -m "Initial commit: face recognition attendance system"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## Deploy on Render

**Option A — Blueprint (fastest):**
1. Push this repo to GitHub (steps above).
2. Go to https://dashboard.render.com/blueprints → **New Blueprint Instance**.
3. Connect your GitHub repo. Render reads `render.yaml` automatically and creates the web service.
4. Click **Apply** — it installs dependencies and starts the app with Gunicorn.

**Option B — Manual Web Service:**
1. Go to https://dashboard.render.com → **New** → **Web Service**.
2. Connect your GitHub repo.
3. Settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
4. Add an environment variable `SECRET_KEY` (any random string).
5. Click **Create Web Service**.

### Important Notes for Render (free tier)
- **Ephemeral disk**: Render's free web services don't persist disk across deploys/restarts. That means `dataset/`, `trainer/trainer.yml`, and `attendance.db` (student faces, trained model, attendance log) can be wiped when the service restarts or redeploys.
  - Fine for a demo/mini-project.
  - For real persistence, add a [Render Persistent Disk](https://render.com/docs/disks) (paid) mounted at the project folder, or swap SQLite for an external DB (e.g., Render PostgreSQL) and store face images in cloud storage (e.g., S3/Cloudinary).
- **Webcam access requires HTTPS** — Render serves your app over HTTPS by default, so `getUserMedia` will work fine in production.
- Free instances spin down after inactivity; the first request after idling may take ~30-60s to wake up.

## Notes / Limitations (mini-project scope)
- Uses classical OpenCV LBPH recognition — lightweight and easy to deploy, but less accurate than deep-learning face recognition (e.g., `face_recognition`/dlib or FaceNet). Good enough for a classroom demo with a handful of students.
- Works best with decent, even lighting and one face in frame at a time.
- Recognition threshold (`confidence > 70`) in `app.py`'s `/mark` route can be tuned — lower it for stricter matching, raise it if genuine users are being rejected.
