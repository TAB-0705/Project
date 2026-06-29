"""Real-time vehicle counting with YOLOv8 + ByteTrack.

Run:  python app.py
Quit: press 'q' in the video window.
"""

import cv2
from detection.detector import VehicleDetector
from detection.counter import LineCounter
from detection.config import SOURCE, LINE_RATIO


def _rotation_code(cap):
    """Phone portrait videos store their pixels landscape plus a rotation flag
    in metadata that OpenCV ignores by default, so frames come in sideways and
    detection fails. Read that flag and return the cv2.rotate code that makes
    frames upright (or None if the video is already upright)."""
    try:
        angle = int(cap.get(cv2.CAP_PROP_ORIENTATION_META))
    except Exception:
        angle = 0
    return {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }.get(angle)


def main() -> None:
    cap = cv2.VideoCapture(SOURCE)
    if not cap.isOpened():
        raise SystemExit(
            f"Could not open source '{SOURCE}'. "
            f"Set SOURCE in detection/config.py to a video file or 0 for webcam."
        )

    rotate = _rotation_code(cap)  # None for normal landscape footage

    detector = VehicleDetector()
    counter: LineCounter | None = None
    line_y = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break  # end of video

        # Make the frame upright BEFORE anything else, so detection, the line
        # position and the centroids all work on the correctly-oriented image.
        if rotate is not None:
            frame = cv2.rotate(frame, rotate)

        h, w = frame.shape[:2]
        if counter is None:
            line_y = int(h * LINE_RATIO)
            counter = LineCounter(line_y)

        # detect + track
        for tid, name, (x1, y1, x2, y2) in detector.track(frame):
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            counter.update(tid, cy)

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)),
                          (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(frame, f"{name} #{tid}", (int(x1), int(y1) - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # counting line
        cv2.line(frame, (0, line_y), (w, line_y), (0, 255, 255), 2)

        # counts (drawn twice: black outline then colour, for readability)
        label = f"Down: {counter.count_down}  Up: {counter.count_up}  Total: {counter.total}"
        cv2.putText(frame, label, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 4)
        cv2.putText(frame, label, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        cv2.imshow("Vehicle Counting - YOLOv8", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
