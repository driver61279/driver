from rbr_track_formats import errors
from rbr_track_formats.binary import PackBin
from rbr_track_formats.common import AaBbBoundingBox
from rbr_track_formats.mat import MaterialID, object_materials
from rbr_track_formats.trk.shape_collision_meshes import (
    BoundingSphere,
    DynamicMesh,
    FaceData,
    MAX_SCM_EDGES,
    MAX_SCM_FACES,
    MAX_SCM_VERTICES,
    ObjectData,
    ObjectKind,
    Quaternion,
    ShapeCollisionMesh,
    ShapeCollisionMeshes,
    SoftVolumeType,
    StaticMesh,
)

from ..common import (
    aabb_bounding_box_to_binary,
    key_to_binary,
    vector3_to_binary,
)
from ..mat import material_id_to_binary


def object_kind_to_binary(self: ObjectKind, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def soft_volume_type_to_binary(self: SoftVolumeType, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def bounding_sphere_to_binary(self: BoundingSphere, bin: PackBin) -> None:
    vector3_to_binary(self.position, bin)
    bin.pack("<f", self.radius)


def face_data_to_binary(self: FaceData, bin: PackBin) -> None:
    physics_id = MaterialID.SPECTATOR if self.spectator else MaterialID.UNDEFINED
    material_id_to_binary(physics_id, bin)
    bin.pack("<III", self.index_a, self.index_b, self.index_c)


def quaternion_to_binary(self: Quaternion, bin: PackBin) -> None:
    bin.pack("<ffff", self.x, self.y, self.z, self.w)


def object_data_to_binary(self: ObjectData, bin: PackBin) -> None:
    key_to_binary(self.key, bin)
    vector3_to_binary(self.position, bin)
    vector3_to_binary(self.scale, bin)
    quaternion_to_binary(self.rotation, bin)


def shape_collision_mesh_to_binary(self: ShapeCollisionMesh, bin: PackBin) -> None:
    # Apparently the game rewrites the kinds if the names match certain
    # strings, so we prevent the user writing the shape if it will be
    # silently altered by the game.
    if "CONE" in self.name:
        if not isinstance(self.mesh_type, DynamicMesh):
            raise errors.E0094(name=self.name)
        if self.mesh_type.kind is not ObjectKind.TRAFFIC_CONE:
            raise errors.E0094(name=self.name)
    if "BANNER_STAND" in self.name:
        if not isinstance(self.mesh_type, DynamicMesh):
            raise errors.E0095(name=self.name)
        if self.mesh_type.kind is not ObjectKind.BANNER_FENCE:
            raise errors.E0095(name=self.name)
    bin.pack_null_terminated_string(self.name)
    # Pack the mesh type
    if isinstance(self.mesh_type, StaticMesh):
        bin.pack("<I", self.mesh_type.object_kind)
        if self.mesh_type.material not in object_materials:
            raise errors.RBRAddonBug(
                "Shape collision mesh material '{self.mesh_type.material.name}' is not in the list of valid object materials"
            )
        material_id_to_binary(self.mesh_type.material, bin)
        bin.pack("<B", self.mesh_type.use_local_rotation)
        if self.mesh_type.soft_volume is None:
            volume_type = SoftVolumeType.NONE
        elif isinstance(self.mesh_type.soft_volume, AaBbBoundingBox):
            volume_type = SoftVolumeType.BOX
        elif isinstance(self.mesh_type.soft_volume, BoundingSphere):
            volume_type = SoftVolumeType.SPHERE
        else:
            raise errors.RBRAddonBug(
                "Unhandled soft volume type '{type(self.mesh_type.soft_volume)}'"
            )
        soft_volume_type_to_binary(volume_type, bin)
        if isinstance(self.mesh_type.soft_volume, BoundingSphere):
            bounding_sphere_to_binary(self.mesh_type.soft_volume, bin)
        if isinstance(self.mesh_type.soft_volume, AaBbBoundingBox):
            aabb_bounding_box_to_binary(self.mesh_type.soft_volume, bin)
    elif isinstance(self.mesh_type, DynamicMesh):
        object_kind_to_binary(self.mesh_type.kind, bin)
        material_id_to_binary(MaterialID.UNDEFINED, bin)
        bin.pack("<B", 0)
        soft_volume_type_to_binary(SoftVolumeType.NONE, bin)
    else:
        raise errors.RBRAddonBug("Unhandled mesh type '{type(self.mesh_type)}'")
    # Pack the mesh and instance data
    if len(self.vertices) > MAX_SCM_VERTICES:
        raise errors.E0096(
            name=self.name,
            num_vertices=len(self.vertices),
            max_vertices=MAX_SCM_VERTICES,
        )
    bin.pack("<I", len(self.vertices))
    for vertex in self.vertices:
        vector3_to_binary(vertex, bin)
    edge_count = self.compute_edge_count()
    if edge_count > MAX_SCM_EDGES:
        raise errors.E0097(
            name=self.name, num_edges=edge_count, max_edges=MAX_SCM_EDGES
        )
    if len(self.faces) > MAX_SCM_FACES:
        raise errors.E0098(
            name=self.name, num_faces=len(self.faces), max_faces=MAX_SCM_FACES
        )
    bin.pack("<I", len(self.faces))
    for face in self.faces:
        face_data_to_binary(face, bin)
    bin.pack("<I", len(self.objects))
    for obj in self.objects:
        object_data_to_binary(obj, bin)


def shape_collision_meshes_to_binary(self: ShapeCollisionMeshes, bin: PackBin) -> None:
    # Hard limit imposed by RBR
    if len(self.meshes) > 0x2000:
        raise errors.E0099(num_meshes=len(self.meshes), max_meshes=0x2000)
    bin.pack("<I", len(self.meshes))
    for mesh in self.meshes:
        shape_collision_mesh_to_binary(mesh, bin)
