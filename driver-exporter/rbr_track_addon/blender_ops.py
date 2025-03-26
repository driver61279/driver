"""This module contains bpy.ops functions which have been wrapped to remove the
awkward context dependent behaviour. Over time, all required bpy.ops functions
should be wrapped with functions in this module, so I don't go completely insane
with peculiar context errors, operators not working as expected, or operators
modifying context unexpectedly.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

import bmesh  # type: ignore
import bpy  # type: ignore
import numpy as np

from rbr_track_formats import errors
from .object_settings.types import RBRObjectSettings, RBRObjectType
from rbr_track_formats.logger import Logger


A = TypeVar("A")


def unions(sets: Iterable[Set[A]]) -> Set[A]:
    result: Set[A] = set()
    for s in sets:
        result = result.union(s)
    return result


@dataclass
class TracedObject:
    parents: Set[str]
    obj: bpy.types.Object

    def source_name(self) -> str:
        if len(self.parents) == 1:
            return list(self.parents)[0]
        else:
            return str(self.parents)

    @staticmethod
    def create(obj: bpy.types.Object) -> TracedObject:
        return TracedObject(
            parents=set([obj.name_full]),
            obj=obj,
        )


def mesh_is_convex(
    obj: TracedObject,
) -> bool:
    mesh = obj.obj.data
    mesh.calc_loop_triangles()
    tolerance = 0.1
    for triangle in mesh.loop_triangles:
        d = -np.dot(
            mesh.vertices[triangle.vertices[0]].co,
            triangle.normal,
        )
        for vertex in mesh.vertices:
            if vertex.index not in triangle.vertices:
                h = (
                    np.dot(
                        vertex.co,
                        triangle.normal,
                    )
                    + d
                )
                if h > tolerance:
                    return False
    return True


def copy_linked_scene(
    scene: bpy.types.Scene,
) -> bpy.types.Scene:
    init_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    try:
        bpy.ops.scene.new(type="LINK_COPY")
        scene = bpy.context.window.scene
        return scene
    finally:
        bpy.context.window.scene = init_scene


def create_cube(
    name: str,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    try:
        bmesh.ops.create_cube(bm, size=1.0)
        bm.to_mesh(mesh)
        return bpy.data.objects.new(name, mesh)
    finally:
        bm.free()


def delete_loose(
    traced_obj: TracedObject,
) -> None:
    def go() -> None:
        try:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.delete_loose(
                use_verts=True,
                use_edges=False,
                use_faces=False,
            )
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")

    with_active_object(traced_obj, go)


def select_objects_exclusively(
    objs: Iterable[bpy.types.Object],
) -> None:
    """Exclusively select the given objects in the global context."""
    for obj in bpy.data.objects:
        obj.select_set(False)
    for obj in objs:
        obj.select_set(True)


def with_selected_objects(
    traced_objs: Iterable[TracedObject],
    f: Callable[[], A],
) -> A:
    """Select the objects and call the function (probably an operator which
    touches selected objects in the global context). Resets the global context
    selection after calling the function.
    """
    original_selected = bpy.context.selected_objects.copy()
    original_hide_selects = dict()
    for traced_obj in traced_objs:
        obj = traced_obj.obj
        original_hide_selects[obj.name] = obj.hide_select
        obj.hide_select = False
    try:
        select_objects_exclusively([o.obj for o in traced_objs])
        return f()
    finally:
        select_objects_exclusively(original_selected)
        for obj_name, hide_select in original_hide_selects.items():
            try:
                bpy.data.objects[obj_name].hide_select = hide_select
            except KeyError:
                continue


def with_active_object(
    traced_obj: TracedObject,
    func: Callable[[], A],
) -> A:
    """Run a function with the given object active in global context.
    Useful for calling operators which ignore overrides.
    """

    original = bpy.context.view_layer.objects.active
    try:
        bpy.context.view_layer.objects.active = traced_obj.obj
        return func()
    finally:
        bpy.context.view_layer.objects.active = original


def apply_visual_transforms(
    traced_objs: Iterable[TracedObject],
) -> None:
    """Apply visual transforms for all objects in a list."""

    def inner() -> None:
        bpy.ops.object.visual_transform_apply()

    return with_selected_objects(traced_objs, inner)


def apply_transforms(
    traced_objs: Iterable[TracedObject],
) -> None:
    """Apply transforms for all objects in a list."""

    def inner() -> None:
        bpy.ops.object.transform_apply()

    return with_selected_objects(traced_objs, inner)


def duplicate_objects(
    traced_objs: List[TracedObject],
) -> List[TracedObject]:
    # This operator duplicates the objects and adds them to the global
    # selection
    def duplicate() -> List[bpy.types.Object]:
        bpy.ops.object.duplicate(
            linked=False,
            mode="INIT",
        )
        return bpy.context.selected_objects.copy()  # type: ignore

    dupes = with_selected_objects(traced_objs, duplicate)
    traced_dupes = []
    for dupe, parent in zip(dupes, traced_objs):
        traced_dupes.append(
            TracedObject(
                parents=parent.parents,
                obj=dupe,
            )
        )
    return traced_dupes


def material_slot_remove_unused(traced_objs: List[TracedObject]) -> None:
    if len(traced_objs) > 0:

        def inner() -> None:
            with bpy.context.temp_override(object=traced_objs[0].obj):
                bpy.ops.object.material_slot_remove_unused()

        return with_selected_objects(traced_objs, inner)


def join_by_material(
    logger: Logger,
    traced_objs: List[TracedObject],
    extra_group: Callable[[TracedObject], A],
) -> List[TracedObject]:
    """Join objects which have matching materials. Input objects must have only
    one material each!

    extra_group
        Function to ensure objects which are of some different type do not get
        merged together. Useful to prevent merging far and near geom block
        geometry, for example.
    """
    by_material: Dict[Tuple[A, str], List[bpy.types.Object]] = dict()
    for traced_obj in traced_objs:
        obj = traced_obj.obj
        if not isinstance(obj.data, bpy.types.Mesh):
            logger.warn(f"Ignoring non mesh object {traced_obj.source_name()}")
            continue
        # We assume the materials are attached to the mesh, not the object. So
        # we just check it here and hope for the best.
        for mat_slot in obj.material_slots:
            if mat_slot.link != "DATA":
                raise errors.E0150(
                    object_name=traced_obj.source_name(), material_name=mat_slot.name
                )
        mesh = obj.data
        if len(mesh.materials) == 0:
            logger.warn(f"Ignoring mesh with no material {traced_obj.source_name()}")
            continue
        if len(mesh.materials) != 1:
            raise errors.RBRAddonBug(
                f"join_by_material encountered mesh with {len(mesh.materials)} "
                + f"materials: {obj.name}. "
                + "This is likely an addon bug, since the input objects to this "
                + "function should already be separated by material."
            )
        material = mesh.materials[0]
        if material is None:
            continue
        material = material.name
        a = extra_group(traced_obj)
        key = (a, material)
        if key in by_material:
            by_material[key].append(traced_obj)
        else:
            by_material[key] = [traced_obj]

    result = []
    for objs in by_material.values():
        joined = join_objects(objs)
        if joined is not None:
            result.append(joined)
    return result


def separate_by_material_single(
    traced_obj: TracedObject,
) -> List[TracedObject]:
    """Separate objects by material. Also cleans up materials so the only
    material is the active one.
    """

    if len(traced_obj.obj.material_slots) == 1:
        return [traced_obj]

    make_local([traced_obj])
    make_data_single_user(traced_obj)

    def inner() -> List[bpy.types.Object]:
        # Use global selection because it works better for objects which fail
        # separation due to only having one material.
        bpy.ops.mesh.separate(
            type="MATERIAL",
        )
        separated: List[bpy.types.Object] = list(bpy.context.selected_objects.copy())
        return separated

    sep_objs = with_selected_objects([traced_obj], inner)
    traced_sep = [TracedObject(parents=traced_obj.parents, obj=o) for o in sep_objs]
    material_slot_remove_unused(traced_sep)
    return traced_sep


def separate_by_material(
    traced_objs: List[TracedObject],
) -> List[TracedObject]:
    """Separate objects by material. Also cleans up materials so the only
    material is the active one.
    """

    # This operator adds the separated objects to the global selection

    def inner() -> List[bpy.types.Object]:
        # Use global selection because it works better for objects which fail
        # separation due to only having one material.
        bpy.ops.mesh.separate(
            type="MATERIAL",
        )
        separated: List[bpy.types.Object] = list(bpy.context.selected_objects.copy())
        return separated

    dupes = []
    for traced_obj in traced_objs:
        sep_objs = with_selected_objects([traced_obj], inner)
        traced_sep = [TracedObject(parents=traced_obj.parents, obj=o) for o in sep_objs]
        material_slot_remove_unused(traced_sep)
        dupes.extend(traced_sep)

    return dupes


def separate_by_loose_parts(
    traced_objs: List[TracedObject],
) -> List[TracedObject]:
    """Separate objects by loose parts."""

    # This operator adds the separated objects to the global selection

    def inner() -> List[bpy.types.Object]:
        # Use global selection because it works better for objects which fail
        # separation due to only having one material.
        bpy.ops.mesh.separate(
            type="LOOSE",
        )
        separated: List[bpy.types.Object] = list(bpy.context.selected_objects.copy())
        return separated

    dupes = []
    for traced_obj in traced_objs:
        sep_objs = with_selected_objects([traced_obj], inner)
        traced_sep = [TracedObject(parents=traced_obj.parents, obj=o) for o in sep_objs]
        dupes.extend(traced_sep)

    return dupes


def split_by_loop_triangle_count(
    traced_obj: TracedObject,
    loop_count: int,
) -> List[TracedObject]:
    """Split an object into sections containing no more than the given
    loop_count. This will also triangulate the object.
    """

    tris_count = loop_count // 3
    obj = traced_obj.obj

    def inner() -> List[bpy.types.Object]:
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            # Triangulate, uses selected faces
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.mesh.select_all(action="DESELECT")
            while len(obj.data.polygons) > tris_count:
                bpy.ops.object.mode_set(mode="OBJECT")
                # Must select faces in object mode
                for i in range(min(tris_count, len(obj.data.polygons))):
                    obj.data.polygons[i].select = True
                bpy.ops.object.mode_set(mode="EDIT")
                # Separate by selection only works in edit mode
                bpy.ops.mesh.separate(type="SELECTED")
            return bpy.context.selected_objects.copy()  # type: ignore
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")

    split_objs = with_selected_objects(
        [traced_obj], lambda: with_active_object(obj, inner)
    )
    return [TracedObject(traced_obj.parents, o) for o in split_objs]


def join_objects(
    traced_objs: List[TracedObject],
) -> Optional[TracedObject]:
    try:
        traced_obj = traced_objs[0]
        obj = traced_obj.obj
        if len(traced_objs) > 1:

            def inner() -> None:
                with bpy.context.temp_override(active_object=obj):
                    bpy.ops.object.join()

            with_selected_objects(traced_objs, inner)
        return TracedObject(unions([o.parents for o in traced_objs]), obj)
    except IndexError:
        return None


def convert_to_mesh(
    traced_objs: List[TracedObject],
) -> None:
    if len(traced_objs) == 0:
        return

    def inner() -> None:
        bpy.ops.object.convert(keep_original=False)

    with_selected_objects(
        traced_objs, lambda: with_active_object(traced_objs[0], inner)
    )


def copy_visual_geometry_to_meshes(
    traced_objs: List[TracedObject],
) -> List[TracedObject]:
    """Visual geometry to mesh, but without changing the originals."""
    if len(traced_objs) == 0:
        return []

    def inner() -> List[bpy.types.Object]:
        # This will convert everything to a mesh and set selected objects to
        # the clones
        bpy.ops.object.convert(
            keep_original=True,
        )
        return bpy.context.selected_objects.copy()  # type: ignore

    dupes = with_selected_objects(
        traced_objs, lambda: with_active_object(traced_objs[0], inner)
    )

    traced_dupes = []
    for traced_obj, dupe in zip(traced_objs, dupes):
        traced_dupes.append(
            TracedObject(
                parents=traced_obj.parents,
                obj=dupe,
            )
        )
    return traced_dupes


def apply_modifier(traced_obj: TracedObject, modifier: str) -> None:
    """Apply a single modifier of an object. Beware that order of modifier
    application is important, they should be applied top to bottom."""
    try:
        with bpy.context.temp_override(object=traced_obj.obj):
            bpy.ops.object.modifier_apply(modifier=modifier)
    except RuntimeError:
        # The warning will still be printed
        pass


def apply_modifiers(traced_obj: TracedObject) -> None:
    """Apply all modifiers for an object."""
    for mod in traced_obj.obj.modifiers:
        # Only apply when both render and viewport are switched off.
        if mod.show_render or mod.show_viewport:
            apply_modifier(traced_obj, mod.name)


def clear_parent_keep_transforms(traced_objs: List[TracedObject]) -> None:
    """Clear the parent relationship and keep the transformation."""

    def inner() -> None:
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")

    return with_selected_objects(traced_objs, inner)


def make_data_single_user(traced_obj: TracedObject) -> None:
    """Turn 'linked' objects into non linked objects."""
    if traced_obj.obj.data.users > 1:
        traced_obj.obj.data = traced_obj.obj.data.copy()


def make_local(traced_objs: List[TracedObject]) -> None:
    """Turn 'linked' mesh objects into non linked objects."""

    def inner() -> None:
        bpy.ops.object.make_local()

    return with_selected_objects(traced_objs, inner)


def duplicates_make_real(traced_obj: TracedObject) -> List[TracedObject]:
    """Make instances of an object real. Returns the real objects."""

    def inner() -> List[bpy.types.Object]:
        bpy.ops.object.duplicates_make_real(use_hierarchy=True)
        reals: List[bpy.types.Object] = bpy.context.selected_objects.copy()
        return [TracedObject(parents=traced_obj.parents, obj=obj) for obj in reals]

    return with_selected_objects([traced_obj], inner)


def prepare_objs(
    logger: Logger,
    traced_objs: List[TracedObject],
    normalise: Callable[[TracedObject], None],
    extra_group: Callable[[TracedObject], A],
) -> List[TracedObject]:
    """Given an input list of objects, turn them into real geometry and apply
    all transforms and modifiers. Then separate them out and join them by
    material, so each object has only one material (and each material has only
    one corresponding object).

    objs
        Input objects
    normalise
        Function to normalise object properties before separation and joining
    extra_group
        Function to return extra grouping information to prevent joining objects
        which are incompatible but share a material
    """
    # Previously we used copy_visual_geometry_to_meshes here, but it does not
    # perform well with thousands of small objects. This method works for
    # geometry nodes (barring blender bugs), particle instances, meshes with
    # many vertices, and thousands of small objects.
    logger.info(f"Copying {len(traced_objs)} objects")
    traced_dupes = duplicate_objects(traced_objs)
    logger.info(f"Applying modifiers on {len(traced_dupes)} objects")
    make_local(traced_dupes)
    for traced_obj in traced_dupes:
        make_data_single_user(traced_obj)
        apply_modifiers(traced_obj)
    traced_applied = traced_dupes
    logger.info(f"Applying transforms to {len(traced_applied)} objects")
    apply_transforms(traced_applied)
    clear_parent_keep_transforms(traced_applied)
    for traced_obj in traced_applied:
        ros: RBRObjectSettings = traced_obj.obj.rbr_object_settings
        ros.type = RBRObjectType.NONE.name
        normalise(traced_obj)
    logger.info(f"Separating {len(traced_applied)} objects by material")
    separated = separate_by_material(traced_applied)
    logger.info(f"Joining {len(separated)} objects by material")
    return join_by_material(logger, separated, extra_group)
