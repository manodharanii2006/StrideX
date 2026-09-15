import cv2
import os


def validate_video(video_path):
    """
    Step 1: Validate the uploaded video.
    """

    # Check that the file exists
    if not video_path or not os.path.exists(video_path):
        raise ValueError("Video file does not exist.")

    # Open video with OpenCV
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("Unable to open the video.")

    # Read video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Validate properties
    if fps <= 0:
        cap.release()
        raise ValueError("Invalid video FPS.")

    if frame_count <= 0:
        cap.release()
        raise ValueError("Video contains no frames.")

    if width <= 0 or height <= 0:
        cap.release()
        raise ValueError("Invalid video resolution.")

    # Calculate duration and time step
    duration = frame_count / fps
    dt = 1.0 / fps

    cap.release()

    return {
        "valid": True,
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration": duration,
        "dt": dt,
    }


def extract_frames(video_path):
    """
    Step 3: Read the video frame-by-frame.
    Returns each frame and its timestamp.
    """

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("Unable to open video.")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        cap.release()
        raise ValueError("Invalid FPS.")

    dt = 1.0 / fps
    frame_number = 0

    while True:

        success, frame = cap.read()

        if not success:
            break

        timestamp = frame_number * dt

        yield frame_number, timestamp, frame

        frame_number += 1

    cap.release()