from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..common import Key


@dataclass
class Helicam:
    """Unused in game."""

    id: Key
    name: str
    unknown_3: float
    unknown_4: int
    unknown_5: float
    unknown_6: float
    unknown_7: float


@dataclass
class Helicams:
    """Unused in game.
    The only native stages with these items are 56 and 62.
    """

    items: List[Helicam]
