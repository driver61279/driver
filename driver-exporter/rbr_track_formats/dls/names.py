from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass
class NameOffset:
    """Offset in AnimationNames list"""

    offset: int

    def __hash__(self) -> int:
        return self.offset.__hash__()


@dataclass
class Names:
    names: Dict[NameOffset, str]
