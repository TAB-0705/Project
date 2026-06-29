"""The only module that imports ultralytics. It loads the model once and
exposes a single track() method returning plain tuples, so the rest of the
app never depends on YOLO's result objects."""

from ultralytics import YOLO
from .config import MODEL_PATH, VEHICLE_CLASSES, CONF


class VehicleDetector:
    def __init__(self) -> None:
        self.model = YOLO(MODEL_PATH)  # auto-downloads weights on first run

    def track(self, frame):
        """Run detection + tracking on one frame.

        persist=True tells the tracker this frame continues the same video,
        so object IDs stay stable across frames (that's what lets us count
        each vehicle exactly once).

        Returns: list of (track_id, class_name, (x1, y1, x2, y2)).
        """
        results = self.model.track(
            frame,
            persist=True,
            conf=CONF,
            classes=VEHICLE_CLASSES,
            tracker="bytetrack.yaml",
            verbose=False,
        )
        r = results[0]
        if r.boxes is None or r.boxes.id is None:
            return []

        dets = []
        for box, tid, cls in zip(r.boxes.xyxy, r.boxes.id, r.boxes.cls):
            x1, y1, x2, y2 = box.tolist()
            name = self.model.names[int(cls)]
            dets.append((int(tid), name, (x1, y1, x2, y2)))
        return dets
