from typing import Dict

import bpy  # type: ignore

from . import operator
from . import properties
from . import uv_velocity
from . import shader_node
from . import sky
from . import texture
from . import time
from . import utils  # noqa: F401


def add_node_type(
    layout: bpy.types.UILayout, node_type: str
) -> bpy.types.OperatorProperties:
    """Add a node type to a menu."""
    bl_rna = bpy.types.Node.bl_rna_get_subclass(node_type)
    label = bl_rna.name
    translation_context = bl_rna.translation_context
    props = layout.operator("node.add_node", text=label, text_ctxt=translation_context)
    props.type = node_type
    props.use_transform = True
    return props


class NODE_MT_category_RBR_SHADER(bpy.types.Menu):
    bl_idname = "NODE_MT_category_RBR_SHADER"
    bl_label = "RBR Nodes"

    def draw(self, _context: bpy.types.Context) -> None:
        add_node_type(self.layout, shader_node.ShaderNodeRBR.bl_name)
        add_node_type(self.layout, texture.ShaderNodeRBRTexture.bl_name)
        add_node_type(self.layout, uv_velocity.ShaderNodeUVVelocity.bl_name)
        add_node_type(self.layout, sky.ShaderNodeRBRSky.bl_name)
        # TODO remove
        add_node_type(self.layout, time.ShaderNodeTime.bl_name)


def draw_rbr_shader_menu(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    self.layout.menu(NODE_MT_category_RBR_SHADER.bl_idname)


def register() -> None:
    properties.register()
    time.register()
    uv_velocity.register()
    texture.register()
    shader_node.register()
    sky.register()
    operator.register()
    bpy.utils.register_class(NODE_MT_category_RBR_SHADER)
    bpy.types.NODE_MT_shader_node_add_all.append(draw_rbr_shader_menu)


def unregister() -> None:
    bpy.types.NODE_MT_shader_node_add_all.remove(draw_rbr_shader_menu)
    bpy.utils.unregister_class(NODE_MT_category_RBR_SHADER)
    operator.unregister()
    sky.unregister()
    shader_node.unregister()
    texture.unregister()
    uv_velocity.unregister()
    time.unregister()
    properties.unregister()


def set_colorspace(node_tree: bpy.types.NodeTree) -> None:
    for node in node_tree.nodes:
        if isinstance(node, bpy.types.ShaderNodeTexImage):
            if node.image is not None:
                node.image.colorspace_settings.name = "sRGB"


def migrate_split_shaders() -> None:
    texture_trees = dict()
    for rbr_texture in bpy.context.scene.rbr_textures.textures:
        node_tree = texture.setup_texture_node_tree()
        node_tree.name = texture.RBR_TEXTURE_NODE_TREE_PREFIX + rbr_texture.name
        internal = node_tree.nodes["internal"]
        internal.is_road_surface = rbr_texture.is_road_surface
        for original in rbr_texture.material_maps:
            new = internal.material_maps.add()
            new.copy(original)
        node_tree.nodes["dry/new"].image = rbr_texture.dry_new
        node_tree.nodes["dry/normal"].image = rbr_texture.dry_normal
        node_tree.nodes["dry/worn"].image = rbr_texture.dry_worn
        node_tree.nodes["damp/new"].image = rbr_texture.damp_new
        node_tree.nodes["damp/normal"].image = rbr_texture.damp_normal
        node_tree.nodes["damp/worn"].image = rbr_texture.damp_worn
        node_tree.nodes["wet/new"].image = rbr_texture.wet_new
        node_tree.nodes["wet/normal"].image = rbr_texture.wet_normal
        node_tree.nodes["wet/worn"].image = rbr_texture.wet_worn
        set_colorspace(node_tree)
        texture_trees[rbr_texture.name] = node_tree
    specular_texture_trees = dict()
    for rbr_texture in bpy.context.scene.rbr_textures.specular_textures:
        node_tree = texture.setup_texture_node_tree()
        node_tree.name = texture.RBR_TEXTURE_NODE_TREE_PREFIX + rbr_texture.name
        internal = node_tree.nodes["internal"]
        node_tree.nodes["dry/new"].image = rbr_texture.dry
        node_tree.nodes["damp/new"].image = rbr_texture.damp
        node_tree.nodes["wet/new"].image = rbr_texture.wet
        set_colorspace(node_tree)
        specular_texture_trees[rbr_texture.name] = node_tree
    for material in bpy.data.materials:
        if material.use_nodes:
            migrate_node_tree(
                node_tree=material.node_tree,
                texture_trees=texture_trees,
                specular_texture_trees=specular_texture_trees,
            )


def migrate_node_tree(
    node_tree: bpy.types.NodeTree,
    texture_trees: Dict[str, bpy.types.NodeTree],
    specular_texture_trees: Dict[str, bpy.types.NodeTree],
) -> None:
    for node in node_tree.nodes:
        if isinstance(node, shader_node.ShaderNodeRBR):
            diffuse_1 = texture_trees.get(node.diffuse_1)
            if diffuse_1 is None:
                node.has_diffuse_1 = False
            else:
                node.has_diffuse_1 = True
                shader_node.create_texture_and_uv(
                    node_tree=node_tree,
                    tex_tree=diffuse_1,
                    uv_layer=node.diffuse_1_uv,
                    color=node.inputs["Diffuse Texture 1"],
                    alpha=node.inputs["Diffuse Texture 1 Alpha"],
                    uv_velocity=node.diffuse_1_velocity,
                )
                diffuse_2 = texture_trees.get(node.diffuse_2)
                if diffuse_2 is not None:
                    node.has_diffuse_2 = True
                    shader_node.create_texture_and_uv(
                        node_tree=node_tree,
                        tex_tree=diffuse_2,
                        uv_layer=node.diffuse_2_uv,
                        color=node.inputs["Diffuse Texture 2"],
                        alpha=node.inputs["Diffuse Texture 2 Alpha"],
                        uv_velocity=node.diffuse_2_velocity,
                    )
                specular = specular_texture_trees.get(node.specular)
                if specular is not None:
                    node.has_specular = True
                    shader_node.create_texture_and_uv(
                        node_tree=node_tree,
                        tex_tree=specular,
                        uv_layer=node.specular_uv,
                        color=node.inputs["Specular Texture"],
                        alpha=node.inputs["Specular Texture Alpha"],
                        uv_velocity=node.specular_velocity,
                    )
