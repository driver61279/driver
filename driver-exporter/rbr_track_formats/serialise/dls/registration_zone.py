from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls.registration_zone import RegistrationZone

from ..common import vector3_to_binary


def registration_zone_to_binary(self: RegistrationZone, bin: PackBin) -> None:
    vector3_to_binary(self.position, bin)
    bin.pack("<f", self.radius)
