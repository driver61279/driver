from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.container_objects import (
    ContainerObject,
    ContainerObjects,
)


def container_object_to_binary(self: ContainerObject, bin: PackBin) -> None:
    bin.pack_null_terminated_string(self.name)
    bin.pack("<III", self.container_id, self.flag.value, self.random_upper_bound)


def container_objects_to_binary(self: ContainerObjects, bin: PackBin) -> None:
    bin.pack("<I", len(self.objects))
    for obj in self.objects:
        container_object_to_binary(obj, bin)
