from rbr_track_formats.binary import PackBin
from rbr_track_formats.common import (
    AaBbBoundingBox,
    Key,
    Matrix4x4,
    Vector2,
    Vector3,
    Vector4,
)


def vector2_to_binary(self: Vector2, bin: PackBin) -> None:
    bin.pack("<ff", self.x, self.y)


def vector3_to_binary(self: Vector3, bin: PackBin) -> None:
    bin.pack("<fff", self.x, self.y, self.z)


def vector4_to_binary(self: Vector4, bin: PackBin) -> None:
    bin.pack("<ffff", self.x, self.y, self.z, self.w)


def matrix4x4_to_binary(self: Matrix4x4, bin: PackBin) -> None:
    vector4_to_binary(self.x, bin)
    vector4_to_binary(self.y, bin)
    vector4_to_binary(self.z, bin)
    vector4_to_binary(self.w, bin)


def aabb_bounding_box_to_binary(self: AaBbBoundingBox, bin: PackBin) -> None:
    vector3_to_binary(self.position, bin)
    vector3_to_binary(self.size, bin)


def key_to_binary(self: Key, bin: PackBin) -> None:
    bin.pack("<I", self.id)
