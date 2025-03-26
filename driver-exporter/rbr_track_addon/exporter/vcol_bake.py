"""
The purpose of this module is to reimplement shader nodes using numpy arrays.
This is so that at export time we can use these fast implementations to compute
vertex color and alpha values, instead of using the (sometimes very slow) cycles
bake to vertex color operator.

Many function implementations are adapted directly from
blender/intern/cycles/kernel/svm.
"""

from __future__ import annotations
from dataclasses import dataclass
import enum
from typing import Dict, List, Optional, Set, Tuple

import bpy  # type: ignore
import numpy as np
from numpy.lib.recfunctions import (
    unstructured_to_structured,
)

from rbr_track_formats.logger import Logger
from rbr_track_formats.common import NumpyArray, pairwise
from rbr_track_formats import dtypes, errors

from rbr_track_addon.shaders.shader_node import (
    ShaderNodeRBR,
    RBR_SPECULAR_STRENGTH_INPUT_NAME,
    RBR_ALPHA_INPUT_NAME,
    RBR_COLOR_INPUT_NAME,
    RBR_SWAY_FREQ_INPUT_NAME,
    RBR_SWAY_AMP_INPUT_NAME,
    RBR_SWAY_PHASE_INPUT_NAME,
)
from rbr_track_addon.numpy_utils import (
    clamp,
    fract,
    hsv_to_rgb,
    rgb_avg,
    rgb_to_bw,
    rgb_to_hsv,
    safe_divide,
    saturate,
    smootherstep,
    smoothminf,
    smoothstep,
)


FLT_EPSILON = 1.192092896e-07


class AttributeDataType(enum.Enum):
    FLOAT_COLOR = enum.auto()


@dataclass
class AttributeData:
    data_type: AttributeDataType
    data: NumpyArray


@dataclass
class AttributeInputs:
    mesh: bpy.types.Mesh
    loop_count: int
    layers: Dict[str, AttributeData]

    def get_color(self, name: str) -> NumpyArray:
        if name not in self.layers:
            raise errors.E0110(mesh_name=self.mesh.name, attr_name=name)
        layer = self.layers[name]
        if layer.data_type is AttributeDataType.FLOAT_COLOR:
            return np.delete(layer.data, 3, 1)

    def get_fac(self, name: str) -> NumpyArray:
        if name not in self.layers:
            raise errors.E0110(mesh_name=self.mesh.name, attr_name=name)
        color = self.get_color(name)
        return rgb_avg(color)

    def get_alpha(self, name: str) -> NumpyArray:
        if name not in self.layers:
            raise errors.E0110(mesh_name=self.mesh.name, attr_name=name)
        layer = self.layers[name]
        if layer.data_type is AttributeDataType.FLOAT_COLOR:
            return np.delete(layer.data, [0, 1, 2], 1)


@dataclass
class TraverseReifyParams:
    group_node: bpy.types.ShaderNodeGroup
    seen: Set[bpy.types.Node]
    outer_node_tree: bpy.types.NodeTree


@dataclass
class ShaderOutput:
    """A shader output socket. We model the shader tree based on output sockets,
    not the shader nodes themselves, because it makes it simpler to handle
    blender's implicit conversion between socket types. We may end up doing
    superfluous computation with this model, but it's not an issue because even
    large arrays are computed quickly with numpy.
    """

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        """Returns a (N, 3) dimensional array (R, G, B). This is not necessarily
        a color socket! It might be a value socket which is converted to color
        implicitly by blender for the next shader node."""
        a = self.bake_value(inputs)
        return np.broadcast_to(a, (inputs.loop_count, 3))

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        """Returns a (N, 1) dimensional array. Note that this is not necessarily
        the alpha channel! If we have a color socket going into a value socket,
        blender will implicitly convert it to black and white."""
        # Colors are converted to values using the same method as the RGBToBW
        # node.
        color = self.bake_color(inputs)
        return rgb_to_bw(color)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        """We need a way to traverse (and possibly modify) shader outputs in
        order to handle node group inputs correctly.
        """
        raise errors.RBRAddonBug(f"traverse_reify not implemented for {type(self)}")


@dataclass
class RGBInput(ShaderOutput):
    color: Tuple[float, float, float]

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        (r, g, b) = self.color
        return np.full((inputs.loop_count, 3), [r, g, b])

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class ValueInput(ShaderOutput):
    value: float

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        return np.full((inputs.loop_count, 1), self.value)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class NewGeometryPosition(ShaderOutput):
    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        vertices = np.zeros(len(inputs.mesh.vertices) * 3)
        inputs.mesh.vertices.foreach_get("co", vertices)
        vertices = vertices.reshape((-1, 3))
        indices = np.zeros(len(inputs.mesh.loops), dtype=int)
        inputs.mesh.loops.foreach_get("vertex_index", indices)
        return vertices[indices]

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class NewGeometryNormal(ShaderOutput):
    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        normals = np.zeros(len(inputs.mesh.loops) * 3)
        # Must calc normals before getting the data
        inputs.mesh.calc_normals_split()
        inputs.mesh.loops.foreach_get("normal", normals)
        return normals.reshape((-1, 3))

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class VectorValue(ShaderOutput):
    value: Tuple[float, float, float]

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        (r, g, b) = self.value
        return np.full((inputs.loop_count, 3), [r, g, b])

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class AttributeColor(ShaderOutput):
    name: str

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        return inputs.get_color(self.name)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class AttributeFac(ShaderOutput):
    name: str

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        return inputs.get_fac(self.name)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class AttributeAlpha(ShaderOutput):
    name: str

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        return inputs.get_alpha(self.name)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class VertexColorColor(ShaderOutput):
    layer: str

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        return inputs.get_color(self.layer)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class VertexColorAlpha(ShaderOutput):
    layer: str

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        return inputs.get_alpha(self.layer)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return self


@dataclass
class Math(ShaderOutput):
    operation: str
    use_clamp: bool
    value1: ShaderOutput
    value2: ShaderOutput
    value3: ShaderOutput

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        value1 = self.value1.bake_value(inputs)
        value2 = self.value2.bake_value(inputs)
        value3 = self.value3.bake_value(inputs)
        result = None
        if self.operation == "ADD":
            result = value1 + value2
        elif self.operation == "SUBTRACT":
            result = value1 - value2
        elif self.operation == "MULTIPLY":
            result = value1 * value2
        elif self.operation == "DIVIDE":
            result = safe_divide(value1, value2)
        elif self.operation == "MULTIPLY_ADD":
            result = value1 * value2 + value3
        elif self.operation == "POWER":
            y_mod_1 = np.fmod(value2, 1)
            result = np.where(
                value1 >= 0,
                value1**value2,
                np.where(
                    np.logical_or(y_mod_1 > 0.999, y_mod_1 < 0.001),
                    value1 ** np.floor(value2 + 0.5),
                    0,
                ),
            )
        elif self.operation == "LOGARITHM":
            result = np.where(
                np.logical_and(value1 > 0, value2 > 0),
                np.log(value1) / np.log(value2),
                0,
            )
        elif self.operation == "SQRT":
            result = np.where(value1 > 0, np.sqrt(value1), 0)
        elif self.operation == "INVERSE_SQRT":
            result = np.where(value1 > 0, 1 / np.sqrt(value1), 0)
        elif self.operation == "ABSOLUTE":
            result = np.fabs(value1)
        elif self.operation == "EXPONENT":
            result = np.exp(value1)
        elif self.operation == "MINIMUM":
            result = np.minimum(value1, value2)
        elif self.operation == "MAXIMUM":
            result = np.maximum(value1, value2)
        elif self.operation == "LESS_THAN":
            result = np.less(value1, value2)
        elif self.operation == "GREATER_THAN":
            result = np.greater(value1, value2)
        elif self.operation == "SIGN":
            result = np.sign(value1)
        elif self.operation == "COMPARE":
            result = np.where(
                np.fabs(value1 - value2) <= np.maximum(value3, 1e-5),
                1.0,
                0.0,
            )
        elif self.operation == "SMOOTH_MIN":
            result = smoothminf(value1, value2, value3)
        elif self.operation == "SMOOTH_MAX":
            result = -smoothminf(-value1, -value2, value3)
        elif self.operation == "ROUND":
            result = np.around(value1)
        elif self.operation == "FLOOR":
            result = np.floor(value1)
        elif self.operation == "CEIL":
            result = np.ceil(value1)
        elif self.operation == "TRUNC":
            result = np.trunc(value1)
        elif self.operation == "FRACT":
            result = fract(value1)
        elif self.operation == "MODULO":
            result = np.where(value2 == 0, 0, np.fmod(value1, value2))
        elif self.operation == "WRAP":
            range = value2 - value3
            result = np.where(
                range != 0,
                value1 - (range * np.floor((value1 - value3) / range)),
                value3,
            )
        elif self.operation == "SNAP":
            result = np.where(
                np.logical_or(value1 == 0, value2 == 0),
                0,
                np.floor(value1 / value2) * value2,
            )
        elif self.operation == "PINGPONG":
            result = np.where(
                value2 == 0.0,
                0.0,
                np.abs(fract((value1 - value2) / (value2 * 2)) * value2 * 2 - value2),
            )
        elif self.operation == "SINE":
            result = np.sin(value1)
        elif self.operation == "COSINE":
            result = np.cos(value1)
        elif self.operation == "TANGENT":
            result = np.tan(value1)
        elif self.operation == "ARCSINE":
            result = np.arcsin(value1)
        elif self.operation == "ARCCOSINE":
            result = np.arccos(value1)
        elif self.operation == "ARCTANGENT":
            result = np.arctan(value1)
        elif self.operation == "ARCTAN2":
            result = np.arctan2(value1, value2)
        elif self.operation == "SINH":
            result = np.sinh(value1)
        elif self.operation == "COSH":
            result = np.cosh(value1)
        elif self.operation == "TANH":
            result = np.tanh(value1)
        elif self.operation == "RADIANS":
            result = np.radians(value1)
        elif self.operation == "DEGREES":
            result = np.degrees(value1)
        if result is None:
            raise errors.RBRAddonBug(f"bake math unhandled operation: {self.operation}")
        if self.use_clamp:
            return clamp(result, 0, 1)
        else:
            return result

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return Math(
            operation=self.operation,
            use_clamp=self.use_clamp,
            value1=self.value1.traverse_reify(params),
            value2=self.value2.traverse_reify(params),
            value3=self.value3.traverse_reify(params),
        )


@dataclass
class MixRGB(ShaderOutput):
    blend_type: str
    use_clamp: bool
    fac: ShaderOutput
    color1: ShaderOutput
    color2: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        value = self.fac.bake_value(inputs)
        invValue = 1.0 - value
        color1 = self.color1.bake_color(inputs)
        color2 = self.color2.bake_color(inputs)
        mixed = None
        use_clamp = self.use_clamp  # Here so we can force it in some cases
        if self.blend_type == "MIX":
            mixed = invValue * color1 + value * color2
        elif self.blend_type == "DARKEN":
            mixed = np.minimum(color1, color2) * value + color1 * invValue
        elif self.blend_type == "MULTIPLY":
            mixed = color1 * (invValue + value * color2)
        elif self.blend_type == "BURN":
            use_clamp = True
            tmp = invValue + value * color2
            mixed = np.where(
                tmp <= 0.0,
                0.0,
                1.0 - (1.0 - color1) / tmp,
            )
        elif self.blend_type == "LIGHTEN":
            tmp = value * color2
            mixed = np.where(tmp > color1, tmp, color1)
        elif self.blend_type == "SCREEN":
            mixed = 1.0 - (invValue + value * (1.0 - color2)) * (1.0 - color1)
        elif self.blend_type == "DODGE":
            tmp = 1.0 - value * color2
            mixed = np.where(
                color1 != 0.0,
                np.where(
                    tmp <= 0.0,
                    1.0,
                    np.fmin(color1 / tmp, 1.0),
                ),
                0.0,
            )
        elif self.blend_type == "ADD":
            mixed = color1 + value * color2
        elif self.blend_type == "OVERLAY":
            mixed = np.where(
                color1 < 0.5,
                color1 * (invValue + 2 * value * color2),
                1 - (invValue + 2 * value * (1 - color2)) * (1 - color1),
            )
        elif self.blend_type == "SOFT_LIGHT":
            sc = 1 - (1 - color2) * (1 - color1)
            mixed = invValue * color1 + value * (
                ((1 - color1) * color2 * color1) + (color1 * sc)
            )
        elif self.blend_type == "LINEAR_LIGHT":
            mixed = np.where(
                color2 > 0.5,
                color1 + value * (2 * (color2 - 0.5)),
                color1 + value * (2 * color2 - 1.0),
            )
        elif self.blend_type == "DIFFERENCE":
            mixed = invValue * color1 + value * np.abs(color1 - color2)
        elif self.blend_type == "SUBTRACT":
            mixed = color1 - value * color2
        elif self.blend_type == "DIVIDE":
            mixed = np.where(
                color2 != 0.0,
                invValue * color1 + value * color1 / color2,
                color1,
            )
        elif self.blend_type == "HUE":
            hsv1 = rgb_to_hsv(color1)
            (_h1, s1, v1) = np.hsplit(hsv1, 3)
            hsv2 = rgb_to_hsv(color2)
            (h2, s2, _v2) = np.hsplit(hsv2, 3)
            # Where saturation of second colour is non zero, we overwrite the
            # hue of the first colour.
            rgb = np.where(
                s2 != 0,
                hsv_to_rgb(np.hstack((h2, s1, v1))),
                color1,
            )
            return invValue * color1 + value * rgb
        elif self.blend_type == "SATURATION":
            hsv1 = rgb_to_hsv(color1)
            (h1, s1, v1) = np.hsplit(hsv1, 3)
            hsv2 = rgb_to_hsv(color2)
            (_h2, s2, _v2) = np.hsplit(hsv2, 3)
            return np.where(
                s1 != 0,
                hsv_to_rgb(np.hstack((h1, invValue * s1 + value * s2, v1))),
                color1,
            )
        elif self.blend_type == "VALUE":
            hsv1 = rgb_to_hsv(color1)
            (h1, s1, v1) = np.hsplit(hsv1, 3)
            hsv2 = rgb_to_hsv(color2)
            (_h2, _s2, v2) = np.hsplit(hsv2, 3)
            v = invValue * v1 + value * v2
            return hsv_to_rgb(np.hstack((h1, s1, v)))
        elif self.blend_type == "COLOR":
            hsv1 = rgb_to_hsv(color1)
            (h1, s1, v1) = np.hsplit(hsv1, 3)
            hsv2 = rgb_to_hsv(color2)
            (h2, s2, v2) = np.hsplit(hsv2, 3)
            rgb = hsv_to_rgb(np.hstack((h2, s2, v1)))
            out = invValue * color1 + value * rgb
            return np.where(
                s2 != 0,
                out,
                color1,
            )
        if mixed is None:
            raise errors.RBRAddonBug(
                f"bake MixRGB unhandled blend type: {self.blend_type}"
            )
        if use_clamp:
            return clamp(mixed, 0, 1)
        else:
            return mixed

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return MixRGB(
            blend_type=self.blend_type,
            use_clamp=self.use_clamp,
            fac=self.fac,
            color1=self.color1.traverse_reify(params),
            color2=self.color2.traverse_reify(params),
        )


@dataclass
class VectorMathToScalar(ShaderOutput):
    operation: str
    vector1: ShaderOutput
    vector2: ShaderOutput
    vector3: ShaderOutput
    scalar: ShaderOutput

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        vector1 = self.vector1.bake_value(inputs)
        vector2 = self.vector2.bake_value(inputs)
        if self.operation == "LENGTH":
            return np.linalg.norm(vector1, axis=1)
        elif self.operation == "DISTANCE":
            return np.linalg.norm(vector1 - vector2, axis=1)
        elif self.operation == "DOT_PRODUCT":
            mul = vector1 * vector2
            a = mul[:, 0]
            b = mul[:, 1]
            c = mul[:, 2]
            return a + b + c
        raise errors.RBRAddonBug(
            f"bake vector math to scalar unhandled operation: {self.operation}"
        )

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return VectorMathToScalar(
            operation=self.operation,
            vector1=self.vector1.traverse_reify(params),
            vector2=self.vector2.traverse_reify(params),
            vector3=self.vector3.traverse_reify(params),
            scalar=self.scalar.traverse_reify(params),
        )


@dataclass
class VectorMathToVector(ShaderOutput):
    operation: str
    vector1: ShaderOutput
    vector2: ShaderOutput
    vector3: ShaderOutput
    scalar: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        vector1 = self.vector1.bake_value(inputs)
        vector2 = self.vector2.bake_value(inputs)
        vector3 = self.vector3.bake_value(inputs)
        scalar = self.scalar.bake_value(inputs)
        if self.operation == "SCALE":
            return vector1 * scalar
        elif self.operation == "FACEFORWARD":
            mul = vector3 * vector2
            a = mul[:, 0]
            b = mul[:, 1]
            c = mul[:, 2]
            dot = a + b + c
            return np.where(dot < 0, vector1, -vector1)
        elif self.operation == "CROSS_PRODUCT":
            return np.cross(vector1, vector2)
        elif self.operation == "MULTIPLY_ADD":
            return vector1 * vector2 + vector3
        elif self.operation == "DIVIDE":
            return vector1 / vector2
        elif self.operation == "MULTIPLY":
            return vector1 * vector2
        elif self.operation == "SUBTRACT":
            return vector1 - vector2
        elif self.operation == "ADD":
            return vector1 + vector2
        elif self.operation == "TANGENT":
            return np.tan(vector1)
        elif self.operation == "COSINE":
            return np.cos(vector1)
        elif self.operation == "SINE":
            return np.sin(vector1)
        elif self.operation == "SNAP":
            return np.floor(np.true_divide(vector1, vector2)) * vector2
        elif self.operation == "MODULO":
            return np.fmod(vector1)  # type: ignore
        elif self.operation == "FRACTION":
            return vector1 - np.floor(vector1)
        elif self.operation == "CEIL":
            return np.ceil(vector1)
        elif self.operation == "FLOOR":
            return np.floor(vector1)
        elif self.operation == "MAXIMUM":
            return np.maximum(vector1, vector2)
        elif self.operation == "MINIMUM":
            return np.minimum(vector1, vector2)
        elif self.operation == "ABSOLUTE":
            return np.fabs(vector1)
        elif self.operation == "NORMALIZE":
            mag = np.linalg.norm(vector1, axis=1)
            return vector1 / np.expand_dims(mag, axis=1)
        raise errors.E0149(operation=self.operation)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return VectorMathToVector(
            operation=self.operation,
            vector1=self.vector1.traverse_reify(params),
            vector2=self.vector2.traverse_reify(params),
            vector3=self.vector3.traverse_reify(params),
            scalar=self.scalar.traverse_reify(params),
        )


@dataclass
class Invert(ShaderOutput):
    fac: ShaderOutput
    color: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        value = self.fac.bake_value(inputs)
        invValue = 1.0 - value
        color = self.color.bake_color(inputs)
        return (1.0 - color) * value + color * invValue

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return Invert(
            fac=self.fac.traverse_reify(params),
            color=self.color.traverse_reify(params),
        )


@dataclass
class RGBToBW(ShaderOutput):
    color: ShaderOutput

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        return self.color.bake_value(inputs)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return RGBToBW(
            color=self.color.traverse_reify(params),
        )


@dataclass
class Clamp(ShaderOutput):
    clamp_type: str
    value: ShaderOutput
    min: ShaderOutput
    max: ShaderOutput

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        if self.clamp_type != "MINMAX":
            raise errors.E0111()
        value = self.value.bake_value(inputs)
        min = self.min.bake_value(inputs)
        max = self.max.bake_value(inputs)
        return clamp(value, min, max)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return Clamp(
            clamp_type=self.clamp_type,
            value=self.value.traverse_reify(params),
            min=self.min.traverse_reify(params),
            max=self.max.traverse_reify(params),
        )


@dataclass
class BrightContrast(ShaderOutput):
    color: ShaderOutput
    bright: ShaderOutput
    contrast: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        """See intern/cycles/kernel/svm/svm_color_util.h/svm_brightness_contrast"""
        color = self.color.bake_color(inputs)
        brightness = self.bright.bake_value(inputs)
        contrast = self.contrast.bake_value(inputs)
        a = 1 + contrast
        b = brightness - contrast * 0.5
        return np.fmax(a * color + b, 0)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return BrightContrast(
            color=self.color.traverse_reify(params),
            bright=self.bright.traverse_reify(params),
            contrast=self.contrast.traverse_reify(params),
        )


@dataclass
class Gamma(ShaderOutput):
    color: ShaderOutput
    gamma: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        color = self.color.bake_color(inputs)
        gamma = self.gamma.bake_value(inputs)
        return np.where(color > 0, color**gamma, color)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return Gamma(
            color=self.color.traverse_reify(params),
            gamma=self.gamma.traverse_reify(params),
        )


class SeparateXYZOutput(str, enum.Enum):
    X = "X"
    Y = "Y"
    Z = "Z"

    def channel(self) -> int:
        if self is SeparateXYZOutput.X:
            return 0
        elif self is SeparateXYZOutput.Y:
            return 1
        elif self is SeparateXYZOutput.Z:
            return 2


@dataclass
class SeparateXYZ(ShaderOutput):
    output: SeparateXYZOutput
    vector: ShaderOutput

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        channel = self.output.channel()
        a = self.vector.bake_color(inputs)
        split = np.hsplit(a, 3)
        return np.reshape(split[channel], (-1, 1))

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return SeparateXYZ(
            output=self.output,
            vector=self.vector.traverse_reify(params),
        )


class SeparateRGBOutput(str, enum.Enum):
    RED = "R"
    GREEN = "G"
    BLUE = "B"

    def channel(self) -> int:
        if self is SeparateRGBOutput.RED:
            return 0
        elif self is SeparateRGBOutput.GREEN:
            return 1
        elif self is SeparateRGBOutput.BLUE:
            return 2


@dataclass
class SeparateRGB(ShaderOutput):
    output: SeparateRGBOutput
    color: ShaderOutput

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        channel = self.output.channel()
        a = self.color.bake_color(inputs)
        split = np.hsplit(a, 3)
        return np.reshape(split[channel], (-1, 1))

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return SeparateRGB(
            output=self.output,
            color=self.color.traverse_reify(params),
        )


@dataclass
class CombineRGB(ShaderOutput):
    red: ShaderOutput
    green: ShaderOutput
    blue: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        r = self.red.bake_value(inputs)
        g = self.green.bake_value(inputs)
        b = self.blue.bake_value(inputs)
        return np.hstack((r, g, b))

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return CombineRGB(
            red=self.red.traverse_reify(params),
            green=self.green.traverse_reify(params),
            blue=self.blue.traverse_reify(params),
        )


class SeparateHSVOutput(str, enum.Enum):
    HUE = "H"
    SATURATION = "S"
    VALUE = "V"

    def channel(self) -> int:
        if self is SeparateHSVOutput.HUE:
            return 0
        elif self is SeparateHSVOutput.SATURATION:
            return 1
        elif self is SeparateHSVOutput.VALUE:
            return 2


@dataclass
class SeparateHSV(ShaderOutput):
    output: SeparateHSVOutput
    color: ShaderOutput

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        channel = self.output.channel()
        rgb = self.color.bake_color(inputs)
        hsv = rgb_to_hsv(rgb)
        split = np.hsplit(hsv, 3)
        return np.reshape(split[channel], (-1, 1))

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return SeparateHSV(
            output=self.output,
            color=self.color.traverse_reify(params),
        )


@dataclass
class CombineHSV(ShaderOutput):
    hue: ShaderOutput
    saturation: ShaderOutput
    value: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        h = self.hue.bake_value(inputs)
        s = self.saturation.bake_value(inputs)
        v = self.value.bake_value(inputs)
        hsv = np.hstack((h, s, v))
        return hsv_to_rgb(hsv)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return CombineHSV(
            hue=self.hue.traverse_reify(params),
            saturation=self.saturation.traverse_reify(params),
            value=self.value.traverse_reify(params),
        )


@dataclass
class ColorRampElement:
    position: float
    color: List[float]

    @staticmethod
    def from_node(node: bpy.types.ColorRampElement) -> ColorRampElement:
        return ColorRampElement(
            position=node.position,
            color=list(node.color),
        )


@dataclass
class ColorRamp(ShaderOutput):
    """Currently this only has support for RGB Linear and Constant."""

    is_alpha_socket: bool
    color_mode: str
    interpolation: str
    hue_interpolation: str
    elements: List[ColorRampElement]
    fac: ShaderOutput

    def bake_all(self, inputs: AttributeInputs) -> NumpyArray:
        fac = self.fac.bake_value(inputs)
        color_mode = self.color_mode
        # Cheat if we have HSV/Linear, it can be treated exactly the same as
        # RGB/Linear. I think.
        if self.color_mode == "HSV" and self.interpolation == "LINEAR":
            color_mode = "RGB"
        if color_mode != "RGB":
            raise errors.E0112()
        # Start with the first colour. There's always at least one element.
        result = self.elements[0].color
        # Traverse the rest, pairwise. The elements are already in the correct
        # order. Note that the construction of the result is right biased here,
        # because we continually wrap previous results under later calls to
        # np.where, so we only need to check that the factor is to the right of
        # the left hand element.
        for left, right in pairwise(self.elements):
            if self.interpolation == "LINEAR":
                if left.position != right.position:
                    local_fac = (fac - left.position) / (right.position - left.position)
                else:
                    local_fac = 0
            elif self.interpolation == "CONSTANT":
                local_fac = 0
            else:
                raise errors.E0113()
            interp = (1 - local_fac) * left.color + local_fac * right.color
            result = np.where(fac > left.position, interp, result)  # type: ignore
        last_el = self.elements[-1]
        return np.where(
            fac >= last_el.position,
            last_el.color,
            result,
        )

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        if self.is_alpha_socket:
            a = self.bake_value(inputs)
            return np.broadcast_to(a, (inputs.loop_count, 3))
        else:
            rgba = self.bake_all(inputs)
            return np.delete(rgba, 3, 1)

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        if self.is_alpha_socket:
            rgba = self.bake_all(inputs)
            return np.delete(rgba, [0, 1, 2], 1)
        else:
            rgb = self.bake_color(inputs)
            return rgb_to_bw(rgb)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return ColorRamp(
            is_alpha_socket=self.is_alpha_socket,
            color_mode=self.color_mode,
            interpolation=self.interpolation,
            hue_interpolation=self.hue_interpolation,
            elements=self.elements,
            fac=self.fac.traverse_reify(params),
        )


@dataclass
class MapRange(ShaderOutput):
    interpolation_type: str
    use_clamp: bool
    value: ShaderOutput
    from_min: ShaderOutput
    from_max: ShaderOutput
    to_min: ShaderOutput
    to_max: ShaderOutput
    steps: ShaderOutput

    def bake_value(self, inputs: AttributeInputs) -> NumpyArray:
        value = self.value.bake_value(inputs)
        from_min = self.from_min.bake_value(inputs)
        from_max = self.from_max.bake_value(inputs)
        to_min = self.to_min.bake_value(inputs)
        to_max = self.to_max.bake_value(inputs)
        steps = self.steps.bake_value(inputs)

        use_clamp = False
        factor = value
        if self.interpolation_type == "LINEAR":
            factor = safe_divide(value - from_min, from_max - from_min)
            use_clamp = self.use_clamp
        elif self.interpolation_type == "STEPPED":
            factor = safe_divide(value - from_min, from_max - from_min)
            factor = np.where(steps > 0, np.floor(factor * (steps + 1)) / steps, 0)
            use_clamp = self.use_clamp
        elif self.interpolation_type == "SMOOTHSTEP":
            factor = np.where(
                from_min > from_max,
                1 - smoothstep(from_max, from_min, factor),
                smoothstep(from_min, from_max, factor),
            )
        elif self.interpolation_type == "SMOOTHERSTEP":
            factor = np.where(
                from_min > from_max,
                1 - smootherstep(from_max, from_min, factor),
                smootherstep(from_min, from_max, factor),
            )
        else:
            # We should have covered all (currently) existing cases
            raise errors.RBRAddonBug(
                f"MapRange: no implementation for {self.interpolation_type}"
            )
        result = to_min + factor * (to_max - to_min)
        if use_clamp:
            result = clamp(result, 0, 1)
        return np.where(from_max != from_min, result, 0)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return MapRange(
            interpolation_type=self.interpolation_type,
            use_clamp=self.use_clamp,
            value=self.value.traverse_reify(params),
            from_min=self.from_min.traverse_reify(params),
            from_max=self.from_max.traverse_reify(params),
            to_min=self.to_min.traverse_reify(params),
            to_max=self.to_max.traverse_reify(params),
            steps=self.steps.traverse_reify(params),
        )


@dataclass
class HueSaturationValue(ShaderOutput):
    hue: ShaderOutput
    saturation: ShaderOutput
    value: ShaderOutput
    fac: ShaderOutput
    color: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        hue = self.hue.bake_value(inputs)
        sat = self.saturation.bake_value(inputs)
        val = self.value.bake_value(inputs)
        fac = self.fac.bake_value(inputs)
        in_color = self.color.bake_color(inputs)

        (h, s, v) = np.hsplit(rgb_to_hsv(in_color), 3)

        out_color = hsv_to_rgb(
            np.hstack(
                (
                    np.fmod(h + hue + 0.5, 1),
                    saturate(s * sat),
                    v * val,
                )
            )
        )

        return np.fmax(fac * out_color + (1 - fac) * in_color, 0)

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return HueSaturationValue(
            hue=self.hue.traverse_reify(params),
            saturation=self.saturation.traverse_reify(params),
            value=self.value.traverse_reify(params),
            fac=self.fac.traverse_reify(params),
            color=self.color.traverse_reify(params),
        )


@dataclass
class Group(ShaderOutput):
    color: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        color = self.color.bake_color(inputs)
        return color

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return Group(
            color=self.color.traverse_reify(params),
        )


@dataclass
class ReifiedGroupInput(ShaderOutput):
    color: ShaderOutput

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        color = self.color.bake_color(inputs)
        return color

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        return ReifiedGroupInput(
            color=self.color.traverse_reify(params),
        )


@dataclass
# This isn't really a ShaderOutput, but it will be after traverse_reify.
class UnreifiedGroupInput(ShaderOutput):
    socket_id: str

    def bake_color(self, inputs: AttributeInputs) -> NumpyArray:
        raise errors.RBRAddonBug("UnreifiedGroupInput cannot bake_color")

    def traverse_reify(self, params: TraverseReifyParams) -> ShaderOutput:
        """We need a way to traverse (and possibly modify) shader outputs in
        order to handle node group inputs correctly.
        """
        input_socket = find_input_by_identifier(
            node=params.group_node,
            identifier=self.socket_id,
        )
        if input_socket is None:
            raise errors.RBRAddonBug(
                f"traverse_reify couldn't find an input by identifier {self.socket_id}"
            )
        return ReifiedGroupInput(
            color=reify_input(params.seen, params.outer_node_tree, input_socket),
        )


def find_input_by_identifier(
    node: bpy.types.Node,
    identifier: str,
) -> Optional[bpy.types.NodeSocketInterfaceColor]:
    for i in node.inputs:
        if i.identifier == identifier:
            return i
    return None


# TODO use this resolution method elsewhere!
def find_active_group_output(
    node_tree: bpy.types.NodeTree,
) -> Optional[bpy.types.NodeGroupOutput]:
    """Find the active group output node in a group's node tree."""
    for node in node_tree.nodes:
        if isinstance(node, bpy.types.NodeGroupOutput) and node.is_active_output:
            return node
    return None


def reify_input(
    seen: Set[bpy.types.Node],
    node_tree: bpy.types.NodeTree,
    socket: bpy.types.NodeSocket,
) -> ShaderOutput:
    for link in node_tree.links:
        if link.to_socket != socket:
            continue
        return reify_output(seen, node_tree, link.from_socket)
    else:
        v = socket.default_value
        try:
            return VectorValue((v[0], v[1], v[2]))
        except TypeError:
            return VectorValue((v, v, v))


def reify_output(
    seen: Set[bpy.types.Node],
    node_tree: bpy.types.NodeTree,
    socket: bpy.types.NodeSocket,
) -> ShaderOutput:
    node = socket.node
    if node in seen:
        raise errors.E0114(node_tree=node_tree.name)
    else:
        seen = seen.union({node})
    if isinstance(node, bpy.types.ShaderNodeVertexColor):
        if socket.name == "Color":
            return VertexColorColor(node.layer_name)
        elif socket.name == "Alpha":
            return VertexColorAlpha(node.layer_name)
        else:
            raise errors.RBRAddonBug(
                f"reify_output VertexColor: {socket.name} should be impossible"
            )
    elif isinstance(node, bpy.types.ShaderNodeAttribute):
        if node.attribute_type != "GEOMETRY":
            raise AssertionError(f"Not geometry: {node.attribute_type}")
        if socket.name == "Color":
            return AttributeColor(node.attribute_name)
        elif socket.name == "Vector":
            return AttributeColor(node.attribute_name)
        elif socket.name == "Fac":
            return AttributeFac(node.attribute_name)
        elif socket.name == "Alpha":
            return AttributeAlpha(node.attribute_name)
        else:
            raise errors.RBRAddonBug(
                f"reify_output Attribute: {socket.name} should be impossible"
            )
    elif isinstance(node, bpy.types.ShaderNodeRGB):
        v = node.outputs["Color"].default_value
        return RGBInput(
            color=(v[0], v[1], v[2]),
        )
    elif isinstance(node, bpy.types.ShaderNodeValue):
        return ValueInput(
            value=node.outputs["Value"].default_value,
        )
    elif isinstance(node, bpy.types.ShaderNodeNewGeometry):
        if socket.name == "Position":
            return NewGeometryPosition()
        elif socket.name == "Normal":
            return NewGeometryNormal()
        else:
            raise errors.E0115(socket_name=socket.name)
    elif isinstance(node, bpy.types.ShaderNodeMath):
        return Math(
            operation=node.operation,
            use_clamp=node.use_clamp,
            value1=reify_input(seen, node_tree, node.inputs[0]),
            value2=reify_input(seen, node_tree, node.inputs[1]),
            value3=reify_input(seen, node_tree, node.inputs[2]),
        )
    elif isinstance(node, bpy.types.ShaderNodeVectorMath):
        if socket.name == "Value":
            return VectorMathToScalar(
                operation=node.operation,
                vector1=reify_input(seen, node_tree, node.inputs[0]),
                vector2=reify_input(seen, node_tree, node.inputs[1]),
                vector3=reify_input(seen, node_tree, node.inputs[2]),
                scalar=reify_input(seen, node_tree, node.inputs[3]),
            )
        elif socket.name == "Vector":
            return VectorMathToVector(
                operation=node.operation,
                vector1=reify_input(seen, node_tree, node.inputs[0]),
                vector2=reify_input(seen, node_tree, node.inputs[1]),
                vector3=reify_input(seen, node_tree, node.inputs[2]),
                scalar=reify_input(seen, node_tree, node.inputs[3]),
            )
        else:
            raise errors.RBRAddonBug(f"Unhandled vector math socket {socket.name}")
    elif isinstance(node, bpy.types.ShaderNodeMixRGB):
        return MixRGB(
            blend_type=node.blend_type,
            use_clamp=node.use_clamp,
            fac=reify_input(seen, node_tree, node.inputs["Fac"]),
            color1=reify_input(seen, node_tree, node.inputs["Color1"]),
            color2=reify_input(seen, node_tree, node.inputs["Color2"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeMix):
        if node.data_type == "RGBA":
            return MixRGB(
                blend_type=node.blend_type,
                use_clamp=node.clamp_result,
                fac=reify_input(seen, node_tree, node.inputs[0]),
                color1=reify_input(seen, node_tree, node.inputs[6]),
                color2=reify_input(seen, node_tree, node.inputs[7]),
            )
        elif node.data_type == "FLOAT":
            return MixRGB(
                blend_type="MIX",
                use_clamp=False,
                fac=reify_input(seen, node_tree, node.inputs[0]),
                color1=reify_input(seen, node_tree, node.inputs[2]),
                color2=reify_input(seen, node_tree, node.inputs[3]),
            )
        elif node.data_type == "VECTOR":
            raise errors.RBRAddonBug(f"Unhandled mix node type {node.data_type}")
        else:
            raise errors.RBRAddonBug(f"Unhandled mix node type {node.data_type}")
    elif isinstance(node, bpy.types.ShaderNodeRGBToBW):
        return RGBToBW(
            color=reify_input(seen, node_tree, node.inputs["Color"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeInvert):
        return Invert(
            fac=reify_input(seen, node_tree, node.inputs["Fac"]),
            color=reify_input(seen, node_tree, node.inputs["Color"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeSeparateXYZ):
        return SeparateXYZ(
            output=SeparateXYZOutput(socket.name),
            vector=reify_input(seen, node_tree, node.inputs["Vector"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeSeparateRGB):
        return SeparateRGB(
            output=SeparateRGBOutput(socket.name),
            color=reify_input(seen, node_tree, node.inputs["Image"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeCombineRGB):
        return CombineRGB(
            red=reify_input(seen, node_tree, node.inputs["R"]),
            green=reify_input(seen, node_tree, node.inputs["G"]),
            blue=reify_input(seen, node_tree, node.inputs["B"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeSeparateHSV):
        return SeparateHSV(
            output=SeparateHSVOutput(socket.name),
            color=reify_input(seen, node_tree, node.inputs["Color"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeCombineHSV):
        return CombineHSV(
            hue=reify_input(seen, node_tree, node.inputs["H"]),
            saturation=reify_input(seen, node_tree, node.inputs["S"]),
            value=reify_input(seen, node_tree, node.inputs["V"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeValToRGB):
        return ColorRamp(
            is_alpha_socket=socket.name == "Alpha",
            color_mode=node.color_ramp.color_mode,
            interpolation=node.color_ramp.interpolation,
            hue_interpolation=node.color_ramp.hue_interpolation,
            elements=[ColorRampElement.from_node(e) for e in node.color_ramp.elements],
            fac=reify_input(seen, node_tree, node.inputs["Fac"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeClamp):
        return Clamp(
            clamp_type=node.clamp_type,
            value=reify_input(seen, node_tree, node.inputs["Value"]),
            min=reify_input(seen, node_tree, node.inputs["Min"]),
            max=reify_input(seen, node_tree, node.inputs["Max"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeGamma):
        return Gamma(
            color=reify_input(seen, node_tree, node.inputs["Color"]),
            gamma=reify_input(seen, node_tree, node.inputs["Gamma"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeBrightContrast):
        return BrightContrast(
            color=reify_input(seen, node_tree, node.inputs["Color"]),
            bright=reify_input(seen, node_tree, node.inputs["Bright"]),
            contrast=reify_input(seen, node_tree, node.inputs["Contrast"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeMapRange):
        return MapRange(
            interpolation_type=node.interpolation_type,
            use_clamp=node.clamp,
            value=reify_input(seen, node_tree, node.inputs["Value"]),
            from_min=reify_input(seen, node_tree, node.inputs["From Min"]),
            from_max=reify_input(seen, node_tree, node.inputs["From Max"]),
            to_min=reify_input(seen, node_tree, node.inputs["To Min"]),
            to_max=reify_input(seen, node_tree, node.inputs["To Max"]),
            steps=reify_input(seen, node_tree, node.inputs["Steps"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeHueSaturation):
        return HueSaturationValue(
            hue=reify_input(seen, node_tree, node.inputs["Hue"]),
            saturation=reify_input(seen, node_tree, node.inputs["Saturation"]),
            value=reify_input(seen, node_tree, node.inputs["Value"]),
            fac=reify_input(seen, node_tree, node.inputs["Fac"]),
            color=reify_input(seen, node_tree, node.inputs["Color"]),
        )
    elif isinstance(node, bpy.types.ShaderNodeGroup):
        group_output = find_active_group_output(node.node_tree)
        # I don't think this can happen.
        if group_output is None:
            raise errors.RBRAddonBug(
                f"reify_output could not find output node in group {node.name}"
            )
        found_input = find_input_by_identifier(
            node=group_output,
            identifier=socket.identifier,
        )
        # I also don't think this can happen.
        if found_input is None:
            raise errors.RBRAddonBug(
                f"reify_output could not find input socket for group {node.name}"
            )
        # Somewhere in this tree might exist a GroupInput node, which needs
        # further reification. We need to do this weird traversal in order to
        # reify the full shader tree, including nested groups.
        color = reify_input(seen, node.node_tree, found_input)
        return Group(
            color=color.traverse_reify(
                params=TraverseReifyParams(
                    group_node=node,
                    seen=seen,
                    outer_node_tree=node_tree,
                ),
            )
        )
    elif isinstance(node, bpy.types.NodeGroupInput):
        # Note useful information here: this is then rewritten in the Group
        # handler above. We don't have a direct way (in blender) to walk back
        # up the group hierarchy, so we use traverse_reify to fix this later.
        return UnreifiedGroupInput(
            socket_id=socket.identifier,
        )
    elif isinstance(node, bpy.types.NodeReroute):
        return reify_input(seen, node_tree, node.inputs[0])
    else:
        raise errors.E0116(
            node_type=str(type(node)),
            socket_type=str(type(socket)),
            baking_socket="",
        )


def get_first_material(mesh: bpy.types.Mesh) -> bpy.types.Material:
    try:
        return mesh.materials[0]
    except IndexError:
        raise errors.E0119(mesh_name=mesh.name)


def setup_bake(
    logger: Logger,
    mesh: bpy.types.Mesh,
) -> Tuple[ShaderNodeRBR, AttributeInputs]:
    node_tree = get_first_material(mesh).node_tree

    # TODO walk the tree backwards, this might get wrong node
    for node in node_tree.nodes:
        if isinstance(node, ShaderNodeRBR):
            rbr_shader = node
            break
    else:
        raise errors.E0117()

    indices = np.zeros(len(mesh.loops), dtype=int)
    mesh.loops.foreach_get("vertex_index", indices)

    def mk_col_array(domain_size: int, layer: str) -> NumpyArray:
        """Return an array of rgba as linear rgb"""
        a = np.zeros(4 * domain_size, dtype=np.float32)
        mesh.attributes[layer].data.foreach_get("color", a)
        a = np.reshape(a, (-1, 4))
        # ~~Color layers are stored as sRGB in vertex colors~~
        # This _was_ true up until the attribute change, now they are linear.
        color = np.delete(a, 3, 1)
        # Alpha layers are stored as linear in vertex colors
        alpha = np.delete(a, [0, 1, 2], 1)
        return np.hstack((color, alpha))

    # Turn all of the vcol layers into numpy arrays
    layers = dict()
    for layer, attr in mesh.attributes.items():
        if isinstance(attr, bpy.types.ByteColorAttribute):
            # This data is stored as float
            if attr.domain == "POINT":
                domain_size = len(mesh.vertices)
            elif attr.domain == "CORNER":
                domain_size = len(mesh.loops)
            else:
                continue
            a = mk_col_array(domain_size, layer)
            # Expand vertex attrs into loop attrs
            if attr.domain == "POINT":
                a = a[indices]
            layers[layer] = AttributeData(AttributeDataType.FLOAT_COLOR, a)
        elif isinstance(attr, bpy.types.FloatColorAttribute):
            if attr.domain == "POINT":
                domain_size = len(mesh.vertices)
            elif attr.domain == "CORNER":
                domain_size = len(mesh.loops)
            else:
                continue
            a = mk_col_array(domain_size, layer)
            if attr.domain == "POINT":
                a = a[indices]
            layers[layer] = AttributeData(AttributeDataType.FLOAT_COLOR, a)
        else:
            logger.warn(
                f"Skipping unsupported attribute layer '{layer}' of type '{type(attr)}'"
            )
    return (
        rbr_shader,
        AttributeInputs(
            mesh=mesh,
            loop_count=len(mesh.loops),
            layers=layers,
        ),
    )


def do_value_bake_for_input(
    node_tree: bpy.types.NodeTree,
    rbr_shader: ShaderNodeRBR,
    inputs: AttributeInputs,
    name: str,
) -> NumpyArray:
    inp = rbr_shader.inputs[name]
    try:
        reified = reify_input(set(), node_tree, inp)
    except errors.E0116 as e:
        e.baking_socket = name
        raise e
    return reified.bake_value(inputs).flatten()


def bake_sway(
    logger: Logger,
    mesh: bpy.types.Mesh,
) -> NumpyArray:
    """Return sway values as dtypes.sway"""
    material = get_first_material(mesh)
    try:
        node_tree = material.node_tree
        (rbr_shader, inputs) = setup_bake(logger, mesh)

        sway = np.empty(len(mesh.loops), dtype=dtypes.sway)
        sway["angular_frequency"] = do_value_bake_for_input(
            node_tree=node_tree,
            rbr_shader=rbr_shader,
            inputs=inputs,
            name=RBR_SWAY_FREQ_INPUT_NAME,
        )
        sway["amplitude"] = do_value_bake_for_input(
            node_tree=node_tree,
            rbr_shader=rbr_shader,
            inputs=inputs,
            name=RBR_SWAY_AMP_INPUT_NAME,
        )
        sway["phase_offset"] = do_value_bake_for_input(
            node_tree=node_tree,
            rbr_shader=rbr_shader,
            inputs=inputs,
            name=RBR_SWAY_PHASE_INPUT_NAME,
        )
        return sway
    except errors.RBRAddonError as e:
        raise errors.E0118(
            inner_error=e,
            material_name=material.name,
        )


def bake_spec_strength(
    logger: Logger,
    mesh: bpy.types.Mesh,
) -> NumpyArray:
    """Return specular strength values as floats"""
    material = get_first_material(mesh)
    try:
        node_tree = material.node_tree
        (rbr_shader, inputs) = setup_bake(logger, mesh)

        return do_value_bake_for_input(
            node_tree=node_tree,
            rbr_shader=rbr_shader,
            inputs=inputs,
            name=RBR_SPECULAR_STRENGTH_INPUT_NAME,
        )
    except errors.RBRAddonError as e:
        raise errors.E0118(
            inner_error=e,
            material_name=material.name,
        )


def bake_alpha(
    logger: Logger,
    mesh: bpy.types.Mesh,
) -> Tuple[ShaderNodeRBR, NumpyArray]:
    """Return alpha values as floats"""
    material = get_first_material(mesh)
    try:
        node_tree = material.node_tree
        (rbr_shader, inputs) = setup_bake(logger, mesh)

        alpha = do_value_bake_for_input(
            node_tree=node_tree,
            rbr_shader=rbr_shader,
            inputs=inputs,
            name=RBR_ALPHA_INPUT_NAME,
        )
        return (rbr_shader, alpha)
    except errors.RBRAddonError as e:
        raise errors.E0118(
            inner_error=e,
            material_name=material.name,
        )


def bake(
    logger: Logger,
    mesh: bpy.types.Mesh,
) -> NumpyArray:
    """Returns a dtypes.color numpy array in RGB linear color space with an
    element per mesh loop.

    The input mesh must have only one material."""
    material = get_first_material(mesh)
    try:
        node_tree = material.node_tree
        (rbr_shader, inputs) = setup_bake(logger, mesh)

        color_input = rbr_shader.inputs[RBR_COLOR_INPUT_NAME]
        try:
            reified_color = reify_input(set(), node_tree, color_input)
        except errors.E0116 as e:
            e.baking_socket = RBR_COLOR_INPUT_NAME
            raise e
        linear_rgb = clamp(reified_color.bake_color(inputs), 0, 1)

        alpha_input = rbr_shader.inputs[RBR_ALPHA_INPUT_NAME]
        try:
            reified_alpha = reify_input(set(), node_tree, alpha_input)
        except errors.E0116 as e:
            e.baking_socket = RBR_ALPHA_INPUT_NAME
            raise e
        alpha = clamp(reified_alpha.bake_value(inputs), 0, 1)

        bgra = np.around(np.hstack((np.flip(linear_rgb, axis=1), alpha)) * 255)
        return unstructured_to_structured(bgra, dtype=dtypes.color)
    except errors.RBRAddonError as e:
        raise errors.E0118(
            inner_error=e,
            material_name=material.name,
        )
