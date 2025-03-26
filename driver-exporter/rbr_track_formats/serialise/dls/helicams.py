from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls.helicams import Helicam, Helicams
from rbr_track_formats.dls.names import Names

from ..common import key_to_binary
from .names import names_pack_name_offset


def helicam_to_binary(self: Helicam, names: Names, bin: PackBin) -> None:
    key_to_binary(self.id, bin)
    names_pack_name_offset(names, self.name, bin)
    bin.pack(
        "<fIfff",
        self.unknown_3,
        self.unknown_4,
        self.unknown_5,
        self.unknown_6,
        self.unknown_7,
    )


def helicams_to_binary(self: Helicams, names: Names, bin: PackBin) -> None:
    bin.pack("<I", len(self.items))
    for item in self.items:
        helicam_to_binary(item, names, bin)
