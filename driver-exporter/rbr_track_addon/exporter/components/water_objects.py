from typing import List, Optional

from rbr_track_formats.lbs.water_objects import (
    WaterObject,
    WaterObjects,
)

from rbr_track_addon.blender_ops import (
    duplicate_objects,
    apply_transforms,
    make_data_single_user,
    apply_modifiers,
    separate_by_material,
    TracedObject,
)
from rbr_track_formats.logger import Logger
from rbr_track_addon.object_settings.types import RBRObjectSettings, RBRObjectType

from .data_3d import (
    create_super_data3d,
    fixup_data_triangles_dtype,
    recursive_split,
)
from .textures import RBRExportTextureOracle
from ..util import create_supers_with


def export_water_objects(
    export_texture_oracle: RBRExportTextureOracle,
    logger: Logger,
    traced_input_objs: List[TracedObject],
) -> Optional[WaterObjects]:
    logger.info("Duplicating objects")
    dupes = duplicate_objects(traced_objs=traced_input_objs)

    logger.info("Applying modifiers")
    for obj in dupes:
        ros: RBRObjectSettings = obj.obj.rbr_object_settings
        ros.type = RBRObjectType.NONE.name
        make_data_single_user(obj)
        apply_modifiers(obj)
    apply_transforms(dupes)

    logger.info("Creating water objects")
    water_objects = []
    for obj in dupes:
        separated = separate_by_material([obj])

        data_3ds = create_supers_with(
            f=lambda m, o: create_super_data3d(
                logger=logger,
                rbr_material=m,
                traced_obj=o,
                supports_specular=True,
                supports_untextured=False,
            ),
            export_texture_oracle=export_texture_oracle,
            traced_objs=separated,
        )

        fixed_data_3ds = []
        for data_3d in data_3ds:
            split_data_3ds = recursive_split(
                logger=logger,
                data=data_3d,
            )
            for split_data_3d in split_data_3ds:
                fixed_data_3ds.append(fixup_data_triangles_dtype(split_data_3d))

        water_objects.append(
            WaterObject(
                name=obj.obj.name,
                data_3d=fixed_data_3ds,
            )
        )

    if len(water_objects) > 0:
        return WaterObjects(objects=water_objects)
    else:
        return None
