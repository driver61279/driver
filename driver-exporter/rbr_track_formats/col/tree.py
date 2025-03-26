from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Union
import enum
import numpy as np

from ..common import A, AaBbBoundingBox, NumpyArray, KdTree, KdTreeNode
from ..errors import RBRAddonBug
from .. import dtypes


class Direction(enum.Enum):
    LEFT = 0x0
    RIGHT = 0x1


@dataclass
class BranchTraversal:
    traversal: List[Direction]

    @staticmethod
    def empty_traversal() -> BranchTraversal:
        return BranchTraversal(traversal=[])

    def cut_to_level(self, level: int) -> None:
        if not all(map(lambda d: d is Direction.LEFT, self.traversal[level:])):
            raise RBRAddonBug("Unexpected value in BranchTraversal.cut_to_level")
        self.traversal = self.traversal[:level]

    def level(self) -> int:
        return len(self.traversal)


# This is the raw binary encoding of surface triangles
raw_surface_triangle_dtype = np.dtype(
    [
        ("a_index", "<H"),
        ("b_index", "<H"),
        ("c_index", "<H"),
        # bitfield X CCCCC BBBBB AAAAA
        # X = no_auto_spawn
        # C = blending value for C
        # B = blending value for B
        # A = blending value for A
        ("blending_value", "<H"),
        # bitfield X CCCCC BBBBB AAAAA
        # X = no_auto_spawn_if_flipped
        # C = shading value for C
        # B = shading value for B
        # A = shading value for A
        ("shading_value", "<H"),
        ("material_1_id", "<B"),
        ("material_2_id", "<B"),
        # bitfield UUUUVVVV
        ("a_material_1_uv", "<B"),
        ("b_material_1_uv", "<B"),
        ("c_material_1_uv", "<B"),
        ("a_material_2_uv", "<B"),
        ("b_material_2_uv", "<B"),
        ("c_material_2_uv", "<B"),
    ]
)


# This is the user friendly encoding of surface triangles
surface_triangle_point_dtype = np.dtype(
    [
        ("index", "<I"),
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


@dataclass
class CollisionTreeLeaf:
    triangles: NumpyArray  # dtype=surface_triangle_dtype
    __padding__: Optional[bytes] = None


@dataclass
class CollisionTreeNodeHeader:
    """This is the real storage format of the node.

    bounding_box
        A 3D axis aligned bounding box covering everything within this node
    num_surface_triangles
        The number of surface triangles contained (only set if this is a leaf
        node).
    link_node
        True if we are a link node. Link nodes are the leaf nodes of the root
        tree, or the root nodes of a subtree.
    offset
        The offset of the child tree / leaf. Invalid if we are a subtree of the
        col file root tree.
    """

    bounding_box: AaBbBoundingBox
    num_surface_triangles: int
    link_node: bool
    offset: int


@dataclass
class CollisionTreeLinkNode:
    offset: int
    num_surface_triangles: int


@dataclass
class CollisionTreeNode:
    bounding_box: AaBbBoundingBox
    # The int value is only present for the root tree (without any materials
    # packed within it). The Leaf value is only present for the subtrees (with
    # materials packed within them).
    value: Union[CollisionTree, CollisionTreeLinkNode, CollisionTreeLeaf]

    def to_header(self) -> CollisionTreeNodeHeader:
        """Convert this to a suitable header. Not all values are initialised
        and they must be fixed later when offsets are known.
        """
        if isinstance(self.value, CollisionTree):
            link_node = False
            num_surface_triangles = 0
            offset = 0
        elif isinstance(self.value, CollisionTreeLinkNode):
            link_node = True
            num_surface_triangles = self.value.num_surface_triangles
            offset = self.value.offset
        elif isinstance(self.value, CollisionTreeLeaf):
            link_node = False
            num_surface_triangles = len(self.value.triangles)
            offset = 0
        else:
            raise RBRAddonBug(
                f"Missing case in CollisionTreeNode.to_header: {type(self.value)}"
            )
        return CollisionTreeNodeHeader(
            bounding_box=self.bounding_box,
            link_node=link_node,
            num_surface_triangles=num_surface_triangles,
            offset=offset,
        )

    def to_tree_string(self) -> List[str]:
        result = []
        result.append(str(self.bounding_box))
        if isinstance(self.value, CollisionTree):
            result.extend(self.value.to_tree_string())
        elif isinstance(self.value, CollisionTreeLeaf):
            result.append(str(self.value))
        else:
            result.append(str(self.value))
        return result

    def walk(self, traversal: List[Direction]) -> CollisionTreeNode:
        if traversal == []:
            return self
        else:
            if isinstance(self.value, CollisionTree):
                return self.value.walk(traversal)
            elif isinstance(self.value, CollisionTreeLinkNode):
                return self
            else:
                raise RBRAddonBug(
                    f"Missing case in CollisionTreeNode.walk: {type(self.value)}"
                )

    def depth(self, comparator: Callable[[int, int], int]) -> int:
        if isinstance(self.value, CollisionTree):
            return self.value.depth(comparator) + 1
        elif isinstance(self.value, CollisionTreeLeaf):
            return 0
        else:
            return 0

    def traverse_leaves(self, f: Callable[[CollisionTreeLeaf], None]) -> None:
        if isinstance(self.value, CollisionTree):
            self.value.traverse_leaves(f)
        elif isinstance(self.value, CollisionTreeLeaf):
            f(self.value)
        else:
            raise RBRAddonBug(
                f"Missing case in CollisionTreeNode.traverse_leaves: {type(self.value)}"
            )

    @staticmethod
    def tree_from_kdtree(
        make_node: Callable[[A], CollisionTreeNode],
        tree: KdTreeNode[A],
    ) -> CollisionTreeNode:
        """Create a collision tree from a KdTree"""
        if isinstance(tree.value, KdTree):
            value = CollisionTree.tree_from_kdtree(make_node, tree.value)
            return CollisionTreeNode(
                value=value,
                bounding_box=AaBbBoundingBox.union(
                    value.left.bounding_box, value.right.bounding_box
                ),
            )
        else:
            return make_node(tree.value)

    def get_traversals(
        self, current_traversal: BranchTraversal
    ) -> List[Tuple[BranchTraversal, CollisionTreeLinkNode]]:
        if isinstance(self.value, CollisionTree):
            return self.value.get_traversals(current_traversal)
        elif isinstance(self.value, CollisionTreeLinkNode):
            return [(current_traversal, self.value)]
        else:
            raise RBRAddonBug(
                f"Missing case in CollisionTreeNode.get_traversals: {type(self.value)}"
            )


@dataclass
class CollisionTree:
    left: CollisionTreeNode
    right: CollisionTreeNode

    def to_tree_string(self) -> List[str]:
        left = self.left.to_tree_string()
        left = list(map(lambda x: "│ " + x, left))
        left[0] = "├" + left[0][1:]
        right = self.right.to_tree_string()
        right = list(map(lambda x: "  " + x, right))
        right[0] = "└" + right[0][1:]
        return left + right

    def walk(self, traversal: List[Direction]) -> CollisionTreeNode:
        direction = traversal[0]
        side = self.left if direction is Direction.LEFT else self.right
        return side.walk(traversal[1:])

    def depth(self, comparator: Callable[[int, int], int]) -> int:
        return comparator(self.left.depth(comparator), self.right.depth(comparator))

    def traverse_leaves(self, f: Callable[[CollisionTreeLeaf], None]) -> None:
        self.left.traverse_leaves(f)
        self.right.traverse_leaves(f)

    def get_traversals(
        self, current_traversal: BranchTraversal
    ) -> List[Tuple[BranchTraversal, CollisionTreeLinkNode]]:
        left_traversal = BranchTraversal(traversal=current_traversal.traversal.copy())
        left_traversal.traversal.append(Direction.LEFT)
        left_result = self.left.get_traversals(left_traversal)
        right_traversal = BranchTraversal(traversal=current_traversal.traversal.copy())
        right_traversal.traversal.append(Direction.RIGHT)
        right_result = self.right.get_traversals(right_traversal)
        return left_result + right_result

    @staticmethod
    def tree_from_kdtree(
        make_node: Callable[[A], CollisionTreeNode],
        tree: KdTree[A],
    ) -> CollisionTree:
        """Create a collision tree from a KdTree"""
        return CollisionTree(
            left=CollisionTreeNode.tree_from_kdtree(make_node, tree.left),
            right=CollisionTreeNode.tree_from_kdtree(make_node, tree.right),
        )


@dataclass
class CollisionTreeRoot:
    root: CollisionTreeNode

    def draw_tree(self) -> None:
        for str in self.root.to_tree_string():
            print(str)

    def walk(self, traversal: List[Direction]) -> CollisionTreeNode:
        return self.root.walk(traversal)

    def depth(self, comparator: Callable[[int, int], int]) -> int:
        return self.root.depth(comparator)

    def traverse_leaves(self, f: Callable[[CollisionTreeLeaf], None]) -> None:
        self.root.traverse_leaves(f)

    def get_traversals(self) -> List[Tuple[BranchTraversal, CollisionTreeLinkNode]]:
        return self.root.get_traversals(BranchTraversal.empty_traversal())
