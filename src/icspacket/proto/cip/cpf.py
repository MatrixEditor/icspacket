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
"""[ODVA CIP Vol 2] EtherNet/IP Common Packet Format codecs."""

import enum
import ipaddress
from collections.abc import Callable
from dataclasses import field
from typing import Any

from caterpillar.abc import _ContextLike
from caterpillar.py import (
    AsLengthRef,
    Bytes,
    Prefixed,
    StructDefMixin,
    Transformer,
    this,
    uint8,
    uint16,
)
from caterpillar.shortcuts import BigEndian, F, LittleEndian, f, struct
from caterpillar.types import ipv4_t, uint8_t, uint16_t, uint32_t
from typing_extensions import Self, TypeVar, overload, override


class CPFItemType(enum.IntEnum):
    """Common Packet Format item type identifiers (See CIP Volume 2, clause
    2-6.1, Table 2-6.3)."""

    NULL_ADDRESS = 0x0000
    LIST_IDENTITY = 0x000C
    CONNECTED_ADDRESS = 0x00A1
    CONNECTED_DATA = 0x00B1
    UNCONNECTED_DATA = 0x00B2
    LIST_SERVICES = 0x0100
    SOCKADDR_INFO_OT = 0x8000
    SOCKADDR_INFO_TO = 0x8001
    SEQUENCED_ADDRESS = 0x8002


class _FixedServiceName(Transformer):
    """Encode and decode the List Services service name.

    According to Vol2, Table 2-4.11, this is specified as a fixed ARRAY of 16
    USINT, and that's what we emit when encoding. Some real-world
    implementations (e.g. cpppo) instead send a variable-length, NUL-terminated
    name whose true length is bounded only by the enclosing CPF item's declared
    length -- so decoding reads whatever bytes remain in the item rather than
    requiring exactly 16.
    """

    def __init__(self) -> None:
        super().__init__(Bytes(...))

    @override
    def encode(self, obj: str | bytes, context: object) -> bytes:
        """Encode a ListServices name as a fixed 16-octet field."""

        value = obj.encode("ascii") if isinstance(obj, str) else bytes(obj)
        if len(value) > 16:
            raise ValueError("service_name is limited to 16 octets")
        return value.ljust(16, b"\0")

    @override
    def decode(self, parsed: bytes, context: object) -> str | bytes:
        """Decode a ListServices name, stripping trailing NUL padding."""

        value = bytes(parsed).rstrip(b"\0")
        try:
            return value.decode("ascii")
        except UnicodeDecodeError:
            return value


@struct(order=BigEndian)
class SockaddrInfo(StructDefMixin):
    """Address and port pair embedded in CPF discovery items so a target device
    can advertise how it can be reached (See CIP Volume 2, clause 2-6.3.3,
    Table 2-6.9)."""

    family: uint16_t = 2
    """Selects the addressing scheme in use; this codec only builds and expects
    the IPv4 form, so the value is always 2 (AF_INET)."""

    port: uint16_t = 0
    """UDP port number the advertised CIP endpoint listens on."""

    address: ipv4_t = ipaddress.IPv4Address("0.0.0.0")
    """IPv4 address of the advertised CIP endpoint."""

    zero: f[bytes, Bytes(8)] = b"\0" * 8
    """Unused 8-byte filler with no defined meaning; callers should leave it
    zeroed."""

    def __post_init__(self) -> None:
        self.address = ipaddress.IPv4Address(self.address)


_T = TypeVar("_T")

#: Registry of CPF item structs by item type ID.
__cpf_items__: dict[int, type[StructDefMixin]] = {}


def register_cpf_item(type_id: int | CPFItemType, item_cls: type[_T]) -> type[_T]:
    """Register the struct used to decode a CPF item type.

    Most callers should use the :func:`cpf_item` decorator instead, which
    derives ``type_id`` from the class automatically; this is exposed
    directly for the rarer case of registering a struct that isn't itself
    decorated (e.g. reusing one struct across several item types).
    """

    __cpf_items__[int(type_id)] = item_cls  # pyright: ignore[reportArgumentType]
    return item_cls


@overload
def cpf_item(cls: type[_T]) -> type[_T]: ...
@overload
def cpf_item(cls: None = None) -> Callable[[type[_T]], type[_T]]: ...
def cpf_item(cls: type[_T] | None = None) -> type[_T] | Callable[[type[_T]], type[_T]]:
    """Decorator to register a CPF item struct for its ``TYPE_ID``."""

    def decorator(item_cls: type[_T]) -> type[_T]:
        type_id = getattr(item_cls, "TYPE_ID", None)
        if not isinstance(type_id, (int, CPFItemType)):
            raise TypeError(f"CPF item class {item_cls.__name__} must define TYPE_ID")
        return register_cpf_item(type_id, item_cls)

    if cls is None:
        return decorator
    return decorator(cls)


def _cpf_item_type(type_id: int) -> type[StructDefMixin] | None:
    """Look up the struct registered for a CPF item type ID, if any."""

    return __cpf_items__.get(int(type_id))


@cpf_item
@struct(order=LittleEndian)
class NullAddressItem(StructDefMixin):
    """Null Address CPF item (See CIP Volume 2, clause 2-6.2.1, Table 2-6.4)."""

    # NOTE: it is important to omit the type annotation here in order
    # for caterpillar to ignore this field
    TYPE_ID = CPFItemType.NULL_ADDRESS


@cpf_item
@struct(order=LittleEndian)
class UnconnectedDataItem(StructDefMixin):
    """Unconnected Data CPF item (See CIP Volume 2, clause 2-6.3.1, Table
    2-6.7)."""

    TYPE_ID = CPFItemType.UNCONNECTED_DATA

    data: f[bytes, Bytes(...)] = b""


@cpf_item
@struct(order=LittleEndian)
class ConnectedAddressItem(StructDefMixin):
    """Connected Address CPF item (See CIP Volume 2, clause 2-6.2.2, Table
    2-6.5)."""

    TYPE_ID = CPFItemType.CONNECTED_ADDRESS

    connection_id: uint32_t
    """Numeric ID naming the connection this address item is directed at."""


@cpf_item
@struct(order=LittleEndian)
class ConnectedDataItem(StructDefMixin):
    """Connected Data CPF item (See CIP Volume 2, clause 2-6.3.2, Table
    2-6.8)."""

    TYPE_ID = CPFItemType.CONNECTED_DATA

    data: f[bytes, Bytes(...)] = b""


@cpf_item
@struct(order=LittleEndian)
class SequencedAddressItem(StructDefMixin):
    """Sequenced Address CPF item (See CIP Volume 2, clause 2-6.2.3, Table
    2-6.6)."""

    TYPE_ID = CPFItemType.SEQUENCED_ADDRESS

    connection_id: uint32_t
    """Numeric ID naming which open connection this sequenced item belongs
    to."""

    sequence_number: uint32_t
    """Running counter carried alongside the connection ID so the receiver can
    order this connection's I/O messages."""


@cpf_item
@struct
class SockaddrInfoItem(StructDefMixin):
    """Base CPF item for originator/target socket-address information (See CIP
    Volume 2, clause 2-6.3.3, Table 2-6.9)."""

    TYPE_ID = CPFItemType.SOCKADDR_INFO_OT

    address_info: SockaddrInfo

    @property
    def family(self) -> int:
        """Address family from the embedded socket address."""

        return self.address_info.family

    @property
    def port(self) -> int:
        """TCP or UDP port from the embedded socket address."""

        return self.address_info.port

    @property
    def address(self) -> ipaddress.IPv4Address:
        """IPv4 address from the embedded socket address."""

        return self.address_info.address


@cpf_item
@struct
class SockaddrInfoOTItem(SockaddrInfoItem):
    """Originator-to-target Sockaddr Info CPF item (See CIP Volume 2, clause
    2-6.3.3, Table 2-6.9)."""

    TYPE_ID = CPFItemType.SOCKADDR_INFO_OT


@cpf_item
@struct
class SockaddrInfoTOItem(SockaddrInfoItem):
    """Target-to-originator Sockaddr Info CPF item (See CIP Volume 2, clause
    2-6.3.3, Table 2-6.9)."""

    TYPE_ID = CPFItemType.SOCKADDR_INFO_TO


@cpf_item
@struct(order=LittleEndian)
class ListServicesResponseItem(StructDefMixin):
    """ListServices reply CPF item (See CIP Volume 2, clause 2-4.6, Table
    2-4.11)."""

    TYPE_ID = CPFItemType.LIST_SERVICES

    protocol_version: uint16_t = 1
    """Version number of the CIP encapsulation service that the responding
    target implements."""

    capability_flags: uint16_t = 0
    """Bit flags describing which optional capabilities the target's service
    supports."""

    service_name: f[str, _FixedServiceName()] = ""
    """Human-readable service name; encoded as up to 16 bytes of ASCII,
    right-padded with NUL bytes."""


@cpf_item
@struct(order=LittleEndian)
class ListInterfacesResponseItem(StructDefMixin):
    """Placeholder ListInterfaces reply item.

    CIP Volume 2, clause 2-4.3 defines the command but no standard item
    body, so this only carries the protocol-version/capability-flags
    prefix any future item would share.
    """

    TYPE_ID = 0x0101

    protocol_version: uint16_t = 1
    """Version of the interface information the target claims to support."""

    capability_flags: uint16_t = 0
    """Bit flags describing the target's interface-related capabilities."""


@cpf_item
@struct(order=LittleEndian)
class ListIdentityResponseItem(StructDefMixin):
    """ListIdentity reply CPF item (See CIP Volume 2, clause 2-4.2.3, Table
    2-4.4)."""

    TYPE_ID = CPFItemType.LIST_IDENTITY

    protocol_version: uint16_t = 1
    """Encapsulation protocol version implemented by the responding device."""

    socket_address: SockaddrInfo = field(default_factory=SockaddrInfo)
    """Address and port where the target can be reached, embedded as a
    SockaddrInfo structure."""

    vendor_id: uint16_t = 0
    """Numeric identifier of the device's manufacturer."""

    device_type: uint16_t = 0
    """Code classifying the general product category this device belongs to."""

    product_code: uint16_t = 0
    """Code that distinguishes this specific product within its device type."""

    revision_major: uint8_t = 0
    """Major segment of the device's two-part revision number."""

    revision_minor: uint8_t = 0
    """Minor segment of the device's two-part revision number."""

    status: uint16_t = 0
    """Device status value captured at the moment it answered."""

    serial_number: uint32_t = 0
    """Serial number reported by the responding device."""

    product_name: f[str, Prefixed(uint8, encoding="ascii")] = ""
    """Human-readable description of the device, encoded as a length-prefixed
    ASCII string."""

    state: uint8_t = 0
    """Current operating state reported by the device."""


def _cpf_item_from_type(value: int, context: _ContextLike) -> Any:
    item_ty = _cpf_item_type(value)
    return item_ty or Bytes(...)


_CPFItemValueT = (
    bytes
    | UnconnectedDataItem
    | ConnectedAddressItem
    | ConnectedDataItem
    | SequencedAddressItem
    | SockaddrInfoItem
    | SockaddrInfoOTItem
    | SockaddrInfoTOItem
    | ListServicesResponseItem
    | ListInterfacesResponseItem
    | ListIdentityResponseItem
    | NullAddressItem
)


@struct(order=LittleEndian)
class CPFItem(StructDefMixin):
    """Fallback CPF item for a type ID with no struct registered via
    :func:`cpf_item`."""

    type_id: uint16_t = 0
    """Numeric code identifying which CPF item type this is; left undecoded
    since no struct is registered for it."""

    value: f[
        _CPFItemValueT, Prefixed(uint16, F(this.type_id) >> _cpf_item_from_type)
    ] = b""
    """decoded item body."""

    @classmethod
    def new(
        cls: type[Self],
        value: _CPFItemValueT,
        type_id: int | CPFItemType | None = None,
    ) -> Self:
        """Builds a :class:`CPFItem`, deriving ``type_id`` from ``value``'s
        ``TYPE_ID`` when not given explicitly."""

        if type_id is None:
            if isinstance(value, bytes):
                raise ValueError("TypeId required when passing raw bytes")

            type_id = value.TYPE_ID
        return cls(type_id=type_id, value=value)


@struct(order=LittleEndian, kw_only=True)
class CPF(StructDefMixin):
    """Common Packet Format envelope: an item count followed by that many typed
    items (See CIP Volume 2, clause 2-6.1, Table 2-6.1)."""

    count: f[int, AsLengthRef("count", "items", uint16)] = 0
    """Number of items encoded in :attr:`items`; kept in sync automatically
    when constructed from items directly."""

    items: f[list[CPFItem], CPFItem[this.count]]
    """Item list, each entry wrapping a ``type_id``/decoded-value pair. Use
    :meth:`new`/:attr:`values` to work with bare item values instead."""

    @property
    def values(self) -> list[_CPFItemValueT]:
        """:attr:`items`, unwrapped to their bare decoded values."""

        return [item.value for item in self.items]

    @classmethod
    def new(cls: type[Self], *values: _CPFItemValueT) -> Self:
        """Builds a :class:`CPF` from bare item values, wrapping each one in
        a :class:`CPFItem` with its ``type_id`` derived automatically."""

        return cls(items=[CPFItem.new(value) for value in values])


__all__ = [
    "CPF",
    "CPFItem",
    "CPFItemType",
    "ConnectedAddressItem",
    "ConnectedDataItem",
    "ListIdentityResponseItem",
    "ListInterfacesResponseItem",
    "ListServicesResponseItem",
    "NullAddressItem",
    "SequencedAddressItem",
    "SockaddrInfo",
    "SockaddrInfoItem",
    "SockaddrInfoOTItem",
    "SockaddrInfoTOItem",
    "UnconnectedDataItem",
    "cpf_item",
    "register_cpf_item",
]
