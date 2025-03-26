from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls.names import Names, NameOffset


def name_offset_to_binary(self: NameOffset, bin: PackBin) -> None:
    bin.pack("<I", self.offset)


def names_pack_name_offset(self: Names, name: str, bin: PackBin) -> None:
    for offset, name_ in self.names.items():
        if name == name_:
            name_offset_to_binary(offset, bin)
            return
    raise IndexError


def names_to_binary(self: Names, bin: PackBin) -> None:
    start = bin.offset
    bin.pack("<I", 0)
    for name in self.names.values():
        bin.pack_bytes(name.encode("latin1"))
        bin.pack_bytes(bytes(1))
    bin.pack_bytes(bytes(1))
    end = bin.offset
    bin.pack_at(start, "<I", end - start - 4)
