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
"""[ODVA CIP Vol 1] CIP Message Router request and response codecs.

The layouts implemented here are defined according to CIP Volume 1, clause
2-4, Tables 2-4.1 and 2-4.2.
"""
import itertools
from collections.abc import Iterable
from dataclasses import field
from typing import TypeAlias

from caterpillar.py import (
    Bytes,
    StructDefMixin,
    this,
    uint8,
    uint16,
)
from caterpillar.shortcuts import LittleEndian, f, struct
from caterpillar.types import uint8_t
from typing_extensions import Self

from .const import CommonService, GeneralStatus
from .epath import (
    EPATH,
    DataSegment,
    ElectronicKeySegment,
    LogicalSegment,
    NetworkSegment,
    PortSegment,
    SymbolicSegment,
)

_Segment = (
    PortSegment
    | LogicalSegment
    | NetworkSegment
    | SymbolicSegment
    | DataSegment
    | ElectronicKeySegment
)
MessageRouterPath: TypeAlias = EPATH | bytes | bytearray | Iterable[_Segment]


def path_bytes(path: MessageRouterPath) -> bytes:
    if isinstance(path, EPATH):
        raw = path.to_bytes(padded=True)
    elif isinstance(path, (bytes, bytearray)):
        raw = bytes(path)
    else:
        raw = EPATH(*tuple(path)).to_bytes(padded=True)
    if len(raw) & 1:
        raw += b"\0"
    return raw


def _split_entries(count: int, offsets: list[int], payload: bytes) -> list[bytes]:
    table_end = 2 + 2 * count
    bounds = [*offsets, table_end + len(payload)]
    return [
        payload[start - table_end : end - table_end]
        for start, end in itertools.pairwise(bounds)
    ]


@struct(order=LittleEndian, kw_only=True)
class MessageRouterRequest(StructDefMixin):
    """A Message Router request (See CIP Vol 1, clause 2-4, Table 2-4.1)."""

    service: uint8_t = 0
    """Numeric code naming the CIP service this request invokes."""

    path_size: uint8_t = 0
    """Length of :attr:`path`, counted in 16-bit words."""

    path: f[bytes, Bytes(this.path_size * 2)] = b""
    """Raw, padded EPATH bytes naming the request's target. Use
    :meth:`new`/:attr:`epath` for the rich :class:`EPATH` view."""

    request_data: f[bytes, Bytes(...)] = b""
    """Service-specific request data following the request path."""

    @property
    def epath(self) -> EPATH:
        """:attr:`path`, parsed into an :class:`EPATH`."""

        return EPATH.from_bytes(self.path)

    @classmethod
    def new(
        cls: type[Self],
        service: int,
        path: MessageRouterPath = b"",
        request_data: bytes = b"",
    ) -> Self:
        """Builds a request, accepting a rich ``path`` (:class:`EPATH`, raw
        bytes, or an iterable of segments) instead of pre-encoded,
        word-counted bytes."""

        raw = path_bytes(path)
        return cls(
            service=service,
            path_size=len(raw) // 2,
            path=raw,
            request_data=request_data,
        )


@struct(order=LittleEndian, kw_only=True)
class MessageRouterResponse(StructDefMixin):
    """A Message Router response (See CIP Vol 1, clause 2-4, Table 2-4.2)."""

    reply_service: uint8_t = 0
    """Service code being answered, echoed back with its top reply bit
    set."""

    reserved: uint8_t = 0
    """Byte reserved for future use; must always be encoded as zero."""

    general_status: uint8_t = 0
    """Outcome of the request; compare against ``GeneralStatus`` values."""

    # directly integrated with compact [prefix::] prefix syntax
    # additional_status_size: f[
    #     int, AsLengthRef("additional_status_size", "additional_status", uint8)
    # ] = 0
    # """Word count of :attr:`additional_status`; kept in sync automatically
    # when constructed from ``additional_status`` directly."""

    additional_status: f[list[int], uint16[uint8::]] = field(default_factory=list)
    """Extra 16-bit status words supplying detail beyond the single
    general-status byte, when the responder provides any."""

    response_data: f[bytes, Bytes(...)] = b""
    """Service-specific reply data following the fixed status fields."""

    @property
    def service(self) -> int:
        """Original request service code with the reply bit removed."""

        return self.reply_service & 0x7F

    @property
    def is_success(self) -> bool:
        """Whether the response general status is Success."""

        return int(self.general_status) == int(GeneralStatus.SUCCESS)

    @classmethod
    def new(
        cls: type[Self],
        service: int,
        general_status: GeneralStatus | int = GeneralStatus.SUCCESS,
        additional_status: Iterable[int] = (),
        response_data: bytes = b"",
    ) -> Self:
        """Builds a response, deriving ``reply_service`` from ``service``
        (i.e. ``service`` with the reply bit set)."""

        return cls(
            reply_service=int(service) | 0x80,
            general_status=general_status,
            additional_status=list(additional_status),
            response_data=response_data,
        )


@struct(order=LittleEndian, kw_only=True)
class MultipleServicePacket(StructDefMixin):
    """Helper for common service ``0x0A`` (See CIP Vol 1, clause A-4.10,
    Tables A-4.17 and A-4.18).

    Each embedded Message Router request/reply carries no length of its
    own on the wire, so :attr:`payload` cannot be split back into
    individual entries by a declarative field alone; use
    :meth:`build`/:meth:`decode_requests`/:meth:`decode_replies` to move
    between :attr:`payload` and rich request/reply lists.
    """

    # directly integrated
    # count: f[int, AsLengthRef("count", "offsets", uint16)] = 0
    # """Number of embedded services; kept in sync automatically by
    # :meth:`build`."""

    offsets: f[list[int], uint16[uint16::]] = field(default_factory=list)
    """Byte offset of each embedded service, measured from the start of
    this packet. Populated by :meth:`build`."""

    payload: f[bytes, Bytes(...)] = b""
    """Raw, concatenated embedded-service bytes. Populated by
    :meth:`build`; split back into entries via :meth:`decode_requests`/
    :meth:`decode_replies`."""

    def build(self, requests: Iterable[MessageRouterRequest]) -> bytes:
        """Encodes ``requests``, recomputing :attr:`offsets`/
        :attr:`payload`, and returns the fully encoded packet."""

        encoded = [request.to_bytes() for request in requests]
        offset = 2 + 2 * len(encoded)
        offsets: list[int] = []
        for item in encoded:
            offsets.append(offset)
            offset += len(item)
        self.offsets = offsets
        self.payload = b"".join(encoded)
        return self.to_bytes()

    def request(self, path: MessageRouterPath = b"") -> MessageRouterRequest:
        """Wrap this packet in a Message Router service ``0x0A``
        request."""

        return MessageRouterRequest.new(
            CommonService.MULTIPLE_SERVICE_PACKET, path, self.to_bytes()
        )

    def decode_requests(self) -> list[MessageRouterRequest]:
        """Splits :attr:`payload` back into individual embedded
        requests."""

        entries = _split_entries(len(self.offsets), self.offsets, self.payload)
        return [MessageRouterRequest.from_bytes(raw) for raw in entries]

    def decode_replies(self) -> list[MessageRouterResponse]:
        """Splits :attr:`payload` back into individual embedded replies
        (See CIP Volume 1, clause A-4.10.3, Table A-4.18)."""

        entries = _split_entries(len(self.offsets), self.offsets, self.payload)
        return [MessageRouterResponse.from_bytes(raw) for raw in entries]


__all__ = [
    "MessageRouterPath",
    "MessageRouterRequest",
    "MessageRouterResponse",
    "MultipleServicePacket",
]
