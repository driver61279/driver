from typing import Callable, TypeVar

from rbr_track_formats.binary import PackBin
from rbr_track_formats.trk import TrackSegmentType, TRKSegmentRaw, TRK

from .driveline import driveline_to_binary
from .shape_collision_meshes import shape_collision_meshes_to_binary


def trk_segment_raw_to_binary(self: TRKSegmentRaw, bin: PackBin) -> None:
    bin.pack(
        "<III",
        8,
        self.track_segment_type.category().value,
        self.track_segment_type.value,
    )
    bin.pack("<I", len(self.raw_bytes))
    bin.pack_bytes(self.raw_bytes)


A = TypeVar("A")


def trk_to_binary(self: TRK) -> bytes:
    raw_segments = self.unhandled_segments.copy()

    def required(
        t: TrackSegmentType,
        b: A,
        f: Callable[[A, PackBin], None],
    ) -> None:
        bin = PackBin()
        f(b, bin)
        raw_segments[t] = bin.bytes()

    required(
        TrackSegmentType.DRIVE_LINE,
        self.driveline,
        driveline_to_binary,
    )
    required(
        TrackSegmentType.SHAPE_COLLISION_MESHES,
        self.shape_collision_meshes,
        shape_collision_meshes_to_binary,
    )

    bin = PackBin()
    for segment_type in self.segment_order:
        if segment_type not in raw_segments:
            continue
        raw_segment = TRKSegmentRaw(
            track_segment_type=segment_type,
            raw_bytes=raw_segments[segment_type],
        )
        trk_segment_raw_to_binary(raw_segment, bin)
    return bin.bytes()
