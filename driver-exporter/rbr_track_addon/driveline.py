from typing import List, Optional, Set, Tuple
import math

import bpy  # type: ignore
import blf  # type: ignore
import gpu  # type: ignore
import gpu_extras  # type: ignore
from mathutils import Vector  # type: ignore
from bpy_extras.view3d_utils import location_3d_to_region_2d  # type: ignore

from rbr_track_formats.dls.animation_sets import PacenoteID

from .object_settings.types import RBRObjectSettings, RBRObjectType


def ensure_longest_spline(
    obj: bpy.types.Object,
) -> Optional[Tuple[bpy.types.Spline, float]]:
    """Get the longest spline and its length. Beware: length will be incorrect
    if the curve is scaled."""
    if not isinstance(obj.data, bpy.types.Curve):
        return None
    curve = obj.data
    # Find longest spline
    longest_spline = None
    longest_length = 0
    for this_spline in curve.splines:
        this_length = this_spline.calc_length(resolution=16)
        if this_length > longest_length:
            longest_length = this_length
            longest_spline = this_spline
    for spline in curve.splines:
        if spline != longest_spline:
            curve.splines.remove(spline)
    return (longest_spline, longest_length)


class RBR_OT_remove_pacenote(bpy.types.Operator):
    """Remove a pacenote from a driveline object"""

    bl_idname = "rbr.remove_pacenote"
    bl_label = "Remove pacenote"
    bl_description = "Remove pacenote from the stack"
    bl_options = {"UNDO"}

    index: bpy.props.IntProperty()  # type: ignore

    @classmethod
    def poll(_cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        object_settings: RBRObjectSettings = obj.rbr_object_settings
        object_type: RBRObjectType = RBRObjectType[object_settings.type]
        return all(
            [
                object_type is RBRObjectType.DRIVELINE,
                object_type.validation_errors(obj) is None,
            ]
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        return self.invoke(context, None)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        obj = context.active_object
        driveline: RBRDrivelineSettings = obj.rbr_driveline_settings
        driveline.pacenotes.remove(self.index)
        driveline.update_sorted_pacenotes()
        return {"FINISHED"}


class RBR_OT_add_pacenote(bpy.types.Operator):
    """Add a pacenote to a driveline object"""

    bl_idname = "rbr.add_pacenote"
    bl_label = "Add pacenote"
    bl_description = "Add a pacenote to the stack"
    bl_options = {"UNDO"}

    @classmethod
    def poll(_cls, context: bpy.types.Context) -> bool:
        return RBR_OT_remove_pacenote.poll(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        return self.invoke(context, None)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        obj = context.active_object
        driveline: RBRDrivelineSettings = obj.rbr_driveline_settings
        pacenote = driveline.pacenotes.add()
        pacenote.location = max(map(lambda p: p.location, driveline.pacenotes))
        driveline.update_sorted_pacenotes()
        return {"FINISHED"}


class RBRPacenoteDefinition(bpy.types.PropertyGroup):
    def update(self, context: bpy.types.Context) -> None:
        obj = context.active_object
        if obj is None:
            return
        driveline: RBRDrivelineSettings = obj.rbr_driveline_settings
        driveline.update_sorted_pacenotes()

    location: bpy.props.FloatProperty(  # type: ignore
        name="Location",  # noqa: F821
        min=0,
        max=100000,
        update=update,
    )
    pacenote_id: bpy.props.EnumProperty(  # type: ignore
        items=[
            (p.name, p.pretty(), p.pretty(), p.value)
            for p in PacenoteID.nicely_ordered_universe()
        ],
        name="Note",  # noqa: F821
        default=PacenoteID.EVENT_START.name,
    )

    def draw(
        self, context: bpy.types.Context, layout: bpy.types.UILayout, index: int
    ) -> None:
        row = layout.row()
        row.prop(self, "location", text="")
        row.prop(self, "pacenote_id", text="")
        op = row.operator(
            RBR_OT_remove_pacenote.bl_idname,
            icon="REMOVE",
            text="",
        )
        op.index = index


class RBRDrivelineSettings(bpy.types.PropertyGroup):
    # We maintain a list of sorted pacenotes so we don't have to compute it
    # every frame
    def get_sorted_pacenote_indices(self) -> List[int]:
        if "_sorted_pacenote_indices" in self:
            return self["_sorted_pacenote_indices"]  # type: ignore
        else:
            return []

    def update_sorted_pacenotes(self) -> None:
        self["_sorted_pacenote_indices"] = list(
            map(
                lambda t: t[0],
                sorted(enumerate(self.pacenotes), key=lambda t: t[1].location),
            )
        )

    alpha_far: bpy.props.FloatProperty(  # type: ignore
        name="Visible Distance",
        min=1e3,
        default=3e3,
        max=2e4,
    )

    pacenotes: bpy.props.CollectionProperty(  # type: ignore
        type=RBRPacenoteDefinition,
        name="Pacenotes",  # noqa: F821
    )

    def draw(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        obj: bpy.types.Object,
    ) -> None:
        layout.prop(self, "alpha_far", slider=True)
        layout.separator()
        for index in self.get_sorted_pacenote_indices():
            pacenote = self.pacenotes[index]
            pacenote.draw(context, layout, index)
        layout.operator(RBR_OT_add_pacenote.bl_idname)


class RBR_PT_driveline_settings(bpy.types.Panel):
    """A simple panel to display the driveline settings and operators."""

    bl_idname = "RBR_PT_driveline_settings"
    bl_label = "RBR Driveline Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(_cls, context: bpy.types.Context) -> bool:
        return RBR_OT_remove_pacenote.poll(context)

    def draw(self, context: bpy.types.Context) -> None:
        obj = context.active_object
        layout = self.layout
        obj.rbr_driveline_settings.draw(context, layout, obj)


pacenote_draw_handler = None


def draw_pacenotes_in_3d() -> None:
    context = bpy.context
    obj = context.active_object
    if obj is None:
        return
    object_settings: RBRObjectSettings = obj.rbr_object_settings
    if object_settings.type != RBRObjectType.DRIVELINE.name:
        return

    spline_and_len = ensure_longest_spline(obj)
    if spline_and_len is None:
        return
    (spline, _) = spline_and_len
    if spline.type != "BEZIER":
        return

    driveline: RBRDrivelineSettings = obj.rbr_driveline_settings

    # x/y offset of text compared to point (screen space)
    offset = 15

    pacenote_stack = []
    lines = []
    lines_colors = []
    points = []
    points_colors = []
    # Optimisation for position_along_spline
    last_min_point = (0, 0.0)
    for index in driveline.get_sorted_pacenote_indices():
        pacenote = driveline.pacenotes[index]
        m_pos_spline = position_along_spline(
            spline=spline,
            distance_along_spline=pacenote.location,
            min_point=last_min_point,
        )
        if m_pos_spline is None:
            continue
        (last_min_point_prime, pos_spline) = m_pos_spline
        pos_spline = obj.matrix_world @ pos_spline
        last_min_point = last_min_point_prime
        pos = location_3d_to_region_2d(
            context.region,
            context.region_data,
            pos_spline,
        )
        # Returns None when the pacenote is off screen, so we just skip it
        if pos is None:
            continue
        # Calculate a nice alpha value so far away notes fade out
        camera_pos = context.region_data.view_matrix.inverted().translation
        view_dist = (pos_spline - camera_pos).length
        near = 200
        far = driveline.alpha_far
        depth = min(max(view_dist, near), far)
        alpha = 1 - (depth - near) / (far - near)
        pacenote_stack.append((pacenote.pacenote_id, pos, alpha))
        lines.append((pos.x, pos.y))
        lines.append((pos.x + offset, pos.y + offset))
        lines_colors.append((1, 1, 1, alpha))
        lines_colors.append((1, 1, 1, alpha))
        points.append((pos.x, pos.y))
        points_colors.append((1, 1, 1, alpha))

    # Draw a small line from the driveline to the position of the text
    gpu.state.line_width_set(2)
    shader = gpu.shader.from_builtin("SMOOTH_COLOR")
    shader.bind()
    batch = gpu_extras.batch.batch_for_shader(
        shader, "LINES", {"pos": lines, "color": lines_colors}
    )
    gpu.state.blend_set("ALPHA")
    batch.draw(shader)
    batch = gpu_extras.batch.batch_for_shader(
        shader, "POINTS", {"pos": points, "color": points_colors}
    )
    batch.draw(shader)

    # Draw text for each note
    for pacenote, pos, alpha in pacenote_stack:
        pid = PacenoteID[pacenote]
        FONT_ID = 0
        blf.position(FONT_ID, pos.x + offset + 2, pos.y + offset + 2, 0)
        if pid.is_event():
            blf.color(FONT_ID, 0.91, 0.49, 0.05, alpha)
        else:
            blf.color(FONT_ID, 1, 1, 1, alpha)
        blf.size(FONT_ID, 20)
        blf.draw(FONT_ID, pid.pretty())


def interpolate_cubic_bezier(
    bsp0: bpy.types.BezierSplinePoint,
    bsp1: bpy.types.BezierSplinePoint,
    t: float,
) -> Vector:
    """Get the position at a certain point along the cubic bezier spline
    segment

    bsp0
        First bezier point
    bsp1
        Second bezier point
    t
        Relative position on curve (range: [0, 1])
    """
    p0 = bsp0.co
    p1 = bsp0.handle_right
    p2 = bsp1.handle_left
    p3 = bsp1.co
    r = 1 - t
    a = r * r * r * p0
    b = 3 * r * r * t * p1
    c = 3 * r * t * t * p2
    d = t * t * t * p3
    return a + b + c + d


def walk_cubic_bezier_segment(
    bsp0: bpy.types.BezierSplinePoint,
    bsp1: bpy.types.BezierSplinePoint,
    distance_along_segment: float,
    resolution: int = 16,
) -> Tuple[float, Optional[Vector]]:
    """Walk along a segment and return the segment length and the point which
    is at distance_along_segment. Returns None if the point is not on the
    segment.
    """
    walked = 0.0
    last_pos = bsp0.co
    pos_to_return = None
    for i in range(resolution + 2):
        t = i / (resolution + 1)
        pos = interpolate_cubic_bezier(bsp0, bsp1, t)
        # A vector pointing from the last position to this position
        segment = pos - last_pos
        # If the point we seek lies on this segment
        if walked <= distance_along_segment <= walked + segment.length:
            # Linear interpolation between last position and this position
            pos_to_return = last_pos + segment.normalized() * (
                distance_along_segment - walked
            )
        walked += segment.length
        last_pos = pos
    return (walked, pos_to_return)


def position_along_spline(
    spline: bpy.types.Spline,
    distance_along_spline: float,
    min_point: Tuple[int, float] = (0, 0.0),
) -> Optional[Tuple[Tuple[int, float], Vector]]:
    """Compute the position from a distance along a spline.

    spline
        The spline we are walking along
    distance_along_spline
        The distance along the spline to walk
    min_point
        Optimisation - the minimum point to consider and the distance
        (previously) walked to the minimum point

    Returns None if the point does not lie on the spline.
    Otherwise returns a tuple of:
        - The index of the segment the point lies on
        - The total distance walked along the spline up to that segment
        - The world position
    The first two of these can be plugged back into future invocations,
    provided we are walking a sorted list of points. This turns a quadratic
    algorithm into a linear one.
    """
    distance_travelled_from_min_point = 0.0
    for i in range(min_point[0], len(spline.bezier_points) - 1):
        bsp0 = spline.bezier_points[i]
        bsp1 = spline.bezier_points[i + 1]
        distance_along_segment = (
            distance_along_spline - min_point[1] - distance_travelled_from_min_point
        )
        (segment_length, pos) = walk_cubic_bezier_segment(
            bsp0, bsp1, distance_along_segment
        )
        if pos is not None:
            # The point lies on this segment
            return ((i, min_point[1] + distance_travelled_from_min_point), pos)
        else:
            distance_travelled_from_min_point += segment_length
    return None


def setup_driveline_curve(
    curve: bpy.types.Curve,
    computed_length: float,
) -> None:
    curve.dimensions = "3D"
    curve.twist_mode = "Z_UP"
    # Make sure we are animating the path, for any child objects
    curve.use_path = True
    curve.path_duration = int(computed_length)
    anim = curve.animation_data
    if anim is None:
        anim = curve.animation_data_create()
    if anim.action is None:
        anim.action = bpy.data.actions.new("Driveline Action")
    fcurve = anim.action.fcurves.find("eval_time")
    if fcurve is None:
        fcurve = anim.action.fcurves.new("eval_time")
    for modifier in fcurve.modifiers.values():
        fcurve.modifiers.remove(modifier)
    gen = fcurve.modifiers.new("GENERATOR")
    gen.coefficients = (0, 1)
    fcurve.modifiers.active = gen
    # Hack to make sure it's updated. Must be some sort of bad cache in the way.
    gen.mute = True
    gen.mute = False


def setup_zfar(zfar: bpy.types.Object) -> bpy.types.Object:
    """Setup a zfar (render distance) circle."""
    zfar.empty_display_type = "CIRCLE"
    zfar.empty_display_size = 300
    zfar.rotation_euler = (math.pi / 2, 0, 0)
    zfar.show_in_front = True
    zfar.hide_render = True
    return zfar


def fixup_driveline(obj: bpy.types.Object, full_fixup: bool) -> None:
    """Ensure the driveline meets RBR expectations.
    - Mirrors the spline handles, RBR only supports mirrored handles
    - Sets radius == 1, this value is used to scale child objects like render
      distance.

    obj
        Driveline object
    full_fixup
        Modify all handles
    """
    spline_and_len = ensure_longest_spline(obj)
    if spline_and_len is None:
        return
    (spline, length) = spline_and_len
    if full_fixup:
        setup_driveline_curve(
            obj.data,
            length,  # TODO can we use our internal length function here?
        )
    for bezier_point in spline.bezier_points:
        any_selected = any(
            [
                bezier_point.select_control_point,
                bezier_point.select_left_handle,
                bezier_point.select_right_handle,
            ]
        )
        # Skip the point if nothing is selected. Must do this to avoid a
        # performance penalty in edit mode.
        if not full_fixup and not any_selected:
            continue
        # Force use of aligned handles
        bezier_point.handle_left_type = "ALIGNED"
        bezier_point.handle_right_type = "ALIGNED"
        # So that parenting works correctly without scaling the objects
        bezier_point.radius = 1.0
        # Force the handles to be equal length
        pos = bezier_point.co
        if full_fixup:
            # Set handles to the average of both
            left = bezier_point.handle_left
            right = bezier_point.handle_right
            # Vector from left to right, halved
            between = (right - left) * 0.5
            bezier_point.handle_left = pos - between
            bezier_point.handle_right = pos + between
        else:
            # Move opposite handle
            if not bezier_point.select_right_handle:
                left = bezier_point.handle_left
                bezier_point.handle_right = 2 * pos - left
            if not bezier_point.select_left_handle:
                right = bezier_point.handle_right
                bezier_point.handle_left = 2 * pos - right


@bpy.app.handlers.persistent  # type: ignore
def fixup_driveline_daemon(
    scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph
) -> None:
    """A little daemon which watches for driveline updates and fiddles with
    it to ensure it matches RBR requirements."""
    for update in depsgraph.updates:
        if not update.is_updated_geometry:
            continue
        if not isinstance(update.id, bpy.types.Object):
            continue
        obj = update.id
        # Check if we are a driveline
        object_settings: RBRObjectSettings = obj.rbr_object_settings
        if object_settings.type != RBRObjectType.DRIVELINE.name:
            continue
        try:
            was_edit_mode = fixup_driveline_daemon.last_mode == "EDIT"
        except AttributeError:
            was_edit_mode = False
        finally:
            fixup_driveline_daemon.last_mode = obj.mode
        to_object_mode = obj.mode == "OBJECT" and was_edit_mode
        fixup_driveline(obj, full_fixup=to_object_mode)
        break


def register() -> None:
    bpy.utils.register_class(RBRPacenoteDefinition)
    bpy.utils.register_class(RBRDrivelineSettings)
    bpy.types.Object.rbr_driveline_settings = bpy.props.PointerProperty(
        type=RBRDrivelineSettings,
    )
    bpy.utils.register_class(RBR_OT_add_pacenote)
    bpy.utils.register_class(RBR_OT_remove_pacenote)
    bpy.utils.register_class(RBR_PT_driveline_settings)
    global pacenote_draw_handler
    pacenote_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_pacenotes_in_3d,
        (),
        "WINDOW",
        "POST_PIXEL",
    )
    bpy.app.handlers.depsgraph_update_post.append(fixup_driveline_daemon)


def unregister() -> None:
    try:
        bpy.app.handlers.depsgraph_update_post.remove(fixup_driveline_daemon)
    except ValueError:
        pass
    bpy.types.SpaceView3D.draw_handler_remove(pacenote_draw_handler, "WINDOW")
    bpy.utils.unregister_class(RBR_PT_driveline_settings)
    bpy.utils.unregister_class(RBR_OT_remove_pacenote)
    bpy.utils.unregister_class(RBR_OT_add_pacenote)
    del bpy.types.Object.rbr_driveline_settings
    bpy.utils.unregister_class(RBRDrivelineSettings)
    bpy.utils.unregister_class(RBRPacenoteDefinition)
