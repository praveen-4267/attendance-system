import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- PostgreSQL ---
    # Render injects a single DATABASE_URL env var when you attach a
    # PostgreSQL instance to a web service, e.g.:
    #   postgres://user:pass@host:5432/dbname
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        # Render's URL sometimes starts with "postgres://" — psycopg2 wants
        # "postgresql://". Normalize just in case.
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        _parsed = urlparse(DATABASE_URL)
        PG_HOST = _parsed.hostname
        PG_PORT = _parsed.port or 5432
        PG_USER = _parsed.username
        PG_PASSWORD = _parsed.password
        PG_DB = _parsed.path.lstrip("/")
    else:
        # Local dev fallback — set these in a .env file
        PG_HOST = os.getenv("PG_HOST", "localhost")
        PG_PORT = int(os.getenv("PG_PORT", 5432))
        PG_USER = os.getenv("PG_USER", "postgres")
        PG_PASSWORD = os.getenv("PG_PASSWORD", "")
        PG_DB = os.getenv("PG_DB", "smart_attendance")
        DATABASE_URL = (
            f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        )

    # --- Flask ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), "reports")

    # --- Face recognition ---
    # Lower = stricter match. 0.6 is the face_recognition library default.
    FACE_MATCH_TOLERANCE = float(os.getenv("FACE_MATCH_TOLERANCE", 0.5))
