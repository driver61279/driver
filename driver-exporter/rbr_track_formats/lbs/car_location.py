"""Car location controls the initial position and rotation of the car.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..common import Vector3, Matrix4x4


@dataclass
class CarLocation:
    """Specify the car location in world space.

    position
        World space position
    euler_vector
        A combined axis/angle vector specifying rotation
    transformation_matrix
        Unused in the game, but this is a transformation matrix which
        matches the above position and euler_vector.
    """

    position: Vector3
    euler_vector: Vector3
    # Apparently the game skips these bytes.
    transformation_matrix: Optional[Matrix4x4] = None
