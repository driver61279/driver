import math
from typing import Any, List, Optional, Tuple

import bpy  # type: ignore
from mathutils import Vector  # type: ignore

from rbr_track_formats import errors
from rbr_track_formats.mat import (
    ConditionIdentifier,
    MaterialID,
    MaterialMap,
    SurfaceType,
    SurfaceAge,
)
from .types import GrabHandle


def point_in_area(point: Vector, pos1: Vector, pos2: Vector) -> bool:
    (px, py) = point
    (x0, y0) = pos1
    (x1, y1) = pos2
    return all(
        [
            px > min(x0, x1),
            px < max(x0, x1),
            py > min(y0, y1),
            py < max(y0, y1),
        ]
    )


class RBRPropertyNodePointer(bpy.types.PropertyGroup):
    """This PropertyGroup can point at a particular node in a material.
    It's necessary because from a node's draw context we can't detect the material directly.
    We instead use the node tree pointer to identify the material.
    """

    node_name: bpy.props.StringProperty()  # type: ignore
    # String instead of Int, IntProperty can overflow.
    nodetree_pointer: bpy.props.StringProperty()  # type: ignore

    def get_shader_node(self) -> Optional[bpy.types.ShaderNode]:
        found_tree = None
        # Look for the node tree matching the pointer. Can't use name equality,
        # since node trees in different materials can have the same name!
        # We can't actually use the pointer as a pointer, blender crashes. Not
        # sure what the problem is, but this loop is fast enough.
        for material in bpy.data.materials:
            if material.use_nodes:
                if str(material.node_tree.as_pointer()) == self.nodetree_pointer:
                    found_tree = material.node_tree
                    break
        if found_tree is None:
            return None
        return found_tree.nodes.get(self.node_name)


class RBRMaterialID(bpy.types.PropertyGroup):
    material_id: bpy.props.IntProperty()  # type: ignore

    def to_material(self) -> MaterialID:
        return MaterialID(self.material_id)


class RBRMaterialMapRow(bpy.types.PropertyGroup):
    cols: bpy.props.CollectionProperty(  # type: ignore
        type=RBRMaterialID,
    )

    def __init__(self) -> None:
        for _ in range(16):
            self.cols.add()


class RBRMaterialMap(bpy.types.PropertyGroup):
    """An individual material map. This is a direct encoding of the normal
    MaterialMap class, as blender properties, so they can be saved in blend
    files."""

    rows: bpy.props.CollectionProperty(  # type: ignore
        type=RBRMaterialMapRow,
    )

    def __init__(self) -> None:
        for _ in range(16):
            row = self.rows.add()
            row.__init__()

    def set_from_format(self, mat: MaterialMap) -> None:
        """Set this blender property based material map from a plain material
        map
        """
        self.rows.clear()
        for mat_row in mat.bitmap:
            row = self.rows.add()
            for mat_id in mat_row:
                col = row.cols.add()
                col.material_id = mat_id.value

    def to_format(self) -> MaterialMap:
        """Convert this blender property based material map into a plain
        material map
        """
        rows: List[List[MaterialID]] = []
        for mat_row in self.rows:
            cols = []
            for mat_id in mat_row.cols:
                cols.append(mat_id.to_material())
            rows.append(cols)
        return MaterialMap(bitmap=rows)


class RBRMaterialMaps(bpy.types.PropertyGroup):
    """A collection of material maps, one for each surface type/wear
    combination. This also controls the corner positions of all maps.
    """

    # Position of one corner in UV coordinates
    # This is the bottom left of the viewport
    position_1: bpy.props.FloatVectorProperty(size=2)  # type: ignore
    # Position of opposite corner in UV coordinates
    # This is the top right of the viewport
    # Invariant: both X and Y coordinates are higher than X and Y coordinates of
    # position_1. This way the maps are always the same way up, and copying and
    # pasting between them works properly.
    position_2: bpy.props.FloatVectorProperty(size=2)  # type: ignore
    maps: bpy.props.CollectionProperty(  # type: ignore
        type=RBRMaterialMap,
    )

    repeat_x: bpy.props.BoolProperty()  # type: ignore
    repeat_y: bpy.props.BoolProperty()  # type: ignore

    def __init__(self) -> None:
        for _ in range(9):
            m = self.maps.add()
            m.__init__()
        self.maintain_position_invariant()

    # 'other' has type RBRMaterialMaps, but we can't specify that here without
    # from __future__ import annotations, and that breaks PropertyGroup
    # definitions. See CONTRIBUTING.md.
    def copy(self, other: Any) -> None:
        self.position_1 = other.position_1
        self.position_2 = other.position_2
        self.repeat_x = other.repeat_x
        self.repeat_y = other.repeat_y
        self.maps.clear()
        for other_map in other.maps:
            map = self.maps.add()
            map.set_from_format(other_map.to_format())

    def maintain_position_invariant(self) -> Tuple[bool, bool]:
        """Maintain the position invariant (see comment by position
        definitions)"""
        (p1x, p1y) = self.position_1
        (p2x, p2y) = self.position_2
        flip_x = p1x > p2x
        flip_y = p1y > p2y
        if flip_x:
            self.position_1[0] = p2x
            self.position_2[0] = p1x
        if flip_y:
            self.position_1[1] = p2y
            self.position_2[1] = p1y
        # Fix positions if this map is marked as repeated
        if self.repeat_x:
            self.position_1[0] = 0.0
            self.position_2[0] = 1.0
        if self.repeat_y:
            self.position_1[1] = 0.0
            self.position_2[1] = 1.0
        return (flip_x, flip_y)

    def update_mat_pos(
        self, handle: GrabHandle, mouse_pos: Vector
    ) -> Optional[GrabHandle]:
        """Update the material position using a grab handle, and possibly return
        a new grab handle. The returned grab handle is present when the map gets
        flipped in an axis, to make sure maps are always the same way up."""
        if handle == GrabHandle.BOTTOM_LEFT:
            self.position_1[0] = mouse_pos.x
            self.position_1[1] = mouse_pos.y
        elif handle == GrabHandle.BOTTOM_MID:
            self.position_1[1] = mouse_pos.y
        elif handle == GrabHandle.BOTTOM_RIGHT:
            self.position_2[0] = mouse_pos.x
            self.position_1[1] = mouse_pos.y
        elif handle == GrabHandle.MID_LEFT:
            self.position_1[0] = mouse_pos.x
        elif handle == GrabHandle.MID_RIGHT:
            self.position_2[0] = mouse_pos.x
        elif handle == GrabHandle.TOP_LEFT:
            self.position_1[0] = mouse_pos.x
            self.position_2[1] = mouse_pos.y
        elif handle == GrabHandle.TOP_MID:
            self.position_2[1] = mouse_pos.y
        elif handle == GrabHandle.TOP_RIGHT:
            self.position_2[0] = mouse_pos.x
            self.position_2[1] = mouse_pos.y
        (flip_x, flip_y) = self.maintain_position_invariant()
        return handle.flip(flip_x, flip_y)

    def drag(self, delta: Vector) -> None:
        self.position_1[0] += delta.x
        self.position_1[1] += delta.y
        self.position_2[0] += delta.x
        self.position_2[1] += delta.y
        self.maintain_position_invariant()

    def get_map(
        self, surface_type: SurfaceType, surface_age: SurfaceAge
    ) -> RBRMaterialMap:
        cond = ConditionIdentifier(surface_type=surface_type, surface_age=surface_age)
        m: RBRMaterialMap = self.maps[cond.packed_index()]
        return m

    def get_active_map(self) -> RBRMaterialMap:
        surface_type = bpy.context.scene.rbr_track_settings.get_active_surface_type()
        # Walk to the highest parent node tree (ShaderNodeRBRTexture) and get
        # the internal data
        is_road_surface = self.id_data.nodes["internal"].is_road_surface
        if is_road_surface:
            surface_age = bpy.context.scene.rbr_track_settings.get_active_surface_age()
        else:
            surface_age = SurfaceAge.NEW
        return self.get_map(surface_type, surface_age)

    def uv_to_mat(self, pos: Vector) -> Vector:
        """From UV space (view space) to material space"""
        (x, y) = pos.to_tuple()
        (x0, y0) = self.position_1
        (x1, y1) = self.position_2
        dx = x1 - x0
        dy = y1 - y0
        if dx != 0:
            mat_x = (x - x0) / dx
        else:
            mat_x = 0
        if dy != 0:
            mat_y = (y - y0) / dy
        else:
            mat_y = 0
        return Vector((mat_x, mat_y))

    def quantized_uv(self, uv_x: float, uv_y: float) -> Tuple[int, int]:
        """Given UV coordinates in texture UV space, return the RBR collision
        material quantized UV coordinates, pre swapped. This is not quite the
        same as the x,y pixel: there are 16 pixels in a given direction, but
        also only 16 distinct UV points (which need to represent the left side
        of the leftmost pixel, and the right side of the rightmost pixel, and if
        this was treated the same way as the pixel calculation, we'd need 17
        distinct points)."""
        mat = self.uv_to_mat(Vector((uv_x, uv_y)))

        def clamp(a: int) -> int:
            return max(0, min(15, round(a * 15)))

        return (clamp(mat.y), clamp(mat.x))

    def pixel(self, uv_x: float, uv_y: float) -> Tuple[int, int]:
        """Find the x,y coordinates of the pixel containing the given UV
        coordinates"""
        mat = self.uv_to_mat(Vector((uv_x, uv_y)))

        def clamp(a: int) -> int:
            return max(0, min(15, math.floor(a * 16)))

        return (clamp(mat.x), clamp(mat.y))

    def point_in_map(self, px: int, py: int) -> bool:
        return point_in_area(Vector((px, py)), self.position_1, self.position_2)


class RBRFallbackMaterials(bpy.types.PropertyGroup):
    dry_new: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore
    damp_new: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore
    wet_new: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore
    dry_normal: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore
    damp_normal: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore
    wet_normal: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore
    dry_worn: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore
    damp_worn: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore
    wet_worn: bpy.props.PointerProperty(type=RBRMaterialID)  # type: ignore

    def active_material(self) -> MaterialID:
        track_settings = bpy.context.scene.rbr_track_settings
        surface_type: SurfaceType = track_settings.get_active_surface_type()
        surface_age: SurfaceAge = track_settings.get_active_surface_age()
        return self.get_condition(surface_type, surface_age)

    def get_condition(
        self, surface_type: SurfaceType, surface_age: SurfaceAge
    ) -> MaterialID:
        if surface_type is SurfaceType.DRY and surface_age is SurfaceAge.NEW:
            return self.dry_new.to_material()  # type: ignore
        elif surface_type is SurfaceType.DRY and surface_age is SurfaceAge.NORMAL:
            return self.dry_normal.to_material()  # type: ignore
        elif surface_type is SurfaceType.DRY and surface_age is SurfaceAge.WORN:
            return self.dry_worn.to_material()  # type: ignore
        elif surface_type is SurfaceType.DAMP and surface_age is SurfaceAge.NEW:
            return self.damp_new.to_material()  # type: ignore
        elif surface_type is SurfaceType.DAMP and surface_age is SurfaceAge.NORMAL:
            return self.damp_normal.to_material()  # type: ignore
        elif surface_type is SurfaceType.DAMP and surface_age is SurfaceAge.WORN:
            return self.damp_worn.to_material()  # type: ignore
        elif surface_type is SurfaceType.WET and surface_age is SurfaceAge.NEW:
            return self.wet_new.to_material()  # type: ignore
        elif surface_type is SurfaceType.WET and surface_age is SurfaceAge.NORMAL:
            return self.wet_normal.to_material()  # type: ignore
        elif surface_type is SurfaceType.WET and surface_age is SurfaceAge.WORN:
            return self.wet_worn.to_material()  # type: ignore
        else:
            raise errors.RBRAddonBug(
                f"Unhandled type/age in active_material: {surface_type} {surface_age}"
            )

    def set_from_active(self) -> None:
        paint_material = bpy.context.scene.rbr_material_picker.material_id
        track_settings = bpy.context.scene.rbr_track_settings
        surface_type: SurfaceType = track_settings.get_active_surface_type()
        surface_age: SurfaceAge = track_settings.get_active_surface_age()
        if surface_type is SurfaceType.DRY and surface_age is SurfaceAge.NEW:
            self.dry_new.material_id = paint_material
        elif surface_type is SurfaceType.DRY and surface_age is SurfaceAge.NORMAL:
            self.dry_normal.material_id = paint_material
        elif surface_type is SurfaceType.DRY and surface_age is SurfaceAge.WORN:
            self.dry_worn.material_id = paint_material
        elif surface_type is SurfaceType.DAMP and surface_age is SurfaceAge.NEW:
            self.damp_new.material_id = paint_material
        elif surface_type is SurfaceType.DAMP and surface_age is SurfaceAge.NORMAL:
            self.damp_normal.material_id = paint_material
        elif surface_type is SurfaceType.DAMP and surface_age is SurfaceAge.WORN:
            self.damp_worn.material_id = paint_material
        elif surface_type is SurfaceType.WET and surface_age is SurfaceAge.NEW:
            self.wet_new.material_id = paint_material
        elif surface_type is SurfaceType.WET and surface_age is SurfaceAge.NORMAL:
            self.wet_normal.material_id = paint_material
        elif surface_type is SurfaceType.WET and surface_age is SurfaceAge.WORN:
            self.wet_worn.material_id = paint_material


def register() -> None:
    bpy.utils.register_class(RBRPropertyNodePointer)
    bpy.utils.register_class(RBRMaterialID)
    bpy.utils.register_class(RBRMaterialMapRow)
    bpy.utils.register_class(RBRMaterialMap)
    bpy.utils.register_class(RBRMaterialMaps)
    bpy.utils.register_class(RBRFallbackMaterials)


def unregister() -> None:
    bpy.utils.unregister_class(RBRFallbackMaterials)
    bpy.utils.unregister_class(RBRMaterialMaps)
    bpy.utils.unregister_class(RBRMaterialMap)
    bpy.utils.unregister_class(RBRMaterialMapRow)
    bpy.utils.unregister_class(RBRMaterialID)
    bpy.utils.unregister_class(RBRPropertyNodePointer)
