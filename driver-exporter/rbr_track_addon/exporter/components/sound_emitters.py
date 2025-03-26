from typing import List

from rbr_track_formats.common import Vector3
from rbr_track_formats.dls.sound_emitters import SoundEmitter, SoundEmitters

from rbr_track_addon.blender_ops import TracedObject


def export_sound_emitters(traced_objs: List[TracedObject]) -> SoundEmitters:
    sound_emitters = []
    for traced_obj in traced_objs:
        obj = traced_obj.obj
        (sx, sy, sz) = obj.scale
        max_scale = max(sx, sy, sz)
        radius = obj.empty_display_size
        sound_emitters.append(
            SoundEmitter(
                position=Vector3.from_tuple(obj.location),
                radius=radius * max_scale,
            )
        )
    return SoundEmitters(items=sound_emitters)
