"""Deprecated, kept to enable migrations.
TODO: remove this after a couple of releases.
"""

import bpy  # type: ignore

from .physical_material_editor.properties import RBRMaterialMaps


class RBRTexture(bpy.types.PropertyGroup):
    """Deprecated, kept to enable migrations"""

    name: bpy.props.StringProperty()  # type: ignore
    is_road_surface: bpy.props.BoolProperty()  # type: ignore
    dry_new: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    damp_new: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    wet_new: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    dry_normal: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    damp_normal: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    wet_normal: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    dry_worn: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    damp_worn: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    wet_worn: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    material_maps: bpy.props.CollectionProperty(type=RBRMaterialMaps)  # type: ignore


class RBRSpecularTexture(bpy.types.PropertyGroup):
    """Deprecated, kept to enable migrations"""

    name: bpy.props.StringProperty()  # type: ignore
    dry: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    damp: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore
    wet: bpy.props.PointerProperty(type=bpy.types.Image)  # type: ignore


class RBRTextures(bpy.types.PropertyGroup):
    textures: bpy.props.CollectionProperty(type=RBRTexture)  # type: ignore
    specular_textures: bpy.props.CollectionProperty(type=RBRSpecularTexture)  # type: ignore


def register() -> None:
    bpy.utils.register_class(RBRTexture)
    bpy.utils.register_class(RBRSpecularTexture)
    bpy.utils.register_class(RBRTextures)
    bpy.types.Scene.rbr_textures = bpy.props.PointerProperty(
        type=RBRTextures,
    )


def unregister() -> None:
    del bpy.types.Scene.rbr_textures
    bpy.utils.unregister_class(RBRTextures)
    bpy.utils.unregister_class(RBRSpecularTexture)
    bpy.utils.unregister_class(RBRTexture)
