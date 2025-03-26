from __future__ import annotations
from typing import Callable, Dict, List, Tuple
import numpy as np
from numpy.lib.recfunctions import (
    structured_to_unstructured,
    unstructured_to_structured,
)

from ..common import (
    KdTree,
    KdTreeNode,
    NumpyArray,
    compute_bounding_box_from_positions,
)
from ..errors import RBRAddonBug
from .. import dtypes
from . import tree
from .tree import (
    BranchTraversal,
    CollisionTreeLeaf,
    CollisionTreeLinkNode,
    CollisionTreeNode,
    CollisionTreeRoot,
)


# These dtypes are not suitable for direct serialisation, because numpy does
# not support the bitfields in the real types particularly well.
# They are suitable for quickly getting data out of blender and constructing
# the tree, though. The vertex positions are embedded into the triangles for
# ease of processing.

surface_triangle_point_dtype = np.dtype(
    [
        ("position", dtypes.vector3),
        ("blending", "<f"),
        ("shading", "<f"),
        ("material_1_uv", dtypes.uv),
        ("material_2_uv", dtypes.uv),
    ]
)

surface_triangle_dtype = np.dtype(
    [
        ("a", surface_triangle_point_dtype),
        ("b", surface_triangle_point_dtype),
        ("c", surface_triangle_point_dtype),
        ("material_1_id", "<I"),
        ("material_2_id", "<I"),
        ("no_auto_spawn", "?"),
        ("no_auto_spawn_if_flipped", "?"),
    ]
)


def vector3_to_xyz(arr: NumpyArray) -> NumpyArray:
    """Convert a dtype=vector3 array into an [[x,y,z]] multidim array"""
    if arr.dtype != dtypes.vector3:
        raise RBRAddonBug(f"Bad dtype for input array {arr.dtype}")
    return structured_to_unstructured(arr)


def xyz_to_vector3(arr: NumpyArray) -> NumpyArray:
    """Convert an [[x,y,z]] multidim array into a dtype=vector3 array"""
    return unstructured_to_structured(arr, dtype=dtypes.vector3)


def surface_triangle_centres(tris: NumpyArray) -> NumpyArray:
    """Get the triangle centres (as dtypes.vector3) given an array of
    dtype=surface_triangle_dtype.
    """
    if tris.dtype != surface_triangle_dtype:
        raise RBRAddonBug(
            f"surface_triangle_centres: tris dtype is invalid:\n{tris.dtype}\nexpected:\n{surface_triangle_dtype}"
        )
    a_position = vector3_to_xyz(tris["a"]["position"])
    b_position = vector3_to_xyz(tris["b"]["position"])
    c_position = vector3_to_xyz(tris["c"]["position"])
    return xyz_to_vector3((a_position + b_position + c_position) / 3)


Bin = Tuple[float, float]


def bin_triangles(
    tris: NumpyArray,
    bin_size: float,
) -> Dict[Bin, NumpyArray]:
    """Put a bunch of triangles into square bins in the X,Y plane"""
    # Centres as vector3
    triangle_centres = surface_triangle_centres(tris)
    # Centres as multidimensional x,y
    xy_centres = np.vstack(
        (
            triangle_centres["x"],
            triangle_centres["y"],
        )
    ).transpose()
    if xy_centres.shape != (
        len(tris),
        2,
    ):
        raise RBRAddonBug(f"Bad xy_centres shape: {xy_centres.shape}")
    # Convert the centres into bins
    # [ [x_bin z_bin]
    # , [x_bin z_bin]
    # ... one for each triangle
    # ]
    triangle_bins = np.floor_divide(xy_centres, bin_size)
    # Find all unique bins so we can iterate over them
    unique_bins = np.unique(triangle_bins, axis=0)
    result: Dict[Bin, NumpyArray] = dict()
    for bin_arr in unique_bins:
        key = (bin_arr[0], bin_arr[1])
        # Filter to the triangles which exist in this bin
        mask = np.all(np.equal(triangle_bins, key), axis=1)
        these_tris = tris[mask]
        result[key] = these_tris
    return result


def unique_verts(tris: NumpyArray) -> Tuple[NumpyArray, NumpyArray]:
    a_positions = tris["a"]["position"]
    b_positions = tris["b"]["position"]
    c_positions = tris["c"]["position"]
    tri_positions = np.vstack((a_positions, b_positions, c_positions)).transpose()
    if tri_positions.shape != (
        len(tris),
        3,
    ):
        raise RBRAddonBug(f"tri_positions has bad shape {tri_positions.shape}")
    (vertices, flat_indices) = np.unique(tri_positions, return_inverse=True)
    if flat_indices.shape != (len(tris) * 3,):
        raise RBRAddonBug(f"flat_indices has bad shape {flat_indices.shape}")
    (i_a, i_b, i_c) = np.hsplit(flat_indices.reshape(len(tris), 3), 3)

    def make_new(indices: NumpyArray, old: NumpyArray) -> NumpyArray:
        new = np.empty(len(tris), dtype=tree.surface_triangle_point_dtype)
        new["index"] = indices.reshape(-1)
        new["blending"] = old["blending"]
        new["shading"] = old["shading"]
        new["material_1_uv"] = old["material_1_uv"]
        new["material_2_uv"] = old["material_2_uv"]
        return new

    new_tris = np.empty(len(tris), dtype=tree.surface_triangle_dtype)
    new_tris["a"] = make_new(i_a, tris["a"])
    new_tris["b"] = make_new(i_b, tris["b"])
    new_tris["c"] = make_new(i_c, tris["c"])
    new_tris["material_1_id"] = tris["material_1_id"]
    new_tris["material_2_id"] = tris["material_2_id"]
    new_tris["no_auto_spawn"] = tris["no_auto_spawn"]
    new_tris["no_auto_spawn_if_flipped"] = tris["no_auto_spawn_if_flipped"]

    return (vertices, new_tris)


# Two levels of tree:
# The outer level which contains subtrees. The subtrees contain vertices, and
# can't index more than 65536 (2^16).
# The inner level which has < 12 triangles per leaf.

# Plan:
# 1) Recursively split all_tris until we have subtree_tris with < 2^16 verts
# 2) Recursively split subtree_tris until we have < 12 triangles per leaf


def split_array_by(arr: NumpyArray, cond: NumpyArray) -> Tuple[NumpyArray, NumpyArray]:
    """Given an array and a condition (which should have the same number of
    elements) split the array according to the condition.
    """
    return (arr[cond], arr[~cond])


def split_along_longest_axis(
    tris: NumpyArray,
) -> Tuple[NumpyArray, NumpyArray]:
    # Centres as vector3
    if tris.dtype != surface_triangle_dtype:
        raise RBRAddonBug(
            f"split_along_longest_axis: tris dtype is invalid:\n{tris.dtype}\nexpected:\n{surface_triangle_dtype}"
        )
    triangle_centres = surface_triangle_centres(tris)
    mask = mask_to_split_longest_axis(triangle_centres)
    return split_array_by(tris, mask)


def index_surface_triangle_centres(
    verts: NumpyArray,
    tris: NumpyArray,
) -> NumpyArray:
    """Get the triangle centres (as dtypes.vector3) given an array of
    dtype=surface_triangle_dtype.
    """
    if verts.dtype != dtypes.vector3:
        raise RBRAddonBug(f"verts dtype is invalid: {verts.dtype}")
    if tris.dtype != tree.surface_triangle_dtype:
        raise RBRAddonBug(
            f"index_surface_triangle_centres: tris dtype is invalid:\n{tris.dtype}\nexpected:\n{tree.surface_triangle_dtype}"
        )
    a_position = vector3_to_xyz(verts[tris["a"]["index"]])
    b_position = vector3_to_xyz(verts[tris["b"]["index"]])
    c_position = vector3_to_xyz(verts[tris["c"]["index"]])
    return xyz_to_vector3((a_position + b_position + c_position) / 3)


def verts_in_tris(
    verts: NumpyArray,
    tris: NumpyArray,
) -> NumpyArray:
    if verts.dtype != dtypes.vector3:
        raise RBRAddonBug(f"verts dtype is invalid: {verts.dtype}")
    if tris.dtype != tree.surface_triangle_dtype:
        raise RBRAddonBug(
            f"tris dtype is invalid:\n{tris.dtype}\nexpected:\n{tree.surface_triangle_dtype}"
        )
    a_verts = verts[tris["a"]["index"]]
    b_verts = verts[tris["b"]["index"]]
    c_verts = verts[tris["c"]["index"]]
    return np.concatenate((a_verts, b_verts, c_verts))


def split_along_longest_axis_with_verts(
    verts: NumpyArray,
    tris: NumpyArray,
) -> Tuple[NumpyArray, NumpyArray]:
    # Centres as vector3
    if tris.dtype != tree.surface_triangle_dtype:
        raise RBRAddonBug(
            f"tris dtype is invalid:\n{tris.dtype}\nexpected:\n{tree.surface_triangle_dtype}"
        )
    if verts.dtype != dtypes.vector3:
        raise RBRAddonBug(f"verts dtype is invalid: {verts.dtype}")
    triangle_centres = index_surface_triangle_centres(verts, tris)
    mask = mask_to_split_longest_axis(triangle_centres)
    return split_array_by(tris, mask)


def mask_to_split_longest_axis(
    vectors: NumpyArray,
) -> NumpyArray:
    """Find a mask which splits the given array in two along the midpoint of
    the longest axis.
    """
    if vectors.dtype != dtypes.vector3:
        raise RBRAddonBug(f"vectors dtype is invalid: {vectors.dtype}")
    xyz = vector3_to_xyz(vectors)
    # Find the longest axis
    maxi = np.amax(xyz, axis=0)
    mini = np.amin(xyz, axis=0)
    span = maxi - mini
    longest_axis = np.amax(span)
    axis_arr = np.where(span == longest_axis)
    longest_axis_index = axis_arr[0][0]
    midpoint = np.average(xyz, axis=0)[longest_axis_index]

    longest_axis_values = xyz[:, longest_axis_index]
    result = longest_axis_values < midpoint
    if result.dtype != bool:
        raise RBRAddonBug(f"result dtype is invalid: {result.dtype}")
    if result.shape != (len(vectors),):
        raise RBRAddonBug(f"result shape is invalid: {result.shape}")
    return result


def build_tree(
    logger: Callable[[str], None],
    tris: NumpyArray,
) -> Tuple[
    CollisionTreeRoot,
    List[Tuple[BranchTraversal, NumpyArray, CollisionTreeRoot]],
]:
    logger("Splitting root tree")
    root_kdtree = recursive_split_root(tris)
    subtrees_list = []
    i = 0

    def build_root(tup: Tuple[NumpyArray, NumpyArray]) -> CollisionTreeNode:
        subtrees_list.append(tup)
        (verts, tris) = tup
        nonlocal i
        offset = i
        i += 1
        return CollisionTreeNode(
            bounding_box=compute_bounding_box_from_positions(verts),
            value=CollisionTreeLinkNode(
                offset=offset,
                num_surface_triangles=len(tris),
            ),
        )

    main_root = CollisionTreeRoot(
        root=CollisionTreeNode.tree_from_kdtree(
            tree=root_kdtree.traverse(build_root),
            make_node=lambda x: x,
        ),
    )

    # Get all possible traversals and flip them around so we know which
    # traversal to use for a given index
    traversals = main_root.get_traversals()
    index_to_traversal_list = [(n.offset, t) for t, n in traversals]
    index_to_traversal_list.sort()
    index_to_traversal: List[BranchTraversal] = []
    for i, (j, t) in enumerate(index_to_traversal_list):
        if i != j:
            raise RBRAddonBug(f"build_tree: suspicious traversal indices {i} {j}")
        index_to_traversal.append(t)

    logger("Splitting subtrees...")
    # Deal with the subtrees
    subtrees: List[Tuple[BranchTraversal, NumpyArray, CollisionTreeRoot]] = []
    for i, (vertices, triangles) in enumerate(subtrees_list):
        logger(f"Splitting subtree {i} with {len(triangles)} triangles")
        leaf_kdtree = recursive_split_leaf(vertices, triangles)

        def build_leaf(tris: NumpyArray) -> CollisionTreeNode:
            return CollisionTreeNode(
                bounding_box=compute_bounding_box_from_positions(
                    verts_in_tris(vertices, tris)
                ),
                value=CollisionTreeLeaf(tris),
            )

        subtree = CollisionTreeRoot(
            root=CollisionTreeNode.tree_from_kdtree(
                tree=leaf_kdtree.traverse(build_leaf),
                make_node=lambda x: x,
            ),
        )

        subtrees.append((index_to_traversal[i], vertices, subtree))
    return (main_root, subtrees)


def recursive_split_root(
    tris: NumpyArray,
    level: int = 0,
) -> KdTreeNode[Tuple[NumpyArray, NumpyArray]]:
    if tris.dtype != surface_triangle_dtype:
        raise RBRAddonBug(
            f"tris dtype is invalid:\n{tris.dtype}\nexpected:\n{surface_triangle_dtype}"
        )
    (verts, unique_tris) = unique_verts(tris)
    # We split if the number of vertices doesn't fit in the buffer
    # or if we're on the first level (RBR doesn't like trees which don't branch
    # at all, the game crashes as the stage starts). Real stages shouldn't run
    # into this case, but it's useful for tiny test stages.
    if len(verts) < 2**16 and level > 0:
        return KdTreeNode(
            value=(verts, unique_tris),
        )
    else:
        (left, right) = split_along_longest_axis(tris)
        if np.size(left) == 0:
            return KdTreeNode(value=right)
        if np.size(right) == 0:
            return KdTreeNode(value=left)
        # If we actually managed to reduce the input set, split again
        return KdTreeNode(
            value=KdTree(
                left=recursive_split_root(left, level=level + 1),
                right=recursive_split_root(right, level=level + 1),
            )
        )


def recursive_split_leaf(
    verts: NumpyArray,
    tris: NumpyArray,
    leaf_triangle_count: int = 12,
) -> KdTreeNode[NumpyArray]:
    """Recursively split the longest axis until the tree only contains
    leaf_triangle_count triangles
    """
    if verts.dtype != dtypes.vector3:
        raise RBRAddonBug(f"verts dtype is invalid: {verts.dtype}")
    if tris.dtype != tree.surface_triangle_dtype:
        raise RBRAddonBug(
            f"tris dtype is invalid:\n{tris.dtype}\nexpected:\n{tree.surface_triangle_dtype}"
        )
    if len(tris) <= leaf_triangle_count:
        return KdTreeNode(
            value=tris,
        )
    else:
        (left, right) = split_along_longest_axis_with_verts(verts, tris)
        if np.size(left) == 0:
            return KdTreeNode(value=right)
        if np.size(right) == 0:
            return KdTreeNode(value=left)
        # If we actually managed to reduce the input set, split again
        return KdTreeNode(
            value=KdTree(
                left=recursive_split_leaf(verts, left, leaf_triangle_count),
                right=recursive_split_leaf(verts, right, leaf_triangle_count),
            )
        )
