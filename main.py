import cv2
import carla

from detector import YOLODetector
from tracker import DeepSortTracker
from trajectory import InMemoryTrajectoryStore, FadingLineRenderer
from render import BoundingBoxRenderer, HUDRenderer, CompositeRenderer
from pipeline import TrackingPipeline
from spawn_carla import *
from video_save import OpenCVVideoRecorder, NullVideoRecorder
from utils import carla_image_to_array


def build_pipeline():
    return TrackingPipeline(
        detector=YOLODetector('yolov8n.pt', classes=[2, 5, 7], conf_threshold=0.5),
        tracker=DeepSortTracker(max_age=30, n_init=3, nn_budget=100),
        trajectory_store=InMemoryTrajectoryStore(max_len=30),
        trajectory_renderer=FadingLineRenderer(),
        frame_renderer=CompositeRenderer([
            BoundingBoxRenderer(),
            HUDRenderer(),
        ])
    )


def main(record=True):
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    FPS = 30
    WIDTH, HEIGHT = 1280, 720

    world_factory = SynchronousWorldFactory(fps=FPS)
    world = world_factory.create_world(client, town='Town03')

    ego = EgoVehicleSpawner().spawn(world, client=client)
    npcs = TrafficSpawner(num_vehicles=20).spawn(world, client=client)

    cam_spawner = ChaseCameraSpawner(
        width=WIDTH, height=HEIGHT, height_z=8.0, back_distance=10.0, pitch=-25.0
    )
    camera = cam_spawner.spawn(world, target=ego)

    pipeline = build_pipeline()

    recorder = (
        OpenCVVideoRecorder(output_dir='recordings', fps=FPS, width=WIDTH, height=HEIGHT)
        if record else NullVideoRecorder()
    )

    latest_frame = {'data': None, 'timestamp': 0}

    def camera_callback(image):
        latest_frame['data'] = carla_image_to_array(image)
        latest_frame['timestamp'] = image.timestamp

    camera.listen(camera_callback)
    actors = [ego, camera, npcs]

    try:
        while True:
            world.tick()

            # Keep camera locked to ego vehicle, road-normal orientation
            cam_spawner.update(camera)

            if latest_frame['data'] is None:
                continue

            frame = latest_frame['data'].copy()
            frame = pipeline.process(frame, latest_frame['timestamp'])

            recorder.write(frame)

            cv2.imshow('CARLA MOT', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        recorder.release()
        ActorCleanup.destroy_all(actors)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main(record=True)