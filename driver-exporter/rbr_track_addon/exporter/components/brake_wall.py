from typing import List, Optional

import bpy  # type: ignore
import bmesh  # type: ignore

import rbr_track_formats as formats
from rbr_track_formats import errors
from rbr_track_formats.col.brake_wall import (
    BrakeWall,
    BrakeWallPointPair,
    BrakeWallRoot,
)

from rbr_track_addon.blender_ops import (
    apply_transforms,
    copy_visual_geometry_to_meshes,
    TracedObject,
)
from rbr_track_addon.object_settings.types import RBRObjectSettings
from rbr_track_formats.logger import Logger


def winding_direction(points: List[formats.common.Vector2]) -> float:
    """
    Compute the winding direction of a polygon. Negative results are
    anticlockwise.
    Taken from https://stackoverflow.com/a/1165943.
    """
    result = 0.0
    for i in range(len(points)):
        p1 = points[i]
        if i == len(points) - 1:
            p2 = points[0]
        else:
            p2 = points[i + 1]
        result += (p2.x - p1.x) * (p2.y + p1.y)
    return result


def export_brake_wall(
    logger: Logger,
    traced_objs: List[TracedObject],
) -> Optional[BrakeWall]:
    """
    Take the first brake wall object and convert it to the exportable format.
    """
    try:
        ob = traced_objs[0]
        if len(traced_objs) > 1:
            logger.warn(f"More than one brake wall object! Using {ob.source_name()}.")
    except IndexError:
        logger.warn("No brake wall object found")
        return None
    dupes = copy_visual_geometry_to_meshes([ob])
    apply_transforms(dupes)
    return export_brake_wall_inner(logger, dupes[0])


def export_brake_wall_inner(
    logger: Logger,
    traced_ob: TracedObject,
) -> Optional[BrakeWall]:
    ob = traced_ob.obj
    mesh = ob.data

    object_settings: RBRObjectSettings = ob.rbr_object_settings
    inner_layer = object_settings.brake_wall_inner_group
    outer_layer = object_settings.brake_wall_outer_group
    respawn_layer = object_settings.brake_wall_respawn_group

    inner_group = ob.vertex_groups.get(inner_layer)
    if inner_group is None:
        raise errors.E0002(layer_type="inner", missing_layer_name=inner_layer)

    outer_group = ob.vertex_groups.get(outer_layer)
    if outer_group is None:
        raise errors.E0002(layer_type="outer", missing_layer_name=outer_layer)

    respawn_group: Optional[bpy.types.VertexGroup] = ob.vertex_groups.get(respawn_layer)
    if respawn_group is None and respawn_layer != "":
        raise errors.E0002(layer_type="respawn", missing_layer_name=respawn_layer)

    def walk(bm: bmesh.types.BMesh) -> List[BrakeWallPointPair]:
        inner_indices = set()
        outer_indices = set()
        respawn_indices = set()
        # Partition the vertices into inner and outer groups
        for v in mesh.vertices:
            groups = [g.group for g in v.groups]
            is_inner = inner_group.index in groups
            is_outer = outer_group.index in groups
            if is_inner and not is_outer:
                inner_indices.add(v.index)
            elif is_outer and not is_inner:
                outer_indices.add(v.index)
            else:
                raise errors.E0003(position=list(v.co))
            # Add to the respawn group too if necessary
            if respawn_group is not None:
                if respawn_group.index in groups:
                    respawn_indices.add(v.index)
        if len(inner_indices) == 0:
            raise errors.E0004()
        if len(inner_indices) != len(outer_indices):
            raise errors.E0005(
                num_inner=len(inner_indices), num_outer=len(outer_indices)
            )
        # Walk the inner edge of the mesh and build a list of brake wall pairs.
        visited = set()
        result = []
        inner_index = list(inner_indices)[0]
        while True:
            edges = bm.verts[inner_index].link_edges
            inner_pos = list(bm.verts[inner_index].co)
            if len(edges) != 3:
                raise errors.E0006(position=inner_pos)
            inner_edges = set()
            outer_index = None
            for edge in edges:
                indices = [v.index for v in edge.verts if v.index != inner_index]
                if len(indices) != 1:
                    raise errors.E0006(position=inner_pos)
                if indices[0] in inner_indices:
                    if indices[0] not in visited:
                        inner_edges.add(indices[0])
                elif indices[0] in outer_indices:
                    # There should only be one outer vertex connected to an
                    # inner vertex
                    if outer_index is not None:
                        raise errors.E0006(position=inner_pos)
                    outer_index = indices[0]
                else:
                    raise errors.RBRAddonBug("brake wall export")
            if outer_index is None:
                raise errors.E0006(position=inner_pos)
            visited.add(inner_index)
            result.append(
                BrakeWallPointPair(
                    inner=formats.common.Vector2(
                        bm.verts[inner_index].co.x, bm.verts[inner_index].co.y
                    ),
                    outer=formats.common.Vector2(
                        bm.verts[outer_index].co.x, bm.verts[outer_index].co.y
                    ),
                    auto_respawn=(
                        inner_index in respawn_indices or outer_index in respawn_indices
                    ),
                )
            )
            if len(inner_edges) == 0:
                # We've already visited all of the possible links, so we're done
                return result
            else:
                inner_index = inner_edges.pop()

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
        bm.verts.ensure_lookup_table()
        point_pairs = walk(bm)
        direction = winding_direction([p.inner for p in point_pairs])
        # Add initial point to the end to match the default stages
        point_pairs.append(point_pairs[0])
        if direction < 0:  # anticlockwise
            point_pairs.reverse()
        return BrakeWall(
            point_pairs=point_pairs,
            root=BrakeWallRoot.generate_tree(point_pairs),
        )
    finally:
        bm.free()
