"""Animation objects
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from rbr_track_formats.common import Vector3


@dataclass
class RGBAColor:
    r: int
    g: int
    b: int
    a: int


@dataclass
class AnimationObject:
    name: str
    animation_id: int
    randomised: int
    container_id: int
    lua_load_script_name: str
    lua_run_script_name: str
    position: Vector3
    rotation: Vector3
    scale: Vector3  # unused
    car_position: Vector3  # unused
    light: Vector3  # unused
    color: RGBAColor


@dataclass
class AnimationObjects:
    objects: List[AnimationObject]
