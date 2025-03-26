import numpy as np

from rbr_track_formats.binary import PackBin
from rbr_track_formats.common import (
    NumpyArray,
)
from rbr_track_formats.col.tree import (
    BranchTraversal,
    CollisionTree,
    CollisionTreeLeaf,
    CollisionTreeLinkNode,
    CollisionTreeNode,
    CollisionTreeNodeHeader,
    CollisionTreeRoot,
    Direction,
    raw_surface_triangle_dtype,
    surface_triangle_dtype,
)

from ... import errors
from ..common import (
    aabb_bounding_box_to_binary,
)


def branch_traversal_to_binary(self: BranchTraversal, bin: PackBin) -> None:
    extra = [Direction.LEFT for _ in range(24 - len(self.traversal))]
    traversal = self.traversal.copy()
    traversal.extend(extra)
    if len(traversal) != 24:
        raise errors.RBRAddonBug(f"Unexpected branch traversal length {len(traversal)}")
    a = 0
    for i, d in enumerate(self.traversal[0:8]):
        if d is Direction.RIGHT:
            a |= 1 << i
    b = 0
    for i, d in enumerate(self.traversal[8:16]):
        if d is Direction.RIGHT:
            b |= 1 << i
    c = 0
    for i, d in enumerate(self.traversal[16:24]):
        if d is Direction.RIGHT:
            c |= 1 << i
    bin.pack("<BBB", a, b, c)


def assert_raw_surface_triangle_dtype(arr: NumpyArray) -> None:
    if arr.dtype != raw_surface_triangle_dtype:
        raise errors.RBRAddonBug(f"arr has bad dtype: {arr.dtype}")


def assert_surface_triangle_dtype(arr: NumpyArray) -> None:
    if arr.dtype != surface_triangle_dtype:
        raise errors.RBRAddonBug(f"arr has bad dtype: {arr.dtype}")


def clamp(arr: NumpyArray, low: NumpyArray, high: NumpyArray) -> NumpyArray:
    return np.maximum(np.minimum(arr, high), low)


# 98 in 65s old method -N0
# 98 in 68s new method -N0
# 98 in 316s old method -N1
# 98 in 304s new method -N1
def to_raw_triangles(tris: NumpyArray) -> NumpyArray:
    assert_surface_triangle_dtype(tris)
    raw = np.empty(len(tris), dtype=raw_surface_triangle_dtype)
    raw["a_index"] = tris["a"]["index"]
    if raw["a_index"].dtype != "<H":
        raise errors.RBRAddonBug("to_raw_triangles: invalid type for a_index")
    raw["b_index"] = tris["b"]["index"]
    if raw["b_index"].dtype != "<H":
        raise errors.RBRAddonBug("to_raw_triangles: invalid type for b_index")
    raw["c_index"] = tris["c"]["index"]
    if raw["c_index"].dtype != "<H":
        raise errors.RBRAddonBug("to_raw_triangles: invalid type for c_index")

    blending_value: NumpyArray = np.ushort(tris["no_auto_spawn"])
    blending_value = (blending_value << 5) | np.ushort(tris["c"]["blending"] * 0b11111)
    blending_value = (blending_value << 5) | np.ushort(tris["b"]["blending"] * 0b11111)
    blending_value = (blending_value << 5) | np.ushort(tris["a"]["blending"] * 0b11111)
    if blending_value.dtype != "<H":
        raise errors.RBRAddonBug("to_raw_triangles: invalid type for blending_value")

    shading_value: NumpyArray = np.ushort(tris["no_auto_spawn_if_flipped"])
    shading_value = (shading_value << 5) | np.ushort(tris["c"]["shading"] * 0b11111)
    shading_value = (shading_value << 5) | np.ushort(tris["b"]["shading"] * 0b11111)
    shading_value = (shading_value << 5) | np.ushort(tris["a"]["shading"] * 0b11111)
    if shading_value.dtype != "<H":
        raise errors.RBRAddonBug("to_raw_triangles: invalid type for shading_value")

    raw["blending_value"] = blending_value
    raw["shading_value"] = shading_value

    # TODO check overflows
    raw["material_1_id"] = np.ubyte(tris["material_1_id"])
    if raw["material_1_id"].dtype != np.uint8:
        raise errors.RBRAddonBug(
            f"to_raw_triangles: invalid type for material_1_id: {raw['material_1_id'].dtype}"
        )
    raw["material_2_id"] = np.ubyte(tris["material_2_id"])
    if raw["material_2_id"].dtype != np.uint8:
        raise errors.RBRAddonBug(
            f"to_raw_triangles: invalid type for material_2_id: {raw['material_2_id'].dtype}"
        )

    def pack_uv(uv: NumpyArray) -> NumpyArray:
        u = np.ubyte(np.around(clamp(uv["u"], 0, 1) * 0xF))
        v = np.ubyte(np.around(clamp(uv["v"], 0, 1) * 0xF))
        byte_arr = u << 4 | v
        return byte_arr

    raw["a_material_1_uv"] = pack_uv(tris["a"]["material_1_uv"])
    raw["b_material_1_uv"] = pack_uv(tris["b"]["material_1_uv"])
    raw["c_material_1_uv"] = pack_uv(tris["c"]["material_1_uv"])
    raw["a_material_2_uv"] = pack_uv(tris["a"]["material_2_uv"])
    raw["b_material_2_uv"] = pack_uv(tris["b"]["material_2_uv"])
    raw["c_material_2_uv"] = pack_uv(tris["c"]["material_2_uv"])
    assert_raw_surface_triangle_dtype(raw)
    return raw


def collision_tree_leaf_to_binary(self: CollisionTreeLeaf, bin: PackBin) -> None:
    bin.pack_bytes(to_raw_triangles(self.triangles).tobytes())
    if self.__padding__ is None:
        bin.pad_alignment(0x4)
    else:
        bin.pack_bytes(self.__padding__)


def collision_tree_node_header_to_binary(
    self: CollisionTreeNodeHeader, bin: PackBin
) -> None:
    aabb_bounding_box_to_binary(self.bounding_box, bin)
    value = self.num_surface_triangles & 0b111111111111111111111
    if self.link_node:
        value |= 1 << 21
    bin.pack("<II", value, self.offset)


def collision_tree_node_to_binary(
    self: CollisionTreeNode, root_offset: int, bin: PackBin
) -> None:
    if isinstance(self.value, CollisionTree):
        collision_tree_to_binary(self.value, root_offset, bin)
    elif isinstance(self.value, CollisionTreeLeaf):
        collision_tree_leaf_to_binary(self.value, bin)
    elif isinstance(self.value, CollisionTreeLinkNode):
        pass
    else:
        raise errors.RBRAddonBug(
            f"collision_tree_node_to_binary: missing case: {type(self.value)}"
        )


def collision_tree_to_binary(
    self: CollisionTree, root_offset: int, bin: PackBin
) -> None:
    # Write the left header
    left_header_offset = bin.offset
    left_header = self.left.to_header()
    collision_tree_node_header_to_binary(left_header, bin)
    # Write the right header
    right_header_offset = bin.offset
    right_header = self.right.to_header()
    collision_tree_node_header_to_binary(right_header, bin)
    # Write the left data: fixup the header to point to it, and call the
    # appropriate to_binary function
    left_value_offset = bin.offset
    bin.offset = left_header_offset
    if not left_header.link_node:
        left_header.offset = left_value_offset - root_offset
    collision_tree_node_header_to_binary(left_header, bin)
    bin.offset = left_value_offset
    collision_tree_node_to_binary(self.left, root_offset, bin)
    # Write the right data, same as writing the left data
    right_value_offset = bin.offset
    bin.offset = right_header_offset
    if not right_header.link_node:
        right_header.offset = right_value_offset - root_offset
    collision_tree_node_header_to_binary(right_header, bin)
    bin.offset = right_value_offset
    collision_tree_node_to_binary(self.right, root_offset, bin)


def collision_tree_root_to_binary(
    self: CollisionTreeRoot, subtree: bool, bin: PackBin
) -> None:
    # Write the header
    root_header_offset = bin.offset
    root_header = self.root.to_header()
    collision_tree_node_header_to_binary(root_header, bin)
    # Write the data and fixup the header
    root_value_offset = bin.offset
    root_header.offset = root_value_offset - root_header_offset
    # Subtrees all have root nodes which are link nodes
    root_header.link_node = root_header.link_node or subtree
    # root_header.link_node = subtree
    bin.offset = root_header_offset
    collision_tree_node_header_to_binary(root_header, bin)
    bin.offset = root_value_offset
    collision_tree_node_to_binary(self.root, root_header_offset, bin)
