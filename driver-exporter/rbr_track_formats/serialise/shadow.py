from rbr_track_formats.binary import PackBin
from rbr_track_formats.shadow import ShadowDAT


def shadow_dat_to_binary(self: ShadowDAT) -> bytes:
    bin = PackBin()
    bin.pack("<II", self.width, self.height)
    for row in self.bitmap:
        for s in row:
            bin.pack("<B", s)
    return bin.bytes()
