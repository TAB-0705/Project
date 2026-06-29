"""All tunable settings in one place."""

# yolov8n = the 'nano' model: smallest and fastest, best for real-time on CPU.
# Step up to yolov8s / yolov8m for more accuracy if you have a GPU.
MODEL_PATH = "yolov8s.pt"

# Video source. Use a traffic video file for vehicle counting, e.g.:
#   SOURCE = "traffic.mp4"
# Use 0 for the default webcam (handy for testing detection on any object).
SOURCE = "traffic.mp4"

# COCO class indices to count: car=2, motorcycle=3, bus=5, truck=7.
VEHICLE_CLASSES = [2, 3, 5, 7]

# Minimum detection confidence.
CONF = 0.4

# Horizontal counting line position, as a fraction of frame height (0.5 = middle).
LINE_RATIO = 0.5
