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
"""EtherNet/IP explicit-message connection support."""

import socket
from collections.abc import Callable, Iterable
from typing import Any, ClassVar

from caterpillar.exception import StructException
from caterpillar.fields import uint16
from caterpillar.shortcuts import LittleEndian
from typing_extensions import override

from icspacket.core.connection import (
    ConnectionClosedError,
    ConnectionError,
    ConnectionNotEstablished,
    ConnectionStateError,
    connection,
)

from .connmgr import (
    ForwardCloseRequest,
    ForwardCloseResponse,
    ForwardOpenRequest,
    ForwardOpenResponse,
    LargeForwardOpenRequest,
    UnconnectedSendRequest,
)
from .const import CIPStatusError, ClassCode, CommonService
from .cpf import (
    CPF,
    ConnectedAddressItem,
    ConnectedDataItem,
    ListIdentityResponseItem,
    ListInterfacesResponseItem,
    ListServicesResponseItem,
    NullAddressItem,
    UnconnectedDataItem,
)
from .encap import (
    EncapsulationCommand,
    EncapsulationPacket,
    EncapsulationStatus,
    ListIdentityPayload,
    ListInterfacesPayload,
    ListServicesPayload,
    RegisterSessionPayload,
    SendRRDataPayload,
    SendUnitDataPayload,
    UnRegisterSessionPayload,
)
from .epath import EPATH, LogicalSegment
from .io import CIPIO_Connection
from .msgrouter import MessageRouterPath, MessageRouterRequest, MessageRouterResponse


class CIPProtocolError(ConnectionError):
    """Raised for malformed or failed EtherNet/IP/CIP exchanges."""


class CIP_Connection(connection):
    """Synchronous EtherNet/IP TCP connection for explicit CIP messaging."""

    DEFAULT_PORT: ClassVar[int] = 44818

    def __init__(
        self,
        timeout: float = 10.0,
        *,
        sock: socket.socket | None = None,
        sock_cls: Callable[..., socket.socket] | None = None,
        auto_register: bool = True,
    ) -> None:
        super().__init__()
        self.timeout: float = timeout
        self._sock: socket.socket | None = sock
        self._sock_cls: Callable[..., socket.socket] | None = sock_cls
        self.auto_register: bool = auto_register
        self.session_handle: int = 0
        self.address: tuple[str, int] | None = None
        self.connection_id: int = 0
        self.originator_connection_id: int = 0
        self._connected_sequence: int = 0
        self._forward_open_request: (
            ForwardOpenRequest | LargeForwardOpenRequest | None
        ) = None
        self._io_connection: CIPIO_Connection | None = None
        if self._sock is not None:
            self._sock.settimeout(timeout)

    @property
    def sock(self) -> socket.socket:
        """Underlying TCP socket, or ``ConnectionNotEstablished`` if closed."""

        if self._sock is None:
            raise ConnectionNotEstablished
        return self._sock

    @property
    def session(self) -> int:
        """Current EtherNet/IP session handle."""

        return self.session_handle

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """Connect to an EtherNet/IP target and register a session, unless
        :attr:`auto_register` is disabled.

        :param address: ``(host, port)`` of the EtherNet/IP target.
        :type address: tuple[str, int]
        :raises ConnectionError: If the raw TCP connection fails.
        :raises CIPProtocolError: If session registration (See CIP Vol 2,
            clause 2-4.4) fails.
        """

        if self.is_connected():
            return
        host, port = address
        if self._sock is None:
            factory = self._sock_cls or socket.socket
            self._sock = factory(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(self.timeout)
        try:
            self._sock.connect((host, port))
        except OSError as exc:
            self._close_socket()
            raise ConnectionError(
                f"failed to connect to EtherNet/IP server at {host}:{port}"
            ) from exc

        self.address = (host, port)
        self._connected: bool = True
        self._valid: bool = not self.auto_register
        if self.auto_register:
            try:
                _ = self.register_session()
            except ConnectionError:
                self._close_socket()
                raise

    @override
    def close(self) -> None:
        """Close the EtherNet/IP session and underlying TCP socket,
        best-effort.

        Sends UnRegisterSession (See CIP Vol 2, clause 2-4.5) if a session is
        registered; failures are ignored since the socket is closed
        regardless.
        """

        if self._connected and self.session_handle:
            try:
                self.unregister_session()
            except (OSError, ConnectionError):
                pass
        self._close_socket()

    def _close_socket(self) -> None:
        """Close the raw socket, the I/O connection, and reset all
        per-connection state."""

        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None
        self.session_handle = 0
        self.connection_id = 0
        self.originator_connection_id = 0
        self._connected_sequence = 0
        self._forward_open_request = None
        self._connected = False
        self._valid = False
        self.close_io_connection()

    def _recv_exact(self, length: int) -> bytes:
        """Read exactly ``length`` bytes, looping over partial ``recv()``
        calls."""

        self._assert_connected()
        result = bytearray()
        while len(result) < length:
            try:
                chunk = self.sock.recv(length - len(result))
            except OSError as exc:
                raise ConnectionError("EtherNet/IP receive failed") from exc
            if not chunk:
                raise ConnectionClosedError("peer closed the EtherNet/IP socket")
            result.extend(chunk)
        return bytes(result)

    def _send_all(self, data: bytes) -> None:
        """Send every byte of ``data``, translating socket failures."""

        self._assert_connected()
        try:
            self.sock.sendall(bytes(data))
        except OSError as exc:
            raise ConnectionError("EtherNet/IP send failed") from exc

    def _recv_packet(
        self, expected: EncapsulationCommand | None = None
    ) -> EncapsulationPacket:
        """Read one encapsulation packet and validate its command and
        status."""

        header = self._recv_exact(24)
        length = uint16.from_bytes(header[2:4], order=LittleEndian)
        payload = self._recv_exact(length)
        try:
            response = EncapsulationPacket.from_bytes(header + payload)
        except (ValueError, StructException) as exc:
            raise CIPProtocolError(
                "malformed EtherNet/IP encapsulation response"
            ) from exc
        if expected is not None and response.command != expected:
            raise CIPProtocolError(
                f"expected {expected.name} response, got {response.command!r}"
            )
        if response.status != int(EncapsulationStatus.SUCCESS):
            raise CIPProtocolError(
                f"EtherNet/IP encapsulation request failed with status 0x{response.status:08x}"
            )
        return response

    def _exchange(
        self, packet: EncapsulationPacket, expected: EncapsulationCommand | None = None
    ) -> EncapsulationPacket:
        """Send ``packet`` and return the next matching encapsulation
        reply."""

        self._send_all(packet.to_bytes())
        return self._recv_packet(expected)

    def register_session(self) -> int:
        """Register an EtherNet/IP TCP session and return the target handle
        (See CIP Vol 2, clause 2-4.4)."""

        self._assert_connected()
        packet = EncapsulationPacket(
            command=EncapsulationCommand.REGISTER_SESSION,
            payload_raw=RegisterSessionPayload(),  # pyright: ignore[reportArgumentType]
            session_handle=0,
        )
        response = self._exchange(packet, EncapsulationCommand.REGISTER_SESSION)
        if response.session_handle == 0:
            raise CIPProtocolError(
                "Register Session response returned a zero session handle"
            )
        self.session_handle = response.session_handle
        self._valid = True
        return self.session_handle

    def unregister_session(self) -> None:
        """Send UnRegisterSession (See CIP Vol 2, clause 2-4.5 -
        UnRegisterSession).

        The target treats receipt of this command as its cue to close the
        TCP connection and never answers it, so this method just fires the
        request and returns without waiting for (or expecting) a reply.
        """
        self._assert_connected()
        if not self.session_handle:
            return
        packet = EncapsulationPacket(
            command=EncapsulationCommand.UNREGISTER_SESSION,
            payload_raw=UnRegisterSessionPayload(),  # pyright: ignore[reportArgumentType]
            session_handle=self.session_handle,
        )
        self._send_all(packet.to_bytes())
        self.session_handle = 0
        self._valid = False

    @override
    def send_data(self, octets: bytes, /) -> None:
        """Send raw bytes directly on the underlying TCP socket.

        Prefer :meth:`send_rr_data`/:meth:`send_unit_data` for framed CIP
        requests; this is the low-level primitive the base :class:`connection`
        contract requires.

        :param octets: Raw bytes to send.
        :type octets: bytes
        :raises ConnectionNotEstablished: If no connection is established.
        :raises ConnectionClosedError: If the socket send fails.
        """

        self._send_all(bytes(octets))

    @override
    def recv_data(self) -> bytes:
        """Receive one raw EtherNet/IP encapsulation packet.

        :return: The header and payload bytes of one encapsulation packet.
        :rtype: bytes
        :raises ConnectionNotEstablished: If no connection is established.
        :raises ConnectionClosedError: If the peer closes the socket first.
        """

        header = self._recv_exact(24)
        length = uint16.from_bytes(header[2:4], order=LittleEndian)
        return header + self._recv_exact(length)

    def _send_cpf(
        self,
        command: EncapsulationCommand,
        payload_type: type[SendRRDataPayload] | type[SendUnitDataPayload],
        data: bytes,
    ) -> bytes:
        """Send unconnected data via SendRRData/SendUnitData and return the
        peer's reply data."""

        self._assert_connected()
        if self.auto_register and not self.session_handle:
            raise ConnectionNotEstablished("EtherNet/IP session is not registered")
        cpf = CPF.new(NullAddressItem(), UnconnectedDataItem(bytes(data)))
        payload = payload_type(interface_handle=0, timeout=10, cpf=cpf)
        packet = EncapsulationPacket(
            command=command,
            payload_raw=payload,  # pyright: ignore[reportArgumentType]
            session_handle=self.session_handle,
        )
        response = self._exchange(packet, command)
        for item in response.payload.cpf.values:
            if isinstance(item, UnconnectedDataItem):
                return item.data
        raise CIPProtocolError(
            "Send Data response did not contain an unconnected data item"
        )

    def _send_connected_cpf(
        self,
        data: bytes,
        *,
        connection_id: int | None = None,
        sequence: int | None = None,
    ) -> bytes:
        """Send Class-3 connected data via SendUnitData and return the
        peer's reply data, stripped of its leading sequence count."""

        self._assert_connected()
        if self.auto_register and not self.session_handle:
            raise ConnectionNotEstablished("EtherNet/IP session is not registered")
        target_id = self.connection_id if connection_id is None else int(connection_id)
        if target_id <= 0:
            raise ConnectionStateError(
                "no connected connection_id available; call forward_open() first"
            )
        if sequence is None:
            sequence = self._connected_sequence
            self._connected_sequence = (self._connected_sequence + 1) & 0xFFFF
        connected_data = bytes(uint16.to_bytes(int(sequence), order=LittleEndian))
        connected_data += bytes(data)
        cpf = CPF.new(
            ConnectedAddressItem(target_id),
            ConnectedDataItem(connected_data),
        )
        payload = SendUnitDataPayload(interface_handle=0, timeout=0, cpf=cpf)
        packet = EncapsulationPacket(
            command=EncapsulationCommand.SEND_UNIT_DATA,
            payload_raw=payload,
            session_handle=self.session_handle,
        )
        self._send_all(packet.to_bytes())
        response = self._recv_packet(EncapsulationCommand.SEND_UNIT_DATA)
        for item in response.payload.cpf.values:
            if isinstance(item, ConnectedDataItem):
                if len(item.data) < 2:
                    raise CIPProtocolError("connected data is missing its sequence")
                return item.data[2:]
        raise CIPProtocolError(
            "SendUnitData peer packet did not contain connected data"
        )

    def send_rr_data(self, data: bytes | MessageRouterRequest) -> bytes:
        """Send a UCMM request/reply packet via SendRRData."""

        raw = data.to_bytes() if isinstance(data, MessageRouterRequest) else bytes(data)
        return self._send_cpf(EncapsulationCommand.SEND_RR_DATA, SendRRDataPayload, raw)

    def send_unit_data(
        self,
        data: bytes | MessageRouterRequest,
        *,
        connected: bool = False,
        connection_id: int | None = None,
        sequence: int | None = None,
    ) -> bytes:
        """Send connected data via SendUnitData and read the next peer packet.

        SendUnitData is not a UCMM request/reply command; use
        :meth:`send_rr_data` for unconnected Message Router traffic.
        """

        raw = data.to_bytes() if isinstance(data, MessageRouterRequest) else bytes(data)
        if not connected and connection_id is None:
            raise ValueError(
                "SendUnitData carries connected data; use send_rr_data for UCMM traffic"
            )
        return self._send_connected_cpf(
            raw,
            connection_id=connection_id,
            sequence=sequence,
        )

    def send_connected_unit_data(
        self,
        data: bytes | MessageRouterRequest,
        *,
        connection_id: int | None = None,
        sequence: int | None = None,
    ) -> bytes:
        """Send Class-3 connected explicit data over SendUnitData."""

        raw = data.to_bytes() if isinstance(data, MessageRouterRequest) else bytes(data)
        return self._send_connected_cpf(
            raw, connection_id=connection_id, sequence=sequence
        )

    def _discovery(
        self, command: EncapsulationCommand, payload: object
    ) -> tuple[object, ...]:
        """Send a UCMM discovery command and return its raw CPF item list."""

        self._assert_connected()
        response = self._exchange(
            EncapsulationPacket(command=command, payload_raw=payload, session_handle=0),
            command,
        )
        return tuple(response.payload.cpf.values)

    def list_identity(self) -> list[ListIdentityResponseItem]:
        """Return decoded ListIdentity response items (See CIP Vol 2, clause
        2-4.2)."""

        return [
            item
            for item in self._discovery(
                EncapsulationCommand.LIST_IDENTITY, ListIdentityPayload()
            )
            if isinstance(item, ListIdentityResponseItem)
        ]

    def list_services(self) -> list[ListServicesResponseItem]:
        """Return decoded ListServices response items (See CIP Vol 2, clause
        2-4.6)."""

        return [
            item
            for item in self._discovery(
                EncapsulationCommand.LIST_SERVICES, ListServicesPayload()
            )
            if isinstance(item, ListServicesResponseItem)
        ]

    def list_interfaces(self) -> list[ListInterfacesResponseItem]:
        """Return known ListInterfaces response items (See CIP Vol 2, clause
        2-4.3); Vol 2 defines none publicly."""

        return [
            item
            for item in self._discovery(
                EncapsulationCommand.LIST_INTERFACES, ListInterfacesPayload()
            )
            if isinstance(item, ListInterfacesResponseItem)
        ]

    def _check_status(self, response: MessageRouterResponse) -> None:
        """Raise :class:`CIPStatusError` when `response` reports failure."""

        if not response.is_success:
            raise CIPStatusError(
                response.general_status,
                response.additional_status,
                service=response.service,
            )

    def generic_message(
        self,
        service: int | CommonService,
        path: MessageRouterPath,
        request_data: bytes = b"",
        *,
        connected: bool = False,
        return_response: bool = False,
    ) -> bytes | MessageRouterResponse:
        """Send one Message Router request (See CIP Vol 1, clause A-3) and
        return its response data."""

        request = MessageRouterRequest.new(int(service), path, request_data)
        raw = (
            self.send_connected_unit_data(request)
            if connected
            else self.send_rr_data(request)
        )
        response = MessageRouterResponse.from_bytes(raw)
        self._check_status(response)
        return response if return_response else response.response_data

    def _connection_manager_exchange(
        self,
        service: int | CommonService,
        request_data: bytes,
    ) -> MessageRouterResponse:
        """Send a Connection Manager service request and return its
        response (See CIP Vol 1, clause 3-5.5)."""

        request = MessageRouterRequest.new(
            int(service),
            self.object_path(ClassCode.CONNECTION_MANAGER, 1),
            request_data,
        )
        raw = self.send_rr_data(request)
        response = MessageRouterResponse.from_bytes(raw)
        self._check_status(response)
        return response

    def forward_open(
        self,
        request: ForwardOpenRequest | LargeForwardOpenRequest | None = None,
        **kwargs: Any,
    ) -> ForwardOpenResponse:
        """Open a Class-3 or I/O connection through Connection Manager (See
        CIP Vol 1, clause 3-5.5.2)."""

        if request is None:
            request = ForwardOpenRequest.new(**kwargs)
        elif kwargs:
            raise TypeError(
                "specify a Forward_Open request or keyword fields, not both"
            )
        response = self._connection_manager_exchange(
            (
                CommonService.LARGE_FORWARD_OPEN
                if isinstance(request, LargeForwardOpenRequest)
                else CommonService.FORWARD_OPEN
            ),
            request.to_bytes(),
        )
        result = ForwardOpenResponse.from_bytes(response.response_data)
        self.connection_id = result.o_to_t_connection_id
        self.originator_connection_id = result.t_to_o_connection_id
        self._connected_sequence = 0
        self._forward_open_request = request
        return result

    def large_forward_open(
        self, request: LargeForwardOpenRequest | None = None, **kwargs: Any
    ) -> ForwardOpenResponse:
        """Open a connection using the Large_Forward_Open service."""

        if request is None:
            request = LargeForwardOpenRequest.new(**kwargs)
        elif kwargs:
            raise TypeError(
                "specify a Large_Forward_Open request or keyword fields, not both"
            )
        return self.forward_open(request)

    def forward_close(
        self,
        request: ForwardCloseRequest | None = None,
        **kwargs: Any,
    ) -> ForwardCloseResponse:
        """Close the current connection through Connection Manager (See CIP
        Vol 1, clause 3-5.5.3)."""

        if request is None:
            previous = self._forward_open_request
            if previous is not None:
                kwargs.setdefault("connection_path", previous.connection_path)
                kwargs.setdefault("priority", previous.priority)
                kwargs.setdefault("timeout_ticks", previous.timeout_ticks)
            request = ForwardCloseRequest.new(
                connection_serial_number=kwargs.pop(
                    "connection_serial_number",
                    previous.connection_serial_number if previous is not None else 0,
                ),
                originator_vendor_id=kwargs.pop(
                    "originator_vendor_id",
                    previous.originator_vendor_id if previous is not None else 0,
                ),
                originator_serial_number=kwargs.pop(
                    "originator_serial_number",
                    previous.originator_serial_number if previous is not None else 0,
                ),
                **kwargs,
            )
        elif kwargs:
            raise TypeError(
                "specify a Forward_Close request or keyword fields, not both"
            )

        response = self._connection_manager_exchange(
            CommonService.FORWARD_CLOSE, request.to_bytes()
        )
        result = ForwardCloseResponse.from_bytes(response.response_data)
        self.connection_id = 0
        self.originator_connection_id = 0
        self._connected_sequence = 0
        self._forward_open_request = None
        return result

    def open_io_connection(
        self,
        response: ForwardOpenResponse | None = None,
        *,
        address: tuple[str, int] | None = None,
        timeout: float = 1.0,
        header_format: bool = True,
        sequence_format: bool = True,
    ) -> CIPIO_Connection:
        """Open a Class 0/1 cyclic I/O (UDP) connection from a prior
        Forward_Open response.

        ``response`` defaults to the result of the most recent
        :meth:`forward_open`/:meth:`large_forward_open` call on this
        connection. ``address`` defaults to the host this connection is
        registered against, using :attr:`CIPIOConnection.DEFAULT_PORT`
        (UDP/2222) unless overridden. ``header_format`` controls whether
        O->T datagrams carry the 4-byte Run/Idle header (required by
        exclusive-owner style connections; see :mod:`icspacket.proto.cip.io`).
        ``sequence_format`` controls whether O->T datagrams carry a 16-bit
        connected sequence count prefix; disable for targets that rely
        solely on the CPF-level sequence number instead.
        """

        if self._io_connection is not None:
            raise ConnectionStateError("a Class 0/1 I/O connection is already open")
        if response is None:
            if not self.connection_id:
                raise ConnectionStateError(
                    "no Forward_Open response available; call forward_open() first"
                )
            response = ForwardOpenResponse(
                o_to_t_connection_id=self.connection_id,
                t_to_o_connection_id=self.originator_connection_id,
                connection_serial_number=0,
                originator_vendor_id=0,
                originator_serial_number=0,
                o_to_t_api=0,
                t_to_o_api=0,
            )
        if address is None:
            if self.address is None:
                raise ConnectionStateError(
                    "no target address available; specify address explicitly"
                )
            address = (self.address[0], CIPIO_Connection.DEFAULT_PORT)
        self._io_connection = CIPIO_Connection.from_forward_open(
            response,
            address,
            timeout=timeout,
            header_format=header_format,
            sequence_format=sequence_format,
        )
        return self._io_connection

    def send_io_data(self, data: bytes) -> None:
        """Send one cyclic O->T datagram over the open Class 0/1 connection."""

        if self._io_connection is None:
            raise ConnectionStateError("no Class 0/1 I/O connection is open")
        self._io_connection.send(data)

    def recv_io_data(self) -> bytes:
        """Receive one cyclic T->O datagram over the open Class 0/1
        connection."""

        if self._io_connection is None:
            raise ConnectionStateError("no Class 0/1 I/O connection is open")
        return self._io_connection.recv()

    def close_io_connection(self) -> None:
        """Close the Class 0/1 I/O connection opened by
        :meth:`open_io_connection`, if any."""

        if self._io_connection is not None:
            self._io_connection.close()
            self._io_connection = None

    def unconnected_send(
        self,
        message: MessageRouterRequest | bytes | None = None,
        route_path: EPATH | bytes | Iterable[Any] = EPATH(),
        *,
        priority: int = 0,
        timeout_ticks: int = 0,
        request: UnconnectedSendRequest | None = None,
    ) -> MessageRouterResponse:
        """Route a Message Router request through Connection Manager (See
        CIP Vol 1, clause 3-5.5.4)."""

        if request is not None:
            if message is not None:
                raise TypeError("specify request or message, not both")
            encoded = request.to_bytes()
        else:
            if message is None:
                raise TypeError("message is required")
            encoded_request = UnconnectedSendRequest.new(
                message, route_path, priority=priority, timeout_ticks=timeout_ticks
            )
            encoded = encoded_request.to_bytes()
        response = self._connection_manager_exchange(
            CommonService.UNCONNECTED_SEND, encoded
        )
        embedded = MessageRouterResponse.from_bytes(response.response_data)
        self._check_status(embedded)
        return embedded

    def object_path(
        self, class_code: int | ClassCode, instance: int, attribute: int | None = None
    ) -> EPATH:
        """Build the EPATH addressing a class/instance, optionally down to
        one attribute.

        :param class_code: The CIP object class code.
        :param instance: The target object instance.
        :param attribute: Narrows the path to one specific attribute, if given.
        """

        segments = [
            LogicalSegment.class_id(int(class_code)),
            LogicalSegment.instance_id(instance),
        ]
        if attribute is not None:
            segments.append(LogicalSegment.attribute_id(attribute))
        return EPATH(*segments)

    def get_attribute_single(
        self, class_code: int | ClassCode, instance: int, attribute: int
    ) -> bytes:
        """Read one attribute using Get_Attribute_Single (See CIP Vol 1,
        clause A-3)."""

        return self.generic_message(
            CommonService.GET_ATTRIBUTE_SINGLE,
            self.object_path(class_code, instance, attribute),
        )

    def set_attribute_single(
        self, class_code: int | ClassCode, instance: int, attribute: int, value: bytes
    ) -> bytes:
        """Write one attribute using Set_Attribute_Single (See CIP Vol 1,
        clause A-3)."""

        return self.generic_message(
            CommonService.SET_ATTRIBUTE_SINGLE,
            self.object_path(class_code, instance, attribute),
            value,
        )

    def get_attributes_all(self, class_code: int | ClassCode, instance: int) -> bytes:
        """Read all attributes from a class instance using
        Get_Attributes_All (See CIP Vol 1, clause A-3)."""

        return self.generic_message(
            CommonService.GET_ATTRIBUTES_ALL, self.object_path(class_code, instance)
        )


__all__ = ["CIPProtocolError", "CIP_Connection"]
