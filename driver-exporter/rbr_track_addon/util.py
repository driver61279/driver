from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Union
import math

import bpy  # type: ignore
from mathutils import Vector  # type: ignore
import numpy as np

from rbr_track_formats import errors
from rbr_track_formats.common import (
    Key,
    Vector2,
    AaBbBoundingBox,
    NumpyArray,
    NumpyDType,
)
from rbr_track_formats.dls.animation_sets import (
    RealChannel,
    RealChannelControlPoint,
    TriggerKind,
)
from rbr_track_formats.dls.splines import Interpolation
from rbr_track_formats import dtypes

from .blender_ops import create_cube
from rbr_track_formats.logger import Logger


def insert_control_point_keyframe(
    control_point: RealChannelControlPoint,
    obj: bpy.types.Object,
    data_path: str,
    length_rescale: float,
    fixup_val: Callable[[float], float] = lambda x: x,
) -> None:
    """Create a keyframe from a control point and value."""
    if obj.animation_data is None:
        obj.animation_data_create()
    if obj.animation_data is None:
        raise errors.RBRAddonBug(
            "Missing animation data in insert_control_point_keyframe"
        )
    if obj.animation_data.action is None:
        action = bpy.data.actions.new(data_path)
        obj.animation_data.action = action
    fcurve = obj.animation_data.action.fcurves.find(data_path)
    if fcurve is None:
        fcurve = obj.animation_data.action.fcurves.new(data_path)
    keyframe = fcurve.keyframe_points.insert(
        frame=control_point.position.x * length_rescale,
        value=control_point.position.y,
    )

    if control_point.interpolation is Interpolation.CONSTANT:
        keyframe.interpolation = "CONSTANT"
    elif control_point.interpolation is Interpolation.LINEAR:
        keyframe.interpolation = "LINEAR"
    elif control_point.interpolation is Interpolation.CUBIC_HERMITE:
        # Convert hermite derivatives to bezier points
        keyframe.interpolation = "BEZIER"
        keyframe.handle_left_type = "FREE"
        keyframe.handle_left = keyframe.co - Vector(
            (
                control_point.tangent_end.x / 3,
                control_point.tangent_end.y / 3,
            )
        )
        keyframe.handle_left.y = fixup_val(keyframe.handle_left.y)
        keyframe.handle_right_type = "FREE"
        keyframe.handle_right = keyframe.co + Vector(
            (
                control_point.tangent_start.x / 3,
                control_point.tangent_start.y / 3,
            )
        )
        keyframe.handle_right.y = fixup_val(keyframe.handle_right.y)
    keyframe.co.y = fixup_val(keyframe.co.y)


def fcurve_control_points(
    logger: Logger,
    fcurve: bpy.types.FCurve,
    fixup_val: Callable[[float], float],
) -> List[RealChannelControlPoint]:
    control_points = []
    for keyframe in fcurve.keyframe_points:
        if keyframe.interpolation == "CONSTANT":
            interpolation = Interpolation.CONSTANT
        elif keyframe.interpolation == "LINEAR":
            interpolation = Interpolation.LINEAR
        elif keyframe.interpolation == "BEZIER":
            interpolation = Interpolation.CUBIC_HERMITE
        else:
            logger.warn(
                f"Unsupported keyframe interpolation {keyframe.interpolation}"
                + " for RBR object. Must be CONSTANT, LINEAR, or BEZIER."
                + " Defaulting to bezier."
            )

        (pos_x, pos_y) = keyframe.co
        (left_x, left_y) = keyframe.handle_left
        (right_x, right_y) = keyframe.handle_right

        pos = Vector2(pos_x, fixup_val(pos_y))
        left = Vector2(left_x, fixup_val(left_y))
        right = Vector2(right_x, fixup_val(right_y))

        start = (right - pos).scale(3)
        end = (left - pos).scale(-3)

        control_points.append(
            RealChannelControlPoint(
                interpolation=interpolation,
                position=pos,
                tangent_end=end,
                tangent_start=start,
            )
        )
    return control_points


def constant_channel(value: float) -> List[RealChannelControlPoint]:
    return [
        RealChannelControlPoint(
            interpolation=Interpolation.CONSTANT,
            position=Vector2(0, value),
            tangent_end=Vector2(0, 0),
            tangent_start=Vector2(0, 0),
        )
    ]


def fcurve_real_channel(
    logger: Logger,
    key: Key,
    kind: TriggerKind,
    obj: Union[bpy.types.Object, bpy.types.Camera],
    prop: str,
    default: bool = True,
    fixup_val: Callable[[float], float] = lambda x: x,
) -> Optional[RealChannel]:
    """Create a real channel from an object (or camera) property. If the
    property is animated with an fcurve, use that, otherwise make a constant
    real channel."""
    try:
        assert obj.animation_data is not None, f"'{obj.name}' is missing animation data"
        assert obj.animation_data.action is not None, f"'{obj.name}' has no action"
        fcurve = obj.animation_data.action.fcurves.find(prop)
        assert fcurve is not None, f"'{obj.name}' has no f-curve for '{prop}'"
        assert (
            len(fcurve.keyframe_points) > 0
        ), f"'{obj.name}' has no keyframes for the '{prop}' f-curve"
        control_points = fcurve_control_points(logger, fcurve, fixup_val)
    except AssertionError as e:
        logger.warn(str(e))
        if default:
            val = getattr(obj, prop)
            logger.warn(f"Setting constant '{prop}' '{val}'")
            control_points = constant_channel(fixup_val(val))
        else:
            return None

    return RealChannel(
        id=key,
        kind=kind,
        control_points=control_points,
    )


def focal_length_to_hfov_degrees(
    focal_length: float,
    sensor_size: float,
) -> float:
    return focal_length_to_hfov_radians(focal_length, sensor_size) / math.pi * 180


def focal_length_to_hfov_radians(
    focal_length: float,
    sensor_size: float,
) -> float:
    return 2 * math.atan(sensor_size / (2 * focal_length))


def hfov_degrees_to_focal_length(
    hfov: float,
    sensor_size: float,
) -> float:
    return hfov_radians_to_focal_length(hfov / 180 * math.pi, sensor_size)


def hfov_radians_to_focal_length(
    hfov: float,
    sensor_size: float,
) -> float:
    a = math.tan(hfov / 2)
    return (sensor_size / 2) / a


def mesh_vertices(
    mesh: bpy.types.Mesh,
    dtype: NumpyDType,
) -> NumpyArray:
    if dtype not in [dtypes.vector3, dtypes.vector3_lh]:
        raise errors.RBRAddonBug("Bad dtype for mesh_vertices")
    co = np.zeros(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    reshaped = np.reshape(co, (-1, 3))
    vertex_positions = np.empty(len(mesh.vertices), dtype=dtype)
    (x, y, z) = np.hsplit(reshaped, 3)
    vertex_positions["x"] = x.flatten()
    vertex_positions["y"] = y.flatten()
    vertex_positions["z"] = z.flatten()
    return vertex_positions


def mesh_vertices_to_loop_positions(
    mesh: bpy.types.Mesh,
    dtype: NumpyDType,
) -> Tuple[NumpyArray, NumpyArray]:
    """Return mesh vertices in a numpy array with the given vector3 dtype (left
    or right handed).
    Returns (vertex_indices, loop_positions)
    """
    vertex_positions = mesh_vertices(mesh, dtype)
    # For converting from vertex to loop indices
    loop_vertex_indices = np.zeros(len(mesh.loops), dtype=int)
    mesh.loops.foreach_get("vertex_index", loop_vertex_indices)
    return (loop_vertex_indices, np.take(vertex_positions, loop_vertex_indices))


@dataclass
class UVMap:
    uv_map: str


@dataclass
class UVMapAttr:
    attribute_name: str


SomeUVMap = Union[UVMap, UVMapAttr]


def get_uv_array(
    mesh: bpy.types.Mesh,
    layer: Optional[SomeUVMap],
    invert_v: bool,
    material_name: str,
) -> Optional[NumpyArray]:
    if layer is None:
        return None
    if isinstance(layer, UVMap):
        uv_loop_layer = mesh.uv_layers.get(layer.uv_map)
        if uv_loop_layer is None:
            # Although we rejected empty materials further up the chain, the mesh
            # might not have the UV layer the user picked (maybe from a different
            # object or prior to renaming it).
            raise errors.E0147(
                material_name=material_name,
                uv_map_layer=layer.uv_map,
                mesh_name=mesh.name,
            )
        uv = np.zeros(len(mesh.loops) * 2)
        uv_loop_layer.data.foreach_get("uv", uv)
        (u, v) = np.hsplit(uv.reshape((len(mesh.loops), 2)), 2)
        uv_out = np.empty(len(mesh.loops), dtype=dtypes.uv)
        uv_out["u"] = u.flatten()
        uv_out["v"] = 1 - v.flatten() if invert_v else v.flatten()
        return uv_out
    elif isinstance(layer, UVMapAttr):
        attr = mesh.attributes.get(layer.attribute_name)
        if attr is None:
            raise errors.E0147(
                material_name=material_name,
                uv_map_layer=layer.attribute_name,
                mesh_name=mesh.name,
            )
        if not isinstance(attr, bpy.types.FloatVectorAttribute):
            raise errors.E0151(
                material_name=material_name,
                attr_type=str(type(attr)),
                attr_domain=attr.domain,
                mesh_name=mesh.name,
            )
        if attr.domain == "CORNER":
            domain_size = len(mesh.loops)
        elif attr.domain == "POINT":
            domain_size = len(mesh.vertices)
        else:
            raise errors.E0151(
                material_name=material_name,
                attr_type=str(type(attr)),
                attr_domain=attr.domain,
                mesh_name=mesh.name,
            )
        # 2 and 3 component vectors are stored as 3 components
        uv = np.zeros(domain_size * 3)
        attr.data.foreach_get("vector", uv)
        (u, v, _) = np.hsplit(uv.reshape((-1, 3)), 3)
        uv_out = np.empty(domain_size, dtype=dtypes.uv)
        uv_out["u"] = u.flatten()
        uv_out["v"] = 1 - v.flatten() if invert_v else v.flatten()
        # Remap vector data to corner data
        if attr.domain == "POINT":
            indices = np.zeros(len(mesh.loops), dtype=int)
            mesh.loops.foreach_get("vertex_index", indices)
            return uv_out[indices]
        return uv_out


def mesh_loop_triangles(mesh: bpy.types.Mesh) -> NumpyArray:
    """Returns a C,B,A 2d numpy array of triangles"""
    indices = np.zeros(len(mesh.loop_triangles) * 3, dtype=int)
    mesh.loop_triangles.foreach_get("loops", indices)
    return indices.reshape((len(mesh.loop_triangles), 3))


def setup_bounding_box(
    name: str,
    box: AaBbBoundingBox,
) -> bpy.types.Object:
    obj = create_cube(name)
    obj.location = (
        box.position.x,
        box.position.z,
        box.position.y,
    )
    obj.scale = (
        box.size.x * 2,
        box.size.z * 2,
        box.size.y * 2,
    )
    return obj


def make_vc(mesh: bpy.types.Mesh, layer: str) -> None:
    if layer not in mesh.vertex_colors.keys():
        mesh.vertex_colors.new(name=layer)


def make_uv(mesh: bpy.types.Mesh, layer: str) -> None:
    if layer not in mesh.uv_layers.keys():
        mesh.uv_layers.new(name=layer, do_init=False)
