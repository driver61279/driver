"""Object blocks are general visual object meshes. These objects can sway in
    the wind and are subject to simple level-of-detail optimisations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import enum

from ..common import AaBbBoundingBox, NumpyArray
from .common import RenderStateFlags


@dataclass
class ObjectBlockLOD(enum.Enum):
    """This controls which buffer the game chooses when rendering geometry
    which is a certain distance away from the camera.

    For RenderQuality=high:

    ObjectBlockLOD                  Distance    Buffer used     Alpha blend mode
    ------------------------------------------------------------------------------
    NEAR_GEOMETRY_FROM_MAIN_BUFFER  0-1500      main_buffer     blend
    NEAR_GEOMETRY_FROM_MAIN_BUFFER  1500+       -               -
    FAR_GEOMETRY_FROM_MAIN_BUFFER   0-1500      -               -
    FAR_GEOMETRY_FROM_MAIN_BUFFER   1500+       main_buffer     clip threshold 0.8
    FAR_GEOMETRY_FROM_FAR_BUFFER    0-1500      main_buffer     blend
    FAR_GEOMETRY_FROM_FAR_BUFFER    1500+       far_buffer      clip threshold 0.8

    For RenderQuality=low, RBR uses main_buffer everywhere with clip threshold 0.2.
    """

    NEAR_GEOMETRY_FROM_MAIN_BUFFER = 0
    FAR_GEOMETRY_FROM_MAIN_BUFFER = 1
    FAR_GEOMETRY_FROM_FAR_BUFFER = 2


@dataclass
class ObjectBlock:
    # Options for rendering this block
    render_state_flags: RenderStateFlags
    # Not really optional, only single texture objects are supported in game.
    # Untextured and double textured objects crash the game, and anecdotally
    # there doesn't seem to be a pixel shader for those object types.
    diffuse_texture_index_1: Optional[int]
    # This must be None when exporting.
    diffuse_texture_index_2: Optional[int]
    # Primary triangles for this scenery. Whether this is near or far geometry
    # depends on the lod.
    main_buffer: NumpyArray
    # Level of detail optimisation. If the setting is
    # FAR_GEOMETRY_FROM_FAR_BUFFER, you must populate the far_buffer.
    lod: ObjectBlockLOD
    # Triangles for far geometry
    far_buffer: Optional[NumpyArray]
    # Vertex array (format has sway data)
    vertices: NumpyArray
    # This is the bounding box for the entire mesh. It's specified by the
    # position of the centre of the box, and the half extents of the sides.
    bounding_box: AaBbBoundingBox
    # This is only to aid roundtripping Wallaby maps. They don't specify this
    # like the default maps, and it's unused in game so it doesn't matter.
    fvf: int = 0


@dataclass
class ObjectBlockSegment:
    blocks_1: List[ObjectBlock]
    # Appears to be used for collidable objects: tree trunks, rocks.
    # There doesn't seem to be any difference in how they are rendered.
    blocks_2: List[ObjectBlock]

    def compute_bounding_box(self) -> Optional[AaBbBoundingBox]:
        boxes = [b.bounding_box for b in self.blocks_1]
        boxes.extend([b.bounding_box for b in self.blocks_2])
        return AaBbBoundingBox.unions(boxes)


@dataclass
class ObjectBlocks:
    """ObjectBlocks specify general object meshes. These objects can sway in
    the wind and are subject to level-of-detail optimisations.

    Each item of 'blocks' corresponds to a particular geom block.
    """

    blocks: List[Optional[ObjectBlockSegment]]
