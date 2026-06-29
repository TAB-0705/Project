"""Line-crossing vehicle counter. Deliberately independent of YOLO/OpenCV so
the counting rule can be reasoned about and tested on its own.

Idea: a virtual horizontal line at y = line_y. For each tracked object we
remember its previous centroid y. When an object's centroid moves from one
side of the line to the other, it has crossed — count it once, in the
direction it crossed."""


class LineCounter:
    def __init__(self, line_y: int) -> None:
        self.line_y = line_y
        self._last_y: dict[int, float] = {}   # track_id -> previous centroid y
        self._counted: set[int] = set()        # ids already counted
        self.count_down = 0                     # crossed top -> bottom
        self.count_up = 0                       # crossed bottom -> top

    def update(self, track_id: int, cy: float) -> None:
        prev = self._last_y.get(track_id)
        self._last_y[track_id] = cy

        if prev is None or track_id in self._counted:
            return

        # Crossed downward: was above the line, now on/below it.
        if prev < self.line_y <= cy:
            self.count_down += 1
            self._counted.add(track_id)
        # Crossed upward: was below the line, now on/above it.
        elif prev > self.line_y >= cy:
            self.count_up += 1
            self._counted.add(track_id)

    @property
    def total(self) -> int:
        return self.count_up + self.count_down
