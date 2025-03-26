from typing import List, Tuple

from rbr_track_formats import errors
from rbr_track_formats.common import Vector3
from rbr_track_formats.col import WaterSurface

from rbr_track_addon.blender_ops import (
    apply_transforms,
    copy_visual_geometry_to_meshes,
    TracedObject,
)
from rbr_track_addon.object_settings.types import RBRObjectSettings, WetSurfaceKind
from rbr_track_formats.logger import Logger


def export_wet_surfaces(
    logger: Logger,
    traced_objs: List[TracedObject],
) -> Tuple[List[WaterSurface], List[WaterSurface]]:
    logger.info(f"{len(traced_objs)} source objects")
    dupes = copy_visual_geometry_to_meshes(traced_objs)
    apply_transforms(dupes)
    wet_surfaces = []
    water_surfaces = []
    for obj in dupes:
        settings: RBRObjectSettings = obj.obj.rbr_object_settings
        kind = WetSurfaceKind[settings.wet_surface_kind]
        surfaces = export_wet_surface(logger, obj)
        if kind is WetSurfaceKind.WET:
            wet_surfaces.extend(surfaces)
        elif kind is WetSurfaceKind.WATER:
            water_surfaces.extend(surfaces)
        else:
            raise errors.RBRAddonBug(f"Unhandled case in export_wet_surfaces: {kind}")
    logger.info(
        f"Exported {len(wet_surfaces)} wet surfaces and {len(water_surfaces)} water surfaces"
    )
    return (wet_surfaces, water_surfaces)


def export_wet_surface(
    logger: Logger,
    traced_ob: TracedObject,
) -> List[WaterSurface]:
    mesh = traced_ob.obj.data
    surfaces = []
    for poly in mesh.polygons:
        if len(poly.vertices) != 4:
            raise errors.E0157(object_name=traced_ob.source_name())

        def f(idx: int) -> Vector3:
            v = mesh.vertices[idx]
            if len(v.co) != 3:
                raise errors.RBRAddonBug(
                    f"export_wet_surface: unexpected vector size {len(v.co)}"
                )
            return Vector3(
                x=v.co[0],
                y=v.co[1],
                z=v.co[2],
            )

        surfaces.append(
            WaterSurface(
                a=f(poly.vertices[3]),
                b=f(poly.vertices[2]),
                c=f(poly.vertices[1]),
                d=f(poly.vertices[0]),
            )
        )
    return surfaces
