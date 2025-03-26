"""A shader node for RBR textures.

A key property of this is we can dynamically switch out which texture (e.g.
dry/damp/wet) is rendered in the viewport by changing some scene properties.
"""

from typing import Any, List, Iterable, Optional, Set, Tuple
import math

import bpy  # type: ignore

from rbr_track_formats import errors
from rbr_track_formats.mat import SurfaceType, SurfaceAge
from ..physical_material_editor.operator import RBR_OT_edit_material_maps
from ..physical_material_editor.properties import (
    RBRPropertyNodePointer,
    RBRMaterialMaps,
    RBRFallbackMaterials,
)
from .utils import linear_to_srgb

RBR_TEXTURE_NODE_TREE_PREFIX: str = ".RBRTextureV0."


def suggested_size(x: int) -> int:
    """Get the closest size for fast loading in RBR (power of two)"""
    if x <= 0:
        return 0
    s: int = 2 ** math.ceil(math.log2(x))
    return s


def recreate_internals(
    context: bpy.types.Context,
    node_tree: bpy.types.NodeTree,
) -> None:
    node_tree.links.clear()
    old_internal = None
    images = dict()
    for node in node_tree.nodes:
        if isinstance(node, bpy.types.NodeGroupInput):
            continue
        if isinstance(node, bpy.types.NodeGroupOutput):
            continue
        if isinstance(node, ShaderNodeRBRTextureInternal):
            node.name = "old_internal"
            old_internal = node
            continue
        if isinstance(node, bpy.types.ShaderNodeTexImage):
            images[node.name] = node.image
        node_tree.nodes.remove(node)
    node_tree.interface.clear()
    create_sockets(node_tree)
    make_nodes_and_links(node_tree)
    is_road_surface = False
    if old_internal is not None:
        is_road_surface = old_internal.is_road_surface
    active_name = context_active_image_name(
        context=context,
        is_road_surface=is_road_surface,
    )
    if old_internal is not None:
        node_tree.nodes["internal"].is_road_surface = old_internal.is_road_surface
        node_tree.nodes["internal"].override_mip_levels = (
            old_internal.override_mip_levels
        )
        node_tree.nodes["internal"].mip_levels = old_internal.mip_levels
        for original in old_internal.material_maps:
            new = node_tree.nodes["internal"].material_maps.add()
            new.copy(original)
        node_tree.nodes.remove(old_internal)
    for name, image in images.items():
        node_tree.nodes[name].image = image
    link_texture_for_tree(node_tree, active_name)


RBR_TEXTURE_COLOR_OUTPUT: str = "RBR Texture Color"
RBR_TEXTURE_ALPHA_OUTPUT: str = "RBR Texture Alpha"


def create_sockets(node_tree: bpy.types.NodeTree) -> None:
    # Add the input and output sockets (this also adjusts the group
    # inputs/outputs)
    uv_socket = node_tree.interface.new_socket(
        "UV", in_out="INPUT", socket_type="NodeSocketVector"
    )
    uv_socket.hide_value = True
    node_tree.interface.new_socket(
        RBR_TEXTURE_COLOR_OUTPUT, in_out="OUTPUT", socket_type="NodeSocketColor"
    )
    node_tree.interface.new_socket(
        RBR_TEXTURE_ALPHA_OUTPUT, in_out="OUTPUT", socket_type="NodeSocketFloat"
    )


def setup_texture_node_tree() -> bpy.types.NodeTree:
    node_tree = bpy.data.node_groups.new(
        RBR_TEXTURE_NODE_TREE_PREFIX + "Name", "ShaderNodeTree"
    )
    # Create the internal group input and output nodes
    node_tree.nodes.new("NodeGroupInput")
    node_tree.nodes.new("NodeGroupOutput")
    create_sockets(node_tree)
    make_nodes_and_links(node_tree)
    return node_tree


def make_nodes_and_links(node_tree: bpy.types.NodeTree) -> None:
    # Get user inputs
    uv_in = node_tree.nodes["Group Input"].outputs["UV"]

    internal = node_tree.nodes.new("ShaderNodeRBRTextureInternal")
    internal.name = "internal"

    for surface_type in SurfaceType:
        for surface_age in SurfaceAge:
            tex_image = node_tree.nodes.new("ShaderNodeTexImage")
            node_tree.links.new(tex_image.inputs["Vector"], uv_in)
            tex_image.name = surface_type.name.lower() + "/" + surface_age.name.lower()

    # Convert to sRGB. The input value is linear (regardless of image
    # colorspace, blender has already converted it before this point).
    # RBR does calculations in sRGB space, so we mimic that.
    convert_out = linear_to_srgb(node_tree, "sRGBConverter")
    # The connection of the image to the converter and the alpha to the output
    # is done in 'link_texture_for_tree'
    node_tree.links.new(
        node_tree.nodes["Group Output"].inputs[RBR_TEXTURE_COLOR_OUTPUT],
        convert_out,
    )


def context_active_image_name(context: bpy.types.Context, is_road_surface: bool) -> str:
    track_settings = context.scene.rbr_track_settings
    surface_type: SurfaceType = track_settings.get_active_surface_type()
    surface_age: SurfaceAge = track_settings.get_active_surface_age()
    if is_road_surface:
        return surface_type.name.lower() + "/" + surface_age.name.lower()
    else:
        return surface_type.name.lower() + "/" + SurfaceAge.NEW.name.lower()


def unsafe_tree_name_to_texture_name(node_tree: bpy.types.NodeTree) -> str:
    name = tree_name_to_texture_name(node_tree)
    if name is None:
        raise errors.RBRAddonBug(f"Could not get texture name of tree {node_tree.name}")
    return name


def tree_name_to_texture_name(node_tree: bpy.types.NodeTree) -> Optional[str]:
    if not node_tree.name.startswith(RBR_TEXTURE_NODE_TREE_PREFIX):
        return None
    name: str = node_tree.name[len(RBR_TEXTURE_NODE_TREE_PREFIX) :]
    if node_tree.library is not None:
        return f"{name} [{node_tree.library.name}]"
    else:
        return name


def tree_name_to_texture_filename(node_tree: bpy.types.NodeTree) -> Optional[str]:
    """Return a filename suitable for RBR.
    It's still possible to have collisions between non-library and library
    names, but it's unlikely.
    """
    if node_tree is None:
        raise errors.RBRAddonBug("ShaderNodeRBRTexture missing node tree")
    if not node_tree.name.startswith(RBR_TEXTURE_NODE_TREE_PREFIX):
        return None
    name: str = node_tree.name[len(RBR_TEXTURE_NODE_TREE_PREFIX) :]
    if node_tree.library is not None:
        lib_name = node_tree.library.name
        if lib_name.endswith(".blend"):
            lib_name = lib_name[0 : -len(".blend")]
        return f"{lib_name}-{name}"
    else:
        return name


class ShaderNodeRBRTextureInternal(bpy.types.ShaderNodeCustomGroup):
    """The storage node contained within the texture node tree."""

    bl_name = ".RBRTextureInternalV0"
    bl_label = "RBR Texture Internal"
    node_tree: Optional[bpy.types.NodeTree] = None

    def __update_is_road_surface__(self, context: bpy.types.Context) -> None:
        name = context_active_image_name(
            context=context,
            is_road_surface=self.is_road_surface,
        )
        parent_tree = self.id_data
        link_texture_for_tree(parent_tree, name)
        # This might update an unrelated editor, but that's fine.
        if RBR_OT_edit_material_maps.active_operator is not None:
            RBR_OT_edit_material_maps.active_operator.update_active_texture(context)

    is_road_surface: bpy.props.BoolProperty(  # type: ignore
        name="Road Surface (diffuse only)",
        description="Textures should differ when track is worn",
        default=False,
        options=set(),  # No animation
        update=lambda self, context: self.__update_is_road_surface__(context),
    )

    override_mip_levels: bpy.props.BoolProperty(  # type: ignore
        name="Override MipLevels",
        description="Use custom MipLevels when exporting instead of taking the value from the file",
        default=False,
        options=set(),  # No animation
    )
    mip_levels: bpy.props.IntProperty(  # type: ignore
        name="MipLevels",  # noqa: F821
        description="MipLevels to export",
        default=0,
        min=-1,
        soft_max=20,
        options=set(),  # No animation
    )

    material_maps: bpy.props.CollectionProperty(  # type: ignore
        type=RBRMaterialMaps,
    )

    fallback_materials: bpy.props.PointerProperty(  # type: ignore
        type=RBRFallbackMaterials,
    )


def link_texture_for_tree(node_tree: bpy.types.NodeTree, node_name: str) -> None:
    convert_in = node_tree.nodes["sRGBConverter"].inputs[0]
    node_tree.links.new(
        convert_in,
        node_tree.nodes[node_name].outputs["Color"],
    )
    node_tree.links.new(
        node_tree.nodes["Group Output"].inputs[RBR_TEXTURE_ALPHA_OUTPUT],
        node_tree.nodes[node_name].outputs["Alpha"],
    )


class ShaderNodeRBRTexture(bpy.types.ShaderNodeCustomGroup):
    """Set textures for RBR objects which can vary for dry/damp/wet and
    new/normal/worn combinations.
    """

    bl_name = "ShaderNodeRBRTexture"
    bl_label = "RBR Texture"
    # This is a field of ShaderNodeCustomGroup
    node_tree: Optional[bpy.types.NodeTree] = None

    # Use getters/setters to control these, so that we can store the texture
    # name in the node tree name (with a prefix).
    def __get_name__(self) -> str:
        if self.node_tree is None:
            raise errors.RBRAddonBug("ShaderNodeRBRTexture missing node tree")
        name = tree_name_to_texture_name(self.node_tree)
        if name is None:
            raise errors.RBRAddonBug(
                f"ShaderNodeRBRTexture has invalid name {self.node_tree.name}"
            )
        return name

    def __set_name__(self, value: str) -> None:
        if self.node_tree is None:
            raise errors.RBRAddonBug("ShaderNodeRBRTexture missing node tree")
        self.node_tree.name = f"{RBR_TEXTURE_NODE_TREE_PREFIX}{value}"

    texture_name: bpy.props.StringProperty(  # type: ignore
        name="Texture Name",  # noqa: F821
        default="Name",  # noqa: F821
        get=lambda self: self.__get_name__(),
        set=lambda self, value: self.__set_name__(value),
    )

    def texture_name_filename(self) -> str:
        name = tree_name_to_texture_filename(self.node_tree)
        if name is None:
            raise errors.RBRAddonBug("Missing node tree for texture node")
        return name

    def set_id(
        self,
        new_name: str,
    ) -> None:
        """Call to set the "ID block" to a different one. Used when the user
        picks a different texture name from the dropdown box.
        """
        # Must iterate instead of using the name keys, because two texture nodes
        # can have the same name from two different libraries.
        for node_tree in bpy.data.node_groups:
            if tree_name_to_texture_name(node_tree) == new_name:
                self.node_tree = node_tree
                break

    def init(self, context: bpy.types.Context) -> None:
        self.width = 300

    def free(self) -> None:
        # Intentionally leak the node tree.
        pass

    def copy(self, original) -> None:  # type: ignore
        """self is the pasted node, original is the original node"""
        self.make_single_user()

    def make_single_user(self) -> None:
        if self.node_tree is not None:
            self.node_tree = self.node_tree.copy()

    def __make_texture_layout__(
        self, layout: bpy.types.UILayout, texture_node_name: str, label: str
    ) -> None:
        if self.node_tree is None:
            raise errors.RBRAddonBug("ShaderNodeRBRTexture missing node tree")
        texture_node = self.node_tree.nodes[texture_node_name]
        img = texture_node.image
        if isinstance(img, bpy.types.Image):
            [width, height] = img.size
            ideal_width = suggested_size(width)
            ideal_height = suggested_size(height)
            if ideal_width != width or ideal_height != height:
                layout.box().label(
                    icon="ERROR",
                    text=f"Suggested size: {ideal_width}x{ideal_height}",
                )

        split = layout.split(factor=0.3)
        split.label(text=label)
        split.template_ID(texture_node, "image", new="image.new", open="image.open")

    def get_internal(self) -> ShaderNodeRBRTextureInternal:
        if self.node_tree is None:
            raise errors.RBRAddonBug("Missing node tree for get_internal")
        internal = self.node_tree.nodes.get("internal")
        if internal is None:
            raise errors.RBRAddonBug("Missing internal node in node tree")
        return internal  # type: ignore

    def link_context_active_texture(self, context: bpy.types.Context) -> None:
        name = context_active_image_name(
            context=context,
            is_road_surface=self.get_internal().is_road_surface,
        )
        if self.node_tree is None:
            raise errors.RBRAddonBug(
                "Missing node tree for link_context_active_texture"
            )
        link_texture_for_tree(self.node_tree, name)

    def get_active_image(self, context: bpy.types.Context) -> bpy.types.Image:
        name = context_active_image_name(context, self.get_internal().is_road_surface)
        if self.node_tree is None:
            raise errors.RBRAddonBug("Missing node tree for get_active_image")
        node = self.node_tree.nodes.get(name)
        if node is None:
            raise errors.RBRAddonBug("Missing image node for get_active_image")
        return node.image

    def draw_buttons(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
    ) -> None:
        # Display the template_ID like UI
        template_ID = layout.row(align=True)
        choose_texture = template_ID.operator(
            "rbr.choose_texture", text="", icon="TRIA_DOWN"
        )
        choose_texture.node.node_name = self.name
        choose_texture.node.nodetree_pointer = str(self.id_data.as_pointer())
        if self.node_tree is None:
            new_texture = template_ID.operator("rbr.new_texture")
            new_texture.node.node_name = self.name
            new_texture.node.nodetree_pointer = str(self.id_data.as_pointer())
            return

        count = self.node_tree.users
        # Only display the "make single user" operator if it's applicable.
        if count > 1:
            split = template_ID.split(align=True, factor=0.85)
            name_container = split.column(align=True)
            name_container.enabled = self.node_tree.library is None
            name_container.prop(self, "texture_name", text="")
            make_single_user = split.operator(
                "rbr.make_texture_single_user", text=f"{count}"
            )
            make_single_user.node.node_name = self.name
            make_single_user.node.nodetree_pointer = str(self.id_data.as_pointer())
        else:
            template_ID.enabled = self.node_tree.library is None
            template_ID.prop(self, "texture_name", text="")
        unlink = template_ID.operator("rbr.unlink_texture", text="", icon="PANEL_CLOSE")
        unlink.node.node_name = self.name
        unlink.node.nodetree_pointer = str(self.id_data.as_pointer())

        texture_ui = layout.box()
        is_road_surface = False
        internal = self.node_tree.nodes.get("internal")
        if internal is not None:
            is_road_surface = internal.is_road_surface
            texture_ui.prop(internal, "is_road_surface")
            texture_ui.prop(internal, "override_mip_levels")
            if internal.override_mip_levels:
                texture_ui.prop(internal, "mip_levels")
        if is_road_surface:
            self.__make_texture_layout__(texture_ui, "dry/new", "Dry/New")
            self.__make_texture_layout__(texture_ui, "dry/normal", "Dry/Normal")
            self.__make_texture_layout__(texture_ui, "dry/worn", "Dry/Worn")
            self.__make_texture_layout__(texture_ui, "damp/new", "Damp/New")
            self.__make_texture_layout__(texture_ui, "damp/normal", "Damp/Normal")
            self.__make_texture_layout__(texture_ui, "damp/worn", "Damp/Worn")
            self.__make_texture_layout__(texture_ui, "wet/new", "Wet/New")
            self.__make_texture_layout__(texture_ui, "wet/normal", "Wet/Normal")
            self.__make_texture_layout__(texture_ui, "wet/worn", "Wet/Worn")
        else:
            self.__make_texture_layout__(texture_ui, "dry/new", "Dry")
            self.__make_texture_layout__(texture_ui, "damp/new", "Damp")
            self.__make_texture_layout__(texture_ui, "wet/new", "Wet")

        edit_material = layout.operator("rbr.edit_material_maps")
        edit_material.node.node_name = self.name
        edit_material.node.nodetree_pointer = str(self.id_data.as_pointer())


# (identifier, name, description, icon, numeric ID)
def get_textures_enum(x: Any, y: Any) -> List[Tuple[str, str, str, str, int]]:
    result = []
    for i, node_tree in enumerate(bpy.data.node_groups):
        texture_name = tree_name_to_texture_name(node_tree)
        if texture_name is None:
            continue
        icon = "TEXTURE"
        if node_tree.library is not None:
            icon = "LINK_BLEND"
        result.append(
            (
                texture_name,
                texture_name,
                texture_name,
                icon,
                i,
            )
        )
    return result


class RBR_OT_choose_texture(bpy.types.Operator):
    """This operator is used to produce a dropdown box similar to template_ID,
    but for our custom RBR Texture types.
    """

    bl_idname = "rbr.choose_texture"
    bl_label = "Browse existing textures"
    bl_options = {"INTERNAL", "UNDO"}
    bl_property = "texture"
    bl_description = "Select texture to be linked"

    texture: bpy.props.EnumProperty(  # type: ignore
        items=get_textures_enum,
    )
    node: bpy.props.PointerProperty(type=RBRPropertyNodePointer)  # type: ignore

    def execute(self, context: bpy.types.Context) -> Set[str]:
        node = self.node.get_shader_node()
        if node is None:
            return {"CANCELLED"}
        node.set_id(self.texture)
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class RBR_OT_new_texture(bpy.types.Operator):
    bl_idname = "rbr.new_texture"
    bl_label = "New"
    bl_description = "Create a new texture data-block"
    bl_options = {"INTERNAL", "UNDO"}

    node: bpy.props.PointerProperty(type=RBRPropertyNodePointer)  # type: ignore

    def execute(self, context: bpy.types.Context) -> Set[str]:
        node = self.node.get_shader_node()
        if node is None:
            return {"CANCELLED"}
        node.node_tree = setup_texture_node_tree()
        node.link_context_active_texture(context)
        return {"FINISHED"}


class RBR_OT_make_texture_single_user(bpy.types.Operator):
    bl_idname = "rbr.make_texture_single_user"
    bl_label = "User count"
    bl_description = (
        "Display number of users of this data (click to make a single-user copy)"
    )
    bl_options = {"INTERNAL", "UNDO"}

    node: bpy.props.PointerProperty(type=RBRPropertyNodePointer)  # type: ignore

    def execute(self, context: bpy.types.Context) -> Set[str]:
        node = self.node.get_shader_node()
        if node is None:
            return {"CANCELLED"}
        node.make_single_user()
        return {"FINISHED"}


class RBR_OT_unlink_texture(bpy.types.Operator):
    bl_idname = "rbr.unlink_texture"
    bl_label = "Unlink data-block"
    bl_description = "Unlink this texture data-block"
    bl_options = {"INTERNAL", "UNDO"}

    node: bpy.props.PointerProperty(type=RBRPropertyNodePointer)  # type: ignore

    def execute(self, context: bpy.types.Context) -> Set[str]:
        node = self.node.get_shader_node()
        if node is None:
            return {"CANCELLED"}
        node.node_tree = None
        return {"FINISHED"}


def all_rbr_texture_nodes() -> Iterable[ShaderNodeRBRTexture]:
    for material in bpy.data.materials:
        if material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if isinstance(node, ShaderNodeRBRTexture):
                yield node


def all_rbr_texture_node_trees_filename() -> Iterable[Tuple[str, bpy.types.NodeTree]]:
    for node_tree in bpy.data.node_groups:
        texture_name = tree_name_to_texture_filename(node_tree)
        if texture_name is not None:
            yield (texture_name, node_tree)


def register() -> None:
    bpy.utils.register_class(RBR_OT_new_texture)
    bpy.utils.register_class(RBR_OT_choose_texture)
    bpy.utils.register_class(RBR_OT_make_texture_single_user)
    bpy.utils.register_class(RBR_OT_unlink_texture)
    bpy.utils.register_class(ShaderNodeRBRTextureInternal)
    bpy.utils.register_class(ShaderNodeRBRTexture)


def unregister() -> None:
    bpy.utils.unregister_class(ShaderNodeRBRTexture)
    bpy.utils.unregister_class(ShaderNodeRBRTextureInternal)
    bpy.utils.unregister_class(RBR_OT_unlink_texture)
    bpy.utils.unregister_class(RBR_OT_make_texture_single_user)
    bpy.utils.unregister_class(RBR_OT_choose_texture)
    bpy.utils.unregister_class(RBR_OT_new_texture)
