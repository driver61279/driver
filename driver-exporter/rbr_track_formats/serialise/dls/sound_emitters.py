from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls.sound_emitters import SoundEmitter, SoundEmitters

from ..common import vector3_to_binary


def sound_emitter_to_binary(self: SoundEmitter, bin: PackBin) -> None:
    vector3_to_binary(self.position, bin)
    bin.pack("<f", self.radius)


def sound_emitters_to_binary(self: SoundEmitters, bin: PackBin) -> None:
    bin.pack("<I", len(self.items))
    for item in self.items:
        sound_emitter_to_binary(item, bin)
