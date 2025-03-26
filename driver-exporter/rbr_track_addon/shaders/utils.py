"""Shader node helper functions.
"""

from typing import Optional, Tuple, Union

import bpy  # type: ignore


def make_math_node(
    node_tree: bpy.types.NodeTree,
    operation: str,
    in1: Union[float, bpy.types.NodeSocket],
    in2: Optional[Union[float, bpy.types.NodeSocket]] = None,
    in3: Optional[Union[float, bpy.types.NodeSocket]] = None,
    clamp: bool = False,
) -> bpy.types.NodeSocket:
    node = node_tree.nodes.new("ShaderNodeMath")
    node.operation = operation
    node.use_clamp = clamp
    if isinstance(in1, float):
        node.inputs[0].default_value = in1
    else:
        node_tree.links.new(
            node.inputs[0],
            in1,
        )
    if in2 is not None:
        if isinstance(in2, float):
            node.inputs[1].default_value = in2
        else:
            node_tree.links.new(
                node.inputs[1],
                in2,
            )
    if in3 is not None:
        if isinstance(in3, float):
            node.inputs[1].default_value = in3
        else:
            node_tree.links.new(
                node.inputs[2],
                in3,
            )
    return node.outputs["Value"]


def mix_rgb(
    node_tree: bpy.types.NodeTree,
    fac: Union[float, bpy.types.NodeSocket],
    a: Union[Tuple[float, float, float, float], bpy.types.NodeSocket],
    b: Union[Tuple[float, float, float, float], bpy.types.NodeSocket],
    blend_type: str = "MIX",
    clamp: bool = False,
) -> bpy.types.NodeSocket:
    """Linear interpolation between two colours according to some factor"""
    node = node_tree.nodes.new("ShaderNodeMixRGB")
    node.blend_type = blend_type
    node.use_clamp = clamp
    if isinstance(fac, bpy.types.NodeSocket):
        node_tree.links.new(
            node.inputs["Fac"],
            fac,
        )
    else:
        node.inputs["Fac"].default_value = fac
    if isinstance(a, bpy.types.NodeSocket):
        node_tree.links.new(
            node.inputs["Color1"],
            a,
        )
    else:
        node.inputs["Color1"].default_value = a
    if isinstance(b, bpy.types.NodeSocket):
        node_tree.links.new(
            node.inputs["Color2"],
            b,
        )
    else:
        node.inputs["Color2"].default_value = b
    return node.outputs["Color"]


def srgb_to_linear(
    node_tree: bpy.types.NodeTree,
    input: Union[str, bpy.types.NodeSocket],
) -> bpy.types.NodeSocket:
    # TODO this isn't perfect, it needs a where clause
    separate = node_tree.nodes.new("ShaderNodeSeparateRGB")
    if isinstance(input, str):
        separate.name = input
    elif isinstance(input, bpy.types.NodeSocket):
        node_tree.links.new(input, separate.inputs[0])
    else:
        raise NotImplementedError
    combine = node_tree.nodes.new("ShaderNodeCombineRGB")
    for i in [0, 1, 2]:
        add = make_math_node(
            node_tree,
            "ADD",
            separate.outputs[i],
            0.055,
        )
        divide = make_math_node(
            node_tree,
            "DIVIDE",
            add,
            1.055,
        )
        power = make_math_node(
            node_tree,
            "POWER",
            divide,
            2.4,
        )
        node_tree.links.new(power, combine.inputs[i])
    return combine.outputs[0]


def linear_to_srgb(
    node_tree: bpy.types.NodeTree,
    input: Union[str, bpy.types.NodeSocket],
) -> bpy.types.NodeSocket:
    # TODO this isn't perfect, it needs a where clause
    separate = node_tree.nodes.new("ShaderNodeSeparateRGB")
    if isinstance(input, str):
        separate.name = input
    elif isinstance(input, bpy.types.NodeSocket):
        node_tree.links.new(input, separate.inputs[0])
    else:
        raise NotImplementedError
    combine = node_tree.nodes.new("ShaderNodeCombineRGB")
    for i in [0, 1, 2]:
        # node_tree.links.new(separate.outputs[i], combine.inputs[i])
        # continue
        power = make_math_node(
            node_tree,
            "POWER",
            separate.outputs[i],
            1 / 2.4,
        )
        mult = make_math_node(
            node_tree,
            "MULTIPLY",
            power,
            1.055,
        )
        subtract = make_math_node(
            node_tree,
            "SUBTRACT",
            mult,
            0.055,
        )
        node_tree.links.new(subtract, combine.inputs[i])
    return combine.outputs[0]


def vector_exp(
    node_tree: bpy.types.NodeTree,
    vector: bpy.types.NodeSocketVector,
) -> bpy.types.NodeSocketVector:
    separate = node_tree.nodes.new("ShaderNodeSeparateXYZ")
    node_tree.links.new(vector, separate.inputs[0])
    combine = node_tree.nodes.new("ShaderNodeCombineXYZ")
    for i in [0, 1, 2]:
        math = make_math_node(node_tree, "EXPONENT", in1=separate.outputs[i])
        node_tree.links.new(math, combine.inputs[i])
    return combine.outputs[0]


def vector_power(
    node_tree: bpy.types.NodeTree,
    exponent: float,
    vector: bpy.types.NodeSocketVector,
) -> bpy.types.NodeSocketVector:
    separate = node_tree.nodes.new("ShaderNodeSeparateXYZ")
    node_tree.links.new(vector, separate.inputs[0])
    combine = node_tree.nodes.new("ShaderNodeCombineXYZ")
    for i in [0, 1, 2]:
        math = make_math_node(node_tree, "POWER", in1=separate.outputs[i], in2=exponent)
        node_tree.links.new(math, combine.inputs[i])
    return combine.outputs[0]


def vector_scale(
    node_tree: bpy.types.NodeTree,
    vector: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
    scale: Union[bpy.types.NodeSocketFloat, float],
) -> bpy.types.NodeSocketVector:
    scale_node = node_tree.nodes.new("ShaderNodeVectorMath")
    scale_node.operation = "SCALE"
    if isinstance(vector, bpy.types.NodeSocket):
        node_tree.links.new(vector, scale_node.inputs[0])
    else:
        scale_node.inputs[0].default_value = vector
    if isinstance(scale, bpy.types.NodeSocket):
        node_tree.links.new(scale, scale_node.inputs["Scale"])
    else:
        scale_node.inputs["Scale"].default_value = scale
    return scale_node.outputs[0]


def vector_multiply(
    node_tree: bpy.types.NodeTree,
    v1: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
    v2: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
) -> bpy.types.NodeSocketVector:
    return vector_math(node_tree, "MULTIPLY", v1, v2)


def vector_add(
    node_tree: bpy.types.NodeTree,
    v1: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
    v2: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
) -> bpy.types.NodeSocketVector:
    return vector_math(node_tree, "ADD", v1, v2)


def vector_subtract(
    node_tree: bpy.types.NodeTree,
    v1: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
    v2: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
) -> bpy.types.NodeSocketVector:
    return vector_math(node_tree, "SUBTRACT", v1, v2)


def vector_math(
    node_tree: bpy.types.NodeTree,
    operation: str,
    v1: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
    v2: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
) -> bpy.types.NodeSocketVector:
    add = node_tree.nodes.new("ShaderNodeVectorMath")
    add.operation = operation
    if isinstance(v1, bpy.types.NodeSocket):
        node_tree.links.new(v1, add.inputs[0])
    else:
        add.inputs[0].default_value = v1
    if isinstance(v2, bpy.types.NodeSocket):
        node_tree.links.new(v2, add.inputs[1])
    else:
        add.inputs[1].default_value = v2
    return add.outputs[0]


def vector_math_float(
    node_tree: bpy.types.NodeTree,
    operation: str,
    v1: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
    v2: Union[bpy.types.NodeSocketVector, Tuple[float, float, float]],
) -> bpy.types.NodeSocketVector:
    add = node_tree.nodes.new("ShaderNodeVectorMath")
    add.operation = operation
    if isinstance(v1, bpy.types.NodeSocket):
        node_tree.links.new(v1, add.inputs[0])
    else:
        add.inputs[0].default_value = v1
    if isinstance(v2, bpy.types.NodeSocket):
        node_tree.links.new(v2, add.inputs[1])
    else:
        add.inputs[1].default_value = v2
    return add.outputs["Value"]
