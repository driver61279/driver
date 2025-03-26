"""Drive points are just a list of position vectors along the driveline.
They are loaded by the game, but unused, and can be omitted.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..common import Vector3


@dataclass
class DrivePoints:
    """Not used in the game. Native stages sometimes have bad data here, too."""

    points: List[Vector3]
