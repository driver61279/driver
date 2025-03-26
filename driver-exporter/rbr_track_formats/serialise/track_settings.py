from typing import Dict

from rbr_track_formats.track_settings import (
    CloudName,
    RGBColor,
    TrackSettings,
    TrackSpecification,
)


def cloud_name_to_ini(self: CloudName) -> str:
    return self.value


def rgb_color_to_ini(self: RGBColor, prefix: str) -> Dict[str, str]:
    return {
        (prefix + "Red"): f"{self.red:f}",
        (prefix + "Green"): f"{self.red:f}",
        (prefix + "Blue"): f"{self.red:f}",
    }


def track_settings_to_ini(self: TrackSettings) -> Dict[str, str]:
    parts = [
        rgb_color_to_ini(self.ambient, "Ambient") if self.ambient is not None else {},
        rgb_color_to_ini(self.fog_color, "Fog") if self.fog_color is not None else {},
        (
            rgb_color_to_ini(self.terrain_reflectance_color, "Terrain_Reflectance_")
            if self.terrain_reflectance_color is not None
            else {}
        ),
        (
            {"Car_Deep_Shadow_Alpha": f"{self.car_deep_shadow_alpha:f}"}
            if self.car_deep_shadow_alpha is not None
            else {}
        ),
        (
            {"Car_Shadow_Alpha": f"{self.car_shadow_alpha:f}"}
            if self.car_shadow_alpha is not None
            else {}
        ),
        (
            {"CloudName": cloud_name_to_ini(self.cloud_name)}
            if self.cloud_name is not None
            else {}
        ),
        {"Extinction": f"{self.extinction:f}"} if self.extinction is not None else {},
        {"FogEnd": f"{self.fog_end:f}"} if self.fog_end is not None else {},
        {"FogStart": f"{self.fog_start:f}"} if self.fog_start is not None else {},
        (
            {"Greenstein_Value": f"{self.greenstein_value:f}"}
            if self.greenstein_value is not None
            else {}
        ),
        (
            {"Inscattering": f"{self.inscattering:f}"}
            if self.inscattering is not None
            else {}
        ),
        (
            {"Mie_Multiplier": f"{self.mie_multiplier:f}"}
            if self.mie_multiplier is not None
            else {}
        ),
        {"MipMapBias": f"{self.mipmapbias:f}"} if self.mipmapbias is not None else {},
        (
            {"Rayleigh_Multiplier": f"{self.rayleigh_multiplier:f}"}
            if self.rayleigh_multiplier is not None
            else {}
        ),
        (
            {"SkyboxSaturation": f"{self.skybox_saturation:f}"}
            if self.skybox_saturation is not None
            else {}
        ),
        (
            {"Skybox_Scale": f"{self.skybox_scale:f}"}
            if self.skybox_scale is not None
            else {}
        ),
        (
            {"Specular_Alpha": f"{self.specular_alpha:f}"}
            if self.specular_alpha is not None
            else {}
        ),
        (
            {"Specular_Glossiness": f"{self.specular_glossiness:f}"}
            if self.specular_glossiness is not None
            else {}
        ),
        {"SunDir": self.sun_dir.to_ini_string()} if self.sun_dir is not None else {},
        (
            {"Sun_Intensity": f"{self.sun_intensity:f}"}
            if self.sun_intensity is not None
            else {}
        ),
        {"SunOffset": f"{self.sun_offset:f}"} if self.sun_offset is not None else {},
        (
            {"SuperbowlFogStart": f"{self.superbowl_fog_start:f}"}
            if self.superbowl_fog_end is not None
            else {}
        ),
        (
            {"Terrain_Reflectance": f"{self.terrain_reflectance:f}"}
            if self.terrain_reflectance is not None
            else {}
        ),
        {"Turbidity": f"{self.turbidity:f}"} if self.turbidity is not None else {},
        {"UseFog": str(self.use_fog).lower()} if self.use_fog is not None else {},
        (
            {"Car_Ambient_Lighting": f"{self.car_ambient_lighting:f}"}
            if self.car_ambient_lighting is not None
            else {}
        ),
        (
            {"Car_Diffuse_Lighting": f"{self.car_diffuse_lighting:f}"}
            if self.car_diffuse_lighting is not None
            else {}
        ),
        (
            {"Character_Lighting": f"{self.character_lighting:f}"}
            if self.character_lighting is not None
            else {}
        ),
        (
            {"Cloud_Scale": f"{self.cloud_scale:f}"}
            if self.cloud_scale is not None
            else {}
        ),
        (
            {"Particle_Lighting": f"{self.particle_lighting:f}"}
            if self.particle_lighting is not None
            else {}
        ),
        (
            {"SuperbowlFogEnd": f"{self.superbowl_fog_end:f}"}
            if self.superbowl_fog_end is not None
            else {}
        ),
        (
            {"Superbowl_Scale": f"{self.superbowl_scale:f}"}
            if self.superbowl_scale is not None
            else {}
        ),
    ]
    ret = dict()
    for part in parts:
        for k, v in part.items():
            ret[k] = v
    return ret


def serialise_track_settings(settings: Dict[TrackSpecification, TrackSettings]) -> str:
    lines = []
    for spec, track_settings in settings.items():
        lines.append("[" + spec.serialise() + "]")
        for k, v in track_settings_to_ini(track_settings).items():
            lines.append(k + " = " + v)
        lines.append("")
    return "\n".join(lines)
