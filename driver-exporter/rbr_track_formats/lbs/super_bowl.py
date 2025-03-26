"""Super bowl
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..common import Vector3
from .common import ObjectData3D


@dataclass
class SuperBowlObject:
    """A piece of the super bowl mesh.

    position
        Centre of the bounding box, unused in game
    data_3d
        Mesh and material data
    """

    position: Vector3
    data_3d: ObjectData3D


@dataclass
class SuperBowl:
    """A super bowl object

    name
        Name of the super bowl
    objects
        Parts of the mesh, each can have a different texture associated with it.
    """

    name: str
    objects: List[SuperBowlObject]
