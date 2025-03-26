from dataclasses import dataclass
from typing import Callable, List, TypeVar

from rbr_track_formats import errors
from rbr_track_formats.common import Key

from rbr_track_addon.blender_ops import TracedObject
from .components.textures import RBRResolvedMaterial, RBRExportTextureOracle


@dataclass
class KeyGen:
    last_key: int = 1

    def new_key(self) -> Key:
        self.last_key += 1
        return Key(id=self.last_key)


A = TypeVar("A")


def create_supers_with(
    f: Callable[[RBRResolvedMaterial, TracedObject], A],
    export_texture_oracle: RBRExportTextureOracle,
    traced_objs: List[TracedObject],
) -> List[A]:
    result = []
    for traced_obj in traced_objs:
        obj = traced_obj.obj
        material_name = obj.data.materials[0].name
        rbr_material = export_texture_oracle.resolve_material(material_name)
        if rbr_material is None:
            raise errors.E0104(
                object_name=traced_obj.source_name(),
                material_name=material_name,
            )
        result.append(f(rbr_material, traced_obj))
    return result
