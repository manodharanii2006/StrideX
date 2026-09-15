# ============================================================
# STRIDEX - POSE ESTIMATOR
# MediaPipe Pose + Visibility Filtering + EMA Smoothing
# ============================================================

import cv2
import mediapipe as mp
import math


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

mp_pose = mp.solutions.pose


# ============================================================
# POSE ESTIMATOR CLASS
# ============================================================

class PoseEstimator:

    def __init__(
        self,
        model_complexity=2,
        visibility_threshold=0.5,
        smoothing_alpha=0.7,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ):

        self.visibility_threshold = visibility_threshold
        self.smoothing_alpha = smoothing_alpha

        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        self.previous_landmarks = None


    # ========================================================
    # EXTRACT LANDMARKS
    # ========================================================

    def extract_landmarks(self, frame):

        if frame is None:
            return None

        # OpenCV BGR -> MediaPipe RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = self.pose.process(rgb_frame)

        if not results.pose_landmarks:
            return None

        # ----------------------------------------------------
        # Prefer WORLD landmarks
        # ----------------------------------------------------

        if results.pose_world_landmarks:

            landmarks = []

            for landmark in results.pose_world_landmarks.landmark:

                landmarks.append({
                    "x": float(landmark.x),
                    "y": float(landmark.y),
                    "z": float(landmark.z),
                    "visibility": float(landmark.visibility)
                })

            return landmarks

        return None


    # ========================================================
    # VISIBILITY FILTER
    # ========================================================

    def filter_landmarks(
        self,
        landmarks,
        threshold=None
    ):

        if landmarks is None:
            return None

        if threshold is None:
            threshold = self.visibility_threshold

        filtered = []

        for landmark in landmarks:

            if landmark is None:
                filtered.append(None)

            elif landmark["visibility"] >= threshold:
                filtered.append(landmark)

            else:
                filtered.append(None)

        return filtered


    # ========================================================
    # EMA SMOOTHING
    # ========================================================

    @staticmethod
    def ema_smooth(
        current,
        previous,
        alpha=0.7
    ):

        # Current landmark unavailable
        if current is None:

            return previous

        # First valid frame
        if previous is None:

            return current

        return {
            "x": (
                alpha * current["x"]
                +
                (1 - alpha) * previous["x"]
            ),

            "y": (
                alpha * current["y"]
                +
                (1 - alpha) * previous["y"]
            ),

            "z": (
                alpha * current["z"]
                +
                (1 - alpha) * previous["z"]
            ),

            "visibility": current["visibility"]
        }


    # ========================================================
    # SMOOTH ALL LANDMARKS
    # ========================================================

    def smooth_landmarks(
        self,
        current_landmarks,
        previous_landmarks=None,
        alpha=None
    ):

        if alpha is None:
            alpha = self.smoothing_alpha

        # No current detection
        if current_landmarks is None:

            return previous_landmarks

        # First frame
        if previous_landmarks is None:

            return current_landmarks

        smoothed = []

        for current, previous in zip(
            current_landmarks,
            previous_landmarks
        ):

            smoothed.append(
                self.ema_smooth(
                    current,
                    previous,
                    alpha
                )
            )

        return smoothed


    # ========================================================
    # PROCESS ONE FRAME
    # ========================================================

    def process_frame(
        self,
        frame
    ):

        # 1. Extract
        raw_landmarks = self.extract_landmarks(frame)

        # No person
        if raw_landmarks is None:

            return self.previous_landmarks

        # 2. Filter
        filtered_landmarks = self.filter_landmarks(
            raw_landmarks
        )

        # 3. Smooth
        smoothed_landmarks = self.smooth_landmarks(
            filtered_landmarks,
            self.previous_landmarks
        )

        # Save state
        self.previous_landmarks = smoothed_landmarks

        return smoothed_landmarks


    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        self.previous_landmarks = None


    # ========================================================
    # CLOSE MEDIAPIPE
    # ========================================================

    def close(self):

        self.pose.close()


# ============================================================
# GLOBAL ESTIMATOR
# ============================================================

_default_estimator = PoseEstimator()


# ============================================================
# BACKWARD-COMPATIBLE FUNCTION
# ============================================================

def extract_landmarks(frame):

    return _default_estimator.extract_landmarks(frame)


def filter_landmarks(
    landmarks,
    threshold=0.7
):

    return _default_estimator.filter_landmarks(
        landmarks,
        threshold
    )


def ema_smooth(
    current,
    previous,
    alpha=0.7
):

    return PoseEstimator.ema_smooth(
        current,
        previous,
        alpha
    )


def smooth_landmarks(
    current_landmarks,
    previous_landmarks,
    alpha=0.7
):

    return _default_estimator.smooth_landmarks(
        current_landmarks,
        previous_landmarks,
        alpha
    )


def process_frame(
    frame,
    previous_landmarks=None,
    visibility_threshold=0.7,
    alpha=0.7
):

    # --------------------------------------------------------
    # IMPORTANT:
    # This function is intentionally independent of
    # PoseEstimator importing itself.
    # --------------------------------------------------------

    raw_landmarks = _default_estimator.extract_landmarks(
        frame
    )

    if raw_landmarks is None:

        return previous_landmarks

    filtered_landmarks = _default_estimator.filter_landmarks(
        raw_landmarks,
        visibility_threshold
    )

    smoothed_landmarks = _default_estimator.smooth_landmarks(
        filtered_landmarks,
        previous_landmarks,
        alpha
    )

    return smoothed_landmarks