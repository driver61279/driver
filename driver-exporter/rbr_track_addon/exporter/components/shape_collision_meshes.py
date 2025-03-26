from __future__ import annotations
from typing import Dict, List, Optional, Union

from rbr_track_formats import errors
from rbr_track_formats.common import Vector3, AaBbBoundingBox
from rbr_track_formats.mat import MaterialID
from rbr_track_formats.trk.shape_collision_meshes import (
    BoundingSphere,
    FaceData,
    ObjectData,
    Quaternion,
    ShapeCollisionMesh,
    ShapeCollisionMeshes,
    StaticMesh,
)

import rbr_track_addon.blender_ops as ops
from rbr_track_addon.blender_ops import TracedObject
from rbr_track_formats.logger import Logger
from rbr_track_addon.object_settings.types import RBRObjectSettings, check_scale_is_1

from ..util import KeyGen


def make_shape_collision_mesh(
    keygen: KeyGen,
    traced_objs: List[TracedObject],
) -> List[ShapeCollisionMesh]:
    """Given a mesh marked as a shape collision mesh and all of the objects
    which use it, create the exportable format. This returns a list because
    mesh materials are stored in the objects, so one mesh may lead to multiple
    shape collision meshes.
    """
    mesh = traced_objs[0].obj.data
    mesh.calc_loop_triangles()
    if not ops.mesh_is_convex(traced_objs[0]):
        raise errors.E0156(object_name=traced_objs[0].source_name())
    vertices = [Vector3.from_tuple(v.co.to_tuple()) for v in mesh.vertices]
    faces = []
    for loop_triangle in mesh.loop_triangles:
        faces.append(
            FaceData(
                index_a=loop_triangle.vertices[0],
                index_b=loop_triangle.vertices[1],
                index_c=loop_triangle.vertices[2],
            )
        )
    objects_by_material: Dict[MaterialID, List[ObjectData]] = dict()
    for traced_obj in traced_objs:
        # Try to find the soft volume
        soft_volume: Optional[Union[BoundingSphere, AaBbBoundingBox]] = None
        obj = traced_obj.obj
        for child in obj.children:
            if child.data is not None:
                continue
            if child.empty_display_type == "SPHERE":
                s_max = max(child.scale.x, child.scale.y, child.scale.z)
                soft_volume = BoundingSphere(
                    position=Vector3.from_tuple(child.location.to_tuple()),
                    radius=s_max * child.empty_display_size,
                )
                break
            elif child.empty_display_type == "CUBE":
                soft_volume = AaBbBoundingBox(
                    position=Vector3.from_tuple(child.location.to_tuple()),
                    size=Vector3.from_tuple(child.scale.to_tuple())
                    .scale(child.empty_display_size)
                    .flip_handedness(),
                )
                break

        key = keygen.new_key()
        # Get the world position
        (position, quaternion, scale) = obj.matrix_world.decompose()
        if not check_scale_is_1(obj):
            raise errors.E0153(
                object_name=traced_obj.source_name(),
                scale=str(scale.to_tuple()),
            )
        object_data = ObjectData(
            key=key,
            position=Vector3.from_tuple(position.to_tuple()),
            rotation=Quaternion(
                x=quaternion.x,
                y=quaternion.y,
                z=quaternion.z,
                w=quaternion.w,
            ),
            scale=Vector3(1, 1, 1),
        )
        object_settings: RBRObjectSettings = obj.rbr_object_settings
        mat = MaterialID[object_settings.shape_collision_mesh_material]
        if mat in objects_by_material:
            objects_by_material[mat].append(object_data)
        else:
            objects_by_material[mat] = [object_data]
    shape_colmeshes = []
    for material, objects in objects_by_material.items():
        scm = ShapeCollisionMesh(
            # Must keep the user defined _short name_ i.e. no library
            name=mesh.name,
            mesh_type=StaticMesh(
                material=material,
                soft_volume=soft_volume,
            ),
            vertices=vertices,
            faces=faces,
            objects=objects,
        )
        shape_colmeshes.append(scm)
    return shape_colmeshes


def export_shape_collision_meshes(
    keygen: KeyGen,
    logger: Logger,
    traced_objs: List[TracedObject],
) -> ShapeCollisionMeshes:
    # Objects indexed by mesh _full name_ including library
    blender_meshes: Dict[str, List[TracedObject]] = dict()
    logger.info(f"Shape colmesh count: {len(traced_objs)}")
    for traced_obj in traced_objs:
        blender_mesh = traced_obj.obj.data
        if blender_mesh.name_full in blender_meshes:
            blender_meshes[blender_mesh.name_full].append(traced_obj)
        else:
            blender_meshes[blender_mesh.name_full] = [traced_obj]
    shape_meshes = []
    for full_mesh_name, traced_objs in blender_meshes.items():
        logger.info(f"Handling mesh {full_mesh_name}, object count: {len(traced_objs)}")
        shape_meshes.extend(
            make_shape_collision_mesh(
                keygen=keygen,
                traced_objs=traced_objs,
            )
        )
    return ShapeCollisionMeshes(
        meshes=shape_meshes,
    )
