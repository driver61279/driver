"""A shader node to get the animation time (in seconds) as a float value.
"""

from typing import Optional

from .utils import make_math_node

import bpy  # type: ignore


TIME_NODE_TREE_NAME: str = ".TimeNodeTreeV0"


def fps_float_from_scene(scene: bpy.types.Scene) -> float:
    fps = float(scene.render.fps)
    base = float(scene.render.fps_base)
    return fps / base


def setup_time_node_tree() -> bpy.types.NodeTree:
    node_tree: bpy.types.NodeTree = bpy.data.node_groups.new(
        TIME_NODE_TREE_NAME, "ShaderNodeTree"
    )
    # Create the internal group input and output nodes
    node_tree.nodes.new("NodeGroupOutput")
    # Add the output sockets (this also adjusts the group outputs)
    node_tree.interface.new_socket(
        "Time", in_out="OUTPUT", socket_type="NodeSocketFloat"
    )
    # Create the internal nodes and driver
    frame = node_tree.nodes.new("ShaderNodeValue").outputs["Value"]
    fcurve = frame.driver_add("default_value")
    fcurve.driver.type = "SCRIPTED"
    # Not ideal since this won't auto update when the user changes FPS, but
    # this is the best we can do without introducing a direct dependency on the
    # scene. https://developer.blender.org/T93249
    fcurve.driver.expression = "frame"
    divide = make_math_node(
        node_tree,
        "DIVIDE",
        in1=frame,
        in2=fps_float_from_scene(bpy.context.scene),
    )
    node_tree.links.new(
        node_tree.nodes["Group Output"].inputs["Time"],
        divide,
    )
    return node_tree


class ShaderNodeTime(bpy.types.ShaderNodeCustomGroup):
    """A node which outputs the current timeline time (in seconds as a float).
    This should really be provided by blender, but alas.
    It requires updating when the FPS changes (bpy.context.scene.render.fps),
    and this is achieved by the blender handler update_time_node_fps.
    We can't introduce a direct dependency on that value, since blender will
    include the entire scene if a user copies the node.
    """

    bl_name = "ShaderNodeTime"
    bl_label = "Time"
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
        existing_tree = bpy.data.node_groups.get(TIME_NODE_TREE_NAME)
        if existing_tree is not None:
            self.node_tree = existing_tree
        else:
            self.node_tree = setup_time_node_tree()

    def free(self) -> None:
        # This leaves garbage - in the form of a single node tree - if this is
        # the last active time node. But if a new node is created later,
        # that tree is reused, so this seems fine.
        return


@bpy.app.handlers.persistent  # type: ignore
def update_time_node_fps(
    scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph
) -> None:
    """Watch for FPS updates and update our time nodes as necessary."""
    # Detect play state
    playing = bpy.context.screen.is_animation_playing
    try:
        was_playing = update_time_node_fps.last_playing
    except AttributeError:
        was_playing = False
    finally:
        update_time_node_fps.last_playing = playing
    # Only update if we changed from paused to playing
    if playing and not was_playing:
        # It can happen that there is more than one tree in the file, e.g. if
        # two libraries with time nodes are imported. So we must loop here.
        for node_group in bpy.data.node_groups:
            if node_group.name != TIME_NODE_TREE_NAME:
                continue
            for node in node_group.nodes:
                if isinstance(node, bpy.types.ShaderNodeMath):
                    node.inputs[1].default_value = fps_float_from_scene(scene)
                    break


def register() -> None:
    bpy.utils.register_class(ShaderNodeTime)
    bpy.app.handlers.frame_change_post.append(update_time_node_fps)


def unregister() -> None:
    try:
        bpy.app.handlers.frame_change_post.remove(update_time_node_fps)
    except ValueError:
        pass
    bpy.utils.unregister_class(ShaderNodeTime)
