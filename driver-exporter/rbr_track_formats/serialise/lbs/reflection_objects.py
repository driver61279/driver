from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.reflection_objects import (
    ReflectionObject,
    ReflectionObjects,
)

from .common import object_data_3d_to_binary


def reflection_object_to_binary(self: ReflectionObject, bin: PackBin) -> None:
    bin.pack_null_terminated_string(self.name)
    bin.pack("<BI", 0, len(self.data_3d))
    for data_3d in self.data_3d:
        object_data_3d_to_binary(data_3d, bin)


def reflection_objects_to_binary(self: ReflectionObjects, bin: PackBin) -> None:
    bin.pack("<I", len(self.objects))
    for obj in self.objects:
        reflection_object_to_binary(obj, bin)
