from typing import List

import bpy  # type: ignore
import bmesh  # type: ignore

from rbr_track_formats.common import AaBbBoundingBox, Vector3
from rbr_track_formats.fnc import FNC, FenceTexture, FenceData, FencePost, BGRAColor

from rbr_track_formats.logger import Logger
from rbr_track_addon.blender_ops import TracedObject
import rbr_track_addon.blender_ops as ops
from rbr_track_addon.object_settings.types import RBRObjectSettings, RBRObjectType
from rbr_track_addon.object_settings.fences import (
    FenceKind,
    FencePoleNetTexture,
    FencePoleTapeTexture,
    FenceTileNetTexture,
    FenceTileTapeTexture,
)


def export_fnc(logger: Logger, traced_objs: List[TracedObject]) -> FNC:
    dupes = ops.duplicate_objects(traced_objs)
    ops.make_local(dupes)
    for traced_obj in dupes:
        ops.make_data_single_user(traced_obj)
        ops.apply_modifiers(traced_obj)
    ops.apply_transforms(dupes)
    ops.clear_parent_keep_transforms(dupes)
    sep = ops.separate_by_loose_parts(dupes)
    textures: List[FenceTexture] = []
    fences = []
    for dupe in sep:
        obj = dupe.obj
        # Pull info from object settings
        obj_settings: RBRObjectSettings = obj.rbr_object_settings
        obj_settings.type = RBRObjectType.NONE.name
        fence_kind = FenceKind[obj_settings.fence_kind]
        fence_pole_net_texture = FencePoleNetTexture[
            obj_settings.fence_pole_net_texture
        ]
        fence_pole_tape_texture = FencePoleTapeTexture[
            obj_settings.fence_pole_tape_texture
        ]
        fence_tile_net_texture = FenceTileNetTexture[
            obj_settings.fence_tile_net_texture
        ]
        fence_tile_tape_texture = FenceTileTapeTexture[
            obj_settings.fence_tile_tape_texture
        ]
        fence_is_long = obj_settings.fence_is_long
        fence_shading_layer = obj_settings.fence_shading
        # Resolve to RBR style data
        # Poles
        pole_type = fence_kind.to_fence_pole_type(fence_pole_net_texture)
        if fence_kind is FenceKind.BARBED_WIRE:
            pole_texture = FenceTexture.POLE_BARBED
        elif fence_kind is FenceKind.NET:
            pole_texture = fence_pole_net_texture.to_fence_texture()
        elif fence_kind is FenceKind.TAPE:
            pole_texture = fence_pole_tape_texture.to_fence_texture()
        # Tiles
        tile_type = fence_kind.to_fence_tile_type(fence_is_long)
        if fence_kind is FenceKind.BARBED_WIRE:
            tile_texture = FenceTexture.TILE_BARBED
        elif fence_kind is FenceKind.NET:
            tile_texture = fence_tile_net_texture.to_fence_texture()
        elif fence_kind is FenceKind.TAPE:
            tile_texture = fence_tile_tape_texture.to_fence_texture()
        # Pole textures
        for i, tex in enumerate(textures):
            if tex == pole_texture:
                pole_texture_index = i
                break
        else:
            pole_texture_index = len(textures)
            textures.append(pole_texture)
        # Tile textures
        for i, tex in enumerate(textures):
            if tex == tile_texture:
                tile_texture_index = i
                break
        else:
            tile_texture_index = len(textures)
            textures.append(tile_texture)
        # Get the fence post data
        mesh = obj.data
        if not isinstance(mesh, bpy.types.Mesh):
            logger.warn(f"Skipping non-mesh object '{dupe.source_name()}'")
            continue
        bm = bmesh.new()
        bm.from_mesh(mesh)
        # Get shading colour
        shading_layer = bm.verts.layers.color.get(fence_shading_layer)
        if shading_layer is None and fence_shading_layer != "":
            logger.warn(
                f"Shading layer for fence '{dupe.source_name()}' could not be found, it must be a 'Vertex Byte Color' attribute"
            )
        # Find a vertex with only one edge
        for vert in bm.verts:
            if len(vert.link_edges) == 1:
                first_vert = vert
                break
        else:
            logger.warn(
                f"Couldn't find start of fence for object '{dupe.source_name()}' (is the mesh a loop?)"
            )
            continue
        # Walk along the edge
        seen_edges = set()
        vertices = [first_vert]
        vert = first_vert
        while vert is not None:
            # Find the unseen edge. If we can't find one then we've reached the end.
            for edge in vert.link_edges:
                if edge not in seen_edges:
                    next_edge = edge
                    break
            else:
                break
            seen_edges.add(next_edge)
            # Walk along the edge to the next vertex.
            vert = next_edge.other_vert(vert)
            if vert is not None:
                vertices.append(vert)
        # Export sections
        fence_posts = []
        for i, vert in enumerate(vertices):
            position = Vector3.from_tuple(vert.co[0:3]).flip_handedness()
            bounding_box = AaBbBoundingBox(
                position=position,
                size=Vector3(0.1, 1.6, 0.1),
            )
            if shading_layer is not None:
                c = vert[shading_layer]

                def f(x: float) -> int:
                    return round(x * 255)

                color = BGRAColor(r=f(c[0]), g=f(c[1]), b=f(c[2]), a=f(c[3]))
            else:
                color = BGRAColor(r=255, g=255, b=255, a=255)
            try:
                next_pos = Vector3.from_tuple(vertices[i + 1].co[0:3]).flip_handedness()
                next_bb = AaBbBoundingBox(
                    position=next_pos,
                    size=Vector3(0.1, 1.6, 0.1),
                )
                bounding_box = bounding_box.union(next_bb)
            except IndexError:
                pass
            fence_posts.append(
                FencePost(
                    position=position,
                    bounding_box=bounding_box,
                    color=color,
                )
            )
        m_bounding_box = AaBbBoundingBox.unions([fp.bounding_box for fp in fence_posts])
        if m_bounding_box is not None:
            fences.append(
                FenceData(
                    tile_type=tile_type,
                    pole_type=pole_type,
                    tile_texture_index=tile_texture_index,
                    pole_texture_index=pole_texture_index,
                    bounding_box=m_bounding_box,
                    fence_posts=fence_posts,
                )
            )

    return FNC(
        fences=fences,
        textures=textures,
    )
