from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

from ..common import Key, Vector3


@dataclass
class CardanAngles:
    """Pitch, roll, and yaw, in degrees.

    pitch
        Angle from horizontal, negative looks upwards
    roll
        Angle from horizontal, positive tilts camera clockwise
    yaw
        0 Looks in positive Y direction?
        Positive values turn camera clockwise in plan view.
    """

    pitch: float
    roll: float
    yaw: float


@dataclass
class SplineIDs:
    id: int
    group_id: int

    def __hash__(self) -> int:
        return (self.id, self.group_id).__hash__()


@dataclass
class TriggerDataItem:
    """A container for holding event related data.

    spline
        Related spline, used for interpolating position values.
    position
        Position of the controlled entity in world space
    angles
        Rotation of the controlled entity, in degrees
    active
        Whether the triggered entity is activated
    """

    spline: Optional[SplineIDs]
    position: Vector3
    angles: CardanAngles
    active: bool
    unused_angles: CardanAngles = CardanAngles(1, 1, 1)


@dataclass
class TriggerData:
    """
    items
        Trigger data, keyed on ID, same as ID of the trigger or other related
        object
    """

    items: Dict[Key, TriggerDataItem]
