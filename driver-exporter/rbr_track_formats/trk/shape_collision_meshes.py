"""Collision objects
"""

from __future__ import annotations
from dataclasses import dataclass
import enum
from math import sqrt
from typing import List, Optional, Set, Tuple, Union

from ..common import AaBbBoundingBox, Key, Vector3, Matrix3x3
from ..mat import MaterialID


# RBR has limits on how complex the collision meshes can be.
MAX_SCM_VERTICES = 30
MAX_SCM_EDGES = 84
MAX_SCM_FACES = 56


class ObjectKind(enum.Enum):
    """Kinds of dynamic objects. This gives the object mass and inertia
    reminiscent of the chosen ObjectKind.

    Name                Mass    Behavior    Comments
    TRAFFIC_CONE        5       Very Soft   Often used for rally signs too
    TRAFFIC_PIG         3003                Heavy concrete object
    STREET_SIGN         10      Very Soft
    BANNER_FENCE        100
    LOG                 33
    LOG_POLE            1000
    WOODEN_FENCE_BAR    333
    WOODEN_FENCE_POLE   2000
    """

    TRAFFIC_CONE = 0x1
    TRAFFIC_PIG = 0x2
    STREET_SIGN = 0x3
    BANNER_FENCE = 0x6
    LOG = 0x7
    LOG_POLE = 0x8
    WOODEN_FENCE_BAR = 0x9
    WOODEN_FENCE_POLE = 0xA

    def pretty(self) -> str:
        if self is ObjectKind.TRAFFIC_CONE:
            return "Traffic Cone"
        elif self is ObjectKind.TRAFFIC_PIG:
            return "Heavy Concrete Block"
        elif self is ObjectKind.STREET_SIGN:
            return "Street Sign"
        elif self is ObjectKind.BANNER_FENCE:
            return "Banner Fence"
        elif self is ObjectKind.LOG:
            return "Log"
        elif self is ObjectKind.LOG_POLE:
            return "Log Pole"
        elif self is ObjectKind.WOODEN_FENCE_BAR:
            return "Wooden Fence Bar"
        elif self is ObjectKind.WOODEN_FENCE_POLE:
            return "Wooden Fence Pole"

    def description(self) -> str:
        if self is ObjectKind.TRAFFIC_CONE:
            return "Very soft, can be used for small signs"
        elif self is ObjectKind.TRAFFIC_PIG:
            return "Very heavy object which can easily kill the car"
        elif self is ObjectKind.STREET_SIGN:
            return "Very soft"
        elif self is ObjectKind.BANNER_FENCE:
            return ""
        elif self is ObjectKind.LOG:
            return ""
        elif self is ObjectKind.LOG_POLE:
            return ""
        elif self is ObjectKind.WOODEN_FENCE_BAR:
            return ""
        elif self is ObjectKind.WOODEN_FENCE_POLE:
            return ""


class SoftVolumeType(enum.Enum):
    NONE = 0x0
    BOX = 0x1
    SPHERE = 0x2


@dataclass
class BoundingSphere:
    """Bounding volume, as a sphere.

    position
        Position of the centre of sphere
    radius
        Radius of the sphere
    """

    position: Vector3
    radius: float

    def __hash__(self) -> int:
        return (self.position, self.radius).__hash__()


@dataclass
class FaceData:
    """A face triangle, defined by indices into vertex arrays.

    spectator
        Determines if this is a face of a spectator object.
        This doesn't seem to actually have any effect in game.
        If it's set, running into the face will not cause a red screen.
        Even if it _isn't_ set, but the soft volume is present, we will get a
        red screen.
        In native stages this is true for every static mesh object with material
        set to SCRIPT_CHARACTER, so we should match that.
    index_a, index_b, index_c
        Indices into the vertex array.
    """

    index_a: int
    index_b: int
    index_c: int
    spectator: bool = False


@dataclass
class Quaternion:
    x: float
    y: float
    z: float
    w: float

    def to_3x3_matrix(self) -> Matrix3x3:
        x = self.x
        y = self.y
        z = self.z
        w = self.w
        return Matrix3x3(
            Vector3(
                1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w
            ),
            Vector3(
                2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w
            ),
            Vector3(
                2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y
            ),
        )

    def flip_handedness(self) -> Quaternion:
        return Quaternion(self.x, self.z, self.y, self.w)

    def length(self) -> float:
        return sqrt(
            self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w
        )

    def scale(self, scalar: float) -> Quaternion:
        return Quaternion(
            x=self.x * scalar,
            y=self.y * scalar,
            z=self.z * scalar,
            w=self.w * scalar,
        )

    def normalised(self) -> Quaternion:
        length = self.length()
        if length > 0:
            return self.scale(1 / length)
        else:
            return self.scale(1)


@dataclass
class ObjectData:
    """Information about an instance of a shape collision mesh. The vectors use
    right handed coordinate systems.

    key
        Unique ID used to refer to this instance. For dynamic objects, there
        should be a corresponding entry in interactive_objects.
    position
        Position in world space
    scale
        Scale multiplier
    rotation
        Rotation. Not used if the shape mesh has use_local_rotation set to True.
    """

    key: Key
    position: Vector3
    scale: Vector3
    rotation: Quaternion


@dataclass
class StaticMesh:
    """Static mesh object, may have a corresponding soft volume.
    The mesh data gives a hard collision, and the simple soft_volume gives a
    soft collision (a force applied to the car). Mesh data may be entirely
    empty in order to get only soft collisions, for small bushes and snowwalls.

    material
        Physical material. Must be a member of ..mat.object_materials.
    soft_volume
        Optional soft volume. Some things like snowbanks and spectators
        don't have mesh data, opting for just using the soft volume instead.
        The positions are relative to the object instance position.
    use_local_rotation
        When True, we don't use the rotation of the instance data. i.e. we use
        the local (mesh) rotation from the mesh data instead. Generally this
        should be allowed to default to False, I think it's a hack the devs
        implemented to get things done faster.
    object_kind
        If the data includes a bad object kind, we keep it around for
        roundtripping. If you are constructing this type, just let it default
        to 0.
    """

    material: MaterialID
    soft_volume: Optional[Union[AaBbBoundingBox, BoundingSphere]]
    use_local_rotation: bool = False
    object_kind: int = 0


@dataclass
class DynamicMesh:
    """Dynamic mesh object. No soft volume."""

    kind: ObjectKind


@dataclass
class ShapeCollisionMesh:
    """Instanced collision meshes for track objects.

    name
        The name of this type of mesh object
    mesh_type
        Either static or dynamic objects. This is static/dynamic from the
        perspective of the physics engine.
    vertices
        Vertices of the collision mesh
    faces
        Face triangles of the collision mesh
    objects
        Instances of this mesh in the world
    """

    name: str
    mesh_type: Union[StaticMesh, DynamicMesh]
    vertices: List[Vector3]
    faces: List[FaceData]
    objects: List[ObjectData]

    def compute_edge_count(self) -> int:
        """Compute the number of edges in the mesh"""
        edges: Set[Tuple[int, ...]] = set()
        for face in self.faces:
            edges.add(tuple(sorted([face.index_a, face.index_b])))
            edges.add(tuple(sorted([face.index_b, face.index_c])))
            edges.add(tuple(sorted([face.index_c, face.index_a])))
        return len(edges)


@dataclass
class ShapeCollisionMeshes:
    meshes: List[ShapeCollisionMesh]

    def union(self, other: ShapeCollisionMeshes) -> ShapeCollisionMeshes:
        meshes = []
        meshes.extend(self.meshes)
        meshes.extend(other.meshes)
        return ShapeCollisionMeshes(meshes=meshes)
