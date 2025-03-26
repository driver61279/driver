"""Fence data file.
This is a placeholder until fences are fully supported.
The game requires the fence data file to be present - without it, the game will
render the car shadow without accounting for the fog, and particles might not
work.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List
import dataclasses
import enum

from .common import Vector3, AaBbBoundingBox


class FenceType(enum.Enum):
    FENCE_TAPE = 0x0
    FENCE_TAPE_LONG = 0x1
    FENCE_NET = 0x2
    FENCE_NET_LONG = 0x3
    FENCE_TAPE_POLE_GREY = 0x4
    FENCE_NET_POLE_GREY = 0x5
    FENCE_TAPE_POLE_BLACK = 0x6
    FENCE_NET_POLE_BLACK = 0x7
    FENCE_TAPE_POLE_BLUE = 0x8
    FENCE_NET_POLE_BLUE = 0x9
    FENCE_TAPE_POLE_RED = 0xA
    FENCE_NET_POLE_RED = 0xB
    FENCE_BARBED_WIRE = 0xC
    FENCE_BARBED_WIRE_LONG = 0xD
    FENCE_BARBED_WIRE_POLE = 0xE

    def pretty(self) -> str:
        return self.name.replace("_", " ").title()


@dataclass
class BGRAColor:
    r: int
    g: int
    b: int
    a: int


@dataclass
class FencePost:
    position: Vector3
    # Covers this post to the next
    bounding_box: AaBbBoundingBox
    color: BGRAColor


@dataclass
class FenceData:
    tile_type: FenceType
    pole_type: FenceType
    tile_texture_index: int
    pole_texture_index: int
    bounding_box: AaBbBoundingBox
    fence_posts: List[FencePost]


class FenceTexture(str, enum.Enum):
    POLE_AR = "ar_fencestolpe"
    POLE_AU = "au_fencestolpe"
    POLE_BR = "br_fencestolpe"
    POLE_HO = "ho_fencestolpe"
    POLE_MB = "mb_fencestolpe"
    POLE_RS = "rs_fencestolpe"
    POLE_US = "us_fencestolpe"
    POLE_BARBED = "barbed_wire_stolpe"
    POLE_BLACK = "fence_pole_black"
    POLE_BLUE = "fence_pole_blue"
    POLE_GREY = "fence_pole_grey"
    POLE_RED = "fence_pole_red"
    POLE_SIGNS_ROAD = "signs_road"

    TILE_TAPE_AR = "ar_fence_tile"
    TILE_TAPE_AU = "au_fence_tile"
    TILE_TAPE_BR = "br_fence_tile"
    TILE_TAPE_HO = "ho_fence_tile"
    TILE_TAPE_MB = "mb_fence_tile"
    TILE_TAPE_RS = "rs_fence_tile"
    TILE_TAPE_US = "us_fence_tile"
    TILE_TAPE_DIAG_STRIPE_RED_WHITE = "fence_tile02"
    TILE_TAPE_BLUE = "fence_tile03"
    TILE_TAPE_YELLOW = "fence_tile04"
    TILE_TAPE_ORANGE = "fence_tile06"
    TILE_NET_ORANGE = "fence_tile01"
    TILE_NET_BLUE = "fence_tile05"
    TILE_BARBED = "barbed_wire_tile"


@dataclass
class FNC:
    fences: List[FenceData]
    textures: List[FenceTexture]
    __textures_garbage__: List[bytes] = dataclasses.field(default_factory=lambda: [])
