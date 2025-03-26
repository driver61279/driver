"""INI files contain information about track textures
"""

from __future__ import annotations
from configparser import ConfigParser, DuplicateSectionError, SectionProxy
from dataclasses import dataclass
from typing import Dict, List, Tuple
import enum
import io

from .dds import DXTCodec


class Filter(str, enum.Enum):
    NONE = "None"
    POINT = "Point"
    LINEAR = "Linear"
    ANISOTROPIC = "Anisotropic"


@dataclass
class TextureInfo:
    """
    TextureInfo encapsulates settings for an individual texture file.

    mip_levels
        Number of mipmap levels. If the value is zero or -1, a complete mipmap
        chain is generated.
    opacity_map
        Use alpha channel of texture as opacity. Set to False for DXT1, True
        otherwise.
    is_road_surface_texture
        Road surface textures are found in new/normal/worn subdirectories
    mip_filter
        Mipmap filter
    min_filter
        Mipmap min filter
    mag_filter
        Mipmap mag filter
    texture_format
        DXT compression codec
    one_bit_opacity
        Only relevant if opacity_map is True
        TODO is this important? It is usually False.
    dynamic
        Unused by the game
    """

    mip_levels: int
    opacity_map: bool
    is_road_surface_texture: bool
    mip_filter: Filter
    min_filter: Filter
    mag_filter: Filter
    texture_format: DXTCodec
    one_bit_opacity: bool = False
    dynamic: bool = False

    @staticmethod
    def from_ini(section: SectionProxy) -> TextureInfo:
        return TextureInfo(
            mip_levels=section.getint("MipLevels"),
            dynamic=section.getboolean("Dynamic"),
            opacity_map=section.getboolean("OpacityMap"),
            one_bit_opacity=section.getboolean("OneBitOpacity"),
            is_road_surface_texture=section.getboolean("IsGroundTexture"),
            mip_filter=Filter(section.get("MipFilter")),
            min_filter=Filter(section.get("MinFilter")),
            mag_filter=Filter(section.get("MagFilter")),
            texture_format=DXTCodec[section.get("TextureFormat")],
        )

    def to_ini(self) -> Dict[str, str]:
        return {
            "MipLevels": str(self.mip_levels),
            "Dynamic": str(self.dynamic).lower(),
            "OpacityMap": str(self.opacity_map).lower(),
            "OneBitOpacity": str(self.one_bit_opacity).lower(),
            "IsGroundTexture": str(self.is_road_surface_texture).lower(),
            "MipFilter": self.mip_filter.value,
            "MinFilter": self.min_filter.value,
            "MagFilter": self.mag_filter.value,
            "TextureFormat": self.texture_format.name,
        }


@dataclass
class INI:
    """
    INI files contain information about track textures.

    textures
        General texture data. The left side of the tuple is the file name, the
        right side is extra information.
    shadow_textures
        File names of shadow textures. These files should be at the top level,
        with the dry/damp/wet folders.
    specular_textures
        File names of specular textures. These files should be in the
        dry/damp/wet folders.
    """

    textures: List[Tuple[str, TextureInfo]]
    shadow_textures: List[str]
    specular_textures: List[str]

    @staticmethod
    def from_ini(raw: str) -> INI:
        config = ConfigParser(strict=False)
        config.read_string(raw)
        texture_info = config["TextureInfo"]
        num_textures = texture_info.getint("NumTextures")
        textures = []
        for i in range(num_textures):
            texture_file = texture_info.get("Texture" + str(i))
            info = config[texture_file]
            textures.append((texture_file, TextureInfo.from_ini(info)))
        num_shadow_textures = texture_info.getint("NumShadowTextures")
        if num_shadow_textures is None:
            num_shadow_textures = 0
        shadow_textures = []
        for i in range(num_shadow_textures):
            shadow_texture_file = texture_info.get("ShadowTexture" + str(i))
            shadow_textures.append(shadow_texture_file)
        num_specular_textures = texture_info.getint("NumSpecularTextures")
        if num_specular_textures is None:
            num_specular_textures = 0
        specular_textures = []
        for i in range(num_specular_textures):
            specular_texture_file = texture_info.get("SpecularTexture" + str(i))
            specular_textures.append(specular_texture_file)
        return INI(
            textures=textures,
            shadow_textures=shadow_textures,
            specular_textures=specular_textures,
        )

    def to_ini(self) -> str:
        config = ConfigParser()
        config.optionxform = lambda x: x  # type: ignore
        config.add_section("TextureInfo")
        config.set("TextureInfo", "NumTextures", str(len(self.textures)))
        for i, (texture, _) in enumerate(self.textures):
            config.set("TextureInfo", "Texture" + str(i), texture)
        config.set("TextureInfo", "NumShadowTextures", str(len(self.shadow_textures)))
        for i, shadow_texture in enumerate(self.shadow_textures):
            config.set("TextureInfo", "ShadowTexture" + str(i), shadow_texture)
        config.set(
            "TextureInfo", "NumSpecularTextures", str(len(self.specular_textures))
        )
        for i, specular_texture in enumerate(self.specular_textures):
            config.set("TextureInfo", "SpecularTexture" + str(i), specular_texture)
        for texture, info in self.textures:
            try:
                config.add_section(texture)
                for k, v in info.to_ini().items():
                    config.set(texture, k, v)
            except DuplicateSectionError:
                continue
        output = io.StringIO()
        config.write(output, space_around_delimiters=False)
        contents = output.getvalue()
        output.close()
        return contents
