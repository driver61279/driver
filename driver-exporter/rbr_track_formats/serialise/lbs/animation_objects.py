from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.animation_objects import (
    AnimationObject,
    AnimationObjects,
    RGBAColor,
)
from rbr_track_formats.serialise.common import vector3_to_binary


def rgba_color_to_binary(self: RGBAColor, bin: PackBin) -> None:
    bin.pack("<BBBB", self.b, self.g, self.r, self.a)


def animation_object_to_binary(self: AnimationObject, bin: PackBin) -> None:
    bin.pack_null_terminated_string(self.name)
    bin.pack("<III", self.animation_id, self.randomised, self.container_id)
    bin.pack_null_terminated_string(self.lua_load_script_name)
    bin.pack_null_terminated_string(self.lua_run_script_name)
    vector3_to_binary(self.position, bin)
    vector3_to_binary(self.rotation, bin)
    vector3_to_binary(self.scale, bin)
    vector3_to_binary(self.car_position, bin)
    vector3_to_binary(self.light, bin)
    rgba_color_to_binary(self.color, bin)


def animation_objects_to_binary(self: AnimationObjects, bin: PackBin) -> None:
    bin.pack("<I", len(self.objects))
    for obj in self.objects:
        animation_object_to_binary(obj, bin)
