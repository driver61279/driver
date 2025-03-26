from __future__ import annotations
import dataclasses
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import enum

from ..common import Key, Vector2
from .splines import Interpolation


class PacenoteID(enum.Enum):
    """This defines pace note and checkpoint events which should be triggered
    along the driveline
    """

    NOTE_HAIRPINLEFT = 0
    NOTE_LEFT90 = 1
    NOTE_KLEFT = 2
    NOTE_MEDIUMLEFT = 3
    NOTE_FASTLEFT = 4
    NOTE_EASYLEFT = 5
    NOTE_EASYRIGHT = 6
    NOTE_FASTRIGHT = 7
    NOTE_MEDIUMRIGHT = 8
    NOTE_KRIGHT = 9
    NOTE_RIGHT90 = 10
    NOTE_HAIRPINRIGHT = 11
    NOTE_TWISTY = 12
    NOTE_DISTANCE = 13
    NOTE_NARROWS = 14  # Also used as flag
    NOTE_WIDEOUT = 15  # Also used as flag
    NOTE_OVERCREST = 16
    NOTE_FORD = 17
    NOTE_CARE = 18
    NOTE_BUMP = 19
    NOTE_JUMP = 20

    # These actually control the timing
    EVENT_START = 21
    EVENT_FINISH = 22
    EVENT_CHECKPOINT = 23
    EVENT_ENDSTAGE = 24

    NOTE_FLATRIGHT = 25
    NOTE_FLATLEFT = 26
    NOTE_BRIDGE = 27
    NOTE_GOSTRAIGHT = 28
    NOTE_KEEPRIGHT = 29
    NOTE_KEEPLEFT = 30
    NOTE_KEEPMIDDLE = 31
    NOTE_CAUTION = 32

    def is_checkpoint(self) -> bool:
        return self is PacenoteID.EVENT_CHECKPOINT

    def is_event(self) -> bool:
        return any(
            [
                self is PacenoteID.EVENT_START,
                self is PacenoteID.EVENT_FINISH,
                self is PacenoteID.EVENT_CHECKPOINT,
                self is PacenoteID.EVENT_ENDSTAGE,
            ]
        )

    @staticmethod
    def nicely_ordered_universe() -> List[PacenoteID]:
        """Return all PacenoteIDs in a nice order"""
        return [
            PacenoteID.EVENT_START,
            PacenoteID.EVENT_FINISH,
            PacenoteID.EVENT_CHECKPOINT,
            PacenoteID.EVENT_ENDSTAGE,
            PacenoteID.NOTE_HAIRPINLEFT,
            PacenoteID.NOTE_LEFT90,
            PacenoteID.NOTE_KLEFT,
            PacenoteID.NOTE_MEDIUMLEFT,
            PacenoteID.NOTE_FASTLEFT,
            PacenoteID.NOTE_EASYLEFT,
            PacenoteID.NOTE_FLATLEFT,
            PacenoteID.NOTE_HAIRPINRIGHT,
            PacenoteID.NOTE_RIGHT90,
            PacenoteID.NOTE_KRIGHT,
            PacenoteID.NOTE_MEDIUMRIGHT,
            PacenoteID.NOTE_FASTRIGHT,
            PacenoteID.NOTE_EASYRIGHT,
            PacenoteID.NOTE_FLATRIGHT,
            PacenoteID.NOTE_DISTANCE,
            PacenoteID.NOTE_CARE,
            PacenoteID.NOTE_CAUTION,
            PacenoteID.NOTE_TWISTY,
            PacenoteID.NOTE_NARROWS,
            PacenoteID.NOTE_WIDEOUT,
            PacenoteID.NOTE_FORD,
            PacenoteID.NOTE_OVERCREST,
            PacenoteID.NOTE_BUMP,
            PacenoteID.NOTE_JUMP,
            PacenoteID.NOTE_BRIDGE,
            PacenoteID.NOTE_GOSTRAIGHT,
            PacenoteID.NOTE_KEEPRIGHT,
            PacenoteID.NOTE_KEEPLEFT,
            PacenoteID.NOTE_KEEPMIDDLE,
        ]

    def pretty(self) -> str:
        if self is PacenoteID.NOTE_HAIRPINLEFT:
            return "Left Hairpin"
        elif self is PacenoteID.NOTE_LEFT90:
            return "Left 90"
        elif self is PacenoteID.NOTE_KLEFT:
            return "Left K"
        elif self is PacenoteID.NOTE_MEDIUMLEFT:
            return "Left Medium"
        elif self is PacenoteID.NOTE_FASTLEFT:
            return "Left Fast"
        elif self is PacenoteID.NOTE_EASYLEFT:
            return "Left Easy"
        elif self is PacenoteID.NOTE_FLATLEFT:
            return "Left Flat"

        if self is PacenoteID.NOTE_HAIRPINRIGHT:
            return "Right Hairpin"
        elif self is PacenoteID.NOTE_RIGHT90:
            return "Right 90"
        elif self is PacenoteID.NOTE_KRIGHT:
            return "Right K"
        elif self is PacenoteID.NOTE_MEDIUMRIGHT:
            return "Right Medium"
        elif self is PacenoteID.NOTE_FASTRIGHT:
            return "Right Fast"
        elif self is PacenoteID.NOTE_EASYRIGHT:
            return "Right Easy"
        elif self is PacenoteID.NOTE_FLATRIGHT:
            return "Right Flat"

        elif self is PacenoteID.NOTE_TWISTY:
            return "Twisty"
        elif self is PacenoteID.NOTE_DISTANCE:
            return "Distance"
        elif self is PacenoteID.NOTE_NARROWS:
            return "Narrows"
        elif self is PacenoteID.NOTE_WIDEOUT:
            return "Wide Out"
        elif self is PacenoteID.NOTE_OVERCREST:
            return "Over Crest"
        elif self is PacenoteID.NOTE_FORD:
            return "Ford"
        elif self is PacenoteID.NOTE_CARE:
            return "Care"
        elif self is PacenoteID.NOTE_BUMP:
            return "Bump"
        elif self is PacenoteID.NOTE_JUMP:
            return "Jump"
        elif self is PacenoteID.NOTE_BRIDGE:
            return "Bridge"
        elif self is PacenoteID.NOTE_GOSTRAIGHT:
            return "Go Straight"
        elif self is PacenoteID.NOTE_KEEPRIGHT:
            return "Keep Right"
        elif self is PacenoteID.NOTE_KEEPLEFT:
            return "Keep Left"
        elif self is PacenoteID.NOTE_KEEPMIDDLE:
            return "Keep Middle"
        elif self is PacenoteID.NOTE_CAUTION:
            return "Caution"

        elif self is PacenoteID.EVENT_START:
            return "Event: Start"
        elif self is PacenoteID.EVENT_FINISH:
            return "Event: Finish"
        elif self is PacenoteID.EVENT_CHECKPOINT:
            return "Event: Split"
        elif self is PacenoteID.EVENT_ENDSTAGE:
            return "Event: End of Stage"


class PacenoteFlags(enum.Flag):
    NONE = 0x0
    NARROWS = 0x1
    WIDEOUT = 0x2
    TIGHTENS = 0x4
    SOUND_FILE = 0x8  # Whether the index for a sound file is set
    OCCUPIED_SOUND_2B = 0x10  # Legacy RBR
    DONT_CUT = 0x20
    CUT = 0x40
    TIGHTENS_BAD = 0x80
    NO_LINK = 0x100  # No link to successor note (don't emit into/and) [addon]
    HANDLED = 0x200  # Flag indicating this has been handled by enhanced handler
    LONG = 0x400
    PLUS = 0x800  # Faster than normal call. Do not use, RBR will crash
    MINUS = 0x1000  # Slower than normal call. Do not use, RBR will crash
    MAYBE = 0x2000
    # The custom id value mapped to a legacy pacenote id is contained in the
    # flags and the legacy id is in the pacenote's id_ value.
    ID_MAPPED = 0x4000
    RESERVED_0x8000 = 0x8000
    # 3 bits of sound index value.
    SOUND_INDEX_BIT_1 = 0x00010000
    SOUND_INDEX_BIT_2 = 0x00020000
    SOUND_INDEX_BIT_3 = 0x00040000
    # 12 bits of the ID value.
    ID_BIT_1 = 0x00080000
    ID_BIT_2 = 0x00100000
    ID_BIT_3 = 0x00200000
    ID_BIT_4 = 0x00400000
    ID_BIT_5 = 0x00800000
    ID_BIT_6 = 0x01000000
    ID_BIT_7 = 0x02000000
    ID_BIT_8 = 0x04000000
    ID_BIT_9 = 0x08000000
    ID_BIT_10 = 0x10000000
    ID_BIT_11 = 0x20000000
    ID_BIT_12 = 0x40000000
    # The pacenote call has been processed by the legacy pacenote handler.
    PROCESSED = 0x80000000


@dataclass
class AnimationSetDescriptorAddress:
    address: int = 0
    size: int = 0


class AnimationSetSection(enum.Enum):
    SIG_TRIGGER_DATA = 0
    SECTION_CHANNELS = 1
    ANIMATION_CHANNELS = 2
    BOOL_CHANNELS = 3
    REAL_CHANNELS = 4
    PACENOTES = 5
    ANIM_DATA = 6
    RALLY_SCHOOL = 7


@dataclass
class AnimationSetDescriptorItem:
    count: int = 0
    address: int = 0


def empty_animation_set_descriptor_addresses() -> (
    Dict[AnimationSetSection, AnimationSetDescriptorItem]
):
    return dict([(k, AnimationSetDescriptorItem()) for k in AnimationSetSection])


@dataclass
class AnimationSetDescriptor:
    name: str
    addresses: Dict[AnimationSetSection, AnimationSetDescriptorItem] = (
        dataclasses.field(default_factory=empty_animation_set_descriptor_addresses)
    )


@dataclass
class SigTriggerData:
    """
    id
        Associated trigger
    kind
        Only ever NONE or REPLAY_CAMERA_CHANGE
    """

    id: Key
    kind: TriggerKind


@dataclass
class SectionChannel:
    """Used for the replay cameras along the road, but is not limited to this
    use case.

    sig_trigger_data_index
        Index of the attached trigger data within the SigTriggerData array
    location
        Distance along the driveline when this trigger is to be fired.
    is_exit
        Flag whether this is the entry or exit of a section along the driveline

    Each camera has two of these: one with is_exit=False and one with
    is_exit=True. The location of the second is usually set to slightly before
    the start of the next camera. I the location of is_exit is set _after_ a
    later camera, it will override the later camera. If it is set significantly
    before the next camera, nothing different seems to happen.
    """

    sig_trigger_data_index: int
    location: float
    is_exit: bool


@dataclass
class AnimationChannel:
    """Used to start animations along the road, like deers crossing, marshals,
    media people. These animations are controlled by lua scripts.

    sig_trigger_data_index
        Index of the attached trigger data within the SigTriggerData array
    location
        Distance along on the driveline when this trigger is to be fired
    trigger_time
        Animation gets triggered trigger_time seconds before the car reaches the
        location. This is based on the car velocity.
    """

    sig_trigger_data_index: int
    location: float
    trigger_time: float


@dataclass
class BoolChannel:
    """Used to activate/deactivate a trigger.
    Only used in a few native stages.

    id
        ID of the channel, same as the associated trigger ID
    """

    id: Key


@dataclass
class BoolChannelTrigger:
    """Channel trigger used with bool channels.

    location
        Location on the driveline when the trigger is to be fired
    active
        Flag whether this channel is active
    """

    location: float
    active: bool


@dataclass
class RealChannelControlPoint:
    """Control point used by a real channel along the driveline.

    interpolation
        Interpolation mode of this spline point. Alters interpolation between
        this point and the next point.
    position
        Vector of (driveline location, animation value).
        This can be seen as the 2d coordinate of the control point in the graph
        editor where driveline location is on the X axis, and animation value is
        on the Y axis.
        Using interpolation (dependent on flags, but usually cubic hermite), the
        values of two adjacent control points are combined before being passed
        to the controlled entity.
    tangent_end
        Derivative of position for the left control point handle.
    tangent_start
        Derivative of position for the right control point handle.
    """

    interpolation: Interpolation
    position: Vector2
    tangent_end: Vector2
    tangent_start: Vector2
    # This value is for roundtripping when there is some garbage inside the
    # interpolation value. The game treats it as a bit flag and ignores the
    # other bits.
    __remaining_interpolation_bits__: int = 0


class TriggerKind(enum.Enum):
    """Triggers can control various properties of specific entities.
    - Positions and orientation (rotation) of an entity.
    - Activate/deactivate a trigger.
    - Change animation camera FOV.
    - Control fog settings.
    - Control view and camera ZFAR.
    - Control sound effects.
    """

    NONE = 0
    # Trigger data is required for these.
    POSITION_X = 1
    POSITION_Y = 2
    POSITION_Z = 3
    # Presumably also needs a spline attached to the trigger data.
    POSITION_FROM_SPLINE = 4
    ROTATION_X = 5
    ROTATION_Y = 6
    ROTATION_Z = 7
    ROTATION2_X = 8
    ROTATION2_Y = 9
    ROTATION2_Z = 10
    # Used by a bool channel to activate or deactivate another trigger.
    # Trigger data is required.
    TRIGGER_ACTIVATION = 11
    ANIMATION_CAMERA_FOV = 12
    # No data attached, the trigger ID identifies the replay camera.
    REPLAY_CAMERA_CHANGE = 13
    # No trigger data needed, value is taken from the channel.
    FOG_END = 14
    FOG_START = 15
    ZFAR = 16
    # Not used.
    __HELI_CAM_0X0C__ = 17
    __HELI_CAM_0X10__ = 18
    __HELI_CAM_0X04__ = 19
    __HELI_CAM_0X08__ = 20
    # No trigger data needed, value is taken from the channel.
    SOUND_LEFT_DELAY = 21
    SOUND_RIGHT_DELAY = 22
    SOUND_LEFT_REVERB = 23
    SOUND_RIGHT_REVERB = 24


@dataclass
class RealChannel:
    """Trigger channel used to fire events using floating point values.
    A channel may have trigger data attached.

    id
        ID of the channel, same as the associated trigger's id and trigger data.
    kind
        Kind of the trigger to be fired
    control_points
        Attached control points
    """

    id: Key
    kind: TriggerKind
    control_points: List[RealChannelControlPoint]


@dataclass
class Pacenote:
    """A pacenote callout along the driveline.

    id
        Pacenote ID (int indicates a non standard note)
    flags
        Pacenote flags (modifiers)
    location
        Distance along the driveline at which this pacenote is called
    """

    id: Union[PacenoteID, int]
    flags: PacenoteFlags
    location: float


class AnimFlags(enum.Flag):
    """Flags to control an animation"""

    NONE = 0x0  # No action
    RESPAWN = 0x1  # Automatically respawn/restart the animation when it is finished
    AUTO_REVERSE = (
        0x2  # Automatically reverse the animation when it has reached the end
    )
    REVERSE = 0x4  # Animation plays in reverse
    INIT_ANIMATION_SET = 0x8  # Internal flag


@dataclass
class AnimData:
    """Not useful for addon tracks."""

    name: str
    start: float
    end: float
    speed: float
    flags: AnimFlags


@dataclass
class RallySchool:
    """Some useless stuff for new tracks, so we omit modelling it.
    For native tracks we wouldn't have to store the count, but Wallaby requires
    it to roundtrip.
    """

    count: int
    raw: bytes


def default_animation_set_section_order() -> (
    List[Tuple[AnimationSetSection, Optional[int]]]
):
    return [(k, None) for k in AnimationSetSection]


@dataclass
class AnimationSet:
    name: str
    sig_trigger_data: List[SigTriggerData]
    # Sorted by location, low to high.
    section_channels: List[SectionChannel]
    # Sorted by location, low to high.
    animation_channels: List[AnimationChannel]
    bool_channels: List[BoolChannel]
    real_channels: List[RealChannel]
    pacenotes: List[Pacenote]
    # Not useful for addon tracks.
    anim_data: List[AnimData] = dataclasses.field(default_factory=lambda: [])
    # Not useful for addon tracks.
    rally_school: Optional[RallySchool] = None
    # Specify the order of the sections, necessary for roundtripping without
    # having to explicity store addresses. Nonetheless, we do also store
    # addresses, because the addresses of missing sections can be either zero or
    # the same as the subsequent section, but also because it makes for easy
    # roundtrip checks of offsets. Use None if constructing AnimationSet
    # directly.
    section_order: List[Tuple[AnimationSetSection, Optional[int]]] = dataclasses.field(
        default_factory=default_animation_set_section_order
    )
    wallaby_garbage: bytes = b""

    def set_real_channel(self, channel: RealChannel) -> None:
        """Add a channel, replacing existing channel with same id/type"""
        new_channels = []
        for real_channel in self.real_channels:
            if real_channel.kind is channel.kind and real_channel.id == channel.id:
                continue
            new_channels.append(real_channel)
        new_channels.append(channel)
        self.real_channels = new_channels


@dataclass
class AnimationSets:
    """There must be at least one set with the name 'Driveline'.
    The 'Driveline' set is the one controlling the pacenotes and replay cameras,
    and the game finds it by the name.
    """

    sets: List[AnimationSet]
    # When True, the descriptors and sets are interleaved. For examples,
    # track-86_M is not interleaved and has two sets, and track-491_O is
    # interleaved and has three sets.
    interleaved: bool = False
