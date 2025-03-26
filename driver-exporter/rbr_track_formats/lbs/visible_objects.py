"""VisibleObjects contains a bounding box for each geom block.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..common import AaBbBoundingBox
from .geom_blocks import GeomBlocks


@dataclass
class VisibleObjects:
    # Each item corresponds to a particular geom block.
    bounding_boxes: List[AaBbBoundingBox]

    @staticmethod
    def from_geom_blocks(geom_blocks: GeomBlocks) -> VisibleObjects:
        # TODO take object blocks into account too.
        bounding_boxes = [b.bounding_box for b in geom_blocks.blocks]
        return VisibleObjects(bounding_boxes=bounding_boxes)
