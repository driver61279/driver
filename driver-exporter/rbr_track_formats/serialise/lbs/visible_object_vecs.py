from rbr_track_formats import errors
from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.visible_object_vecs import (
    VisibleObjectVec,
    VisibleObjectVecs,
)

from ..common import vector3_to_binary


def visible_object_vec_to_binary(self: VisibleObjectVec, bin: PackBin) -> None:
    if len(self.vecs) != 5:
        raise errors.E0091(expected_length=5, actual_length=len(self.vecs))
    for vec in self.vecs:
        vector3_to_binary(vec, bin)


def visible_object_vecs_to_binary(self: VisibleObjectVecs, bin: PackBin) -> None:
    for vec in self.vecs:
        visible_object_vec_to_binary(vec, bin)
