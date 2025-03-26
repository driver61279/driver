import enum
from typing import Optional, Set, Tuple

import bpy  # type: ignore

from rbr_track_formats.errors import Language


class DistStyle(enum.Enum):
    ORIGINAL = 0
    RSF = 1

    def pretty(self) -> str:
        if self is DistStyle.ORIGINAL:
            return "Original"
        elif self is DistStyle.RSF:
            return "RSF"

    def description(self) -> str:
        if self is DistStyle.ORIGINAL:
            return "Tracks share /Maps (Vanilla, TM, TrainingDay)"
        elif self is DistStyle.RSF:
            return "Tracks have separate folders in /Maps (RSF)"


class RBRExportDirectory(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(  # type: ignore
        name="Name",  # noqa: F821
    )
    directory: bpy.props.StringProperty(  # type: ignore
        name="RBR Maps Directory",  # noqa: F821
        subtype="DIR_PATH",  # noqa: F821
    )
    style: bpy.props.EnumProperty(  # type: ignore
        name="Style",  # noqa: F821
        items=[(x.name, x.pretty(), x.description(), x.value) for x in DistStyle],
        default=DistStyle.ORIGINAL.name,
    )


class RBR_OT_add_export_directory(bpy.types.Operator):
    bl_idname = "rbr.add_export_directory"
    bl_label = "Add RBR export directory"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        prefs = context.preferences.addons["rbr_track_addon"].preferences
        prefs.export_directories.add()
        return {"FINISHED"}


class RBR_OT_remove_export_directory(bpy.types.Operator):
    bl_idname = "rbr.remove_export_directory"
    bl_label = "Remove RBR export directory"
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty()  # type: ignore

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        prefs = context.preferences.addons["rbr_track_addon"].preferences
        prefs.export_directories.remove(self.index)
        return {"FINISHED"}


class RBRAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = "rbr_track_addon"

    export_directories: bpy.props.CollectionProperty(  # type: ignore
        type=RBRExportDirectory,
    )

    def get_export_directory(self, name: str) -> Optional[Tuple[str, DistStyle]]:
        for export_directory in self.export_directories:
            if export_directory.name == name:
                return (export_directory.directory, DistStyle[export_directory.style])
        return None

    language: bpy.props.EnumProperty(  # type: ignore
        name="Language",
        items=[(x.name, x.pretty(), x.pretty(), x.value) for x in Language],
        default=Language.EN.name,
    )

    def get_language(self) -> Language:
        return Language[self.language]

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.prop(self, "language")
        box = self.layout.box()
        box.operator(RBR_OT_add_export_directory.bl_idname)
        for i, export_directory in enumerate(self.export_directories):
            row = box.row()
            row.prop(export_directory, "name", text="")
            row.prop(export_directory, "directory", text="")
            row.prop(export_directory, "style", text="")
            remove = row.operator(
                RBR_OT_remove_export_directory.bl_idname, text="", icon="REMOVE"
            )
            remove.index = i


def register() -> None:
    bpy.utils.register_class(RBR_OT_remove_export_directory)
    bpy.utils.register_class(RBR_OT_add_export_directory)
    bpy.utils.register_class(RBRExportDirectory)
    bpy.utils.register_class(RBRAddonPreferences)


def unregister() -> None:
    bpy.utils.unregister_class(RBRAddonPreferences)
    bpy.utils.unregister_class(RBRExportDirectory)
    bpy.utils.unregister_class(RBR_OT_add_export_directory)
    bpy.utils.unregister_class(RBR_OT_remove_export_directory)
