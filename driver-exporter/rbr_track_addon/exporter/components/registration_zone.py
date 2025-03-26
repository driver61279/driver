from typing import List, Optional

from rbr_track_formats.common import Vector3
from rbr_track_formats.dls.registration_zone import RegistrationZone

from rbr_track_addon.blender_ops import TracedObject


def export_registration_zone(
    traced_objs: List[TracedObject],
) -> Optional[RegistrationZone]:
    if len(traced_objs) == 0:
        return None
    zone_obj = traced_objs[0].obj
    (sx, sy, sz) = zone_obj.scale
    max_scale = max(sx, sy, sz)
    radius = zone_obj.empty_display_size
    return RegistrationZone(
        position=Vector3.from_tuple(zone_obj.location),
        radius=radius * max_scale,
    )
