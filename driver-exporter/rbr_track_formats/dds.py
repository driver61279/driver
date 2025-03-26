"""DDS files the only supported texture format for RBR tracks.

We need to parse the header in order to automatically fill out some parts of
the INI files.

https://docs.microsoft.com/en-us/windows/win32/direct3ddds/dds-header
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, BinaryIO
import enum

from .binary import UnpackBin
from . import errors


class DXTCodec(enum.Enum):
    DXT1 = 1
    DXT2 = 2
    DXT3 = 3
    DXT4 = 4
    DXT5 = 5


DDS_MAGIC: bytes = b"DDS "

FLAG_DDSD_CAPS: int = 0x1
FLAG_DDSD_HEIGHT: int = 0x2
FLAG_DDSD_WIDTH: int = 0x4
FLAG_DDSD_PIXELFORMAT: int = 0x1000
FLAG_DDSD_MIPMAPCOUNT: int = 0x20000


class DDS_PIXELFORMAT_FLAGS(enum.Flag):
    ALPHAPIXELS = 0x1
    ALPHA = 0x2
    FOURCC = 0x4
    RGB = 0x40
    YUV = 0x200
    LUMINANCE = 0x20000


@dataclass
class DDS:
    """
    This class contains useful information which can be easily parsed from DDS
    files.

    height
        Height in pixels
    width
        Width in pixels
    mip_levels
        Number of levels of detail in the texture file, if it is mipmapped
    alpha_data
        Texture contains alpha data
    codec
        The DXT compression codec used
    """

    height: int
    width: int
    mip_levels: Optional[int]
    alpha_data: bool
    codec: DXTCodec

    @staticmethod
    def from_binary_io(io: BinaryIO) -> DDS:
        bin = UnpackBin(io.read(0x80))
        magic = bin.unpack_bytes(4)
        if magic != DDS_MAGIC:
            raise errors.E0035(actual_magic=str(magic), expected_magic=str(DDS_MAGIC))
        (_size, flags) = bin.unpack("<II")
        if not (flags & FLAG_DDSD_CAPS):
            raise errors.E0036(flag="DDSD_CAPS")
        if not (flags & FLAG_DDSD_HEIGHT):
            raise errors.E0036(flag="DDSD_HEIGHT")
        if not (flags & FLAG_DDSD_WIDTH):
            raise errors.E0036(flag="DDSD_WIDTH")
        if not (flags & FLAG_DDSD_PIXELFORMAT):
            raise errors.E0036(flag="DDSD_PIXELFORMAT")
        is_mipmapped = flags & FLAG_DDSD_MIPMAPCOUNT
        (height, width) = bin.unpack("<II")
        (_pitch, _depth) = bin.unpack("<II")
        (mip_levels,) = bin.unpack("<I")
        bin.unpack_bytes(4 * 11)
        (pfsize, raw_pxflags) = bin.unpack("<II")
        if pfsize != 32:
            raise errors.E0037(actual_size=pfsize, expected_size=32)
        pxflags = DDS_PIXELFORMAT_FLAGS(raw_pxflags)
        if not (pxflags & DDS_PIXELFORMAT_FLAGS.FOURCC):
            raise errors.E0038()
        fourcc = bin.unpack_bytes(4)
        fourcc_ascii = fourcc.decode("ascii")
        try:
            codec = DXTCodec[fourcc_ascii]
        except KeyError:
            raise errors.E0039(ascii_codec=fourcc_ascii)
        # (_rgbbitcount,) = bin.unpack("<I")
        # (_bm_r, _bm_g, _bm_b, _bm_a) = bin.unpack("<IIII")
        return DDS(
            height=height,
            width=width,
            mip_levels=mip_levels if is_mipmapped else None,
            alpha_data=bool(pxflags & DDS_PIXELFORMAT_FLAGS.ALPHA),
            codec=codec,
        )

    @staticmethod
    def from_file(file: str) -> DDS:
        with open(file, "rb") as io:
            try:
                return DDS.from_binary_io(io)
            except errors.RBRAddonError as e:
                raise errors.E0040(
                    inner_error=e,
                    file_name=file,
                )
