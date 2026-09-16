from ai.vision.video_processor import validate_video, extract_frames

video_path = "sample walk.mp4"

info = validate_video(video_path)

print("VIDEO INFO:")
print(info)

print("\nFIRST 5 FRAMES:")

for frame_number, timestamp, frame in extract_frames(video_path):
    print(frame_number, timestamp, frame.shape)

    if frame_number == 4:
        break