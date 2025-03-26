import bpy  # type: ignore

bl_info = {
    "name": "RBR Track Addon",
    "description": "Importer / exporter for RBR's native track format",
    "version": (0, 3, 1),  # Don't forget to update migrations!
    "blender": (4, 0, 0),
    "author": "Tom Smalley, WorkerBee (reverse engineering)",
    "url": "https://github.com/RichardBurnsRally/blender-rbr-track-addon",
    "tracker_url": "https://github.com/RichardBurnsRally/blender-rbr-track-addon/issues",
    "category": "Import-Export",
}

from . import driveline  # noqa: E402
from . import object_settings  # noqa: E402
from . import physical_material_editor  # noqa: E402
from . import shaders  # noqa: E402
from . import textures  # noqa: E402
from . import track_settings  # noqa: E402
from . import exporter  # noqa: E402
from . import preferences  # noqa: E402

try:
    from . import importer  # noqa: E402
except ImportError:
    # The importer might not be included in the addon.
    pass


# Modules to register, in order
modules = [
    object_settings,
    driveline,
    physical_material_editor,
    track_settings,
    textures,
    shaders,
]


def migrate_ios_from_scm() -> None:
    for obj in bpy.data.objects:
        if obj.rbr_object_settings.type == "INTERACTIVE_OBJECTS":
            kind = obj.rbr_object_settings.interactive_object_kind
            for child in obj.children:
                if child.rbr_object_settings.type == "SHAPE_COLLISION_MESH":
                    child.rbr_object_settings.type = "INTERACTIVE_OBJECTS_COLMESH"
                    child.rbr_object_settings.interactive_object_kind = kind


@bpy.app.handlers.persistent  # type: ignore
def load_post_handler(
    scene: bpy.types.Scene,
    depsgraph: bpy.types.Depsgraph,
) -> None:
    # Run a migration between addon versions
    current_version = bl_info["version"]
    iteration = 0
    while bpy.context.scene.rbr_addon_version != str(current_version):
        version = bpy.context.scene.rbr_addon_version
        # If the file was pre-auto-migration, the version will be blank
        if version == "":
            # This did refresh shaders but a subsequent shader rewrite made it irrelevant
            bpy.context.scene.rbr_addon_version = str((0, 1, 12))
        elif version == str((0, 1, 12)):
            # Nothing needs doing for this bump
            bpy.context.scene.rbr_addon_version = str((0, 1, 13))
        elif version == str((0, 1, 13)):
            # Nothing needs doing for this bump
            bpy.context.scene.rbr_addon_version = str((0, 1, 14))
        elif version == str((0, 1, 14)):
            # Major shader rewrite
            shaders.migrate_split_shaders()
            bpy.context.scene.rbr_addon_version = str((0, 1, 15))
        elif version == str((0, 1, 15)):
            # Nothing to do, just bug fixes
            bpy.context.scene.rbr_addon_version = str((0, 1, 16))
        elif version == str((0, 1, 16)):
            # Nothing to do, just bug fixes
            bpy.context.scene.rbr_addon_version = str((0, 1, 17))
        elif version == str((0, 1, 17)):
            bpy.ops.rbr.refresh_shaders()
            bpy.context.scene.rbr_track_settings.update_sky_values()
            bpy.context.scene.rbr_addon_version = str((0, 1, 18))
        elif version == str((0, 1, 18)):
            # Large restructuring, small changes otherwise
            bpy.context.scene.rbr_addon_version = str((0, 1, 19))
        elif version == str((0, 1, 19)):
            # Removal of texture socket
            bpy.ops.rbr.refresh_shaders()
            bpy.context.scene.rbr_track_settings.update_sky_values()
            bpy.context.scene.rbr_addon_version = str((0, 1, 20))
        elif version == str((0, 1, 20)):
            bpy.context.scene.rbr_addon_version = str((0, 1, 21))
        elif version == str((0, 1, 21)):
            bpy.context.scene.rbr_addon_version = str((0, 1, 22))
        elif version == str((0, 1, 22)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 0))
        elif version == str((0, 2, 0)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 1))
        elif version == str((0, 2, 1)):
            track_settings.migrate_world_weathers()
            bpy.ops.rbr.refresh_shaders()
            bpy.context.scene.rbr_addon_version = str((0, 2, 2))
        elif version == str((0, 2, 2)):
            migrate_ios_from_scm()
            bpy.context.scene.rbr_addon_version = str((0, 2, 3))
        elif version == str((0, 2, 3)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 4))
        elif version == str((0, 2, 4)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 5))
        elif version == str((0, 2, 5)):
            bpy.ops.rbr.refresh_shaders()
            bpy.context.scene.rbr_track_settings.update_world_context(bpy.context)
            bpy.context.scene.rbr_addon_version = str((0, 2, 6))
        elif version == str((0, 2, 6)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 7))
        elif version == str((0, 2, 7)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 8))
        elif version == str((0, 2, 8)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 9))
        elif version == str((0, 2, 9)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 10))
        elif version == str((0, 2, 10)):
            bpy.context.scene.rbr_addon_version = str((0, 2, 11))
        elif version == str((0, 2, 11)):
            bpy.context.scene.rbr_addon_version = str((0, 3, 0))
        elif version == str((0, 3, 0)):
            bpy.context.scene.rbr_addon_version = str((0, 3, 1))
        elif version == str(current_version):
            # current version, stop trying to find migrations
            if iteration > 0:
                print("RBR Addon: reached migration target")
            break
        else:
            print(
                f"RBR Addon: unexpected version '{version}' in file, skipping migrations"
            )
            bpy.context.scene.rbr_addon_version = str(current_version)
            break
        iteration += 1


def register() -> None:
    preferences.register()
    for module in modules:
        module.register()
    bpy.types.Scene.rbr_addon_version = bpy.props.StringProperty(
        name="RBR Addon Version",  # noqa: F821
    )
    bpy.app.handlers.load_post.append(load_post_handler)
    try:
        importer.register()
    except NameError:
        pass
    exporter.register()


def unregister() -> None:
    exporter.unregister()
    try:
        importer.unregister()
    except NameError:
        pass
    try:
        bpy.app.handlers.load_post.remove(load_post_handler)
    except ValueError:
        pass
    del bpy.types.Scene.rbr_addon_version
    for module in reversed(modules):
        module.unregister()
    preferences.unregister()


if __name__ == "__main__":
    try:
        unregister()
    except:  # noqa: E722
        pass
    register()
