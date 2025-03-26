from rbr_track_formats import dtypes
from rbr_track_formats.binary import PackBin
from rbr_track_formats.col import (
    COL,
    COLHeader,
    COL_MAGIC,
    CollisionTreeDataType,
    CollisionTreeType,
    NPhysics_CCollisionTreeFileNode,
    RootHeader,
    WaterSurface,
)
from rbr_track_formats.col.tree import (
    BranchTraversal,
)

from .brake_wall import brake_wall_to_binary
from .tree import (
    branch_traversal_to_binary,
    collision_tree_root_to_binary,
)
from ..common import vector3_to_binary
from ... import errors


def col_header_to_binary(self: COLHeader, bin: PackBin) -> None:
    bin.pack_bytes(COL_MAGIC)
    bin.pack(
        "<III",
        self.root_file_node_offset,
        self.num_subtree_nodes,
        self.subtree_nodes_offset,
    )


def collision_tree_data_type_to_binary(
    self: CollisionTreeDataType, bin: PackBin
) -> None:
    bin.pack("<B", self.value)


def collision_tree_type_to_binary(self: CollisionTreeType, bin: PackBin) -> None:
    bin.pack("<B", self.value)


def root_header_to_binary(self: RootHeader, bin: PackBin) -> None:
    bin.pack("<I", self.brake_wall_offset)
    bin.pack("<II", self.num_wet_surfaces, self.wet_surfaces_offset)
    bin.pack("<II", self.num_water_surfaces, self.water_surfaces_offset)


def nphysics_ccollisiontreefilenode_to_binary(
    self: NPhysics_CCollisionTreeFileNode, bin: PackBin
) -> None:
    collision_tree_data_type_to_binary(
        CollisionTreeDataType.WET_SURFACES_AND_WATER, bin
    )
    collision_tree_type_to_binary(self.tree_type, bin)
    bin.pack("<H", 0)
    branch_traversal_to_binary(self.branch_traversal, bin)
    bin.pack(
        "<BIII",
        self.branch_traversal.level(),
        self.num_vertices,
        self.vertices_offset,
        self.collision_tree_offset,
    )


def water_surface_to_binary(self: WaterSurface, bin: PackBin) -> None:
    vector3_to_binary(self.a, bin)
    bin.pack("<f", 0)
    vector3_to_binary(self.b, bin)
    bin.pack("<f", 0)
    vector3_to_binary(self.c, bin)
    bin.pack("<f", 0)
    vector3_to_binary(self.d, bin)
    bin.pack("<f", 0)


def col_to_binary(self: COL) -> bytes:
    bin = PackBin()
    if len(self.wet_surfaces) + len(self.water_surfaces) > 512:
        raise errors.E0159(
            num_wet_surfaces=len(self.wet_surfaces),
            num_water_surfaces=len(self.water_surfaces),
        )
    header = COLHeader(
        root_file_node_offset=0,
        num_subtree_nodes=0,
        subtree_nodes_offset=0,
    )
    col_header_to_binary(header, bin)
    header.root_file_node_offset = bin.offset
    root_offset = bin.offset
    root = NPhysics_CCollisionTreeFileNode(
        tree_type=CollisionTreeType.DATA,
        branch_traversal=BranchTraversal.empty_traversal(),
        num_vertices=0,
        vertices_offset=0,
        collision_tree_offset=0,
    )
    nphysics_ccollisiontreefilenode_to_binary(root, bin)
    root_header_offset = bin.offset
    root_header = RootHeader(
        brake_wall_offset=0,
        num_wet_surfaces=len(self.wet_surfaces),
        wet_surfaces_offset=0,
        num_water_surfaces=len(self.water_surfaces),
        water_surfaces_offset=0,
    )
    root_header_to_binary(root_header, bin)
    brake_wall_offset = 0 if self.brake_wall is None else bin.offset - root_offset
    if self.brake_wall is not None:
        brake_wall_to_binary(self.brake_wall, bin)
    if self.__brake_wall_padding__ is not None:
        bin.pack_bytes(self.__brake_wall_padding__)
    else:
        bin.pad_alignment(0x10)
    wet_surfaces_offset = bin.offset
    for s in self.wet_surfaces:
        water_surface_to_binary(s, bin)
    water_surfaces_offset = bin.offset
    for s in self.water_surfaces:
        water_surface_to_binary(s, bin)
    collision_tree_offset = bin.offset
    collision_tree_root_to_binary(self.collision_tree_root, False, bin)
    subtree_nodes_offset = bin.offset
    # Pack dummy subtree offsets
    for _ in self.subtrees:
        bin.pack("<I", 0)
    # if self.__subtree_padding__ is not None:
    #     bin.pack_bytes(self.__subtree_padding__)
    # else:
    #     bin.pad_alignment(0x8)
    for i, (traversal, vertices, subtree) in enumerate(self.subtrees):
        descriptor_address = bin.offset
        # Fixup subtree offsets pointer
        bin.pack_at(subtree_nodes_offset + i * 4, "<I", descriptor_address)
        descriptor = NPhysics_CCollisionTreeFileNode(
            tree_type=CollisionTreeType.RELATIVE_ADDRESSED_SUBTREE,
            branch_traversal=traversal,
            num_vertices=len(vertices),
            vertices_offset=0,
            collision_tree_offset=0,
        )
        descriptor.num_vertices = len(vertices)
        nphysics_ccollisiontreefilenode_to_binary(descriptor, bin)
        descriptor.vertices_offset = bin.offset - descriptor_address
        if vertices.dtype != dtypes.vector3:
            raise errors.RBRAddonBug(f"vertices dtype is invalid: {vertices.dtype}")
        bin.pack_bytes(vertices.tobytes())
        descriptor.collision_tree_offset = bin.offset - descriptor_address
        collision_tree_root_to_binary(subtree, True, bin)
        end_offset = bin.offset
        bin.offset = descriptor_address
        nphysics_ccollisiontreefilenode_to_binary(descriptor, bin)
        bin.offset = end_offset
    # Fixup header pointers
    bin.offset = 0
    header.num_subtree_nodes = len(self.subtrees)
    header.subtree_nodes_offset = subtree_nodes_offset
    col_header_to_binary(header, bin)
    # Fixup root pointers
    bin.offset = root_offset
    root.vertices_offset = collision_tree_offset - root_offset
    root.collision_tree_offset = collision_tree_offset - root_offset
    nphysics_ccollisiontreefilenode_to_binary(root, bin)
    # Fixup root header pointers
    bin.offset = root_header_offset
    root_header.brake_wall_offset = brake_wall_offset
    root_header.wet_surfaces_offset = wet_surfaces_offset - root_offset
    root_header.water_surfaces_offset = water_surfaces_offset - root_offset
    root_header_to_binary(root_header, bin)
    return bin.bytes()
