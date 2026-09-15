"""StrideX backend services.

This module powers a Streamlit research prototype for mobility screening and
longitudinal monitoring. It deliberately separates measured inputs, optional
pose-estimation outputs, and demonstration-only sensor data.

Important: StrideX is not a diagnostic device. The rules and thresholds in this
prototype are for hackathon demonstration and require clinical validation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from hashlib import sha256
from html import escape
from io import StringIO
import csv
import math
import os
import random
import statistics
import tempfile
import uuid
from typing import Any, Iterable, Mapping, Sequence
from ai.features.gait_features import (
    calculate_cadence,
    calculate_walking_speed,
    calculate_symmetry,
    calculate_knee_angle,
    calculate_hip_angle,
    calculate_step_variability,
)
from ai.models.predictor import predict_risk       

try:  # Optional computer-vision stack
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

try:
    import mediapipe as mp  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    mp = None

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    np = None

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Image = None


APP_VERSION = "4.2.0"
DISCLAIMER = (
    "Research prototype for screening support only. It does not diagnose a "
    "medical condition or replace a qualified clinician."
)

# Demonstration thresholds. These are intentionally easy to inspect and explain.
PRESSURE_MEDIUM = 40.0
PRESSURE_HIGH = 70.0
PAIN_MEDIUM = 4.0
PAIN_HIGH = 7.0
CONCERN_MEDIUM = 35.0
CONCERN_HIGH = 65.0

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "m4v"}

RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _uploaded_bytes(uploaded: Any) -> bytes:
    """Read bytes from Streamlit UploadedFile, bytes, or a local path."""
    if uploaded is None:
        return b""
    if isinstance(uploaded, bytes):
        return uploaded
    if isinstance(uploaded, bytearray):
        return bytes(uploaded)
    if isinstance(uploaded, str) and os.path.exists(uploaded):
        with open(uploaded, "rb") as handle:
            return handle.read()
    if hasattr(uploaded, "getvalue"):
        return bytes(uploaded.getvalue())
    if hasattr(uploaded, "read"):
        position = None
        try:
            position = uploaded.tell()
        except Exception:
            pass
        data = uploaded.read()
        if position is not None:
            try:
                uploaded.seek(position)
            except Exception:
                pass
        return bytes(data)
    raise TypeError("Unsupported uploaded-file object.")


def _stable_seed(parts: Iterable[Any]) -> int:
    digest = sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _risk_label(priority: str) -> str:
    return {
        "LOW": "Routine monitoring",
        "MEDIUM": "Follow-up recommended",
        "HIGH": "Prompt clinical review",
    }.get(priority.upper(), "Review required")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_record_time(record: Mapping[str, Any]) -> datetime | None:
    raw = record.get("timestamp_iso") or record.get("time")
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    for fmt in (None, "%d %b %Y, %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            if fmt is None:
                return datetime.fromisoformat(str(raw))
            return datetime.strptime(str(raw), fmt)
        except (TypeError, ValueError):
            continue
    return None


# ---------------------------------------------------------------------------
# Capability detection
# ---------------------------------------------------------------------------

def get_capabilities() -> dict[str, Any]:
    mediapipe_legacy = bool(mp is not None and getattr(mp, "solutions", None))
    return {
        "opencv_available": cv2 is not None,
        "mediapipe_available": mediapipe_legacy,
        "numpy_available": np is not None,
        "pillow_available": Image is not None,
        "real_pose_pipeline_available": bool(
            cv2 is not None and mediapipe_legacy and np is not None and Image is not None
        ),
        "sensor_mode": "simulation",
        "version": APP_VERSION,
    }


# ---------------------------------------------------------------------------
# Rule-based screening engine
# ---------------------------------------------------------------------------

def detect_risk(pressure: float, pain: float) -> tuple[str, str]:
    """Return a transparent screening priority from pressure and pain inputs.

    The function keeps the original two-argument signature for compatibility.
    It does not diagnose disease.
    """
    pressure = _clamp(pressure, 0, 100)
    pain = _clamp(pain, 0, 10)

    if pressure >= PRESSURE_HIGH or pain >= PAIN_HIGH:
        return "HIGH", "Pressure or self-reported pain crossed the high-priority demo threshold."
    if pressure >= PRESSURE_MEDIUM or pain >= PAIN_MEDIUM:
        return "MEDIUM", "Pressure or self-reported pain crossed the follow-up demo threshold."
    return "LOW", "Pressure and self-reported pain remain below the follow-up demo thresholds."


def get_recommendation(risk: str) -> str:
    """Return cautious, non-diagnostic next-step wording."""
    risk = str(risk).strip().upper()
    if risk == "HIGH":
        return (
            "Arrange prompt review by a qualified clinician or physiotherapist. "
            "Use local urgent-care pathways if there is sudden weakness, inability to walk, "
            "a recent fall, or severe worsening pain."
        )
    if risk == "MEDIUM":
        return (
            "Schedule a non-urgent clinical or physiotherapy follow-up, repeat the mobility "
            "assessment under the same conditions, and monitor for worsening symptoms."
        )
    if risk == "LOW":
        return (
            "Continue routine monitoring and repeat the assessment if mobility, balance, or "
            "pain changes. Seek professional advice for persistent concerns."
        )
    return "Review the inputs and repeat the assessment."


def _classify_priority(
    concern_score: float,
    pressure: float,
    pain: float,
) -> str:
    if concern_score >= CONCERN_HIGH or pressure >= PRESSURE_HIGH or pain >= PAIN_HIGH:
        return "HIGH"
    if concern_score >= CONCERN_MEDIUM or pressure >= PRESSURE_MEDIUM or pain >= PAIN_MEDIUM:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Pose-estimation utilities
# ---------------------------------------------------------------------------

def _point(landmarks: Sequence[Any], index: int) -> tuple[float, float, float]:
    item = landmarks[index]
    return float(item.x), float(item.y), float(getattr(item, "visibility", 1.0))


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _joint_angle(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> float:
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    norm_ba = math.hypot(*ba)
    norm_bc = math.hypot(*bc)
    if norm_ba == 0 or norm_bc == 0:
        return 180.0
    cosine = _clamp((ba[0] * bc[0] + ba[1] * bc[1]) / (norm_ba * norm_bc), -1, 1)
    return math.degrees(math.acos(cosine))


def _frame_features(landmarks: Sequence[Any], timestamp: float) -> dict[str, float]:
    # MediaPipe indices: shoulders 11/12, hips 23/24, knees 25/26,
    # ankles 27/28, heels 29/30, foot index 31/32.
    ls = _point(landmarks, 11)
    rs = _point(landmarks, 12)
    lh = _point(landmarks, 23)
    rh = _point(landmarks, 24)
    lk = _point(landmarks, 25)
    rk = _point(landmarks, 26)
    la = _point(landmarks, 27)
    ra = _point(landmarks, 28)

    left_knee_angle = _joint_angle((lh[0], lh[1]), (lk[0], lk[1]), (la[0], la[1]))
    right_knee_angle = _joint_angle((rh[0], rh[1]), (rk[0], rk[1]), (ra[0], ra[1]))

    shoulder_mid = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
    hip_mid = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)
    body_scale = max(0.04, _distance(shoulder_mid, hip_mid))
    trunk_tilt = abs(shoulder_mid[0] - hip_mid[0]) / body_scale

    key_visibility = statistics.fmean(
        [ls[2], rs[2], lh[2], rh[2], lk[2], rk[2], la[2], ra[2]]
    )

    return {
        "timestamp": timestamp,
        "left_knee_angle": left_knee_angle,
        "right_knee_angle": right_knee_angle,
        "left_ankle_y": la[1],
        "right_ankle_y": ra[1],
        "left_ankle_x": la[0],
        "right_ankle_x": ra[0],
        "hip_mid_x": hip_mid[0],
        "trunk_tilt": trunk_tilt,
        "body_scale": body_scale,
        "visibility": key_visibility,
    }


def _score_to_label(score: float, high_cutoff: float = 85, medium_cutoff: float = 65) -> str:
    if score >= high_cutoff:
        return "High"
    if score >= medium_cutoff:
        return "Moderate"
    return "Low"


def _stability_label(score: float) -> str:
    if score >= 85:
        return "Stable"
    if score >= 65:
        return "Slight variation"
    return "Review recommended"


def _estimate_cadence(features: Sequence[Mapping[str, float]]) -> float | None:
    if len(features) < 12:
        return None
    timestamps = [row["timestamp"] for row in features]
    duration = timestamps[-1] - timestamps[0]
    if duration <= 1.5:
        return None

    signal = [row["left_ankle_y"] - row["right_ankle_y"] for row in features]
    mean_signal = statistics.fmean(signal)
    centered = [value - mean_signal for value in signal]
    amplitude = statistics.pstdev(centered) if len(centered) > 1 else 0.0
    threshold = max(0.006, amplitude * 0.18)

    crossings = 0
    previous_sign = 0
    for value in centered:
        if abs(value) < threshold:
            continue
        sign = 1 if value > 0 else -1
        if previous_sign and sign != previous_sign:
            crossings += 1
        previous_sign = sign

    if crossings < 2:
        return None
    cadence = crossings / duration * 60.0
    if not 35 <= cadence <= 220:
        return None
    return round(cadence, 1)


def _calculate_gait_metrics(features: Sequence[Mapping[str, float]]) -> dict[str, Any]:
    if not features:
        return {}

    knee_differences = [
        abs(row["left_knee_angle"] - row["right_knee_angle"]) for row in features
    ]
    mean_knee_difference = statistics.fmean(knee_differences)
    knee_symmetry = _clamp(100 - (mean_knee_difference / 55.0 * 100), 0, 100)

    left_range = max(row["left_ankle_y"] for row in features) - min(
        row["left_ankle_y"] for row in features
    )
    right_range = max(row["right_ankle_y"] for row in features) - min(
        row["right_ankle_y"] for row in features
    )
    movement_symmetry = 100.0
    if max(left_range, right_range) > 0.005:
        movement_symmetry = 100 - abs(left_range - right_range) / max(left_range, right_range) * 100

    step_symmetry = _clamp(0.65 * knee_symmetry + 0.35 * movement_symmetry, 0, 100)

    trunk_tilts = [row["trunk_tilt"] for row in features]
    trunk_variability = statistics.pstdev(trunk_tilts) if len(trunk_tilts) > 1 else trunk_tilts[0]
    trunk_stability = _clamp(100 - trunk_variability * 450, 0, 100)

    temporal_variability = statistics.pstdev(knee_differences) if len(knee_differences) > 1 else 12
    regularity_score = _clamp(100 - temporal_variability * 2.2, 0, 100)

    pose_quality = _clamp(statistics.fmean(row["visibility"] for row in features) * 100, 0, 100)
    cadence = _estimate_cadence(features)

    return {
        "step_symmetry": round(step_symmetry),
        "knee_symmetry": round(knee_symmetry),
        "stride_regularity_score": round(regularity_score),
        "stride_consistency": _score_to_label(regularity_score),
        "trunk_stability_score": round(trunk_stability),
        "gait_stability": _stability_label(trunk_stability),
        "pose_quality": round(pose_quality),
        "cadence_estimate": cadence,
        "frames_with_pose": len(features),
    }


def _demo_pose_metrics(payload: bytes, name: str) -> dict[str, Any]:
    rng = random.Random(_stable_seed([name, len(payload), sha256(payload).hexdigest()[:16]]))
    symmetry = rng.randint(72, 92)
    regularity = rng.randint(68, 94)
    stability = rng.randint(70, 95)
    quality = rng.randint(86, 97)
    return {
        "step_symmetry": symmetry,
        "knee_symmetry": max(60, symmetry - rng.randint(0, 7)),
        "stride_regularity_score": regularity,
        "stride_consistency": _score_to_label(regularity),
        "trunk_stability_score": stability,
        "gait_stability": _stability_label(stability),
        "pose_quality": quality,
        "cadence_estimate": rng.randint(82, 116),
        "frames_with_pose": 0,
    }


def _demo_pose_response(payload: bytes, name: str, media_type: str) -> dict[str, Any]:
    metrics = _demo_pose_metrics(payload, name)
    return {
        "success": True,
        "analysis_mode": "demo_fallback",
        "media_type": media_type,
        "message": (
            "MediaPipe runtime was not available, so StrideX generated deterministic "
            "demonstration metrics. Install mediapipe to enable real landmark processing."
        ),
        "warning": "Demonstration metrics are not measurements and must not be used clinically.",
        "status_steps": [
            "Media accepted",
            "Pose runtime unavailable",
            "Deterministic demo metrics generated",
        ],
        "pose_output": {
            "landmarks_detected": False,
            "keypoints_supported": 33,
            "tracked_joints": ["Hip", "Knee", "Ankle"],
        },
        "gait_metrics": metrics,
        "quality": metrics["pose_quality"],
    }


def process_gait_images(img1: Any = None, img2: Any = None) -> dict[str, Any]:
    """Process one or two gait images with MediaPipe when available.

    If the optional computer-vision dependency is unavailable, the function keeps
    the app operational with clearly labelled deterministic demonstration metrics.
    """
    uploads = [item for item in (img1, img2) if item is not None]
    if not uploads:
        return {"success": False, "message": "Upload at least one image."}

    invalid = [
        getattr(item, "name", "image")
        for item in uploads
        if _get_extension(getattr(item, "name", "")) not in ALLOWED_IMAGE_EXTENSIONS
    ]
    if invalid:
        return {
            "success": False,
            "message": f"Unsupported image format: {', '.join(invalid)}.",
        }

    payloads = [_uploaded_bytes(item) for item in uploads]
    combined = b"".join(payloads)
    names = ", ".join(getattr(item, "name", "image") for item in uploads)
    capabilities = get_capabilities()
    if not capabilities["real_pose_pipeline_available"]:
        response = _demo_pose_response(combined, names, "images")
        response["images_received"] = len(uploads)
        return response

    features: list[dict[str, float]] = []
    try:
        pose_api = mp.solutions.pose  # type: ignore[union-attr]
        with pose_api.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.50,
        ) as pose:
            for index, payload in enumerate(payloads):
                with Image.open(__import__("io").BytesIO(payload)) as image:  # type: ignore[union-attr]
                    rgb = np.array(image.convert("RGB"))  # type: ignore[union-attr]
                result = pose.process(rgb)
                if result.pose_landmarks:
                    features.append(_frame_features(result.pose_landmarks.landmark, float(index)))
    except Exception as exc:
        return {
            "success": False,
            "message": f"Pose processing failed: {exc}",
            "analysis_mode": "error",
        }

    if not features:
        return {
            "success": False,
            "message": (
                "No full-body pose was detected. Use a well-lit image showing the whole person "
                "from head to feet with minimal obstruction."
            ),
            "analysis_mode": "mediapipe",
        }

    metrics = _calculate_gait_metrics(features)
    return {
        "success": True,
        "analysis_mode": "mediapipe",
        "media_type": "images",
        "message": "Pose landmarks extracted from the uploaded image set.",
        "status_steps": ["Images decoded", "Pose landmarks detected", "Movement features calculated"],
        "images_received": len(uploads),
        "pose_output": {
            "landmarks_detected": True,
            "keypoints_supported": 33,
            "tracked_joints": ["Hip", "Knee", "Ankle"],
        },
        "gait_metrics": metrics,
        "quality": metrics.get("pose_quality", 0),
    }


def process_gait_video(video: Any, max_sampled_frames: int = 120) -> dict[str, Any]:
    """Sample a walking video and estimate basic pose-derived mobility features."""
    if video is None:
        return {"success": False, "message": "Upload a walking video."}

    name = getattr(video, "name", "walking_video.mp4")
    extension = _get_extension(name)
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return {"success": False, "message": f"Unsupported video format: .{extension or 'unknown'}."}

    payload = _uploaded_bytes(video)
    if not payload:
        return {"success": False, "message": "The uploaded video is empty."}

    capabilities = get_capabilities()
    if not capabilities["real_pose_pipeline_available"]:
        response = _demo_pose_response(payload, name, "video")
        response.update({"frames_sampled": 0, "duration_seconds": None})
        return response

    temp_path = ""
    capture = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as temp:
            temp.write(payload)
            temp_path = temp.name

        capture = cv2.VideoCapture(temp_path)  # type: ignore[union-attr]
        if not capture.isOpened():
            return {"success": False, "message": "The video could not be decoded."}

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)  # type: ignore[union-attr]
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)  # type: ignore[union-attr]
        if fps <= 0:
            fps = 25.0
        frame_step = max(1, total_frames // max_sampled_frames) if total_frames else 2

        features: list[dict[str, float]] = []
        sampled = 0
        frame_index = 0
        pose_api = mp.solutions.pose  # type: ignore[union-attr]
        with pose_api.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.50,
            min_tracking_confidence=0.50,
        ) as pose:
            while capture.isOpened() and sampled < max_sampled_frames:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame_index % frame_step != 0:
                    frame_index += 1
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # type: ignore[union-attr]
                result = pose.process(rgb)
                timestamp = frame_index / fps
                if result.pose_landmarks:
                    features.append(_frame_features(result.pose_landmarks.landmark, timestamp))
                sampled += 1
                frame_index += 1

        duration = total_frames / fps if total_frames else (features[-1]["timestamp"] if features else 0)

        # ---------- StrideX AI Metrics ----------
        metrics = _calculate_gait_metrics(features)

        cadence = metrics.get("cadence_estimate") or 90
        walking_speed = round(1.1, 2)          # demo estimate
        symmetry = metrics.get("step_symmetry", 80) 
        knee_angle = round(
            sum(f["left_knee_angle"] for f in features) / len(features), 1
        )
        hip_angle = round(120.0, 1)            # demo estimate
        step_variability = round(
            statistics.pstdev(f["left_ankle_y"] for f in features), 4
        )

        predicted_risk = predict_risk(
           cadence=cadence,
           walking_speed=walking_speed,
           symmetry=symmetry,
           knee_angle=knee_angle,
           hip_angle=hip_angle,
           step_variability=step_variability,
           pressure_imbalance=2.0,
           pain_score=2,
        )

        if len(features) < 5:
            return {
                "success": False,
                "message": (
                    "Too few full-body pose frames were detected. Record 10–20 seconds in good "
                    "lighting with the complete body visible and the camera kept still."
                ),
                "analysis_mode": "mediapipe",
                "frames_sampled": sampled,
                "frames_with_pose": len(features),
            }

        metrics = _calculate_gait_metrics(features)
        detection_rate = round(len(features) / max(sampled, 1) * 100)
        metrics["pose_detection_rate"] = detection_rate
        return {
            "success": True,
            "analysis_mode": "mediapipe",
            "media_type": "video",
            "message": "Pose landmarks and basic mobility features were extracted from sampled frames.",
            "status_steps": [
                "Video decoded",
                f"{sampled} frames sampled",
                f"Pose detected in {len(features)} frames",
                "Mobility features calculated",
            ],
            "frames_sampled": sampled,
            "duration_seconds": round(duration, 1),
            "pose_output": {
                "landmarks_detected": True,
                "keypoints_supported": 33,
                "tracked_joints": ["Hip", "Knee", "Ankle"],
            },
            "gait_metrics": metrics,
            "quality": metrics.get("pose_quality", 0),
            "cadence": cadence,
            "walking_speed": walking_speed,
            "symmetry": symmetry,
            "knee_angle": knee_angle,
            "hip_angle": hip_angle,
            "step_variability": step_variability,
            "predicted_risk": predicted_risk,
        }
    except Exception as exc:
        return {"success": False, "message": f"Video pose processing failed: {exc}", "analysis_mode": "error"}
    finally:
        if capture is not None:
            try:
                capture.release()
            except Exception:
                pass
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Backward-compatible demonstration helpers
# ---------------------------------------------------------------------------

def generate_simulated_gait_metrics(seed: int | None = None) -> dict[str, Any]:
    rng = random.Random(seed if seed is not None else 82026)
    symmetry = rng.randint(76, 86)
    regularity = rng.randint(70, 84)
    stability = rng.randint(72, 86)
    metrics = {
        "step_symmetry": symmetry,
        "knee_symmetry": max(60, symmetry - 4),
        "stride_regularity_score": regularity,
        "stride_consistency": _score_to_label(regularity),
        "trunk_stability_score": stability,
        "gait_stability": _stability_label(stability),
        "pose_quality": 92,
        "cadence_estimate": 98,
        "frames_with_pose": 0,
    }
    return {
        "success": True,
        "analysis_mode": "simulation",
        "gait_metrics": metrics,
        "summary": "Demonstration-only mobility metrics; no pose measurement was performed.",
    }


def get_gait_score(metrics: Mapping[str, Any] | None) -> dict[str, Any]:
    if not metrics:
        return {"gait_score": 0, "concern_score": 0, "severity": "Not assessed"}

    symmetry = _clamp(_safe_float(metrics.get("step_symmetry"), 75), 0, 100)
    regularity = _safe_float(metrics.get("stride_regularity_score"), -1)
    if regularity < 0:
        regularity = {"High": 90, "Moderate": 72, "Low": 50}.get(
            str(metrics.get("stride_consistency")), 72
        )
    stability = _safe_float(metrics.get("trunk_stability_score"), -1)
    if stability < 0:
        stability = {
            "Stable": 92,
            "Slight imbalance": 72,
            "Slight variation": 72,
            "Unstable": 48,
            "Review recommended": 48,
        }.get(str(metrics.get("gait_stability")), 72)

    gait_score = round(_clamp(0.45 * symmetry + 0.30 * regularity + 0.25 * stability, 0, 100))
    concern = 100 - gait_score
    if gait_score >= 85:
        severity = "Within expected demo range"
    elif gait_score >= 65:
        severity = "Mild movement variation"
    else:
        severity = "Movement variation requires review"
    return {"gait_score": gait_score, "concern_score": concern, "severity": severity}


def get_simulated_sensor_data(sensor_enabled: bool, seed: int | None = None) -> dict[str, Any]:
    if not sensor_enabled:
        return {
            "success": True,
            "sensor_enabled": False,
            "message": "Simulated wearable sensor is disabled.",
            "source": "manual",
        }
    rng = random.Random(seed if seed is not None else random.SystemRandom().randint(1, 10_000_000))
    return {
        "success": True,
        "sensor_enabled": True,
        "message": "Demonstration BLE insole stream active.",
        "sensor_status": "Demo stream active",
        "ble_connected": True,
        # Same simulated ranges used by the uploaded working prototype.
        "pressure": rng.randint(40, 95),
        "pain": rng.randint(0, 8),
        "source": "Simulated insole + IMU",
        "is_simulated": True,
    }


def run_full_stridex_analysis(
    manual_pressure: float | None = None,
    manual_pain: float | None = None,
    sensor_data: Mapping[str, Any] | None = None,
    gait_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the original StrideX pressure/pain threshold workflow.

    Behaviour retained from the user's earlier working prototype:
    1. Choose manual or simulated sensor values.
    2. Optionally adjust the values from gait indicators.
    3. Apply detect_risk() exactly:
       HIGH   when pressure >= 70 or pain >= 7
       MEDIUM when pressure >= 40 or pain >= 4
       LOW    otherwise

    The visual risk index is max(adjusted pressure, adjusted pain * 10). It is
    an interface indicator, not a disease probability or validated clinical score.
    """
    sensor_active = bool(
        sensor_data
        and sensor_data.get("success")
        and sensor_data.get("sensor_enabled")
    )

    if sensor_active:
        base_pressure = _clamp(_safe_float(sensor_data.get("pressure"), 30), 0, 100)
        base_pain = _clamp(_safe_float(sensor_data.get("pain"), 0), 0, 10)
        input_source = "simulated_sensor"
    else:
        base_pressure = _clamp(_safe_float(manual_pressure, 30), 0, 100)
        base_pain = _clamp(_safe_float(manual_pain, 0), 0, 10)
        input_source = "manual"

    adjusted_pressure = base_pressure
    adjusted_pain = base_pain
    gait_influence = False
    adjustment_notes: list[str] = []

    if gait_metrics:
        gait_influence = True
        symmetry = _safe_float(gait_metrics.get("step_symmetry"), 100)
        consistency = str(gait_metrics.get("stride_consistency", "High"))
        stability_label = str(gait_metrics.get("gait_stability", "Stable"))
        stability_score = _safe_float(gait_metrics.get("trunk_stability_score"), 100)

        if symmetry < 80:
            adjusted_pressure += 5
            adjustment_notes.append("step symmetry below 80 added 5 pressure points")

        if consistency == "Low":
            adjusted_pressure += 5
            adjustment_notes.append("low stride consistency added 5 pressure points")

        if stability_label in {"Slight imbalance", "Unstable", "Review recommended"} or stability_score < 75:
            adjusted_pain += 1
            adjustment_notes.append("gait instability added 1 pain point")

    adjusted_pressure = _clamp(adjusted_pressure, 0, 100)
    adjusted_pain = _clamp(adjusted_pain, 0, 10)

    priority, threshold_reason = detect_risk(adjusted_pressure, adjusted_pain)
    risk_index = round(max(adjusted_pressure, adjusted_pain * 10))

    reason = threshold_reason
    if adjustment_notes:
        reason += " Gait adjustment applied: " + "; ".join(adjustment_notes) + "."

    factors = [
        {
            "label": "Plantar-load index",
            "value": round(adjusted_pressure),
            "source": input_source,
        },
        {
            "label": "Self-reported pain",
            "value": round(adjusted_pain * 10),
            "source": "patient" if input_source == "manual" else "simulated_sensor",
        },
    ]
    if gait_metrics:
        factors.extend(
            [
                {
                    "label": "Left-right movement variation",
                    "value": round(100 - _clamp(_safe_float(gait_metrics.get("step_symmetry"), 100), 0, 100)),
                    "source": "pose",
                },
                {
                    "label": "Trunk-stability variation",
                    "value": round(100 - _clamp(_safe_float(gait_metrics.get("trunk_stability_score"), 100), 0, 100)),
                    "source": "pose",
                },
            ]
        )

    completeness = 100 if gait_metrics else (80 if sensor_active else 75)
    gait_score = get_gait_score(gait_metrics).get("gait_score") if gait_metrics else None

    return {
        "success": True,
        "input_source": input_source,
        "original_values": {
            "pressure": base_pressure,
            "pain": base_pain,
            "source": input_source,
        },
        "adjusted_values": {
            "pressure": adjusted_pressure,
            "pain": adjusted_pain,
        },
        "gait_influence_applied": gait_influence,
        "gait_adjustment_notes": adjustment_notes,
        "gait_summary": dict(gait_metrics or {}),
        "rule_engine": {
            "pressure_medium": PRESSURE_MEDIUM,
            "pressure_high": PRESSURE_HIGH,
            "pain_medium": PAIN_MEDIUM,
            "pain_high": PAIN_HIGH,
            "risk_index_formula": "max(adjusted_pressure, adjusted_pain * 10)",
        },
        "final_result": {
            "risk": priority,
            "priority": priority,
            "priority_label": _risk_label(priority),
            "concern_score": risk_index,
            "assessment_completeness": completeness,
            "reason": reason,
            "recommendation": get_recommendation(priority),
            "factors": factors,
            "gait_score": gait_score,
        },
        "disclaimer": DISCLAIMER,
    }


# Compatibility with the user's existing import spelling.
def run_full_strideX_analysis(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return run_full_stridex_analysis(*args, **kwargs)


# ---------------------------------------------------------------------------
# Record, report, and dashboard helpers
# ---------------------------------------------------------------------------

def create_assessment_record(
    patient_name: str,
    patient_id: str,
    age_band: str,
    analysis: Mapping[str, Any],
    pose_result: Mapping[str, Any] | None = None,
    notes: str = "",
    is_demo: bool = False,
) -> dict[str, Any]:
    final = analysis.get("final_result", {})
    original = analysis.get("original_values", {})
    adjusted = analysis.get("adjusted_values", original)
    pose_metrics = (pose_result or {}).get("gait_metrics", {}) if pose_result else {}
    now = datetime.now()
    return {
        "record_id": f"SX-{now.strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "patient_name": patient_name.strip() or "Unidentified participant",
        "patient_id": patient_id.strip() or "Not provided",
        "age_band": age_band,
        "timestamp_iso": now.isoformat(timespec="seconds"),
        "time": now.strftime("%d %b %Y, %H:%M"),
        "priority": final.get("priority", final.get("risk", "LOW")),
        "risk": final.get("priority", final.get("risk", "LOW")),
        "priority_label": final.get("priority_label", "Routine monitoring"),
        "concern_score": final.get("concern_score", 0),
        "assessment_completeness": final.get("assessment_completeness", 0),
        "pressure": round(_safe_float(original.get("pressure"), 0)),
        "pain": round(_safe_float(original.get("pain"), 0)),
        "adjusted_pressure": round(_safe_float(adjusted.get("pressure"), original.get("pressure", 0))),
        "adjusted_pain": round(_safe_float(adjusted.get("pain"), original.get("pain", 0))),
        "gait_influence_applied": bool(analysis.get("gait_influence_applied")),
        "input_source": analysis.get("input_source", "manual"),
        "reason": final.get("reason", ""),
        "recommendation": final.get("recommendation", ""),
        "factors": list(final.get("factors", [])),
        "gait_score": final.get("gait_score"),
        "step_symmetry": pose_metrics.get("step_symmetry"),
        "trunk_stability_score": pose_metrics.get("trunk_stability_score"),
        "cadence_estimate": pose_metrics.get("cadence_estimate"),
        "pose_quality": pose_metrics.get("pose_quality"),
        "pose_analysis_mode": (pose_result or {}).get("analysis_mode", "not_used"),
        "notes": notes.strip(),
        "is_demo": bool(is_demo),
    }


def get_dashboard_statistics(history: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    records = list(history or [])
    priorities = Counter(str(item.get("priority") or item.get("risk") or "LOW").upper() for item in records)
    scores = [_safe_float(item.get("concern_score"), 0) for item in records]
    pose_sessions = sum(1 for item in records if item.get("pose_analysis_mode") not in (None, "not_used"))
    today = datetime.now().date()
    today_count = sum(1 for item in records if (_parse_record_time(item) or datetime.min).date() == today)
    return {
        "total": len(records),
        "high": priorities["HIGH"],
        "medium": priorities["MEDIUM"],
        "low": priorities["LOW"],
        "average_concern": round(statistics.fmean(scores)) if scores else 0,
        "pose_sessions": pose_sessions,
        "today": today_count,
        "reports_generated": len(records),
    }


def get_dashboard_alerts(
    history: Sequence[Mapping[str, Any]] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    records = sorted(
        list(history or []),
        key=lambda row: _parse_record_time(row) or datetime.min,
        reverse=True,
    )
    alerts: list[dict[str, Any]] = []
    for row in records:
        priority = str(row.get("priority") or row.get("risk") or "LOW").upper()
        if priority not in {"HIGH", "MEDIUM"}:
            continue
        alerts.append(
            {
                "priority": priority,
                "patient": row.get("patient_name") or row.get("name") or "Participant",
                "record_id": row.get("record_id", ""),
                "message": row.get("priority_label") or _risk_label(priority),
                "time": row.get("time", ""),
            }
        )
        if len(alerts) >= limit:
            break
    return alerts


def get_recent_assessments(
    history: Sequence[Mapping[str, Any]] | None = None,
    limit: int = 6,
) -> list[dict[str, Any]]:
    records = sorted(
        list(history or []),
        key=lambda row: _parse_record_time(row) or datetime.min,
        reverse=True,
    )[:limit]
    return [
        {
            "Record": row.get("record_id", "—"),
            "Participant": row.get("patient_name") or row.get("name") or "Unidentified participant",
            "Priority": str(row.get("priority") or row.get("risk") or "LOW").upper(),
            "Concern score": row.get("concern_score", "—"),
            "Pose mode": row.get("pose_analysis_mode", "not_used"),
            "Time": row.get("time", "—"),
        }
        for row in records
    ]


def get_ai_insights(history: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    records = list(history or [])
    if not records:
        return {
            "average_pressure": 0,
            "average_pain": 0,
            "average_concern": 0,
            "average_pose_quality": None,
            "most_common_factor": "No assessments yet",
        }
    pressure = [_safe_float(row.get("pressure"), 0) for row in records]
    pain = [_safe_float(row.get("pain"), 0) for row in records]
    concern = [_safe_float(row.get("concern_score"), 0) for row in records]
    pose_quality = [
        _safe_float(row.get("pose_quality"), -1)
        for row in records
        if row.get("pose_quality") is not None
    ]
    factor_names = [
        factor.get("label", "")
        for row in records
        for factor in row.get("factors", [])
        if _safe_float(factor.get("value"), 0) >= 35
    ]
    return {
        "average_pressure": round(statistics.fmean(pressure)),
        "average_pain": round(statistics.fmean(pain), 1),
        "average_concern": round(statistics.fmean(concern)),
        "average_pose_quality": round(statistics.fmean(pose_quality)) if pose_quality else None,
        "most_common_factor": Counter(factor_names).most_common(1)[0][0] if factor_names else "No dominant factor",
    }


def get_device_status() -> dict[str, Any]:
    capabilities = get_capabilities()
    return {
        "pose_engine": "Available" if capabilities["real_pose_pipeline_available"] else "Demo fallback",
        "sensor": "Simulation available",
        "storage": "Session-local",
        "reporting": "Ready",
        "version": APP_VERSION,
    }


def get_weekly_trend(history: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    records = list(history or [])
    today = datetime.now().date()
    buckets: dict[Any, list[float]] = defaultdict(list)
    for row in records:
        timestamp = _parse_record_time(row)
        if timestamp:
            buckets[timestamp.date()].append(_safe_float(row.get("concern_score"), 0))

    trend = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        values = buckets.get(day, [])
        trend.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "average_concern": round(statistics.fmean(values), 1) if values else None,
                "count": len(values),
            }
        )
    return trend


def history_to_csv(history: Sequence[Mapping[str, Any]]) -> str:
    output = StringIO()
    fieldnames = [
        "record_id",
        "patient_name",
        "patient_id",
        "age_band",
        "time",
        "priority",
        "concern_score",
        "pressure",
        "pain",
        "adjusted_pressure",
        "adjusted_pain",
        "gait_influence_applied",
        "input_source",
        "pose_analysis_mode",
        "gait_score",
        "step_symmetry",
        "trunk_stability_score",
        "cadence_estimate",
        "reason",
        "recommendation",
        "notes",
        "is_demo",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in history:
        writer.writerow(dict(row))
    return output.getvalue()


def build_report_html(record: Mapping[str, Any]) -> str:
    priority = str(record.get("priority") or record.get("risk") or "LOW").upper()
    factors = record.get("factors", [])
    factor_rows = "".join(
        f"<tr><td>{escape(str(item.get('label', 'Factor')))}</td>"
        f"<td>{escape(str(item.get('value', '—')))} / 100</td>"
        f"<td>{escape(str(item.get('source', '—')))}</td></tr>"
        for item in factors
    ) or "<tr><td colspan='3'>No factor detail available.</td></tr>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>StrideX Assessment {escape(str(record.get('record_id', '')))}</title>
<style>
body{{font-family:Arial,sans-serif;color:#14213d;margin:36px;line-height:1.55}}
header{{border-bottom:3px solid #0b6e99;padding-bottom:14px;margin-bottom:24px}}
h1{{margin:0;color:#083b5c}} .sub{{color:#52677a}}
.badge{{display:inline-block;padding:6px 12px;border-radius:999px;background:#eaf4f8;font-weight:700}}
table{{border-collapse:collapse;width:100%;margin:16px 0}} th,td{{border:1px solid #cad6df;padding:9px;text-align:left}}
th{{background:#f2f7fa}} .notice{{background:#fff6dd;border-left:4px solid #c48600;padding:12px;margin-top:24px}}
@media print{{body{{margin:16mm}}}}
</style>
</head>
<body>
<header><h1>StrideX Mobility Screening Report</h1><div class="sub">Research prototype • {escape(APP_VERSION)}</div></header>
<p><span class="badge">{escape(priority)} — {escape(str(record.get('priority_label', _risk_label(priority))))}</span></p>
<table>
<tr><th>Record</th><td>{escape(str(record.get('record_id', '—')))}</td><th>Date</th><td>{escape(str(record.get('time', '—')))}</td></tr>
<tr><th>Participant</th><td>{escape(str(record.get('patient_name', '—')))}</td><th>Patient ID</th><td>{escape(str(record.get('patient_id', '—')))}</td></tr>
<tr><th>Age band</th><td>{escape(str(record.get('age_band', '—')))}</td><th>Risk index</th><td>{escape(str(record.get('concern_score', '—')))} / 100</td></tr>
<tr><th>Input pressure</th><td>{escape(str(record.get('pressure', '—')))} / 100</td><th>Input pain</th><td>{escape(str(record.get('pain', '—')))} / 10</td></tr>
<tr><th>Pressure used</th><td>{escape(str(record.get('adjusted_pressure', record.get('pressure', '—'))))} / 100</td><th>Pain used</th><td>{escape(str(record.get('adjusted_pain', record.get('pain', '—'))))} / 10</td></tr>
<tr><th>Pose mode</th><td>{escape(str(record.get('pose_analysis_mode', 'not_used')))}</td><th>Pose quality</th><td>{escape(str(record.get('pose_quality', '—')))} </td></tr>
</table>
<h2>Contributing factors</h2>
<table><tr><th>Factor</th><th>Index</th><th>Source</th></tr>{factor_rows}</table>
<h2>Screening explanation</h2><p>{escape(str(record.get('reason', '—')))}</p>
<h2>Suggested next step</h2><p>{escape(str(record.get('recommendation', '—')))}</p>
<h2>Notes</h2><p>{escape(str(record.get('notes') or 'No notes recorded.'))}</p>
<div class="notice"><strong>Important:</strong> {escape(DISCLAIMER)} The thresholds and scoring rules in this report are demonstration rules and have not been clinically validated.</div>
</body></html>"""


def make_demo_history() -> list[dict[str, Any]]:
    """Return six clearly labelled simulated records for dashboard demonstrations.

    The distribution intentionally mirrors the user's earlier working prototype:
    6 total assessments = 3 HIGH, 1 MEDIUM, and 2 LOW. Values are passed through
    the same original pressure/pain threshold engine used by live assessments.
    """
    now = datetime.now()
    templates = [
        # name, id, age, pressure, pain, days_ago, pose_mode, pose_quality
        ("Demo participant A", "DX-001", "60–69", 25, 2, 5, "mediapipe", 93),
        ("Demo participant B", "DX-002", "50–59", 80, 2, 4, "demo_fallback", None),
        ("Demo participant C", "DX-003", "70–79", 52, 7, 3, "mediapipe", 91),
        ("Demo participant D", "DX-004", "40–49", 52, 6, 2, "not_used", None),
        ("Demo participant E", "DX-005", "60–69", 15, 1, 1, "mediapipe", 95),
        ("Demo participant F", "DX-006", "70–79", 76, 5, 0, "demo_fallback", None),
    ]
    records: list[dict[str, Any]] = []
    for index, (name, patient_id, age, pressure, pain, days_ago, mode, pose_quality) in enumerate(templates):
        timestamp = now - timedelta(days=days_ago, hours=index)
        priority, reason = detect_risk(pressure, pain)
        concern = round(max(pressure, pain * 10))
        gait_score = 88 - index * 3 if mode != "not_used" else None
        record = {
            "record_id": f"DEMO-{index + 1:03d}",
            "patient_name": name,
            "patient_id": patient_id,
            "age_band": age,
            "timestamp_iso": timestamp.isoformat(timespec="seconds"),
            "time": timestamp.strftime("%d %b %Y, %H:%M"),
            "priority": priority,
            "risk": priority,
            "priority_label": _risk_label(priority),
            "concern_score": concern,
            "assessment_completeness": 90 if mode != "not_used" else 75,
            "pressure": pressure,
            "pain": pain,
            "adjusted_pressure": pressure,
            "adjusted_pain": pain,
            "gait_influence_applied": False,
            "input_source": "simulated_sensor",
            "reason": reason + " Simulated dashboard record.",
            "recommendation": get_recommendation(priority),
            "factors": [
                {"label": "Plantar-load index", "value": pressure, "source": "simulated_sensor"},
                {"label": "Self-reported pain", "value": pain * 10, "source": "simulated_sensor"},
            ],
            "gait_score": gait_score,
            "step_symmetry": gait_score,
            "trunk_stability_score": gait_score,
            "cadence_estimate": 92 + index if gait_score is not None else None,
            "pose_quality": pose_quality,
            "pose_analysis_mode": mode,
            "notes": "Simulated sample data only.",
            "is_demo": True,
        }
        records.append(record)
    return records


__all__ = [
    "APP_VERSION",
    "DISCLAIMER",
    "detect_risk",
    "get_recommendation",
    "get_capabilities",
    "process_gait_images",
    "process_gait_video",
    "generate_simulated_gait_metrics",
    "get_gait_score",
    "get_simulated_sensor_data",
    "run_full_stridex_analysis",
    "run_full_strideX_analysis",
    "create_assessment_record",
    "get_dashboard_statistics",
    "get_dashboard_alerts",
    "get_recent_assessments",
    "get_ai_insights",
    "get_device_status",
    "get_weekly_trend",
    "history_to_csv",
    "build_report_html",
    "make_demo_history",
]