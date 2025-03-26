from __future__ import annotations
from typing import Tuple

import enum

from rbr_track_formats.fnc import FenceType, FenceTexture


class FenceKind(enum.Enum):
    TAPE = 0x4
    NET = 0x5
    BARBED_WIRE = 0xE

    def pretty(self) -> str:
        return self.name.replace("_", " ").title()

    def to_fence_pole_type(
        self,
        col: FencePoleNetTexture,
    ) -> FenceType:
        if self is FenceKind.TAPE:
            if col is FencePoleNetTexture.GREY:
                return FenceType.FENCE_TAPE_POLE_GREY
            elif col is FencePoleNetTexture.BLACK:
                return FenceType.FENCE_TAPE_POLE_BLACK
            elif col is FencePoleNetTexture.BLUE:
                return FenceType.FENCE_TAPE_POLE_BLUE
            elif col is FencePoleNetTexture.RED:
                return FenceType.FENCE_TAPE_POLE_RED
        elif self is FenceKind.NET:
            if col is FencePoleNetTexture.GREY:
                return FenceType.FENCE_NET_POLE_GREY
            elif col is FencePoleNetTexture.BLACK:
                return FenceType.FENCE_NET_POLE_BLACK
            elif col is FencePoleNetTexture.BLUE:
                return FenceType.FENCE_NET_POLE_BLUE
            elif col is FencePoleNetTexture.RED:
                return FenceType.FENCE_NET_POLE_RED
        elif self is FenceKind.BARBED_WIRE:
            return FenceType.FENCE_BARBED_WIRE_POLE

    @staticmethod
    def from_fence_pole_type(typ: FenceType) -> FenceKind:
        if typ is FenceType.FENCE_TAPE_POLE_GREY:
            return FenceKind.TAPE
        elif typ is FenceType.FENCE_NET_POLE_GREY:
            return FenceKind.NET
        elif typ is FenceType.FENCE_TAPE_POLE_BLACK:
            return FenceKind.TAPE
        elif typ is FenceType.FENCE_NET_POLE_BLACK:
            return FenceKind.NET
        elif typ is FenceType.FENCE_TAPE_POLE_BLUE:
            return FenceKind.TAPE
        elif typ is FenceType.FENCE_NET_POLE_BLUE:
            return FenceKind.NET
        elif typ is FenceType.FENCE_TAPE_POLE_RED:
            return FenceKind.TAPE
        elif typ is FenceType.FENCE_NET_POLE_RED:
            return FenceKind.NET
        elif typ is FenceType.FENCE_BARBED_WIRE_POLE:
            return FenceKind.BARBED_WIRE
        else:
            return FenceKind.TAPE

    def to_fence_tile_type(self, long: bool) -> FenceType:
        if self is FenceKind.TAPE:
            if long:
                return FenceType.FENCE_TAPE_LONG
            else:
                return FenceType.FENCE_TAPE
        elif self is FenceKind.NET:
            if long:
                return FenceType.FENCE_NET_LONG
            else:
                return FenceType.FENCE_NET
        elif self is FenceKind.BARBED_WIRE:
            if long:
                return FenceType.FENCE_BARBED_WIRE_LONG
            else:
                return FenceType.FENCE_BARBED_WIRE

    @staticmethod
    def from_fence_tile_type(typ: FenceType) -> Tuple[FenceKind, bool]:
        if typ is FenceType.FENCE_TAPE:
            return (FenceKind.TAPE, False)
        elif typ is FenceType.FENCE_TAPE_LONG:
            return (FenceKind.TAPE, True)
        elif typ is FenceType.FENCE_NET:
            return (FenceKind.NET, False)
        elif typ is FenceType.FENCE_NET_LONG:
            return (FenceKind.NET, True)
        elif typ is FenceType.FENCE_BARBED_WIRE:
            return (FenceKind.BARBED_WIRE, False)
        elif typ is FenceType.FENCE_BARBED_WIRE_LONG:
            return (FenceKind.BARBED_WIRE, True)
        else:
            return (FenceKind.TAPE, False)


class FencePoleNetTexture(enum.Enum):
    BLACK = 0
    BLUE = 1
    GREY = 2
    RED = 3

    def pretty(self) -> str:
        return self.name.title()

    def to_fence_texture(self) -> FenceTexture:
        if self is FencePoleNetTexture.BLACK:
            return FenceTexture.POLE_BLACK
        elif self is FencePoleNetTexture.BLUE:
            return FenceTexture.POLE_BLUE
        elif self is FencePoleNetTexture.GREY:
            return FenceTexture.POLE_GREY
        elif self is FencePoleNetTexture.RED:
            return FenceTexture.POLE_RED

    @staticmethod
    def from_fence_texture(tex: FenceTexture) -> FencePoleNetTexture:
        if tex is FenceTexture.POLE_BLACK:
            return FencePoleNetTexture.BLACK
        elif tex is FenceTexture.POLE_BLUE:
            return FencePoleNetTexture.BLUE
        elif tex is FenceTexture.POLE_GREY:
            return FencePoleNetTexture.GREY
        elif tex is FenceTexture.POLE_RED:
            return FencePoleNetTexture.RED
        return FencePoleNetTexture.GREY


class FencePoleTapeTexture(enum.Enum):
    AR = 0
    AU = 1
    BR = 2
    HO = 3
    MB = 4
    RS = 5
    US = 6
    SIGNS_ROAD = 7

    def pretty(self) -> str:
        return self.name.replace("_", " ").title()

    def to_fence_texture(self) -> FenceTexture:
        if self is FencePoleTapeTexture.AR:
            return FenceTexture.POLE_AR
        elif self is FencePoleTapeTexture.AU:
            return FenceTexture.POLE_AU
        elif self is FencePoleTapeTexture.BR:
            return FenceTexture.POLE_BR
        elif self is FencePoleTapeTexture.HO:
            return FenceTexture.POLE_HO
        elif self is FencePoleTapeTexture.MB:
            return FenceTexture.POLE_MB
        elif self is FencePoleTapeTexture.RS:
            return FenceTexture.POLE_RS
        elif self is FencePoleTapeTexture.US:
            return FenceTexture.POLE_US
        elif self is FencePoleTapeTexture.SIGNS_ROAD:
            return FenceTexture.POLE_SIGNS_ROAD

    @staticmethod
    def from_fence_texture(tex: FenceTexture) -> FencePoleTapeTexture:
        if tex is FenceTexture.POLE_AR:
            return FencePoleTapeTexture.AR
        elif tex is FenceTexture.POLE_AU:
            return FencePoleTapeTexture.AU
        elif tex is FenceTexture.POLE_BR:
            return FencePoleTapeTexture.BR
        elif tex is FenceTexture.POLE_HO:
            return FencePoleTapeTexture.HO
        elif tex is FenceTexture.POLE_MB:
            return FencePoleTapeTexture.MB
        elif tex is FenceTexture.POLE_RS:
            return FencePoleTapeTexture.RS
        elif tex is FenceTexture.POLE_US:
            return FencePoleTapeTexture.US
        elif tex is FenceTexture.POLE_SIGNS_ROAD:
            return FencePoleTapeTexture.SIGNS_ROAD
        return FencePoleTapeTexture.BR


class FenceTileNetTexture(enum.Enum):
    ORANGE = 0
    BLUE = 1

    def pretty(self) -> str:
        return self.name.title()

    def to_fence_texture(self) -> FenceTexture:
        if self is FenceTileNetTexture.ORANGE:
            return FenceTexture.TILE_NET_ORANGE
        elif self is FenceTileNetTexture.BLUE:
            return FenceTexture.TILE_NET_BLUE

    @staticmethod
    def from_fence_texture(tex: FenceTexture) -> FenceTileNetTexture:
        if tex is FenceTexture.TILE_NET_ORANGE:
            return FenceTileNetTexture.ORANGE
        elif tex is FenceTexture.TILE_NET_BLUE:
            return FenceTileNetTexture.BLUE
        return FenceTileNetTexture.ORANGE


class FenceTileTapeTexture(enum.Enum):
    AR = 0
    AU = 1
    BR = 2
    HO = 3
    MB = 4
    RS = 5
    US = 6
    DIAG_STRIPE_RED_WHITE = 7
    BLUE = 8
    YELLOW = 9
    ORANGE = 10

    def pretty(self) -> str:
        return self.name.replace("_", " ").title()

    def to_fence_texture(self) -> FenceTexture:
        if self is FenceTileTapeTexture.AR:
            return FenceTexture.TILE_TAPE_AR
        elif self is FenceTileTapeTexture.AU:
            return FenceTexture.TILE_TAPE_AU
        elif self is FenceTileTapeTexture.BR:
            return FenceTexture.TILE_TAPE_BR
        elif self is FenceTileTapeTexture.HO:
            return FenceTexture.TILE_TAPE_HO
        elif self is FenceTileTapeTexture.MB:
            return FenceTexture.TILE_TAPE_MB
        elif self is FenceTileTapeTexture.RS:
            return FenceTexture.TILE_TAPE_RS
        elif self is FenceTileTapeTexture.US:
            return FenceTexture.TILE_TAPE_US
        elif self is FenceTileTapeTexture.DIAG_STRIPE_RED_WHITE:
            return FenceTexture.TILE_TAPE_DIAG_STRIPE_RED_WHITE
        elif self is FenceTileTapeTexture.BLUE:
            return FenceTexture.TILE_TAPE_BLUE
        elif self is FenceTileTapeTexture.YELLOW:
            return FenceTexture.TILE_TAPE_YELLOW
        elif self is FenceTileTapeTexture.ORANGE:
            return FenceTexture.TILE_TAPE_ORANGE

    @staticmethod
    def from_fence_texture(tex: FenceTexture) -> FenceTileTapeTexture:
        if tex is FenceTexture.TILE_TAPE_AR:
            return FenceTileTapeTexture.AR
        elif tex is FenceTexture.TILE_TAPE_AU:
            return FenceTileTapeTexture.AU
        elif tex is FenceTexture.TILE_TAPE_BR:
            return FenceTileTapeTexture.BR
        elif tex is FenceTexture.TILE_TAPE_HO:
            return FenceTileTapeTexture.HO
        elif tex is FenceTexture.TILE_TAPE_MB:
            return FenceTileTapeTexture.MB
        elif tex is FenceTexture.TILE_TAPE_RS:
            return FenceTileTapeTexture.RS
        elif tex is FenceTexture.TILE_TAPE_US:
            return FenceTileTapeTexture.US
        elif tex is FenceTexture.TILE_TAPE_DIAG_STRIPE_RED_WHITE:
            return FenceTileTapeTexture.DIAG_STRIPE_RED_WHITE
        elif tex is FenceTexture.TILE_TAPE_BLUE:
            return FenceTileTapeTexture.BLUE
        elif tex is FenceTexture.TILE_TAPE_YELLOW:
            return FenceTileTapeTexture.YELLOW
        elif tex is FenceTexture.TILE_TAPE_ORANGE:
            return FenceTileTapeTexture.ORANGE
        return FenceTileTapeTexture.DIAG_STRIPE_RED_WHITE
