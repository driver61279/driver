"""The track settings file contains all weather settings for every track.
"""

from __future__ import annotations
from configparser import SectionProxy
from dataclasses import dataclass
from typing import Dict, List, Optional
import enum
import re

from . import errors
from .common import Vector3


class CloudName(str, enum.Enum):
    CLEAR = "Us_clear"
    CLEAR02 = "Us_clear02"
    CLOUDED = "Us_clouded"
    CLOUDED02 = "Us_clouded02"
    OVERCAST = "Us_overcast"
    OVERCAST02 = "Us_overcast02"
    PARTLY_CLOUDED = "Us_partly_clouded"
    PARTLY_CLOUDED02 = "Us_partly_clouded02"
    PRECIPITATION = "Us_precipitation"
    PRECIPITATION_PC = "Us_precipitation_pc"
    PRECIPITATION02_PC = "Us_precipitation02_pc"

    @staticmethod
    def from_ini(section: SectionProxy) -> Optional[CloudName]:
        s = section.get("CloudName")
        if s is not None:
            return CloudName(s)
        return None

    def to_ini(self) -> str:
        return self.value

    def pretty(self) -> str:
        return self.name.replace("_", " ").title()

    def id(self) -> int:
        # Be careful when changing this, blend files use it.
        return list(CloudName).index(self)


@dataclass
class RGBColor:
    red: float
    green: float
    blue: float

    @staticmethod
    def from_ini(prefix: str, section: SectionProxy) -> Optional[RGBColor]:
        red = section.getfloat(prefix + "Red")
        green = section.getfloat(prefix + "Green")
        blue = section.getfloat(prefix + "Blue")
        if None not in [red, green, blue]:
            return RGBColor(
                red=red,
                green=green,
                blue=blue,
            )
        return None

    def to_ini(self, prefix: str) -> Dict[str, str]:
        return {
            (prefix + "Red"): f"{self.red:f}",
            (prefix + "Green"): f"{self.green:f}",
            (prefix + "Blue"): f"{self.blue:f}",
        }

    @staticmethod
    def from_list(cols: List[float]) -> Optional[RGBColor]:
        try:
            return RGBColor(
                red=cols[0],
                green=cols[1],
                blue=cols[2],
            )
        except IndexError:
            return None

    def to_list(self) -> List[float]:
        return [self.red, self.green, self.blue]


@dataclass
class TrackSettings:
    ambient: Optional[RGBColor] = None
    car_ambient_lighting: Optional[float] = None
    car_diffuse_lighting: Optional[float] = None
    car_deep_shadow_alpha: Optional[float] = None
    car_shadow_alpha: Optional[float] = None
    character_lighting: Optional[float] = None
    cloud_name: Optional[CloudName] = None
    cloud_scale: Optional[float] = None
    extinction: Optional[float] = None
    fog_color: Optional[RGBColor] = None
    fog_end: Optional[float] = None
    fog_start: Optional[float] = None
    greenstein_value: Optional[float] = None
    inscattering: Optional[float] = None
    mie_multiplier: Optional[float] = None
    mipmapbias: Optional[float] = None
    particle_lighting: Optional[float] = None
    rayleigh_multiplier: Optional[float] = None
    skybox_saturation: Optional[float] = None
    skybox_scale: Optional[float] = None
    specular_alpha: Optional[float] = None
    specular_glossiness: Optional[float] = None
    sun_dir: Optional[Vector3] = None
    sun_intensity: Optional[float] = None
    sun_offset: Optional[float] = None
    superbowl_fog_end: Optional[float] = None
    superbowl_fog_start: Optional[float] = None
    superbowl_scale: Optional[float] = None
    terrain_reflectance: Optional[float] = None
    terrain_reflectance_color: Optional[RGBColor] = None
    turbidity: Optional[float] = None
    use_fog: Optional[bool] = None

    @staticmethod
    def from_ini(section: SectionProxy) -> TrackSettings:
        def optional_float(key: str) -> Optional[float]:
            value = section.get(key)
            if value is None:
                return None
            else:
                try:
                    return float(value.split()[0])
                except ValueError:
                    return None

        raw_sun_dir = section.get("SunDir")
        if raw_sun_dir is not None:
            sun_dir = Vector3.parse_ini_string(raw_sun_dir)
        else:
            sun_dir = None

        return TrackSettings(
            ambient=RGBColor.from_ini("Ambient", section),
            car_ambient_lighting=optional_float("Car_Ambient_Lighting"),
            car_diffuse_lighting=optional_float("Car_Diffuse_Lighting"),
            car_deep_shadow_alpha=optional_float("Car_Deep_Shadow_Alpha"),
            car_shadow_alpha=optional_float("Car_Shadow_Alpha"),
            character_lighting=optional_float("Character_Lighting"),
            cloud_name=CloudName.from_ini(section),
            cloud_scale=optional_float("Cloud_Scale"),
            extinction=optional_float("Extinction"),
            fog_color=RGBColor.from_ini("Fog", section),
            fog_end=optional_float("FogEnd"),
            fog_start=optional_float("FogStart"),
            greenstein_value=optional_float("Greenstein_Value"),
            inscattering=optional_float("Inscattering"),
            mie_multiplier=optional_float("Mie_Multiplier"),
            mipmapbias=optional_float("MipMapBias"),
            particle_lighting=optional_float("Particle_Lighting"),
            rayleigh_multiplier=optional_float("Rayleigh_Multiplier"),
            skybox_saturation=optional_float("SkyboxSaturation"),
            skybox_scale=optional_float("Skybox_Scale"),
            specular_alpha=optional_float("Specular_Alpha"),
            specular_glossiness=optional_float("Specular_Glossiness"),
            sun_dir=sun_dir,
            sun_intensity=optional_float("Sun_Intensity"),
            sun_offset=optional_float("SunOffset"),
            superbowl_fog_end=optional_float("SuperbowlFogEnd"),
            superbowl_fog_start=optional_float("SuperbowlFogStart"),
            superbowl_scale=optional_float("Superbowl_Scale"),
            terrain_reflectance=optional_float("Terrain_Reflectance"),
            terrain_reflectance_color=RGBColor.from_ini(
                "Terrain_Reflectance_", section
            ),
            turbidity=optional_float("Turbidity"),
            use_fog=section.getboolean("UseFog"),
        )

    def to_ini(self) -> Dict[str, str]:
        parts = [
            self.ambient.to_ini("Ambient") if self.ambient is not None else {},
            self.fog_color.to_ini("Fog") if self.fog_color is not None else {},
            (
                self.terrain_reflectance_color.to_ini("Terrain_Reflectance_")
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
                {"CloudName": self.cloud_name.to_ini()}
                if self.cloud_name is not None
                else {}
            ),
            (
                {"Extinction": f"{self.extinction:f}"}
                if self.extinction is not None
                else {}
            ),
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
            (
                {"MipMapBias": f"{self.mipmapbias:f}"}
                if self.mipmapbias is not None
                else {}
            ),
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
            (
                {"SunDir": self.sun_dir.to_ini_string()}
                if self.sun_dir is not None
                else {}
            ),
            (
                {"Sun_Intensity": f"{self.sun_intensity:f}"}
                if self.sun_intensity is not None
                else {}
            ),
            (
                {"SunOffset": f"{self.sun_offset:f}"}
                if self.sun_offset is not None
                else {}
            ),
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


class TintSet(str, enum.Enum):
    MORNING = "M"
    NOON = "N"
    EVENING = "E"
    OVERCAST = "O"

    def pretty(self) -> str:
        return self.name.title()

    def to_time_of_day(self) -> Optional[TimeOfDay]:
        try:
            return TimeOfDay(self.value)
        except ValueError:
            return None

    def bitmask(self) -> int:
        if self is TintSet.MORNING:
            return 0b00001
        elif self is TintSet.NOON:
            return 0b00010
        elif self is TintSet.EVENING:
            return 0b00100
        elif self is TintSet.OVERCAST:
            return 0b01000


class TimeOfDay(str, enum.Enum):
    """For use with overcast tint set"""

    MORNING = "M"
    NOON = "N"
    EVENING = "E"

    def pretty(self) -> str:
        return self.name.title()

    @staticmethod
    def from_tint_set_and_overcast_time(
        tint_set: TintSet, time_of_day: TimeOfDay
    ) -> TimeOfDay:
        if tint_set is TintSet.MORNING:
            return TimeOfDay.MORNING
        elif tint_set is TintSet.NOON:
            return TimeOfDay.NOON
        elif tint_set is TintSet.EVENING:
            return TimeOfDay.EVENING
        elif tint_set is TintSet.OVERCAST:
            return time_of_day


class Weather(str, enum.Enum):
    CRISP = "crisp"
    HAZY = "hazy"
    LIGHT_FOG = "lightfog"
    HEAVY_FOG = "heavyfog"
    NO_RAIN = "norain"
    LIGHT_RAIN = "lightrain"
    HEAVY_RAIN = "heavyrain"
    NO_SNOW = "nosnow"
    LIGHT_SNOW = "lightsnow"
    HEAVY_SNOW = "heavysnow"

    def pretty(self) -> str:
        return " ".join(self.name.split("_")).title()

    def id(self) -> int:
        if self is Weather.CRISP:
            return 0
        elif self is Weather.HAZY:
            return 1
        elif self is Weather.LIGHT_FOG:
            return 2
        elif self is Weather.HEAVY_FOG:
            return 3
        elif self is Weather.NO_RAIN:
            return 4
        elif self is Weather.LIGHT_RAIN:
            return 5
        elif self is Weather.HEAVY_RAIN:
            return 6
        elif self is Weather.NO_SNOW:
            return 7
        elif self is Weather.LIGHT_SNOW:
            return 8
        elif self is Weather.HEAVY_SNOW:
            return 9


class Sky(str, enum.Enum):
    CLEAR = "clear"
    PART_CLOUD = "partcloud"
    LIGHT_CLOUD = "lightcloud"
    HEAVY_CLOUD = "heavycloud"

    def pretty(self) -> str:
        return " ".join(self.name.split("_")).title()

    def id(self) -> int:
        if self is Sky.CLEAR:
            return 0
        elif self is Sky.PART_CLOUD:
            return 1
        elif self is Sky.LIGHT_CLOUD:
            return 2
        elif self is Sky.HEAVY_CLOUD:
            return 3


@dataclass
class TrackFileName:
    track_id: int
    tint_set: TintSet

    @staticmethod
    def parse(name: str) -> TrackFileName:
        r = re.compile(r"track-(\d+)_(\w).+")
        matched = r.match(name)
        if matched is None:
            raise errors.E0102(name=name)
        return TrackFileName(
            track_id=int(matched.group(1)),
            tint_set=TintSet(matched.group(2)),
        )

    def serialise(self) -> str:
        return "track-" + str(self.track_id) + "_" + self.tint_set.value


@dataclass
class TrackSpecification:
    track_id: int
    tint_set: TintSet
    time_of_day: TimeOfDay
    weather: Weather
    sky: Sky

    @staticmethod
    def parse(full_name: str) -> TrackSpecification:
        parts = list(reversed(full_name.split("_")))
        if not (len(parts) == 3 or len(parts) == 4):
            raise errors.E0103(name=full_name)
        number_tint = parts.pop()
        track_id = int(number_tint[:-1])
        tint_set = TintSet(number_tint[-1].upper())
        tint_time_of_day = tint_set.to_time_of_day()
        if tint_time_of_day is None:
            time_of_day = TimeOfDay(parts.pop().upper())
        else:
            time_of_day = tint_time_of_day
        weather = Weather(parts.pop())
        sky = Sky(parts.pop())
        return TrackSpecification(
            track_id=track_id,
            tint_set=tint_set,
            time_of_day=time_of_day,
            weather=weather,
            sky=sky,
        )

    def serialise(self) -> str:
        parts = [str(self.track_id) + self.tint_set.value]
        if self.tint_set.to_time_of_day() is None:
            parts.append(self.time_of_day.value)
        parts.append(self.weather.value)
        parts.append(self.sky.value)
        return "_".join(parts)

    def __hash__(self) -> int:
        return (
            self.track_id,
            self.tint_set.value,
            self.time_of_day.value,
            self.weather.value,
            self.sky.value,
        ).__hash__()


def serialise_track_settings(settings: Dict[TrackSpecification, TrackSettings]) -> str:
    lines = []
    for spec, track_settings in settings.items():
        lines.append("[" + spec.serialise() + "]")
        for k, v in track_settings.to_ini().items():
            lines.append(k + " = " + v)
        lines.append("")
    return "\n".join(lines)
