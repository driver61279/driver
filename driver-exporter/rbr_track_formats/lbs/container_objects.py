"""Container objects
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List
import enum


class ContainerObjectFlag(enum.Enum):
    NONE = 0x0
    RANDOMISED = 0x1
    GLOBAL = 0x2


@dataclass
class ContainerObject:
    name: str
    container_id: int
    flag: ContainerObjectFlag
    random_upper_bound: int


@dataclass
class ContainerObjects:
    objects: List[ContainerObject]
