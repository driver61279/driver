from __future__ import annotations
from dataclasses import dataclass
import enum
from typing import List

from ..common import Vector3


HIGH_COUNT: int = 10000


class Interpolation(enum.Enum):
    """Spline point interpolation mode.

    CUBIC_HERMITE
        use cubic hermite interpolation.
    LINEAR
        use linear interpolation.
    CONSTANT
        use constant value (no interpolation).
    """

    CUBIC_HERMITE = 0x0
    LINEAR = 0x200
    CONSTANT = 0x400


@dataclass
class SplineControlPoint:
    """A cubic hermite spline control point.

    position
        Position of the controlled entity in the world
    tangent_end
        Tangent vector at the end of the segment
    tangent_start
        Tangent vector at the start of the segment
    anim_value
        Value of the controlled entity to set
    """

    position: Vector3
    tangent_end: Vector3
    tangent_start: Vector3
    anim_value: float


@dataclass
class Spline:
    """A cubic hermite spline"""

    group: int
    id: int
    points: List[SplineControlPoint]


@dataclass
class Splines:
    splines: List[Spline]
