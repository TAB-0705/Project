# Real-Time Vehicle Counting with YOLOv8

Detects and tracks vehicles in a video stream and counts them as they cross a
virtual line, separated by direction. Uses the COCO-pretrained `yolov8n` model
(no training needed) and ByteTrack for stable IDs across frames.

## Architecture

```
app.py                    real-time loop: read frame -> detect -> draw -> count
detection/
  config.py               model, source, classes, line position
  detector.py             wraps YOLOv8 .track() (the only file importing ultralytics)
  counter.py              line-crossing counting logic (pure, testable)
```

The detector and the counter are independent: the counter knows nothing about
YOLO, only about centroids and a line. That separation is why the counting
logic can be unit-tested without a GPU or any model.

## ⚠️ Python version

Use **Python 3.11 or 3.12** (install alongside 3.14, don't remove it).
`ultralytics` installs `torch`, which has no Python 3.14 wheel yet.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If tracking errors mention `lap`, run: `pip install lapx`.

## Get a video

Vehicle counting needs traffic footage (a webcam pointed at your room won't
show cars). Download any short traffic clip (e.g. a free one from Pexels),
save it as `traffic.mp4` next to `app.py`. `SOURCE` in config.py already
points to it. To test detection generally without traffic, set `SOURCE = 0`
(webcam) — it will detect/track whatever it sees.

## Run

```powershell
python app.py
```

First run downloads `yolov8n.pt` (~6MB) automatically — do this once before
the demo so it isn't downloading live. Press `q` to quit.

## Talking points

- **Detection vs tracking:** YOLO detects objects in a single frame.
  ByteTrack links detections across frames into persistent IDs. You need BOTH
  to count: detection alone would recount the same car every frame.
- **Why count on line-crossing, not just presence:** counting objects per
  frame and summing would massively overcount. A vehicle is counted once, the
  moment its centroid crosses the line.
- **Why `yolov8n` (nano):** smallest variant, fastest inference — the right
  trade-off for real-time on a laptop CPU.
