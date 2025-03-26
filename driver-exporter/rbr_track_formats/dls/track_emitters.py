from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..common import Key


@dataclass
class TrackEmitter:
    """
    name
        Name of emitter (or group of emitters?)
    trigger_id
        ID of the trigger this emitter is attached to
    distance_squared
        Squared distance of the collision point to activate this emitter
    """

    name: str
    trigger_id: Key
    distance_squared: float


@dataclass
class TrackEmitters:
    items: List[TrackEmitter]
