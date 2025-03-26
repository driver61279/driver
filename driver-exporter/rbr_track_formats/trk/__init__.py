"""Track file
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, TypeVar
import dataclasses
import enum

from .driveline import Driveline
from .shape_collision_meshes import ShapeCollisionMeshes


class TrackSegmentCategory(enum.Enum):
    PHYSICS = 0x3


class TrackSegmentType(enum.Enum):
    DRIVE_LINE = 0x14
    SHAPE_COLLISION_MESHES = 0x16

    def category(self) -> TrackSegmentCategory:
        if self is TrackSegmentType.DRIVE_LINE:
            return TrackSegmentCategory.PHYSICS
        elif self is TrackSegmentType.SHAPE_COLLISION_MESHES:
            return TrackSegmentCategory.PHYSICS
        else:
            return NotImplementedError("Missing category for " + self.name)

    @staticmethod
    def canonical_order() -> List[TrackSegmentType]:
        return [
            TrackSegmentType.DRIVE_LINE,
            TrackSegmentType.SHAPE_COLLISION_MESHES,
        ]


@dataclass
class TRKSegmentRaw:
    track_segment_type: TrackSegmentType
    raw_bytes: bytes


A = TypeVar("A")


@dataclass
class TRK:
    driveline: Driveline
    shape_collision_meshes: ShapeCollisionMeshes
    # TODO can this be removed?
    unhandled_segments: Dict[TrackSegmentType, bytes] = dataclasses.field(
        default_factory=dict
    )

    segment_order: List[TrackSegmentType] = dataclasses.field(
        default_factory=TrackSegmentType.canonical_order
    )
