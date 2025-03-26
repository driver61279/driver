from typing import List, Optional

from rbr_track_formats.lbs.reflection_objects import (
    ReflectionObject,
    ReflectionObjects,
)

from rbr_track_addon.blender_ops import (
    apply_modifiers,
    apply_transforms,
    make_data_single_user,
    separate_by_material,
    duplicate_objects,
    TracedObject,
)
from rbr_track_addon.object_settings.types import RBRObjectSettings, RBRObjectType
from rbr_track_formats.logger import Logger

from .data_3d import (
    create_super_data3d,
    fixup_data_triangles_dtype,
    recursive_split,
)
from .textures import RBRExportTextureOracle
from ..util import create_supers_with


def export_reflection_objects(
    export_texture_oracle: RBRExportTextureOracle,
    logger: Logger,
    traced_objs: List[TracedObject],
) -> Optional[ReflectionObjects]:
    logger.info("Duplicating objects")
    dupes = duplicate_objects(traced_objs=traced_objs)

    logger.info("Applying modifiers")
    for traced_obj in dupes:
        ros: RBRObjectSettings = traced_obj.obj.rbr_object_settings
        ros.type = RBRObjectType.NONE.name
        make_data_single_user(traced_obj)
        apply_modifiers(traced_obj)
    apply_transforms(dupes)

    logger.info("Creating reflection objects")
    reflection_objects = []
    for traced_obj in dupes:
        separated = separate_by_material([traced_obj])

        data_3ds = create_supers_with(
            f=lambda m, o: create_super_data3d(
                logger=logger,
                rbr_material=m,
                traced_obj=o,
                supports_specular=False,
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

        reflection_objects.append(
            ReflectionObject(
                name=traced_obj.obj.name,
                data_3d=fixed_data_3ds,
            )
        )

    if len(reflection_objects) > 0:
        return ReflectionObjects(objects=reflection_objects)
    else:
        return None
