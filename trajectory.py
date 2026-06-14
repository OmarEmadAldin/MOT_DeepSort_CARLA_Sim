from abc import ABC, abstractmethod
from collections import defaultdict, deque
import cv2


class ITrajectoryStore(ABC):
    @abstractmethod
    def update(self, track_id, cx, cy):
        pass

    @abstractmethod
    def get(self, track_id):
        pass

    @abstractmethod
    def cleanup(self, active_ids):
        pass


class InMemoryTrajectoryStore(ITrajectoryStore):
    def __init__(self, max_len=30):
        self.max_len = max_len
        self._history = defaultdict(lambda: deque(maxlen=self.max_len))

    def update(self, track_id, cx, cy):
        self._history[track_id].append((int(cx), int(cy)))

    def get(self, track_id):
        return self._history[track_id]

    def cleanup(self, active_ids):
        stale = [tid for tid in self._history if tid not in active_ids]
        for tid in stale:
            del self._history[tid]


class ITrajectoryRenderer(ABC):
    @abstractmethod
    def render(self, frame, points, color):
        pass


class FadingLineRenderer(ITrajectoryRenderer):
    def render(self, frame, points, color=(255, 0, 0)):
        for i in range(1, len(points)):
            thickness = max(1, int(2 * (i / len(points))))
            cv2.line(frame, points[i-1], points[i], color, thickness)