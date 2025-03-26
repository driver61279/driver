import math
from typing import Dict, List, Optional, Tuple

import bpy  # type: ignore

from rbr_track_formats.common import Key, Vector3
from rbr_track_formats.dls.animation_cameras import (
    AnimCameraMode,
    LookAtMode,
    AnimationCamera,
    AnimationCameras,
)
from rbr_track_formats.dls.animation_sets import (
    SectionChannel,
    SigTriggerData,
    TriggerKind,
    RealChannel,
)
from rbr_track_formats.dls.splines import Splines, Spline, SplineControlPoint
from rbr_track_formats.dls.trigger_data import (
    CardanAngles,
    SplineIDs,
    TriggerData,
    TriggerDataItem,
)

from rbr_track_addon.blender_ops import TracedObject
import rbr_track_addon.blender_ops as ops
from rbr_track_addon.driveline import ensure_longest_spline, walk_cubic_bezier_segment
from rbr_track_formats.logger import Logger
from rbr_track_addon.object_settings.types import RBRObjectSettings
from rbr_track_addon.util import (
    fcurve_real_channel,
    focal_length_to_hfov_degrees,
)

from ..util import KeyGen


def export_cameras(
    logger: Logger,
    keygen: KeyGen,
    traced_objs: List[TracedObject],
) -> Tuple[
    AnimationCameras,
    TriggerData,
    List[SigTriggerData],
    List[SectionChannel],
    List[RealChannel],
    Splines,
]:
    animation_cameras: Dict[Key, AnimationCamera] = dict()
    trigger_data: Dict[Key, TriggerDataItem] = dict()
    camera_to_key: Dict[str, Key] = dict()
    real_channels: List[RealChannel] = []
    splines_to_export: Dict[SplineIDs, TracedObject] = dict()

    for traced_obj in traced_objs:
        obj = traced_obj.obj
        if not isinstance(obj.data, bpy.types.Camera):
            continue
        object_settings: RBRObjectSettings = obj.rbr_object_settings
        camera = obj.data

        look_at = LookAtMode.FIXED
        if object_settings.camera_look_at_car:
            look_at = LookAtMode.CAR

        key = keygen.new_key()
        camera_to_key[obj.name] = key
        animation_cameras[key] = AnimationCamera(
            look_at=look_at,
            fov=camera.angle / math.pi * 180,
            shake=object_settings.camera_shake,
            mode=AnimCameraMode[object_settings.camera_mode],
            znear=camera.clip_start,
        )

        # Position animation (typically helicam)
        spline_ids = None
        for constraint in obj.constraints:
            if constraint.type != "FOLLOW_PATH":
                continue
            target = constraint.target
            [dupe] = ops.duplicate_objects([TracedObject.create(target)])
            ops.apply_transforms([dupe])
            spline_and_length = ensure_longest_spline(dupe.obj)
            if spline_and_length is None:
                logger.warn(
                    f"Camera {obj.name} is marked to follow the path of non-spline object {target.name}, skipping path animation"
                )
                continue
            (spline, spline_length) = spline_and_length
            spline_ids = SplineIDs(
                len(splines_to_export) + 1,
                len(splines_to_export) + 1,
            )
            splines_to_export[spline_ids] = dupe
            if tuple(obj.location) != (0, 0, 0):
                logger.warn(
                    f"Camera {obj.name} has follow path constraint but non-zero location"
                )

            def path_duration_to_length(x: float) -> float:
                """Convert path duration relative value to length relative value"""
                y: float = -x / target.data.path_duration * spline_length
                return y

            real_channel = fcurve_real_channel(
                logger=logger,
                key=key,
                kind=TriggerKind.POSITION_FROM_SPLINE,
                obj=obj,
                prop=f'constraints["{constraint.name}"].offset',
                default=False,
                fixup_val=path_duration_to_length,
            )
            if real_channel is None:
                logger.warn(
                    f"Real channel not created for follow path constraint of {obj.name}"
                )
            else:
                real_channels.append(real_channel)
                break

        (euler_x, euler_y, euler_z) = tuple(obj.rotation_euler)
        trigger_data[key] = TriggerDataItem(
            spline=spline_ids,
            position=Vector3(
                x=obj.location.x,
                y=obj.location.y,
                z=obj.location.z,
            ),
            angles=CardanAngles(
                pitch=90 - euler_x * 180 / math.pi,
                roll=euler_y * 180 / math.pi,
                yaw=-euler_z * 180 / math.pi,
            ),
            active=True,
        )

        # FOV animation
        real_channel = fcurve_real_channel(
            logger=logger,
            key=key,
            kind=TriggerKind.ANIMATION_CAMERA_FOV,
            obj=camera,
            prop="lens",
            default=False,
            fixup_val=lambda l: focal_length_to_hfov_degrees(l, camera.sensor_width),
        )
        if real_channel is not None:
            real_channels.append(real_channel)

    sig_trigger_data: List[SigTriggerData] = []
    section_channels: List[SectionChannel] = []

    markers = sorted(bpy.context.scene.timeline_markers, key=lambda m: m.frame)
    for marker in markers:
        if marker.camera is None:
            continue
        try:
            key = camera_to_key[marker.camera.name]
        except KeyError:
            logger.warn(f"Marker for {marker.camera} has no key, skipping")
            continue
        location = float(marker.frame)

        sig_trigger_data_index = len(sig_trigger_data)
        sig_trigger_data.append(
            SigTriggerData(
                id=key,
                kind=TriggerKind.REPLAY_CAMERA_CHANGE,
            )
        )

        section_channels.append(
            SectionChannel(
                sig_trigger_data_index=sig_trigger_data_index,
                location=location,
                is_exit=False,
            )
        )
        section_channels.append(
            SectionChannel(
                sig_trigger_data_index=sig_trigger_data_index,
                # See comment in SectionChannel documentation.
                location=location + 1,
                is_exit=True,
            )
        )

    splines = export_splines(logger, splines_to_export)

    return (
        AnimationCameras(cameras=animation_cameras),
        TriggerData(items=trigger_data),
        sig_trigger_data,
        section_channels,
        real_channels,
        splines,
    )


def export_spline(
    logger: Logger,
    spline_ids: SplineIDs,
    dupes: List[TracedObject],
) -> Optional[Spline]:
    ops.apply_transforms(dupes)
    obj = dupes[0]
    spline_and_length = ensure_longest_spline(obj.obj)
    if spline_and_length is None:
        logger.warn(f"Object marked as spline is not a spline: {obj.source_name()}")
        return None
    (spline, length) = spline_and_length
    points = []
    last_bezier_point = None
    location = 0
    for bezier_point in spline.bezier_points:
        pos = Vector3.from_tuple(bezier_point.co)
        left = Vector3.from_tuple(bezier_point.handle_left)
        right = Vector3.from_tuple(bezier_point.handle_right)
        if last_bezier_point is not None:
            (length, _) = walk_cubic_bezier_segment(
                bsp0=last_bezier_point,
                bsp1=bezier_point,
                distance_along_segment=0,
            )
            location += length
        last_bezier_point = bezier_point
        points.append(
            SplineControlPoint(
                position=pos,
                tangent_end=(left - pos).scale(3),
                tangent_start=(right - pos).scale(3),
                anim_value=location,
            )
        )
    return Spline(
        id=spline_ids.id,
        group=spline_ids.group_id,
        points=points,
    )


def export_splines(
    logger: Logger,
    spline_objs: Dict[SplineIDs, TracedObject],
) -> Splines:
    splines: List[Spline] = []
    for spline_ids, original_obj in spline_objs.items():
        dupes = ops.duplicate_objects([original_obj])
        spline = export_spline(
            logger=logger,
            spline_ids=spline_ids,
            dupes=dupes,
        )
        if spline is not None:
            splines.append(spline)

    return Splines(splines=splines)
