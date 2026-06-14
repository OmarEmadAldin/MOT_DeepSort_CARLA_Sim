from abc import ABC, abstractmethod
import carla
import random


class IWorldFactory(ABC):
    @abstractmethod
    def create_world(self, client, town):
        pass


class SynchronousWorldFactory(IWorldFactory):
    def __init__(self, fps=30):
        self.fps = fps

    def create_world(self, client, town='Town12'):
        world = client.load_world(town)
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 1.0 / self.fps
        world.apply_settings(settings)
        return world


class IActorSpawner(ABC):
    @abstractmethod
    def spawn(self, world, **kwargs):
        pass


class EgoVehicleSpawner(IActorSpawner):
    def __init__(self, blueprint_id='vehicle.tesla.model3'):
        self.blueprint_id = blueprint_id

    def spawn(self, world, client=None, **kwargs):
        bp = world.get_blueprint_library().find(self.blueprint_id)
        spawn_points = world.get_map().get_spawn_points()
        ego = world.try_spawn_actor(bp, random.choice(spawn_points))

        if client is not None:
            tm = client.get_trafficmanager()
            tm.set_synchronous_mode(True)
            ego.set_autopilot(True, tm.get_port())
        else:
            ego.set_autopilot(True)

        return ego


class ChaseCameraSpawner(IActorSpawner):
    """Camera follows a target actor, positioned above and behind it,
    oriented along the vehicle's heading (road-normal)."""
    def __init__(self, width=1280, height=720, fov=90,
                 height_z=4.0, back_distance=5.0, pitch=-25.0):
        self.width = width
        self.height = height
        self.fov = fov
        self.height_z = height_z
        self.back_distance = back_distance
        self.pitch = pitch
        self.target = None

    def spawn(self, world, target=None, **kwargs):
        bp = world.get_blueprint_library().find('sensor.camera.rgb')
        bp.set_attribute('image_size_x', str(self.width))
        bp.set_attribute('image_size_y', str(self.height))
        bp.set_attribute('fov', str(self.fov))

        self.target = target
        transform = self._compute_transform(target.get_transform())
        camera = world.spawn_actor(bp, transform)
        return camera

    def _compute_transform(self, target_transform):
        forward = target_transform.get_forward_vector()
        loc = target_transform.location

        camera_loc = carla.Location(
            x=loc.x - forward.x * self.back_distance,
            y=loc.y - forward.y * self.back_distance,
            z=loc.z + self.height_z
        )

        camera_rot = carla.Rotation(
            pitch=self.pitch,
            yaw=target_transform.rotation.yaw,
            roll=0.0
        )

        return carla.Transform(camera_loc, camera_rot)

    def update(self, camera, *_args, **_kwargs):
        """Call every tick to keep camera following the target."""
        if self.target is None:
            return
        transform = self._compute_transform(self.target.get_transform())
        camera.set_transform(transform)


class TrafficSpawner(IActorSpawner):
    def __init__(self, num_vehicles=20):
        self.num_vehicles = num_vehicles

    def spawn(self, world, client=None, **kwargs):
        bp_lib = world.get_blueprint_library().filter('vehicle.*')
        spawn_points = world.get_map().get_spawn_points()
        random.shuffle(spawn_points)

        tm = client.get_trafficmanager()
        tm.set_synchronous_mode(True)

        npcs = []
        for sp in spawn_points[:self.num_vehicles]:
            bp = random.choice(bp_lib)
            npc = world.try_spawn_actor(bp, sp)
            if npc:
                npc.set_autopilot(True, tm.get_port())
                npcs.append(npc)
        return npcs


class ActorCleanup:
    @staticmethod
    def destroy_all(actors):
        for a in actors:
            if a is None:
                continue
            if isinstance(a, list):
                ActorCleanup.destroy_all(a)
            elif a.is_alive:
                a.destroy()