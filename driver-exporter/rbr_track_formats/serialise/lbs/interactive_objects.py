from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.interactive_objects import (
    Instance,
    InteractiveObject,
    InteractiveObjects,
)

from ..common import key_to_binary, matrix4x4_to_binary
from .common import object_data_3d_to_binary


def instance_to_binary(self: Instance, bin: PackBin) -> None:
    key_to_binary(self.key, bin)
    matrix4x4_to_binary(self.transformation_matrix, bin)


def interactive_object_to_binary(self: InteractiveObject, bin: PackBin) -> None:
    bin.pack_null_terminated_string(self.name)
    bin.pack(
        "<BI",
        self.object_kind.value if self.object_kind is not None else 0,
        len(self.data_3d),
    )
    for data_3d in self.data_3d:
        object_data_3d_to_binary(data_3d, bin)
    bin.pack("<I", len(self.instances))
    for instance in self.instances:
        instance_to_binary(instance, bin)


def interactive_objects_to_binary(self: InteractiveObjects, bin: PackBin) -> None:
    bin.pack("<I", len(self.objects))
    for obj in self.objects:
        interactive_object_to_binary(obj, bin)
