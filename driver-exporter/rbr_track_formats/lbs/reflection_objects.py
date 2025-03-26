"""Reflection objects
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from .common import ObjectData3D


@dataclass
class ReflectionObject:
    """An reflection object mesh

    name
        Name of this object
    data_3d
        Parts of the mesh, each can have a different texture associated with it.
    """

    name: str
    data_3d: List[ObjectData3D]


@dataclass
class ReflectionObjects:
    objects: List[ReflectionObject]
