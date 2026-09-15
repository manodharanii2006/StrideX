import math
import numpy as np


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_mean(values):
    values = [
        float(v)
        for v in values
        if v is not None and np.isfinite(v)
    ]

    if not values:
        return 0.0

    return float(np.mean(values))


def safe_std(values):
    values = [
        float(v)
        for v in values
        if v is not None and np.isfinite(v)
    ]

    if len(values) < 2:
        return 0.0

    return float(np.std(values))


# ============================================================
# DISTANCE
# ============================================================

def calculate_distance(p1, p2):

    if p1 is None or p2 is None:
        return None

    return math.sqrt(
        (p1["x"] - p2["x"]) ** 2 +
        (p1["y"] - p2["y"]) ** 2 +
        (p1["z"] - p2["z"]) ** 2
    )


# ============================================================
# ANGLE
# ============================================================

def calculate_angle(a, b, c):

    if a is None or b is None or c is None:
        return None

    v1 = np.array([
        a["x"] - b["x"],
        a["y"] - b["y"],
        a["z"] - b["z"]
    ], dtype=float)

    v2 = np.array([
        c["x"] - b["x"],
        c["y"] - b["y"],
        c["z"] - b["z"]
    ], dtype=float)

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return None

    cosine = np.dot(v1, v2) / (norm1 * norm2)

    cosine = np.clip(cosine, -1.0, 1.0)

    return float(
        math.degrees(
            math.acos(cosine)
        )
    )


# ============================================================
# JOINT ANGLES FROM LANDMARKS
# ============================================================

def calculate_joint_angles(landmarks):

    if landmarks is None or len(landmarks) < 33:
        return {
            "left_knee_angle": None,
            "right_knee_angle": None
        }

    left_angle = calculate_angle(
        landmarks[23],
        landmarks[25],
        landmarks[27]
    )

    right_angle = calculate_angle(
        landmarks[24],
        landmarks[26],
        landmarks[28]
    )

    return {
        "left_knee_angle": left_angle,
        "right_knee_angle": right_angle
    }


# ============================================================
# ANGULAR VELOCITY
#
# ω(t) = [θ(t) - θ(t-1)] / Δt
# Δt = 1 / FPS
# ============================================================

def calculate_angular_velocity(angles, fps):

    if angles is None:
        return {
            "left_angular_velocity": 0.0,
            "right_angular_velocity": 0.0
        }

    if fps <= 0:
        fps = 30.0

    dt = 1.0 / fps

    left_velocity = []
    right_velocity = []

    left = angles.get(
        "left_knee_angles",
        []
    )

    right = angles.get(
        "right_knee_angles",
        []
    )

    for i in range(1, len(left)):

        if (
            left[i] is not None
            and left[i - 1] is not None
        ):

            left_velocity.append(
                (left[i] - left[i - 1]) / dt
            )

    for i in range(1, len(right)):

        if (
            right[i] is not None
            and right[i - 1] is not None
        ):

            right_velocity.append(
                (right[i] - right[i - 1]) / dt
            )

    return {
        "left_angular_velocity":
            safe_mean(left_velocity),

        "right_angular_velocity":
            safe_mean(right_velocity)
    }


# ============================================================
# CENTER OF MASS
#
# CoM = (Left Hip + Right Hip) / 2
# ============================================================

def calculate_com_from_hips(
    left_hip_x,
    left_hip_y,
    left_hip_z,
    right_hip_x,
    right_hip_y,
    right_hip_z
):

    return {
        "x": (
            left_hip_x +
            right_hip_x
        ) / 2.0,

        "y": (
            left_hip_y +
            right_hip_y
        ) / 2.0,

        "z": (
            left_hip_z +
            right_hip_z
        ) / 2.0
    }


# ============================================================
# POSTURAL SWAY
#
# σCoM = standard deviation of CoM X
# ============================================================

def calculate_postural_sway(com_x):

    if com_x is None:
        return 0.0

    return safe_std(com_x)


# ============================================================
# STEP ASYMMETRY
#
# A = |Tleft - Tright| / Ttotal × 100
# ============================================================

def calculate_step_asymmetry(
    left_step_time,
    right_step_time
):

    if (
        left_step_time is None
        or right_step_time is None
    ):
        return 0.0

    total = (
        left_step_time +
        right_step_time
    )

    if total <= 0:
        return 0.0

    return float(
        abs(
            left_step_time -
            right_step_time
        ) / total * 100.0
    )


# ============================================================
# CADENCE
#
# Estimates cadence from knee-angle periodicity.
#
# A complete gait cycle of one leg contains approximately
# two steps (left + right).
#
# cadence = 120 * FPS / stride_period_frames
# ============================================================

def calculate_cadence(
    left_knee_angles,
    right_knee_angles,
    fps
):

    if fps <= 0:
        fps = 30.0

    # --------------------------------------------------------
    # Clean signals
    # --------------------------------------------------------

    left = np.array(
        [
            float(x)
            for x in left_knee_angles
            if x is not None
            and np.isfinite(x)
        ],
        dtype=float
    )

    right = np.array(
        [
            float(x)
            for x in right_knee_angles
            if x is not None
            and np.isfinite(x)
        ],
        dtype=float
    )

    # --------------------------------------------------------
    # Select usable signal
    # --------------------------------------------------------

    if len(left) >= 30:
        signal = left

    elif len(right) >= 30:
        signal = right

    else:
        return 0.0

    if len(signal) < 30:
        return 0.0

    # --------------------------------------------------------
    # Remove mean
    # --------------------------------------------------------

    signal = signal - np.mean(signal)

    # --------------------------------------------------------
    # Remove linear trend
    # --------------------------------------------------------

    x = np.arange(len(signal), dtype=float)

    try:
        trend = np.polyfit(
            x,
            signal,
            1
        )

        signal = (
            signal -
            np.polyval(trend, x)
        )

    except Exception:
        pass

    # --------------------------------------------------------
    # Prevent zero signal
    # --------------------------------------------------------

    if np.std(signal) < 1e-6:
        return 0.0

    # --------------------------------------------------------
    # Autocorrelation
    # --------------------------------------------------------

    autocorr = np.correlate(
        signal,
        signal,
        mode="full"
    )

    autocorr = autocorr[
        len(signal) - 1:
    ]

    if autocorr[0] <= 0:
        return 0.0

    autocorr = (
        autocorr /
        autocorr[0]
    )

    # --------------------------------------------------------
    # Physiological search range
    #
    # Assume cadence approximately:
    #
    # 30 to 180 steps/min
    #
    # Convert this into stride-frame range.
    # One stride ≈ 2 steps.
    # --------------------------------------------------------

    min_cadence = 30.0
    max_cadence = 180.0

    min_lag = int(
        (120.0 * fps) /
        max_cadence
    )

    max_lag = int(
        (120.0 * fps) /
        min_cadence
    )

    min_lag = max(
        2,
        min_lag
    )

    max_lag = min(
        len(autocorr) - 1,
        max_lag
    )

    if max_lag <= min_lag:
        return 0.0

    search = autocorr[
        min_lag:max_lag + 1
    ]

    if len(search) == 0:
        return 0.0

    # --------------------------------------------------------
    # Find dominant gait-cycle lag
    # --------------------------------------------------------

    best_index = int(
        np.argmax(search)
    )

    best_lag = (
        min_lag +
        best_index
    )

    # --------------------------------------------------------
    # Convert stride period to cadence
    #
    # stride period = best_lag / FPS
    #
    # cadence = 2 steps / stride period × 60
    #
    # = 120 × FPS / best_lag
    # --------------------------------------------------------

    cadence = (
        120.0 *
        float(fps) /
        float(best_lag)
    )

    # --------------------------------------------------------
    # Safety bounds
    # --------------------------------------------------------

    cadence = float(
        np.clip(
            cadence,
            30.0,
            180.0
        )
    )

    return cadence


# ============================================================
# MAIN GAIT FEATURE ENGINE
# ============================================================

def create_gait_features(
    left_knee_angles=None,
    right_knee_angles=None,
    left_ankle_angles=None,
    right_ankle_angles=None,
    fps=30.0,
    left_hip_x=None,
    right_hip_x=None,
    left_hip_y=None,
    right_hip_y=None,
    left_hip_z=None,
    right_hip_z=None,
    left_step_time=None,
    right_step_time=None,
    **kwargs
):

    # --------------------------------------------------------
    # NORMALIZE INPUT ARRAYS
    # --------------------------------------------------------

    if left_knee_angles is None:
        left_knee_angles = []

    if right_knee_angles is None:
        right_knee_angles = []

    if left_ankle_angles is None:
        left_ankle_angles = []

    if right_ankle_angles is None:
        right_ankle_angles = []

    # --------------------------------------------------------
    # CLEAN VALUES
    # --------------------------------------------------------

    left_knee_clean = [
        float(x)
        for x in left_knee_angles
        if x is not None
        and np.isfinite(x)
    ]

    right_knee_clean = [
        float(x)
        for x in right_knee_angles
        if x is not None
        and np.isfinite(x)
    ]

    left_ankle_clean = [
        float(x)
        for x in left_ankle_angles
        if x is not None
        and np.isfinite(x)
    ]

    right_ankle_clean = [
        float(x)
        for x in right_ankle_angles
        if x is not None
        and np.isfinite(x)
    ]

    # --------------------------------------------------------
    # KNEE ANGLE STATISTICS
    # --------------------------------------------------------

    left_knee_mean = safe_mean(
        left_knee_clean
    )

    right_knee_mean = safe_mean(
        right_knee_clean
    )

    left_knee_min = (
        float(min(left_knee_clean))
        if left_knee_clean
        else 0.0
    )

    right_knee_min = (
        float(min(right_knee_clean))
        if right_knee_clean
        else 0.0
    )

    left_knee_max = (
        float(max(left_knee_clean))
        if left_knee_clean
        else 0.0
    )

    right_knee_max = (
        float(max(right_knee_clean))
        if right_knee_clean
        else 0.0
    )

    # --------------------------------------------------------
    # KNEE RANGE OF MOTION
    # --------------------------------------------------------

    left_knee_rom = (
        left_knee_max -
        left_knee_min
    )

    right_knee_rom = (
        right_knee_max -
        right_knee_min
    )

    # --------------------------------------------------------
    # ANGULAR VELOCITY
    #
    # ω(t) = [θ(t)-θ(t-1)] / Δt
    # --------------------------------------------------------

    if fps <= 0:
        fps = 30.0

    dt = 1.0 / fps

    left_velocity = []

    for i in range(
        1,
        len(left_knee_clean)
    ):

        left_velocity.append(
            (
                left_knee_clean[i]
                -
                left_knee_clean[i - 1]
            ) / dt
        )

    right_velocity = []

    for i in range(
        1,
        len(right_knee_clean)
    ):

        right_velocity.append(
            (
                right_knee_clean[i]
                -
                right_knee_clean[i - 1]
            ) / dt
        )

    left_angular_velocity = safe_mean(
        left_velocity
    )

    right_angular_velocity = safe_mean(
        right_velocity
    )

    # --------------------------------------------------------
    # ANGULAR VELOCITY MAGNITUDE
    # --------------------------------------------------------

    left_angular_velocity_abs = safe_mean(
        [
            abs(x)
            for x in left_velocity
        ]
    )

    right_angular_velocity_abs = safe_mean(
        [
            abs(x)
            for x in right_velocity
        ]
    )

    # --------------------------------------------------------
    # CENTER OF MASS
    #
    # CoM = (Left Hip + Right Hip) / 2
    # --------------------------------------------------------

    com_x = []

    if (
        left_hip_x is not None
        and right_hip_x is not None
    ):

        count = min(
            len(left_hip_x),
            len(right_hip_x)
        )

        for i in range(count):

            if (
                left_hip_x[i] is not None
                and right_hip_x[i] is not None
            ):

                com_x.append(
                    (
                        left_hip_x[i]
                        +
                        right_hip_x[i]
                    ) / 2.0
                )

    # --------------------------------------------------------
    # POSTURAL SWAY
    # --------------------------------------------------------

    postural_sway = calculate_postural_sway(
        com_x
    )

    # --------------------------------------------------------
    # STEP ASYMMETRY
    # --------------------------------------------------------

    step_asymmetry = calculate_step_asymmetry(
        left_step_time,
        right_step_time
    )

    # --------------------------------------------------------
    # KNEE ASYMMETRY
    # --------------------------------------------------------

    knee_angle_asymmetry = abs(
        left_knee_mean -
        right_knee_mean
    )

    knee_rom_asymmetry = abs(
        left_knee_rom -
        right_knee_rom
    )

    # --------------------------------------------------------
    # CADENCE
    # --------------------------------------------------------

    cadence = calculate_cadence(
        left_knee_angles,
        right_knee_angles,
        fps
    )

    # --------------------------------------------------------
    # TOTAL DURATION
    # --------------------------------------------------------

    frame_count = max(
        len(left_knee_angles),
        len(right_knee_angles),
        len(left_ankle_angles),
        len(right_ankle_angles)
    )

    duration_seconds = (
        frame_count / float(fps)
        if fps > 0
        else 0.0
    )

    # --------------------------------------------------------
    # FINAL FEATURE DICTIONARY
    # --------------------------------------------------------

    features = {

        # ----------------------------------------------------
        # KNEE ANGLES
        # ----------------------------------------------------

        "left_knee_angle_mean":
            left_knee_mean,

        "right_knee_angle_mean":
            right_knee_mean,

        "left_knee_angle_min":
            left_knee_min,

        "right_knee_angle_min":
            right_knee_min,

        "left_knee_angle_max":
            left_knee_max,

        "right_knee_angle_max":
            right_knee_max,

        # ----------------------------------------------------
        # KNEE ROM
        # ----------------------------------------------------

        "left_knee_rom":
            left_knee_rom,

        "right_knee_rom":
            right_knee_rom,

        # ----------------------------------------------------
        # ANGULAR VELOCITY
        # ----------------------------------------------------

        "left_angular_velocity":
            left_angular_velocity,

        "right_angular_velocity":
            right_angular_velocity,

        "left_angular_velocity_abs":
            left_angular_velocity_abs,

        "right_angular_velocity_abs":
            right_angular_velocity_abs,

        # ----------------------------------------------------
        # ANKLE
        # ----------------------------------------------------

        "left_ankle_angle_mean":
            safe_mean(left_ankle_clean),

        "right_ankle_angle_mean":
            safe_mean(right_ankle_clean),

        # ----------------------------------------------------
        # CENTER OF MASS
        # ----------------------------------------------------

        "com_x_mean":
            safe_mean(com_x),

        "com_x_std":
            postural_sway,

        # ----------------------------------------------------
        # POSTURAL SWAY
        # ----------------------------------------------------

        "postural_sway":
            postural_sway,

        # ----------------------------------------------------
        # GAIT
        # ----------------------------------------------------

        "cadence":
            cadence,

        "step_asymmetry":
            step_asymmetry,

        # ----------------------------------------------------
        # ASYMMETRY
        # ----------------------------------------------------

        "knee_angle_asymmetry":
            knee_angle_asymmetry,

        "knee_rom_asymmetry":
            knee_rom_asymmetry,

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        "fps":
            float(fps),

        "frame_count":
            frame_count,

        "duration_seconds":
            duration_seconds,

        "left_knee_samples":
            len(left_knee_clean),

        "right_knee_samples":
            len(right_knee_clean),

        "left_ankle_samples":
            len(left_ankle_clean),

        "right_ankle_samples":
            len(right_ankle_clean)
    }

    return features


# ============================================================
# PRINT FEATURES
# ============================================================

def print_gait_features(features):

    if features is None:
        print("No gait features available.")
        return

    print()
    print("=" * 60)
    print("STRIDEX GAIT FEATURES")
    print("=" * 60)

    print(
        f"Left Knee Mean Angle      : "
        f"{features['left_knee_angle_mean']:.2f}°"
    )

    print(
        f"Right Knee Mean Angle     : "
        f"{features['right_knee_angle_mean']:.2f}°"
    )

    print(
        f"Left Knee ROM             : "
        f"{features['left_knee_rom']:.2f}°"
    )

    print(
        f"Right Knee ROM            : "
        f"{features['right_knee_rom']:.2f}°"
    )

    print(
        f"Left Angular Velocity     : "
        f"{features['left_angular_velocity_abs']:.2f}°/s"
    )

    print(
        f"Right Angular Velocity    : "
        f"{features['right_angular_velocity_abs']:.2f}°/s"
    )

    print(
        f"Left Ankle Mean Angle     : "
        f"{features['left_ankle_angle_mean']:.2f}°"
    )

    print(
        f"Right Ankle Mean Angle    : "
        f"{features['right_ankle_angle_mean']:.2f}°"
    )

    print(
        f"Cadence                   : "
        f"{features['cadence']:.2f} steps/min"
    )

    print(
        f"CoM X Mean                : "
        f"{features['com_x_mean']:.4f}"
    )

    print(
        f"Postural Sway             : "
        f"{features['postural_sway']:.4f}"
    )

    print(
        f"Step Asymmetry            : "
        f"{features['step_asymmetry']:.2f}%"
    )

    print(
        f"Knee Angle Asymmetry      : "
        f"{features['knee_angle_asymmetry']:.2f}°"
    )

    print(
        f"Knee ROM Asymmetry        : "
        f"{features['knee_rom_asymmetry']:.2f}°"
    )

    print(
        f"Duration                  : "
        f"{features['duration_seconds']:.2f} sec"
    )

    print("=" * 60)


# ============================================================
# COMPATIBILITY EXPORTS
# ============================================================

def calculate_walking_speed(cadence, step_length=0.65):
    """Estimate walking speed (m/s) from cadence and step length."""
    return round((float(cadence) * float(step_length)) / 60.0, 2) if cadence else 0.0


def calculate_symmetry(left_val, right_val):
    """Calculate percentage symmetry between left and right values."""
    if left_val is None or right_val is None:
        return 100.0
    denom = max(abs(left_val), abs(right_val))
    return round(100.0 - (abs(left_val - right_val) / denom * 100.0), 1) if denom > 0 else 100.0


def calculate_knee_angle(hip, knee, ankle):
    """Calculate knee joint angle."""
    return calculate_angle(hip, knee, ankle)


def calculate_hip_angle(shoulder, hip, knee):
    """Calculate hip joint angle."""
    return calculate_angle(shoulder, hip, knee)


def calculate_step_variability(values):
    """Calculate standard deviation of step parameters."""
    return safe_std(values)