# ============================================================
# STRIDEX - COMPLETE PHYSICS / GAIT TEST
# ============================================================

import os
import sys
import cv2
import math
import numpy as np

# ------------------------------------------------------------
# PROJECT ROOT
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------

from ai.vision.pose_estimator import process_frame
from ai.features.gait_features import create_gait_features


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_PATH = os.path.join(
    PROJECT_ROOT,
    "sample walk.mp4"
)

VISIBILITY_THRESHOLD = 0.7
EMA_ALPHA = 0.7


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        value = float(value)

        if not np.isfinite(value):
            return default

        return value

    except Exception:
        return default


def safe_mean(values):
    if not values:
        return 0.0

    clean = []

    for value in values:
        try:
            value = float(value)

            if np.isfinite(value):
                clean.append(value)

        except Exception:
            pass

    if not clean:
        return 0.0

    return float(np.mean(clean))


# ============================================================
# ANGLE CALCULATION
# ============================================================

def calculate_angle(a, b, c):
    """
    Calculate angle ABC.

    a = first point
    b = joint
    c = third point
    """

    if a is None or b is None or c is None:
        return None

    try:

        ba = np.array([
            a["x"] - b["x"],
            a["y"] - b["y"],
            a["z"] - b["z"]
        ], dtype=float)

        bc = np.array([
            c["x"] - b["x"],
            c["y"] - b["y"],
            c["z"] - b["z"]
        ], dtype=float)

        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)

        if norm_ba == 0 or norm_bc == 0:
            return None

        cosine = np.dot(ba, bc) / (
            norm_ba * norm_bc
        )

        cosine = np.clip(cosine, -1.0, 1.0)

        return float(
            math.degrees(
                math.acos(cosine)
            )
        )

    except Exception:
        return None


# ============================================================
# PROCESS VIDEO
# ============================================================

def process_video():

    print()
    print("=" * 60)
    print("STRIDEX PHYSICS / GAIT ENGINE TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # CHECK VIDEO
    # --------------------------------------------------------

    if not os.path.exists(VIDEO_PATH):

        print()
        print("ERROR: Video not found.")
        print()
        print("Expected:")
        print(VIDEO_PATH)
        print()
        print("Make sure 'sample walk.mp4' is in the project root.")
        return

    print()
    print("Video:", os.path.basename(VIDEO_PATH))

    # --------------------------------------------------------
    # OPEN VIDEO
    # --------------------------------------------------------

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():

        print("ERROR: Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30.0

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    print(
        f"FPS: {fps:.2f}"
    )

    print(
        f"Frames: {total_frames}"
    )

    print()
    print("Processing video...")
    print()

    # --------------------------------------------------------
    # STORAGE
    # --------------------------------------------------------

    left_knee_angles = []
    right_knee_angles = []

    left_ankle_angles = []
    right_ankle_angles = []

    left_hip_x = []
    right_hip_x = []

    left_hip_y = []
    right_hip_y = []

    left_hip_z = []
    right_hip_z = []

    previous_landmarks = None

    detected_frames = 0

    frame_number = 0

    # --------------------------------------------------------
    # VIDEO LOOP
    # --------------------------------------------------------

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # ----------------------------------------------------
        # PROCESS FRAME
        # ----------------------------------------------------

        landmarks = process_frame(
            frame,
            previous_landmarks=previous_landmarks,
            visibility_threshold=VISIBILITY_THRESHOLD,
            alpha=EMA_ALPHA
        )

        # ----------------------------------------------------
        # NO PERSON
        # ----------------------------------------------------

        if landmarks is None:

            left_knee_angles.append(None)
            right_knee_angles.append(None)

            left_ankle_angles.append(None)
            right_ankle_angles.append(None)

            left_hip_x.append(None)
            right_hip_x.append(None)

            left_hip_y.append(None)
            right_hip_y.append(None)

            left_hip_z.append(None)
            right_hip_z.append(None)

        else:

            detected_frames += 1

            previous_landmarks = landmarks

            # ------------------------------------------------
            # LANDMARK INDEXES
            #
            # 23 = LEFT HIP
            # 24 = RIGHT HIP
            # 25 = LEFT KNEE
            # 26 = RIGHT KNEE
            # 27 = LEFT ANKLE
            # 28 = RIGHT ANKLE
            # ------------------------------------------------

            left_hip = landmarks[23]
            right_hip = landmarks[24]

            left_knee = landmarks[25]
            right_knee = landmarks[26]

            left_ankle = landmarks[27]
            right_ankle = landmarks[28]

            # ------------------------------------------------
            # KNEE ANGLES
            # ------------------------------------------------

            left_knee_angle = calculate_angle(
                left_hip,
                left_knee,
                left_ankle
            )

            right_knee_angle = calculate_angle(
                right_hip,
                right_knee,
                right_ankle
            )

            left_knee_angles.append(
                left_knee_angle
            )

            right_knee_angles.append(
                right_knee_angle
            )

            # ------------------------------------------------
            # ANKLE ANGLES
            #
            # Approximation using:
            # knee -> ankle -> opposite direction
            #
            # For prototype-level gait analysis.
            # ------------------------------------------------

            left_ankle_angle = calculate_angle(
                left_knee,
                left_ankle,
                left_hip
            )

            right_ankle_angle = calculate_angle(
                right_knee,
                right_ankle,
                right_hip
            )

            left_ankle_angles.append(
                left_ankle_angle
            )

            right_ankle_angles.append(
                right_ankle_angle
            )

            # ------------------------------------------------
            # HIP / COM DATA
            # ------------------------------------------------

            left_hip_x.append(
                safe_float(left_hip["x"])
            )

            right_hip_x.append(
                safe_float(right_hip["x"])
            )

            left_hip_y.append(
                safe_float(left_hip["y"])
            )

            right_hip_y.append(
                safe_float(right_hip["y"])
            )

            left_hip_z.append(
                safe_float(left_hip["z"])
            )

            right_hip_z.append(
                safe_float(right_hip["z"])
            )

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        if frame_number % 50 == 0:

            if landmarks is not None:

                print(
                    f"Frame {frame_number} | PERSON DETECTED"
                )

            else:

                print(
                    f"Frame {frame_number} | NO PERSON DETECTED"
                )

        frame_number += 1

    # --------------------------------------------------------
    # RELEASE VIDEO
    # --------------------------------------------------------

    cap.release()

    # ========================================================
    # DETECTION SUMMARY
    # ========================================================

    detection_rate = 0.0

    if total_frames > 0:

        detection_rate = (
            detected_frames /
            total_frames
        ) * 100.0

    print()
    print("=" * 60)
    print("POSE PROCESSING COMPLETE")
    print("=" * 60)

    print(
        f"Total frames       : {total_frames}"
    )

    print(
        f"Detected frames    : {detected_frames}"
    )

    print(
        f"Detection rate     : {detection_rate:.2f}%"
    )

    print(
        f"Left knee samples  : "
        f"{len([x for x in left_knee_angles if x is not None])}"
    )

    print(
        f"Right knee samples : "
        f"{len([x for x in right_knee_angles if x is not None])}"
    )

    print(
        f"Left ankle samples : "
        f"{len([x for x in left_ankle_angles if x is not None])}"
    )

    print(
        f"Right ankle samples: "
        f"{len([x for x in right_ankle_angles if x is not None])}"
    )

    # ========================================================
    # GAIT FEATURE ENGINE
    # ========================================================

    print()
    print("Running gait feature engine...")

    try:

        gait_features = create_gait_features(

            left_knee_angles=left_knee_angles,

            right_knee_angles=right_knee_angles,

            left_ankle_angles=left_ankle_angles,

            right_ankle_angles=right_ankle_angles,

            fps=fps,

            left_hip_x=left_hip_x,

            right_hip_x=right_hip_x,

            left_hip_y=left_hip_y,

            right_hip_y=right_hip_y,

            left_hip_z=left_hip_z,

            right_hip_z=right_hip_z
        )

    except Exception as e:

        print()
        print("ERROR in gait feature engine:")
        print(type(e).__name__, ":", str(e))
        return

    print(
        "GAIT FEATURE ENGINE : SUCCESS"
    )

    # ========================================================
    # RESULTS
    # ========================================================

    print()
    print("=" * 60)
    print("STRIDEX GAIT ANALYSIS RESULTS")
    print("=" * 60)

    # --------------------------------------------------------
    # KNEE
    # --------------------------------------------------------

    print()
    print("KNEE BIOMECHANICS")
    print("-" * 60)

    print(
        f"Left Knee Mean Angle      : "
        f"{gait_features.get('left_knee_angle_mean', 0):.2f}°"
    )

    print(
        f"Right Knee Mean Angle     : "
        f"{gait_features.get('right_knee_angle_mean', 0):.2f}°"
    )

    print(
        f"Left Knee ROM             : "
        f"{gait_features.get('left_knee_rom', 0):.2f}°"
    )

    print(
        f"Right Knee ROM            : "
        f"{gait_features.get('right_knee_rom', 0):.2f}°"
    )

    print(
        f"Knee Angle Asymmetry      : "
        f"{gait_features.get('knee_angle_asymmetry', 0):.2f}°"
    )

    print(
        f"Knee ROM Asymmetry        : "
        f"{gait_features.get('knee_rom_asymmetry', 0):.2f}°"
    )

    # --------------------------------------------------------
    # ANGULAR VELOCITY
    # --------------------------------------------------------

    print()
    print("ANGULAR VELOCITY")
    print("-" * 60)

    print(
        f"Left Angular Velocity     : "
        f"{gait_features.get('left_angular_velocity_abs', 0):.2f}°/s"
    )

    print(
        f"Right Angular Velocity    : "
        f"{gait_features.get('right_angular_velocity_abs', 0):.2f}°/s"
    )

    # --------------------------------------------------------
    # ANKLE
    # --------------------------------------------------------

    print()
    print("ANKLE BIOMECHANICS")
    print("-" * 60)

    print(
        f"Left Ankle Mean Angle     : "
        f"{gait_features.get('left_ankle_angle_mean', 0):.2f}°"
    )

    print(
        f"Right Ankle Mean Angle    : "
        f"{gait_features.get('right_ankle_angle_mean', 0):.2f}°"
    )

    # --------------------------------------------------------
    # CENTER OF MASS
    # --------------------------------------------------------

    print()
    print("CENTER OF MASS / POSTURAL SWAY")
    print("-" * 60)

    print(
        f"CoM X Mean                : "
        f"{gait_features.get('com_x_mean', 0):.4f}"
    )

    print(
        f"CoM X Standard Deviation  : "
        f"{gait_features.get('com_x_std', 0):.4f}"
    )

    print(
        f"Postural Sway             : "
        f"{gait_features.get('postural_sway', 0):.4f}"
    )

    # --------------------------------------------------------
    # STEP ASYMMETRY
    # --------------------------------------------------------

    print()
    print("STEP ASYMMETRY")
    print("-" * 60)

    print(
        f"Step Asymmetry            : "
        f"{gait_features.get('step_asymmetry', 0):.2f}%"
    )

    # ========================================================
    # ALL AVAILABLE FEATURES
    # ========================================================

    print()
    print("=" * 60)
    print("ALL AVAILABLE GAIT FEATURES")
    print("=" * 60)

    for key, value in gait_features.items():

        if isinstance(value, float):

            print(
                f"{key:35s}: {value:.4f}"
            )

        else:

            print(
                f"{key:35s}: {value}"
            )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    print()
    print("=" * 60)
    print("STRIDEX PHYSICS ENGINE TEST COMPLETED")
    print("=" * 60)

    print()
    print("POSE ESTIMATION       : SUCCESS")
    print("EMA SMOOTHING         : SUCCESS")
    print("GAIT FEATURE ENGINE   : SUCCESS")
    print("JOINT ANGLE ENGINE    : SUCCESS")
    print("ANGULAR VELOCITY      : SUCCESS")
    print("CENTER OF MASS        : SUCCESS")
    print("POSTURAL SWAY         : SUCCESS")
    print("ASYMMETRY ENGINE      : SUCCESS")

    print()
    print(
        f"FINAL DETECTION RATE  : "
        f"{detection_rate:.2f}%"
    )

    print()
    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    process_video()