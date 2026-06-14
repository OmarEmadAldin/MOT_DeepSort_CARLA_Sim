from abc import ABC, abstractmethod
import cv2
import os
import datetime


class IVideoRecorder(ABC):
    @abstractmethod
    def write(self, frame):
        pass

    @abstractmethod
    def release(self):
        pass


class OpenCVVideoRecorder(IVideoRecorder):
    def __init__(self, output_dir='recordings', fps=30, width=1280, height=720,
                 fourcc='mp4v', filename=None):
        os.makedirs(output_dir, exist_ok=True)

        if filename is None:
            filename = f'sim_.mp4'

        self.filepath = os.path.join(output_dir, filename)
        fourcc_code = cv2.VideoWriter_fourcc(*fourcc)
        self._writer = cv2.VideoWriter(self.filepath, fourcc_code, fps, (width, height))

        if not self._writer.isOpened():
            raise RuntimeError(f"Failed to open video writer for {self.filepath}")

    def write(self, frame):
        self._writer.write(frame)

    def release(self):
        self._writer.release()
        print(f"Saved recording to {self.filepath}")


class NullVideoRecorder(IVideoRecorder):
    """No-op recorder — used when recording is disabled (Null Object pattern)"""
    def write(self, frame):
        pass

    def release(self):
        pass