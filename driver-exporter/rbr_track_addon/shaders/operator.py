from typing import Dict, List, Set, Tuple

import bpy  # type: ignore

from ..object_settings.types import RBRObjectType
from . import shader_node
from . import sky
from . import texture


def pop_links() -> Dict[str, List[Tuple[str, str, str, str]]]:
    materials_to_relink: Dict[str, List[Tuple[str, str, str, str]]] = dict()

    def node_is_rbr(node: bpy.types.Node) -> bool:
        return isinstance(node, shader_node.ShaderNodeRBR) or isinstance(
            node, texture.ShaderNodeRBRTexture
        )

    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        materials_to_relink[material.name] = []
        for link in material.node_tree.links:
            if node_is_rbr(link.from_node) or node_is_rbr(link.to_node):
                materials_to_relink[material.name].append(
                    (
                        link.from_node.name,
                        link.from_socket.name,
                        link.to_node.name,
                        link.to_socket.name,
                    )
                )
            else:
                continue
            # Unlink now we have recorded it
            material.node_tree.links.remove(link)

    return materials_to_relink


def push_links(links: Dict[str, List[Tuple[str, str, str, str]]]) -> None:
    for material_name, missing_links in links.items():
        node_tree = bpy.data.materials[material_name].node_tree
        for (
            from_node_name,
            from_socket_name,
            to_node_name,
            to_socket_name,
        ) in missing_links:
            from_node = node_tree.nodes[from_node_name]
            to_node = node_tree.nodes[to_node_name]
            if (
                isinstance(from_node, texture.ShaderNodeRBRTexture)
                and from_socket_name == "RBR Texture"
            ):
                # Rewrite sockets which have since changed name
                from_socket_name = texture.RBR_TEXTURE_COLOR_OUTPUT
                # Create the alpha socket link too automatically
                if isinstance(to_node, shader_node.ShaderNodeRBR):
                    if to_socket_name == shader_node.RBR_DIFFUSE_1_TEXTURE_INPUT:
                        node_tree.links.new(
                            from_node.outputs[texture.RBR_TEXTURE_ALPHA_OUTPUT],
                            to_node.inputs[shader_node.RBR_DIFFUSE_1_ALPHA_INPUT],
                        )
                    elif to_socket_name == shader_node.RBR_DIFFUSE_2_TEXTURE_INPUT:
                        node_tree.links.new(
                            from_node.outputs[texture.RBR_TEXTURE_ALPHA_OUTPUT],
                            to_node.inputs[shader_node.RBR_DIFFUSE_2_ALPHA_INPUT],
                        )
            node_tree.links.new(
                from_node.outputs[from_socket_name],
                to_node.inputs[to_socket_name],
            )


def refresh_all_rbr_shaders(context: bpy.types.Context) -> None:
    links = pop_links()
    sky.recreate_internals()
    shader_node.recreate_internals(context)
    for _, node_tree in texture.all_rbr_texture_node_trees_filename():
        texture.recreate_internals(context, node_tree)
    push_links(links)
    for obj in bpy.data.objects:
        obj.rbr_object_type_value = RBRObjectType[obj.rbr_object_settings.type].value
        # Must also force an update here
        obj.update_tag()
    context.scene.rbr_track_settings.update_world_context(context)
    context.scene.rbr_track_settings.update_sky_values()


class RBR_OT_refresh_shaders(bpy.types.Operator):
    """Utility operator for recreating all node trees. Also updates all object
    types so the shaders pick up the right data."""

    bl_idname = "rbr.refresh_shaders"
    bl_label = "Recreate RBR shader trees"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        refresh_all_rbr_shaders(context)
        return {"FINISHED"}


def register() -> None:
    bpy.utils.register_class(RBR_OT_refresh_shaders)


def unregister() -> None:
    bpy.utils.unregister_class(RBR_OT_refresh_shaders)
