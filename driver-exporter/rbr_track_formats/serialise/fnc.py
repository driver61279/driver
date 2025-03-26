from rbr_track_formats.binary import PackBin
from rbr_track_formats.fnc import (
    FencePost,
    FNC,
    FenceData,
    FenceType,
    BGRAColor,
)

from .common import vector3_to_binary, aabb_bounding_box_to_binary


def fence_type_to_binary(self: FenceType, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def rgba_color_to_binary(self: BGRAColor, bin: PackBin) -> None:
    bin.pack("<BBBB", self.b, self.g, self.r, self.a)


def fence_post_to_binary(self: FencePost, bin: PackBin) -> None:
    vector3_to_binary(self.position, bin)
    aabb_bounding_box_to_binary(self.bounding_box, bin)
    rgba_color_to_binary(self.color, bin)


def fence_data_to_binary(self: FenceData, bin: PackBin) -> None:
    bin.pack("<I", len(self.fence_posts))
    fence_type_to_binary(self.tile_type, bin)
    fence_type_to_binary(self.pole_type, bin)
    bin.pack("<II", self.tile_texture_index, self.pole_texture_index)
    aabb_bounding_box_to_binary(self.bounding_box, bin)
    for obj in self.fence_posts:
        fence_post_to_binary(obj, bin)


def fnc_to_binary(self: FNC) -> bytes:
    bin = PackBin()
    bin.pack("<II", 2, len(self.fences))
    for fence in self.fences:
        fence_data_to_binary(fence, bin)
    bin.pack("<II", len(self.textures), 0x20)
    for i, texture in enumerate(self.textures):
        before = bin.offset
        bin.pack_null_terminated_string(texture.value)
        after = bin.offset
        try:
            garbage = self.__textures_garbage__[i]
        except IndexError:
            garbage = b""
        extra_garbage = b"0" * (0x20 - (after - before) - len(garbage))
        bin.pack_bytes(extra_garbage)
        bin.pack_bytes(garbage)
    return bin.bytes()
