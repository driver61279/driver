from typing import List, Optional

from rbr_track_formats import errors
from rbr_track_formats.common import Vector3
from rbr_track_formats.dls.animation_sets import (
    Pacenote,
    PacenoteFlags,
    PacenoteID,
)
from rbr_track_formats.trk.driveline import (
    Driveline,
    DrivelinePoint,
    cubic_hermite_segment_length,
    check_segment_is_well_formed,
)

from rbr_track_addon.driveline import (
    ensure_longest_spline,
    fixup_driveline,
    RBRDrivelineSettings,
)

from rbr_track_formats.logger import Logger
from rbr_track_addon.blender_ops import (
    apply_modifiers,
    apply_transforms,
    make_local,
    make_data_single_user,
    duplicate_objects,
    TracedObject,
)


def compute_stage_length(traced_driveline_obj: TracedObject) -> float:
    driveline_obj = traced_driveline_obj.obj
    driveline: RBRDrivelineSettings = driveline_obj.rbr_driveline_settings
    start: Optional[float] = None
    finish: Optional[float] = None
    for pacenote in driveline.pacenotes:
        pacenote_id = PacenoteID[pacenote.pacenote_id]
        if pacenote_id is PacenoteID.EVENT_START:
            start = pacenote.location
        elif pacenote_id is PacenoteID.EVENT_FINISH:
            finish = pacenote.location
    if start is not None and finish is not None:
        return (finish - start) / 1000
    return 0.0


def export_pacenotes(traced_driveline_obj: TracedObject) -> List[Pacenote]:
    driveline_obj = traced_driveline_obj.obj
    driveline: RBRDrivelineSettings = driveline_obj.rbr_driveline_settings
    pacenotes = []
    for pacenote in driveline.pacenotes:
        pacenotes.append(
            Pacenote(
                id=PacenoteID[pacenote.pacenote_id],
                flags=PacenoteFlags.NONE,
                location=pacenote.location,
            )
        )
    return pacenotes


def export_driveline(
    logger: Logger,
    traced_objs: List[TracedObject],
) -> Driveline:
    driveline_objs = duplicate_objects(traced_objs=traced_objs)

    if len(driveline_objs) != 1:
        raise errors.E0134(num_objects=len(driveline_objs))
    traced_driveline_obj = driveline_objs[0]
    driveline_obj = traced_driveline_obj.obj
    # Un-link the data first, _then_ unlink the object
    make_data_single_user(traced_driveline_obj)
    make_local([traced_driveline_obj])
    apply_transforms([traced_driveline_obj])
    apply_modifiers(traced_driveline_obj)
    fixup_driveline(driveline_obj, full_fixup=True)
    spline_and_len = ensure_longest_spline(driveline_obj)
    if spline_and_len is None:
        raise errors.E0135(driveline_name=traced_driveline_obj.source_name())
    (spline, _) = spline_and_len
    if spline.type != "BEZIER":
        raise errors.E0135(driveline_name=traced_driveline_obj.source_name())
    MAX_DRIVELINE_POINTS: int = 10000
    if len(spline.bezier_points) > MAX_DRIVELINE_POINTS:
        raise errors.E0136(
            max_points=MAX_DRIVELINE_POINTS, num_points=len(spline.bezier_points)
        )
    driveline_points = []
    last_position_and_direction = None
    location = 0
    for point_index, point in enumerate(spline.bezier_points):
        position = Vector3.from_tuple(point.co)
        direction = (Vector3.from_tuple(point.handle_right) - position).scale(3)
        direction_left = (Vector3.from_tuple(point.handle_left) - position).scale(3)
        # This should be okay due to the earlier call to fixup_driveline
        if (direction + direction_left).length() > 0.1:
            raise errors.RBRAddonBug(
                f"Driveline spline handles do not match for point {point_index-1}:\n"
                + f"  Left direction: {direction_left}\n"
                + f"  Right direction: {direction}\n"
                + "The handles must be equal length and in opposite directions. An easy way to ensure this is to use the 'auto' handle type, and only manipulate the bezier point with translate/rotate/scale rather than manipulating the handles directly."
            )

        if last_position_and_direction is not None:
            (last_position, last_direction) = last_position_and_direction
            well_formed = check_segment_is_well_formed(
                A=last_position,
                a=last_direction,
                B=position,
                b=direction,
            )
            if not well_formed:
                raise errors.E0137(
                    position=last_position.to_tuple(),
                )

            location += cubic_hermite_segment_length(
                last_position,
                last_direction,
                position,
                direction,
            )
        last_position_and_direction = (position, direction)
        driveline_points.append(
            DrivelinePoint(
                position=position,
                direction=direction,
                location=location,
            )
        )
    return Driveline(points=driveline_points)
