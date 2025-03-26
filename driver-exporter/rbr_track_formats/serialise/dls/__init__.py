from rbr_track_formats import errors
from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls import (
    DLSSection,
    DLS,
    DLS_HEADER,
)

from .animation_sets import animation_sets_to_binary
from .trigger_data import trigger_data_to_binary
from .splines import splines_to_binary
from .animation_cameras import animation_cameras_to_binary
from .track_emitters import track_emitters_to_binary
from .helicams import helicams_to_binary
from .sound_emitters import sound_emitters_to_binary
from .registration_zone import registration_zone_to_binary
from .animation_ids import animation_ids_to_binary
from .names import names_to_binary


def dls_to_binary(self: DLS) -> bytes:
    names = self.to_names()
    bin = PackBin()
    bin.pack_bytes(DLS_HEADER)
    addresses_offset = bin.offset
    bin.pack_bytes(bytes(40))
    for section, expected_addr in self.section_order:
        # These sections are aligned to 4 byte boundaries, so we pad accordingly.
        bin.pack_bytes(bytes((4 - bin.offset % 4) % 4))
        # Check that we are at the correct address if one is given
        if (
            expected_addr is not None
            and expected_addr != 0
            and expected_addr != 0xFFFFFFFF
        ):
            if bin.offset != expected_addr:
                raise errors.RBRAddonBug(
                    "DLS.to_binary: Writing section "
                    + section.name
                    + " at incorrect address, expected "
                    + hex(expected_addr)
                    + " but we are at "
                    + hex(bin.offset)
                )
        # Make a note of the current offset: we need to write this into the address object.
        address_to_write = bin.offset
        if section == DLSSection.ANIMATION_SETS:
            animation_sets_to_binary(self.animation_sets, names, bin)
        elif section == DLSSection.TRIGGER_DATA:
            trigger_data_to_binary(self.trigger_data, bin)
        elif section == DLSSection.SPLINES:
            splines_to_binary(self.splines, bin)
        elif section == DLSSection.ANIMATION_CAMERAS:
            animation_cameras_to_binary(self.animation_cameras, bin)
        elif section == DLSSection.TRACK_EMITTERS:
            track_emitters_to_binary(self.track_emitters, names, bin)
        elif section == DLSSection.HELICAMS:
            helicams_to_binary(self.helicams, names, bin)
        elif section == DLSSection.SOUND_EMITTERS:
            sound_emitters_to_binary(self.sound_emitters, bin)
        elif section == DLSSection.REGISTRATION_ZONE:
            if self.registration_zone is not None:
                registration_zone_to_binary(self.registration_zone, bin)
            else:
                address_to_write = 0xFFFFFFFF
        elif section == DLSSection.ANIMATION_IDS:
            animation_ids_to_binary(self.animation_ids, names, bin)
        elif section == DLSSection.ANIMATION_NAMES:
            names_to_binary(names, bin)
        else:
            raise errors.RBRAddonBug(
                "DLS to_binary: DLSSection not handled: " + section.name
            )
        # Write a pointer to the section we just added. Note that this is here
        # rather than before the section is written, because the finish line area
        # can be missing and the pointer must be 0xFFFFFFFF.
        bin.pack_at(addresses_offset + section.value * 4, "<I", address_to_write)
    return bin.bytes()
