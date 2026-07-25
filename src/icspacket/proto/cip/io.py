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
"""EtherNet/IP Class 0/1 cyclic I/O connections (UDP transport).

A Class 0/1 connection carries the raw I/O data negotiated by a prior
Forward_Open/Large_Forward_Open exchange (see
:mod:`icspacket.proto.cip.connmgr`); this module does not perform any Connection
Manager services itself, it only transports the cyclic data once a connection
has been opened.
"""

import socket
from typing import ClassVar

from caterpillar.exception import StructException
from caterpillar.fields import uint16, uint32
from caterpillar.shortcuts import LittleEndian
from typing_extensions import Self

from .connmgr import ForwardOpenResponse
from .cpf import (
    CPF,
    ConnectedAddressItem,
    ConnectedDataItem,
    SequencedAddressItem,
)


class CIPIOError(ConnectionError):
    """Raised for malformed or failed Class 0/1 I/O exchanges."""


class CIPIO_Connection:
    """UDP transport for a Class 0/1 (cyclic) CIP I/O connection."""

    DEFAULT_PORT: ClassVar[int] = 2222

    #: Value this class writes into the Run/Idle header to mark the O->T
    #: payload as live data the target should act on (the "Run" state).
    RUN: ClassVar[int] = 1
    #: Value this class writes into the Run/Idle header to tell the target
    #: to disregard the accompanying O->T payload (the "Idle" state).
    IDLE: ClassVar[int] = 0

    def __init__(
        self,
        timeout: float = 1.0,
        *,
        header_format: bool = True,
        sequence_format: bool = True,
        bind_address: str | None = None
    ) -> None:
        self.timeout: float = timeout
        #: Whether O->T datagrams carry a 4-byte Run/Idle header (See CIP
        #: Volume 1, clause 3-6.1.4 "32-Bit Header Format"), as used by
        #: exclusive-owner/input-output connections. Disable for
        #: connections that use the plain "Modeless" O->T format.
        self.header_format: bool = header_format
        #: Whether O->T datagrams carry a 16-bit connected sequence count
        #: prefix identifying a class 1 real-time format (See CIP Volume 1,
        #: clause 3-6.1). Some targets omit this prefix and rely solely on
        #: the CPF-level sequence number instead; disable for those
        #: connections.
        self.sequence_format: bool = sequence_format
        self.sock: socket.socket | None = None
        self.address: tuple[str, int] | None = None
        self.bind_address: str = bind_address or "0.0.0.0"
        self.o_to_t_connection_id: int = 0
        self.t_to_o_connection_id: int = 0
        self._send_sequence: int = 0
        self._recv_sequence: int = 0
        self._connected_sequence: int = 0

    @classmethod
    def from_forward_open(
        cls,
        response: ForwardOpenResponse,
        address: tuple[str, int],
        *,
        timeout: float = 1.0,
        header_format: bool = True,
        sequence_format: bool = True,
    ) -> "CIPIO_Connection":
        """Open a Class 0/1 connection using connection IDs from a Forward_Open
        response."""

        io_conn = cls(
            timeout=timeout,
            header_format=header_format,
            sequence_format=sequence_format,
        )
        io_conn.open(response, address)
        return io_conn

    def open(self, response: ForwardOpenResponse, address: tuple[str, int]) -> None:
        """Open the UDP socket using connection IDs from ``response``."""

        if self.sock is not None:
            raise CIPIOError("I/O connection is already open")
        self.o_to_t_connection_id = int(response.o_to_t_connection_id)
        self.t_to_o_connection_id = int(response.t_to_o_connection_id)
        self._send_sequence = 0
        self._recv_sequence = 0
        self._connected_sequence = 0
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Targets reply to the well-known CIP I/O port itself rather than to
        # the source port of the received datagram, so the local socket must
        # be bound to that same fixed port to observe the reply.
        self.sock.bind((self.bind_address, self.DEFAULT_PORT))
        self.sock.settimeout(self.timeout)

    def close(self) -> None:
        """Close the UDP socket and clear negotiated connection IDs."""

        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None
        self.o_to_t_connection_id = 0
        self.t_to_o_connection_id = 0

    def _assert_open(self) -> None:
        if self.sock is None or self.address is None:
            raise CIPIOError("I/O connection is not open")

    def send(self, data: bytes, *, run_idle: int | None = None) -> None:
        """Send one cyclic O->T datagram carrying ``data`` as the assembly
        payload.

        ``run_idle`` overrides :attr:`header_format`'s default ``RUN`` value
        for this datagram only; pass it explicitly to send an ``IDLE``
        datagram. Ignored entirely when :attr:`header_format` is ``False``.
        """

        self._assert_open()
        assert self.sock is not None and self.address is not None
        sequence_prefix = b""
        if self.sequence_format:
            sequence_prefix = bytes(
                uint16.to_bytes(self._connected_sequence, order=LittleEndian)
            )
            self._connected_sequence = (self._connected_sequence + 1) & 0xFFFF
        header = b""
        if self.header_format:
            header = bytes(
                uint32.to_bytes(self.RUN if run_idle is None else run_idle, order=LittleEndian)
            )
        connected_data = sequence_prefix + header + bytes(data)
        cpf = CPF.new(
            SequencedAddressItem(self.o_to_t_connection_id, self._send_sequence),
            ConnectedDataItem(connected_data),
        )
        self._send_sequence = (self._send_sequence + 1) & 0xFFFFFFFF
        try:
            _ = self.sock.sendto(cpf.to_bytes(), self.address)
        except OSError as exc:
            raise CIPIOError("failed to send Class 0/1 I/O datagram") from exc

    def recv(self) -> bytes:
        """Receive one cyclic T->O datagram and return its raw assembly data."""

        self._assert_open()
        assert self.sock is not None
        try:
            raw, _ = self.sock.recvfrom(65535)
        except OSError as exc:
            raise CIPIOError("failed to receive Class 0/1 I/O datagram") from exc
        return self._decode(raw)

    def _decode(self, raw: bytes) -> bytes:
        try:
            cpf = CPF.from_bytes(raw)
        except StructException as exc:
            raise CIPIOError("malformed Class 0/1 I/O datagram") from exc
        address_item = next(
            (
                item
                for item in cpf.values
                if isinstance(item, (SequencedAddressItem, ConnectedAddressItem))
            ),
            None,
        )
        data_item = next(
            (item for item in cpf.values if isinstance(item, ConnectedDataItem)), None
        )
        if address_item is None or data_item is None:
            raise CIPIOError("Class 0/1 I/O datagram is missing an address or data item")
        if address_item.connection_id != self.t_to_o_connection_id:
            raise CIPIOError("Class 0/1 I/O datagram has an unexpected connection ID")
        data = bytes(data_item.data)
        if isinstance(address_item, SequencedAddressItem):
            self._recv_sequence = address_item.sequence_number
        if self.sequence_format:
            if len(data) < 2:
                raise CIPIOError("Class 0/1 I/O datagram data is missing its sequence count")
            data = data[2:]
        return data

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


__all__ = ["CIPIOError", "CIPIO_Connection"]
