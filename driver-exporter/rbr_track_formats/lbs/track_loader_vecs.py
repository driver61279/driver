"""Track loader vecs.
Does not appear to be used.
"""

from __future__ import annotations
from dataclasses import dataclass

from ..common import Vector3


@dataclass
class TrackLoaderVecs:
    a: Vector3
    # Normalised vector
    b: Vector3
