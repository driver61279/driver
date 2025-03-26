from __future__ import annotations
from dataclasses import dataclass
import os
from zipfile import ZipFile
from typing import Dict, Optional

import bpy  # type: ignore

from rbr_track_formats import errors
from rbr_track_formats.common import Vector2
from rbr_track_formats.dds import DXTCodec, DDS
from rbr_track_formats.ini import INI, TextureInfo, Filter
from rbr_track_formats.lbs.common import UVVelocity
from rbr_track_formats.lbs.geom_blocks import RenderType

from rbr_track_formats.logger import Logger
from rbr_track_addon.shaders.shader_node import ShaderNodeRBR
from rbr_track_addon.shaders.texture import (
    suggested_size,
    all_rbr_texture_node_trees_filename,
)
from rbr_track_addon.util import SomeUVMap


@dataclass
class RBRUnresolvedMaterial:
    """The important parts of RBR material definitions. This is a combination
    of shader node settings and material settings.
    """

    diffuse_1: Optional[str]
    diffuse_1_uv: Optional[SomeUVMap]
    diffuse_2: Optional[str]
    diffuse_2_uv: Optional[SomeUVMap]
    specular: Optional[str]
    specular_uv: Optional[SomeUVMap]
    uv_velocity: Optional[UVVelocity]
    render_type: RenderType
    use_backface_culling: bool
    transparent: bool


@dataclass
class RBRResolvedMaterial:
    """RBRUnresolvedMaterial, but with texture indices based on the
    resultant INI file"""

    # Keep track of the blender name for better error reporting
    name: str
    diffuse_1: Optional[int]
    diffuse_1_uv: Optional[SomeUVMap]
    diffuse_2: Optional[int]
    diffuse_2_uv: Optional[SomeUVMap]
    specular: Optional[int]
    specular_uv: Optional[SomeUVMap]
    uv_velocity: Optional[UVVelocity]
    render_type: RenderType
    use_backface_culling: bool
    transparent: bool


@dataclass
class RBRExportableTexture:
    """Wrap the ShaderNodeRBRTexture node tree but also includes information
    from the blender material which we need to put in the INI file
    """

    texture: str
    transparent: bool

    def get_name(self) -> str:
        """Returns a 'unique' name. Transparent and non-transparent versions of
        the same texture must be separate in the INI file and the rbz file, so
        we just append some stuff to each name."""
        s: str = self.texture + ("_T" if self.transparent else "_O") + ".dds"
        return s

    def __hash__(self) -> int:
        return (self.texture, self.transparent).__hash__()


@dataclass
class DDSBits:
    mip_levels: int
    codec: DXTCodec

    @staticmethod
    def from_dds(dds: DDS) -> DDSBits:
        return DDSBits(
            mip_levels=dds.mip_levels if dds.mip_levels is not None else 0,
            codec=dds.codec,
        )


class RBRExportTextureOracle:
    logger: Logger
    unresolved_materials: Dict[str, RBRUnresolvedMaterial]
    textures_to_export: Dict[RBRExportableTexture, int]
    specular_textures_to_export: Dict[str, int]

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.unresolved_materials = dict()
        self.textures_to_export = dict()
        self.specular_textures_to_export = dict()
        self.__setup__()

    def __setup__(self) -> None:
        # Get user defined RBR textures
        # Get all RBR materials, indexed by blender material name
        for material in bpy.data.materials:
            if not material.use_nodes:
                self.logger.info(f"Ignoring non-node based material {material.name}")
                continue
            node_tree = material.node_tree
            # Find the output node
            for node in node_tree.nodes:
                # Pick the first eevee output. This seems to match blender
                # behavior. is_active_output cannot be used because it can be
                # false for all eevee outputs if the cycles output is selected.
                if node.type == "OUTPUT_MATERIAL" and (
                    node.target == "EEVEE" or node.target == "ALL"
                ):
                    output = node
                    break
            else:
                self.logger.info(f"Ignoring material without output {material.name}")
                continue
            # Find the shader node connected to the output
            for link in node_tree.links:
                if link.to_node == output:
                    shader = link.from_node
                    break
            else:
                self.logger.info(f"No linked shader found in material {material.name}")
                continue
            if not isinstance(shader, ShaderNodeRBR):
                self.logger.info(
                    f"Linked shader is not an RBR shader in material {material.name}"
                )
                continue

            # Walk to each texture
            (diffuse_1, diffuse_1_uv, uv_velocity_1) = shader.walk_to_texture(
                material=material,
                input_name="Diffuse Texture 1",
            )
            (diffuse_2, diffuse_2_uv, uv_velocity_2) = shader.walk_to_texture(
                material=material,
                input_name="Diffuse Texture 2",
            )
            (specular, specular_uv, uv_velocity_spec) = shader.walk_to_texture(
                material=material,
                input_name="Specular Texture",
            )

            self.logger.debug(
                f"Material {material.name}, D1 {diffuse_1}, D2 {diffuse_2}"
            )
            if (
                uv_velocity_1 is None
                and uv_velocity_2 is None
                and uv_velocity_spec is None
            ):
                uv_velocity = None
            else:
                uv_velocity = UVVelocity(
                    diffuse_1=(
                        uv_velocity_1 if uv_velocity_1 is not None else Vector2(0, 0)
                    ),
                    diffuse_2=(
                        uv_velocity_2 if uv_velocity_2 is not None else Vector2(0, 0)
                    ),
                    specular=(
                        uv_velocity_spec
                        if uv_velocity_spec is not None
                        else Vector2(0, 0)
                    ),
                )
            unresolved = RBRUnresolvedMaterial(
                diffuse_1=diffuse_1,
                diffuse_1_uv=diffuse_1_uv,
                diffuse_2=diffuse_2,
                diffuse_2_uv=diffuse_2_uv,
                specular=specular,
                specular_uv=specular_uv,
                uv_velocity=uv_velocity,
                render_type=shader.calculate_render_type(),
                use_backface_culling=material.use_backface_culling,
                transparent=material.blend_method != "OPAQUE",
            )
            if unresolved.diffuse_1 is not None:
                if unresolved.diffuse_1_uv is None:
                    raise errors.E0120(
                        texture_type="Diffuse 1", material_name=material.name
                    )
            if unresolved.diffuse_2 is not None:
                if unresolved.diffuse_2_uv is None:
                    raise errors.E0120(
                        texture_type="Diffuse 2", material_name=material.name
                    )
            if unresolved.specular is not None:
                if unresolved.specular is None:
                    raise errors.E0120(
                        texture_type="Specular", material_name=material.name
                    )
            self.unresolved_materials[material.name] = unresolved

    def resolve_material(
        self, blender_material_name: str
    ) -> Optional[RBRResolvedMaterial]:
        """Call this when exporting part of a mesh."""
        try:
            unresolved = self.unresolved_materials[blender_material_name]

            def resolve_texture(texture: Optional[str]) -> Optional[int]:
                if texture is None:
                    return None
                exportable = RBRExportableTexture(
                    texture=texture,
                    transparent=unresolved.transparent,
                )
                self.logger.debug(f"resolve_texture {texture}")
                try:
                    return self.textures_to_export[exportable]
                except KeyError:
                    i = len(self.textures_to_export)
                    self.textures_to_export[exportable] = i
                    return i

            def resolve_specular_texture(texture: Optional[str]) -> Optional[int]:
                if texture is None:
                    return None
                try:
                    return self.specular_textures_to_export[texture]
                except KeyError:
                    i = len(self.specular_textures_to_export)
                    self.specular_textures_to_export[texture] = i
                    return i

            self.logger.debug(f"Resolve material {blender_material_name}")
            return RBRResolvedMaterial(
                name=blender_material_name,
                diffuse_1=resolve_texture(unresolved.diffuse_1),
                diffuse_1_uv=unresolved.diffuse_1_uv,
                diffuse_2=resolve_texture(unresolved.diffuse_2),
                diffuse_2_uv=unresolved.diffuse_2_uv,
                specular=resolve_specular_texture(unresolved.specular),
                specular_uv=unresolved.specular_uv,
                uv_velocity=unresolved.uv_velocity,
                render_type=unresolved.render_type,
                use_backface_culling=unresolved.use_backface_culling,
                transparent=unresolved.transparent,
            )
        except KeyError:
            self.logger.warn(f"Ignoring non RBR material {blender_material_name}")
            return None

    def export_textures_ini(self, rbz: ZipFile, rbz_name: str) -> INI:
        texture_node_group_dict = dict(all_rbr_texture_node_trees_filename())

        def handle_image(
            dir: str,
            node_name: str,
            rbr_texture_name: str,
        ) -> Optional[DDS]:
            rbr_texture = texture_node_group_dict[rbr_texture_name]
            image_node = rbr_texture.nodes.get(node_name)
            if image_node is None:
                return None
            image = image_node.image
            if image is None:
                return None
            if image.packed_file is not None:
                raise errors.E0121(image_name=image.name)
            [width, height] = image.size
            ideal_width = suggested_size(width)
            ideal_height = suggested_size(height)
            if ideal_width != width or ideal_height != height:
                raise errors.E0122(
                    image_name=image.name,
                    texture_name=rbr_texture_name,
                    ideal_width=ideal_width,
                    ideal_height=ideal_height,
                )

            if image.library is not None and image.filepath.startswith("//"):
                abs_library_path = bpy.path.abspath(image.library.filepath)
                abs_library_dir = os.path.dirname(abs_library_path)
                # Must drop the // prefix on image.filepath
                dds_path: str = os.path.join(abs_library_dir, image.filepath[2:])
            else:
                dds_path = bpy.path.abspath(image.filepath)
            try:
                dds = DDS.from_file(dds_path)
                rbz.write(dds_path, os.path.join(rbz_name, dir, name))
            except FileNotFoundError:
                raise errors.E0123(
                    texture_variant=dir,
                    texture_name=rbr_texture_name,
                    image_name=image.name,
                    expected_path=dds_path,
                )
            return dds

        self.logger.debug(
            f"textures_to_export {[t.texture for t in self.textures_to_export.keys()]}"
        )
        textures = []
        for exportable_rbr_texture in self.textures_to_export:
            rbr_texture_name = exportable_rbr_texture.texture
            name = exportable_rbr_texture.get_name()
            self.logger.debug(f"Exportable texture {rbr_texture_name} {name}")

            rbr_texture = texture_node_group_dict[rbr_texture_name]
            dds_settings = None
            # TODO don't write duplicates in subfolders
            is_road_surface = rbr_texture.nodes["internal"].is_road_surface
            if is_road_surface:
                dds_params = []
                dds_params.append(handle_image("dry/new", "dry/new", rbr_texture_name))
                dds_params.append(
                    handle_image("damp/new", "damp/new", rbr_texture_name)
                )
                dds_params.append(handle_image("wet/new", "wet/new", rbr_texture_name))
                dds_params.append(
                    handle_image("dry/normal", "dry/normal", rbr_texture_name)
                )
                dds_params.append(
                    handle_image("damp/normal", "damp/normal", rbr_texture_name)
                )
                dds_params.append(
                    handle_image("wet/normal", "wet/normal", rbr_texture_name)
                )
                dds_params.append(
                    handle_image("dry/worn", "dry/worn", rbr_texture_name)
                )
                dds_params.append(
                    handle_image("damp/worn", "damp/worn", rbr_texture_name)
                )
                dds_params.append(
                    handle_image("wet/worn", "wet/worn", rbr_texture_name)
                )
                for dds in dds_params:
                    if dds is None:
                        continue
                    dds_bits = DDSBits.from_dds(dds)
                    if dds_settings is not None:
                        if dds_settings != dds_bits:
                            raise errors.E0124(texture_name=rbr_texture_name)
                    dds_settings = dds_bits
            else:
                dds_params = []
                dds_params.append(handle_image("dry", "dry/new", rbr_texture_name))
                dds_params.append(handle_image("damp", "damp/new", rbr_texture_name))
                dds_params.append(handle_image("wet", "wet/new", rbr_texture_name))
                dds_settings = None
                for dds in dds_params:
                    if dds is None:
                        continue
                    dds_bits = DDSBits.from_dds(dds)
                    if dds_settings is not None:
                        if dds_settings != dds_bits:
                            raise errors.E0124(texture_name=rbr_texture_name)
                    dds_settings = dds_bits

            if dds_settings is None:
                raise errors.E0125(texture_name=rbr_texture_name)
            if rbr_texture.nodes["internal"].override_mip_levels:
                mip_levels = rbr_texture.nodes["internal"].mip_levels
            else:
                mip_levels = dds_settings.mip_levels
            textures.append(
                (
                    name,
                    TextureInfo(
                        mip_levels=mip_levels,
                        opacity_map=exportable_rbr_texture.transparent,
                        one_bit_opacity=False,  # TODO
                        is_road_surface_texture=is_road_surface,
                        mip_filter=Filter.LINEAR,
                        min_filter=Filter.POINT,
                        mag_filter=Filter.POINT,
                        texture_format=dds_settings.codec,
                    ),
                )
            )

        specular_textures = []
        for rbr_specular_texture_name in self.specular_textures_to_export:
            name = rbr_specular_texture_name + ".dds"
            # TODO don't write duplicates in subfolders
            handle_image("dry", "dry/new", rbr_specular_texture_name)
            handle_image("damp", "damp/new", rbr_specular_texture_name)
            handle_image("wet", "wet/new", rbr_specular_texture_name)
            specular_textures.append(name)

        return INI(
            textures=textures,
            specular_textures=specular_textures,
            shadow_textures=[],  # TODO
        )
