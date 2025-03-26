from rbr_track_formats.binary import PackBin
from rbr_track_formats.common import Key
from rbr_track_formats.dls.trigger_data import (
    CardanAngles,
    TriggerDataItem,
    TriggerData,
)

from ..common import vector3_to_binary


def cardan_angles_to_binary(self: CardanAngles, bin: PackBin) -> None:
    bin.pack("<fff", self.pitch, self.roll, self.yaw)


def trigger_data_item_to_binary(self: TriggerDataItem, id: Key, bin: PackBin) -> None:
    if self.spline is None:
        spline_id = 0
        spline_group_id = 0
    else:
        spline_id = self.spline.id
        spline_group_id = self.spline.group_id
    bin.pack(
        "<IIII",
        id.id,
        id.id,
        spline_group_id,
        spline_id,
    )
    vector3_to_binary(self.position, bin)
    cardan_angles_to_binary(self.angles, bin)
    cardan_angles_to_binary(self.unused_angles, bin)
    bin.pack("<I", self.active)


def trigger_data_to_binary(self: TriggerData, bin: PackBin) -> None:
    bin.pack("<I", len(self.items))
    for id, item in self.items.items():
        trigger_data_item_to_binary(item, id, bin)
