from typing import List

import bpy  # type: ignore

from rbr_track_formats import errors
from rbr_track_formats.common import Key
from rbr_track_formats.dls.animation_sets import (
    RealChannel,
    TriggerKind,
)

from rbr_track_addon.blender_ops import TracedObject
from rbr_track_formats.logger import Logger

from rbr_track_addon.util import fcurve_real_channel, constant_channel


def is_valid_zfar_obj(obj: bpy.types.Object) -> bool:
    return obj.data is None and obj.empty_display_type == "CIRCLE"


DEFAULT_ZFAR: float = 300


def export_zfar(
    logger: Logger,
    traced_objs: List[TracedObject],
    traced_driveline_obj: TracedObject,
) -> RealChannel:
    """Get the render distance object and export anything we can. Doesn't fail
    hard, just defaults where possible.
    """
    traced_obj = None
    if len(traced_objs) > 1:
        raise errors.E0131(num_zfar_objects=len(traced_objs))
    try:
        traced_obj = traced_objs[0]
    except IndexError:
        logger.warn(f"Defaulting render distance to constant {DEFAULT_ZFAR}m")
        return RealChannel(
            id=Key(0),
            kind=TriggerKind.ZFAR,
            control_points=constant_channel(DEFAULT_ZFAR),
        )
    obj = traced_obj.obj
    driveline_obj = traced_driveline_obj.obj
    if obj.parent != driveline_obj:
        raise errors.E0132()
    if obj.data is not None:
        raise errors.E0133()
    scale: float = sum(obj.scale) / 3
    real_channel = fcurve_real_channel(
        logger=logger,
        key=Key(0),
        kind=TriggerKind.ZFAR,
        obj=obj,
        prop="empty_display_size",
        fixup_val=lambda x: x * scale,
    )
    if real_channel is None:
        return RealChannel(
            id=Key(0),
            kind=TriggerKind.ZFAR,
            control_points=constant_channel(obj.empty_display_size),
        )
    else:
        return real_channel
