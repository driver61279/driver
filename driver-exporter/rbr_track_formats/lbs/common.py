"""Common types for the LBS file.
"""

from __future__ import annotations
from dataclasses import dataclass
import enum
from typing import Optional

from ..common import NumpyArray, Vector2


class RenderStateFlags(enum.Flag):
    """Extra options which control rendering settings.

    NO_CULLING
        Disable backface culling
    UNKNOWN_*
        Some stages have these set. They don't seem to do anything.
    TEXTURE_ADDRESS_MODE_U_CLAMP
        Don't repeat the texture in the U direction. Just use the colour at the
        edge of the texture.
    TEXTURE_ADDRESS_MODE_V_CLAMP
        Don't repeat the texture in the V direction. Just use the colour at the
        edge of the texture.
    TEXTURE_ADDRESS_MODE_U_MIRROR
        Repeat the texture in the U direction, but also mirror it.
    TEXTURE_ADDRESS_MODE_V_MIRROR
        Repeat the texture in the V direction, but also mirror it.
    """

    NO_CULLING = 0x1
    UNKNOWN_0x2 = 0x2
    UNKNOWN_0x4 = 0x4
    UNKNOWN_0x8 = 0x8
    TEXTURE_ADDRESS_MODE_U_CLAMP = 0x10
    TEXTURE_ADDRESS_MODE_V_CLAMP = 0x20
    TEXTURE_ADDRESS_MODE_U_MIRROR = 0x40
    TEXTURE_ADDRESS_MODE_V_MIRROR = 0x80


class TrackObjectFlags(enum.Flag):
    # Yes, this is meant to be 0b101.
    HAS_RENDER_STATE = 0x5
    HAS_SINGLE_TEXTURE = 0x10
    HAS_DOUBLE_TEXTURE = 0x20
    # Yes, this is meant to be 0x42. Its possible that one bit represents
    # 'normal' and one represents 'specular', but it just so happens that only
    # specular objects have normals.
    HAS_SPECULAR_TEXTURE = 0x42
    HAS_SHADER_DATA = 0x80

    def vertex_size_bytes(self) -> int:
        """Vertex size for normal objects"""
        s = 3 * 4  # Position
        s += 4  # Colour
        if bool(self & TrackObjectFlags.HAS_SINGLE_TEXTURE):
            s += 2 * 4  # UV
        if bool(self & TrackObjectFlags.HAS_DOUBLE_TEXTURE):
            s += 2 * 4  # UV
        if bool(self & TrackObjectFlags.HAS_SPECULAR_TEXTURE):
            s += 2 * 4  # UV
            s += 3 * 4  # Normal
            s += 4  # Strength
        return s

    def vertex_size_sway_bytes(self) -> int:
        """Vertex size for swaying objects"""
        sway = 3 * 4  # Contribution from sway parameters
        return self.vertex_size_bytes() + sway


class D3DFVF(enum.Flag):
    """The minimum set of flags we need to import RBR tracks.
    https://docs.microsoft.com/en-us/windows/win32/direct3d9/d3dfvf

    This is enough to import default tracks, but Wallaby puts all kinds of
    values there, so we don't even use this type. Also, the game doesn't
    actually use the fvf data.

    The developers might have used the fixed function pipeline at first and
    switched to programmable shaders, but neglected removing this from the
    tracks.
    """

    XYZ = 0x0002
    NORMAL = 0x0010
    DIFFUSE = 0x0040
    SPECULAR = 0x0080
    TEX1 = 0x0100
    TEX2 = 0x0200


@dataclass
class UVVelocity:
    """Properties controlling animated textures. Each vector specifies the
    UV velocity for animation, in UV space.

    Note that we're using Vector2, so the uniforms are specified by x and y,
    but the shader positions are actually y and z.
    """

    diffuse_1: Vector2
    diffuse_2: Vector2
    specular: Vector2

    @staticmethod
    def zeros() -> UVVelocity:
        return UVVelocity(
            diffuse_1=Vector2(0, 0),
            diffuse_2=Vector2(0, 0),
            specular=Vector2(0, 0),
        )


@dataclass
class ObjectData3D:
    # Options for rendering this block
    render_state_flags: RenderStateFlags
    diffuse_texture_index_1: Optional[int]
    diffuse_texture_index_2: Optional[int]
    specular_texture_index: Optional[int]
    uv_velocity: Optional[UVVelocity]
    triangles: NumpyArray
    vertices: NumpyArray
    # This is only to aid roundtripping maps. We don't bother trying to
    # construct this correctly ourselves, because it isn't used.
    fvf: int = 0
