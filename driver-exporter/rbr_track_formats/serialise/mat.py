from rbr_track_formats import errors
from rbr_track_formats.binary import PackBin
from rbr_track_formats.mat import (
    ConditionIdentifier,
    MAT,
    MaterialID,
    MaterialMap,
)


def material_id_to_binary(self: MaterialID, bin: PackBin) -> None:
    bin.pack("<B", self.value)


def material_map_to_binary(self: MaterialMap, bin: PackBin) -> None:
    bin.pack("<II", 16, 16)
    for row in self.bitmap:
        for v in row:
            material_id_to_binary(v, bin)


def condition_identifier_to_binary(self: ConditionIdentifier, bin: PackBin) -> None:
    identifier = self.name
    identifier += " "
    identifier += self.surface_type.to_string()
    identifier += " "
    identifier += self.surface_age.to_string()
    bin.pack_null_terminated_string(identifier)


def mat_to_binary(self: MAT) -> bytes:
    bin = PackBin()
    bin.pack("<I", len(self.conditions))
    for identifier, material_maps in self.conditions.items():
        condition_identifier_to_binary(identifier, bin)
        if len(material_maps) > 256:
            raise errors.E0158(num_maps=len(material_maps))
        bin.pack("<I", len(material_maps))
        for material_map in material_maps:
            material_map_to_binary(material_map, bin)
    if self.__wallaby_stuff__ is not None:
        bin.pack_bytes(self.__wallaby_stuff__)
    return bin.bytes()
