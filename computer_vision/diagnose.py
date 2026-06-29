"""Temporary diagnostic — what does YOLO actually see in your video?

Place this file next to app.py (project root, NOT inside detection/) and run:
    python diagnose.py

It scans the first 60 frames with the class filter REMOVED and a low
confidence threshold, then prints every object class it found and how many
times. This tells us definitively whether your cars are being detected at all
in this footage. Delete it after debugging.
"""

from collections import Counter
import cv2
from ultralytics import YOLO
from detection.config import SOURCE, MODEL_PATH


def main() -> None:
    cap = cv2.VideoCapture(SOURCE)
    if not cap.isOpened():
        raise SystemExit(f"Could not open SOURCE='{SOURCE}'. Check the path in detection/config.py")

    model = YOLO(MODEL_PATH)
    seen: Counter[str] = Counter()
    frames = 0

    while frames < 60:
        ok, frame = cap.read()
        if not ok:
            break
        frames += 1
        # conf=0.25, NO class filter -> show everything the model thinks it sees
        r = model(frame, conf=0.25, verbose=False)[0]
        if r.boxes is None:
            continue
        for cls in r.boxes.cls:
            seen[model.names[int(cls)]] += 1

    cap.release()
    print(f"\nScanned {frames} frames from '{SOURCE}'.")
    print("Detected (class: total boxes across those frames):")
    if not seen:
        print("  NOTHING detected at all -> footage/source problem, not detection.")
    else:
        for name, n in seen.most_common():
            print(f"  {name:15s} {n}")


if __name__ == "__main__":
    main()
