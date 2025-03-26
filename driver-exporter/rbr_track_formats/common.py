from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from math import cos, sin
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)
import copy
import enum
import functools
import itertools
import math

import numpy as np
from numpy.lib.recfunctions import (
    structured_to_unstructured,
)

from . import dtypes
from . import errors


# The numpy version in blender does not include numpy.typing
NumpyArray = Any
NumpyDType = Any


@dataclass
class Vector2:
    x: float
    y: float

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def scale(self, scalar: float) -> Vector2:
        return Vector2(self.x * scalar, self.y * scalar)

    def to_list(self) -> List[float]:
        return [self.x, self.y]

    def __hash__(self) -> int:
        return (self.x, self.y).__hash__()


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def __add__(self, other: Vector3) -> Vector3:
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3) -> Vector3:
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def scale(self, scalar: float) -> Vector3:
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other: Vector3) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vector3) -> Vector3:
        return Vector3(
            x=self.y * other.z - self.z * other.y,
            y=self.z * other.x - self.x * other.z,
            z=self.x * other.y - self.y * other.x,
        )

    def __hash__(self) -> int:
        return (self.x, self.y, self.z).__hash__()

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    @staticmethod
    def from_tuple(tup: Tuple[float, float, float]) -> Vector3:
        (x, y, z) = tup
        return Vector3(x, y, z)

    def copy(self) -> Vector3:
        return Vector3(self.x, self.y, self.z)

    def normalised(self) -> Vector3:
        length = self.length()
        if length > 0:
            return self.copy().scale(1 / length)
        else:
            return self.copy()

    @staticmethod
    def parse_ini_string(s: str) -> Vector3:
        words = s.split()
        if len(words) != 3:
            raise errors.E0034(words=words)

        def from_string(x: str) -> float:
            try:
                return float(x.replace(",", "."))
            except ValueError:
                if len(x) > 1:
                    return from_string(x[1:])
                else:
                    raise errors.E0034(words=words)

        return Vector3(
            x=from_string(words[0]),
            y=from_string(words[1]),
            z=from_string(words[2]),
        )

    def to_ini_string(self) -> str:
        return f"{self.x:f} {self.y:f} {self.z:f}"

    def pretty(self) -> str:
        return "{: f} {: f} {: f}".format(self.x, self.y, self.z)

    def flip_handedness(self) -> Vector3:
        return Vector3(self.x, self.z, self.y)


@dataclass
class Vector4:
    x: float
    y: float
    z: float
    w: float

    def pretty(self) -> str:
        return "{: f} {: f} {: f} {: f}".format(self.x, self.y, self.z, self.w)

    def __eq__(self, other: object) -> bool:
        """Approximate equality suitable for floating point"""
        if not isinstance(other, Vector4):
            return NotImplemented
        epsilon = 0.0000001
        return all(
            [
                abs(self.x - other.x) < epsilon,
                abs(self.y - other.y) < epsilon,
                abs(self.z - other.z) < epsilon,
                abs(self.w - other.w) < epsilon,
            ]
        )


@dataclass
class Matrix3x3:
    x: Vector3
    y: Vector3
    z: Vector3

    def pretty(self) -> str:
        return self.x.pretty() + "\n" + self.y.pretty() + "\n" + self.z.pretty()

    def mul(self, other: Matrix3x3) -> Matrix3x3:
        return Matrix3x3(
            x=Vector3(
                self.x.x * other.x.x + self.x.y * other.y.x + self.x.z * other.z.x,
                self.x.x * other.x.y + self.x.y * other.y.y + self.x.z * other.z.y,
                self.x.x * other.x.z + self.x.y * other.y.z + self.x.z * other.z.z,
            ),
            y=Vector3(
                self.y.x * other.x.x + self.y.y * other.y.x + self.y.z * other.z.x,
                self.y.x * other.x.y + self.y.y * other.y.y + self.y.z * other.z.y,
                self.y.x * other.x.z + self.y.y * other.y.z + self.y.z * other.z.z,
            ),
            z=Vector3(
                self.z.x * other.x.x + self.z.y * other.y.x + self.z.z * other.z.x,
                self.z.x * other.x.y + self.z.y * other.y.y + self.z.z * other.z.y,
                self.z.x * other.x.z + self.z.y * other.y.z + self.z.z * other.z.z,
            ),
        )

    @staticmethod
    def from_euler_vector(
        euler_vector: Vector3,
    ) -> Matrix3x3:
        """Convert an euler vector (combined axis angle) into a rotation
        matrix
        """
        # This implementation is taken from
        # https://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle
        t = euler_vector.length()
        e = euler_vector.normalised()
        pre = 1 - cos(t)
        return Matrix3x3(
            Vector3(
                pre * e.x * e.x + cos(t),
                pre * e.x * e.y - e.z * sin(t),
                pre * e.x * e.z + e.y * sin(t),
            ),
            Vector3(
                pre * e.y * e.x + e.z * sin(t),
                pre * e.y * e.y + cos(t),
                pre * e.y * e.z - e.x * sin(t),
            ),
            Vector3(
                pre * e.z * e.x - e.y * sin(t),
                pre * e.z * e.y + e.x * sin(t),
                pre * e.z * e.z + cos(t),
            ),
        )


@dataclass
class Matrix4x4:
    x: Vector4
    y: Vector4
    z: Vector4
    w: Vector4

    def pretty(self) -> str:
        return (
            self.x.pretty()
            + "\n"
            + self.y.pretty()
            + "\n"
            + self.z.pretty()
            + "\n"
            + self.w.pretty()
        )

    @staticmethod
    def from_position_and_rotation_matrix(
        position: Vector3,
        rotation: Matrix3x3,
    ) -> Matrix4x4:
        """Combine a position vector and a rotation matrix"""
        return Matrix4x4(
            Vector4(rotation.x.x, rotation.x.y, rotation.x.z, 0),
            Vector4(rotation.y.x, rotation.y.y, rotation.y.z, 0),
            Vector4(rotation.z.x, rotation.z.y, rotation.z.z, 0),
            Vector4(position.x, position.y, position.z, 1),
        )


@dataclass
class AaBbBoundingBox:
    # position is the centre of the box
    position: Vector3
    # size is the half extents of the side lengths (positive)
    size: Vector3

    def __hash__(self) -> int:
        return (self.position, self.size).__hash__()

    def union(self, other: AaBbBoundingBox) -> AaBbBoundingBox:
        self_min_pos = self.position - self.size
        self_max_pos = self.position + self.size
        other_min_pos = other.position - other.size
        other_max_pos = other.position + other.size
        x_min = min(self_min_pos.x, other_min_pos.x)
        x_max = max(self_max_pos.x, other_max_pos.x)
        y_min = min(self_min_pos.y, other_min_pos.y)
        y_max = max(self_max_pos.y, other_max_pos.y)
        z_min = min(self_min_pos.z, other_min_pos.z)
        z_max = max(self_max_pos.z, other_max_pos.z)
        return AaBbBoundingBox.from_min_max(
            min_pos=Vector3(x_min, y_min, z_min),
            max_pos=Vector3(x_max, y_max, z_max),
        )

    @staticmethod
    def unions(boxes: List[AaBbBoundingBox]) -> Optional[AaBbBoundingBox]:
        combined = None
        for box in boxes:
            if combined is None:
                combined = box
            else:
                combined = combined.union(box)
        return combined

    @staticmethod
    def from_min_max(min_pos: Vector3, max_pos: Vector3) -> AaBbBoundingBox:
        return AaBbBoundingBox(
            position=(min_pos + max_pos).scale(0.5),
            size=(max_pos - min_pos).scale(0.5),
        )


def pretty(prepend: str, skip: List[str], obj: Any) -> None:
    """Utility function for pretty printing structures as a tree"""
    for line in pretty_lines(skip, obj):
        print(prepend + line)


def pretty_lines(skip: List[str], obj: Any) -> List[str]:
    lines = []
    if hasattr(obj, "__dict__"):
        if isinstance(obj, enum.Enum):
            lines.append(str(obj.name))
        else:
            for k in obj.__dict__:
                if k in skip:
                    continue
                val = pretty_lines(skip, obj.__dict__[k])
                if len(val) == 1:
                    lines.append(str(k) + " = " + val[0])
                else:
                    lines.append(str(k))
                    lines += list(map(lambda v: "  " + v, val))
    else:
        lines.append(str(obj))
    return lines


class TriangleIndices:
    @abstractmethod
    def get_abc(self) -> Tuple[int, int, int]:
        pass

    @abstractmethod
    def set_abc(self, a: int, b: int, c: int) -> None:
        pass

    def compute_centre(self, vertices: List[Vector3]) -> Vector3:
        (a, b, c) = self.get_abc()
        va = vertices[a]
        vb = vertices[b]
        vc = vertices[c]
        return (va + vb + vc).scale(1 / 3)


T = TypeVar("T", bound="TriangleIndices")


def chunk_triangles(
    vertices: List[Vector3],
    triangles: List[T],
    chunk_size: float,
) -> Dict[Tuple[int, int, int], List[T]]:
    """Split a large mesh into cubic chunks with sides of size chunk_size.
    This chunks the triangles: it doesn't fully split the mesh since the
    vertices are ignored.
    """
    chunks: Dict[Tuple[int, int, int], List[T]] = dict()
    for triangle in triangles:
        centre = triangle.compute_centre(vertices)
        bin_x = round(centre.x // chunk_size)
        bin_y = round(centre.y // chunk_size)
        bin_z = round(centre.z // chunk_size)
        key = (bin_x, bin_y, bin_z)
        if key in chunks:
            chunks[key].append(triangle)
        else:
            chunks[key] = [triangle]
    return chunks


def chunk_mesh(
    vertices: List[Vector3],
    triangles: List[T],
    chunk_size: float,
) -> Dict[Tuple[int, int, int], Tuple[List[Vector3], List[T]]]:
    """Split a large mesh into cubic chunks with sides of size chunk_size.
    This chunks the vertices and the triangles: i.e. it is a full mesh split.
    """
    # A dictionary where each item is a cubic chunk of the mesh. The key is the
    # bin (position of minimum point of chunk), the value is a tuple of
    # vertices and triangles. The vertices are in a dict so we can find the
    # index of a vertex in O(1) average time.
    chunks: Dict[Tuple[int, int, int], Tuple[Dict[Vector3, int], List[T]]] = dict()
    for triangle in triangles:
        centre = triangle.compute_centre(vertices)
        bin_x = round(centre.x // chunk_size)
        bin_y = round(centre.y // chunk_size)
        bin_z = round(centre.z // chunk_size)
        key = (bin_x, bin_y, bin_z)
        (ia, ib, ic) = triangle.get_abc()
        vert_a = vertices[ia]
        vert_b = vertices[ib]
        vert_c = vertices[ic]
        new_triangle = copy.deepcopy(triangle)
        if key in chunks:
            (chunk_vertices, chunk_triangles) = chunks[key]

            # These lookups may need optimising later.
            def get_index(v: Vector3) -> int:
                try:
                    return chunk_vertices[v]
                except KeyError:
                    num_verts = len(chunk_vertices)
                    chunk_vertices[v] = num_verts
                    return num_verts

            idx_a = get_index(vert_a)
            idx_b = get_index(vert_b)
            idx_c = get_index(vert_c)
            new_triangle.set_abc(idx_a, idx_b, idx_c)
            chunk_triangles.append(new_triangle)
        else:
            chunk_vertices = {vert_a: 0, vert_b: 1, vert_c: 2}
            new_triangle.set_abc(0, 1, 2)
            chunks[key] = (chunk_vertices, [new_triangle])
    new_chunks = dict()
    for key in chunks:
        (vertices_dict, triangles) = chunks[key]
        new_chunks[key] = (list(vertices_dict.keys()), triangles)
    return new_chunks


A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")


def flatten(xss: Iterable[Iterable[A]]) -> List[A]:
    """Flatten a list of lists"""
    return [x for xs in xss for x in xs]


def cat_maybes(xs: Iterable[Optional[A]]) -> List[A]:
    return [x for x in xs if x is not None]


def compose(f: Callable[[B], C], g: Callable[[A], B]) -> Callable[[A], C]:
    return lambda a: f(g(a))


def fold_compose(fs: Iterable[Callable[[A], A]]) -> Callable[[A], A]:
    return functools.reduce(compose, fs, lambda x: x)


def pairwise(iterable: Iterable[A]) -> Iterable[Tuple[A, A]]:
    """Yields a tuple containing the previous and current object.
    This is from blender source code."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def list_lookup(arr: List[A], i: int) -> Optional[A]:
    try:
        return arr[i]
    except IndexError:
        return None


def list_lookup_opt(arr: List[A], i: Optional[int]) -> Optional[A]:
    if i is None:
        return None
    return list_lookup(arr, i)


@dataclass
class KdTree(Generic[A]):
    left: KdTreeNode[A]
    right: KdTreeNode[A]

    @staticmethod
    def construct(
        k: int, points: List[Tuple[List[float], A]], max_children: int, depth: int = 0
    ) -> KdTree[List[A]]:
        """Construct a KdTree from a list of points.

        k
            Number of dimensions
        points
            A list of pairs of positions (represented as x,y,z.. list of k
            floats) and some value which ends up in the leaves.
        max_children
            The maximum number of children which end up in a single leaf.
        depth
            Current depth, leave as default.
        """
        axis: int = depth % k
        points.sort(key=lambda p: p[0][axis])
        halfway = len(points) // 2
        return KdTree(
            left=KdTreeNode.construct(k, points[:halfway], max_children, depth + 1),
            right=KdTreeNode.construct(k, points[halfway:], max_children, depth + 1),
        )

    def traverse(self, f: Callable[[A], B]) -> KdTree[B]:
        left = self.left.traverse(f)
        right = self.right.traverse(f)
        return KdTree(left, right)


@dataclass
class KdTreeNode(Generic[A]):
    value: Union[KdTree[A], A]

    @staticmethod
    def construct(
        k: int, points: List[Tuple[List[float], A]], max_children: int, depth: int = 0
    ) -> KdTreeNode[List[A]]:
        """Construct a KdTreeNode from a list of points.

        k
            Number of dimensions
        points
            A list of pairs of positions (represented as x,y,z.. list of k
            floats) and some value which ends up in the leaves.
        max_children
            The maximum number of children which end up in a single leaf.
        depth
            Current depth, leave as default.
        """
        if len(points) <= max_children:
            return KdTreeNode(value=list(map(lambda p: p[1], points)))
        else:
            return KdTreeNode(value=KdTree.construct(k, points, max_children, depth))

    def traverse(self, f: Callable[[A], B]) -> KdTreeNode[B]:
        if isinstance(self.value, KdTree):
            return KdTreeNode(self.value.traverse(f))
        else:
            return KdTreeNode(f(self.value))


@dataclass
class Key:
    """Unique ID used across animations, cameras, triggers, and interactive
    objects."""

    id: int

    def __hash__(self) -> int:
        return self.id.__hash__()


def compute_bounding_box_from_positions(
    pos: NumpyArray,
) -> AaBbBoundingBox:
    """Compute the bounding box of the given vertex positions.

    pos
        Numpy array of dtype vector3
    """
    if pos.dtype not in [dtypes.vector3, dtypes.vector3_lh]:
        raise errors.RBRAddonBug(
            f"compute_bounding_box_from_positions: bad dtype {pos.dtype}"
        )
    xzy = structured_to_unstructured(pos)
    min_pos = np.amin(xzy, axis=0)
    max_pos = np.amax(xzy, axis=0)
    return AaBbBoundingBox.from_min_max(
        min_pos=Vector3(
            x=min_pos[0],
            y=min_pos[1],
            z=min_pos[2],
        ),
        max_pos=Vector3(
            x=max_pos[0],
            y=max_pos[1],
            z=max_pos[2],
        ),
    )
