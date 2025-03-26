"""A shader node equivalent for the RBR SkyDome shader.
"""

import math
from typing import Optional, Tuple

import bpy  # type: ignore
from mathutils import Vector  # type: ignore

from rbr_track_formats.common import Vector3
from .utils import (
    make_math_node,
    mix_rgb,
    vector_add,
    vector_exp,
    vector_math,
    vector_math_float,
    vector_multiply,
    vector_power,
    vector_scale,
    vector_subtract,
)
from ..object_settings.types import RBRObjectSettings, RBRObjectType


SKY_NODE_TREE_NAME: str = ".RBRSkyNodeTreeV0"


def compute_object_sun_dir_blender(
    obj: bpy.types.Object,
) -> Vector:
    """Compute sun direction as a blender vector"""
    (_pos, quat, _scale) = obj.matrix_world.decompose()
    v = Vector((0, 0, -1))
    v.rotate(quat)
    return v


def compute_left_hand_sun_dir(
    obj: bpy.types.Object,
) -> Vector3:
    """Compute sun direction as an RBR (left hand) vector"""
    v = compute_object_sun_dir_blender(obj)
    return Vector3.from_tuple(v.to_tuple()).flip_handedness().normalised()


def update_sun_dir() -> None:
    for obj in bpy.context.scene.objects:
        if not isinstance(obj.data, bpy.types.SunLight):
            continue
        settings: RBRObjectSettings = obj.rbr_object_settings
        if RBRObjectType[settings.type] is not RBRObjectType.SUN:
            continue
        if bpy.context.scene.rbr_track_settings.tint_set not in settings.tint_sets:
            continue
        sun_dir = compute_left_hand_sun_dir(obj)
        update_sky_vector(SKY_SUN_DIR, sun_dir.to_tuple())
        break


SHADER_PREFIX: str = ".ShaderNodeRBR."


def update_sky_value(node_name: str, value: float) -> None:
    for node_group in bpy.data.node_groups:
        if node_group.name == SKY_NODE_TREE_NAME or node_group.name.startswith(
            SHADER_PREFIX
        ):
            node = node_group.nodes.get(node_name)
            if node is not None:
                node.outputs[0].default_value = value


def update_sky_vector(node_name: str, value: Tuple[float, float, float]) -> None:
    for node_group in bpy.data.node_groups:
        if node_group.name == SKY_NODE_TREE_NAME or node_group.name.startswith(
            SHADER_PREFIX
        ):
            node = node_group.nodes.get(node_name)
            if node is not None:
                node.inputs["X"].default_value = value[0]
                node.inputs["Y"].default_value = value[1]
                node.inputs["Z"].default_value = value[2]


def make_wavelength(node_tree: bpy.types.NodeTree) -> bpy.types.NodeSocket:
    wavelength = node_tree.nodes.new("ShaderNodeCombineXYZ")
    wavelength.inputs["X"].default_value = 0.65
    wavelength.inputs["Y"].default_value = 0.57
    wavelength.inputs["Z"].default_value = 0.475
    return wavelength.outputs[0]


def flip_handedness(
    node_tree: bpy.types.NodeTree,
    vector: bpy.types.NodeSocketVector,
) -> bpy.types.NodeSocketVector:
    """Flip handedness (XYZ to XZY)"""
    separate = node_tree.nodes.new("ShaderNodeSeparateXYZ")
    node_tree.links.new(vector, separate.inputs[0])
    combine = node_tree.nodes.new("ShaderNodeCombineXYZ")
    node_tree.links.new(separate.outputs["X"], combine.inputs["X"])
    node_tree.links.new(separate.outputs["Y"], combine.inputs["Z"])
    node_tree.links.new(separate.outputs["Z"], combine.inputs["Y"])
    return combine.outputs[0]


def setup_transmittance_nodes(
    node_tree: bpy.types.NodeTree,
    turbidity: bpy.types.NodeSocketFloat,
    sun_dir: bpy.types.NodeSocketVector,
    sun_offset: bpy.types.NodeSocketFloat,
) -> bpy.types.NodeSocketVector:
    wavelength = make_wavelength(node_tree)
    # Compute Z (apparent solar zenith angle)
    sep_sun_dir = node_tree.nodes.new("ShaderNodeSeparateXYZ")
    node_tree.links.new(sun_dir, sep_sun_dir.inputs[0])
    sun_dir_y = sep_sun_dir.outputs["Y"]
    # Light direction is the opposite of the sun direction
    light_dir = make_math_node(node_tree, "MULTIPLY", in1=sun_dir_y, in2=-1.0)
    acos_light_dir = make_math_node(node_tree, "ARCCOSINE", in1=light_dir)
    mul_sun_offset = make_math_node(
        node_tree, "MULTIPLY", in1=sun_offset, in2=math.pi / 9
    )
    max_sun_offset = make_math_node(node_tree, "MAXIMUM", in1=mul_sun_offset, in2=0.0)
    min_sun_offset = make_math_node(
        node_tree, "MINIMUM", in1=max_sun_offset, in2=2 * math.pi
    )
    Z = make_math_node(node_tree, "SUBTRACT", in1=acos_light_dir, in2=min_sun_offset)
    # Compute M (relative air mass)
    cosZ = make_math_node(node_tree, "COSINE", in1=Z)
    degZ = make_math_node(node_tree, "MULTIPLY", in1=Z, in2=180.0 / math.pi)
    deg_sub = make_math_node(node_tree, "SUBTRACT", in1=93.885, in2=degZ)
    deg_pow = make_math_node(node_tree, "POWER", in1=deg_sub, in2=-1.253)
    deg_mul = make_math_node(node_tree, "MULTIPLY", in1=deg_pow, in2=0.15)
    add_cosZ = make_math_node(node_tree, "ADD", in1=cosZ, in2=deg_mul)
    M = make_math_node(node_tree, "POWER", in1=add_cosZ, in2=-1.0)
    # Compute T_a (aerosol scattering contribution)
    turbidity_mul = make_math_node(
        node_tree, "MULTIPLY", in1=turbidity, in2=0.046083659
    )
    B = make_math_node(node_tree, "SUBTRACT", in1=turbidity_mul, in2=0.045860261)
    negateB = make_math_node(node_tree, "MULTIPLY", in1=B, in2=-1.0)
    negateBM = make_math_node(node_tree, "MULTIPLY", in1=negateB, in2=M)
    wavelength_Ta = vector_power(node_tree, exponent=-1.3, vector=wavelength)
    T_a = vector_scale(node_tree, vector=wavelength_Ta, scale=negateBM)
    # Compute T_r (rayleigh scattering contribution)
    wavelength_Tr = vector_power(node_tree, exponent=-4.08, vector=wavelength)
    rayleighM = make_math_node(node_tree, "MULTIPLY", in1=M, in2=-0.008735)
    T_r = vector_scale(node_tree, vector=wavelength_Tr, scale=rayleighM)
    # Compute transmittance
    add_Ta_Tr = vector_add(node_tree, T_a, T_r)
    return vector_exp(node_tree, add_Ta_Tr)


def make_value(node_tree: bpy.types.NodeTree, name: str) -> bpy.types.NodeSocketFloat:
    node = node_tree.nodes.new("ShaderNodeValue")
    node.name = name
    return node.outputs[0]


def make_vector_value(
    node_tree: bpy.types.NodeTree, name: str
) -> bpy.types.NodeSocketVector:
    node = node_tree.nodes.new("ShaderNodeCombineXYZ")
    node.name = name
    return node.outputs[0]


SKY_FOG_COLOR: str = "Fog_Color"
SKY_GREENSTEIN_VALUE: str = "Greenstein_Value"
SKY_INSCATTERING: str = "Inscattering"
SKY_MIE_MULTIPLIER: str = "Mie_Multiplier"
SKY_SUN_DIR: str = "SunDir"
SKY_SUN_INTENSITY: str = "Sun_Intensity"
SKY_SUN_OFFSET: str = "SunOffset"
SKY_RAYLEIGH_MULTIPLIER: str = "Rayleigh_Multiplier"
SKY_SKYBOX_SATURATION: str = "SkyboxSaturation"
SKY_SKYBOX_SCALE: str = "Skybox_Scale"
SKY_TURBIDITY: str = "Turbidity"
SKY_USE_FOG: str = "UseFog"

SKY_EXTINCTION = "Extinction"
SKY_TERRAIN_REFLECTANCE_COLOR = "Terrain_Reflectance_Color"
SKY_TERRAIN_REFLECTANCE_MULTIPLIER = "Terrain_Reflectance_Multiplier"
SKY_SUPERBOWL_SCALE = "Superbowl_Scale"
SKY_FOG_START = "Fog_Start"
SKY_FOG_END = "Fog_End"
SKY_SUPERBOWL_FOG_START = "SuperbowlFogStart"
SKY_SUPERBOWL_FOG_END = "SuperbowlFogEnd"

SKY_SPECULAR_GLOSSINESS = "Specular_Glossiness"
SKY_SPECULAR_ALPHA = "Specular_Alpha"


def setup_rayleigh_mie_nodes(
    node_tree: bpy.types.NodeTree,
    view_vector: bpy.types.NodeSocketVector,
    turbidity: bpy.types.NodeSocketFloat,
    scattering_depth: bpy.types.NodeSocketFloat,
    light_dir: bpy.types.NodeSocketVector,
) -> bpy.types.NodeSocketVector:
    # The mixed Rayleigh-Mie values
    rayleigh_multiplier = make_value(node_tree, SKY_RAYLEIGH_MULTIPLIER)
    scaled_rayleigh_mixed = vector_scale(
        node_tree,
        vector=(
            0.00069715281,
            0.0011789137,
            0.0024445958,
        ),
        scale=rayleigh_multiplier,
    )
    mie_multiplier = make_value(node_tree, SKY_MIE_MULTIPLIER)
    mie_turbidity = make_math_node(node_tree, "MULTIPLY", in1=turbidity, in2=6.544)
    mie_turbidity = make_math_node(node_tree, "SUBTRACT", in1=mie_turbidity, in2=6.510)
    mie_contribution_mixed = vector_scale(
        node_tree,
        vector=(
            1.6213017e12 * 1.3634512 * 39.47842 * 9.99999983775159e-18,
            2.089874e12 * 1.3634512 * 39.47842 * 9.99999983775159e-18,
            2.9695295e12 * 1.3634512 * 39.47842 * 9.99999983775159e-18,
        ),
        scale=mie_turbidity,
    )
    scaled_mie_mixed = vector_scale(
        node_tree, vector=mie_contribution_mixed, scale=mie_multiplier
    )
    rayleigh_mie_mixed = vector_add(
        node_tree, v1=scaled_rayleigh_mixed, v2=scaled_mie_mixed
    )
    inverse_rayleigh_mie_mixed = vector_math(
        node_tree, "DIVIDE", v1=(1.0, 1.0, 1.0), v2=rayleigh_mie_mixed
    )

    # Rayleigh contributions
    cos_theta_dot = vector_math_float(
        node_tree, "DOT_PRODUCT", v1=view_vector, v2=light_dir
    )
    cos_theta = make_math_node(node_tree, "MINIMUM", in1=cos_theta_dot, in2=0.0)
    cos_theta_sq = make_math_node(node_tree, "MULTIPLY", in1=cos_theta, in2=cos_theta)
    rayleigh_phase = make_math_node(node_tree, "ADD", in1=cos_theta_sq, in2=1.0)
    rayleigh = vector_scale(
        node_tree,
        vector=(
            0.00004160824,
            0.000070361231,
            0.00014590107,
        ),
        scale=rayleigh_multiplier,
    )
    rayleigh_cont = vector_scale(node_tree, vector=rayleigh, scale=rayleigh_phase)
    # Greenstein values
    greenstein_value = make_value(node_tree, SKY_GREENSTEIN_VALUE)
    greenstein_x = make_math_node(
        node_tree, "MULTIPLY", in1=greenstein_value, in2=greenstein_value
    )
    greenstein_x = make_math_node(node_tree, "SUBTRACT", in1=1.0, in2=greenstein_x)
    greenstein_y = make_math_node(node_tree, "ADD", in1=greenstein_value, in2=1.0)
    greenstein_z = make_math_node(node_tree, "MULTIPLY", in1=greenstein_value, in2=2.0)
    # Henyey-Greenstein phase function
    hg_denominator = make_math_node(
        node_tree, "MULTIPLY", in1=greenstein_z, in2=cos_theta
    )
    hg_denominator = make_math_node(
        node_tree, "ADD", in1=hg_denominator, in2=greenstein_y
    )
    hg_denominator = make_math_node(node_tree, "ABSOLUTE", in1=hg_denominator)
    hg_denominator = make_math_node(node_tree, "POWER", in1=hg_denominator, in2=-1.5)
    henyey_greenstein_phase = make_math_node(
        node_tree, "MULTIPLY", in1=hg_denominator, in2=greenstein_x
    )
    # Mie contributions
    mie_contribution = vector_scale(
        node_tree,
        vector=(
            2.3668638e12 * 0.217 * 39.47842 * 9.99999983775159e-18,
            3.0778702e12 * 0.217 * 39.47842 * 9.99999983775159e-18,
            4.4321331e12 * 0.217 * 39.47842 * 9.99999983775159e-18,
        ),
        scale=mie_turbidity,
    )
    mie = vector_scale(node_tree, vector=mie_contribution, scale=mie_multiplier)
    mie_cont = vector_scale(node_tree, vector=mie, scale=henyey_greenstein_phase)
    # Combined Rayleigh-Mie
    add_rayleigh_mie = vector_add(node_tree, v1=rayleigh_cont, v2=mie_cont)
    negate_scattering_depth = make_math_node(
        node_tree, "MULTIPLY", in1=scattering_depth, in2=-1.0
    )
    rayleigh_mie_scaled = vector_scale(
        node_tree, vector=rayleigh_mie_mixed, scale=negate_scattering_depth
    )
    # Construct the result
    r1 = vector_exp(node_tree, rayleigh_mie_scaled)
    result = vector_subtract(node_tree, v1=(1.0, 1.0, 1.0), v2=r1)
    result = vector_multiply(node_tree, v1=add_rayleigh_mie, v2=result)
    result = vector_multiply(node_tree, v1=result, v2=inverse_rayleigh_mie_mixed)
    return (r1, result)


def recreate_internals() -> None:
    existing_tree = bpy.data.node_groups.get(SKY_NODE_TREE_NAME)
    if existing_tree is not None:
        setup_sky_node_tree(existing_tree)


def setup_sky_node_tree(node_tree: bpy.types.NodeTree) -> None:
    # Reset if already present
    node_tree.links.clear()
    output_exists = False
    for node in node_tree.nodes:
        if isinstance(node, bpy.types.NodeGroupOutput):
            output_exists = True
            continue
        node_tree.nodes.remove(node)
    # Create the internal group output node
    if not output_exists:
        node_tree.nodes.new("NodeGroupOutput")
    # Adjust the output sockets (this also adjusts the group outputs)
    seen_surface_output = False
    for item in node_tree.interface.items_tree:
        if item.item_type == "SOCKET":
            if item.in_out == "OUTPUT":
                if item.name == "Surface" and not seen_surface_output:
                    seen_surface_output = True
                    continue
        node_tree.interface.remove(item)
    if not seen_surface_output:
        node_tree.interface.new_socket(
            "Surface", in_out="OUTPUT", socket_type="NodeSocketShader"
        )

    # Create the internal nodes
    sun_dir = make_vector_value(node_tree, SKY_SUN_DIR)

    # Compute theta, the scattering angle
    skybox_scale = make_value(node_tree, SKY_SKYBOX_SCALE)
    geometry = node_tree.nodes.new("ShaderNodeNewGeometry")
    # Left hand to match the left hand light direction
    view_vector = flip_handedness(node_tree, geometry.outputs["Incoming"])

    # Compute depth to scattering point
    # Flip the view vector around
    flipped_view_vec = node_tree.nodes.new("ShaderNodeVectorMath")
    flipped_view_vec.operation = "SCALE"
    flipped_view_vec.inputs["Scale"].default_value = -1.0
    node_tree.links.new(geometry.outputs["Incoming"], flipped_view_vec.inputs[0])
    # Go from world to camera space
    transform = node_tree.nodes.new("ShaderNodeVectorTransform")
    transform.vector_type = "VECTOR"
    transform.convert_from = "WORLD"
    transform.convert_to = "CAMERA"
    node_tree.links.new(flipped_view_vec.outputs[0], transform.inputs[0])
    # Separate out Z (depth)
    view_vec_z = node_tree.nodes.new("ShaderNodeSeparateXYZ")
    node_tree.links.new(transform.outputs[0], view_vec_z.inputs[0])
    view_vec_z = view_vec_z.outputs["Z"]
    view_dome_z = make_math_node(node_tree, "MULTIPLY", in1=view_vec_z, in2=100.0)
    scattering_depth = make_math_node(
        node_tree, "MULTIPLY", in1=view_dome_z, in2=skybox_scale
    )
    # Rayleigh-Mie scattering
    turbidity = make_value(node_tree, SKY_TURBIDITY)
    light_dir = vector_scale(node_tree, vector=sun_dir, scale=-1.0)
    use_fog = make_value(node_tree, SKY_USE_FOG)
    (_, rayleigh_mie) = setup_rayleigh_mie_nodes(
        node_tree=node_tree,
        view_vector=view_vector,
        turbidity=turbidity,
        scattering_depth=scattering_depth,
        light_dir=light_dir,
    )
    # Multiply inscattering
    inscattering = make_value(node_tree, SKY_INSCATTERING)
    result = vector_scale(node_tree, vector=rayleigh_mie, scale=inscattering)
    # Multiply transmittance
    sun_offset = make_value(node_tree, SKY_SUN_OFFSET)
    transmittance = setup_transmittance_nodes(node_tree, turbidity, sun_dir, sun_offset)
    result = vector_multiply(node_tree, v1=result, v2=transmittance)
    # Multiply sun intensity
    sun_intensity = make_value(node_tree, SKY_SUN_INTENSITY)
    result = vector_scale(node_tree, vector=result, scale=sun_intensity)
    # Fog
    skybox_saturation = make_value(node_tree, SKY_SKYBOX_SATURATION)
    inv_fog = make_math_node(node_tree, "SUBTRACT", in1=1.0, in2=use_fog)
    fog_mix = make_math_node(node_tree, "MAXIMUM", in1=skybox_saturation, in2=inv_fog)
    fog_color = make_vector_value(node_tree, SKY_FOG_COLOR)
    result = mix_rgb(node_tree, fac=fog_mix, a=fog_color, b=result, blend_type="MIX")
    # Gamma correct
    gamma = node_tree.nodes.new("ShaderNodeGamma")
    gamma.inputs["Gamma"].default_value = 2.2
    node_tree.links.new(gamma.inputs["Color"], result)
    # Link to output
    node_tree.links.new(
        node_tree.nodes["Group Output"].inputs["Surface"],
        gamma.outputs[0],
    )


class ShaderNodeRBRSky(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodeRBRSky"
    bl_label = "RBR Sky"
    # This is a field of ShaderNodeCustomGroup
    node_tree: Optional[bpy.types.NodeTree] = None

    def init(self, context: Optional[bpy.types.Context]) -> None:
        existing_tree = bpy.data.node_groups.get(SKY_NODE_TREE_NAME)
        if existing_tree is not None:
            self.node_tree = existing_tree
        else:
            self.node_tree = bpy.data.node_groups.new(
                SKY_NODE_TREE_NAME, "ShaderNodeTree"
            )
            setup_sky_node_tree(self.node_tree)
        # The context passed in is 'None'
        bpy.context.scene.rbr_track_settings.update_sky_values()

    def free(self) -> None:
        return


@bpy.app.handlers.persistent  # type: ignore
def sun_direction_daemon(
    scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph
) -> None:
    """A little daemon which watches for sun object updates and updates the
    shaders.
    """
    for update in depsgraph.updates:
        if not update.is_updated_transform:
            continue
        if not isinstance(update.id, bpy.types.Object):
            continue
        obj = update.id
        # Check if we are a sun object
        object_settings: RBRObjectSettings = obj.rbr_object_settings
        if object_settings.type != RBRObjectType.SUN.name:
            continue
        if (
            bpy.context.scene.rbr_track_settings.tint_set
            not in object_settings.tint_sets
        ):
            continue
        sun_dir = compute_left_hand_sun_dir(obj)
        update_sky_vector(SKY_SUN_DIR, sun_dir.to_tuple())
        break


def register() -> None:
    bpy.utils.register_class(ShaderNodeRBRSky)
    bpy.app.handlers.depsgraph_update_post.append(sun_direction_daemon)


def unregister() -> None:
    try:
        bpy.app.handlers.depsgraph_update_post.remove(sun_direction_daemon)
    except ValueError:
        pass
    bpy.utils.unregister_class(ShaderNodeRBRSky)
