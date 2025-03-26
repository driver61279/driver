from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.drive_points import DrivePoints

from ..common import vector3_to_binary


def drive_points_to_binary(self: DrivePoints, bin: PackBin) -> None:
    bin.pack("<I", len(self.points))
    for point in self.points:
        vector3_to_binary(point, bin)
