"""Geometry data
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, TypeVar
import dataclasses
import enum

from .. import errors
from ..common import AaBbBoundingBox
from .animation_objects import AnimationObjects
from .car_location import CarLocation
from .clipping_planes import ClippingPlanes
from .container_objects import ContainerObjects
from .drive_points import DrivePoints
from .interactive_objects import InteractiveObjects
from .object_blocks import ObjectBlocks, ObjectBlockSegment
from .geom_blocks import GeomBlocks, GeomBlock
from .reflection_objects import ReflectionObjects
from .super_bowl import SuperBowl
from .track_loader_vecs import TrackLoaderVecs
from .visible_object_vecs import VisibleObjectVec, VisibleObjectVecs
from .visible_objects import VisibleObjects
from .water_objects import WaterObjects


class TrackSegmentCategory(enum.Enum):
    UNKNOWN_0x0 = 0x0
    MAJOR = 0x1
    MINOR = 0x2
    WALLABY_0x9 = 0x9  # Wallaby writes this value incorrectly.


class TrackSegmentType(enum.Enum):
    GEOM_BLOCKS = 0x0
    OBJECT_BLOCKS = 0x1
    UNKNOWN_0x2 = 0x2
    SUPER_BOWL = 0x3
    CLIPPING_PLANES = 0x4
    INTERACTIVE_OBJECTS = 0x6
    REFLECTION_OBJECTS = 0x7
    WATER_OBJECTS = 0x8
    UNKNOWN_0x9 = 0x9
    VISIBLE_OBJECTS = 0xA  # Required or stage doesn't load
    CAR_LOCATION = 0xB
    DRIVE_POINTS = 0xC
    UNKNOWN_0xD = 0xD
    PC_ANIMATION_OBJECTS = 0xE
    PC_CONTAINER_OBJECTS = 0xF
    TRACK_LOADER_VECS = 0x10
    VISIBLE_OBJECT_VECS = 0x12
    UNKNOWN_0x17 = 0x17

    def category(self) -> TrackSegmentCategory:
        if self is TrackSegmentType.GEOM_BLOCKS:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.OBJECT_BLOCKS:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.UNKNOWN_0x2:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.SUPER_BOWL:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.CLIPPING_PLANES:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.INTERACTIVE_OBJECTS:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.REFLECTION_OBJECTS:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.WATER_OBJECTS:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.UNKNOWN_0x9:
            return TrackSegmentCategory.MAJOR
        elif self is TrackSegmentType.VISIBLE_OBJECTS:
            return TrackSegmentCategory.MINOR
        elif self is TrackSegmentType.CAR_LOCATION:
            return TrackSegmentCategory.MINOR
        elif self is TrackSegmentType.DRIVE_POINTS:
            return TrackSegmentCategory.MINOR
        elif self is TrackSegmentType.UNKNOWN_0xD:
            return TrackSegmentCategory.MINOR
        elif self is TrackSegmentType.PC_ANIMATION_OBJECTS:
            return TrackSegmentCategory.MINOR
        elif self is TrackSegmentType.PC_CONTAINER_OBJECTS:
            return TrackSegmentCategory.MINOR
        elif self is TrackSegmentType.TRACK_LOADER_VECS:
            return TrackSegmentCategory.MINOR
        elif self is TrackSegmentType.VISIBLE_OBJECT_VECS:
            return TrackSegmentCategory.MINOR
        elif self is TrackSegmentType.UNKNOWN_0x17:
            return TrackSegmentCategory.UNKNOWN_0x0
        else:
            raise errors.RBRAddonBug("Missing category for " + self.name)

    @staticmethod
    def canonical_order() -> List[TrackSegmentType]:
        return [
            TrackSegmentType.CAR_LOCATION,
            TrackSegmentType.TRACK_LOADER_VECS,
            TrackSegmentType.DRIVE_POINTS,
            TrackSegmentType.UNKNOWN_0xD,
            TrackSegmentType.UNKNOWN_0x17,
            TrackSegmentType.VISIBLE_OBJECTS,
            TrackSegmentType.CLIPPING_PLANES,
            TrackSegmentType.SUPER_BOWL,
            TrackSegmentType.INTERACTIVE_OBJECTS,
            TrackSegmentType.REFLECTION_OBJECTS,
            TrackSegmentType.WATER_OBJECTS,
            TrackSegmentType.UNKNOWN_0x9,
            TrackSegmentType.GEOM_BLOCKS,
            TrackSegmentType.OBJECT_BLOCKS,
            TrackSegmentType.PC_CONTAINER_OBJECTS,
            TrackSegmentType.PC_ANIMATION_OBJECTS,
            TrackSegmentType.VISIBLE_OBJECT_VECS,
        ]


@dataclass
class LBSSegmentRaw:
    track_segment_type: TrackSegmentType
    raw_bytes: bytes


@dataclass
class WorldChunk:
    bounding_box: AaBbBoundingBox
    geom_block: GeomBlock
    object_block_segment: Optional[ObjectBlockSegment]
    vec: VisibleObjectVec


@dataclass
class WorldChunks:
    beckmann_glossiness: float
    chunks: List[WorldChunk]

    def to_geom_blocks(self) -> GeomBlocks:
        return GeomBlocks(
            beckmann_glossiness=self.beckmann_glossiness,
            blocks=[c.geom_block for c in self.chunks],
        )

    def to_object_blocks(self) -> ObjectBlocks:
        return ObjectBlocks(
            blocks=[c.object_block_segment for c in self.chunks],
        )

    def to_visible_objects(self) -> VisibleObjects:
        return VisibleObjects(
            bounding_boxes=[c.bounding_box for c in self.chunks],
        )

    def to_visible_object_vecs(self) -> VisibleObjectVecs:
        return VisibleObjectVecs(
            vecs=[c.vec for c in self.chunks],
        )

    @staticmethod
    def from_blocks(
        visible_objects: VisibleObjects,
        geom_blocks: GeomBlocks,
        object_blocks: ObjectBlocks,
        visible_object_vecs: Optional[VisibleObjectVecs],
    ) -> WorldChunks:
        if not (
            len(geom_blocks.blocks)
            == len(object_blocks.blocks)
            == len(visible_objects.bounding_boxes)
        ):
            raise errors.E0083(
                num_geom_blocks=len(geom_blocks.blocks),
                num_object_blocks=len(object_blocks.blocks),
                num_visible_objects=len(visible_objects.bounding_boxes),
            )
        if visible_object_vecs is not None:
            if len(geom_blocks.blocks) != len(visible_object_vecs.vecs):
                raise errors.E0084(
                    num_geom_blocks=len(geom_blocks.blocks),
                    num_visible_object_vecs=len(visible_object_vecs.vecs),
                )
        chunks: List[WorldChunk] = []
        for i in range(len(visible_objects.bounding_boxes)):
            if visible_object_vecs is None:
                vec = VisibleObjectVec([])
            else:
                vec = visible_object_vecs.vecs[i]
            chunks.append(
                WorldChunk(
                    bounding_box=visible_objects.bounding_boxes[i],
                    geom_block=geom_blocks.blocks[i],
                    object_block_segment=object_blocks.blocks[i],
                    vec=vec,
                )
            )
        return WorldChunks(
            beckmann_glossiness=geom_blocks.beckmann_glossiness,
            chunks=chunks,
        )


A = TypeVar("A")


@dataclass
class LBS:
    world_chunks: WorldChunks
    clipping_planes: Optional[ClippingPlanes]
    car_location: CarLocation
    animation_objects: Optional[AnimationObjects]
    container_objects: Optional[ContainerObjects]
    drive_points: Optional[DrivePoints]
    track_loader_vecs: Optional[TrackLoaderVecs]
    interactive_objects: Optional[InteractiveObjects]
    reflection_objects: Optional[ReflectionObjects]
    water_objects: Optional[WaterObjects]
    super_bowl: Optional[SuperBowl]
    unhandled_segments: Dict[TrackSegmentType, bytes]

    segment_order: List[TrackSegmentType] = dataclasses.field(
        default_factory=TrackSegmentType.canonical_order
    )
