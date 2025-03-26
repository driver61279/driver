import bpy  # type: ignore

from .operator import RBR_OT_setup_object


class RBR_PT_object_settings(bpy.types.Panel):
    bl_idname = "RBR_PT_object_settings"
    bl_label = "RBR Object Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        obj.rbr_object_settings.draw(context, layout)
        layout.separator()
        if RBR_OT_setup_object.poll(context):
            layout.operator(RBR_OT_setup_object.bl_idname)
