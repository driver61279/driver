from __future__ import annotations
import copy
from typing import List

import numpy as np

from rbr_track_formats.logger import Logger
from rbr_track_formats.common import (
    compute_bounding_box_from_positions,
)
from rbr_track_formats.lbs.geom_blocks import (
    RenderChunkDistance,
    TransformedRenderChunkData,
)
from rbr_track_formats import dtypes
from rbr_track_formats.lbs import WorldChunks

from rbr_track_formats.lbs.super_chunks import split_super_chunks
from rbr_track_addon.blender_ops import prepare_objs, TracedObject
from rbr_track_addon.object_settings.types import (
    RBRObjectSettings,
)
from rbr_track_addon.util import (
    get_uv_array,
    mesh_loop_triangles,
    mesh_vertices_to_loop_positions,
)

from .textures import RBRResolvedMaterial, RBRExportTextureOracle
from .. import vcol_bake
from ..util import (
    create_supers_with,
)

from .object_blocks import create_super_object_block


def create_super_chunk(
    logger: Logger,
    rbr_material: RBRResolvedMaterial,
    traced_obj: TracedObject,
) -> TransformedRenderChunkData:
    """Create a chunk which does not conform to chunk boundaries"""
    obj = traced_obj.obj

    rbr_object_settings: RBRObjectSettings = obj.rbr_object_settings
    chunk_distance = RenderChunkDistance[rbr_object_settings.geom_blocks_distance]

    mesh = obj.data
    mesh.calc_loop_triangles()

    diffuse_1_uv = None
    diffuse_2_uv = None
    specular_uv = None
    rbr_material_diffuse_2 = None
    if rbr_material.render_type.has_diffuse_1():
        diffuse_1_uv = get_uv_array(
            mesh=mesh,
            layer=rbr_material.diffuse_1_uv,
            invert_v=True,
            material_name=rbr_material.name,
        )

        if rbr_material.render_type.has_diffuse_2():
            diffuse_2_uv = get_uv_array(
                mesh=mesh,
                layer=rbr_material.diffuse_2_uv,
                invert_v=True,
                material_name=rbr_material.name,
            )
            rbr_material_diffuse_2 = rbr_material.diffuse_2
        else:
            rbr_material_diffuse_2 = rbr_material.diffuse_1

        if rbr_material.render_type.has_specular():
            specular_uv = get_uv_array(
                mesh=mesh,
                layer=rbr_material.specular_uv,
                invert_v=True,
                material_name=rbr_material.name,
            )

    if diffuse_1_uv is None:
        vertices = np.empty(len(mesh.loops), dtype=dtypes.position_color)
    elif specular_uv is None:
        # Always use the double texture buffer, even for single texture
        # case. The single texture shaders do not work.
        vertices = np.empty(len(mesh.loops), dtype=dtypes.double_texture)
    else:
        vertices = np.empty(len(mesh.loops), dtype=dtypes.double_texture_specular)

    (vertex_indices, position) = mesh_vertices_to_loop_positions(
        mesh, dtype=dtypes.vector3_lh
    )
    bounding_box = compute_bounding_box_from_positions(position)
    vertices["position"] = position
    vertices["color"] = vcol_bake.bake(logger, mesh)

    if diffuse_1_uv is not None:
        vertices["diffuse_1_uv"] = diffuse_1_uv
        vertices["diffuse_2_uv"] = diffuse_1_uv
        if diffuse_2_uv is not None:
            vertices["diffuse_2_uv"] = diffuse_2_uv

        if specular_uv is not None:
            vertex_normals = np.zeros(len(mesh.vertices) * 3)
            mesh.vertices.foreach_get("normal", vertex_normals)
            vertex_normals = vertex_normals.reshape((-1, 3))
            loop_normals = vertex_normals[vertex_indices]
            (n_x, n_y, n_z) = np.hsplit(loop_normals, 3)
            normal = np.empty(len(loop_normals), dtype=dtypes.vector3_lh)
            normal["x"] = n_x.flatten()
            normal["y"] = n_y.flatten()
            normal["z"] = n_z.flatten()
            vertices["normal"] = normal
            vertices["specular_uv"] = specular_uv
            vertices["specular_strength"] = vcol_bake.bake_spec_strength(logger, mesh)

    #    loop_color = mesh.vertex_colors.get(rbr_material.specular_strength)
    #    if loop_color is None:
    #        specular_strength = 1
    #    else:
    #        vc_specular_strength = loop_color.data[loop_index].color
    #        specular_strength = vc_specular_strength[0]
    #    uv_loop_layer = uv_loop_layers.get(rbr_material.specular_uv)
    #    if uv_loop_layer is None:
    #        uv_loop_layer = uv_loop_layers.active
    #    uv_specular = uv_loop_layer.data[loop_index].uv
    #    normal = Vector3(
    #        x=v.normal[0],
    #        y=v.normal[2],
    #        z=v.normal[1],
    #    )

    triangles = mesh_loop_triangles(mesh)

    # Fix UV velocity for single texture case. We rewrite the single textures
    # as double textures, so we need to rewrite the second texture velocity
    # too.
    uv_velocity = copy.deepcopy(rbr_material.uv_velocity)
    if (
        uv_velocity is not None
        and rbr_material.render_type.has_diffuse_1()
        and not rbr_material.render_type.has_diffuse_2()
    ):
        uv_velocity.diffuse_2 = uv_velocity.diffuse_1

    return TransformedRenderChunkData(
        type=rbr_material.render_type.to_double_texture(),
        vertices=vertices,
        triangles=triangles,
        bounding_box=bounding_box,
        texture_index_1=rbr_material.diffuse_1,
        texture_index_2=rbr_material_diffuse_2,
        specular_texture_index=rbr_material.specular,
        shadow_texture_index=None,  # TODO
        chunk_distance=chunk_distance,
        uv_velocity=uv_velocity,
    )


def export_world_chunks(
    export_texture_oracle: RBRExportTextureOracle,
    logger: Logger,
    chunk_size: float,
    geom_block_objects: List[TracedObject],
    object_block_objects: List[TracedObject],
) -> WorldChunks:
    def gb_group(traced_obj: TracedObject) -> str:
        ros: RBRObjectSettings = traced_obj.obj.rbr_object_settings
        return ros.geom_blocks_distance  # type: ignore

    gb_dupes = logger.section(
        "Preparing geom block objects",
        lambda: prepare_objs(
            logger=logger,
            traced_objs=geom_block_objects,
            normalise=lambda _: None,
            extra_group=gb_group,
        ),
    )

    def group_object(traced_obj: TracedObject) -> str:
        ros: RBRObjectSettings = traced_obj.obj.rbr_object_settings
        return ros.object_blocks_detail  # type: ignore

    ob_dupes = logger.section(
        "Preparing object block objects",
        lambda: prepare_objs(
            logger=logger,
            traced_objs=object_block_objects,
            normalise=lambda _: None,
            extra_group=group_object,
        ),
    )
    super_chunks = logger.section(
        "Creating geom block super chunks",
        lambda: create_supers_with(
            lambda m, o: create_super_chunk(logger, m, o),
            export_texture_oracle,
            gb_dupes,
        ),
    )
    super_object_blocks = logger.section(
        "Creating object block super chunks",
        lambda: create_supers_with(
            lambda m, o: create_super_object_block(logger, m, o),
            export_texture_oracle,
            ob_dupes,
        ),
    )
    chunks = split_super_chunks(
        logger,
        chunk_size,
        super_chunks,
        super_object_blocks,
    )
    return WorldChunks(
        beckmann_glossiness=12,  # TODO
        chunks=chunks,
    )
