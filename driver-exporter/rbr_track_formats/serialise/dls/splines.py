from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls.splines import (
    Interpolation,
    SplineControlPoint,
    Spline,
    Splines,
)

from ..common import vector3_to_binary


HIGH_COUNT: int = 10000


def interpolation_to_binary(self: Interpolation, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def spline_control_point_to_binary(self: SplineControlPoint, bin: PackBin) -> None:
    interpolation_to_binary(Interpolation.CUBIC_HERMITE, bin)
    vector3_to_binary(self.position, bin)
    vector3_to_binary(self.tangent_end, bin)
    vector3_to_binary(self.tangent_start, bin)
    bin.pack("<f", self.anim_value)


def spline_to_binary(self: Spline, bin: PackBin) -> None:
    # assert len(self.points) >= 2
    bin.pack("<III", self.group, self.id, len(self.points))
    for point in self.points:
        spline_control_point_to_binary(point, bin)


def splines_to_binary(self: Splines, bin: PackBin) -> None:
    bin.pack("<I", len(self.splines))
    for spline in self.splines:
        spline_to_binary(spline, bin)
