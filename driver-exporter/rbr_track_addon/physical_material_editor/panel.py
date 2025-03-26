import bpy  # type: ignore

from .operator import RBR_OT_edit_material_maps
from .. import materials


class RBR_PT_physical_material_editor(bpy.types.Panel):
    bl_idname = "RBR_PT_physical_material_editor"
    bl_label = "RBR Material Map Editor"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context: bpy.types.Context) -> None:
        ui = self.layout

        if RBR_OT_edit_material_maps.handle is not None:
            ui.label(text="Material Map Transparency")
            ui.prop(context.scene.rbr_material_picker, "alpha", slider=True)
            ui.label(text="Material Palette")
            context.scene.rbr_material_picker.draw(context, ui)
        else:
            ui.label(text="Launch the editor from your texture node")


def register() -> None:
    materials.register()
    bpy.utils.register_class(RBR_PT_physical_material_editor)


def unregister() -> None:
    bpy.utils.unregister_class(RBR_PT_physical_material_editor)
    materials.unregister()
