import sqlite3
import json
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stridex.db")

def _hash(pw):
    """Simple SHA-256 hash. Replace with bcrypt in production."""
    return hashlib.sha256(pw.encode()).hexdigest()

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── users ─────────────────────────────────────────────────────────────────
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id          TEXT PRIMARY KEY,
        role        TEXT NOT NULL,          -- 'patient' | 'doctor'
        name        TEXT NOT NULL,
        email       TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,          -- SHA-256 hash
        created_at  TEXT NOT NULL
    )''')

    # ── patient profiles ──────────────────────────────────────────────────────
    c.execute('''CREATE TABLE IF NOT EXISTS patients (
        id                  TEXT PRIMARY KEY,
        name                TEXT,
        email               TEXT,
        dob                 TEXT,
        age                 INTEGER,
        gender              TEXT,
        condition           TEXT,
        mobility_level      TEXT DEFAULT 'Independent',
        activity_frequency  TEXT DEFAULT 'Occasionally',
        walking_change      TEXT DEFAULT 'No',
        assessment_goal     TEXT DEFAULT 'Track my gait over time',
        created_at          TEXT
    )''')

    # ── assessments ───────────────────────────────────────────────────────────
    c.execute('''CREATE TABLE IF NOT EXISTS assessments (
        id                TEXT PRIMARY KEY,
        patient_id        TEXT,
        doctor_id         TEXT,
        patient_name      TEXT,
        doctor_name       TEXT,
        date              TEXT,
        walking_condition TEXT,
        camera_view       TEXT,
        notes             TEXT,
        video_path        TEXT,
        video_filename    TEXT,
        status            TEXT DEFAULT 'pending',
        gait_score        INTEGER,
        risk_level        TEXT,
        duration          INTEGER,
        fps               INTEGER,
        features          TEXT,   -- JSON blob
        risk              TEXT,   -- JSON blob
        created_at        TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')

    # ── personal baselines ────────────────────────────────────────────────────
    c.execute('''CREATE TABLE IF NOT EXISTS baselines (
        id              TEXT PRIMARY KEY,
        patient_id      TEXT NOT NULL,
        assessment_id   TEXT NOT NULL,
        metric          TEXT NOT NULL,
        baseline_value  REAL NOT NULL,
        established_at  TEXT NOT NULL,
        UNIQUE(patient_id, metric)          -- one baseline per metric per patient
    )''')

    conn.commit()
    conn.close()

# ── seeding ───────────────────────────────────────────────────────────────────
def seed_demo_data():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE email='doctor@stridex.health'")
    if c.fetchone():
        conn.close()
        return          # already seeded

    now = datetime.now().isoformat()

    # ── demo clinician (PRE-CREATED, cannot register via website) ─────────────
    c.execute(
        "INSERT INTO users (id,role,name,email,password,created_at) VALUES (?,?,?,?,?,?)",
        ("dr-sarah", "doctor", "Dr. Sarah Jenkins",
         "doctor@stridex.health", _hash("demo1234"), now)
    )

    conn.commit()
    conn.close()

    conn.commit()
    conn.close()

# ── helpers ───────────────────────────────────────────────────────────────────
def dict_factory(cursor, row):
    """Convert sqlite3.Row to dict, JSON-parsing features/risk blobs."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    for blob in ("features", "risk"):
        if blob in d and d[blob] and isinstance(d[blob], str):
            try:
                d[blob] = json.loads(d[blob])
            except Exception:
                pass
    return d

def rows_to_dicts(cursor):
    """Fetch all rows and convert to dicts."""
    return [dict_factory(cursor, r) for r in cursor.fetchall()]

def verify_password(plain, hashed):
    return _hash(plain) == hashed
