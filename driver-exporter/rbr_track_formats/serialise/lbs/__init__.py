from typing import Callable, Optional, TypeVar

from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs import (
    LBS,
    LBSSegmentRaw,
    TrackSegmentType,
)

from .animation_objects import animation_objects_to_binary
from .car_location import car_location_to_binary
from .clipping_planes import clipping_planes_to_binary
from .container_objects import container_objects_to_binary
from .drive_points import drive_points_to_binary
from .interactive_objects import interactive_objects_to_binary
from .object_blocks import object_blocks_to_binary
from .geom_blocks import geom_blocks_to_binary
from .reflection_objects import reflection_objects_to_binary
from .super_bowl import super_bowl_to_binary
from .track_loader_vecs import track_loader_vecs_to_binary
from .visible_object_vecs import visible_object_vecs_to_binary
from .visible_objects import visible_objects_to_binary
from .water_objects import water_objects_to_binary


def lbs_segment_raw_to_binary(self: LBSSegmentRaw, bin: PackBin) -> None:
    bin.pack(
        "<III",
        8,
        self.track_segment_type.category().value,
        self.track_segment_type.value,
    )
    bin.pack("<I", len(self.raw_bytes))
    bin.pack_bytes(self.raw_bytes)


A = TypeVar("A")


def lbs_to_binary(self: LBS) -> bytes:
    raw_segments = self.unhandled_segments.copy()

    def optional(
        t: TrackSegmentType, b: Optional[A], f: Callable[[A, PackBin], None]
    ) -> None:
        if b is None:
            return
        else:
            bin = PackBin()
            f(b, bin)
            raw_segments[t] = bin.bytes()

    def required(t: TrackSegmentType, b: A, f: Callable[[A, PackBin], None]) -> None:
        optional(t, b, f)

    required(
        TrackSegmentType.VISIBLE_OBJECTS,
        self.world_chunks.to_visible_objects(),
        visible_objects_to_binary,
    )
    required(
        TrackSegmentType.GEOM_BLOCKS,
        self.world_chunks.to_geom_blocks(),
        geom_blocks_to_binary,
    )
    required(
        TrackSegmentType.OBJECT_BLOCKS,
        self.world_chunks.to_object_blocks(),
        object_blocks_to_binary,
    )
    optional(
        TrackSegmentType.VISIBLE_OBJECT_VECS,
        self.world_chunks.to_visible_object_vecs(),
        visible_object_vecs_to_binary,
    )
    optional(
        TrackSegmentType.CLIPPING_PLANES,
        self.clipping_planes,
        clipping_planes_to_binary,
    )
    required(
        TrackSegmentType.CAR_LOCATION,
        self.car_location,
        car_location_to_binary,
    )
    optional(
        TrackSegmentType.PC_ANIMATION_OBJECTS,
        self.animation_objects,
        animation_objects_to_binary,
    )
    optional(
        TrackSegmentType.PC_CONTAINER_OBJECTS,
        self.container_objects,
        container_objects_to_binary,
    )
    optional(
        TrackSegmentType.DRIVE_POINTS,
        self.drive_points,
        drive_points_to_binary,
    )
    optional(
        TrackSegmentType.TRACK_LOADER_VECS,
        self.track_loader_vecs,
        track_loader_vecs_to_binary,
    )
    optional(
        TrackSegmentType.INTERACTIVE_OBJECTS,
        self.interactive_objects,
        interactive_objects_to_binary,
    )
    optional(
        TrackSegmentType.REFLECTION_OBJECTS,
        self.reflection_objects,
        reflection_objects_to_binary,
    )
    optional(
        TrackSegmentType.WATER_OBJECTS,
        self.water_objects,
        water_objects_to_binary,
    )
    optional(
        TrackSegmentType.SUPER_BOWL,
        self.super_bowl,
        super_bowl_to_binary,
    )

    bin = PackBin()
    for segment_type in self.segment_order:
        if segment_type not in raw_segments:
            continue
        raw_segment = LBSSegmentRaw(
            track_segment_type=segment_type,
            raw_bytes=raw_segments[segment_type],
        )
        lbs_segment_raw_to_binary(raw_segment, bin)
    return bin.bytes()
