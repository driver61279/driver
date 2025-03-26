from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.super_bowl import (
    SuperBowlObject,
    SuperBowl,
)

from ..common import vector3_to_binary
from .common import object_data_3d_to_binary


def super_bowl_object_to_binary(self: SuperBowlObject, bin: PackBin) -> None:
    vector3_to_binary(self.position, bin)
    object_data_3d_to_binary(self.data_3d, bin)


def super_bowl_to_binary(self: SuperBowl, bin: PackBin) -> None:
    bin.pack_null_terminated_string(self.name)
    bin.pack("<I", len(self.objects))
    for obj in self.objects:
        super_bowl_object_to_binary(obj, bin)
