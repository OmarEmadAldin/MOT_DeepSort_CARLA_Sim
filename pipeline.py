class TrackingPipeline:
    def __init__(self, detector, tracker, trajectory_store,trajectory_renderer, frame_renderer):
        self.detector = detector
        self.tracker = tracker
        self.trajectory_store = trajectory_store
        self.trajectory_renderer = trajectory_renderer
        self.frame_renderer = frame_renderer

    def process(self, frame, timestamp):
        detections = self.detector.detect(frame)
        tracked_objects = self.tracker.update(detections, frame)

        active_ids = []
        for obj in tracked_objects:
            cx, cy = obj.center
            self.trajectory_store.update(obj.track_id, cx, cy)
            active_ids.append(obj.track_id)

        self.trajectory_store.cleanup(active_ids)

        for obj in tracked_objects:
            points = self.trajectory_store.get(obj.track_id)
            self.trajectory_renderer.render(frame, points)

        frame = self.frame_renderer.render(frame, tracked_objects)
        return frame