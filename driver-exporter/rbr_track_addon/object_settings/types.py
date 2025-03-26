import enum
from typing import List, Optional, Tuple

import bpy  # type: ignore

from rbr_track_formats.lbs.geom_blocks import RenderChunkDistance
from rbr_track_formats.dls.animation_cameras import AnimCameraMode
from rbr_track_formats.mat import object_materials, MaterialID
from rbr_track_formats.trk.shape_collision_meshes import (
    MAX_SCM_VERTICES,
    MAX_SCM_FACES,
    ObjectKind,
)
from rbr_track_formats.track_settings import TintSet

from . import fences


def check_scale_is_1(obj: bpy.types.Object) -> bool:
    EPSILON = 0.0001
    return all(map(lambda x: abs(x - 1) < EPSILON, obj.scale))


def type_sorted(
    items: List[Tuple[str, str, str, int]]
) -> List[Tuple[str, str, str, int]]:
    # Make sure 'RBRObjectType.NONE' is the first item, followed by a separator.
    result = [items[0]]
    # Putting 'None' makes a separator.
    result.append(None)  # type: ignore
    # Sort the rest by description.
    result.extend(sorted(items[1:], key=lambda t: t[1]))
    return result


# TODO revisit this
def setup_dummy_car(
    context: bpy.types.Context,
) -> bpy.types.Object:
    """Get or create the dummy car. The dummy car is a singleton, that is,
    there is only ever one, no matter how many drivelines there are.
    """
    dummy_car = bpy.data.objects.get("Dummy Car")
    if dummy_car is None:
        dummy_car = bpy.data.objects.new("Dummy Car", None)
        dummy_car.empty_display_type = "PLAIN_AXES"
        dummy_car.location = (0, 0, 0.8)
        context.scene.collection.objects.link(dummy_car)
    dummy_car.hide_render = True
    return dummy_car


class ClippingPlaneType(enum.Enum):
    DIRECTIONAL = 1
    OMNIDIRECTIONAL = 2

    def pretty(self) -> str:
        if self is ClippingPlaneType.DIRECTIONAL:
            return "Directional"
        elif self is ClippingPlaneType.OMNIDIRECTIONAL:
            return "Omnidirectional"

    def description(self) -> str:
        if self is ClippingPlaneType.DIRECTIONAL:
            return "Clip in one direction"
        elif self is ClippingPlaneType.OMNIDIRECTIONAL:
            return "Clip in both directions"

    def material_name(self) -> str:
        if self is ClippingPlaneType.DIRECTIONAL:
            return "RBR Directional Clipping Plane"
        elif self is ClippingPlaneType.OMNIDIRECTIONAL:
            return "RBR Omnidirectional Clipping Plane"


class ObjectBlocksDetail(enum.Enum):
    NEAR = 1
    FAR = 2
    BOTH = 3

    def pretty(self) -> str:
        if self is ObjectBlocksDetail.NEAR:
            return "Near"
        elif self is ObjectBlocksDetail.FAR:
            return "Far"
        elif self is ObjectBlocksDetail.BOTH:
            return "Both"

    def description(self) -> str:
        if self is ObjectBlocksDetail.NEAR:
            return "Only visible when within 1500m"
        elif self is ObjectBlocksDetail.FAR:
            return "Only visible when over 1500m away"
        elif self is ObjectBlocksDetail.BOTH:
            return "Always visible"


class WetSurfaceKind(enum.Enum):
    WATER = 1
    WET = 2

    def pretty(self) -> str:
        if self is WetSurfaceKind.WATER:
            return "Water splash (all weathers)"
        elif self is WetSurfaceKind.WET:
            return "Puddle (wet only)"

    def description(self) -> str:
        if self is WetSurfaceKind.WATER:
            return "Active in every weather"
        elif self is WetSurfaceKind.WET:
            return "Active only in wet weather"


def check_scm(obj: bpy.types.Object) -> Optional[str]:
    if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
        return "Must be a mesh"
    if not check_scale_is_1(obj):
        return "Scale must be 1"
    if len(obj.data.vertices) > MAX_SCM_VERTICES:
        return f"Too many vertices (max {MAX_SCM_VERTICES})"
    # loop_triangles might not be there, but this'll do for a warning,
    # since we calculate them properly on export
    if len(obj.data.loop_triangles) > MAX_SCM_FACES:
        return f"Too many vertices (max {MAX_SCM_FACES})"
    return None


class RBRObjectType(enum.Enum):
    NONE = 1
    GEOM_BLOCKS = 2
    OBJECT_BLOCKS = 3
    CLIPPING_PLANE = 4
    DRIVELINE = 5
    ZFAR = 6
    CAR_LOCATION = 7
    CAMERA = 8
    SUPER_BOWL = 9
    REFLECTION_OBJECTS = 10
    SHAPE_COLLISION_MESH = 11
    INTERACTIVE_OBJECTS = 12
    INTERACTIVE_OBJECTS_COLMESH = 18
    WATER_OBJECTS = 13
    BRAKE_WALL = 14
    SUN = 15
    REGISTRATION_ZONE = 16
    SOUND_EMITTER = 17
    INSTANCER = 19
    FENCE = 20
    WET_SURFACE = 21

    def pretty(self) -> str:
        if self is RBRObjectType.NONE:
            return "None"
        elif self is RBRObjectType.GEOM_BLOCKS:
            return "Geom Blocks"
        elif self is RBRObjectType.OBJECT_BLOCKS:
            return "Object Blocks"
        elif self is RBRObjectType.CLIPPING_PLANE:
            return "Clipping Plane"
        elif self is RBRObjectType.DRIVELINE:
            return "Driveline"
        elif self is RBRObjectType.ZFAR:
            return "Render Distance"
        elif self is RBRObjectType.CAR_LOCATION:
            return "Car Location"
        elif self is RBRObjectType.CAMERA:
            return "Camera"
        elif self is RBRObjectType.SUPER_BOWL:
            return "Super Bowl"
        elif self is RBRObjectType.REFLECTION_OBJECTS:
            return "Reflection Objects"
        elif self is RBRObjectType.SHAPE_COLLISION_MESH:
            return "Shape Collision Mesh"
        elif self is RBRObjectType.INTERACTIVE_OBJECTS:
            return "Interactive Objects"
        elif self is RBRObjectType.INTERACTIVE_OBJECTS_COLMESH:
            return "Interactive Objects Collision Mesh"
        elif self is RBRObjectType.WATER_OBJECTS:
            return "Water Objects"
        elif self is RBRObjectType.BRAKE_WALL:
            return "Brake Wall"
        elif self is RBRObjectType.SUN:
            return "Sun"
        elif self is RBRObjectType.REGISTRATION_ZONE:
            return "Registration Zone"
        elif self is RBRObjectType.SOUND_EMITTER:
            return "Sound Trigger"
        elif self is RBRObjectType.INSTANCER:
            return "Instancer"
        elif self is RBRObjectType.FENCE:
            return "Fence"
        elif self is RBRObjectType.WET_SURFACE:
            return "Wet Surface"
        else:
            raise NotImplementedError(self.name)

    def description(self) -> str:
        if self is RBRObjectType.NONE:
            return "Not an RBR object"
        elif self is RBRObjectType.GEOM_BLOCKS:
            return (
                "Static visual mesh, supports specularity, shadows, and can "
                + "be used to generate the static world collision mesh"
            )
        elif self is RBRObjectType.OBJECT_BLOCKS:
            return "Static visual mesh whose vertices can sway in the wind"
        elif self is RBRObjectType.CLIPPING_PLANE:
            return "Prevents anything behind (from the camera perspective) being rendered, for optimisation"
        elif self is RBRObjectType.DRIVELINE:
            return "Controls the stage route, triggers, and pacenotes"
        elif self is RBRObjectType.ZFAR:
            return "The size of this circle controls the (variable) render distance along the driveline"
        elif self is RBRObjectType.CAR_LOCATION:
            return "The initial position of the car"
        elif self is RBRObjectType.CAMERA:
            return "Replay camera. Must have a marker in the timeline in order to be activated."
        elif self is RBRObjectType.SUPER_BOWL:
            return "Background scenery. Always drawn, so must be quite low poly. No specular textures."
        elif self is RBRObjectType.REFLECTION_OBJECTS:
            return "Objects which fake reflections of other geometry"
        elif self is RBRObjectType.SHAPE_COLLISION_MESH:
            return "Collision mesh of instanced object, static (e.g. trees) or movable (e.g. bales)."
        elif self is RBRObjectType.INTERACTIVE_OBJECTS:
            return "Visual mesh of movable object. Must have child collision mesh."
        elif self is RBRObjectType.INTERACTIVE_OBJECTS_COLMESH:
            return "Collision mesh of movable object."
        elif self is RBRObjectType.WATER_OBJECTS:
            return "Visual water surface mesh. Can have animated UVs."
        elif self is RBRObjectType.BRAKE_WALL:
            return "A soft wall which prevents the car from straying too far from the stage"
        elif self is RBRObjectType.SUN:
            return (
                "Sun light, used for exporting the sun direction for specular shaders"
            )
        elif self is RBRObjectType.REGISTRATION_ZONE:
            return "An empty sphere which causes the end of the stage when the car stops within it (time control)."
        elif self is RBRObjectType.SOUND_EMITTER:
            return "An empty sphere which triggers sounds in replay mode"
        elif self is RBRObjectType.INSTANCER:
            return (
                "Applies 'Make instances real' modifier on this object when exporting"
            )
        elif self is RBRObjectType.FENCE:
            return "Interactive tape or net fences"
        elif self is RBRObjectType.WET_SURFACE:
            return (
                "Puddle or water splash. Provides the splash effect and water physics."
            )
        else:
            raise NotImplementedError(self.name)

    def validation_errors(self, obj: bpy.types.Object) -> Optional[str]:
        """Return an error message if the object is invalid for the given type.
        Otherwise return None."""
        if self is RBRObjectType.NONE:
            return None
        elif self is RBRObjectType.GEOM_BLOCKS:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
        elif self is RBRObjectType.OBJECT_BLOCKS:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
        elif self is RBRObjectType.CLIPPING_PLANE:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
        elif self is RBRObjectType.DRIVELINE:
            if obj.data is None or not isinstance(obj.data, bpy.types.Curve):
                return "Must be a curve"
            if not check_scale_is_1(obj):
                return "Scale must be 1"
        elif self is RBRObjectType.ZFAR:
            if obj.data is not None or obj.empty_display_type != "CIRCLE":
                return "Must be an empty with type=circle. Radius determines render distance, animatable along the driveline."
            if obj.parent is None:
                return "Must have a parent driveline object"
            object_settings: RBRObjectSettings = obj.parent.rbr_object_settings
            if object_settings.type != RBRObjectType.DRIVELINE.name:
                return "Parent object must have RBR object type of 'Driveline'"
        elif self is RBRObjectType.CAR_LOCATION:
            if obj.data is not None or obj.empty_display_type != "ARROWS":
                return "Must be an empty type=arrows. Z points up, Y points forwards."
        elif self is RBRObjectType.CAMERA:
            if obj.data is None or not isinstance(obj.data, bpy.types.Camera):
                return "Must be a camera"
        elif self is RBRObjectType.SUPER_BOWL:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
        elif self is RBRObjectType.REFLECTION_OBJECTS:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
        elif self is RBRObjectType.SHAPE_COLLISION_MESH:
            return check_scm(obj)
        elif self is RBRObjectType.INTERACTIVE_OBJECTS:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
            if not check_scale_is_1(obj):
                return "Scale must be 1"
            colmesh_children = []
            for child in obj.children:
                child_type = RBRObjectType[child.rbr_object_settings.type]
                if child_type is RBRObjectType.INTERACTIVE_OBJECTS_COLMESH:
                    colmesh_children.append(child)
            if len(colmesh_children) < 1:
                return "Must have child object of type 'Interactive Objects Collision Mesh'"
            elif len(colmesh_children) > 1:
                return "Must have only one child collision mesh"
        elif self is RBRObjectType.INTERACTIVE_OBJECTS_COLMESH:
            return check_scm(obj)
        elif self is RBRObjectType.WATER_OBJECTS:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
        elif self is RBRObjectType.BRAKE_WALL:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                # TODO more validation!
                return "Must be a mesh"
        elif self is RBRObjectType.SUN:
            if obj.data is None or not isinstance(obj.data, bpy.types.SunLight):
                return "Must be a sun light"
        elif self is RBRObjectType.REGISTRATION_ZONE:
            if obj.data is not None or obj.empty_display_type != "SPHERE":
                return "Must be an 'empty' object with empty type of sphere"
        elif self is RBRObjectType.SOUND_EMITTER:
            if obj.data is not None or obj.empty_display_type != "SPHERE":
                return "Must be an 'empty' object with empty type of sphere"
        elif self is RBRObjectType.INSTANCER:
            pass
        elif self is RBRObjectType.FENCE:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
        elif self is RBRObjectType.WET_SURFACE:
            if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
                return "Must be a mesh"
        else:
            raise NotImplementedError(self.name)
        return None


class RBRObjectSettings(bpy.types.PropertyGroup):
    exported: bpy.props.BoolProperty(  # type: ignore
        name="Exported",  # noqa: F821
        description="Should be used for export",
        default=True,
    )

    def update_type(self, context: bpy.types.Context) -> None:
        obj = context.object
        if obj is not None:
            obj.rbr_object_type_value = RBRObjectType[self.type].value

    type: bpy.props.EnumProperty(  # type: ignore
        items=type_sorted(
            [(t.name, t.pretty(), t.description(), t.value) for t in RBRObjectType]
        ),
        name="Type",  # noqa: F821
        default=RBRObjectType.NONE.name,
        update=update_type,
    )
    # DEPRECATED
    tint_sets: bpy.props.EnumProperty(  # type: ignore
        items=[(t.name, t.pretty(), t.pretty(), t.bitmask()) for t in TintSet],
        default=set([s.name for s in TintSet]),
        options={"ENUM_FLAG"},  # noqa: F821
    )
    geom_blocks_distance: bpy.props.EnumProperty(  # type: ignore
        items=[
            (t.name, t.pretty(), t.description(), t.value) for t in RenderChunkDistance
        ],
        name="Geom Blocks Type",
        default=RenderChunkDistance.NEAR.name,
    )
    is_geom_blocks_collision: bpy.props.BoolProperty(  # type: ignore
        name="Generate Collisions",
        description="Generate a static collision mesh for this object",
    )
    is_geom_blocks_invisible: bpy.props.BoolProperty(  # type: ignore
        name="Collision Only",
        description="Don't export the visual geometry component",
    )
    object_blocks_detail: bpy.props.EnumProperty(  # type: ignore
        name="Object Blocks Detail",
        items=[
            (t.name, t.pretty(), t.description(), t.value) for t in ObjectBlocksDetail
        ],
        default=ObjectBlocksDetail.BOTH.name,
    )
    # Technically it makes more sense for this to be a property of the mesh
    # itself, not the object, because we are using the mesh to determine
    # instancing. But it is much more user friendly to do it this way and the
    # partition the meshes based on material later.
    shape_collision_mesh_material: bpy.props.EnumProperty(  # type: ignore
        items=sorted(
            [(t.name, t.pretty(), t.pretty(), t.value) for t in object_materials],
            key=lambda x: x[0],
        ),
        name="Collision Material",
        default=MaterialID.UNDEFINED.name,
    )
    interactive_object_kind: bpy.props.EnumProperty(  # type: ignore
        items=[(t.name, t.pretty(), t.description(), t.value) for t in ObjectKind],
        name="Object Kind",
        default=ObjectKind.TRAFFIC_CONE.name,
    )
    interactive_object_apply_modifiers: bpy.props.BoolProperty(  # type: ignore
        name="Apply Modifiers",
        description="Make this object single user and apply modifiers when exporting",
        default=False,
    )

    def update_look_at_car(self, context: bpy.types.Context) -> None:
        camera_obj = context.object
        if camera_obj is None:
            return
        # Remove existing tracking constraints
        for constraint in camera_obj.constraints:
            if constraint.type == "TRACK_TO":
                camera_obj.constraints.remove(constraint)
        if not self.camera_look_at_car:
            return
        dummy_car = setup_dummy_car(context)
        # Set the parent to a driveline if it isn't already
        if (
            dummy_car.parent is None
            or dummy_car.parent.rbr_object_settings.type != RBRObjectType.DRIVELINE.name
        ):
            for obj in bpy.context.view_layer.objects:
                object_settings: RBRObjectSettings = obj.rbr_object_settings
                if object_settings.type == RBRObjectType.DRIVELINE.name:
                    dummy_car.parent = obj
                    break
        # Add track constraint
        track_to = camera_obj.constraints.new("TRACK_TO")
        track_to.target = dummy_car
        track_to.track_axis = "TRACK_NEGATIVE_Z"
        track_to.up_axis = "UP_Y"

    camera_look_at_car: bpy.props.BoolProperty(  # type: ignore
        update=update_look_at_car,
        name="Look at car",
        default=False,
    )
    camera_mode: bpy.props.EnumProperty(  # type: ignore
        items=[(t.name, t.pretty(), t.description(), t.value) for t in AnimCameraMode],
        name="Camera Mode",
        default=AnimCameraMode.DEFAULT.name,
    )
    camera_shake: bpy.props.FloatProperty(  # type: ignore
        name="Camera Shake",
        description="Higher values shake the camera more. Not visible in blender.",
        min=0,
        max=0.5,
    )

    brake_wall_inner_group: bpy.props.StringProperty(  # type: ignore
        name="Inner Group",
        description="Inner loop of vertices must be in this group",
        default="inner",  # noqa: F821
    )
    brake_wall_outer_group: bpy.props.StringProperty(  # type: ignore
        name="Outer Group",
        description="Outer loop of vertices must be in this group",
        default="outer",  # noqa: F821
    )
    brake_wall_respawn_group: bpy.props.StringProperty(  # type: ignore
        name="Respawn Group",
        description="Any vertices in this group will cause a black screen car respawn",
        default="respawn",  # noqa: F821
    )

    fence_kind: bpy.props.EnumProperty(  # type: ignore
        items=[(t.name, t.pretty(), t.pretty(), t.value) for t in fences.FenceKind],
        name="Fence Kind",
        default=fences.FenceKind.TAPE.name,
    )
    fence_pole_net_texture: bpy.props.EnumProperty(  # type: ignore
        items=[
            (t.name, t.pretty(), t.pretty(), t.value)
            for t in fences.FencePoleNetTexture
        ],
        name="Pole Type",
        default=fences.FencePoleNetTexture.GREY.name,
    )
    fence_pole_tape_texture: bpy.props.EnumProperty(  # type: ignore
        items=[
            (t.name, t.pretty(), t.pretty(), t.value)
            for t in fences.FencePoleTapeTexture
        ],
        name="Pole Texture",
        default=fences.FencePoleTapeTexture.BR.name,
    )
    fence_tile_net_texture: bpy.props.EnumProperty(  # type: ignore
        items=[
            (t.name, t.pretty(), t.pretty(), t.value)
            for t in fences.FenceTileNetTexture
        ],
        name="Net Texture",
        default=fences.FenceTileNetTexture.ORANGE.name,
    )
    fence_tile_tape_texture: bpy.props.EnumProperty(  # type: ignore
        items=[
            (t.name, t.pretty(), t.pretty(), t.value)
            for t in fences.FenceTileTapeTexture
        ],
        name="Tape Texture",
        default=fences.FenceTileTapeTexture.BR.name,
    )
    fence_shading: bpy.props.StringProperty(  # type: ignore
        name="Shading Layer",
    )
    fence_is_long: bpy.props.BoolProperty(  # type: ignore
        name="Fence is Long",  # noqa: F821
        description="Higher resolution used for rendering and collision detection",
    )

    wet_surface_kind: bpy.props.EnumProperty(  # type: ignore
        items=[(t.name, t.pretty(), t.pretty(), t.value) for t in WetSurfaceKind],
        name="Wet Surface Kind",
        default=WetSurfaceKind.WATER.name,
    )

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
        obj = context.active_object
        object_type = RBRObjectType[self.type]
        if object_type is not RBRObjectType.NONE:
            layout.prop(self, "exported")
        layout.prop(self, "type")
        if object_type is RBRObjectType.NONE:
            pass
        elif object_type is RBRObjectType.GEOM_BLOCKS:
            layout.prop(self, "geom_blocks_distance", expand=True)
            if self.geom_blocks_distance != RenderChunkDistance.FAR.name:
                layout.prop(self, "is_geom_blocks_collision")
                if self.is_geom_blocks_collision:
                    layout.prop(self, "is_geom_blocks_invisible")
        elif object_type is RBRObjectType.OBJECT_BLOCKS:
            layout.label(text="Level of detail settings")
            layout.prop(self, "object_blocks_detail", expand=True)
        elif object_type is RBRObjectType.CLIPPING_PLANE:
            pass
        elif object_type is RBRObjectType.DRIVELINE:
            pass
        elif object_type is RBRObjectType.ZFAR:
            pass
        elif object_type is RBRObjectType.CAR_LOCATION:
            pass
        elif object_type is RBRObjectType.CAMERA:
            layout.prop(self, "camera_look_at_car")
            layout.prop(self, "camera_mode", expand=True)
            if (
                self.camera_look_at_car
                and self.camera_mode != AnimCameraMode.DEFAULT.name
            ):
                layout.prop(self, "camera_shake", slider=True)
        elif object_type is RBRObjectType.SUPER_BOWL:
            pass
        elif object_type is RBRObjectType.REFLECTION_OBJECTS:
            pass
        elif object_type is RBRObjectType.SHAPE_COLLISION_MESH:
            layout.prop(self, "shape_collision_mesh_material")
        elif object_type is RBRObjectType.INTERACTIVE_OBJECTS:
            layout.prop(self, "interactive_object_apply_modifiers")
        elif object_type is RBRObjectType.INTERACTIVE_OBJECTS_COLMESH:
            layout.prop(self, "interactive_object_kind")
        elif object_type is RBRObjectType.WATER_OBJECTS:
            pass
        elif object_type is RBRObjectType.BRAKE_WALL:

            def vertex_group_ui(prop: str) -> None:
                layout.prop_search(
                    self,
                    prop,
                    obj,
                    "vertex_groups",
                    icon="GROUP_VERTEX",
                )

            vertex_group_ui("brake_wall_inner_group")
            vertex_group_ui("brake_wall_outer_group")
            vertex_group_ui("brake_wall_respawn_group")
        elif object_type is RBRObjectType.SUN:
            pass
        elif object_type is RBRObjectType.REGISTRATION_ZONE:
            pass
        elif object_type is RBRObjectType.SOUND_EMITTER:
            pass
        elif object_type is RBRObjectType.INSTANCER:
            pass
        elif object_type is RBRObjectType.FENCE:
            layout.prop(self, "fence_kind", expand=True)
            layout.prop(self, "fence_pole_net_texture")
            if fences.FenceKind[self.fence_kind] is fences.FenceKind.TAPE:
                layout.prop(self, "fence_pole_tape_texture")
                layout.prop(self, "fence_tile_tape_texture")
            if fences.FenceKind[self.fence_kind] is fences.FenceKind.NET:
                layout.prop(self, "fence_tile_net_texture")
            if isinstance(obj.data, bpy.types.Mesh):
                layout.prop_search(
                    self,
                    "fence_shading",
                    obj.data,
                    "attributes",
                    icon="COLOR",
                )
            layout.prop(self, "fence_is_long")
        elif object_type is RBRObjectType.WET_SURFACE:
            layout.prop(self, "wet_surface_kind", expand=True)
        else:
            raise NotImplementedError(object_type.name)
        err = object_type.validation_errors(obj)
        if err is not None:
            box = layout.box()
            box.label(text="Invalid " + object_type.pretty(), icon="ERROR")
            box.label(text=err)
