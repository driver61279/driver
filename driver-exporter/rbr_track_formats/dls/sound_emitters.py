from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..common import Vector3


@dataclass
class SoundEmitter:
    """
    Used to play the bird sounds if:
    * car speed is above 70 kph
    * the eye position of the active animation camera is within the sphere

    position
        Position of the sound in the world
    Radius
        Radius of sphere where sound trigger is active
    """

    position: Vector3
    radius: float


@dataclass
class SoundEmitters:
    items: List[SoundEmitter]
