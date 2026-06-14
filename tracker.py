from abc import ABC, abstractmethod
from deep_sort_realtime.deepsort_tracker import DeepSort


class ITrackedObject:
    """DTO so downstream code doesn't depend on DeepSort internals"""
    def __init__(self, track_id, bbox):
        self.track_id = track_id
        self.bbox = bbox  # (l, t, r, b)

    @property
    def center(self):
        l, t, r, b = self.bbox
        return (l + r) / 2, (t + b) / 2


class ITracker(ABC):
    @abstractmethod
    def update(self, detections, frame):
        """Return list of ITrackedObject"""
        pass


class DeepSortTracker(ITracker):
    def __init__(self, max_age=30, n_init=3, nn_budget=100): # max age 34an el num of frames , n_init el3ddd elli by3ml be tracking 
        self._tracker = DeepSort(max_age=max_age, n_init=n_init, nn_budget=nn_budget)

    def update(self, detections, frame):
        raw_tracks = self._tracker.update_tracks(detections, frame=frame)
        result = []
        for t in raw_tracks:
            if not t.is_confirmed():
                continue
            result.append(ITrackedObject(t.track_id, t.to_ltrb()))
        return result