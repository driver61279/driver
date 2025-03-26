from __future__ import annotations
from dataclasses import dataclass
from functools import reduce
from typing import Callable, Iterator, List, Optional, Union
import math

from ..common import A, KdTreeNode, KdTree, Vector2
from ..errors import RBRAddonBug


@dataclass
class BrakeWallFileDataHeader:
    size: int  # Size in bytes of the entire brake wall section
    num_point_pairs: int
    point_pairs_offset: int
    tree_relative_offset: int


@dataclass
class BrakeWallIndex:
    """Holds an index to a brake wall pair, along with a couple of options for
    that pair.
    """

    point_pair_index: int  # The index of the _inner_ brake wall point
    rally_school: bool = False
    auto_respawn: bool = False

    @staticmethod
    def simple(i: int) -> BrakeWallIndex:
        return BrakeWallIndex(
            point_pair_index=i,
            rally_school=False,
            auto_respawn=False,
        )


@dataclass
class BrakeWallLeaf:
    point_indices: List[BrakeWallIndex]
    __pad_bytes__: Optional[bytes] = None


@dataclass
class BrakeWallBranch:
    """A brake wall branch consists of a 2D bounding box and either another
    tree or a leaf.
    """

    bounding_box: AABB2
    value: Union[BrakeWallTree, BrakeWallLeaf]

    def traverse(self, func: Callable[[BrakeWallLeaf], None]) -> None:
        if isinstance(self.value, BrakeWallLeaf):
            func(self.value)
        elif isinstance(self.value, BrakeWallTree):
            self.value.traverse(func)
        else:
            raise RBRAddonBug(
                f"Missing case in BrakeWallBranch.traverse: {type(self.value)}"
            )

    def to_header(self) -> BrakeWallBranchHeader:
        return BrakeWallBranchHeader(
            bounding_box=self.bounding_box,
            num_point_indices=(
                0
                if isinstance(self.value, BrakeWallTree)
                else len(self.value.point_indices)
            ),
            offset=0,
        )

    def to_tree_string(self) -> List[str]:
        result = []
        result.append(str(self.bounding_box))
        if isinstance(self.value, BrakeWallTree):
            result.extend(self.value.to_tree_string())
        elif isinstance(self.value, BrakeWallLeaf):
            result.append(
                str(list(map(lambda x: x.point_pair_index, self.value.point_indices)))
            )
        return result

    @staticmethod
    def tree_from_kdtree(
        make_node: Callable[[List[A]], BrakeWallBranch],
        tree: KdTreeNode[List[A]],
    ) -> BrakeWallBranch:
        """Create a collision tree from a KdTree"""
        if isinstance(tree.value, KdTree):
            value = BrakeWallTree.tree_from_kdtree(make_node, tree.value)
            return BrakeWallBranch(
                value=value,
                bounding_box=AABB2.union(
                    value.left.bounding_box, value.right.bounding_box
                ),
            )
        else:
            return make_node(tree.value)


@dataclass
class AABB2:
    """Position and size specifies two opposite corners of an axis aligned
    bounding box
    """

    position: Vector2  # Centre of the box
    size: Vector2  # Half extents of the sides

    @staticmethod
    def union(a: AABB2, b: AABB2) -> AABB2:
        min_x = min(a.position.x - a.size.x, b.position.x - b.size.x)
        min_y = min(a.position.y - a.size.y, b.position.y - b.size.y)
        max_x = max(a.position.x + a.size.x, b.position.x + b.size.x)
        max_y = max(a.position.y + a.size.y, b.position.y + b.size.y)
        position = Vector2(
            x=(min_x + max_x) / 2,
            y=(min_y + max_y) / 2,
        )
        size = Vector2(
            x=(max_x - min_x) / 2,
            y=(max_y - min_y) / 2,
        )
        return AABB2(
            position=position,
            size=size,
        )


@dataclass
class BrakeWallBranchHeader:
    """The raw branch header stored in the brake wall data."""

    bounding_box: AABB2
    num_point_indices: int
    offset: int


@dataclass
class BrakeWallTree:
    left: BrakeWallBranch
    right: BrakeWallBranch

    def traverse(self, func: Callable[[BrakeWallLeaf], None]) -> None:
        self.left.traverse(func)
        self.right.traverse(func)

    def to_tree_string(self) -> List[str]:
        left = self.left.to_tree_string()
        left = list(map(lambda x: "│ " + x, left))
        left[0] = "├" + left[0][1:]
        right = self.right.to_tree_string()
        right = list(map(lambda x: "  " + x, right))
        right[0] = "└" + right[0][1:]
        return left + right

    @staticmethod
    def tree_from_kdtree(
        make_node: Callable[[List[A]], BrakeWallBranch],
        tree: KdTree[List[A]],
    ) -> BrakeWallTree:
        return BrakeWallTree(
            left=BrakeWallBranch.tree_from_kdtree(make_node, tree.left),
            right=BrakeWallBranch.tree_from_kdtree(make_node, tree.right),
        )


@dataclass
class BrakeWallRoot:
    root: BrakeWallBranch

    def traverse(self, func: Callable[[BrakeWallLeaf], None]) -> None:
        self.root.traverse(func)

    def draw_tree(self) -> None:
        for str in self.root.to_tree_string():
            print(str)

    @staticmethod
    def generate_tree(point_pairs: List[BrakeWallPointPair]) -> BrakeWallRoot:
        """Generate a tree from a list of point pairs.

        The input list must be sorted in a reasonable manner when viewed from
        above, or this will not generate a good tree. By reasonable manner, I
        mean the points must be wound around the driveline such that wall
        pieces are adjacent to each another in the list if they are adjacent to
        each other in the plane. Clockwise or anticlockwise winding should work
        fine.

        The reason for this is the wall segment in each leaf of the tree must
        overlap with its neighbours, or it is possible for a car rubbing along
        the wall to escape. This overlap is created internally by splitting the
        wound list into chunks and extending each chunk with the first piece of
        wall from the subsequent chunk.
        """
        children_per_leaf = 7  # ends up being 8 when we overlap the chunks
        num_pairs = len(point_pairs) - 1
        num_chunks = math.ceil(num_pairs / children_per_leaf)
        chunked_indices = chunks(list(range(num_pairs)), num_chunks)
        annotated_leaves = []
        for indices in chunked_indices:
            indices = list(indices)
            indices.sort()
            # Make the chunk bounding boxes overlap slightly by adding the first
            # index from the next list to the end of our list before calculating
            # the bounding box. We don't actually store this in our leaf,
            # though.
            next_index = indices[-1] + 1
            extra_index = next_index if next_index < num_pairs else 0
            bbox_indices = indices + [extra_index]
            centres: List[Vector2] = [point_pairs[i].centre() for i in bbox_indices]
            centre: Vector2 = reduce(lambda x, y: x + y, centres).scale(0.5)
            annotated_leaves.append(
                (
                    centre.to_list(),
                    BrakeWallBranch(
                        bounding_box=reduce(
                            AABB2.union, [point_pairs[i].aabb() for i in bbox_indices]
                        ),
                        value=BrakeWallLeaf(
                            point_indices=[
                                BrakeWallIndex(
                                    point_pair_index=i,
                                    auto_respawn=point_pairs[i].auto_respawn,
                                )
                                for i in indices
                            ],
                        ),
                    ),
                )
            )
        kdtree_root = KdTreeNode.construct(2, annotated_leaves, 1)
        return BrakeWallRoot(
            root=BrakeWallBranch.tree_from_kdtree(lambda l: l[0], kdtree_root),
        )


def chunks(list: List[A], n: int) -> Iterator[List[A]]:
    """Yield sequential chunks of size n from the given list."""
    d, r = divmod(len(list), n)
    for i in range(n):
        si = (d + 1) * (i if i < r else r) + d * (0 if i < r else i - r)
        yield list[si : si + (d + 1 if i < r else d)]


@dataclass
class BrakeWallPointPair:
    """A pair of points along a brake wall.

    inner
        The inner wall point
    outer
        The corresponding outer wall point
    auto_respawn
        Indicates the car should automatically respawn (call for help) if it
        comes to rest in this part of the wall. This is not read/written from
        the track files from this type's data, instead it's written into the
        brake wall tree when generating a new tree. This is just a more
        convenient interface for building a brake wall.
    """

    inner: Vector2
    outer: Vector2
    auto_respawn: bool = False

    def aabb(self) -> AABB2:
        """Compute the AABB for this pair"""
        min_pos_x = min(self.inner.x, self.outer.x)
        min_pos_y = min(self.inner.y, self.outer.y)
        max_pos_x = max(self.inner.x, self.outer.x)
        max_pos_y = max(self.inner.y, self.outer.y)
        return AABB2(
            position=Vector2(
                x=(min_pos_x + max_pos_x) / 2,
                y=(min_pos_y + max_pos_y) / 2,
            ),
            size=Vector2(
                x=(max_pos_x - min_pos_x) / 2,
                y=(max_pos_y - min_pos_y) / 2,
            ),
        )

    def centre(self) -> Vector2:
        return (self.inner + self.outer).scale(0.5)


@dataclass
class BrakeWall:
    """A brake wall is an infinitely tall soft wall surrounding the track which
    prevents the car from driving too far away from the road. It consists of a
    series of two dimensional points defining two walls:

    - the inner wall at which the braking effect begins, and
    - the outer wall, which is impenetrable.

    The walls each form a complete loop around the track.
    From above, a straight bit of road might look like this:

    -------------------------   < outer wall
    -------------------------   < inner wall
    =========================   < track
    -------------------------   < inner wall
    -------------------------   < outer wall

    Each point on the inner wall has exactly one corresponding point on the
    outer wall:

      A         B         C
      .         .         .     < outer points
      |         |         |
      .         .         .     < inner points
      D         E         F

    -------------------------   < driveline

      G         H         I
      .         .         .     < inner points
      |         |         |
      .         .         .     < outer points
      J         K         L

    Note that the lines joining the inner and outer points here are only to
    show the relationship between points.

    These points are defined in an array such that the points at even indices
    0,2,4... are the innermost points, and the points at odd indices 1,3,5...
    are the corresponding outermost points, and these must be wound in a
    clockwise direction (looking from the top):

    > vertices = [D,A, E,B, F,C, G,J, H,K, I,L]

    In python, these are encapsulated by point_pairs. In most default stages,
    the last pair of points are duplicates of the first pair of points,
    presumably to ensure there is always a wall present (game code might not
    account for joining the ends of the loop). It is a good idea to match the
    default stages here or the wall might end up with a gap in some cases.

    For performance reasons, the game uses a B-tree to perform spacial queries
    on the brake walls. This is actually baked into the file, so we need to
    deal with it too. See BrakeWallTree for more information.
    """

    point_pairs: List[BrakeWallPointPair]
    root: BrakeWallRoot

    def generate_tree(self) -> None:
        if len(self.point_pairs) == 0:
            return
        point_pairs = self.point_pairs + [self.point_pairs[0]]
        self.root = BrakeWallRoot.generate_tree(point_pairs)
