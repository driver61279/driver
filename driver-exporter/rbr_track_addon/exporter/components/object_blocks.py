import numpy as np

from rbr_track_formats import dtypes, errors
from rbr_track_formats.logger import Logger
from rbr_track_formats.common import (
    compute_bounding_box_from_positions,
)
from rbr_track_formats.lbs.common import RenderStateFlags
from rbr_track_formats.lbs.object_blocks import (
    ObjectBlock,
    ObjectBlockLOD,
)

from rbr_track_addon.blender_ops import TracedObject
from rbr_track_addon.object_settings.types import (
    ObjectBlocksDetail,
    RBRObjectSettings,
)
from rbr_track_addon.util import (
    get_uv_array,
    mesh_loop_triangles,
    mesh_vertices_to_loop_positions,
)

from .textures import RBRResolvedMaterial
from .. import vcol_bake


def create_super_object_block(
    logger: Logger,
    rbr_material: RBRResolvedMaterial,
    traced_obj: TracedObject,
) -> ObjectBlock:
    """Create an object block which does not conform to chunk boundaries"""

    # TODO I'm not sure this is correct, but users probably shouldn't be trying
    # to export opaque objects as object blocks, so it'll do for now.
    if not rbr_material.transparent:
        raise errors.E0128(
            object_name=traced_obj.source_name(),
            material_name=rbr_material.name,
        )

    rbr_object_settings: RBRObjectSettings = traced_obj.obj.rbr_object_settings

    mesh = traced_obj.obj.data
    mesh.calc_loop_triangles()

    # Others are not supported.
    vertices = np.zeros(len(mesh.loops), dtype=dtypes.single_texture_sway)

    (_, position) = mesh_vertices_to_loop_positions(mesh, dtype=dtypes.vector3_lh)
    bounding_box = compute_bounding_box_from_positions(position)
    vertices["position"] = position
    vertices["color"] = vcol_bake.bake(logger, mesh)

    if not rbr_material.render_type.has_diffuse_1():
        raise errors.E0129(
            object_name=traced_obj.source_name(),
            material_name=rbr_material.name,
        )
    if rbr_material.render_type.has_diffuse_2():
        raise errors.E0129(
            object_name=traced_obj.source_name(),
            material_name=rbr_material.name,
        )
    diffuse_1_uv = get_uv_array(
        mesh=mesh,
        layer=rbr_material.diffuse_1_uv,
        invert_v=True,
        material_name=rbr_material.name,
    )
    if diffuse_1_uv is None:
        raise errors.RBRAddonBug("Missing diffuse_1_uv in create_super_object_block")
    vertices["diffuse_1_uv"] = diffuse_1_uv

    vertices["sway"] = vcol_bake.bake_sway(logger, mesh)

    # Define the level of detail settings and the buffers
    all_triangles = mesh_loop_triangles(mesh)
    detail = ObjectBlocksDetail[rbr_object_settings.object_blocks_detail]
    if detail is ObjectBlocksDetail.NEAR:
        lod = ObjectBlockLOD.NEAR_GEOMETRY_FROM_MAIN_BUFFER
        main_buffer = all_triangles
        far_buffer = None
    elif detail is ObjectBlocksDetail.FAR:
        lod = ObjectBlockLOD.FAR_GEOMETRY_FROM_MAIN_BUFFER
        main_buffer = all_triangles
        far_buffer = None
    elif detail is ObjectBlocksDetail.BOTH:
        lod = ObjectBlockLOD.FAR_GEOMETRY_FROM_FAR_BUFFER
        main_buffer = all_triangles
        far_buffer = all_triangles
    else:
        raise errors.RBRAddonBug(f"Unhandled case for detail: {detail.name}")

    render_state_flags = RenderStateFlags(0)
    if not rbr_material.use_backface_culling:
        render_state_flags |= RenderStateFlags.NO_CULLING

    return ObjectBlock(
        render_state_flags=render_state_flags,
        diffuse_texture_index_1=rbr_material.diffuse_1,
        diffuse_texture_index_2=None,  # Game crashes when loading.
        main_buffer=main_buffer,
        lod=lod,
        far_buffer=far_buffer,
        vertices=vertices,
        bounding_box=bounding_box,
    )
