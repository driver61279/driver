import bpy  # type: ignore
from typing import Dict, List

from rbr_track_formats.track_settings import (
    CloudName,
    serialise_track_settings,
    RGBColor,
    Sky,
    TimeOfDay,
    TrackSettings,
    TrackSpecification,
    Weather,
)

from rbr_track_addon.blender_ops import TracedObject
from rbr_track_formats.logger import Logger
from rbr_track_addon.shaders.sky import compute_left_hand_sun_dir


def export_track_settings(
    logger: Logger,
    track_id: int,
    traced_suns: List[TracedObject],
) -> str:
    result: Dict[TrackSpecification, TrackSettings] = dict()
    for scene in bpy.data.scenes:
        try:
            sun_dir = compute_left_hand_sun_dir(traced_suns[0].obj)
        except IndexError:
            sun_dir = None

        tint_set = scene.rbr_track_settings.get_tint_set()

        weather_ptrs = scene.rbr_track_settings.world_weathers
        for weather_ptr in weather_ptrs:
            world = weather_ptr.world
            if world is None:
                continue
            weather_sky = world.rbr_track_settings
            time_of_day = TimeOfDay.from_tint_set_and_overcast_time(
                tint_set, TimeOfDay[weather_ptr.overcast_time_of_day]
            )
            spec = TrackSpecification(
                track_id=track_id,
                tint_set=tint_set,
                time_of_day=time_of_day,
                weather=Weather[weather_sky.weather],
                sky=Sky[weather_sky.sky],
            )
            result[spec] = TrackSettings(
                cloud_name=CloudName[weather_sky.cloud_name],
                extinction=weather_sky.extinction,
                fog_color=RGBColor.from_list(weather_sky.fog_color),
                fog_end=weather_sky.fog_end,
                fog_start=weather_sky.fog_start,
                greenstein_value=weather_sky.greenstein_value,
                inscattering=weather_sky.inscattering,
                mie_multiplier=weather_sky.mie_multiplier,
                rayleigh_multiplier=weather_sky.rayleigh_multiplier,
                skybox_saturation=weather_sky.skybox_saturation,
                skybox_scale=weather_sky.skybox_scale,
                specular_alpha=weather_sky.specular_alpha,
                specular_glossiness=weather_sky.specular_glossiness,
                sun_dir=sun_dir,
                sun_intensity=weather_sky.sun_intensity,
                sun_offset=weather_sky.sun_offset,
                superbowl_fog_end=weather_sky.superbowl_fog_end,
                superbowl_fog_start=weather_sky.superbowl_fog_start,
                superbowl_scale=weather_sky.superbowl_scale,
                terrain_reflectance=weather_sky.terrain_reflectance_multiplier,
                terrain_reflectance_color=RGBColor.from_list(
                    weather_sky.terrain_reflectance_color
                ),
                turbidity=weather_sky.turbidity,
                use_fog=weather_sky.use_fog,
                ambient=RGBColor.from_list(weather_sky.ambient),
                car_ambient_lighting=weather_sky.car_ambient_lighting,
                car_diffuse_lighting=weather_sky.car_diffuse_lighting,
                car_deep_shadow_alpha=weather_sky.car_deep_shadow_alpha,
                car_shadow_alpha=weather_sky.car_shadow_alpha,
                character_lighting=weather_sky.character_lighting,
                cloud_scale=weather_sky.cloud_scale,
                mipmapbias=weather_sky.mipmapbias,
                particle_lighting=weather_sky.particle_lighting,
            )

    if len(result) == 0:
        logger.warn(
            "Exporting empty track settings file because there are no weathers"
            + " specified (see 'RBR Track Settings' in the scene properties)"
        )
    return serialise_track_settings(result)
