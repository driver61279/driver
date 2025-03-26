from __future__ import annotations
from dataclasses import dataclass
import enum
from typing import Dict, Union

from ..common import Key


class AnimCameraMode(enum.Enum):
    DEFAULT = 0x0
    SHAKE_ACTIVE = 0x1
    HELICAM = 0x2

    def pretty(self) -> str:
        if self is AnimCameraMode.DEFAULT:
            return "Steady"
        elif self is AnimCameraMode.SHAKE_ACTIVE:
            return "Shake"
        elif self is AnimCameraMode.HELICAM:
            return "Helicam"

    def description(self) -> str:
        if self is AnimCameraMode.DEFAULT:
            return "Steady camera"
        elif self is AnimCameraMode.SHAKE_ACTIVE:
            return "Handheld camera which can shake. Shake is only active when the camera is set to track the car."
        elif self is AnimCameraMode.HELICAM:
            return "Helicam emits a helicopter sound and can shake. Shake is only active when the camera is set to track the car."


class LookAtMode(enum.Enum):
    """Camera look at settings.

    FIXED
        Use the angle specified in the trigger data
    CAR
        Look at the car
    CHASE
        Camera becomes the chase camera
    DRIVER
        Camera gives the driver's point of view
    DRIVER_2
        As above, but this also exists in the native tracks.
    """

    FIXED = 0
    CAR = -1
    CHASE = -14
    DRIVER_2 = -15
    DRIVER = -16


@dataclass
class AnimationCamera:
    """Roadside or helicopter camera, controlled by triggers.

    id
        ID of the trigger to control the position
    look_at
        What the camera should be looking at. Either LookAtMode or an animation
        ID of some trigger data - the camera will point at the position of the
        trigger data.
    fov
        FOV of the camera
    shake
        Control the amount of camera wobble. 0 = no wobble. Sensible values are
        less than 0.5.
    mode
        Camera mode, controls shake on/off and helicam.
    znear
        Z-near setting - near clipping distance.
    """

    look_at: Union[LookAtMode, Key]
    fov: float
    shake: float
    mode: AnimCameraMode
    znear: float


@dataclass
class AnimationCameras:
    cameras: Dict[Key, AnimationCamera]
