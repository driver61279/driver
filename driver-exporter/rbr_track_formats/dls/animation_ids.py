from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from ..common import Key


@dataclass
class AnimationIDs:
    """Associate animation IDs and names.

    Triggers, animations, and channels share a unique ID.
    Triggers, animations, channels, and trigger data are linked using this ID.
    E.g. the ID of a real channel is used to identify the attached trigger data.
    """

    items: Dict[Key, str]
