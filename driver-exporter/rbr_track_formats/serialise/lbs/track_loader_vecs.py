from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.track_loader_vecs import TrackLoaderVecs

from ..common import vector3_to_binary


def track_loader_vecs_to_binary(self: TrackLoaderVecs, bin: PackBin) -> None:
    vector3_to_binary(self.a, bin)
    vector3_to_binary(self.b, bin)
