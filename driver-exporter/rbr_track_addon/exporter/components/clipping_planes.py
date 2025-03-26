from typing import List, Optional

import numpy as np
from numpy.lib.recfunctions import unstructured_to_structured

from rbr_track_formats.lbs.clipping_planes import ClippingPlanes
from rbr_track_formats import dtypes

from rbr_track_addon.blender_ops import (
    apply_transforms,
    copy_visual_geometry_to_meshes,
    join_objects,
    TracedObject,
)
from rbr_track_formats.logger import Logger
from rbr_track_addon.util import mesh_vertices


def export_clipping_planes(
    logger: Logger,
    traced_objs: List[TracedObject],
) -> Optional[ClippingPlanes]:
    logger.info("Copying geometry")
    traced_dupes = copy_visual_geometry_to_meshes(traced_objs)
    logger.info("Applying transforms")
    apply_transforms(traced_dupes)
    logger.info("Joining objects")
    obj = join_objects(traced_dupes)
    if obj is None:
        return None
    mesh = obj.obj.data

    mesh.calc_loop_triangles()
    triangle_materials = np.zeros(len(mesh.loop_triangles), dtype=int)
    mesh.loop_triangles.foreach_get("material_index", triangle_materials)

    if len(mesh.materials) > 0:
        culled_materials = np.zeros(len(mesh.materials), dtype=bool)
        mesh.materials.foreach_get("use_backface_culling", culled_materials)
    else:
        culled_materials = np.zeros(1, dtype=bool)

    triangles_indices = np.zeros(len(mesh.loop_triangles) * 3, dtype=int)
    mesh.loop_triangles.foreach_get("vertices", triangles_indices)
    triangles_indices = np.flip(triangles_indices.reshape((-1, 3)), axis=1)
    triangles_indices = unstructured_to_structured(
        triangles_indices, dtype=dtypes.triangle_indices
    )

    culled_triangles = culled_materials[triangle_materials]
    directional_planes = triangles_indices[culled_triangles]
    omnidirectional_planes = triangles_indices[np.logical_not(culled_triangles)]

    vertices = mesh_vertices(
        mesh=mesh,
        dtype=dtypes.vector3_lh,
    )

    return ClippingPlanes(
        vertices=vertices,
        directional_planes=directional_planes,
        omnidirectional_planes=omnidirectional_planes,
    )
