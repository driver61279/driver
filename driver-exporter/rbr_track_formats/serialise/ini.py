from configparser import ConfigParser, DuplicateSectionError
from typing import Dict
import io

from rbr_track_formats.ini import TextureInfo, INI


def texture_info_to_ini(self: TextureInfo) -> Dict[str, str]:
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


def to_ini(self: INI) -> str:
    config = ConfigParser()
    config.optionxform = lambda x: x  # type: ignore
    config.add_section("TextureInfo")
    config.set("TextureInfo", "NumTextures", str(len(self.textures)))
    for i, (texture, _) in enumerate(self.textures):
        config.set("TextureInfo", "Texture" + str(i), texture)
    config.set("TextureInfo", "NumShadowTextures", str(len(self.shadow_textures)))
    for i, shadow_texture in enumerate(self.shadow_textures):
        config.set("TextureInfo", "ShadowTexture" + str(i), shadow_texture)
    config.set("TextureInfo", "NumSpecularTextures", str(len(self.specular_textures)))
    for i, specular_texture in enumerate(self.specular_textures):
        config.set("TextureInfo", "SpecularTexture" + str(i), specular_texture)
    for texture, info in self.textures:
        try:
            config.add_section(texture)
            for k, v in texture_info_to_ini(info).items():
                config.set(texture, k, v)
        except DuplicateSectionError:
            continue
    output = io.StringIO()
    config.write(output, space_around_delimiters=False)
    contents = output.getvalue()
    output.close()
    return contents
