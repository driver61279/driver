from typing import List, Optional

from rbr_track_formats.common import (
    compute_bounding_box_from_positions,
)
from rbr_track_formats.lbs.super_bowl import (
    SuperBowl,
    SuperBowlObject,
)

from rbr_track_addon.blender_ops import prepare_objs, TracedObject
from rbr_track_formats.logger import Logger

from .data_3d import (
    create_super_data3d,
    fixup_data_triangles_dtype,
    recursive_split,
)
from .textures import RBRExportTextureOracle
from ..util import create_supers_with


def export_super_bowl(
    export_texture_oracle: RBRExportTextureOracle,
    logger: Logger,
    traced_objs: List[TracedObject],
) -> Optional[SuperBowl]:
    dupes = prepare_objs(
        logger=logger,
        traced_objs=traced_objs,
        normalise=lambda _: None,
        extra_group=lambda _: None,
    )
    data_3ds = create_supers_with(
        # Specular crashes the game here
        f=lambda m, o: create_super_data3d(
            logger=logger,
            rbr_material=m,
            traced_obj=o,
            supports_specular=False,
            supports_untextured=True,
        ),
        export_texture_oracle=export_texture_oracle,
        traced_objs=dupes,
    )
    super_bowl_objects = []
    for data_3d in data_3ds:
        split_data_3ds = recursive_split(
            logger=logger,
            data=data_3d,
        )
        for split_data_3d in split_data_3ds:
            bounding_box = compute_bounding_box_from_positions(
                split_data_3d.vertices["position"],
            )
            super_bowl_objects.append(
                SuperBowlObject(
                    position=bounding_box.position,
                    data_3d=fixup_data_triangles_dtype(split_data_3d),
                )
            )
    if len(super_bowl_objects) > 0:
        return SuperBowl(
            name="SuperBowl",
            objects=super_bowl_objects,
        )
    else:
        return None
