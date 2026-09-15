"""
StrideX Clinical Flask API
Wraps the existing analysis pipeline (pipeline.py) — do NOT modify that file.
"""
import os, io, json, uuid, threading
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS

import db
from pdf_generator import generate_gait_pdf
from pipeline import run_video_gait_analysis

app = Flask(__name__)
CORS(app, supports_credentials=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR  = os.path.join(PROJECT_ROOT, "data", "uploads")
OUTPUTS_DIR  = os.path.join(PROJECT_ROOT, "data", "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# in-memory live progress tracker (keyed by assessment_id)
analysis_jobs: dict = {}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _patient_id_from_token(token: str):
    """Minimal token decode: token is 'jwt-<user_id>'."""
    if not token:
        return None
    return token.replace("jwt-", "")

def _get_auth_user():
    """Read Authorization header and return the user row as a dict, or None."""
    header = request.headers.get("Authorization", "")
    token  = header.replace("Bearer ", "").strip()
    user_id = _patient_id_from_token(token)
    if not user_id:
        return None
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return db.dict_factory(c, row)


def _establish_baseline(patient_id: str, assessment_id: str, features: dict):
    """Store baseline metrics if patient has no existing baseline."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM baselines WHERE patient_id=?", (patient_id,))
    n = c.fetchone()["n"]
    if n > 0:
        conn.close()
        return  # baseline already set

    now = datetime.now().isoformat()
    BASELINE_METRICS = [
        "cadence", "walking_speed", "symmetry_score",
        "left_knee_rom", "right_knee_rom", "postural_sway",
        "step_time", "step_length", "stride_length",
        "knee_rom_asymmetry"
    ]
    for metric in BASELINE_METRICS:
        val = features.get(metric)
        if val is not None:
            try:
                c.execute(
                    "INSERT OR IGNORE INTO baselines (id,patient_id,assessment_id,metric,baseline_value,established_at) VALUES (?,?,?,?,?,?)",
                    (str(uuid.uuid4()), patient_id, assessment_id, metric, float(val), now)
                )
            except Exception:
                pass
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE WORKER (runs in background thread)
# ══════════════════════════════════════════════════════════════════════════════
def _run_analysis_worker(asm_id: str, video_path: str, patient_id: str):
    try:
        def _progress(pct, stage):
            analysis_jobs[asm_id] = {"percent": pct, "stage": stage, "status": "running"}

        analysis_jobs[asm_id] = {"percent": 0, "stage": "Initialising pipeline…", "status": "running"}

        result = run_video_gait_analysis(video_path, progress_callback=_progress)

        # persist time-series separately (can be large)
        ts_path = os.path.join(OUTPUTS_DIR, f"{asm_id}_timeseries.json")
        with open(ts_path, "w") as f:
            json.dump(result.get("timeseries", {}), f)

        features      = result.get("features", {})
        risk          = result.get("risk", {})
        features_json = json.dumps(features)
        risk_json     = json.dumps(risk)

        # Extract risk level from the nested risk structure
        risk_level = str(risk.get("overall_risk", "UNKNOWN")).upper()
        if risk_level not in ("LOW", "MODERATE", "HIGH"):
            risk_level = "UNKNOWN"

        # Calculate gait score: weighted average of the individual risk factor scores
        # (each factor has a 'score' field 0-100, higher is better)
        factors = risk.get("factors", [])
        if factors:
            factor_scores = [f.get("score", 50) for f in factors if isinstance(f.get("score"), (int, float))]
            gait_score = int(round(sum(factor_scores) / len(factor_scores))) if factor_scores else 0
        else:
            # Fallback: derive from symmetry + cadence indicators
            sym = float(features.get("symmetry_score", 75))
            cadence = float(features.get("cadence", 100))
            sway = float(features.get("postural_sway", 0.003))
            rom_asym = float(features.get("knee_rom_asymmetry", 10))
            sym_score = min(100, max(0, sym))
            cad_score = 100 if 95 <= cadence <= 130 else (75 if 80 <= cadence <= 145 else 50)
            sway_score = 100 if sway < 0.002 else (75 if sway < 0.005 else 50)
            rom_score = 100 if rom_asym < 20 else (75 if rom_asym < 35 else 40)
            gait_score = int(round(0.35*sym_score + 0.25*cad_score + 0.2*sway_score + 0.2*rom_score))

        # Store fps, duration, detection_rate so PDF can show them
        fps = int(features.get("fps", 0) or features.get("video_fps", 0) or 0)
        total_frames = int(features.get("total_video_frames", 0) or 0)
        duration = round(total_frames / fps, 1) if fps > 0 else 0
        detection_rate = float(features.get("detection_rate", 0))

        conn = db.get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE assessments SET status='completed',gait_score=?,risk_level=?,features=?,risk=?,fps=?,duration=? WHERE id=?",
            (gait_score, risk_level, features_json, risk_json, fps or None, duration or None, asm_id)
        )
        conn.commit()
        conn.close()

        # establish personal baseline if this is the first assessment
        _establish_baseline(patient_id, asm_id, features)

        analysis_jobs[asm_id] = {"percent": 100, "stage": "Complete", "status": "completed"}
    except Exception as exc:
        import traceback; traceback.print_exc()
        analysis_jobs[asm_id] = {"percent": 0, "stage": f"Error: {exc}", "status": "failed"}
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("UPDATE assessments SET status='failed',notes=? WHERE id=?", (str(exc), asm_id))
        conn.commit()
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE LOWER(email)=?", (email,))
    row = c.fetchone()
    conn.close()

    if not row or not db.verify_password(password, row["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    user = dict(row)
    # attach patient profile if role==patient
    if user["role"] == "patient":
        conn2 = db.get_connection()
        c2 = conn2.cursor()
        c2.execute("SELECT * FROM patients WHERE id=?", (user["id"],))
        prow = c2.fetchone()
        conn2.close()
        if prow:
            user["patient_profile"] = dict(prow)

    user.pop("password", None)
    return jsonify({"token": f"jwt-{user['id']}", "user": user})


@app.route("/api/auth/register", methods=["POST"])
def register():
    """Patient self-registration. Clinicians are pre-seeded only."""
    data = request.json or {}
    now  = datetime.now().isoformat()
    pid  = f"PT-{uuid.uuid4().hex[:5].upper()}"

    # check email uniqueness
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE LOWER(email)=?", (data.get("email","").lower(),))
    if c.fetchone():
        conn.close()
        return jsonify({"error": "An account with this email already exists"}), 400

    # calculate age from dob
    age = None
    if data.get("dob"):
        try:
            dob = datetime.strptime(data["dob"], "%Y-%m-%d")
            age = (datetime.now() - dob).days // 365
        except Exception:
            pass

    try:
        c.execute(
            "INSERT INTO users (id,role,name,email,password,created_at) VALUES (?,?,?,?,?,?)",
            (pid, "patient", data.get("name"), data.get("email"),
             db._hash(data.get("password","")), now)
        )
        c.execute(
            '''INSERT INTO patients
               (id,name,email,dob,age,gender,
                mobility_level,activity_frequency,walking_change,assessment_goal,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (pid, data.get("name"), data.get("email"), data.get("dob"), age,
             data.get("gender",""),
             data.get("mobility_level","Independent"),
             data.get("activity_frequency","Occasionally"),
             data.get("walking_change","No"),
             data.get("assessment_goal","Track my gait over time"), now)
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(exc)}), 400

    user = {
        "id": pid, "role": "patient",
        "name": data.get("name"), "email": data.get("email"),
        "created_at": now
    }
    conn.close()
    return jsonify({"token": f"jwt-{pid}", "user": user}), 201


# ══════════════════════════════════════════════════════════════════════════════
# PATIENT – self-service routes
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/patient/profile", methods=["GET"])
def patient_profile():
    user = _get_auth_user()
    if not user or user["role"] != "patient":
        return jsonify({"error": "Unauthorized"}), 403
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id=?", (user["id"],))
    profile = c.fetchone() or {}
    conn.close()
    return jsonify({"profile": profile})


@app.route("/api/patient/assessments", methods=["GET"])
def patient_assessments():
    user = _get_auth_user()
    if not user or user["role"] != "patient":
        return jsonify({"error": "Unauthorized"}), 403
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM assessments WHERE patient_id=? ORDER BY created_at DESC", (user["id"],))
    asms = c.fetchall()
    conn.close()
    return jsonify({"assessments": asms})


@app.route("/api/patient/baseline", methods=["GET"])
def patient_baseline():
    user = _get_auth_user()
    if not user or user["role"] != "patient":
        return jsonify({"error": "Unauthorized"}), 403
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM baselines WHERE patient_id=?", (user["id"],))
    rows = c.fetchall()
    conn.close()
    # convert to {metric: value} dict
    baseline = {r["metric"]: r["baseline_value"] for r in rows}
    established = rows[0]["established_at"] if rows else None
    return jsonify({"baseline": baseline, "established_at": established})


@app.route("/api/patient/trends", methods=["GET"])
def patient_trends():
    user = _get_auth_user()
    if not user or user["role"] != "patient":
        return jsonify({"error": "Unauthorized"}), 403
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute(
        "SELECT * FROM assessments WHERE patient_id=? AND status='completed' ORDER BY date ASC",
        (user["id"],)
    )
    asms = c.fetchall()
    conn.close()

    points = []
    for a in asms:
        f = a.get("features") or {}
        points.append({
            "date": a["date"], "assessment_id": a["id"],
            "gait_score": a["gait_score"], "risk_level": a["risk_level"],
            "cadence": f.get("cadence"), "walking_speed": f.get("walking_speed"),
            "symmetry_score": f.get("symmetry_score"),
            "left_knee_rom": f.get("left_knee_rom"), "right_knee_rom": f.get("right_knee_rom"),
            "postural_sway": f.get("postural_sway"), "step_time": f.get("step_time"),
        })
    return jsonify({"data": points})


@app.route("/api/patient/dashboard", methods=["GET"])
def patient_dashboard():
    user = _get_auth_user()
    if not user or user["role"] != "patient":
        return jsonify({"error": "Unauthorized"}), 403

    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute(
        "SELECT * FROM assessments WHERE patient_id=? AND status='completed' ORDER BY created_at DESC LIMIT 1",
        (user["id"],)
    )
    latest = c.fetchone()
    c.execute("SELECT COUNT(*) as n FROM assessments WHERE patient_id=?", (user["id"],))
    total = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM baselines WHERE patient_id=?", (user["id"],))
    has_baseline = c.fetchone()["n"] > 0
    conn.close()

    return jsonify({
        "patient_id": user["id"],
        "name": user["name"],
        "total_assessments": total,
        "has_baseline": has_baseline,
        "latest_assessment": latest,
    })


# ══════════════════════════════════════════════════════════════════════════════
# PATIENTS – clinician access
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/patients", methods=["GET"])
def get_patients():
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    # join to get latest assessment info
    c.execute("""
        SELECT p.*,
               a.gait_score   AS latest_gait_score,
               a.risk_level   AS latest_risk_level,
               a.date         AS last_assessment_date
        FROM patients p
        LEFT JOIN assessments a ON a.id = (
            SELECT id FROM assessments WHERE patient_id=p.id AND status='completed'
            ORDER BY created_at DESC LIMIT 1
        )
        ORDER BY p.created_at DESC
    """)
    patients = c.fetchall()
    conn.close()
    return jsonify({"patients": patients})


@app.route("/api/patients", methods=["POST"])
def create_patient():
    data = request.json or {}
    pid  = f"PT-{uuid.uuid4().hex[:5].upper()}"
    now  = datetime.now().isoformat()
    conn = db.get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO patients (id,name,email,dob,age,gender,condition,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (pid, data.get("name"), data.get("email"), data.get("dob"),
             data.get("age"), data.get("gender"), data.get("condition"), now)
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(exc)}), 400
    conn.close()
    return jsonify({"success": True, "patient": {"id": pid}}), 201


@app.route("/api/patients/<pid>", methods=["GET"])
def get_patient(pid):
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id=?", (pid,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        return jsonify({"error": "Patient not found"}), 404
    # last assessment
    c.execute("SELECT * FROM assessments WHERE patient_id=? ORDER BY created_at DESC LIMIT 1", (pid,))
    last = c.fetchone()
    # baseline
    c.execute("SELECT * FROM baselines WHERE patient_id=?", (pid,))
    brows = c.fetchall()
    baseline = {r["metric"]: r["baseline_value"] for r in brows}
    conn.close()
    return jsonify({"patient": patient, "latest_assessment": last, "baseline": baseline})


@app.route("/api/patients/<pid>/assessments", methods=["GET"])
def patient_assessments_clinician(pid):
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM assessments WHERE patient_id=? ORDER BY created_at DESC", (pid,))
    asms = c.fetchall()
    conn.close()
    return jsonify({"assessments": asms})


@app.route("/api/patients/<pid>/baseline", methods=["GET"])
def patient_baseline_clinician(pid):
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM baselines WHERE patient_id=?", (pid,))
    rows = c.fetchall()
    conn.close()
    baseline = {r["metric"]: r["baseline_value"] for r in rows}
    established = rows[0]["established_at"] if rows else None
    return jsonify({"baseline": baseline, "established_at": established})


@app.route("/api/patients/<pid>/trends", methods=["GET"])
def patient_trends_clinician(pid):
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute(
        "SELECT * FROM assessments WHERE patient_id=? AND status='completed' ORDER BY date ASC", (pid,)
    )
    asms = c.fetchall()
    conn.close()
    points = []
    for a in asms:
        f = a.get("features") or {}
        points.append({
            "date": a["date"], "assessment_id": a["id"],
            "gait_score": a["gait_score"], "risk_level": a["risk_level"],
            "cadence": f.get("cadence"), "symmetry_score": f.get("symmetry_score"),
            "left_knee_rom": f.get("left_knee_rom"), "postural_sway": f.get("postural_sway"),
        })
    return jsonify({"data": points})


# ══════════════════════════════════════════════════════════════════════════════
# ASSESSMENTS
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/assessments", methods=["POST"])
def create_assessment():
    data   = request.json or {}
    asm_id = f"ASM-{uuid.uuid4().hex[:8].upper()}"
    now    = datetime.now().isoformat()
    conn   = db.get_connection()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO assessments
           (id,patient_id,doctor_id,patient_name,doctor_name,
            date,walking_condition,camera_view,notes,status,created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (asm_id, data.get("patient_id"), data.get("doctor_id"),
         data.get("patient_name"), data.get("doctor_name"),
         data.get("date", datetime.now().strftime("%Y-%m-%d")),
         data.get("walking_condition",""), data.get("camera_view",""),
         data.get("notes",""), "pending", now)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "assessment": {"id": asm_id}}), 201


@app.route("/api/assessments/<asm_id>", methods=["GET"])
def get_assessment(asm_id):
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM assessments WHERE id=?", (asm_id,))
    asm = c.fetchone()
    conn.close()
    if not asm:
        return jsonify({"error": "Assessment not found"}), 404
    # attach baseline for comparison
    conn2 = db.get_connection()
    conn2.row_factory = db.dict_factory
    c2 = conn2.cursor()
    c2.execute("SELECT * FROM baselines WHERE patient_id=?", (asm.get("patient_id"),))
    brows = c2.fetchall()
    conn2.close()
    asm["baseline"] = {r["metric"]: r["baseline_value"] for r in brows}
    return jsonify({"assessment": asm})


@app.route("/api/assessments/<asm_id>/upload", methods=["POST"])
def upload_video(asm_id):
    if "video" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOADS_DIR, f"{asm_id}_{filename}")
    file.save(path)
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("UPDATE assessments SET video_path=?,video_filename=? WHERE id=?", (path, filename, asm_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/assessments/<asm_id>/analyze", methods=["POST"])
def start_analysis(asm_id):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT video_path, patient_id FROM assessments WHERE id=?", (asm_id,))
    row = c.fetchone()

    video_path = row["video_path"] if row else None
    patient_id = row["patient_id"] if row else None

    if not video_path or not os.path.exists(video_path):
        sample = os.path.join(PROJECT_ROOT, "sample walk.mp4")
        if os.path.exists(sample):
            video_path = sample
            c.execute("UPDATE assessments SET video_path=?,video_filename=? WHERE id=?",
                      (sample, "sample walk.mp4", asm_id))
        else:
            conn.close()
            return jsonify({"error": "No video available"}), 400

    c.execute("UPDATE assessments SET status='processing' WHERE id=?", (asm_id,))
    conn.commit()
    conn.close()

    analysis_jobs[asm_id] = {"stage": "Starting", "percent": 0, "status": "starting"}
    t = threading.Thread(
        target=_run_analysis_worker,
        args=(asm_id, video_path, patient_id or ""),
        daemon=True
    )
    t.start()
    return jsonify({"success": True, "message": "Analysis started"})


@app.route("/api/assessments/<asm_id>/status", methods=["GET"])
def analysis_status(asm_id):
    job = analysis_jobs.get(asm_id)
    if job:
        return jsonify(job)
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT status FROM assessments WHERE id=?", (asm_id,))
    row = c.fetchone()
    conn.close()
    status = row["status"] if row else "unknown"
    return jsonify({
        "stage": "Completed" if status == "completed" else status.capitalize(),
        "percent": 100 if status == "completed" else 0,
        "status": status,
    })


@app.route("/api/assessments/<asm_id>/timeseries", methods=["GET"])
def get_timeseries(asm_id):
    ts_path = os.path.join(OUTPUTS_DIR, f"{asm_id}_timeseries.json")
    if not os.path.exists(ts_path):
        return jsonify({"error": "Timeseries not available"}), 404
    with open(ts_path) as f:
        raw = json.load(f)
    # Normalize key names: pipeline uses plural snake_case, frontend expects singular
    normalized = {
        "time":               raw.get("timestamps", raw.get("time", [])),
        "left_knee_angle":    raw.get("left_knee_angles",  raw.get("left_knee_angle",  [])),
        "right_knee_angle":   raw.get("right_knee_angles", raw.get("right_knee_angle", [])),
        "left_ankle_angle":   raw.get("left_ankle_angles", raw.get("left_ankle_angle", [])),
        "right_ankle_angle":  raw.get("right_ankle_angles",raw.get("right_ankle_angle",[])),
        "left_angular_velocity":  raw.get("left_angular_velocity",  []),
        "right_angular_velocity": raw.get("right_angular_velocity", []),
        "com_x": raw.get("com_x", []),
        "com_y": raw.get("com_y", []),
    }
    return jsonify(normalized)


@app.route("/api/assessments/<asm_id>/pdf", methods=["GET"])
def download_pdf(asm_id):
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM assessments WHERE id=?", (asm_id,))
    asm = c.fetchone()
    if not asm:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    c.execute("SELECT * FROM patients WHERE id=?", (asm.get("patient_id"),))
    patient = c.fetchone() or {}
    conn.close()

    pdf_bytes = generate_gait_pdf(
        assessment_data={
            "id": asm.get("id"), "date": asm.get("date"),
            "patient_name": asm.get("patient_name"),
            "doctor_name": asm.get("doctor_name"),
            "walking_condition": asm.get("walking_condition"),
            "camera_view": asm.get("camera_view"),
            "video_filename": asm.get("video_filename",""),
            "fps": asm.get("fps", 30), "duration": asm.get("duration", 0),
            "risk_level": asm.get("risk_level","LOW"),
            "gait_score": asm.get("gait_score", 0),
            "features": asm.get("features",{}),
            "risk_factors": (asm.get("risk") or {}).get("factors",[]),
            "clinical_narrative": (asm.get("risk") or {}).get("clinical_narrative",""),
        },
        patient_data=patient
    )
    return send_file(
        io.BytesIO(pdf_bytes), mimetype="application/pdf",
        as_attachment=True,
        download_name=f"StrideX_Report_{asm_id}.pdf"
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLINICIAN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    conn = db.get_connection()
    conn.row_factory = db.dict_factory
    c = conn.cursor()
    c.execute("SELECT count(*) as n FROM patients")
    pat_count = c.fetchone()["n"]
    c.execute("SELECT * FROM assessments ORDER BY created_at DESC")
    all_asms = c.fetchall()
    conn.close()

    month = datetime.now().strftime("%Y-%m")
    this_month    = [a for a in all_asms if str(a.get("created_at","")).startswith(month)]
    review_needed = [a for a in all_asms if a.get("risk_level") in ("MODERATE","HIGH")]

    return jsonify({
        "total_patients": pat_count,
        "assessments_this_month": len(this_month),
        "patients_requiring_review": len({a["patient_id"] for a in review_needed if a.get("patient_id")}),
        "total_assessments": len(all_asms),
        "recent_assessments": all_asms[:8],
    })


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "3.0.0", "db": "SQLite"})


# ══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  STRIDEX Clinical API  v3.0  —  SQLite backend")
    print("=" * 60)
    db.init_db()
    db.seed_demo_data()
    print("  Listening on http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
