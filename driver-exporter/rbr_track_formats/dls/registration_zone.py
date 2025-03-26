from __future__ import annotations
from dataclasses import dataclass

from ..common import Vector3


@dataclass
class RegistrationZone:
    """Position of the registration table at the end of the stage.

    position
        Position of the registration zone in the world
    radius
        Radius in metres. Should reach beyond the brake wall.
    """

    position: Vector3
    radius: float
