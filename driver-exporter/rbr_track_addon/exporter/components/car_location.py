from typing import List

from rbr_track_formats import errors
from rbr_track_formats.common import Vector3
from rbr_track_formats.lbs.car_location import CarLocation

from rbr_track_addon.blender_ops import (
    apply_modifiers,
    apply_visual_transforms,
    duplicate_objects,
    TracedObject,
)
from rbr_track_formats.logger import Logger


def export_car_location(
    logger: Logger,
    traced_objs: List[TracedObject],
) -> CarLocation:
    try:
        original = traced_objs[0]
    except IndexError:
        raise errors.E0106()
    if len(traced_objs) > 1:
        logger.warn(
            "Found multiple car location objects, using the first ({original.source_name()})"
        )

    dupes = duplicate_objects([original])

    if len(dupes) != 1:
        raise errors.RBRAddonBug("Duplicate returned != 1 car location object")
    traced_obj = dupes[0]
    traced_obj.obj.name = "EXPORT Car Location"
    apply_modifiers(traced_obj)
    # Applying visual transform in order to capture constraints.
    apply_visual_transforms([traced_obj])
    # No purpose except to make the object look correct if cleanup is off.
    traced_obj.obj.constraints.clear()
    # Export
    (x, y, z) = traced_obj.obj.location
    traced_obj.obj.rotation_mode = "AXIS_ANGLE"
    (angle, axis_x, axis_y, axis_z) = traced_obj.obj.rotation_axis_angle
    return CarLocation(
        position=Vector3(x, z, y),
        euler_vector=Vector3(axis_x, axis_z, axis_y).scale(-angle),
    )
