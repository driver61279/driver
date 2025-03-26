"""Visible object vecs.
Does not appear to be used.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..common import Vector3


@dataclass
class VisibleObjectVec:
    # The first of these is a position vector somewhere close to the position
    # of the corresponding object block / geom block bounding boxes.
    vecs: List[Vector3]


@dataclass
class VisibleObjectVecs:
    vecs: List[VisibleObjectVec]
