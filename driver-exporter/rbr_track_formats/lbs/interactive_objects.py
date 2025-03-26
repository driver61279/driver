"""Interactive objects are rigid bodies that can be pushed around. They must
have an associated shape collision mesh in the trk file.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from ..common import Key, Matrix4x4
from ..trk.shape_collision_meshes import ObjectKind
from .common import ObjectData3D


@dataclass
class Instance:
    """An instance of an interactive object visual mesh.

    key
        The ID which links to the shape collision mesh
    transformation_matrix
        Redundant data which exactly matches the shape collision mesh
        transformation matrix (constructed from position, rotation, and scale).
        Note that this is left handed, whereas the shape collision mesh data is
        right handed.
    """

    key: Key
    transformation_matrix: Matrix4x4


@dataclass
class InteractiveObject:
    """An interactive object mesh, along with a list of instances.

    name
        Name of this object
    object_kind
        Kind of corresponding collision (seems to be unused in game, it probably
        uses the object_kind from the shape collision mesh).
    data_3d
        Parts of the mesh, each can have a different texture associated with it.
    instances
        Instances of this object in the world
    """

    name: str
    data_3d: List[ObjectData3D]
    instances: List[Instance]
    object_kind: Optional[ObjectKind] = None


@dataclass
class InteractiveObjects:
    objects: List[InteractiveObject]
