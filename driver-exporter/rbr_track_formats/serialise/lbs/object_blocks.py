from rbr_track_formats import dtypes, errors
from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.common import (
    TrackObjectFlags,
)
from rbr_track_formats.lbs.object_blocks import (
    ObjectBlockLOD,
    ObjectBlock,
    ObjectBlockSegment,
    ObjectBlocks,
)

from ..common import aabb_bounding_box_to_binary
from .common import (
    render_state_flags_to_binary,
    track_object_flags_to_binary,
)


def object_block_lod_to_binary(self: ObjectBlockLOD, bin: PackBin) -> None:
    bin.pack("<B", self.value)


def object_block_to_binary(self: ObjectBlock, bin: PackBin) -> None:
    track_object_flags = TrackObjectFlags.HAS_RENDER_STATE
    if self.diffuse_texture_index_2 is not None:
        track_object_flags |= TrackObjectFlags.HAS_DOUBLE_TEXTURE
    elif self.diffuse_texture_index_1 is not None:
        track_object_flags |= TrackObjectFlags.HAS_SINGLE_TEXTURE
    track_object_flags_to_binary(track_object_flags, bin)
    render_state_flags_to_binary(self.render_state_flags, bin)
    if self.diffuse_texture_index_1 is not None:
        bin.pack("<I", self.diffuse_texture_index_1)
    if self.diffuse_texture_index_2 is not None:
        bin.pack("<I", self.diffuse_texture_index_2)
    bin.pack("<I", 0)
    bin.pack("<I", track_object_flags.vertex_size_sway_bytes())
    bin.pack("<I", self.fvf)
    if self.main_buffer.dtype != dtypes.triangle_indices:
        raise errors.RBRAddonBug(
            f"main buffer dtype is invalid: {self.main_buffer.dtype}"
        )
    bin.pack_length_prefixed_numpy_array(self.main_buffer, divisor=3)
    object_block_lod_to_binary(self.lod, bin)
    if self.far_buffer is not None:
        if self.far_buffer.dtype != dtypes.triangle_indices:
            raise errors.RBRAddonBug(
                f"far buffer dtype is invalid: {self.far_buffer.dtype}"
            )
        if self.lod is not ObjectBlockLOD.FAR_GEOMETRY_FROM_FAR_BUFFER:
            raise errors.RBRAddonBug(
                "FAR_GEOMETRY_FROM_FAR_BUFFER must be used with a far buffer"
            )
        bin.pack_length_prefixed_numpy_array(self.far_buffer, divisor=3)
    sway_dtypes = [
        dtypes.position_color_sway,
        dtypes.single_texture_sway,
        dtypes.double_texture_sway,
    ]
    if self.vertices.dtype not in sway_dtypes:
        raise errors.RBRAddonBug(f"vertices dtype is invalid: {self.vertices.dtype}")
    bin.pack_length_prefixed_numpy_array(self.vertices)
    aabb_bounding_box_to_binary(self.bounding_box, bin)


def object_block_segment_to_binary(self: ObjectBlockSegment, bin: PackBin) -> None:
    bin.pack("<I", len(self.blocks_1))
    for block in self.blocks_1:
        object_block_to_binary(block, bin)
    bin.pack("<I", len(self.blocks_2))
    for block in self.blocks_2:
        object_block_to_binary(block, bin)


def object_blocks_to_binary(self: ObjectBlocks, bin: PackBin) -> None:
    bin.pack("<I", len(self.blocks))
    for block in self.blocks:
        bin.pack("<I", 0 if block is None else 1)
        if block is not None:
            object_block_segment_to_binary(block, bin)
