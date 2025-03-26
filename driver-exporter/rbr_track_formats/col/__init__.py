"""Collision tree.
This specifies a number of static collision objects:
- Brake walls (areas which slow the car to a stop)
- Collision meshes (static, e.g. road mesh, buildings)
- Surface water (puddles) - only active when weather is wet
- Deep water (river crossings)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import enum

from .brake_wall import BrakeWall
from .tree import (
    BranchTraversal,
    CollisionTreeRoot,
)
from ..common import NumpyArray, Vector3

COL_MAGIC: bytes = b"OC7R"


@dataclass
class COLHeader:
    root_file_node_offset: int
    num_subtree_nodes: int
    subtree_nodes_offset: int


class CollisionTreeDataType(enum.Enum):
    OFFSET_14_BRAKE_WALL = 0x1
    BRAKE_WALL = 0x2
    WET_SURFACES = 0x3
    WET_SURFACES_AND_WATER = 0x4


class CollisionTreeType(enum.Enum):
    __ROOT_TREE__ = 0x0
    RELATIVE_ADDRESSED_SUBTREE = 0x1
    __ABSOLUTE_ADDRESSED_SUBTREE__ = 0x2
    DATA = 0x3


@dataclass
class RootHeader:
    brake_wall_offset: int
    num_wet_surfaces: int
    wet_surfaces_offset: int
    num_water_surfaces: int
    water_surfaces_offset: int


@dataclass
class NPhysics_CCollisionTreeFileNode:
    tree_type: CollisionTreeType
    branch_traversal: BranchTraversal
    num_vertices: int
    vertices_offset: int
    collision_tree_offset: int


@dataclass
class WaterSurface:
    a: Vector3
    b: Vector3
    c: Vector3
    d: Vector3


@dataclass
class COL:
    brake_wall: Optional[BrakeWall]
    wet_surfaces: List[WaterSurface]
    water_surfaces: List[WaterSurface]
    collision_tree_root: CollisionTreeRoot
    subtrees: List[Tuple[BranchTraversal, NumpyArray, CollisionTreeRoot]]
    __brake_wall_padding__: Optional[bytes] = None
    # __subtree_padding__: Optional[bytes] = None

    def collision_mesh_chunks(
        self,
    ) -> List[Tuple[NumpyArray, List[NumpyArray]]]:
        result = []
        for _, vertices, subtree in self.subtrees:
            triangles = []
            subtree.traverse_leaves(lambda leaf: triangles.append(leaf.triangles))
            result.append((vertices, triangles))
        return result
