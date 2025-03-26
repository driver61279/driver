from rbr_track_formats import errors
from rbr_track_formats.binary import PackBin
from rbr_track_formats.dls.animation_sets import (
    AnimData,
    AnimFlags,
    AnimationChannel,
    AnimationSet,
    AnimationSetDescriptor,
    AnimationSetDescriptorAddress,
    AnimationSetDescriptorItem,
    AnimationSetSection,
    AnimationSets,
    BoolChannel,
    BoolChannelTrigger,
    Pacenote,
    PacenoteFlags,
    PacenoteID,
    RallySchool,
    RealChannel,
    RealChannelControlPoint,
    SectionChannel,
    SigTriggerData,
    TriggerKind,
)
from rbr_track_formats.dls.names import Names

from ..common import key_to_binary, vector2_to_binary
from .names import names_pack_name_offset


def pacenote_id_to_binary(self: PacenoteID, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def pacenote_flags_to_binary(self: PacenoteFlags, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def animation_set_descriptor_address_to_binary(
    self: AnimationSetDescriptorAddress, bin: PackBin
) -> None:
    bin.pack("<II", self.address, self.size)


def animation_set_descriptor_to_binary(
    self: AnimationSetDescriptor, names: Names, bin: PackBin
) -> None:
    names_pack_name_offset(names, self.name, bin)
    for k in AnimationSetSection:
        bin.pack("<I", self.addresses[k].count)
    for k in AnimationSetSection:
        bin.pack("<I", self.addresses[k].address)


def sig_trigger_data_to_binary(self: SigTriggerData, bin: PackBin) -> None:
    key_to_binary(self.id, bin)
    trigger_kind_to_binary(self.kind, bin)


def section_channel_to_binary(self: SectionChannel, bin: PackBin) -> None:
    bin.pack("<IfI", self.sig_trigger_data_index, self.location, self.is_exit)


def animation_channel_to_binary(self: AnimationChannel, bin: PackBin) -> None:
    bin.pack("<Iff", self.sig_trigger_data_index, self.location, self.trigger_time)


def bool_channel_to_binary(self: BoolChannel, bin: PackBin) -> None:
    key_to_binary(self.id, bin)
    trigger_kind_to_binary(TriggerKind.TRIGGER_ACTIVATION, bin)
    bin.pack("<I", 0)


def bool_channel_trigger_to_binary(self: BoolChannelTrigger, bin: PackBin) -> None:
    bin.pack("<fI", self.location, self.active)


def real_channel_control_point_to_binary(
    self: RealChannelControlPoint, bin: PackBin
) -> None:
    bin.pack("<I", self.interpolation.value | self.__remaining_interpolation_bits__)
    vector2_to_binary(self.position, bin)
    vector2_to_binary(self.tangent_end, bin)
    vector2_to_binary(self.tangent_start, bin)


def trigger_kind_to_binary(self: TriggerKind, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def real_channel_to_binary(self: RealChannel, bin: PackBin) -> None:
    key_to_binary(self.id, bin)
    trigger_kind_to_binary(self.kind, bin)
    bin.pack("<II", len(self.control_points), 0)
    for control_point in self.control_points:
        real_channel_control_point_to_binary(control_point, bin)


def pacenote_is_checkpoint(self: Pacenote) -> bool:
    if isinstance(self.id, PacenoteID):
        return self.id.is_checkpoint()
    return False


def pacenote_to_binary(self: Pacenote, bin: PackBin) -> None:
    if isinstance(self.id, PacenoteID):
        pacenote_id_to_binary(self.id, bin)
    else:
        bin.pack("<I", self.id)
    pacenote_flags_to_binary(self.flags, bin)
    bin.pack("<f", self.location)


def anim_flags_to_binary(self: AnimFlags, bin: PackBin) -> None:
    bin.pack("<I", self.value)


def anim_data_to_binary(self: AnimData, names: Names, bin: PackBin) -> None:
    names_pack_name_offset(names, self.name, bin)
    bin.pack(
        "<fff",
        self.start,
        self.end,
        self.speed,
    )
    anim_flags_to_binary(self.flags, bin)


def rally_school_to_binary(self: RallySchool, bin: PackBin) -> None:
    bin.pack_bytes(self.raw)


def animation_set_to_binary(
    self: AnimationSet,
    set_index: int,
    descriptor_offset: int,
    names: Names,
    bin: PackBin,
) -> None:
    addresses = dict()
    for i, (section, expected_address) in enumerate(self.section_order):
        if expected_address is not None and expected_address != 0:
            if bin.offset != expected_address:
                raise errors.RBRAddonBug(
                    "AnimationSet.to_binary: Writing set "
                    + str(set_index)
                    + " section "
                    + section.name
                    + " at incorrect address, expected "
                    + hex(expected_address)
                    + " but we are at "
                    + hex(bin.offset)
                    + ". This is likely due to the previous section, "
                    + str(self.section_order[i - 1][0])
                    + " being too "
                    + ("short" if bin.offset < expected_address else "long")
                    + "."
                )
        # Make a note of the current offset: we need to write this into the address object.
        address_to_write = bin.offset
        if section == AnimationSetSection.SIG_TRIGGER_DATA:
            count = len(self.sig_trigger_data)
            for trigger_data in self.sig_trigger_data:
                sig_trigger_data_to_binary(trigger_data, bin)
        elif section == AnimationSetSection.SECTION_CHANNELS:
            count = len(self.section_channels)
            for camera_trigger in self.section_channels:
                section_channel_to_binary(camera_trigger, bin)
        elif section == AnimationSetSection.ANIMATION_CHANNELS:
            count = len(self.animation_channels)
            for anim_trigger in self.animation_channels:
                animation_channel_to_binary(anim_trigger, bin)
        elif section == AnimationSetSection.PACENOTES:
            count = len(self.pacenotes)
            num_checkpoints = len(list(filter(pacenote_is_checkpoint, self.pacenotes)))
            if num_checkpoints > 2:
                raise errors.E0160(num_checkpoints=num_checkpoints)
            for pacenote in self.pacenotes:
                pacenote_to_binary(pacenote, bin)
        elif section == AnimationSetSection.REAL_CHANNELS:
            count = len(self.real_channels)
            for real_channel in self.real_channels:
                real_channel_to_binary(real_channel, bin)
        elif section == AnimationSetSection.BOOL_CHANNELS:
            count = len(self.bool_channels)
            for bool_channel in self.bool_channels:
                bool_channel_to_binary(bool_channel, bin)
        elif section == AnimationSetSection.ANIM_DATA:
            count = len(self.anim_data)
            for anim_data in self.anim_data:
                anim_data_to_binary(anim_data, names, bin)
        elif section == AnimationSetSection.RALLY_SCHOOL:
            count = 0
            if self.rally_school is not None:
                rally_school_to_binary(self.rally_school, bin)
                count = self.rally_school.count
            bin.pack_bytes(self.wallaby_garbage)
        else:
            raise NotImplementedError(
                "AnimationSet to_binary: not handled: " + section.name
            )
        addresses[section] = AnimationSetDescriptorItem(
            # Only write the address to zero if the expected address is
            # zero. This allows us to roundtrip wonky formats without just
            # trusting the expected_address fully.
            address=0 if expected_address == 0 else address_to_write,
            count=count,
        )
    end = bin.offset
    bin.offset = descriptor_offset
    animation_set_descriptor_to_binary(
        AnimationSetDescriptor(name=self.name, addresses=addresses), names, bin
    )
    bin.offset = end


def animation_sets_to_binary(self: AnimationSets, names: Names, bin: PackBin) -> None:
    bin.pack("<I", len(self.sets))
    descriptor_address_offsets = []
    for animation_set in self.sets:
        # Store this offset so we can write the correct address and size later
        descriptor_address_offsets.append(bin.offset)
        # Pad the appropriate number of bytes
        descriptor_address = AnimationSetDescriptorAddress()
        animation_set_descriptor_address_to_binary(descriptor_address, bin)
    descriptor_offsets = []
    for i, animation_set in enumerate(self.sets):
        start = bin.offset
        # Jump to the address object offset and fill in the correct values
        bin.offset = descriptor_address_offsets[i]
        animation_set_descriptor_address_to_binary(
            AnimationSetDescriptorAddress(address=start, size=68), bin
        )
        bin.offset = start
        descriptor_offsets.append(start)
        # Pad the descriptor
        bin.pack_bytes(bytes((2 * 8 + 1) * 4))
        if self.interleaved:
            animation_set_to_binary(animation_set, i, start, names, bin)
    if not self.interleaved:
        for i, animation_set in enumerate(self.sets):
            animation_set_to_binary(animation_set, i, descriptor_offsets[i], names, bin)
