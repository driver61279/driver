from rbr_track_formats import errors
from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.common import (
    D3DFVF,
    ObjectData3D,
    RenderStateFlags,
    TrackObjectFlags,
    UVVelocity,
)
from rbr_track_formats import dtypes

from ..common import vector2_to_binary


def render_state_flags_to_binary(self: RenderStateFlags, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def track_object_flags_to_binary(self: TrackObjectFlags, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def d3dfvf_to_binary(self: D3DFVF, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def uv_velocity_to_binary(self: UVVelocity, bin: PackBin) -> None:
    vector2_to_binary(self.diffuse_1, bin)
    vector2_to_binary(self.diffuse_2, bin)
    vector2_to_binary(self.specular, bin)


def object_data_3d_to_binary(self: ObjectData3D, bin: PackBin) -> None:
    track_object_flags = TrackObjectFlags.HAS_RENDER_STATE
    if self.diffuse_texture_index_1 is not None:
        track_object_flags |= TrackObjectFlags.HAS_SINGLE_TEXTURE
    if self.diffuse_texture_index_2 is not None:
        if self.diffuse_texture_index_1 is None:
            raise errors.E0092()
        track_object_flags |= TrackObjectFlags.HAS_DOUBLE_TEXTURE
    if self.specular_texture_index is not None:
        if self.diffuse_texture_index_1 is None:
            raise errors.E0093()
        track_object_flags |= TrackObjectFlags.HAS_SPECULAR_TEXTURE
    if self.uv_velocity is not None:
        track_object_flags |= TrackObjectFlags.HAS_SHADER_DATA
    track_object_flags_to_binary(track_object_flags, bin)
    render_state_flags_to_binary(self.render_state_flags, bin)
    if self.diffuse_texture_index_1 is not None:
        bin.pack("<I", self.diffuse_texture_index_1)
        if self.uv_velocity is not None:
            vector2_to_binary(self.uv_velocity.diffuse_1, bin)
    if self.diffuse_texture_index_2 is not None:
        bin.pack("<I", self.diffuse_texture_index_2)
        if self.uv_velocity is not None:
            vector2_to_binary(self.uv_velocity.diffuse_2, bin)
    if self.specular_texture_index is not None:
        bin.pack("<I", self.specular_texture_index)
        if self.uv_velocity is not None:
            vector2_to_binary(self.uv_velocity.specular, bin)
    bin.pack("<I", track_object_flags.vertex_size_bytes())
    bin.pack("<I", self.fvf)
    if self.triangles.dtype != dtypes.triangle_indices:
        raise errors.RBRAddonBug(f"triangles dtype is invalid: {self.triangles.dtype}")
    bin.pack_length_prefixed_numpy_array(self.triangles, divisor=3)
    vertex_dtypes = [
        dtypes.position_color,
        dtypes.single_texture,
        dtypes.single_texture_specular,
        dtypes.double_texture,
        dtypes.double_texture_specular,
    ]
    if self.vertices.dtype not in vertex_dtypes:
        raise errors.RBRAddonBug(f"vertices dtype is invalid: {self.vertices.dtype}")
    bin.pack_length_prefixed_numpy_array(self.vertices)
