"""Animations and replay cameras

Any of the unknown parts are named unknown_address, where the address is
taken from the rally school stage dls file.

If there are errors loading the dls file, the game creates dlserrors.log.
For example:
12-Sep-20 16:58:14 Loading DLS data of stage 71,
  animationIdsOffset = 0x658c,
  count = 0,
  animation id name offsets out of range: NONE,
  animationSetsOffset = 0x38,
  count = 1,
  anim set header 0,
  replay camera channels out of range: 3(60351)
12-Sep-20 17:24:31  RBR crashed while loading data
"""

from __future__ import annotations
import dataclasses
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TypeVar
import enum

from .. import errors
from ..common import Key

from .animation_sets import (
    AnimationSet,
    AnimationSets,
    RealChannelControlPoint,
    TriggerKind,
)
from .trigger_data import TriggerData
from .splines import Splines
from .animation_cameras import AnimationCameras
from .track_emitters import TrackEmitters
from .helicams import Helicams
from .sound_emitters import SoundEmitters
from .registration_zone import RegistrationZone
from .animation_ids import AnimationIDs
from .names import Names, NameOffset


class DLSSection(enum.Enum):
    ANIMATION_SETS = 0
    SPLINES = 1
    TRIGGER_DATA = 2
    ANIMATION_CAMERAS = 3
    TRACK_EMITTERS = 4
    HELICAMS = 5
    SOUND_EMITTERS = 6
    ANIMATION_NAMES = 7
    REGISTRATION_ZONE = 8
    ANIMATION_IDS = 9


@dataclass
class Addresses:
    addresses: Dict[DLSSection, int]


DLS_HEADER: bytes = b"MINAATAD\x12\x00\x00\x00\x00\x00\x00\x00"


def default_dls_section_order() -> List[Tuple[DLSSection, Optional[int]]]:
    return [(k, None) for k in DLSSection]


@dataclass
class RawDLS:
    """Intermediary class, the purpose of this is to allow reading all of the
    sections in a particular order, regardless of the order they are packed into
    the file."""

    raw_sections: Dict[DLSSection, Tuple[int, bytes]]
    section_order: List[Tuple[DLSSection, Optional[int]]] = dataclasses.field(
        default_factory=default_dls_section_order
    )


A = TypeVar("A")


@dataclass
class DLS:
    animation_sets: AnimationSets
    trigger_data: TriggerData
    splines: Splines
    animation_cameras: AnimationCameras
    track_emitters: TrackEmitters
    helicams: Helicams
    sound_emitters: SoundEmitters
    registration_zone: Optional[RegistrationZone]
    animation_ids: AnimationIDs
    section_order: List[Tuple[DLSSection, Optional[int]]] = dataclasses.field(
        default_factory=default_dls_section_order
    )
    # We keep track of any names which are unused (as in, nobody holds offsets
    # to them). This is so we can roundtrip without holding the name offsets.
    # Let this default to an empty dictionary if you are constructing this type.
    extra_names: Dict[int, str] = dataclasses.field(default_factory=dict)

    def get_driveline_set(self) -> Optional[AnimationSet]:
        for animation_set in self.animation_sets.sets:
            if animation_set.name.lower() == "driveline":
                return animation_set
        return None

    def get_driveline_real_channel(
        self, key: Key, kind: TriggerKind
    ) -> Optional[List[RealChannelControlPoint]]:
        animation_set = self.get_driveline_set()
        if animation_set is None:
            return None
        for real_channel in animation_set.real_channels:
            if real_channel.kind is kind and real_channel.id == key:
                return real_channel.control_points
        return None

    def to_names(self) -> Names:
        """Collect named objects in the appropriate order - to match the native
        stages."""
        names: Dict[NameOffset, str] = dict()
        offset: int = 0
        index: int = 0

        def add_name_impl(name: str) -> None:
            nonlocal index
            nonlocal offset
            # Deal with duplicate names. Some stages have two sets with the same
            # name (and same name offset).
            if name in set(names.values()):
                return
            names[NameOffset(offset)] = name
            offset = offset + len(name) + 1
            index = index + 1

        def add_name(name: str) -> None:
            # This function inserts the extra, unused names into the right
            # place so that we can roundtrip without storing any name offsets.
            nonlocal index
            add_name_impl(name)
            while index in self.extra_names:
                add_name_impl(self.extra_names[index])

        for anim_set in self.animation_sets.sets:
            add_name(anim_set.name)
            for anim_data in anim_set.anim_data:
                add_name(anim_data.name)
        for track_emitter in self.track_emitters.items:
            add_name(track_emitter.name)
        for anim_id_name in self.animation_ids.items.values():
            add_name(anim_id_name)
        return Names(names)

    def set_extra_names(self, original_names: Names) -> None:
        """Find extra names and save them for roundtripping"""
        extra_names = dict()
        our_names = set(self.to_names().names.values())
        for i, (offset, name) in enumerate(original_names.names.items()):
            if name in our_names:
                continue
            else:
                extra_names[i] = name
        self.extra_names = extra_names
        our_new_names = self.to_names()
        if original_names != our_new_names:
            raise errors.RBRAddonBug(
                "set_extra_names: {original_names} {our_new_names}"
            )
