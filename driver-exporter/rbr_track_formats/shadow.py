"""Shadow dat file.
Defines a shadow map.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class ShadowDAT:
    """A shadow map is just a very compact texture.
    It's a bitmap of size (width x height), but instead of each pixel having
    RGBA data, it's a single (monochromatic) byte.
    """

    width: int
    height: int
    bitmap: List[List[int]]
