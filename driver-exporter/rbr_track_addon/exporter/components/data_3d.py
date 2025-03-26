from typing import List, Optional, Tuple

import numpy as np
from numpy.lib.recfunctions import (
    unstructured_to_structured,
    structured_to_unstructured,
)

from rbr_track_formats.common import NumpyArray
from rbr_track_formats import dtypes, errors
from rbr_track_formats.lbs.common import ObjectData3D, RenderStateFlags

from rbr_track_addon.blender_ops import TracedObject
from rbr_track_formats.logger import Logger
from rbr_track_addon.util import (
    mesh_loop_triangles,
    mesh_vertices_to_loop_positions,
    get_uv_array,
)
from rbr_track_formats.lbs.super_chunks import (
    split_array_by,
)

from .textures import RBRResolvedMaterial
from .. import vcol_bake


def split_data_along_axis(
    axis_index: int,
    midpoint: float,
    triangle_centres: NumpyArray,
    data: ObjectData3D,
) -> Tuple[Optional[ObjectData3D], Optional[ObjectData3D]]:
    tri_axis_centres = triangle_centres[:, axis_index]
    (left_tris, right_tris) = split_array_by(
        data.triangles, tri_axis_centres < midpoint
    )

    def process_side(tris: NumpyArray) -> Optional[ObjectData3D]:
        (vertices, flat_indices) = np.unique(
            data.vertices[tris],
            return_inverse=True,
        )
        # Reshape indices into triangle triplets
        triangles = flat_indices.reshape((-1, 3))

        return ObjectData3D(
            render_state_flags=data.render_state_flags,
            diffuse_texture_index_1=data.diffuse_texture_index_1,
            diffuse_texture_index_2=data.diffuse_texture_index_2,
            specular_texture_index=data.specular_texture_index,
            uv_velocity=data.uv_velocity,
            triangles=triangles,
            vertices=vertices,
        )

    return (process_side(left_tris), process_side(right_tris))


def recursive_split(
    logger: Logger,
    data: ObjectData3D,
    path: str = "R",
) -> List[ObjectData3D]:
    """Recursively split the given data by the longest axis until the vertices
    fit in the triangle index buffers.
    """
    if len(data.vertices) == 0:
        raise errors.RBRAddonBug("Missing vertices in recursive_split")

    xyz = structured_to_unstructured(data.vertices["position"])
    abc = data.triangles
    # Create a 3D array:
    # [ [ [x y z] [x y z] [x y z] ]
    # , [ [x y z] [x y z] [x y z] ]
    # ... one for each triangle
    # ]
    triangle_verts = np.take(xyz, abc, axis=0)
    # Collapse it to a 2D array of average position (triangle centre)
    # [ [x y z]
    # , [x y z]
    # ... one for each triangle
    # ]
    triangle_centres = np.average(triangle_verts, axis=1)

    logger.info(
        f"Split level {len(path)} path {path} with {len(triangle_centres)} triangles",
        end="\r",
    )

    # We previously unique'd the vertices so this should give an accurate
    # reading on whether we need to split the block further.
    VERT_LIMIT = 2**16
    exceeded_limit = len(data.vertices) > VERT_LIMIT

    # Find the longest axis
    maxi = np.amax(triangle_centres, axis=0)
    mini = np.amin(triangle_centres, axis=0)
    span = maxi - mini
    longest_axis = np.amax(span)
    axis_arr = np.where(span == longest_axis)
    longest_axis_index = axis_arr[0][0]

    if exceeded_limit:
        midpoint = np.average(triangle_centres, axis=0)[longest_axis_index]
        # Split the geometry along the longest axis
        (left_data, right_data) = split_data_along_axis(
            axis_index=longest_axis_index,
            midpoint=midpoint,
            triangle_centres=triangle_centres,
            data=data,
        )
        result = []
        if left_data is not None:
            result.extend(
                recursive_split(
                    logger=logger,
                    data=left_data,
                    path=path + "L",
                )
            )
        if right_data is not None:
            result.extend(
                recursive_split(
                    logger=logger,
                    data=right_data,
                    path=path + "R",
                )
            )
        return result
    else:
        return [data]


def create_super_data3d(
    logger: Logger,
    rbr_material: RBRResolvedMaterial,
    traced_obj: TracedObject,
    supports_specular: bool,
    supports_untextured: bool,
) -> ObjectData3D:
    """Create object data which does not conform to vertex count limits"""
    obj = traced_obj.obj

    mesh = obj.data
    mesh.calc_loop_triangles()

    has_specular = supports_specular and rbr_material.specular is not None

    if rbr_material.diffuse_1 is not None:
        if rbr_material.diffuse_2 is not None:
            if has_specular:
                vertex_dtype = dtypes.double_texture_specular
            else:
                vertex_dtype = dtypes.double_texture
        else:
            if has_specular:
                vertex_dtype = dtypes.single_texture_specular
            else:
                vertex_dtype = dtypes.single_texture
    else:
        if supports_untextured:
            vertex_dtype = dtypes.position_color
        else:
            raise errors.E0127(
                object_name=traced_obj.source_name(),
                material_name=rbr_material.name,
            )

    vertices = np.zeros(len(mesh.loops), dtype=vertex_dtype)

    (_, position) = mesh_vertices_to_loop_positions(mesh, dtype=dtypes.vector3_lh)
    vertices["position"] = position
    vertices["color"] = vcol_bake.bake(logger, mesh)

    if rbr_material.render_type.has_diffuse_1():
        diffuse_1_uv = get_uv_array(
            mesh=mesh,
            layer=rbr_material.diffuse_1_uv,
            invert_v=True,
            material_name=rbr_material.name,
        )
        if diffuse_1_uv is None:
            raise errors.RBRAddonBug("Missing diffuse_1_uv")
        vertices["diffuse_1_uv"] = diffuse_1_uv

    if rbr_material.render_type.has_diffuse_2():
        diffuse_2_uv = get_uv_array(
            mesh=mesh,
            layer=rbr_material.diffuse_2_uv,
            invert_v=True,
            material_name=rbr_material.name,
        )
        if diffuse_2_uv is None:
            raise errors.RBRAddonBug("Missing diffuse_2_uv")
        vertices["diffuse_2_uv"] = diffuse_2_uv

    if has_specular:
        specular_uv = get_uv_array(
            mesh=mesh,
            layer=rbr_material.specular_uv,
            invert_v=True,
            material_name=rbr_material.name,
        )
        if specular_uv is None:
            raise errors.RBRAddonBug("Missing specular_uv")
        vertices["specular_uv"] = specular_uv

    # Define the level of detail settings and the buffers
    triangles = mesh_loop_triangles(mesh)

    render_state_flags = RenderStateFlags(0)
    if not rbr_material.use_backface_culling:
        render_state_flags |= RenderStateFlags.NO_CULLING

    return ObjectData3D(
        render_state_flags=render_state_flags,
        diffuse_texture_index_1=rbr_material.diffuse_1,
        diffuse_texture_index_2=rbr_material.diffuse_2,
        specular_texture_index=rbr_material.specular if supports_specular else None,
        uv_velocity=rbr_material.uv_velocity,
        triangles=triangles,
        vertices=vertices,
    )


def fixup_data_triangles_dtype(
    chunk: ObjectData3D,
) -> ObjectData3D:
    """Change unstructured triangles to the triangle_indices dtype for export"""
    chunk.triangles = unstructured_to_structured(
        np.flip(chunk.triangles, axis=1),
        dtype=dtypes.triangle_indices,
    )
    return chunk
