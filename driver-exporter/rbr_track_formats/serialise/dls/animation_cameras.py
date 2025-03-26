from rbr_track_formats.binary import PackBin
from rbr_track_formats.common import Key
from rbr_track_formats.dls.animation_cameras import (
    AnimCameraMode,
    AnimationCamera,
    AnimationCameras,
    LookAtMode,
)


def anim_camera_mode_to_binary(self: AnimCameraMode, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def animation_camera_to_binary(self: AnimationCamera, id: Key, bin: PackBin) -> None:
    if isinstance(self.look_at, LookAtMode):
        raw_look_at = self.look_at.value
    elif isinstance(self.look_at, Key):
        raw_look_at = self.look_at.id
    else:
        raise TypeError
    bin.pack("<Ii", id.id, raw_look_at)
    bin.pack("<ff", self.fov, self.shake)
    anim_camera_mode_to_binary(self.mode, bin)
    bin.pack("<f", self.znear)


def animation_cameras_to_binary(self: AnimationCameras, bin: PackBin) -> None:
    bin.pack("<I", len(self.cameras))
    for id, camera in self.cameras.items():
        animation_camera_to_binary(camera, id, bin)
