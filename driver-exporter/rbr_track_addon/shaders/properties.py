import bpy  # type: ignore

RBR_COLOR_EXPORT_LAYER: str = "RBR_COLOR_EXPORT"
RBR_ALPHA_EXPORT_LAYER: str = "RBR_ALPHA_EXPORT"


class RBRGlobalShaderFlags(bpy.types.PropertyGroup):
    """A property group for communicating with shader nodes.
    Used for changing shader node behaviour to aid debugging.
    """

    def __update_shading_type__(self, context: bpy.types.Context) -> None:
        bpy.ops.rbr.refresh_shaders()
        bpy.context.scene.rbr_track_settings.update_sky_values()

    realtime_displacement: bpy.props.BoolProperty(  # type: ignore
        name="Realtime Displacement",
        description="Display displacement in viewport (cycles only, slow)",
        default=False,
        update=__update_shading_type__,
    )
    only_display_color: bpy.props.BoolProperty(  # type: ignore
        name="Only Display Color",
        default=False,
        update=__update_shading_type__,
    )
    only_display_alpha: bpy.props.BoolProperty(  # type: ignore
        name="Only Display Alpha",
        default=False,
        update=__update_shading_type__,
    )

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
        layout.prop(self, "realtime_displacement")
        layout.prop(self, "only_display_color")
        layout.prop(self, "only_display_alpha")


class RBR_PT_global_shader_flags(bpy.types.Panel):
    bl_idname = "RBR_PT_global_shader_flags"
    bl_label = "RBR Shader Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context: bpy.types.Context) -> None:
        context.scene.rbr_global_shader_flags.draw(context, self.layout)


def register() -> None:
    bpy.utils.register_class(RBRGlobalShaderFlags)
    bpy.types.Scene.rbr_global_shader_flags = bpy.props.PointerProperty(
        type=RBRGlobalShaderFlags,
    )
    bpy.utils.register_class(RBR_PT_global_shader_flags)


def unregister() -> None:
    bpy.utils.unregister_class(RBR_PT_global_shader_flags)
    del bpy.types.Scene.rbr_global_shader_flags
    bpy.utils.unregister_class(RBRGlobalShaderFlags)
