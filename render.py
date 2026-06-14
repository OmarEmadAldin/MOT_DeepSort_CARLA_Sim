from abc import ABC, abstractmethod
import cv2


class IFrameRenderer(ABC):
    @abstractmethod
    def render(self, frame, tracked_objects, **kwargs):
        pass


class BoundingBoxRenderer(IFrameRenderer):
    def __init__(self, color=(255, 255, 0), thickness=3):
        self.color = color
        self.thickness = thickness

    def render(self, frame, tracked_objects, **kwargs):
        for obj in tracked_objects:
            l, t, r, b = obj.bbox
            cv2.rectangle(frame, (int(l), int(t)), (int(r), int(b)), self.color, self.thickness)
            cv2.putText(frame, f'ID:{obj.track_id}',
                        (int(l), int(t) - 8), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, self.color, 2)
        return frame


class HUDRenderer(IFrameRenderer):
    def render(self, frame, tracked_objects, **kwargs):
        count = len(tracked_objects)
        cv2.rectangle(frame, (10, 10), (260, 50), (0, 0, 0), -1)
        cv2.putText(frame, f'Vehicles tracked: {count}', (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        return frame


class CompositeRenderer(IFrameRenderer):
    """Combines multiple renderers - Open/Closed: add renderers without modifying this class"""
    def __init__(self, renderers):
        self.renderers = renderers

    def render(self, frame, tracked_objects, **kwargs):
        for renderer in self.renderers:
            frame = renderer.render(frame, tracked_objects, **kwargs)
        return frame