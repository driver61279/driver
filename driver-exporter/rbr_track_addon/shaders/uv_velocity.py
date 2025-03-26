"""A shader node for moving UVs.
"""

from typing import Optional

from .time import ShaderNodeTime

import bpy  # type: ignore


UV_VELOCITY_NODE_TREE_NAME: str = ".UVVelocityTreeV0"


def setup_uv_velocity_node_tree() -> bpy.types.NodeTree:
    node_tree = bpy.data.node_groups.new(UV_VELOCITY_NODE_TREE_NAME, "ShaderNodeTree")
    # Create the internal group input and output nodes
    node_tree.nodes.new("NodeGroupInput")
    node_tree.nodes.new("NodeGroupOutput")
    # Add the input and output sockets (this also adjusts the group
    # inputs/outputs)
    uv_socket = node_tree.interface.new_socket(
        "UV", in_out="INPUT", socket_type="NodeSocketVector"
    )
    uv_socket.hide_value = True
    # We use a socket input here instead of properties so that we can share a
    # single node tree among all instances of this node.
    node_tree.interface.new_socket(
        "UV Velocity", in_out="INPUT", socket_type="NodeSocketVector"
    )
    node_tree.interface.new_socket(
        "UV", in_out="OUTPUT", socket_type="NodeSocketVector"
    )
    # Get user inputs
    uv_in = node_tree.nodes["Group Input"].outputs["UV"]
    uv_velocity_in = node_tree.nodes["Group Input"].outputs["UV Velocity"]
    # Turn velocity into time varied position offset
    time_node = node_tree.nodes.new(ShaderNodeTime.bl_name)
    time = time_node.outputs["Time"]
    uv_offset = node_tree.nodes.new("ShaderNodeVectorMath")
    uv_offset.operation = "SCALE"
    node_tree.links.new(uv_offset.inputs["Vector"], uv_velocity_in)
    node_tree.links.new(uv_offset.inputs["Scale"], time)
    uv_offset = uv_offset.outputs["Vector"]
    # Add the UV map to the animation UVs
    combined_uv_node = node_tree.nodes.new("ShaderNodeVectorMath")
    combined_uv_node.operation = "ADD"
    node_tree.links.new(combined_uv_node.inputs[0], uv_in)
    node_tree.links.new(combined_uv_node.inputs[1], uv_offset)
    node_tree.links.new(
        node_tree.nodes["Group Output"].inputs["UV"],
        combined_uv_node.outputs["Vector"],
    )
    return node_tree


class ShaderNodeUVVelocity(bpy.types.ShaderNodeCustomGroup):
    """Modify a UV map with a time varying value."""

    bl_name = "ShaderNodeUVVelocity"
    bl_label = "UV Velocity"
    # This is a field of ShaderNodeCustomGroup
    node_tree: Optional[bpy.types.NodeTree] = None

    # Setup the node - setup the node tree and add the group Input and Output nodes
    def init(self, context: bpy.types.Context) -> None:
        # Try to use an existing tree (if one of these nodes was previously
        # created). This means we only have a single driven time node, and
        # thereby avoids the performance penalty of having N driven nodes
        # active at once. The downside to this is that we need to lift the
        # velocity input to a node socket, but we don't actually support the
        # user connecting things to the socket when exporting.
        existing_tree = bpy.data.node_groups.get(UV_VELOCITY_NODE_TREE_NAME)
        if existing_tree is not None:
            self.node_tree = existing_tree
        else:
            self.node_tree = setup_uv_velocity_node_tree()

    # Free (when node is deleted)
    def free(self) -> None:
        # This leaves garbage - in the form of a single node tree - if this is
        # the last active UV velocity node. But if a new node is created later,
        # that tree is reused, so this seems fine.
        return


def register() -> None:
    bpy.utils.register_class(ShaderNodeUVVelocity)


def unregister() -> None:
    bpy.utils.unregister_class(ShaderNodeUVVelocity)
