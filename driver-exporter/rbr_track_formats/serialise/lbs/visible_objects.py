from rbr_track_formats.binary import PackBin
from rbr_track_formats.lbs.visible_objects import VisibleObjects

from ..common import aabb_bounding_box_to_binary


def visible_objects_to_binary(self: VisibleObjects, bin: PackBin) -> None:
    bin.pack("<I", len(self.bounding_boxes))
    for obj in self.bounding_boxes:
        aabb_bounding_box_to_binary(obj, bin)
