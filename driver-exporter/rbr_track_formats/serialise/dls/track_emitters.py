from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls.track_emitters import TrackEmitter, TrackEmitters
from rbr_track_formats.dls.names import Names

from ..common import key_to_binary
from .names import names_pack_name_offset


def track_emitter_to_binary(self: TrackEmitter, names: Names, bin: PackBin) -> None:
    names_pack_name_offset(names, self.name, bin)
    key_to_binary(self.trigger_id, bin)
    bin.pack("<f", self.distance_squared)


def track_emitters_to_binary(self: TrackEmitters, names: Names, bin: PackBin) -> None:
    bin.pack("<I", len(self.items))
    for item in self.items:
        track_emitter_to_binary(item, names, bin)
