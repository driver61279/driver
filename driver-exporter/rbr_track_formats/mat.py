"""Material file.
This describes all possible surface materials as 16x16 bitmaps.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import enum

from . import errors


class MaterialID(enum.Enum):
    UNDEFINED = 0
    GRAVEL_FINE_DEEPER_DRY = 1
    GRAVEL_FINE_DEEPER_DAMP = 2
    GRAVEL_FINE_DEEPER_WET = 3
    GRAVEL_MEDIUM_DEEPER_DRY = 5
    GRAVEL_MEDIUM_DEEPER_DAMP = 6
    GRAVEL_MEDIUM_DEEPER_WET = 7
    GRAVEL_FINE_DEEP_DRY = 9
    GRAVEL_FINE_DEEP_DAMP = 10
    GRAVEL_FINE_DEEP_WET = 11
    GRAVEL_MEDIUM_DEEP_DRY = 13
    GRAVEL_MEDIUM_DEEP_DAMP = 14
    GRAVEL_MEDIUM_DEEP_WET = 15
    GRAVEL_FINE_SHALLOW_DRY = 17
    GRAVEL_FINE_SHALLOW_DAMP = 18
    GRAVEL_FINE_SHALLOW_WET = 19
    GRAVEL_MEDIUM_SHALLOW_DRY = 21
    GRAVEL_MEDIUM_SHALLOW_DAMP = 22
    GRAVEL_MEDIUM_SHALLOW_WET = 23
    SPRET_BUSH_SMALL = 24
    SPRET_BUSH_MEDIUM = 25
    SPRET_BUSH_LARGE = 26
    LOV_BUSH_SMALL = 27
    LOV_BUSH_MEDIUM = 28
    LOV_BUSH_LARGE = 29
    TREE_SMALL = 30
    TREE_MEDIUM = 31
    TREE_LARGE = 32
    GRAVEL_COARSE_DEEPER_DRY = 33
    GRAVEL_COARSE_DEEPER_DAMP = 34
    GRAVEL_COARSE_DEEPER_WET = 35
    TARMAC_FINE_CLEAN_DRY = 37
    TARMAC_FINE_CLEAN_DAMP = 38
    TARMAC_FINE_CLEAN_WET = 39
    GRAVEL_COARSE_DEEP_DRY = 41
    GRAVEL_COARSE_DEEP_DAMP = 42
    GRAVEL_COARSE_DEEP_WET = 43
    TARMAC_FINE_SPRINKLED_DRY = 45
    TARMAC_FINE_SPRINKLED_DAMP = 46
    TARMAC_FINE_SPRINKLED_WET = 47
    GRAVEL_COARSE_SHALLOW_DRY = 49
    GRAVEL_COARSE_SHALLOW_DAMP = 50
    GRAVEL_COARSE_SHALLOW_WET = 51
    TARMAC_FINE_COVERED_DRY = 53
    TARMAC_FINE_COVERED_DAMP = 54
    TARMAC_FINE_COVERED_WET = 55
    ROCK_SMALL = 56
    ROCK_MEDIUM = 57
    ROCK_LARGE = 58
    TRUNK_SMALL = 59
    TRUNK_MEDIUM = 60
    TRUNK_LARGE = 61
    SNOWWALL = 62
    METAL_POLE = 63
    METAL_BARRIER = 64
    TARMAC_MEDIUM_CLEAN_DRY = 65
    TARMAC_MEDIUM_CLEAN_DAMP = 66
    TARMAC_MEDIUM_CLEAN_WET = 67
    TARMAC_COARSE_CLEAN_DRY = 69
    TARMAC_COARSE_CLEAN_DAMP = 70
    TARMAC_COARSE_CLEAN_WET = 71
    TARMAC_MEDIUM_SPRINKLED_DRY = 73
    TARMAC_MEDIUM_SPRINKLED_DAMP = 74
    TARMAC_MEDIUM_SPRINKLED_WET = 75
    TARMAC_COARSE_SPRINKLED_DRY = 77
    TARMAC_COARSE_SPRINKLED_DAMP = 78
    TARMAC_COARSE_SPRINKLED_WET = 79
    TARMAC_MEDIUM_COVERED_DRY = 81
    TARMAC_MEDIUM_COVERED_DAMP = 82
    TARMAC_MEDIUM_COVERED_WET = 83
    TARMAC_COARSE_COVERED_DRY = 85
    TARMAC_COARSE_COVERED_DAMP = 86
    TARMAC_COARSE_COVERED_WET = 87
    SNOWWALL_BOTTOM = 88  # Possibly used on the ground beneath the snowwall object
    COBBLE_DRY = 89
    COBBLE_DAMP = 90
    COBBLE_WET = 91
    SETT_DRY = 92
    SETT_DAMP = 93
    SETT_WET = 94
    GRASS_HARD_DRY = 97
    GRASS_HARD_DAMP = 98
    GRASS_HARD_WET = 99
    SNOWONGRAVEL_SHALLOW = 101
    SNOWONGRAVEL_MEDIUM = 102
    SNOWONGRAVEL_DEEP = 103
    GRASS_MEDIUM_DRY = 105
    GRASS_MEDIUM_DAMP = 106
    GRASS_MEDIUM_WET = 107
    GRASS_SOFT_DRY = 113
    GRASS_SOFT_DAMP = 114
    GRASS_SOFT_WET = 115
    BLACK_ICE = 116
    SNOWONICE_SHALLOW = 117
    SNOWONICE_MEDIUM = 118
    SNOWONICE_DEEP = 119
    TREE_STUMP = 120
    BENDABLE_TREE = 121
    ROUGH_ROUGH_DRY = 129
    ROUGH_ROUGH_WET = 130
    ROUGH_ROUGH_DAMP = 131
    DIRT_HARD_DRY = 133
    DIRT_HARD_DAMP = 134
    DIRT_HARD_WET = 135
    ROUGH_VERYROUGH_DAMP = 136
    ROUGH_VERYROUGH_DRY = 137
    ROUGH_VERYROUGH_WET = 138
    DIRT_MEDIUM_DRY = 141
    DIRT_MEDIUM_DAMP = 142
    DIRT_MEDIUM_WET = 143
    DIRT_SOFT_DRY = 149
    DIRT_SOFT_DAMP = 150
    DIRT_SOFT_WET = 151
    GRAVEL_FINE_SHALLOW_DRY_CLONE = 153
    GRAVEL_FINE_SHALLOW_DAMP_CLONE = 154
    GRAVEL_FINE_SHALLOW_WET_CLONE = 155
    WATER_SURFACE = 157
    DIRT_HARD_DRY_CLONE = 161
    DIRT_HARD_DAMP_CLONE = 162
    DIRT_HARD_WET_CLONE = 163
    VERY_SPARSE_BUSH = 165
    SPARSE_BUSH = 166
    DENSE_BUSH = 167
    VERY_DENSE_BUSH = 168
    US_GRAVEL_FINE_SHALLOW_DRY = 177
    US_GRAVEL_FINE_SHALLOW_DAMP = 178
    US_GRAVEL_FINE_SHALLOW_WET = 179
    BR_GRAVEL_COARSE_SHALLOW_DRY = 181
    BR_GRAVEL_COARSE_SHALLOW_DAMP = 182
    BR_GRAVEL_COARSE_SHALLOW_WET = 183
    US_GRAVEL_FINE_DEEP_DRY = 185
    US_GRAVEL_FINE_DEEP_DAMP = 186
    US_GRAVEL_FINE_DEEP_WET = 187
    BR_GRAVEL_COARSE_DEEP_DRY = 189
    BR_GRAVEL_COARSE_DEEP_DAMP = 190
    BR_GRAVEL_COARSE_DEEP_WET = 191
    US_GRAVEL_FINE_DEEPER_DRY = 193
    US_GRAVEL_FINE_DEEPER_DAMP = 194
    US_GRAVEL_FINE_DEEPER_WET = 195
    BR_GRAVEL_COARSE_DEEPER_DRY = 197
    BR_GRAVEL_COARSE_DEEPER_DAMP = 198
    BR_GRAVEL_COARSE_DEEPER_WET = 199
    SCRIPT_CHARACTER = 200
    PASSTHROUGH = 254
    SPECTATOR = 255

    def simplify(self) -> MaterialID:
        """Turn the clones into non clones"""
        if self is MaterialID.GRAVEL_FINE_SHALLOW_DRY_CLONE:
            return MaterialID.GRAVEL_FINE_SHALLOW_DRY
        elif self is MaterialID.GRAVEL_FINE_SHALLOW_DAMP_CLONE:
            return MaterialID.GRAVEL_FINE_SHALLOW_DAMP
        elif self is MaterialID.GRAVEL_FINE_SHALLOW_WET_CLONE:
            return MaterialID.GRAVEL_FINE_SHALLOW_WET
        elif self is MaterialID.DIRT_HARD_DRY_CLONE:
            return MaterialID.DIRT_HARD_DRY
        elif self is MaterialID.DIRT_HARD_DAMP_CLONE:
            return MaterialID.DIRT_HARD_DAMP
        elif self is MaterialID.DIRT_HARD_WET_CLONE:
            return MaterialID.DIRT_HARD_WET
        return self

    def pretty(self) -> str:
        return self.name.replace("_", " ").title()


# A set of materials which can be used for shape collision meshes.
object_materials: Set[MaterialID]
object_materials = {
    MaterialID.BENDABLE_TREE,
    MaterialID.DENSE_BUSH,  # Not used in native tracks
    MaterialID.LOV_BUSH_LARGE,
    MaterialID.LOV_BUSH_MEDIUM,
    MaterialID.LOV_BUSH_SMALL,
    MaterialID.METAL_BARRIER,  # Not used in native tracks
    MaterialID.METAL_POLE,
    MaterialID.ROCK_LARGE,
    MaterialID.ROCK_MEDIUM,
    MaterialID.ROCK_SMALL,
    MaterialID.SCRIPT_CHARACTER,
    MaterialID.SNOWWALL,
    MaterialID.SPARSE_BUSH,  # Not used in native tracks
    MaterialID.SPRET_BUSH_LARGE,  # Not used in native tracks
    MaterialID.SPRET_BUSH_MEDIUM,
    MaterialID.SPRET_BUSH_SMALL,  # Not used in native tracks
    MaterialID.TREE_LARGE,
    MaterialID.TREE_MEDIUM,
    MaterialID.TREE_SMALL,
    MaterialID.TREE_STUMP,
    MaterialID.TRUNK_LARGE,
    MaterialID.TRUNK_MEDIUM,
    MaterialID.TRUNK_SMALL,
    MaterialID.UNDEFINED,
    MaterialID.VERY_DENSE_BUSH,  # Not used in native tracks
    MaterialID.VERY_SPARSE_BUSH,  # Not used in native tracks
}


# A set of materials which can be used for the ground collision mesh (via mat
# files). This is basically all materials except for the object_materials, but
# UNDEFINED is allowed anywhere.
ground_materials: Set[MaterialID]
ground_materials = set(
    [
        m
        for m in MaterialID
        if m not in object_materials and m is not MaterialID.SPECTATOR
    ]
    + [MaterialID.UNDEFINED]
)


@dataclass
class MaterialMap:
    bitmap: List[List[MaterialID]]

    def pretty_print(self) -> None:
        for row in self.bitmap:
            for v in row:
                print(hex(v.value)[2:], end=" ")
            print()
        print()

    def __hash__(self) -> int:
        return hash(tuple([m for row in self.bitmap for m in row]))

    @staticmethod
    def full(m: MaterialID) -> MaterialMap:
        bitmap = []
        for row in range(16):
            cols = []
            for col in range(16):
                cols.append(m)
            bitmap.append(cols)
        return MaterialMap(bitmap)

    def copy_x(self) -> MaterialMap:
        """Swap the left and right halves of the map.

        1 2  ->  2 1
        3 4      4 3
        """
        rows: List[List[MaterialID]] = []
        for row in self.bitmap:
            left = row[:8]
            right = row[8:]
            rows.append(right + left)
        return MaterialMap(bitmap=rows)

    def copy_y(self) -> MaterialMap:
        """Swap the top and bottom halves of the map.

        1 2  ->  3 4
        3 4      1 2
        """
        top = self.bitmap[:8]
        bottom = self.bitmap[8:]
        rows = bottom + top
        return MaterialMap(bitmap=rows)

    def copy_xy(self) -> MaterialMap:
        """A combination of copy_x and copy_y"""
        return self.copy_x().copy_y()


def pretty_enum(e: enum.Enum) -> str:
    return e.name[:1] + e.name[1:].lower()


class SurfaceType(enum.Enum):
    DRY = 0x0
    DAMP = 0x1
    WET = 0x2

    def pretty(self) -> str:
        return pretty_enum(self)

    def description(self) -> str:
        return self.pretty()

    def bitmask(self) -> int:
        if self is SurfaceType.DRY:
            return 0b001
        elif self is SurfaceType.DAMP:
            return 0b010
        elif self is SurfaceType.WET:
            return 0b100

    @staticmethod
    def from_string(string: str) -> SurfaceType:
        for t in SurfaceType:
            if t.to_string() in string:
                return t
        raise errors.E0100(string=string)

    def to_string(self) -> str:
        return self.name.lower()


class SurfaceAge(enum.Enum):
    NEW = 0x0
    NORMAL = 0x1
    WORN = 0x2

    def pretty(self) -> str:
        return pretty_enum(self)

    def description(self) -> str:
        return self.pretty()

    @staticmethod
    def from_string(string: str) -> SurfaceAge:
        for t in SurfaceAge:
            if t.to_string() in string:
                return t
        raise errors.E0101(string=string)

    def to_string(self) -> str:
        return self.name.lower()


@dataclass
class ConditionIdentifier:
    surface_type: SurfaceType
    surface_age: SurfaceAge
    name: str = ""

    def __hash__(self) -> int:
        return (self.surface_type.value, self.surface_age.value).__hash__()

    def packed_index(self) -> int:
        return 3 * self.surface_type.value + self.surface_age.value


@dataclass
class MAT:
    conditions: Dict[ConditionIdentifier, List[MaterialMap]]
    # Wallaby puts a load of internal stuff at the end of the file.
    __wallaby_stuff__: Optional[bytes] = None
