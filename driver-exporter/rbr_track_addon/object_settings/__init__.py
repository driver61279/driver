import bpy  # type: ignore

from . import types


def register() -> None:
    from . import operator
    from . import panel

    bpy.utils.register_class(types.RBRObjectSettings)
    # A prop to hold the type directly as an int, updated when the type is
    # updated. This is used by the shader nodes.
    bpy.types.Object.rbr_object_type_value = bpy.props.IntProperty()
    bpy.types.Object.rbr_object_settings = bpy.props.PointerProperty(
        type=types.RBRObjectSettings,
    )
    bpy.utils.register_class(operator.RBR_OT_setup_object)
    bpy.utils.register_class(panel.RBR_PT_object_settings)


def unregister() -> None:
    from . import operator
    from . import panel

    bpy.utils.unregister_class(panel.RBR_PT_object_settings)
    bpy.utils.unregister_class(operator.RBR_OT_setup_object)
    del bpy.types.Object.rbr_object_settings
    del bpy.types.Object.rbr_object_type_value
    bpy.utils.unregister_class(types.RBRObjectSettings)
