from typing import Any, Optional
import struct

import numpy as np

from .common import NumpyDType, NumpyArray
from . import errors


# This value should be a large value which is implausible to come across as a
# length of a vertex array.
HIGH_VERTEX_COUNT: int = 10000000


class PackBin:
    def __init__(self) -> None:
        self.raw: bytearray = bytearray()
        self.offset: int = 0

    def pack(self, format: str, *args: Any) -> None:
        s = struct.Struct(format)
        extra_needed = self.offset + s.size - len(self.raw)
        if extra_needed > 0:
            self.raw.extend(bytearray(extra_needed))
        s.pack_into(self.raw, self.offset, *args)
        self.offset += s.size

    def pack_at(self, pos: int, format: str, *args: Any) -> int:
        """Returns the size of the packed struct"""
        s = struct.Struct(format)
        extra_needed = pos + s.size - len(self.raw)
        if extra_needed > 0:
            self.raw.extend(bytearray(extra_needed))
        s.pack_into(self.raw, pos, *args)
        return s.size

    def pack_bytes(self, raw: bytes) -> None:
        self.offset += self.pack_bytes_at(self.offset, raw)

    def pack_bytes_at(self, pos: int, raw: bytes) -> int:
        """Returns the size of the packed bytes"""
        return self.pack_at(pos, str(len(raw)) + "s", raw)

    def bytes(self) -> bytes:
        return bytes(self.raw)

    def pad_alignment(self, boundary: int) -> None:
        """Zero pad until an alignment boundary"""
        (_, remainder) = divmod(self.offset, boundary)
        if remainder == 0:
            return
        else:
            self.pack_bytes(bytes(boundary - remainder))

    def pack_null_terminated_string(self, string: str) -> None:
        for c in string:
            self.pack("c", c.encode("latin1"))
        self.pack("B", 0)

    def pack_length_prefixed_numpy_array(
        self,
        arr: NumpyArray,
        divisor: int = 1,
    ) -> None:
        self.pack("<I", len(arr) * divisor)
        self.pack_bytes(arr.tobytes())


class UnpackBin:
    def __init__(self, raw: bytes):
        self.raw: bytes = raw
        self.offset: int = 0
        self.overflow: int = len(raw)
        self.overflow_message: str = "default"
        """In cases where we know the size of the data, setting this value
        appropriately can help catch overflow bugs caused by a bad parser.
        """

    def unpack(self, format: str) -> Any:
        s = struct.Struct(format)
        if s.size + self.offset > self.overflow:
            raise errors.E0028(
                fmt=format,
                context=self.overflow_message,
                overflow_offset=self.overflow,
                actual_offset=self.offset,
            )
        r = s.unpack_from(self.raw, self.offset)
        self.offset += s.size
        return r

    def unpack_bytes(self, size: int) -> bytes:
        if size + self.offset > self.overflow:
            raise errors.E0029(
                context=self.overflow_message,
                overflow_size=str(size + self.offset - self.overflow),
            )
        if size < 0:
            return b""
        b = self.raw[self.offset : self.offset + size]
        self.offset += size
        return b

    def unpack_bytes_from(self, pos: int, size: int) -> bytes:
        if size + pos > self.overflow:
            raise errors.E0030(
                context=self.overflow_message,
                position=hex(pos),
            )
        return self.raw[pos : pos + size]

    def remaining(self) -> int:
        return len(self.raw) - self.offset

    def pad_alignment_unchecked(self, boundary: int) -> Optional[bytes]:
        (_, remainder) = divmod(self.offset, boundary)
        if remainder == 0:
            return None
        else:
            padding = self.unpack_bytes(boundary - remainder)
            if all(map(lambda b: b == 0, padding)):
                return None
            else:
                return padding

    def pad_alignment(self, boundary: int) -> None:
        padding = self.pad_alignment_unchecked(boundary)
        if padding is not None:
            raise errors.E0031(contents=str(padding))

    def unpack_null_terminated_string(self) -> str:
        raw = b""
        while True:
            (c,) = self.unpack("c")
            if c == b"\x00":
                break
            raw += c
        # RBR seems to use latin1 encoding
        return raw.decode("latin1")

    def unpack_length_prefixed_numpy_array(
        self,
        dtype: NumpyDType,
        divisor: int = 1,
    ) -> NumpyArray:
        (length,) = self.unpack("<I")
        assert_count_is_reasonable(
            "unpack_length_prefixed_numpy_array",
            length,
            HIGH_VERTEX_COUNT,
        )
        (divided, rem) = divmod(length, divisor)
        if rem != 0:
            raise errors.E0032(
                length=length,
                divisor=divisor,
            )
        raw = self.unpack_bytes(dtype.itemsize * divided)
        return np.frombuffer(raw, dtype=dtype)


def assert_count_is_reasonable(loc: str, count: int, suspicious_count: int) -> None:
    """Check that a parsed index is actually plausible. This helps finding
    errors where we've not actually located the correct index.
    """
    if count > suspicious_count:
        if count > suspicious_count:
            raise errors.E0033(loc=loc, count=count)
