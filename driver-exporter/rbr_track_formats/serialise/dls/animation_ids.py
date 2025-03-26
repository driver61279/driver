from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls.animation_ids import AnimationIDs
from rbr_track_formats.dls.names import Names

from ..common import key_to_binary
from .names import names_pack_name_offset


def animation_ids_to_binary(self: AnimationIDs, names: Names, bin: PackBin) -> None:
    bin.pack("<I", len(self.items))
    for anim_id, name in self.items.items():
        key_to_binary(anim_id, bin)
        names_pack_name_offset(names, name, bin)
