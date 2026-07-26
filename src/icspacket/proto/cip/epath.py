# This file is part of icspacket.
# Copyright (C) 2025-present  MatrixEditor @ github
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# pyright: reportUnannotatedClassAttribute=false
"""CIP EPATH segment codecs."""

import enum
import io

from caterpillar.py import (
    Branch,
    Bytes,
    Const,
    EnumFactory,
    Invisible,
    LittleEndian,
    Otherwise,
    Prefixed,
    StructDefMixin,
    When,
    bitfield,
    f,
    struct,
    this,
    uint8,
    uint16,
    uint32,
)
from caterpillar.types import uint8_t, uint16_t
from typing_extensions import Self, override


class LogicalType(enum.IntEnum):
    """Logical segment identifier (See CIP Volume 1, §3.5.3)."""

    CLASS = 0
    INSTANCE = 1
    MEMBER = 2
    CONNECTION_POINT = 3
    ATTRIBUTE = 4
    SPECIAL = 5
    SERVICE_ID = 6
    SERVICE = 6


@bitfield(order=LittleEndian)
class PortSegment(StructDefMixin):
    """Port segment, including short and extended link addresses.

    (See CIP Volume 1, §3.5.5.2.) ``port_low`` equal to ``0x0F`` is a
    reserved marker meaning the real port number is carried in the
    following 16-bit :attr:`ext_port` field instead of these 4 bits;
    :attr:`ext_link` marks a length-prefixed variable link address instead
    of the fixed single octet.

    This class does not subclass :class:`Segment` -- a ``@bitfield`` model
    can never be a frozen dataclass, and :class:`Segment` is frozen -- but
    it carries the same :attr:`TYPE_ID` tag :class:`EPATH` dispatches on,
    and :class:`~caterpillar.py.StructDefMixin` gives it :meth:`to_bytes`/
    :meth:`from_bytes` directly, with no separate encode/decode step.
    """

    TYPE_ID = 0x00

    s_type: f[int, 3] = 0
    ext_link: f[bool, 1] = False
    port_low: f[int, 4] = 0

    ext_len: f[int | None, uint8 // this.ext_link] = None
    ext_port: f[int | None, uint16 // (this.port_low == 0x0F)] = None
    link_address: f[
        bytes,
        Branch(
            When(this.ext_link, Bytes(this.ext_len)),
            Otherwise(Bytes(1)),
        ),
    ] = b"\x00"

    @property
    def port_id(self) -> int:
        """The logical port number, reassembled from
        ``port_low``/``ext_port``."""
        return self.ext_port if self.ext_port is not None else self.port_low

    @staticmethod
    def new(port_id: int, link_address: int | bytes = 0) -> "PortSegment":
        """Builds a port segment from a ``(port_id, link_address)`` pair."""
        link = (
            bytes([link_address])
            if isinstance(link_address, int)
            else bytes(link_address)
        )
        extended = port_id > 0x0E
        return PortSegment(
            ext_link=len(link) != 1,
            port_low=0x0F if extended else port_id,
            ext_len=len(link) if len(link) != 1 else None,
            ext_port=port_id if extended else None,
            link_address=link,
        )


@bitfield(order=LittleEndian)
class LogicalSegment(StructDefMixin):
    """Logical segment for class, instance, member, and related identifiers.

    (See CIP Volume 1, §3.5.3.) ``format_bits`` selects :attr:`value`'s wire
    width (``0``/``1``/``2`` for 8-/16-/32-bit). Use :meth:`new` or one of
    the per-kind factories below instead of setting ``format_bits``
    directly - they derive it from a plain ``width`` in octets, or pick the
    narrowest fit automatically when ``width`` is omitted.
    """

    TYPE_ID = 0x20

    s_type: f[int, 3] = 0b001
    logical_type: f[LogicalType | int, (3, EnumFactory(LogicalType))] = (
        LogicalType.CLASS
    )
    format_bits: f[int, 2] = 0

    value: f[
        int,
        Branch(
            When(this.format_bits == 0, uint8),
            When(this.format_bits == 1, uint16),
            Otherwise(uint32),
        ),
    ] = 0

    @property
    def width(self) -> int:
        """The width of :attr:`value` on the wire, in octets."""
        return {0: 1, 1: 2}.get(self.format_bits, 4)

    @staticmethod
    def new(
        kind: LogicalType | int, value: int, width: int | None = None
    ) -> "LogicalSegment":
        """Builds a logical segment, auto-selecting the narrowest value
        width."""
        if width is None:
            width = 1 if value <= 0xFF else 2 if value <= 0xFFFF else 4
        format_bits = {1: 0, 2: 1, 4: 2}[width]
        return LogicalSegment(logical_type=kind, format_bits=format_bits, value=value)

    @staticmethod
    def class_id(value: int, width: int | None = None) -> "LogicalSegment":
        """Construct a Class ID logical segment."""
        return LogicalSegment.new(LogicalType.CLASS, value, width)

    @staticmethod
    def instance_id(value: int, width: int | None = None) -> "LogicalSegment":
        """Construct an Instance ID logical segment."""
        return LogicalSegment.new(LogicalType.INSTANCE, value, width)

    @staticmethod
    def member_id(value: int, width: int | None = None) -> "LogicalSegment":
        """Construct a Member ID logical segment."""
        return LogicalSegment.new(LogicalType.MEMBER, value, width)

    @staticmethod
    def connection_point(value: int, width: int | None = None) -> "LogicalSegment":
        """Construct a Connection Point logical segment."""
        return LogicalSegment.new(LogicalType.CONNECTION_POINT, value, width)

    @staticmethod
    def attribute_id(value: int, width: int | None = None) -> "LogicalSegment":
        """Construct an Attribute ID logical segment."""
        return LogicalSegment.new(LogicalType.ATTRIBUTE, value, width)

    @staticmethod
    def special(value: int, width: int | None = None) -> "LogicalSegment":
        """Construct a Special logical segment."""
        return LogicalSegment.new(LogicalType.SPECIAL, value, width)

    @staticmethod
    def service_id(value: int, width: int | None = None) -> "LogicalSegment":
        """Construct a Service ID logical segment."""
        return LogicalSegment.new(LogicalType.SERVICE_ID, value, width)


@bitfield(order=LittleEndian)
class NetworkSegment(StructDefMixin):
    """Network segment with a subtype and opaque network-specific data.

    (See CIP Volume 1, §3.5.4.) A ``subtype`` below ``0x10`` ("fixed") always
    carries exactly one data octet with no length prefix; ``0x10`` and above
    ("variable") is preceded by a :attr:`words` octet counting the trailing
    :attr:`data` in 16-bit words.
    """

    TYPE_ID = 0x40

    s_type: f[int, 3] = 0b010
    subtype: f[int, 5] = 0

    words: f[int | None, uint8 // (this.subtype >= 0x10)] = None
    data: f[
        bytes,
        Branch(
            When(this.subtype < 0x10, Bytes(1)),
            Otherwise(Bytes(this.words * 2)),
        ),
    ] = b""

    @staticmethod
    def new(subtype: int, data: bytes = b"") -> "NetworkSegment":
        """Builds a network segment from a subtype and its payload."""
        data = bytes(data)
        words = len(data) // 2 if subtype >= 0x10 else None
        return NetworkSegment(subtype=subtype, words=words, data=data)


@struct(order=LittleEndian, kw_only=True)
class SymbolicSegment(StructDefMixin):
    """ANSI extended symbolic segment (See CIP Volume 1, §3.5.6)."""

    TYPE_ID = 0x91

    tag: f[int, Const(TYPE_ID, uint8)] = Invisible()
    value: f[bytes, Prefixed(uint8, Bytes(...))] = b""

    @property
    def symbol(self) -> str | bytes:
        """The symbol name, decoded as ASCII when possible."""
        try:
            return self.value.decode("ascii")
        except UnicodeDecodeError:
            return self.value

    @staticmethod
    def new(symbol: str | bytes) -> "SymbolicSegment":
        """Builds a symbolic segment from a ``str`` or raw ``bytes`` name."""
        value = symbol.encode("ascii") if isinstance(symbol, str) else bytes(symbol)
        return SymbolicSegment(value=value)


@struct(order=LittleEndian, kw_only=True)
class DataSegment(StructDefMixin):
    """Simple data segment (See CIP Volume 1, §3.5.7).

    :attr:`words` counts :attr:`data` in 16-bit words, so :attr:`data` is
    always word-aligned. A trailing zero octet is indistinguishable from a
    genuine data byte once round-tripped - :meth:`new` pads an odd-length
    input itself, matching the wire format's own inability to carry the
    original, pre-padding byte count.
    """

    TYPE_ID = 0x80

    tag: f[int, Const(TYPE_ID, uint8)] = Invisible()
    words: uint8_t = 0
    data: f[bytes, Bytes(this.words * 2)] = b""

    @staticmethod
    def new(data: bytes) -> "DataSegment":
        """Builds a data segment, padding odd-length input to a whole word."""
        data = bytes(data)
        if len(data) & 1:
            data += b"\x00"
        return DataSegment(words=len(data) // 2, data=data)


@struct(order=LittleEndian, kw_only=True)
class ElectronicKeySegment(StructDefMixin):
    """Electronic key segment (See CIP Volume 1, §3.5.8)."""

    TYPE_ID = 0x34

    tag: f[int, Const(TYPE_ID, uint8)] = Invisible()
    key_format: uint8_t = 0x04
    vendor_id: uint16_t = 0
    device_type: uint16_t = 0
    product_code: uint16_t = 0
    major_revision: uint8_t = 0
    minor_revision: uint8_t = 0


_SegmentT = (
    PortSegment
    | LogicalSegment
    | NetworkSegment
    | DataSegment
    | ElectronicKeySegment
    | SymbolicSegment
)

_DECODERS: dict[int, type] = {
    PortSegment.TYPE_ID: PortSegment,
    LogicalSegment.TYPE_ID: LogicalSegment,
    NetworkSegment.TYPE_ID: NetworkSegment,
    DataSegment.TYPE_ID: DataSegment,
    ElectronicKeySegment.TYPE_ID: ElectronicKeySegment,
    SymbolicSegment.TYPE_ID: SymbolicSegment,
}


def _decode_segment(data: bytes, offset: int) -> tuple[_SegmentT, int]:
    if offset >= len(data):
        raise ValueError("missing EPATH segment")

    header = data[offset]
    # 0x34 is also the logical-special segment discriminator.  The standard
    # electronic-key form has key-format 0x04, which disambiguates it.
    if (
        header == ElectronicKeySegment.TYPE_ID
        and offset + 10 <= len(data)
        and data[offset + 1] == 0x04
    ):
        decoder = ElectronicKeySegment
    elif header & 0xE0 == 0x20:
        decoder = LogicalSegment
    elif header == SymbolicSegment.TYPE_ID:
        decoder = SymbolicSegment
    elif header & 0xE0 == 0:
        decoder = PortSegment
    else:
        decoder = (
            _DECODERS.get(header & 0xE0)
            or _DECODERS.get(header & 0xF0)
            or _DECODERS.get(header)
        )
    if decoder is None:
        raise ValueError(f"unsupported EPATH segment type 0x{header:02x}")
    stream = io.BytesIO(data[offset:])
    segment = decoder.from_bytes(stream)
    return segment, offset + stream.tell()


class EPATH:
    """A sequence of CIP path segments.

    ``padded`` follows the normal CIP path representation: each segment ends
    on a 16-bit boundary.  ``packed`` is accepted as a convenience alias for
    the unpadded representation used by a few encapsulating services.
    """

    segments: tuple[_SegmentT, ...]

    def __init__(self, *segments: _SegmentT) -> None:
        self.segments = tuple(segments)

    def __iter__(self):
        return iter(self.segments)

    @override
    def __repr__(self) -> str:
        return f"<EPATH [{'|'.join([x.__class__.__name__ for x in self.segments])}]>"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EPATH):
            return NotImplemented
        return self.segments == other.segments

    def to_bytes(self, *, padded: bool = True, packed: bool | None = None) -> bytes:
        """Encode the path as padded or packed EPATH bytes."""
        if packed is not None:
            padded = not packed

        result = bytearray()
        for segment in self.segments:
            raw = segment.to_bytes()
            result.extend(raw)
            if padded and len(raw) & 1:
                result.append(0)

        if padded and len(result) & 1:
            result.append(0)
        return bytes(result)

    @property
    def word_length(self) -> int:
        """Length of the padded EPATH in 16-bit words."""
        encoded = self.to_bytes()
        return len(encoded) // 2

    @classmethod
    def from_bytes(
        cls: type[Self],
        data: bytes,
        *,
        padded: bool = True,
        packed: bool | None = None,
        length: int | None = None,
    ) -> Self:
        """Decode a padded or packed EPATH byte string."""

        if packed is not None:
            padded = not packed
        raw = bytes(data)
        if length is not None:
            if length < 0 or length * 2 > len(raw):
                raise ValueError("invalid EPATH word length")
            raw = raw[: length * 2]

        segments: list[_SegmentT] = []
        offset = 0
        while offset < len(raw):
            if len(raw) - offset == 1 and raw[offset] == 0:
                break
            segment, end = _decode_segment(raw, offset)
            segments.append(segment)
            if padded and (end - offset) & 1:
                end += 1
                if end > len(raw):
                    raise ValueError("missing EPATH padding octet")
            offset = end

        return cls(*segments)


def encode_epath(
    *segments: _SegmentT, padded: bool = True, packed: bool | None = None
) -> bytes:
    """Encode segments into an EPATH byte string."""

    return EPATH(*segments).to_bytes(padded=padded, packed=packed)


def decode_epath(
    data: bytes,
    *,
    padded: bool = True,
    packed: bool | None = None,
    length: int | None = None,
) -> EPATH:
    """Decode an EPATH byte string into segment objects."""

    return EPATH.from_bytes(data, padded=padded, packed=packed, length=length)


__all__ = [
    "EPATH",
    "DataSegment",
    "ElectronicKeySegment",
    "LogicalSegment",
    "LogicalType",
    "NetworkSegment",
    "PortSegment",
    "SymbolicSegment",
    "decode_epath",
    "encode_epath",
]
