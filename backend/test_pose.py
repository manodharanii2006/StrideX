import os
import cv2
import mediapipe as mp

# ============================================================
# STRIDEX - MEDIAPIPE POSE TEST
# Tests different parts of the walking video
# ============================================================

# ------------------------------------------------------------
# 1. Project and video path
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

VIDEO_PATH = os.path.join(
    PROJECT_ROOT,
    "sample walk.mp4"
)

print("=" * 60)
print("STRIDEX POSE DETECTION TEST")
print("=" * 60)

print("\nVideo path:")
print(VIDEO_PATH)

# ------------------------------------------------------------
# 2. Check video exists
# ------------------------------------------------------------

if not os.path.exists(VIDEO_PATH):
    print("\nERROR: Video file does not exist!")
    print("Expected:")
    print(VIDEO_PATH)
    raise SystemExit

print("\nVideo found successfully.")

# ------------------------------------------------------------
# 3. Open video
# ------------------------------------------------------------

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("\nERROR: Could not open video.")
    raise SystemExit

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print("\nVIDEO INFORMATION")
print("-" * 40)
print(f"FPS:        {fps:.2f}")
print(f"Frames:     {frame_count}")
print(f"Resolution: {width} x {height}")
print(f"Duration:   {frame_count / fps:.2f} seconds")

# ------------------------------------------------------------
# 4. Start MediaPipe
# ------------------------------------------------------------

mp_pose = mp.solutions.pose

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=2,
    smooth_landmarks=False,
    enable_segmentation=False,

    # Lower these slightly so we can test detection
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)

print("\nMediaPipe Pose started.")

# ------------------------------------------------------------
# 5. Important gait landmarks
# ------------------------------------------------------------

important_landmarks = {
    23: "Left Hip",
    24: "Right Hip",
    25: "Left Knee",
    26: "Right Knee",
    27: "Left Ankle",
    28: "Right Ankle",
    29: "Left Heel",
    30: "Right Heel"
}

# ------------------------------------------------------------
# 6. Test different sections of the video
# ------------------------------------------------------------

test_frames = [
    0,
    100,
    200,
    300,
    400,
    500,
    600,
    700
]

print("\nTESTING DIFFERENT VIDEO FRAMES")
print("=" * 60)

detected_count = 0

for target_frame in test_frames:

    # Don't request a frame beyond the video
    if target_frame >= frame_count:
        continue

    # Move to target frame
    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        target_frame
    )

    success, frame = cap.read()

    if not success:
        print(
            f"\nFrame {target_frame}: "
            "Could not read frame"
        )
        continue

    # --------------------------------------------------------
    # Convert OpenCV BGR → RGB
    # --------------------------------------------------------

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # --------------------------------------------------------
    # MediaPipe inference
    # --------------------------------------------------------

    results = pose.process(rgb_frame)

    timestamp = target_frame / fps

    print(
        f"\nFrame {target_frame} "
        f"| Time: {timestamp:.2f}s"
    )

    # --------------------------------------------------------
    # Check detection
    # --------------------------------------------------------

    if not results.pose_landmarks:

        print("  ❌ NO PERSON DETECTED")

        continue

    detected_count += 1

    print("  ✅ PERSON DETECTED!")

    landmarks = results.pose_landmarks.landmark

    # --------------------------------------------------------
    # Print important landmarks
    # --------------------------------------------------------

    print("  Gait landmarks:")

    for index, name in important_landmarks.items():

        landmark = landmarks[index]

        print(
            f"    {name:<12} "
            f"x={landmark.x:.3f} "
            f"y={landmark.y:.3f} "
            f"z={landmark.z:.3f} "
            f"visibility={landmark.visibility:.3f}"
        )

# ------------------------------------------------------------
# 7. Final result
# ------------------------------------------------------------

cap.release()
pose.close()

print("\n" + "=" * 60)
print("POSE TEST COMPLETED")
print("=" * 60)

print(
    f"\nPerson detected in "
    f"{detected_count}/{len(test_frames)} "
    f"tested frames."
)

if detected_count == 0:

    print("\n❌ MediaPipe could not detect a person.")
    print("We need to inspect the video framing.")

elif detected_count < len(test_frames):

    print(
        "\n⚠️ Person detected in some frames "
        "but not all frames."
    )

else:

    print(
        "\n✅ MediaPipe is successfully detecting "
        "the person."
    )