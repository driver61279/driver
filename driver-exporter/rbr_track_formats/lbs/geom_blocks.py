"""Geom blocks contain visual ground mesh data. The ground mesh consists of:
    - vertex colours
    - up to 2 diffuse textures
    - up to 1 specular textures
    - up to 1 shadow map
    The textures can also be animated. The ground is backface culled, i.e. is
    only visible from one side.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import enum

import numpy as np
from numpy.lib.recfunctions import (
    structured_to_unstructured,
    unstructured_to_structured,
)

from .. import errors
from ..common import AaBbBoundingBox, NumpyArray, Vector3
from .common import UVVelocity
from .. import dtypes


class VertexShaderID(enum.Enum):
    UNKNOWN_0x0 = 0x0
    OBJ_POS = 0x1
    OBJ_POSITION_COLOR_2_STREAMS = 0x2
    OBJ_POSITION_COLOR_TEXTURE_3_STREAMS = 0x3
    RL_SINGLE_TEXTURE_SHADOW = 0x4
    RL_DOUBLE_TEXTURE_0 = 0x5
    RL_DOUBLE_TEXTURE_SHADOW_0 = 0x6
    OBJ_POS_NORMAL = 0x7
    OBJ_POS_NORMAL_TEXTURE_COLOR = 0x8
    VERTEX_COLOR = 0x9
    RL_SINGLE_TEXTURE = 0xA
    RL_SINGLE_TEXTURE_SHADOW_2 = 0xB
    RL_DOUBLE_TEXTURE = 0xC
    RL_DOUBLE_TEXTURE_SHADOW = 0xD
    RL_SINGLE_TEXTURE_SPECULAR = 0xE
    RL_SINGLE_TEXTURE_SPECULAR_SHADOW = 0xF
    RL_DOUBLE_TEXTURE_SPECULAR = 0x10
    RL_DOUBLE_TEXTURE_SPECULAR_SHADOW = 0x11
    OBJ_POSITION_COLOR_TEXTURE = 0x12
    RL_SINGLE_TEXTURE_SWAY = 0x13
    RL_DOUBLE_TEXTURE_SWAY = 0x14
    RL_SINGLE_TEXTURE_ANIM = 0x15
    RL_SINGLE_TEXTURE_SHADOW_ANIM = 0x16
    RL_DOUBLE_TEXTURE_ANIM = 0x17
    RL_DOUBLE_TEXTURE_SHADOW_ANIM = 0x18
    RL_SINGLE_TEXTURE_SPECULAR_ANIM = 0x19
    RL_SINGLE_TEXTURE_SPECULAR_SHADOW_ANIM = 0x1A
    RL_DOUBLE_TEXTURE_SPECULAR_ANIM = 0x1B
    RL_DOUBLE_TEXTURE_SPECULAR_SHADOW_ANIM = 0x1C
    WATER_SINGLE_TEXTURE = 0x1D
    WATER_DOUBLE_TEXTURE = 0x1E
    UNKNOWN_0x1F = 0x1F
    UNKNOWN_0x20 = 0x20
    UNKNOWN_0x21 = 0x21
    SKY_DOME = 0x22
    CLOUDS_SINGLE_TEXTURE = 0x23
    CLOUDS_DOUBLE_TEXTURE = 0x24
    IO_SINGLE_TEXTURE = 0x25
    IO_DOUBLE_TEXTURE = 0x26
    OBJ_POS_NORMAL_TEXTURE_COLOR_FROM_FILE = 0x27
    OBJ_POS_NORMAL_TEXTURE_SHADOW = 0x28
    UNKNOWN_0x29 = 0x29
    CAR_PAINT_1 = 0x2A
    CAR_PAINT_INTERNAL = 0x2B
    GHOST_CAR = 0x2C
    CAR_TEXTURE = 0x2D
    CAR_TEXTURE_NO_DIRT = 0x2E
    CAR_GLASS = 0x2F
    CAR_GLASS_INTERNAL = 0x30
    CAR_RIM = 0x31
    CAR_PLASTIC = 0x32
    PARTICLE = 0x33


class PixelShaderID(enum.Enum):
    VERTEX_COLOR = 0x0
    RL_SINGLE_TEXTURE = 0x1
    RL_SINGLE_TEXTURE_SPECULAR = 0x2
    RL_SINGLE_TEXTURE_SHADOW = 0x3
    RL_SINGLE_TEXTURE_SPECULAR_SHADOW = 0x4
    RL_DOUBLE_TEXTURE = 0x5
    RL_DOUBLE_TEXTURE_SPECULAR = 0x6
    RL_DOUBLE_TEXTURE_SHADOW = 0x7
    RL_DOUBLE_TEXTURE_SPECULAR_SHADOW = 0x8
    WATER_SINGLE_TEXTURE = 0x9
    WATER_DOUBLE_TEXTURE = 0xA
    OBJ_POS_NORMAL_TEXTURE = 0xB
    UNKNOWN_0XC = 0xC
    CAR_PAINT_1 = 0xD
    CAR_PAINT_INTERNAL = 0xE
    UNKNOWN_0XF = 0xF
    CAR_TEXTURE = 0x10
    CAR_TEXTURE_NO_DIRT = 0x11
    CAR_GLASS = 0x12
    CAR_GLASS_INTERNAL = 0x13
    CAR_RIM = 0x14
    CAR_PLASTIC = 0x15
    PARTICLE = 0x16


class RenderType(enum.Enum):
    VERTEX_COLOR = 0x0
    SINGLE_TEXTURE = 0x1
    SINGLE_TEXTURE_SPECULAR = 0x2
    SINGLE_TEXTURE_SHADOW = 0x3
    SINGLE_TEXTURE_SPECULAR_SHADOW = 0x4
    DOUBLE_TEXTURE = 0x5
    DOUBLE_TEXTURE_SPECULAR = 0x6
    DOUBLE_TEXTURE_SHADOW = 0x7
    DOUBLE_TEXTURE_SPECULAR_SHADOW = 0x8

    def has_diffuse_1(self) -> bool:
        if self is RenderType.VERTEX_COLOR:
            return False
        return True

    def has_diffuse_2(self) -> bool:
        if self is RenderType.DOUBLE_TEXTURE:
            return True
        elif self is RenderType.DOUBLE_TEXTURE_SPECULAR:
            return True
        elif self is RenderType.DOUBLE_TEXTURE_SHADOW:
            return True
        elif self is RenderType.DOUBLE_TEXTURE_SPECULAR_SHADOW:
            return True
        return False

    def has_specular(self) -> bool:
        if self is RenderType.SINGLE_TEXTURE_SPECULAR:
            return True
        elif self is RenderType.DOUBLE_TEXTURE_SPECULAR:
            return True
        elif self is RenderType.SINGLE_TEXTURE_SPECULAR_SHADOW:
            return True
        elif self is RenderType.DOUBLE_TEXTURE_SPECULAR_SHADOW:
            return True
        return False

    def has_shadow(self) -> bool:
        if self is RenderType.SINGLE_TEXTURE_SHADOW:
            return True
        elif self is RenderType.DOUBLE_TEXTURE_SHADOW:
            return True
        elif self is RenderType.SINGLE_TEXTURE_SPECULAR_SHADOW:
            return True
        elif self is RenderType.DOUBLE_TEXTURE_SPECULAR_SHADOW:
            return True
        return False

    def to_double_texture(self) -> RenderType:
        """Convert a render type into something appropriate for RBR. RBR
        defines single texture shaders, but they are unfinished."""
        if self is RenderType.SINGLE_TEXTURE:
            return RenderType.DOUBLE_TEXTURE
        elif self is RenderType.SINGLE_TEXTURE_SPECULAR:
            return RenderType.DOUBLE_TEXTURE_SPECULAR
        elif self is RenderType.SINGLE_TEXTURE_SHADOW:
            return RenderType.DOUBLE_TEXTURE_SHADOW
        elif self is RenderType.SINGLE_TEXTURE_SPECULAR_SHADOW:
            return RenderType.DOUBLE_TEXTURE_SPECULAR_SHADOW
        else:
            return self


def type_to_vertex_shader(type: RenderType, anim: bool) -> VertexShaderID:
    if type == RenderType.VERTEX_COLOR:
        return VertexShaderID.VERTEX_COLOR
    elif type == RenderType.SINGLE_TEXTURE:
        if anim:
            return VertexShaderID.RL_SINGLE_TEXTURE_ANIM
        else:
            return VertexShaderID.RL_SINGLE_TEXTURE
    elif type == RenderType.SINGLE_TEXTURE_SPECULAR:
        if anim:
            return VertexShaderID.RL_SINGLE_TEXTURE_SPECULAR_ANIM
        else:
            return VertexShaderID.RL_SINGLE_TEXTURE_SPECULAR
    elif type == RenderType.SINGLE_TEXTURE_SHADOW:
        if anim:
            return VertexShaderID.RL_SINGLE_TEXTURE_SHADOW_ANIM
        else:
            return VertexShaderID.RL_SINGLE_TEXTURE_SHADOW
    elif type == RenderType.SINGLE_TEXTURE_SPECULAR_SHADOW:
        if anim:
            return VertexShaderID.RL_SINGLE_TEXTURE_SPECULAR_SHADOW_ANIM
        else:
            return VertexShaderID.RL_SINGLE_TEXTURE_SPECULAR_SHADOW
    elif type == RenderType.DOUBLE_TEXTURE:
        if anim:
            return VertexShaderID.RL_DOUBLE_TEXTURE_ANIM
        else:
            return VertexShaderID.RL_DOUBLE_TEXTURE
    elif type == RenderType.DOUBLE_TEXTURE_SPECULAR:
        if anim:
            return VertexShaderID.RL_DOUBLE_TEXTURE_SPECULAR_ANIM
        else:
            return VertexShaderID.RL_DOUBLE_TEXTURE_SPECULAR
    elif type == RenderType.DOUBLE_TEXTURE_SHADOW:
        if anim:
            return VertexShaderID.RL_DOUBLE_TEXTURE_SHADOW_ANIM
        else:
            return VertexShaderID.RL_DOUBLE_TEXTURE_SHADOW
    elif type == RenderType.DOUBLE_TEXTURE_SPECULAR_SHADOW:
        if anim:
            return VertexShaderID.RL_DOUBLE_TEXTURE_SPECULAR_SHADOW_ANIM
        else:
            return VertexShaderID.RL_DOUBLE_TEXTURE_SPECULAR_SHADOW
    else:
        raise NotImplementedError("type_to_vertex_shader: " + type.name)


def type_to_pixel_shader(type: RenderType) -> PixelShaderID:
    if type == RenderType.VERTEX_COLOR:
        return PixelShaderID.VERTEX_COLOR
    elif type == RenderType.SINGLE_TEXTURE:
        return PixelShaderID.RL_SINGLE_TEXTURE
    elif type == RenderType.SINGLE_TEXTURE_SPECULAR:
        return PixelShaderID.RL_SINGLE_TEXTURE_SPECULAR
    elif type == RenderType.SINGLE_TEXTURE_SHADOW:
        return PixelShaderID.RL_SINGLE_TEXTURE_SHADOW
    elif type == RenderType.SINGLE_TEXTURE_SPECULAR_SHADOW:
        return PixelShaderID.RL_SINGLE_TEXTURE_SPECULAR_SHADOW
    elif type == RenderType.DOUBLE_TEXTURE:
        return PixelShaderID.RL_DOUBLE_TEXTURE
    elif type == RenderType.DOUBLE_TEXTURE_SPECULAR:
        return PixelShaderID.RL_DOUBLE_TEXTURE_SPECULAR
    elif type == RenderType.DOUBLE_TEXTURE_SHADOW:
        return PixelShaderID.RL_DOUBLE_TEXTURE_SHADOW
    elif type == RenderType.DOUBLE_TEXTURE_SPECULAR_SHADOW:
        return PixelShaderID.RL_DOUBLE_TEXTURE_SPECULAR_SHADOW
    else:
        raise NotImplementedError("type_to_pixel_shader: " + type.name)


class RenderChunkDistance(enum.Enum):
    """Render chunks are classified into these three categories. They provide
    a simple LOD system for ground geometry.

    NEAR
        High quality mesh, displayed when the camera is within 600m of the
        chunk. Native tracks put everything within the brakewall into this
        category.
    ANY
        Chunk is visible from any distance. Don't include high detail geometry
        here. Native tracks put all geometry which exists outside the brakewall
        into this category, because it doesn't need to be high detail.
    FAR
        Low quality mesh, displayed when the camera is further than 550m away
        from the chunk. This should contain a low poly version of the NEAR
        geometry.
    """

    NEAR = 1
    ANY = 2
    FAR = 3

    def pretty(self) -> str:
        if self is RenderChunkDistance.NEAR:
            return "Near"
        elif self is RenderChunkDistance.ANY:
            return "Any"
        elif self is RenderChunkDistance.FAR:
            return "Far"

    def description(self) -> str:
        if self is RenderChunkDistance.NEAR:
            return "Mesh is visible within 600m (high resolution mesh, used to generate collision mesh)"
        elif self is RenderChunkDistance.ANY:
            return "Mesh is visible from any distance (mid-low resolution mesh)"
        elif self is RenderChunkDistance.FAR:
            return "Mesh is not visible within 550m (very low resolution version of 'Near' mesh)"


@dataclass
class RenderChunkGarbage:
    """A type for helping keep track of garbage in render chunk data.
    We need to keep track of this for roundtripping.
    """

    flag34_2: int = 0
    flag34_3: int = 0
    flag35_1: int = 0
    flag35_2: int = 0
    flag35_3: int = 0
    shader_flag_0: int = 0
    shader_flag_1: int = 0
    shader_flag_2: int = 0
    unknown_flags_1: int = 0
    unknown_flags_2: int = 0
    unknown_flags_3: int = 0


@dataclass
class TransformedRenderChunkData:
    """RenderChunkData without awkward offsets. Instead the vertex and triangle
    data is packed in this type."""

    type: RenderType
    vertices: NumpyArray
    triangles: NumpyArray
    bounding_box: AaBbBoundingBox
    texture_index_1: Optional[int]
    texture_index_2: Optional[int]
    specular_texture_index: Optional[int]
    shadow_texture_index: Optional[int]
    chunk_distance: RenderChunkDistance
    uv_velocity: Optional[UVVelocity]
    __garbage__: RenderChunkGarbage = RenderChunkGarbage()


@dataclass
class RenderChunkData:
    """A list of this class is in each GeomBlock. This contains offsets into
    the buffers, ultimately describing a piece of the mesh and the material
    properties it should have. The buffer to take vertices and primitives from
    is specified by the type field, which also specifies the shader to use.

    type
        The type of mesh (shader type). The buffer used is chosen according to
        this value.
    first_triangle_index
        Index of the first triangle in the buffer.
    num_triangles
        Number of triangles in this chunk.
    first_vertex_index
        Index of the first vertex in the buffer.
    num_vertices
        Number of vertices in this chunk.
    bounding_box
        The axis aligned bounding box surrounding this chunk geometry.
    texture_index_1
        Index of the first diffuse texture (defined by the INI file)
    texture_index_2
        Index of the second diffuse texture (defined by the INI file)
    specular_texture_index
        Index of the specular texture (defined by the INI file)
    shadow_texture_index
        Index of the shadow texture (defined by the INI file)
    chunk_distance
        Distance of this chunk (from the road). Used when deciding how far away
        geometry can be before we stop rendering it.
        TODO investigate this more
    uv_velocity
        Controls UV animation for each texture
    """

    type: RenderType
    first_triangle_index: int
    num_triangles: int
    first_vertex_index: int
    num_vertices: int
    bounding_box: AaBbBoundingBox
    texture_index_1: Optional[int]
    texture_index_2: Optional[int]
    specular_texture_index: Optional[int]
    shadow_texture_index: Optional[int]
    chunk_distance: RenderChunkDistance
    uv_velocity: Optional[UVVelocity]
    __garbage__: RenderChunkGarbage = RenderChunkGarbage()


@dataclass
class Buffer:
    triangles: NumpyArray  # dtypes.triangle_indices
    vertices: NumpyArray  # dtypes.[non sway shader]


@dataclass
class RawGeomBlock:
    color_buffer: Buffer
    rl_single_texture_buffer: Buffer
    rl_single_texture_specular_buffer: Buffer
    rl_single_texture_shadow_buffer: Buffer
    rl_single_texture_specular_shadow_buffer: Buffer
    rl_double_texture_buffer: Buffer
    rl_double_texture_specular_buffer: Buffer
    rl_double_texture_shadow_buffer: Buffer
    rl_double_texture_specular_shadow_buffer: Buffer
    render_chunk_3d: List[RenderChunkData]
    bounding_box: AaBbBoundingBox

    def normalize_chunks(self) -> List[TransformedRenderChunkData]:
        transformed = []
        for chunk in self.render_chunk_3d:
            buffer: Buffer
            if chunk.type is RenderType.VERTEX_COLOR:
                buffer = self.color_buffer
            elif chunk.type is RenderType.SINGLE_TEXTURE:
                buffer = self.rl_single_texture_buffer
            elif chunk.type is RenderType.SINGLE_TEXTURE_SPECULAR:
                buffer = self.rl_single_texture_specular_buffer
            elif chunk.type is RenderType.SINGLE_TEXTURE_SHADOW:
                buffer = self.rl_single_texture_shadow_buffer
            elif chunk.type is RenderType.SINGLE_TEXTURE_SPECULAR_SHADOW:
                buffer = self.rl_single_texture_specular_shadow_buffer
            elif chunk.type is RenderType.DOUBLE_TEXTURE:
                buffer = self.rl_double_texture_buffer
            elif chunk.type is RenderType.DOUBLE_TEXTURE_SPECULAR:
                buffer = self.rl_double_texture_specular_buffer
            elif chunk.type is RenderType.DOUBLE_TEXTURE_SHADOW:
                buffer = self.rl_double_texture_shadow_buffer
            elif chunk.type is RenderType.DOUBLE_TEXTURE_SPECULAR_SHADOW:
                buffer = self.rl_double_texture_specular_shadow_buffer
            vertices = buffer.vertices[
                chunk.first_vertex_index : chunk.first_vertex_index + chunk.num_vertices
            ]
            triangles = buffer.triangles[
                chunk.first_triangle_index : chunk.first_triangle_index
                + chunk.num_triangles
            ]
            unstructured_triangles = (
                structured_to_unstructured(triangles) - chunk.first_vertex_index
            )
            if not np.all(unstructured_triangles < chunk.num_vertices):
                raise errors.RBRAddonBug(
                    "normalize_chunks has triangle vertex out of bounds"
                )
            triangles = unstructured_to_structured(
                unstructured_triangles,
                dtype=dtypes.triangle_indices,
            )
            transformed.append(
                TransformedRenderChunkData(
                    type=chunk.type,
                    vertices=vertices,
                    triangles=triangles,
                    bounding_box=chunk.bounding_box,
                    texture_index_1=chunk.texture_index_1,
                    texture_index_2=chunk.texture_index_2,
                    specular_texture_index=chunk.specular_texture_index,
                    shadow_texture_index=chunk.shadow_texture_index,
                    chunk_distance=chunk.chunk_distance,
                    uv_velocity=chunk.uv_velocity,
                    __garbage__=chunk.__garbage__,
                )
            )
        return transformed


@dataclass
class GeomBlock:
    """A GeomBlock is a chunk of the world's static visual mesh. It is split
    into parts according to materials, this is described by the elements in
    render_chunk_3d. Each element uses a slice of a particular buffer type.

    The single texture buffers should generally not be used. The reason the
    native stages don't use them is that some of them have shaders which are
    unfinished and only output solid red pixels!
    """

    chunks: List[TransformedRenderChunkData]
    bounding_box: AaBbBoundingBox

    @staticmethod
    def create_empty() -> GeomBlock:
        return GeomBlock(
            chunks=[],
            bounding_box=AaBbBoundingBox(
                position=Vector3(0, 0, 0),
                size=Vector3(0, 0, 0),
            ),
        )


@dataclass
class GeomBlocks:
    """GeomBlocks specify the world' static visual mesh. The world is split
    into square chunks, and those chunks are elements in the 'blocks' list.
    """

    beckmann_glossiness: float
    blocks: List[GeomBlock]
