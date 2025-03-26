"""A unified shader node for all RBR objects.

This does not give a perfect representation of all objects, but it's better
than having many different shader nodes for different object types, because you
can then freely switch between them without having to recreate the shader
nodes.

Also getting a perfect preview in the blender viewport through shader nodes is
more effort than it is worth, and future efforts in this direction would be
better off using a custom OpenGL render engine.
https://github.com/RichardBurnsRally/blender-rbr-track-addon/issues/152
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union
import math

from rbr_track_formats import errors
from rbr_track_formats.common import fold_compose, Vector2
from rbr_track_formats.lbs.common import UVVelocity
from rbr_track_formats.lbs.geom_blocks import RenderType

from ..object_settings.types import RBRObjectType
from .properties import RBRGlobalShaderFlags
from .texture import (
    ShaderNodeRBRTexture,
    tree_name_to_texture_name,
    RBR_TEXTURE_COLOR_OUTPUT,
    RBR_TEXTURE_ALPHA_OUTPUT,
)
from .utils import (
    make_math_node,
    mix_rgb,
    srgb_to_linear,
    vector_multiply,
    vector_scale,
)
from ..util import (
    SomeUVMap,
    UVMap,
    UVMapAttr,
)
from .uv_velocity import ShaderNodeUVVelocity
from . import sky
from .sky import (
    make_value,
    make_vector_value,
)

import bpy  # type: ignore


UV_DIFFUSE_1: str = "RBR_DIFFUSE_1"
UV_DIFFUSE_2: str = "RBR_DIFFUSE_2"
UV_SPECULAR: str = "RBR_SPECULAR"
UV_SHADOW: str = "RBR_SHADOW"

VC_SHADOW: str = "RBR_SHADOW"
VC_COLOR: str = "RBR_COLOR"
VC_SPECULAR_STRENGTH: str = "RBR_SPECULAR_STRENGTH"
VC_SWAY_AMPLITUDE: str = "RBR_SWAY_AMPLITUDE"
VC_SWAY_FREQUENCY: str = "RBR_SWAY_FREQUENCY"
VC_SWAY_PHASE: str = "RBR_SWAY_PHASE"


def wrap_with_debug_shader(
    color_socket: bpy.types.NodeSocket,
    alpha_socket: bpy.types.NodeSocket,
    other_shader_socket: bpy.types.NodeSocket,
) -> bpy.types.NodeSocket:
    if bpy.context.scene.rbr_global_shader_flags.only_display_color:
        socket = color_socket
    elif bpy.context.scene.rbr_global_shader_flags.only_display_alpha:
        socket = alpha_socket
    else:
        socket = other_shader_socket
    return socket


def get_object_type(node_tree: bpy.types.NodeTree) -> bpy.types.NodeSocket:
    node = node_tree.nodes.new("ShaderNodeAttribute")
    node.attribute_type = "OBJECT"
    node.attribute_name = "rbr_object_type_value"
    return node.outputs["Fac"]


def check_object_type(
    node_tree: bpy.types.NodeTree,
    object_type_socket: bpy.types.NodeSocket,
    object_type: RBRObjectType,
) -> bpy.types.NodeSocket:
    return make_math_node(
        node_tree,
        "COMPARE",
        object_type_socket,
        float(object_type.value),
        clamp=True,
    )


@dataclass
class PipelineType:
    color: bpy.types.NodeSocket
    alpha: bpy.types.NodeSocket
    # We only need to override the amplitude for non object block objects.
    sway_amp: bpy.types.NodeSocket
    specular: bpy.types.NodeSocket


def multiply_scattering(
    node_tree: bpy.types.NodeTree,
    vcol_in: bpy.types.NodeSocketColor,
    sun_dir: bpy.types.NodeSocketVector,
    light_dir: bpy.types.NodeSocketVector,
) -> Tuple[bpy.types.NodeSocketColor, bpy.types.NodeSocketColor]:
    geo_node = node_tree.nodes.new("ShaderNodeNewGeometry")
    # geo_node.outputs["Position"]

    turbidity = sky.make_value(node_tree, sky.SKY_TURBIDITY)
    camera_data = node_tree.nodes.new("ShaderNodeCameraData")
    view_depth = camera_data.outputs["View Z Depth"]
    # Left hand view vector to match left hand light dir
    view_vector = sky.flip_handedness(node_tree, geo_node.outputs["Incoming"])
    # view_vector = vector_scale(node_tree, vector=geo_node.outputs["Incoming"], scale=-1.0)
    # Different scale for different object types
    object_type_socket = get_object_type(node_tree)
    is_superbowl = check_object_type(
        node_tree, object_type_socket, RBRObjectType.SUPER_BOWL
    )
    is_not_superbowl = make_math_node(node_tree, "SUBTRACT", in1=1.0, in2=is_superbowl)
    superbowl_scale = sky.make_value(node_tree, sky.SKY_SUPERBOWL_SCALE)
    scale = make_math_node(node_tree, "MULTIPLY", in1=is_superbowl, in2=superbowl_scale)
    scale = make_math_node(node_tree, "ADD", in1=scale, in2=is_not_superbowl)
    scattering_depth = make_math_node(node_tree, "MULTIPLY", in1=view_depth, in2=scale)
    (r1, rayleigh_mie) = sky.setup_rayleigh_mie_nodes(
        node_tree=node_tree,
        view_vector=view_vector,
        turbidity=turbidity,
        scattering_depth=scattering_depth,
        light_dir=light_dir,
    )
    # Terrain reflectance
    terrain_reflectance_multiplier = make_value(
        node_tree, sky.SKY_TERRAIN_REFLECTANCE_MULTIPLIER
    )
    terrain_reflectance_color = make_vector_value(
        node_tree, sky.SKY_TERRAIN_REFLECTANCE_COLOR
    )
    terrain_reflectance = vector_scale(
        node_tree,
        vector=terrain_reflectance_color,
        scale=terrain_reflectance_multiplier,
    )
    # Inscattering
    inscattering = make_value(node_tree, sky.SKY_INSCATTERING)
    # Transmittance
    sun_offset = make_value(node_tree, sky.SKY_SUN_OFFSET)
    transmittance = sky.setup_transmittance_nodes(
        node_tree=node_tree,
        turbidity=turbidity,
        sun_dir=sun_dir,
        sun_offset=sun_offset,
    )
    # Sun intensity
    sun_intensity = make_value(node_tree, sky.SKY_SUN_INTENSITY)

    add_result = vector_scale(node_tree, vector=rayleigh_mie, scale=inscattering)
    add_result = vector_multiply(node_tree, v1=add_result, v2=transmittance)
    add_result = vector_scale(node_tree, vector=add_result, scale=sun_intensity)

    # MULTIPLY
    mul_result = vector_multiply(node_tree, v1=r1, v2=terrain_reflectance)
    # Extinction
    extinction = make_value(node_tree, sky.SKY_EXTINCTION)
    mul_result = vector_scale(node_tree, vector=mul_result, scale=extinction)
    # Multiply transmittance
    mul_result = vector_multiply(node_tree, v1=mul_result, v2=transmittance)
    mul_result = vector_scale(node_tree, vector=mul_result, scale=sun_intensity)

    return (
        mix_rgb(
            node_tree=node_tree,
            fac=1.0,
            a=vcol_in,
            b=mul_result,
            blend_type="MULTIPLY",
            clamp=True,
        ),
        add_result,
    )


def make_bsdf(
    node_tree: bpy.types.NodeTree,
    render_type: RenderType,
) -> Tuple[bpy.types.NodeSocketShader, bpy.types.NodeSocketVector]:
    """Returns (surface socket, displacement socket). We can't branch on shading
    type while building this, because a single tree is used for all shadinr
    types.
    """
    if render_type.has_diffuse_1():
        diffuse_1_color = node_tree.nodes["Group Input"].outputs[
            RBR_DIFFUSE_1_TEXTURE_INPUT
        ]
        diffuse_1_alpha = node_tree.nodes["Group Input"].outputs[
            RBR_DIFFUSE_1_ALPHA_INPUT
        ]
        if render_type.has_diffuse_2():
            diffuse_2_color = node_tree.nodes["Group Input"].outputs[
                RBR_DIFFUSE_2_TEXTURE_INPUT
            ]
            diffuse_2_alpha = node_tree.nodes["Group Input"].outputs[
                RBR_DIFFUSE_2_ALPHA_INPUT
            ]
        if render_type.has_specular():
            specular_color = node_tree.nodes["Group Input"].outputs[
                RBR_SPECULAR_TEXTURE_INPUT
            ]
            vcol_spec = node_tree.nodes["Group Input"].outputs[
                RBR_SPECULAR_STRENGTH_INPUT_NAME
            ]
    sun_dir = make_vector_value(node_tree, sky.SKY_SUN_DIR)
    light_dir = vector_scale(node_tree, vector=sun_dir, scale=-1.0)
    # This is actually sRGB already
    vcol_in = node_tree.nodes["Group Input"].outputs[RBR_COLOR_INPUT_NAME]
    flags: RBRGlobalShaderFlags = bpy.context.scene.rbr_global_shader_flags
    # Scattering, only for RBR mode with textures
    if render_type.has_diffuse_1():
        (vcol, add_scattering) = multiply_scattering(
            node_tree=node_tree,
            vcol_in=vcol_in,
            sun_dir=sun_dir,
            light_dir=light_dir,
        )
    else:
        vcol = vcol_in
        add_scattering = (0, 0, 0, 0)
    vcol_alpha = node_tree.nodes["Group Input"].outputs[RBR_ALPHA_INPUT_NAME]
    # Sway inputs to the displacement socket
    sway_freq = node_tree.nodes["Group Input"].outputs[RBR_SWAY_FREQ_INPUT_NAME]
    sway_amp = node_tree.nodes["Group Input"].outputs[RBR_SWAY_AMP_INPUT_NAME]
    sway_phase = node_tree.nodes["Group Input"].outputs[RBR_SWAY_PHASE_INPUT_NAME]

    if not render_type.has_diffuse_1():
        diffuse = vcol
        alpha = vcol_alpha
    elif render_type.has_diffuse_1() and not render_type.has_diffuse_2():
        alpha = make_math_node(
            node_tree,
            "MULTIPLY",
            vcol_alpha,
            diffuse_1_alpha,
            clamp=True,
        )
        # Multiply vertex colors and the first texture
        diffuse = mix_rgb(
            node_tree=node_tree,
            fac=1.0,
            a=vcol,
            b=diffuse_1_color,
            blend_type="MULTIPLY",
            clamp=True,
        )
    elif render_type.has_diffuse_1() and render_type.has_diffuse_2():
        # Multiply vertex colors and the first texture
        node_r0_xyz = mix_rgb(
            node_tree=node_tree,
            fac=1.0,
            a=vcol,
            b=diffuse_1_color,
            blend_type="MULTIPLY",
            clamp=True,
        )
        # Multiply vertex colors and the second texture
        node_r1_xyz = mix_rgb(
            node_tree=node_tree,
            fac=1.0,
            a=vcol,
            b=diffuse_2_color,
            blend_type="MULTIPLY",
            clamp=True,
        )
        alpha = make_math_node(
            node_tree,
            "MULTIPLY",
            vcol_alpha,
            diffuse_1_alpha,
            clamp=True,
        )
        node_r1_w = make_math_node(
            node_tree,
            "MULTIPLY",
            vcol_alpha,
            diffuse_2_alpha,
            clamp=True,
        )
        # Linear interpolate the results according to r1_w
        diffuse = mix_rgb(
            node_tree=node_tree,
            fac=node_r1_w,
            a=node_r0_xyz,
            b=node_r1_xyz,
            blend_type="MIX",
            clamp=True,
        )

    # Tweak the visible alpha and color values to match RBR for each object
    # type. We do this by building a chain of mix shaders using a type
    # comparison as the factor input.
    object_type_socket = get_object_type(node_tree)

    BROKEN_COLOR = (1, 0, 0, 1)
    BROKEN_ALPHA = (1, 1, 1, 1)

    def clip(in_socket: Union[float, bpy.types.NodeSocket]) -> bpy.types.NodeSocket:
        return make_math_node(node_tree, "LESS_THAN", 0.8, in_socket)

    # Textured geom blocks don't have alpha support
    def tweak_geom_blocks(inp: PipelineType) -> PipelineType:
        color_out = inp.color
        is_geom_block = check_object_type(
            node_tree, object_type_socket, RBRObjectType.GEOM_BLOCKS
        )
        if render_type.has_diffuse_1():
            alpha_out = mix_rgb(
                node_tree=node_tree,
                fac=is_geom_block,
                a=inp.alpha,
                b=(1, 1, 1, 1),
            )
        else:
            alpha_out = inp.alpha
        return PipelineType(
            color=color_out,
            alpha=alpha_out,
            sway_amp=inp.sway_amp,
            specular=inp.specular,
        )

    # Object blocks only support exactly one diffuse texture.
    def tweak_object_blocks(inp: PipelineType) -> PipelineType:
        is_object_block = check_object_type(
            node_tree, object_type_socket, RBRObjectType.OBJECT_BLOCKS
        )
        if render_type.has_diffuse_1() and not render_type.has_diffuse_2():
            color_out = inp.color
            alpha_out = inp.alpha
        else:
            color_out = mix_rgb(
                node_tree=node_tree,
                fac=is_object_block,
                a=inp.color,
                b=BROKEN_COLOR,
            )
            alpha_out = mix_rgb(
                node_tree=node_tree,
                fac=is_object_block,
                a=inp.alpha,
                b=BROKEN_ALPHA,
            )
        sway_out = mix_rgb(
            node_tree=node_tree,
            fac=is_object_block,
            a=(0, 0, 0, 0),
            b=inp.sway_amp,
        )
        specular_out = mix_rgb(
            node_tree=node_tree,
            fac=is_object_block,
            a=inp.specular,
            b=(0, 0, 0, 0),
        )
        return PipelineType(
            color=color_out,
            alpha=alpha_out,
            sway_amp=sway_out,
            specular=specular_out,
        )

    # Super bowl objects don't have alpha or specular support, and the single
    # texture case clips at 80% opacity
    def tweak_super_bowl(inp: PipelineType) -> PipelineType:
        is_super_bowl = check_object_type(
            node_tree, object_type_socket, RBRObjectType.SUPER_BOWL
        )
        if render_type.has_diffuse_1() and not render_type.has_diffuse_2():
            alpha_in = clip(inp.alpha)
        else:
            alpha_in = (1, 1, 1, 1)
        alpha_out = mix_rgb(
            node_tree=node_tree,
            fac=is_super_bowl,
            a=inp.alpha,
            b=alpha_in,
        )
        specular_out = mix_rgb(
            node_tree=node_tree,
            fac=is_super_bowl,
            a=inp.specular,
            b=(0, 0, 0, 0),
        )
        return PipelineType(
            color=inp.color,
            alpha=alpha_out,
            sway_amp=inp.sway_amp,
            specular=specular_out,
        )

    # Reflection objects don't support untextured or specular textures.
    def tweak_reflection_objects(inp: PipelineType) -> PipelineType:
        is_reflection_object = check_object_type(
            node_tree, object_type_socket, RBRObjectType.REFLECTION_OBJECTS
        )
        if not render_type.has_diffuse_1():
            color_out = mix_rgb(
                node_tree=node_tree,
                fac=is_reflection_object,
                a=inp.color,
                b=BROKEN_COLOR,
            )
            alpha_out = mix_rgb(
                node_tree=node_tree,
                fac=is_reflection_object,
                a=inp.alpha,
                b=BROKEN_ALPHA,
            )
        else:
            color_out = inp.color
            alpha_out = inp.alpha
        specular_out = mix_rgb(
            node_tree=node_tree,
            fac=is_reflection_object,
            a=inp.specular,
            b=(0, 0, 0, 0),
        )
        return PipelineType(
            color=color_out,
            alpha=alpha_out,
            sway_amp=inp.sway_amp,
            specular=specular_out,
        )

    # Water objects must be textured, but their specularity doesn't work.
    # Also, their UV animation only works if they have a specular texture.
    def tweak_water_objects(inp: PipelineType) -> PipelineType:
        is_water_object = check_object_type(
            node_tree, object_type_socket, RBRObjectType.WATER_OBJECTS
        )
        if not render_type.has_diffuse_1():
            color_out = mix_rgb(
                node_tree=node_tree,
                fac=is_water_object,
                a=inp.color,
                b=BROKEN_COLOR,
            )
            alpha_out = mix_rgb(
                node_tree=node_tree,
                fac=is_water_object,
                a=inp.alpha,
                b=BROKEN_ALPHA,
            )
        else:
            color_out = inp.color
            alpha_out = inp.alpha
        specular_out = mix_rgb(
            node_tree=node_tree,
            fac=is_water_object,
            a=inp.specular,
            b=(0, 0, 0, 0),
        )
        return PipelineType(
            color=color_out,
            alpha=alpha_out,
            sway_amp=inp.sway_amp,
            specular=specular_out,
        )

    # Interactive objects don't have alpha, untextured, or specular support,
    # and the single texture case clips at 80% opacity
    def tweak_interactive_objects(inp: PipelineType) -> PipelineType:
        is_interactive_object = check_object_type(
            node_tree, object_type_socket, RBRObjectType.INTERACTIVE_OBJECTS
        )
        color_in = None
        if not render_type.has_diffuse_1():
            color_in = BROKEN_COLOR
            alpha_in = BROKEN_ALPHA
        elif render_type.has_diffuse_2():
            alpha_in = (1, 1, 1, 1)
        else:
            alpha_in = clip(inp.alpha)
        if color_in is not None:
            color_out = mix_rgb(
                node_tree=node_tree,
                fac=is_interactive_object,
                a=inp.color,
                b=color_in,
            )
        else:
            color_out = inp.color
        alpha_out = mix_rgb(
            node_tree=node_tree,
            fac=is_interactive_object,
            a=inp.alpha,
            b=alpha_in,
        )
        specular_out = mix_rgb(
            node_tree=node_tree,
            fac=is_interactive_object,
            a=inp.specular,
            b=(0, 0, 0, 0),
        )
        return PipelineType(
            color=color_out,
            alpha=alpha_out,
            sway_amp=inp.sway_amp,
            specular=specular_out,
        )

    pipeline_result = fold_compose(
        [
            tweak_geom_blocks,
            tweak_object_blocks,
            tweak_super_bowl,
            tweak_reflection_objects,
            tweak_water_objects,
            tweak_interactive_objects,
        ]
    )(
        PipelineType(
            color=diffuse, alpha=alpha, sway_amp=sway_amp, specular=(1, 1, 1, 1)
        )
    )

    # Add the scattering
    result = mix_rgb(
        node_tree=node_tree,
        fac=1.0,
        a=add_scattering,
        b=pipeline_result.color,
        blend_type="ADD",
        clamp=True,
    )

    # Fog
    is_superbowl = check_object_type(
        node_tree, object_type_socket, RBRObjectType.SUPER_BOWL
    )
    is_not_superbowl = make_math_node(node_tree, "SUBTRACT", in1=1.0, in2=is_superbowl)
    other_fog_start = make_value(node_tree, sky.SKY_FOG_START)
    other_fog_start = make_math_node(
        node_tree, "MULTIPLY", in1=other_fog_start, in2=is_not_superbowl
    )
    superbowl_fog_start = make_value(node_tree, sky.SKY_SUPERBOWL_FOG_START)
    superbowl_fog_start = make_math_node(
        node_tree, "MULTIPLY", in1=superbowl_fog_start, in2=is_superbowl
    )
    fog_start = make_math_node(
        node_tree, "ADD", in1=superbowl_fog_start, in2=other_fog_start
    )
    other_fog_end = make_value(node_tree, sky.SKY_FOG_END)
    other_fog_end = make_math_node(
        node_tree, "MULTIPLY", in1=other_fog_end, in2=is_not_superbowl
    )
    superbowl_fog_end = make_value(node_tree, sky.SKY_SUPERBOWL_FOG_END)
    superbowl_fog_end = make_math_node(
        node_tree, "MULTIPLY", in1=superbowl_fog_end, in2=is_superbowl
    )
    fog_end = make_math_node(node_tree, "ADD", in1=superbowl_fog_end, in2=other_fog_end)
    camera_data = node_tree.nodes.new("ShaderNodeCameraData")
    depth = camera_data.outputs["View Distance"]
    fog_numerator = make_math_node(node_tree, "SUBTRACT", in1=fog_end, in2=depth)
    fog_denominator = make_math_node(node_tree, "SUBTRACT", in1=fog_end, in2=fog_start)
    fog_calc = make_math_node(
        node_tree, "DIVIDE", in1=fog_numerator, in2=fog_denominator
    )
    use_fog = make_value(node_tree, sky.SKY_USE_FOG)
    inv_fog = make_math_node(node_tree, "SUBTRACT", in1=1.0, in2=use_fog)
    fog_mix = make_math_node(node_tree, "MAXIMUM", in1=fog_calc, in2=inv_fog)
    fog_color = make_vector_value(node_tree, sky.SKY_FOG_COLOR)
    result = mix_rgb(node_tree, fac=fog_mix, a=fog_color, b=result, blend_type="MIX")

    # Back to linear now we've done all of the (bad) sRGB multiplications.
    linear_color = srgb_to_linear(node_tree, result)

    # Compute displacement
    # It's really slow (when playing the timeline) so we disable it by default.
    # Note that disabling this after enabling it may still be laggy until the
    # material shader node is modified.
    if flags.realtime_displacement:
        time = node_tree.nodes.new("ShaderNodeTime").outputs["Time"]
    else:
        time = node_tree.nodes.new("ShaderNodeValue").outputs[0]
    disp_pre_sin = make_math_node(
        node_tree,
        "MULTIPLY_ADD",
        sway_freq,
        time,
        sway_phase,
    )
    disp_sin = make_math_node(
        node_tree,
        "SINE",
        disp_pre_sin,
    )
    sway_displacement_value = make_math_node(
        node_tree,
        "MULTIPLY",
        disp_sin,
        pipeline_result.sway_amp,
    )
    # There is a wind strength coefficient hardcoded to 0.15.
    sway_displacement_coeff = make_math_node(
        node_tree,
        "MULTIPLY",
        sway_displacement_value,
        # I don't know why we need this to be half the expected value.
        # Maybe the 'sin' implementation is bad.
        0.15 * 0.5,
    )
    # RBR only sways in X direction, it's hardcoded in the vertex shader.
    sway_displacement_node = node_tree.nodes.new("ShaderNodeCombineXYZ")
    node_tree.links.new(
        sway_displacement_node.inputs["X"],
        sway_displacement_coeff,
    )
    sway_displacement = sway_displacement_node.outputs["Vector"]

    if render_type.has_specular():
        # This implements SpecularVSFragment.hlsl and the use of it in
        # RLDoubleTextureSpecular.hlsl
        geometry = node_tree.nodes.new("ShaderNodeNewGeometry")
        # TODO does this point the right way?
        view_vector = sky.flip_handedness(node_tree, geometry.outputs["Incoming"])
        normal = geometry.outputs["Normal"]

        add_half = node_tree.nodes.new("ShaderNodeVectorMath")
        add_half.operation = "ADD"
        node_tree.links.new(add_half.inputs[0], light_dir)
        node_tree.links.new(add_half.inputs[1], view_vector)

        halfway_vector = node_tree.nodes.new("ShaderNodeVectorMath")
        halfway_vector.operation = "NORMALIZE"
        node_tree.links.new(halfway_vector.inputs[0], add_half.outputs["Vector"])

        dot = node_tree.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        node_tree.links.new(dot.inputs[0], normal)
        node_tree.links.new(dot.inputs[1], halfway_vector.outputs["Vector"])

        divide_dot = make_math_node(
            node_tree, "DIVIDE", in1=1.0, in2=dot.outputs["Value"]
        )
        r1 = make_math_node(node_tree, "MULTIPLY", in1=divide_dot, in2=divide_dot)
        subtract_beckmann = make_math_node(node_tree, "SUBTRACT", in1=1.0, in2=r1)
        beckmann_glossiness = sky.make_value(node_tree, sky.SKY_SPECULAR_GLOSSINESS)
        beckmann_alpha = sky.make_value(node_tree, sky.SKY_SPECULAR_ALPHA)
        mul_gloss = make_math_node(
            node_tree, "MULTIPLY", in1=subtract_beckmann, in2=beckmann_glossiness
        )
        gloss_pow = make_math_node(node_tree, "POWER", in1=2.0, in2=mul_gloss)
        gloss_pow_2 = make_math_node(node_tree, "MULTIPLY", in1=gloss_pow, in2=r1)
        gloss_pow_3 = make_math_node(node_tree, "MULTIPLY", in1=gloss_pow_2, in2=r1)
        mul_alpha = make_math_node(
            node_tree, "MULTIPLY", in1=gloss_pow_3, in2=beckmann_alpha
        )
        mul_strength = make_math_node(
            node_tree, "MULTIPLY", in1=mul_alpha, in2=vcol_spec
        )
        mul_strength_4 = make_math_node(
            node_tree, "MULTIPLY", in1=mul_strength, in2=4.0
        )
        mul_bad = make_math_node(
            node_tree, "MULTIPLY", in1=mul_strength_4, in2=pipeline_result.specular
        )
        specular_out = mix_rgb(
            node_tree=node_tree,
            fac=1.0,
            a=specular_color,
            b=mul_bad,
            blend_type="MULTIPLY",
        )
        output = make_alpha_shader(
            node_tree=node_tree,
            color=mix_rgb(
                node_tree=node_tree,
                fac=1.0,
                a=linear_color,
                b=specular_out,
                blend_type="ADD",
            ),
            alpha=pipeline_result.alpha,
        )
    else:
        output = make_alpha_shader(
            node_tree=node_tree,
            color=linear_color,
            alpha=pipeline_result.alpha,
        )

    return (
        wrap_with_debug_shader(
            color_socket=vcol,
            alpha_socket=vcol_alpha,
            other_shader_socket=output,
        ),
        sway_displacement,
    )


def make_alpha_shader(
    node_tree: bpy.types.NodeTree,
    color: bpy.types.NodeSocket,
    alpha: bpy.types.NodeSocket,
) -> bpy.types.NodeSocket:
    mix = node_tree.nodes.new("ShaderNodeMixShader")
    transparent = node_tree.nodes.new("ShaderNodeBsdfTransparent")
    # We must clamp the alpha to slightly greater than 0, or blender will
    # display the colour as black.
    alpha_clamp = make_math_node(
        node_tree,
        "MAXIMUM",
        in1=alpha,
        in2=0.000001,
    )
    node_tree.links.new(mix.inputs[0], alpha_clamp)
    node_tree.links.new(mix.inputs[1], transparent.outputs["BSDF"])
    node_tree.links.new(mix.inputs[2], color)
    return mix.outputs["Shader"]


RBR_DIFFUSE_1_TEXTURE_INPUT: str = "Diffuse Texture 1"
RBR_DIFFUSE_2_TEXTURE_INPUT: str = "Diffuse Texture 2"
RBR_SPECULAR_TEXTURE_INPUT: str = "Specular Texture"
RBR_DIFFUSE_1_ALPHA_INPUT: str = "Diffuse Texture 1 Alpha"
RBR_DIFFUSE_2_ALPHA_INPUT: str = "Diffuse Texture 2 Alpha"
RBR_COLOR_INPUT_NAME: str = "Color"
RBR_ALPHA_INPUT_NAME: str = "Alpha"
RBR_SPECULAR_STRENGTH_INPUT_NAME: str = "Specular Strength"
RBR_SWAY_FREQ_INPUT_NAME: str = "Sway Frequency"
RBR_SWAY_AMP_INPUT_NAME: str = "Sway Amplitude"
RBR_SWAY_PHASE_INPUT_NAME: str = "Sway Phase Offset"


def render_type_to_shader_name(render_type: RenderType) -> str:
    return sky.SHADER_PREFIX + render_type.name.title().replace("_", "")


def use_bsdf_node_tree(
    context: bpy.types.Context, render_type: RenderType
) -> bpy.types.NodeTree:
    name = render_type_to_shader_name(render_type)
    node_tree = bpy.data.node_groups.get(name)
    if node_tree is None:
        node_tree = create_bsdf_node_tree(context, render_type)
    return node_tree


def recreate_internals(context: bpy.types.Context) -> None:
    # Update the _trees_
    for node_tree in bpy.data.node_groups:
        if not node_tree.name.startswith(sky.SHADER_PREFIX):
            continue
        for render_type in RenderType:
            # Deal with matches
            if node_tree.name == render_type_to_shader_name(render_type):
                break
            # Deal with duplicates (due to libraries) with names like
            # .ShaderNodeRBR.DoubleTexture.001
            if node_tree.name.startswith(render_type_to_shader_name(render_type) + "."):
                break
        else:
            continue
        node_tree.links.clear()
        for node in node_tree.nodes:
            if isinstance(node, bpy.types.NodeGroupInput):
                continue
            if isinstance(node, bpy.types.NodeGroupOutput):
                continue
            node_tree.nodes.remove(node)

        node_tree.interface.clear()
        create_sockets(node_tree, render_type)

        make_nodes_and_links(
            context=context,
            node_tree=node_tree,
            render_type=render_type,
        )

    # Update the _nodes_ (to reset color/alpha default values)
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if not isinstance(node, ShaderNodeRBR):
                continue
            node.select_node_tree(context)


def create_bsdf_node_tree(
    context: bpy.types.Context, render_type: RenderType
) -> bpy.types.NodeTree:
    node_tree = bpy.data.node_groups.new(
        render_type_to_shader_name(render_type),
        "ShaderNodeTree",
    )
    node_tree.nodes.new("NodeGroupInput")
    node_tree.nodes.new("NodeGroupOutput")
    create_sockets(node_tree, render_type)

    make_nodes_and_links(
        context=context,
        node_tree=node_tree,
        render_type=render_type,
    )
    return node_tree


def create_sockets(
    node_tree: bpy.types.NodeTree,
    render_type: RenderType,
) -> None:
    def add_input_socket(
        name: str,
        node_type: str,
        hide_value: bool,
        min: Optional[float] = None,
        max: Optional[float] = None,
    ) -> None:
        socket = node_tree.interface.new_socket(
            name, in_out="INPUT", socket_type=node_type
        )
        if min is not None:
            socket.min_value = min
        if max is not None:
            socket.max_value = max
        socket.hide_value = hide_value

    if render_type.has_diffuse_1():
        add_input_socket(
            name=RBR_DIFFUSE_1_TEXTURE_INPUT,
            node_type="NodeSocketColor",
            hide_value=True,
        )
        add_input_socket(
            name=RBR_DIFFUSE_1_ALPHA_INPUT,
            node_type="NodeSocketFloat",
            hide_value=True,
        )
        if render_type.has_diffuse_2():
            add_input_socket(
                name=RBR_DIFFUSE_2_TEXTURE_INPUT,
                node_type="NodeSocketColor",
                hide_value=True,
            )
            add_input_socket(
                name=RBR_DIFFUSE_2_ALPHA_INPUT,
                node_type="NodeSocketFloat",
                hide_value=True,
            )
        if render_type.has_specular():
            add_input_socket(
                name=RBR_SPECULAR_TEXTURE_INPUT,
                node_type="NodeSocketColor",
                hide_value=True,
            )
            add_input_socket(
                name=RBR_SPECULAR_STRENGTH_INPUT_NAME,
                node_type="NodeSocketFloat",
                hide_value=False,
                min=0.0,
                max=1.0,
            )
    add_input_socket(
        name=RBR_COLOR_INPUT_NAME,
        node_type="NodeSocketColor",
        hide_value=True,
    )
    add_input_socket(
        name=RBR_ALPHA_INPUT_NAME,
        node_type="NodeSocketFloat",
        hide_value=True,
    )
    add_input_socket(
        name=RBR_SWAY_FREQ_INPUT_NAME,
        node_type="NodeSocketFloat",
        hide_value=False,
        min=-math.inf,
        max=math.inf,
    )
    add_input_socket(
        name=RBR_SWAY_AMP_INPUT_NAME,
        node_type="NodeSocketFloat",
        hide_value=False,
        min=-math.inf,
        max=math.inf,
    )
    add_input_socket(
        name=RBR_SWAY_PHASE_INPUT_NAME,
        node_type="NodeSocketFloat",
        hide_value=False,
        min=-math.inf,
        max=math.inf,
    )

    def add_output_socket(
        name: str,
        node_type: str,
        min: Optional[float] = None,
        max: Optional[float] = None,
    ) -> None:
        socket = node_tree.interface.new_socket(
            name, in_out="OUTPUT", socket_type=node_type
        )
        if min is not None:
            socket.min_value = min
        if max is not None:
            socket.max_value = max

    add_output_socket(
        name="Surface",
        node_type="NodeSocketShader",
    )
    add_output_socket(
        name="Displacement",
        node_type="NodeSocketVector",
    )


def make_nodes_and_links(
    context: bpy.types.Context,
    node_tree: bpy.types.NodeTree,
    render_type: RenderType,
) -> None:
    (surface, displacement) = make_bsdf(
        node_tree=node_tree,
        render_type=render_type,
    )
    node_tree.links.new(
        node_tree.nodes["Group Output"].inputs["Surface"],
        surface,
    )
    node_tree.links.new(
        node_tree.nodes["Group Output"].inputs["Displacement"],
        displacement,
    )


def reify_uv_map(
    node: bpy.types.Node,
    socket: bpy.types.NodeSocket,
) -> Optional[SomeUVMap]:
    if isinstance(socket, bpy.types.NodeSocketVector) and isinstance(
        node, bpy.types.ShaderNodeAttribute
    ):
        return UVMapAttr(node.attribute_name)
    elif isinstance(node, bpy.types.ShaderNodeUVMap):
        return UVMap(node.uv_map)
    else:
        return None


class ShaderNodeRBR(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodeRBR"
    bl_label = "RBR Shader"
    render_type: RenderType = RenderType.VERTEX_COLOR
    node_tree: Optional[bpy.types.NodeTree] = None

    # TODO handle shadows.
    def calculate_render_type(self) -> RenderType:
        if not self.has_diffuse_1:
            return RenderType.VERTEX_COLOR
        elif not self.has_diffuse_2:
            if self.has_specular:
                return RenderType.SINGLE_TEXTURE_SPECULAR
            else:
                return RenderType.SINGLE_TEXTURE
        else:
            if self.has_specular:
                return RenderType.DOUBLE_TEXTURE_SPECULAR
            else:
                return RenderType.DOUBLE_TEXTURE

    def select_node_tree(self, context: bpy.types.Context) -> None:
        render_type = self.calculate_render_type()
        # We need to relink the input/output links in the _user_ node tree
        # since they are lost when the node tree switches.
        # Sometimes blender tries to automatically move them, but it often moves
        # texture inputs to value/color inputs, so we remove them before
        # switching trees.
        parent_tree = self.id_data
        input_links = []
        output_links = []
        for link in parent_tree.links:
            if link.to_node == self:
                input_links.append((link.to_socket.name, link.from_socket))
            elif link.from_node == self:
                output_links.append((link.from_socket.name, link.to_socket))
            else:
                continue
            parent_tree.links.remove(link)
        self.node_tree = use_bsdf_node_tree(context, render_type)
        # This can overwrite user settings, but that seems fine. The node tree switch
        # will cause them to revert back to 0, which makes the object invisible and
        # black, which can be confusing for users. It's better to force it back to white.
        self.inputs[RBR_COLOR_INPUT_NAME].default_value = [1, 1, 1, 1]
        self.inputs[RBR_ALPHA_INPUT_NAME].default_value = 1
        for socket_name, from_socket in input_links:
            try:
                parent_tree.links.new(
                    self.inputs[socket_name],
                    from_socket,
                )
            except KeyError:
                # The input might have been removed.
                pass
        for socket_name, to_socket in output_links:
            # This changed between addon versions. This special case is for convenience.
            if socket_name == "Shader":
                socket_name = "Surface"
            parent_tree.links.new(
                self.outputs[socket_name],
                to_socket,
            )

    has_diffuse_1: bpy.props.BoolProperty(  # type: ignore
        name="Diffuse Texture 1",
        update=lambda self, context: self.select_node_tree(context),
    )
    has_diffuse_2: bpy.props.BoolProperty(  # type: ignore
        name="Diffuse Texture 2",
        update=lambda self, context: self.select_node_tree(context),
    )
    has_specular: bpy.props.BoolProperty(  # type: ignore
        name="Specular Texture",
        update=lambda self, context: self.select_node_tree(context),
    )

    # TODO WARNING All of these properties are due to be removed
    diffuse_1: bpy.props.StringProperty()  # type: ignore
    diffuse_1_uv: bpy.props.StringProperty()  # type: ignore
    diffuse_1_velocity: bpy.props.FloatVectorProperty(size=2)  # type: ignore
    diffuse_2: bpy.props.StringProperty()  # type: ignore
    diffuse_2_uv: bpy.props.StringProperty()  # type: ignore
    diffuse_2_velocity: bpy.props.FloatVectorProperty(size=2)  # type: ignore
    specular: bpy.props.StringProperty()  # type: ignore
    specular_uv: bpy.props.StringProperty()  # type: ignore
    specular_velocity: bpy.props.FloatVectorProperty(size=2)  # type: ignore

    def init(self, context: Optional[bpy.types.Context]) -> None:
        # context appears to be 'None' here, not sure why
        self.width = 200
        self.select_node_tree(bpy.context)

    def draw_buttons(
        self, context: bpy.types.Context, layout: bpy.types.UILayout
    ) -> None:
        layout.use_property_decorate = False  # No animation stuff

        layout.prop(self, "has_diffuse_1")
        if self.has_diffuse_1:
            layout.prop(self, "has_diffuse_2")
            layout.prop(self, "has_specular")
        # TODO warn by object type

    def copy(self, node) -> None:  # type: ignore
        pass

    def free(self) -> None:
        pass

    def walk_to_texture(
        self,
        material: bpy.types.Material,
        input_name: str,
    ) -> Tuple[Optional[str], Optional[SomeUVMap], Optional[Vector2]]:
        if not material.use_nodes:
            raise errors.E0138(material_name=material.name)
        node_tree = material.node_tree
        if self.name not in node_tree.nodes:
            raise errors.RBRAddonBug(
                f"Shader node is not in material {material.name}, this is an addon bug"
            )
        if input_name not in self.inputs:
            return (None, None, None)
        for link in node_tree.links:
            if link.to_socket == self.inputs[input_name]:
                texture_node = link.from_node
                break
        else:
            raise errors.E0139(material_name=material.name, input_name=input_name)
        if not isinstance(texture_node, ShaderNodeRBRTexture):
            raise errors.E0140(material_name=material.name, input_name=input_name)
        for link in node_tree.links:
            if link.to_socket == texture_node.inputs["UV"]:
                uv_node = link.from_node
                uv_from_socket = link.from_socket
                break
        else:
            raise errors.E0141(material_name=material.name)

        # Check for UV node or attr node directly connected
        uv_map = reify_uv_map(uv_node, uv_from_socket)
        if uv_map is not None:
            return (texture_node.texture_name_filename(), uv_map, None)
        # Check for velocity node and then UV node
        if not isinstance(uv_node, ShaderNodeUVVelocity):
            raise errors.E0142(material_name=material.name)
        for link in node_tree.links:
            if link.to_socket == uv_node.inputs["UV Velocity"]:
                raise errors.E0143(material_name=material.name)
        uv_velocity = Vector2(
            x=uv_node.inputs["UV Velocity"].default_value[0],
            y=-uv_node.inputs["UV Velocity"].default_value[1],
        )
        for link in node_tree.links:
            if link.to_socket == uv_node.inputs["UV"]:
                uv_map_node = link.from_node
                uv_map_from_socket = link.from_socket
                break
        else:
            raise errors.E0144(material_name=material.name)
        uv_map = reify_uv_map(uv_map_node, uv_map_from_socket)
        if uv_map is not None:
            return (texture_node.texture_name_filename(), uv_map, uv_velocity)
        else:
            raise errors.E0145(material_name=material.name)


def material_name(
    diffuse_1: Optional[bpy.types.NodeTree],
    diffuse_2: Optional[bpy.types.NodeTree],
    specular: Optional[bpy.types.NodeTree],
) -> str:
    def get_name(tree: Optional[bpy.types.NodeTree]) -> str:
        if tree is None:
            return ""
        name = tree_name_to_texture_name(tree)
        if name is None:
            return ""
        return name

    diffuse_1_name = get_name(diffuse_1)
    diffuse_2_name = get_name(diffuse_2)
    specular_name = get_name(specular)
    parts = [diffuse_1_name, diffuse_2_name, specular_name]
    return "_".join(filter(lambda x: x != "", parts))


def create_texture_and_uv(
    node_tree: bpy.types.NodeTree,
    tex_tree: bpy.types.NodeTree,
    uv_layer: str,
    color: bpy.types.NodeSocketColor,
    alpha: Optional[bpy.types.NodeSocketFloat],
    uv_velocity: List[float],  # FloatVectorProperty
) -> None:
    tex_node = node_tree.nodes.new("ShaderNodeRBRTexture")
    tex_node.node_tree = tex_tree
    node_tree.links.new(
        tex_node.outputs[RBR_TEXTURE_COLOR_OUTPUT],
        color,
    )
    if alpha is not None:
        node_tree.links.new(
            tex_node.outputs[RBR_TEXTURE_ALPHA_OUTPUT],
            alpha,
        )
    uv_node = node_tree.nodes.new("ShaderNodeUVMap")
    uv_node.uv_map = uv_layer
    if uv_velocity[0] == 0 and uv_velocity[1] == 0:
        node_tree.links.new(
            tex_node.inputs["UV"],
            uv_node.outputs["UV"],
        )
    else:
        uv_velocity_node = node_tree.nodes.new("ShaderNodeUVVelocity")
        uv_velocity_node.inputs["UV Velocity"].default_value = [
            uv_velocity[0],
            uv_velocity[1],
            0,
        ]
        node_tree.links.new(
            uv_velocity_node.inputs["UV"],
            uv_node.outputs["UV"],
        )
        node_tree.links.new(
            tex_node.inputs["UV"],
            uv_velocity_node.outputs["UV"],
        )


def make_rbr_blender_material(
    diffuse_1: Optional[bpy.types.NodeTree],
    diffuse_2: Optional[bpy.types.NodeTree],
    specular: Optional[bpy.types.NodeTree],
    uv_velocity: Optional[UVVelocity],
    sway: bool = False,
) -> bpy.types.Material:
    name = material_name(
        diffuse_1=diffuse_1,
        diffuse_2=diffuse_2,
        specular=specular,
    )
    # Attempt to find existing materials which match. We just use those if so.
    # This isn't perfect because it won't detect UVVelocity differences, but
    # I'm choosing to ignore that.
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name=name)
    # For sway displacement
    material.cycles.displacement_method = "BOTH"
    material.use_nodes = True
    node_tree = material.node_tree
    node_tree.links.clear()
    node_tree.nodes.clear()
    node_output_material = node_tree.nodes.new("ShaderNodeOutputMaterial")
    node_rbr = node_tree.nodes.new(ShaderNodeRBR.bl_name)
    if diffuse_1 is not None:
        node_rbr.has_diffuse_1 = True
        create_texture_and_uv(
            node_tree=node_tree,
            tex_tree=diffuse_1,
            uv_layer=UV_DIFFUSE_1,
            color=node_rbr.inputs[RBR_DIFFUSE_1_TEXTURE_INPUT],
            alpha=node_rbr.inputs[RBR_DIFFUSE_1_ALPHA_INPUT],
            uv_velocity=(
                [0, 0]
                if uv_velocity is None
                else [uv_velocity.diffuse_1.x, -uv_velocity.diffuse_1.y]
            ),
        )
        if diffuse_2 is not None:
            node_rbr.has_diffuse_2 = True
            create_texture_and_uv(
                node_tree=node_tree,
                tex_tree=diffuse_2,
                uv_layer=UV_DIFFUSE_2,
                color=node_rbr.inputs[RBR_DIFFUSE_2_TEXTURE_INPUT],
                alpha=node_rbr.inputs[RBR_DIFFUSE_2_ALPHA_INPUT],
                uv_velocity=(
                    [0, 0]
                    if uv_velocity is None
                    else [uv_velocity.diffuse_2.x, -uv_velocity.diffuse_2.y]
                ),
            )
        if specular is not None:
            node_rbr.has_specular = True
            create_texture_and_uv(
                node_tree=node_tree,
                tex_tree=specular,
                uv_layer=UV_SPECULAR,
                color=node_rbr.inputs[RBR_SPECULAR_TEXTURE_INPUT],
                alpha=None,
                uv_velocity=(
                    [0, 0]
                    if uv_velocity is None
                    else [uv_velocity.specular.x, -uv_velocity.specular.y]
                ),
            )

    def make_vc(
        layer_name: str,
        color_out: Optional[bpy.types.NodeSocket] = None,
        alpha_out: Optional[bpy.types.NodeSocket] = None,
    ) -> bpy.types.NodeSocket:
        node = node_tree.nodes.new("ShaderNodeVertexColor")
        node.layer_name = layer_name
        if color_out is not None:
            node_tree.links.new(
                color_out,
                node.outputs["Color"],
            )
        if alpha_out is not None:
            node_tree.links.new(
                alpha_out,
                node.outputs["Alpha"],
            )
        return node

    make_vc(
        layer_name=VC_COLOR,
        color_out=node_rbr.inputs[RBR_COLOR_INPUT_NAME],
        alpha_out=node_rbr.inputs[RBR_ALPHA_INPUT_NAME],
    )
    if specular is not None:
        make_vc(
            layer_name=VC_SPECULAR_STRENGTH,
            color_out=node_rbr.inputs[RBR_SPECULAR_STRENGTH_INPUT_NAME],
        )
    if sway:

        def make_multiply(
            layer_name: str,
            sway_input_name: str,
            multiplier: float,
        ) -> None:
            mult = make_math_node(
                node_tree,
                "MULTIPLY",
                in1=make_vc(
                    layer_name=layer_name,
                ).outputs["Color"],
                in2=multiplier,
            )
            node_tree.links.new(
                node_rbr.inputs[sway_input_name],
                mult,
            )

        make_multiply(
            layer_name=VC_SWAY_AMPLITUDE,
            sway_input_name=RBR_SWAY_AMP_INPUT_NAME,
            multiplier=5.0,
        )
        make_multiply(
            layer_name=VC_SWAY_FREQUENCY,
            sway_input_name=RBR_SWAY_FREQ_INPUT_NAME,
            multiplier=5.0,
        )
        make_multiply(
            layer_name=VC_SWAY_PHASE,
            sway_input_name=RBR_SWAY_PHASE_INPUT_NAME,
            multiplier=2 * math.pi,
        )

    node_tree.links.new(
        node_output_material.inputs["Surface"],
        node_rbr.outputs["Surface"],
    )
    node_tree.links.new(
        node_output_material.inputs["Displacement"],
        node_rbr.outputs["Displacement"],
    )
    return material


def register() -> None:
    bpy.utils.register_class(ShaderNodeRBR)


def unregister() -> None:
    bpy.utils.unregister_class(ShaderNodeRBR)
