from rbr_track_formats.binary import PackBin
from rbr_track_formats.col.brake_wall import (
    AABB2,
    BrakeWall,
    BrakeWallBranchHeader,
    BrakeWallFileDataHeader,
    BrakeWallIndex,
    BrakeWallLeaf,
    BrakeWallPointPair,
    BrakeWallRoot,
    BrakeWallTree,
)

from ..common import vector2_to_binary
from ... import errors


def brake_wall_file_data_header_to_binary(
    self: BrakeWallFileDataHeader, bin: PackBin
) -> None:
    bin.pack(
        "<IIII",
        self.size,
        self.num_point_pairs * 2,
        self.point_pairs_offset,
        self.tree_relative_offset,
    )


def brake_wall_index_to_binary(self: BrakeWallIndex, bin: PackBin) -> None:
    value = self.point_pair_index << 1
    if self.rally_school:
        value |= 1 << 14
    if self.auto_respawn:
        value |= 1 << 15
    bin.pack("<H", value)


def brake_wall_leaf_to_binary(self: BrakeWallLeaf, bin: PackBin) -> None:
    for p in self.point_indices:
        brake_wall_index_to_binary(p, bin)
    if self.__pad_bytes__ is not None:
        bin.pack_bytes(self.__pad_bytes__)
    else:
        (_, rem) = divmod(bin.offset, 4)
        bin.pack_bytes(bytes(rem))


def aabb2_to_binary(self: AABB2, bin: PackBin) -> None:
    vector2_to_binary(self.position, bin)
    vector2_to_binary(self.size, bin)


def brake_wall_branch_header_to_binary(
    self: BrakeWallBranchHeader, bin: PackBin
) -> None:
    aabb2_to_binary(self.bounding_box, bin)
    bin.pack("<II", self.num_point_indices, self.offset)


def brake_wall_tree_to_binary(
    self: BrakeWallTree, root_offset: int, bin: PackBin
) -> None:
    # Write the left header
    left_header_offset = bin.offset
    left_header = self.left.to_header()
    brake_wall_branch_header_to_binary(left_header, bin)
    # Write the right header
    right_header_offset = bin.offset
    right_header = self.right.to_header()
    brake_wall_branch_header_to_binary(right_header, bin)
    # Write the left data: fixup the header to point to it, and call the
    # appropriate to_binary function
    left_value_offset = bin.offset
    left_header.offset = left_value_offset - root_offset
    bin.offset = left_header_offset
    brake_wall_branch_header_to_binary(left_header, bin)
    bin.offset = left_value_offset
    if isinstance(self.left.value, BrakeWallTree):
        brake_wall_tree_to_binary(self.left.value, root_offset, bin)
    elif isinstance(self.left.value, BrakeWallLeaf):
        brake_wall_leaf_to_binary(self.left.value, bin)
    # Write the right data, same as writing the left data
    right_value_offset = bin.offset
    right_header.offset = right_value_offset - root_offset
    bin.offset = right_header_offset
    brake_wall_branch_header_to_binary(right_header, bin)
    bin.offset = right_value_offset
    if isinstance(self.right.value, BrakeWallTree):
        brake_wall_tree_to_binary(self.right.value, root_offset, bin)
    elif isinstance(self.right.value, BrakeWallLeaf):
        brake_wall_leaf_to_binary(self.right.value, bin)


def brake_wall_root_to_binary(self: BrakeWallRoot, bin: PackBin) -> None:
    # Write the header
    root_header_offset = bin.offset
    root_header = self.root.to_header()
    brake_wall_branch_header_to_binary(root_header, bin)
    # Write the data and fixup the header
    root_value_offset = bin.offset
    root_header.offset = root_value_offset - root_header_offset
    bin.offset = root_header_offset
    brake_wall_branch_header_to_binary(root_header, bin)
    bin.offset = root_value_offset
    if isinstance(self.root.value, BrakeWallTree):
        brake_wall_tree_to_binary(self.root.value, root_header_offset, bin)
    elif isinstance(self.root.value, BrakeWallLeaf):
        brake_wall_leaf_to_binary(self.root.value, bin)


def brake_wall_point_pair_to_binary(self: BrakeWallPointPair, bin: PackBin) -> None:
    vector2_to_binary(self.inner, bin)
    vector2_to_binary(self.outer, bin)


def brake_wall_to_binary(self: BrakeWall, bin: PackBin) -> None:
    # Write the header data we already know
    header_offset = bin.offset
    num_points = 2 * len(self.point_pairs)
    MAX_POINTS = pow(2, 14)
    if num_points > MAX_POINTS:
        raise errors.E0001(num_points=num_points, max_points=MAX_POINTS)
    if len(self.point_pairs) > 0:
        point_pairs = self.point_pairs + [self.point_pairs[0]]
    else:
        point_pairs = []
    header = BrakeWallFileDataHeader(
        size=0,
        num_point_pairs=len(point_pairs),
        point_pairs_offset=16,
        tree_relative_offset=0,
    )
    brake_wall_file_data_header_to_binary(header, bin)
    # Write pair data
    for pair in point_pairs:
        brake_wall_point_pair_to_binary(pair, bin)
    # Write the tree
    tree_offset = bin.offset
    tree_relative_offset = tree_offset - header_offset
    brake_wall_root_to_binary(self.root, bin)
    # Fixup the missing header data values
    tree_end_offset = bin.offset
    header.size = tree_end_offset - header_offset
    header.tree_relative_offset = tree_relative_offset
    bin.offset = header_offset
    brake_wall_file_data_header_to_binary(header, bin)
    bin.offset = tree_end_offset
