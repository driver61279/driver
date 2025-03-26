from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.water_objects import WaterObject, WaterObjects

from .common import object_data_3d_to_binary


def water_object_to_binary(self: WaterObject, bin: PackBin) -> None:
    bin.pack_null_terminated_string(self.name)
    bin.pack("<BI", 0, len(self.data_3d))
    for data_3d in self.data_3d:
        object_data_3d_to_binary(data_3d, bin)


def water_objects_to_binary(self: WaterObjects, bin: PackBin) -> None:
    bin.pack("<I", len(self.objects))
    for obj in self.objects:
        water_object_to_binary(obj, bin)
