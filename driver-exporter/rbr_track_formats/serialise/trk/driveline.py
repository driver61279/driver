from rbr_track_formats.binary import PackBin
from rbr_track_formats.trk.driveline import DrivelinePoint, Driveline

from ..common import vector3_to_binary


def driveline_point_to_binary(self: DrivelinePoint, bin: PackBin) -> None:
    vector3_to_binary(self.position, bin)
    vector3_to_binary(self.direction, bin)
    bin.pack("<fHH", self.location, 0, 0)


def driveline_to_binary(self: Driveline, bin: PackBin) -> None:
    bin.pack("<I", len(self.points))
    for point in self.points:
        driveline_point_to_binary(point, bin)
