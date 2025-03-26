from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.clipping_planes import ClippingPlanes
from rbr_track_formats import dtypes, errors


def clipping_planes_to_binary(self: ClippingPlanes, bin: PackBin) -> None:
    if self.directional_planes.dtype != dtypes.triangle_indices:
        raise errors.RBRAddonBug(
            f"directional_planes dtype is invalid: {self.directional_planes.dtype}"
        )
    bin.pack_length_prefixed_numpy_array(self.directional_planes)
    if self.omnidirectional_planes.dtype != dtypes.triangle_indices:
        raise errors.RBRAddonBug(
            f"omnidirectional_planes dtype is invalid: {self.omnidirectional_planes.dtype}"
        )
    bin.pack_length_prefixed_numpy_array(self.omnidirectional_planes)
    if self.vertices.dtype != dtypes.vector3_lh:
        raise errors.RBRAddonBug(f"vertices dtype is invalid: {self.vertices.dtype}")
    bin.pack_length_prefixed_numpy_array(self.vertices)
