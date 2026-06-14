from abc import ABC, abstractmethod
from ultralytics import YOLO


class IDetector(ABC):
    @abstractmethod
    def detect(self, frame):
        """Return list of ([x,y,w,h], confidence, class_id)"""
        pass


class YOLODetector(IDetector):
    def __init__(self, model_path='yolov8n.pt', classes=None, conf_threshold=0.5):
        self.model = YOLO(model_path)
        self.classes = classes or [2, 5, 7]  # car, bus, truck
        self.conf_threshold = conf_threshold

    def detect(self, frame):
        results = self.model(frame, classes=self.classes, verbose=False)
        detections = []
        for box in results[0].boxes:
            conf = float(box.conf[0])
            if conf <= self.conf_threshold:
                continue
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            cls = int(box.cls[0])
            detections.append(([x1, y1, x2 - x1, y2 - y1], conf, cls))
        return detections