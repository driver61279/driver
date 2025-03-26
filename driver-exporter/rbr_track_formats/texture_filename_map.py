"""Texture filename map.
Defines shared textures.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass
class TextureFilenameMap:
    """A shadow map is just a very compact texture.
    It's a bitmap of size (width x height), but instead of each pixel having
    RGBA data, it's a single (monochromatic) byte.
    """

    mapping: Dict[str, str]
