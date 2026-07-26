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
"""[ODVA CIP Vol 2] EtherNet/IP encapsulation protocol codecs."""

import enum
from dataclasses import field

from caterpillar.py import (
    AsLengthRef,
    Bytes,
    Enum,
    StructDefMixin,
    this,
    uint16,
)
from caterpillar.shortcuts import LittleEndian, f, struct
from caterpillar.types import uint16_t, uint32_t

from .cpf import CPF


class EncapsulationCommand(enum.IntEnum):
    """EtherNet/IP encapsulation commands (See CIP Vol 2, clause 2-3.2, Table
    2-3.2)."""

    NOP = 0x0000
    LIST_SERVICES = 0x0004
    LIST_IDENTITY = 0x0063
    LIST_INTERFACES = 0x0064
    REGISTER_SESSION = 0x0065
    UNREGISTER_SESSION = 0x0066
    SEND_RR_DATA = 0x006F
    SEND_UNIT_DATA = 0x0070


class EncapsulationStatus(enum.IntEnum):
    """Common encapsulation status values (See CIP Vol 2, clause 2-3.5, Table
    2-3.3)."""

    SUCCESS = 0
    INVALID_COMMAND = 1
    INSUFFICIENT_MEMORY = 2
    INCORRECT_DATA = 3
    INVALID_SESSION_HANDLE = 100
    INVALID_LENGTH = 101
    UNSUPPORTED_PROTOCOL_VERSION = 105


@struct
class NOPPayload(StructDefMixin):
    """NOP command-specific payload (See CIP Vol 2, clause 2-4.1, Table 2-4.1).

    The command carries no required semantics, so this simply stores
    whatever raw bytes accompany it.
    """

    data: f[bytes, Bytes(...)] = b""


@struct
class ListServicesPayload(StructDefMixin):
    """ListServices request/response payload (See CIP Vol 2, clause 2-4.6,
    Tables 2-4.10 and 2-4.11)."""

    cpf: CPF = field(default_factory=CPF.new)


@struct
class ListIdentityPayload(StructDefMixin):
    """ListIdentity request/response payload (See CIP Vol 2, clause 2-4.2,
    Tables 2-4.2 and 2-4.3)."""

    cpf: CPF = field(default_factory=CPF.new)


@struct
class ListInterfacesPayload(StructDefMixin):
    """ListInterfaces request/response payload (See CIP Vol 2, clause 2-4.3,
    Tables 2-4.5 and 2-4.6)."""

    cpf: CPF = field(default_factory=CPF.new)


@struct(order=LittleEndian)
class RegisterSessionPayload(StructDefMixin):
    """RegisterSession payload (See CIP Vol 2, clause 2-4.4, Tables 2-4.7 and
    2-4.8)."""

    protocol_version: uint16_t = 1
    """Encapsulation protocol version the client is requesting to use for this
    session."""

    options: uint16_t = 0
    """Placeholder for future session option flags; none exist yet, so this is
    always sent as zero."""


@struct
class UnRegisterSessionPayload(StructDefMixin):
    """UnRegisterSession has no command-specific data (See CIP Vol 2, clause
    2-4.5, Table 2-4.9)."""


@struct(order=LittleEndian)
class _SendData(StructDefMixin):
    """Common SendRRData / SendUnitData payload prefix (See CIP Vol 2, clause
    2-4.7/2-4.8)."""

    interface_handle: uint32_t = 0
    """Selects which communications interface the message applies to; always 0
    here since encapsulated CIP traffic uses the default interface."""

    timeout: uint16_t = 0
    """How long to wait for a reply, in seconds, up to 65535; a value of 0
    defers to whatever timeout the encapsulated protocol defines on its own."""

    cpf: CPF = field(default_factory=CPF.new)


@struct
class SendRRDataPayload(_SendData):
    """SendRRData payload (See CIP Vol 2, clause 2-4.7, Tables 2-4.13 and
    2-4.14)."""


@struct
class SendUnitDataPayload(_SendData):
    """SendUnitData payload (See CIP Vol 2, clause 2-4.8, Table 2-4.15)."""


#: Registry of command-specific payload structs by encapsulation command.
_PAYLOAD_TYPES: dict[int, type[StructDefMixin]] = {
    EncapsulationCommand.NOP: NOPPayload,
    EncapsulationCommand.LIST_SERVICES: ListServicesPayload,
    EncapsulationCommand.LIST_IDENTITY: ListIdentityPayload,
    EncapsulationCommand.LIST_INTERFACES: ListInterfacesPayload,
    EncapsulationCommand.REGISTER_SESSION: RegisterSessionPayload,
    EncapsulationCommand.UNREGISTER_SESSION: UnRegisterSessionPayload,
    EncapsulationCommand.SEND_RR_DATA: SendRRDataPayload,
    EncapsulationCommand.SEND_UNIT_DATA: SendUnitDataPayload,
}

_PayloadT = (
    NOPPayload
    | ListServicesPayload
    | ListIdentityPayload
    | ListInterfacesPayload
    | RegisterSessionPayload
    | UnRegisterSessionPayload
    | SendRRDataPayload
    | SendUnitDataPayload
)


@struct(order=LittleEndian, kw_only=True)
class EncapsulationPacket(StructDefMixin):
    """Wraps a full EtherNet/IP message as sent on the wire: a constant 24-byte
    header followed by the raw command-specific payload bytes (See CIP Vol 2,
    clause 2-3.1, Table 2-3.1)."""

    command: f[EncapsulationCommand | int, Enum(EncapsulationCommand, uint16)] = 0
    """Which encapsulation command this message carries, determining how the
    payload bytes should be interpreted."""

    length: f[int, AsLengthRef("length", "payload_raw", uint16)] = 0
    """Byte count of the command-specific payload that follows this header, used
    to know how many trailing bytes belong to the message."""

    session_handle: uint32_t = 0
    """Opaque session token whose meaning is left to the communicating endpoints
    rather than fixed by this header."""

    status: uint32_t = 0
    """Outcome of the command, expressed as one of the EncapsulationStatus
    values (zero on success)."""

    sender_context: f[bytes, Bytes(8)] = b"\0" * 8
    """Free-form 8-byte value whose meaning is defined solely by whichever
    endpoint originated the message; other implementations do not need to
    interpret it."""

    options: uint32_t = 0
    """General-purpose flag bits belonging to the encapsulation header."""

    payload_raw: f[bytes, Bytes(this.length)] = b""
    """Undecoded command-specific bytes; use :attr:`payload` to interpret them
    based on :attr:`command`. A :class:`StructDefMixin` instance is also
    accepted and encoded automatically."""

    def __post_init__(self) -> None:
        """Encode a struct instance passed directly as ``payload_raw``."""

        if isinstance(self.payload_raw, StructDefMixin):
            self.payload_raw = self.payload_raw.to_bytes()

    @property
    def payload(self) -> _PayloadT | bytes:
        """Command-specific payload, decoded according to :attr:`command`.

        Falls back to the raw, undecoded bytes for a command with no known
        payload type.
        """

        payload_ty = _PAYLOAD_TYPES.get(self.command)
        return (  # pyright: ignore[reportReturnType]
            self.payload_raw
            if payload_ty is None
            else payload_ty.from_bytes(self.payload_raw)
        )

    @payload.setter
    def payload(self, value: _PayloadT) -> None:
        self.payload_raw = value.to_bytes()


__all__ = [
    "EncapsulationCommand",
    "EncapsulationPacket",
    "EncapsulationStatus",
    "ListIdentityPayload",
    "ListInterfacesPayload",
    "ListServicesPayload",
    "NOPPayload",
    "RegisterSessionPayload",
    "SendRRDataPayload",
    "SendUnitDataPayload",
    "UnRegisterSessionPayload",
]
