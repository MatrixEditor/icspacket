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
"""[ODVA CIP Vol 1] CIP Connection Manager service codecs.

The request and response layouts are defined according to CIP Volume 1,
clause 3-5.5, Tables 3-5.8 through 3-5.24. Connection Manager fields are
little-endian and all EPATHs are represented as an even number of octets.
"""

import enum
from dataclasses import field

from caterpillar.context import this
from caterpillar.fields import Bytes, Padded, uint8
from caterpillar.model import EnumFactory, StructDefMixin
from caterpillar.shortcuts import LittleEndian, bitfield, f, struct
from caterpillar.types import uint8_t, uint16_t, uint32_t
from typing_extensions import Self

from .epath import EPATH
from .msgrouter import MessageRouterPath, MessageRouterRequest, path_bytes


class NetworkConnectionType(enum.IntEnum):
    """Values this library accepts for the Connection Type subfield packed
    into Network Connection Parameters (See CIP Vol 1, clause 3-5.5.1.1,
    Tables 3-5.8 and 3-5.9)."""

    NULL = 0
    MULTICAST = 1
    POINT_TO_POINT = 2


@bitfield(order=LittleEndian)
class NetworkConnectionParameters(StructDefMixin):
    """Wire layout for the UINT-sized form of Network Connection Parameters,
    as carried by a standard Forward_Open (See CIP Vol 1, clause 3-5.5.1.1,
    Table 3-5.8)."""

    redundant_owner: f[bool, 1] = False
    """True allows this connection to be held open by more than one owner
    at the same time."""

    connection_type: f[
        NetworkConnectionType | int, (2, EnumFactory(NetworkConnectionType))
    ] = NetworkConnectionType.NULL
    """Selects the ``NetworkConnectionType`` value (Null, Multicast, or
    Point to Point) for this connection."""

    reserved: f[bool, 1] = False
    """Reserved for future use; must always be encoded as zero."""

    priority: f[int, 2] = 0
    """Connection priority level: one of Low, High, Scheduled, or Urgent."""

    variable: f[bool, 1] = False
    """Data-size framing mode for the connection: ``False`` for fixed
    size, ``True`` for variable size."""

    connection_size: f[int, 9] = 0
    """Largest data size, in bytes, that this connection will carry."""


@bitfield(order=LittleEndian)
class LargeNetworkConnectionParameters(StructDefMixin):
    """Wire layout for the UDINT-sized form of Network Connection
    Parameters, as carried by a Large_Forward_Open (See CIP Vol 1, clause
    3-5.5.1.1, Table 3-5.9)."""

    redundant_owner: f[bool, 1] = False
    """True allows this connection to be held open by more than one owner
    at the same time."""

    connection_type: f[
        NetworkConnectionType | int, (2, EnumFactory(NetworkConnectionType))
    ] = NetworkConnectionType.NULL
    """Selects the ``NetworkConnectionType`` value (Null, Multicast, or
    Point to Point) for this connection."""

    reserved_high: f[int, 3] = 0
    """High-order bits reserved for future use; must always be encoded as
    zero."""

    priority: f[int, 2] = 0
    """Connection priority level: one of Low, High, Scheduled, or Urgent."""

    variable: f[bool, 1] = False
    """Data-size framing mode for the connection: ``False`` for fixed
    size, ``True`` for variable size."""

    reserved_low: f[int, 7] = 0
    """Low-order bits reserved for future use; must always be encoded as
    zero."""

    connection_size: f[int, 16] = 0
    """Largest data size, in bytes, that this connection will carry."""


class _PathMixin:
    """Shared ``connection_path`` friendly-constructor/view for the
    Forward_Open/Forward_Close request classes below. Expects the
    including class to declare ``connection_path_size``/``connection_path``
    struct fields."""

    @property
    def connection_epath(self) -> EPATH:
        """:attr:`connection_path`, parsed into an :class:`EPATH`."""
        # fmt: off
        return EPATH.from_bytes(self.connection_path)  # pyright: ignore[reportAttributeAccessIssue]

    @classmethod
    def new(
        cls: type[Self],
        *,
        connection_path: MessageRouterPath = b"",
        **fields: object,
    ) -> Self:
        """Builds a request, accepting a rich ``connection_path``
        (:class:`EPATH`, raw bytes, or an iterable of segments) instead of
        pre-encoded, word-counted bytes."""
        # fmt: off
        path = path_bytes(connection_path)
        return cls(connection_path_size=len(path) // 2, connection_path=path, **fields)  # pyright: ignore[reportCallIssue]


class _ApplicationReplyMixin:
    """Shared ``application_reply_data`` friendly constructor for the
    Forward_Open/Forward_Close response classes below. Expects the
    including class to declare ``application_reply_data_size``/
    ``application_reply_data`` struct fields."""

    @classmethod
    def new(
        cls: type[Self],
        *,
        application_reply_data: bytes = b"",
        **fields: object,
    ) -> Self:
        """Builds a response, padding odd-length ``application_reply_data``
        to a whole word."""

        data = bytes(application_reply_data)
        if len(data) & 1:
            data += b"\x00"
        # fmt: off
        return cls(
            application_reply_data_size=len(data) // 2,  # pyright: ignore[reportCallIssue]
            application_reply_data=data,  # pyright: ignore[reportCallIssue]
            **fields,
        )


@struct(order=LittleEndian, kw_only=True)
class _ForwardOpenHeaderPrefix(StructDefMixin):
    """Leading fields shared by the Forward_Open and Large_Forward_Open
    requests, before the direction-specific Network Connection Parameters
    (See CIP Vol 1, clause 3-5.5.2, Table 3-5.16)."""

    priority: uint8_t = 0
    """Priority/Time_tick value that, together with ``timeout_ticks``,
    determines how long the target waits before this request times out."""

    timeout_ticks: uint8_t = 0
    """Tick count that, together with ``priority``'s Time_tick value,
    determines how long the target waits before this request times out."""

    o_to_t_connection_id: uint32_t = 0
    """Connection ID this request assigns to the originator-to-target
    direction; the value the originator uses as its Produced Connection
    ID."""

    t_to_o_connection_id: uint32_t = 0
    """Connection ID this request assigns to the target-to-originator
    direction; the value the originator uses as its Consumed Connection
    ID."""

    connection_serial_number: uint16_t = 0
    """Arbitrary serial number the originator generates to distinguish
    this connection instance from others it has opened."""

    originator_vendor_id: uint16_t = 0
    """Vendor ID identifying the originating device."""

    originator_serial_number: uint32_t = 0
    """Serial number identifying the originating device."""

    timeout_multiplier: uint8_t = 0
    """Scale factor applied to the RPI when the target derives this
    connection's inactivity timeout."""

    reserved_timeout: f[list[int], uint8[3]] = field(default_factory=lambda: [0, 0, 0])
    """Bytes reserved for future use, immediately following
    ``timeout_multiplier``; must always be encoded as zero."""

    o_to_t_rpi: uint32_t = 0
    """Requested packet interval, in microseconds, for data flowing from
    originator to target."""


@struct(order=LittleEndian, kw_only=True)
class ForwardOpenRequest(_PathMixin, _ForwardOpenHeaderPrefix):
    """Builds and parses the standard-size Forward_Open request body used
    to open a new CIP connection (See CIP Vol 1, clause 3-5.5.2, Table
    3-5.16)."""

    o_to_t_parameters: NetworkConnectionParameters = field(
        default_factory=NetworkConnectionParameters
    )
    """Network Connection Parameters bitfield describing the
    originator-to-target data flow."""

    t_to_o_rpi: uint32_t = 0
    """Requested packet interval, in microseconds, for data flowing from
    target to originator."""

    t_to_o_parameters: NetworkConnectionParameters = field(
        default_factory=NetworkConnectionParameters
    )
    """Network Connection Parameters bitfield describing the
    target-to-originator data flow."""

    transport_trigger: uint8_t = 0
    """Byte selecting this connection's transport class together with its
    production trigger behavior."""

    connection_path_size: uint8_t = 0
    """Length of :attr:`connection_path`, counted in 16-bit words."""

    connection_path: f[bytes, Bytes(this.connection_path_size * 2)] = b""
    """Raw, padded EPATH bytes identifying the route to establish. Use
    :meth:`new`/:attr:`connection_epath` for the rich :class:`EPATH`
    view."""


@struct(order=LittleEndian, kw_only=True)
class LargeForwardOpenRequest(_PathMixin, _ForwardOpenHeaderPrefix):
    """Builds and parses the Forward_Open request body used when the
    connection needs a larger connection-size range than the standard
    format allows (See CIP Vol 1, clause 3-5.5.2, Table 3-5.16)."""

    o_to_t_parameters: LargeNetworkConnectionParameters = field(
        default_factory=LargeNetworkConnectionParameters
    )
    """Large-format Network Connection Parameters bitfield describing the
    originator-to-target data flow."""

    t_to_o_rpi: uint32_t = 0
    """Requested packet interval, in microseconds, for data flowing from
    target to originator."""

    t_to_o_parameters: LargeNetworkConnectionParameters = field(
        default_factory=LargeNetworkConnectionParameters
    )
    """Large-format Network Connection Parameters bitfield describing the
    target-to-originator data flow."""

    transport_trigger: uint8_t = 0
    """Byte selecting this connection's transport class together with its
    production trigger behavior."""

    connection_path_size: uint8_t = 0
    """Length of :attr:`connection_path`, counted in 16-bit words."""

    connection_path: f[bytes, Bytes(this.connection_path_size * 2)] = b""
    """Raw, padded EPATH bytes identifying the route to establish. Use
    :meth:`new`/:attr:`connection_epath` for the rich :class:`EPATH`
    view."""


@struct(order=LittleEndian, kw_only=True)
class ForwardOpenResponse(_ApplicationReplyMixin, StructDefMixin):
    """Builds and parses the body of a successful Forward_Open or
    Large_Forward_Open reply, shared by both request sizes (See CIP Vol 1,
    clause 3-5.5.2, Table 3-5.17)."""

    o_to_t_connection_id: uint32_t = 0
    """Connection ID the target assigned to the originator-to-target
    direction; the target's Consumed Connection ID."""

    t_to_o_connection_id: uint32_t = 0
    """Connection ID the target assigned to the target-to-originator
    direction; the target's Produced Connection ID."""

    connection_serial_number: uint16_t = 0
    """Echo of the ``connection_serial_number`` sent in the matching
    Forward_Open request."""

    originator_vendor_id: uint16_t = 0
    """Echo of the ``originator_vendor_id`` sent in the matching
    Forward_Open request."""

    originator_serial_number: uint32_t = 0
    """Echo of the ``originator_serial_number`` sent in the matching
    Forward_Open request."""

    o_to_t_api: uint32_t = 0
    """Actual packet rate, in microseconds, that will be used from
    originator to target."""

    t_to_o_api: uint32_t = 0
    """Actual packet rate, in microseconds, that will be used from target
    to originator."""

    application_reply_data_size: uint8_t = 0
    """Length of :attr:`application_reply_data`, counted in 16-bit
    words."""

    reserved: uint8_t = 0
    """Byte reserved for future use; must always be encoded as zero."""

    application_reply_data: f[bytes, Bytes(this.application_reply_data_size * 2)] = b""
    """Application-specific reply data following the fixed header. Use
    :meth:`new` to pad odd-length input automatically."""


@struct(order=LittleEndian, kw_only=True)
class ForwardCloseRequest(_PathMixin, StructDefMixin):
    """Builds and parses the body of a Forward_Close request used to tear
    down a previously opened CIP connection (See CIP Vol 1, clause
    3-5.5.3, Table 3-5.19)."""

    priority: uint8_t = 0
    """Priority/Time_tick value that, together with ``timeout_ticks``,
    determines how long the target waits before this request times out."""

    timeout_ticks: uint8_t = 0
    """Tick count that, together with ``priority``'s Time_tick value,
    determines how long the target waits before this request times out."""

    connection_serial_number: uint16_t = 0
    """Serial number identifying the specific connection instance being
    closed."""

    originator_vendor_id: uint16_t = 0
    """Vendor ID identifying the originating device."""

    originator_serial_number: uint32_t = 0
    """Serial number identifying the originating device."""

    connection_path_size: uint8_t = 0
    """Length of :attr:`connection_path`, counted in 16-bit words."""

    reserved: uint8_t = 0
    """Byte reserved for future use; must always be encoded as zero."""

    connection_path: f[bytes, Bytes(this.connection_path_size * 2)] = b""
    """Raw, padded EPATH bytes identifying the route to close. Use
    :meth:`new`/:attr:`connection_epath` for the rich :class:`EPATH`
    view."""


@struct(order=LittleEndian, kw_only=True)
class ForwardCloseResponse(_ApplicationReplyMixin, StructDefMixin):
    """Builds and parses the body of a successful Forward_Close reply (See
    CIP Vol 1, clause 3-5.5.3, Table 3-5.20)."""

    connection_serial_number: uint16_t = 0
    """Echo of the ``connection_serial_number`` sent in the matching
    Forward_Close request."""

    originator_vendor_id: uint16_t = 0
    """Echo of the ``originator_vendor_id`` sent in the matching
    Forward_Close request."""

    originator_serial_number: uint32_t = 0
    """Echo of the ``originator_serial_number`` sent in the matching
    Forward_Close request."""

    application_reply_data_size: uint8_t = 0
    """Length of :attr:`application_reply_data`, counted in 16-bit
    words."""

    reserved: uint8_t = 0
    """Byte reserved for future use; must always be encoded as zero."""

    application_reply_data: f[bytes, Bytes(this.application_reply_data_size * 2)] = b""
    """Application-specific reply data following the fixed header. Use
    :meth:`new` to pad odd-length input automatically."""


@struct(order=LittleEndian, kw_only=True)
class UnconnectedSendRequest(StructDefMixin):
    """Builds and parses the body of an Unconnected_Send request, which
    wraps another Message Router request for routing over an unconnected
    path (See CIP Vol 1, clause 3-5.5.4, Table 3-5.22)."""

    priority: uint8_t = 0
    """Priority/Time_tick value that, together with ``timeout_ticks``,
    determines how long the target waits before this request times out."""

    timeout_ticks: uint8_t = 0
    """Tick count that, together with ``priority``'s Time_tick value,
    determines how long the target waits before this request times out."""

    message_request_size: uint16_t = 0
    """Length, in bytes, of :attr:`message_request` (not 16-bit words, as
    :attr:`route_path_size` below counts)."""

    message_request: f[
        bytes,
        Padded(
            Bytes(this.message_request_size),
            after=this.message_request_size & 1,
        ),
    ] = b""
    """Embedded Message Router request bytes; a pad byte follows on the
    wire whenever :attr:`message_request_size` is odd."""

    route_path_size: uint8_t = 0
    """Length of :attr:`route_path`, counted in 16-bit words."""

    reserved: uint8_t = 0
    """Byte reserved for future use; must always be encoded as zero."""

    route_path: f[bytes, Bytes(this.route_path_size * 2)] = b""
    """Raw, padded EPATH bytes identifying the route to the embedded
    request's target. Use :meth:`new`/:attr:`route_epath` for the rich
    :class:`EPATH` view."""

    @property
    def route_epath(self) -> EPATH:
        """:attr:`route_path`, parsed into an :class:`EPATH`."""

        return EPATH.from_bytes(self.route_path)

    @classmethod
    def new(
        cls: type[Self],
        message_request: MessageRouterRequest | bytes | bytearray = b"",
        route_path: MessageRouterPath = b"",
        *,
        priority: int = 0,
        timeout_ticks: int = 0,
    ) -> Self:
        """Builds a request from a :class:`MessageRouterRequest` (or raw
        bytes) and a rich ``route_path`` (:class:`EPATH`, raw bytes, or an
        iterable of segments)."""

        request_raw = (
            message_request.to_bytes()
            if isinstance(message_request, MessageRouterRequest)
            else bytes(message_request)
        )
        route_raw = path_bytes(route_path)
        return cls(
            priority=priority,
            timeout_ticks=timeout_ticks,
            message_request_size=len(request_raw),
            message_request=request_raw,
            route_path_size=len(route_raw) // 2,
            route_path=route_raw,
        )


__all__ = [
    "ForwardCloseRequest",
    "ForwardCloseResponse",
    "ForwardOpenRequest",
    "ForwardOpenResponse",
    "LargeForwardOpenRequest",
    "LargeNetworkConnectionParameters",
    "NetworkConnectionParameters",
    "NetworkConnectionType",
    "UnconnectedSendRequest",
]
