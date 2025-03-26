import numpy as np
from numpy.lib.recfunctions import (
    structured_to_unstructured,
    unstructured_to_structured,
)

from rbr_track_formats import dtypes, errors
from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.geom_blocks import (
    Buffer,
    GeomBlock,
    GeomBlocks,
    RawGeomBlock,
    RenderChunkData,
    RenderType,
    type_to_pixel_shader,
    type_to_vertex_shader,
)

from ..common import aabb_bounding_box_to_binary
from .common import uv_velocity_to_binary


def render_chunk_data_to_binary(self: RenderChunkData, bin: PackBin) -> None:
    vertex_shader_id = type_to_vertex_shader(self.type, self.uv_velocity is not None)
    pixel_shader_id = type_to_pixel_shader(self.type)
    bin.pack(
        "<IIII",
        self.type.value,
        vertex_shader_id.value,
        pixel_shader_id.value,
        self.first_triangle_index * 3,
    )
    bin.pack("<III", self.num_triangles, self.num_vertices, self.first_vertex_index)
    aabb_bounding_box_to_binary(self.bounding_box, bin)
    is_shadow = 0 if self.shadow_texture_index is None else 1
    raw_shadow_texture_index = (
        0xFFFFFFFF if self.shadow_texture_index is None else self.shadow_texture_index
    )
    bin.pack(
        "<BBBBI",
        1,
        is_shadow,
        self.__garbage__.flag34_2,
        self.__garbage__.flag34_3,
        raw_shadow_texture_index,
    )
    is_specular = 0 if self.specular_texture_index is None else 1
    raw_specular_texture_index = (
        0xFFFFFFFF
        if self.specular_texture_index is None
        else self.specular_texture_index
    )
    bin.pack(
        "<BBBBI",
        is_specular,
        self.__garbage__.flag35_1,
        self.__garbage__.flag35_2,
        self.__garbage__.flag35_3,
        raw_specular_texture_index,
    )
    num_textures = 0
    if self.texture_index_1 is None:
        raw_texture_index_1 = 0xFFFFFFFF
    else:
        raw_texture_index_1 = self.texture_index_1
        num_textures += 1
    if self.texture_index_2 is None:
        raw_texture_index_2 = 0xFFFFFFFF
    else:
        raw_texture_index_2 = self.texture_index_2
        num_textures += 1
    bin.pack("<III", num_textures, raw_texture_index_1, raw_texture_index_2)
    use_uv_velocity = 0 if self.uv_velocity is None else 1
    bin.pack(
        "<BBBB",
        use_uv_velocity,
        self.__garbage__.shader_flag_0,
        self.__garbage__.shader_flag_1,
        self.__garbage__.shader_flag_2,
    )
    if self.uv_velocity is None:
        bin.pack("<ffffff", 0, 0, 0, 0, 0, 0)
    else:
        uv_velocity_to_binary(self.uv_velocity, bin)
    bin.pack(
        "<BBBB",
        self.chunk_distance.value,
        self.__garbage__.unknown_flags_1,
        self.__garbage__.unknown_flags_2,
        self.__garbage__.unknown_flags_3,
    )


def buffer_to_binary(self: Buffer, bin: PackBin) -> None:
    if self.triangles.dtype != dtypes.triangle_indices:
        raise errors.RBRAddonBug(f"triangles dtype is invalid: {self.triangles.dtype}")
    bin.pack_length_prefixed_numpy_array(self.triangles, divisor=3)
    vertex_dtypes = [
        dtypes.position_color,
        dtypes.single_texture,
        dtypes.single_texture_specular,
        dtypes.single_texture_shadow,
        dtypes.single_texture_specular_shadow,
        dtypes.double_texture,
        dtypes.double_texture_specular,
        dtypes.double_texture_shadow,
        dtypes.double_texture_specular_shadow,
    ]
    if self.vertices.dtype not in vertex_dtypes:
        raise errors.RBRAddonBug(f"vertices dtype is invalid: {self.vertices.dtype}")
    bin.pack_length_prefixed_numpy_array(self.vertices)


def raw_geom_block_to_binary(self: RawGeomBlock, bin: PackBin) -> None:
    buffer_to_binary(self.color_buffer, bin)
    buffer_to_binary(self.rl_single_texture_buffer, bin)
    buffer_to_binary(self.rl_single_texture_specular_buffer, bin)
    buffer_to_binary(self.rl_single_texture_shadow_buffer, bin)
    buffer_to_binary(self.rl_single_texture_specular_shadow_buffer, bin)
    buffer_to_binary(self.rl_double_texture_buffer, bin)
    buffer_to_binary(self.rl_double_texture_specular_buffer, bin)
    buffer_to_binary(self.rl_double_texture_shadow_buffer, bin)
    buffer_to_binary(self.rl_double_texture_specular_shadow_buffer, bin)
    bin.pack("<I", len(self.render_chunk_3d))
    for render_chunk_data in self.render_chunk_3d:
        render_chunk_data_to_binary(render_chunk_data, bin)
    aabb_bounding_box_to_binary(self.bounding_box, bin)


def geom_block_to_binary(self: GeomBlock, bin: PackBin) -> None:
    color_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.position_color),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    rl_single_texture_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.single_texture),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    rl_single_texture_specular_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.single_texture_specular),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    rl_single_texture_shadow_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.single_texture_shadow),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    rl_single_texture_specular_shadow_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.single_texture_specular_shadow),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    rl_double_texture_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.double_texture),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    rl_double_texture_specular_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.double_texture_specular),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    rl_double_texture_shadow_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.double_texture_shadow),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    rl_double_texture_specular_shadow_buffer: Buffer = Buffer(
        vertices=np.empty(0, dtype=dtypes.double_texture_specular_shadow),
        triangles=np.empty(0, dtype=dtypes.triangle_indices),
    )
    render_chunks = []
    for chunk in self.chunks:
        buffer: Buffer
        if chunk.type is RenderType.VERTEX_COLOR:
            buffer = color_buffer
        elif chunk.type is RenderType.SINGLE_TEXTURE:
            buffer = rl_single_texture_buffer
        elif chunk.type is RenderType.SINGLE_TEXTURE_SPECULAR:
            buffer = rl_single_texture_specular_buffer
        elif chunk.type is RenderType.SINGLE_TEXTURE_SHADOW:
            buffer = rl_single_texture_shadow_buffer
        elif chunk.type is RenderType.SINGLE_TEXTURE_SPECULAR_SHADOW:
            buffer = rl_single_texture_specular_shadow_buffer
        elif chunk.type is RenderType.DOUBLE_TEXTURE:
            buffer = rl_double_texture_buffer
        elif chunk.type is RenderType.DOUBLE_TEXTURE_SPECULAR:
            buffer = rl_double_texture_specular_buffer
        elif chunk.type is RenderType.DOUBLE_TEXTURE_SHADOW:
            buffer = rl_double_texture_shadow_buffer
        elif chunk.type is RenderType.DOUBLE_TEXTURE_SPECULAR_SHADOW:
            buffer = rl_double_texture_specular_shadow_buffer
        first_vertex_index = len(buffer.vertices)
        buffer.vertices = np.concatenate((buffer.vertices, chunk.vertices))
        first_triangle_index = len(buffer.triangles)
        unstructured_triangles = structured_to_unstructured(chunk.triangles)
        if not np.all(unstructured_triangles < len(chunk.vertices)):
            raise errors.RBRAddonBug("Triangle vertex index is out of bounds")
        rewritten = unstructured_to_structured(
            unstructured_triangles + first_vertex_index,
            dtype=dtypes.triangle_indices,
        )
        buffer.triangles = np.concatenate((buffer.triangles, rewritten))
        render_chunks.append(
            RenderChunkData(
                type=chunk.type,
                first_vertex_index=first_vertex_index,
                num_vertices=len(chunk.vertices),
                first_triangle_index=first_triangle_index,
                num_triangles=len(chunk.triangles),
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
    raw_geom_block_to_binary(
        RawGeomBlock(
            color_buffer=color_buffer,
            rl_single_texture_buffer=rl_single_texture_buffer,
            rl_single_texture_specular_buffer=rl_single_texture_specular_buffer,
            rl_single_texture_shadow_buffer=rl_single_texture_shadow_buffer,
            rl_single_texture_specular_shadow_buffer=rl_single_texture_specular_shadow_buffer,
            rl_double_texture_buffer=rl_double_texture_buffer,
            rl_double_texture_specular_buffer=rl_double_texture_specular_buffer,
            rl_double_texture_shadow_buffer=rl_double_texture_shadow_buffer,
            rl_double_texture_specular_shadow_buffer=rl_double_texture_specular_shadow_buffer,
            render_chunk_3d=render_chunks,
            bounding_box=self.bounding_box,
        ),
        bin,
    )


def geom_blocks_to_binary(self: GeomBlocks, bin: PackBin) -> None:
    bin.pack("<If", len(self.blocks), self.beckmann_glossiness)
    for block in self.blocks:
        geom_block_to_binary(block, bin)
