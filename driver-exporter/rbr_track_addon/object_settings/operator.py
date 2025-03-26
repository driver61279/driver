from typing import Set

import bpy  # type: ignore

from ..driveline import fixup_driveline, setup_zfar
from .types import (
    RBRObjectSettings,
    RBRObjectType,
)


class RBR_OT_setup_object(bpy.types.Operator):
    """Setup some RBR object"""

    bl_idname = "rbr.setup_object"
    bl_label = "Setup object"
    bl_description = "Adjust this object to have any necessary properties"
    bl_options = {"UNDO"}

    @classmethod
    def poll(_cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None:
            return False
        object_settings: RBRObjectSettings = obj.rbr_object_settings
        object_type: RBRObjectType = RBRObjectType[object_settings.type]
        return any(
            [
                object_type is RBRObjectType.DRIVELINE,
                object_type is RBRObjectType.ZFAR,
            ]
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        return self.invoke(context, None)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        obj = context.active_object
        if obj is None:
            return {"FINISHED"}
        object_settings: RBRObjectSettings = obj.rbr_object_settings
        object_type: RBRObjectType = RBRObjectType[object_settings.type]
        if object_type is RBRObjectType.DRIVELINE:
            fixup_driveline(obj, full_fixup=True)
        elif object_type is RBRObjectType.ZFAR:
            setup_zfar(obj)
        return {"FINISHED"}
