from __future__ import annotations
from typing import Dict, List, Tuple

import bpy  # type: ignore

from rbr_track_formats import errors
from rbr_track_formats.common import (
    Key,
    Vector3,
    Matrix4x4,
)
from rbr_track_formats.lbs.common import ObjectData3D
from rbr_track_formats.lbs.interactive_objects import (
    InteractiveObject,
    InteractiveObjects,
    Instance,
)
from rbr_track_formats.trk.shape_collision_meshes import (
    ObjectKind,
    Quaternion,
    ShapeCollisionMesh,
    ShapeCollisionMeshes,
    FaceData,
    ObjectData,
    DynamicMesh,
)

import rbr_track_addon.blender_ops as ops
from rbr_track_addon.blender_ops import TracedObject
from rbr_track_formats.logger import Logger
from rbr_track_addon.object_settings.types import (
    RBRObjectType,
    check_scale_is_1,
)

from .textures import RBRExportTextureOracle
from .data_3d import (
    create_super_data3d,
    fixup_data_triangles_dtype,
    recursive_split,
)
from ..util import (
    create_supers_with,
    KeyGen,
)


def make_data_3ds(
    export_texture_oracle: RBRExportTextureOracle,
    logger: Logger,
    traced_obj: TracedObject,
) -> List[ObjectData3D]:
    # Duplicate it so we can separate by material without altering the original
    # TODO this is slow if it actually needs to do any work.
    separated = ops.separate_by_material_single(traced_obj)

    data_3ds = create_supers_with(
        f=lambda m, o: create_super_data3d(
            logger=logger,
            rbr_material=m,
            traced_obj=o,
            supports_specular=False,
            # The game can load untextured objects, but the object is at the world origin.
            supports_untextured=False,
        ),
        export_texture_oracle=export_texture_oracle,
        traced_objs=separated,
    )

    result_data_3ds: List[ObjectData3D] = []
    for data_3d in data_3ds:
        split_data_3ds = recursive_split(
            logger=logger,
            data=data_3d,
        )
        for split_data_3d in split_data_3ds:
            result_data_3ds.append(fixup_data_triangles_dtype(split_data_3d))
    return result_data_3ds


def make_interactive_object(
    io_keys: Dict[str, Key],
    export_texture_oracle: RBRExportTextureOracle,
    logger: Logger,
    keygen: KeyGen,
    traced_objs: List[TracedObject],
) -> InteractiveObject:
    """Given a list of interactive objects which share a mesh, create the
    exportable format.
    """

    instances: List[Instance] = []
    for traced_obj in traced_objs:
        obj = traced_obj.obj

        if not check_scale_is_1(obj):
            raise errors.E0152(
                object_name=traced_obj.source_name(),
                scale=str(obj.scale.to_tuple()),
            )

        original_mode = obj.rotation_mode
        obj.rotation_mode = "QUATERNION"
        rot_quaternion = Quaternion(
            w=obj.rotation_quaternion.w,
            x=obj.rotation_quaternion.x,
            y=obj.rotation_quaternion.y,
            z=obj.rotation_quaternion.z,
        )
        obj.rotation_mode = original_mode
        rot_matrix = rot_quaternion.flip_handedness().to_3x3_matrix()

        key = keygen.new_key()
        io_keys[obj.name_full] = key

        instance = Instance(
            key=key,
            transformation_matrix=Matrix4x4.from_position_and_rotation_matrix(
                position=Vector3.from_tuple(obj.location.to_tuple()).flip_handedness(),
                rotation=rot_matrix,
            ),
        )
        instances.append(instance)

    data_3ds = make_data_3ds(
        export_texture_oracle=export_texture_oracle,
        logger=logger,
        traced_obj=traced_objs[0],
    )

    mesh = traced_objs[0].obj.data

    return InteractiveObject(
        name=mesh.name,
        data_3d=data_3ds,
        instances=instances,
    )


def make_scm(
    objs: List[Tuple[Key, bpy.types.Object]],
) -> List[ShapeCollisionMesh]:
    mesh = objs[0][1].data
    mesh.calc_loop_triangles()
    if not ops.mesh_is_convex(TracedObject.create(objs[0][1])):
        raise errors.E0156(object_name=objs[0][1].name)
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
    objects_by_kind: Dict[ObjectKind, List[ObjectData]] = dict()
    for key, obj in objs:
        # Get the world position
        (position, quaternion, scale) = obj.matrix_world.decompose()
        if not check_scale_is_1(obj):
            raise errors.E0153(
                object_name=obj.name,
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
        kind = ObjectKind[obj.rbr_object_settings.interactive_object_kind]
        if kind in objects_by_kind:
            objects_by_kind[kind].append(object_data)
        else:
            objects_by_kind[kind] = [object_data]
    result_scms = []
    for kind, objects in objects_by_kind.items():
        result_scms.append(
            ShapeCollisionMesh(
                name=mesh.name,
                mesh_type=DynamicMesh(kind=kind),
                vertices=vertices,
                faces=faces,
                objects=objects,
            )
        )
    return result_scms


def export_interactive_objects(
    export_texture_oracle: RBRExportTextureOracle,
    logger: Logger,
    keygen: KeyGen,
    traced_objs: List[TracedObject],
) -> Tuple[ShapeCollisionMeshes, InteractiveObjects]:
    # Find the SCMs
    scm_by_io_name: Dict[str, bpy.types.Object] = dict()
    for traced_io in traced_objs:
        io = traced_io.obj
        scm = None
        for child in io.children:
            if (
                child.rbr_object_settings.type
                == RBRObjectType.INTERACTIVE_OBJECTS_COLMESH.name
            ):
                if scm is not None:
                    raise errors.E0154(object_name=traced_io.source_name())
                scm = child
        if scm is None:
            raise errors.E0155(object_name=traced_io.source_name())
        scm_by_io_name[io.name] = scm
    # Duplicate the interactive objects in one shot to avoid N^2 blender operator
    logger.info(f"Duplicating {len(traced_objs)} objects")
    duped_ios = ops.duplicate_objects(traced_objs)

    pairs = []
    to_apply = []
    for original, io_dupe in zip(traced_objs, duped_ios):
        scm = scm_by_io_name[original.obj.name]
        if io_dupe.obj.rbr_object_settings.interactive_object_apply_modifiers:
            to_apply.append(io_dupe)
        pairs.append((io_dupe, scm))

    def apply_modifiers() -> None:
        # Apply modifiers if necessary on the IO, not the SCM.
        # We want to keep SCM count down.
        # Typically IOs might have simple modifiers like data transfer for
        # shading purposes.
        ops.make_local(to_apply)
        for i, obj in enumerate(to_apply):
            ops.make_data_single_user(obj)
        ops.convert_to_mesh(to_apply)

    logger.section(f"Applying modifiers on {len(to_apply)} objects", apply_modifiers)
    io_keys: Dict[str, Key] = dict()

    def create_ios() -> List[InteractiveObject]:
        # Group IO by linked mesh
        io_by_mesh: Dict[str, List[TracedObject]] = dict()
        for io, _ in pairs:
            mesh = io.obj.data
            if mesh.name_full in io_by_mesh:
                io_by_mesh[mesh.name_full].append(io)
            else:
                io_by_mesh[mesh.name_full] = [io]
        # Convert the IOs to RBR types
        # This dict maps from duplicated IO object name to Key
        objects = []
        for n, traced_objs in io_by_mesh.items():
            logger.info(n, end="\r")
            objects.append(
                make_interactive_object(
                    io_keys=io_keys,
                    export_texture_oracle=export_texture_oracle,
                    logger=logger,
                    keygen=keygen,
                    traced_objs=traced_objs,
                )
            )
        return objects

    objects = logger.section("Creating interactive objects", create_ios)

    def create_scms() -> List[ShapeCollisionMesh]:
        # Group SCM by linked mesh
        scm_by_mesh: Dict[str, List[Tuple[Key, TracedObject]]] = dict()
        for io, scm in pairs:
            mesh = scm.data
            key = io_keys[io.obj.name_full]
            if mesh.name_full in scm_by_mesh:
                scm_by_mesh[mesh.name_full].append((key, scm))
            else:
                scm_by_mesh[mesh.name_full] = [(key, scm)]
        # Convert the SCMs to RBR types
        scm_meshes = []
        for _, scms in scm_by_mesh.items():
            scm_meshes.extend(make_scm(scms))
        return scm_meshes

    scm_meshes = logger.section("Creating shape collision meshes", create_scms)

    return (
        ShapeCollisionMeshes(meshes=scm_meshes),
        InteractiveObjects(objects=objects),
    )
