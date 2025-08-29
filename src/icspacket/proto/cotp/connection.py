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
import logging
import socket

from typing_extensions import override
from collections.abc import Iterable


from icspacket.core.connection import ConnectionClosedError, ConnectionError, connection
from icspacket.core.logger import TRACE
from icspacket.proto.cotp.structs import (
    TPDU,
    Parameter,
    Parameter_Code,
    TPDU_ConnectionConfirm,
    TPDU_ConnectionRequest,
    TPDU_Data,
    TPDU_DisconnectReason,
    TPDU_DisconnectRequest,
    TPDU_Error,
    TPDU_Size,
    parse_tpdu,
    TPDU_Class,
    _TPDULike,  # noqa
)
from icspacket.proto.tpkt import tpktsock

COTP_DEFAULT_SRC_REF = 0
"""Default source reference identifier for COTP connections."""

logger = logging.getLogger(__name__)


class COTP_Connection(connection):
    """
    Manages a COTP (Connection-Oriented Transport Protocol) connection over a TCP/IP socket.

    This class provides a high-level interface to establish, maintain, and terminate a
    COTP session on top of a stream-oriented transport such as TCP. It encapsulates the
    connection establishment (CR/CC exchange), error handling, data segmentation, and
    orderly connection release via DR TPDU messages.

    Example:

    >>> conn = COTP_Connection(sock_cls=tpktsock)
    >>> conn.connect(("127.0.0.1", 1234))
    >>> conn.send_data(b"Hello, world!")
    >>> data = conn.recv_data()
    >>> conn.close()

    :param src_ref: Source reference identifier (defaults to :data:`COTP_DEFAULT_SRC_REF`).
    :type src_ref: int | None
    :param sock: Existing socket instance to use for communication.
    :type sock: socket.socket | None
    :param sock_cls: Socket class to use if ``sock`` is not provided.
    :type sock_cls: type[socket.socket] | None
    :param protocol_class: The COTP protocol class to use (default: :class:`TPDU_Class.CLASS0`).
    :type protocol_class: TPDU_Class
    :param max_tpdu_size: Negotiated maximum TPDU size capability (default: :class:`TPDU_Size.SIZE_1024`).
    :type max_tpdu_size: TPDU_Size
    :param src_tsap: Calling transport selector as a hex string (default: "0000").
    :type src_tsap: str
    :param dst_tsap: Called transport selector as a hex string (default: "0000").
    :type dst_tsap: str
    :param parameters: Additional transport parameters to include in the CR TPDU.
    :type parameters: Iterable[Parameter] | None
    """

    def __init__(
        self,
        src_ref: int | None = None,
        sock: socket.socket | None = None,
        sock_cls: type[socket.socket] | None = None,
        protocol_class: TPDU_Class = TPDU_Class.CLASS0,
        max_tpdu_size: TPDU_Size = TPDU_Size.SIZE_1024,
        src_tsap: str = "0000",
        dst_tsap: str = "0000",
        parameters: Iterable[Parameter] | None = None,
        timeout: float | None = None,
    ) -> None:
        super().__init__()
        self.sock = sock
        if self.sock is None:
            if sock_cls is None:
                raise ValueError("Must specify either sock or sock_cls!")

            self.sock = sock_cls(socket.AF_INET, socket.SOCK_STREAM)

        # private members
        self.__src_ref = src_ref if src_ref is not None else COTP_DEFAULT_SRC_REF
        self.__dst_ref = 0
        self.__class = protocol_class
        self.__tpdu_size = max_tpdu_size

        # public (modifiable) members
        self.src_tsap = bytes.fromhex(src_tsap)
        self.dst_tsap = bytes.fromhex(dst_tsap)
        self.conn_params = list(parameters or [])

        if timeout:
            self.sock.settimeout(timeout)

    @property
    def protocol_class(self) -> TPDU_Class:
        """Configured transport protocol class."""
        return self.__class

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """
        Establish a COTP connection to a remote endpoint.

        :param address: Tuple specifying the (host, port) for the TCP connection.
        :type address: tuple[str, int]
        :raises ConnectionError: If the TCP connection fails or the CC TPDU is invalid.
        """
        cr_tpdu = TPDU_ConnectionRequest()
        cr_tpdu.src_ref = self.__src_ref
        cr_tpdu.dst_ref = 0
        cr_tpdu.parameters.extend(list(self.conn_params))
        cr_tpdu.parameters += [
            Parameter(Parameter_Code.TPDU_SIZE, self.__tpdu_size),
            Parameter(Parameter_Code.CALLING_T_SELECTOR, self.src_tsap),
            Parameter(Parameter_Code.CALLED_T_SELECTOR, self.dst_tsap),
        ]
        self.connect_raw(address, cr_tpdu)

    def connect_raw(
        self, address: tuple[str, int], tpdu_cr: TPDU_ConnectionRequest
    ) -> None:
        """
        Perform raw COTP connection establishment with a provided CR TPDU.

        :param address: (host, port) tuple for the remote TCP endpoint.
        :type address: tuple[str, int]
        :param tpdu_cr: Pre-constructed CR TPDU to send.
        :type tpdu_cr: TPDU_ConnectionRequest
        :raises ConnectionRefusedError: If a Disconnect Request TPDU is received.
        :raises ConnectionError: If an unexpected or invalid TPDU is received.
        """
        if self.is_connected() or self.is_valid():
            # already connected, ignore
            return

        try:
            self.sock.connect(address)
            self._connected = True
            logger.log(TRACE, "Connected to %s", address)
        except socket.error as e:
            raise ConnectionRefusedError from e

        self.send_tpdu(tpdu_cr)
        tpdu = self.receive_tpdu()
        self._propagate_errors(tpdu)
        if isinstance(tpdu, TPDU_DisconnectRequest):
            reason = tpdu.reason
            info = tpdu.user_data if tpdu.user_data else "<no-additional-info>"
            raise ConnectionRefusedError(
                f"Remote refused connection with reason {reason!r}: {info}"
            )

        if not isinstance(tpdu, TPDU_ConnectionConfirm):
            raise ConnectionError(
                f"Expected COTP Connection Response, got TPDU with code={tpdu.tpdu_code}"
            )

        if self.protocol_class == TPDU_Class.CLASS4:
            if not tpdu.is_valid():
                raise ConnectionError(
                    f"Received invalid COTP Connection Response (invalid checksum): {tpdu}"
                )

        self.__dst_ref = tpdu.src_ref
        self._valid = True

    @override
    def close(self) -> None:
        """
        Close the connection gracefully with a normal disconnect reason.
        """
        self.close_with_reason()

    def close_with_reason(
        self,
        reason: TPDU_DisconnectReason = TPDU_DisconnectReason.NORMAL,
    ) -> None:
        """
        Close the connection with an explicit disconnect reason.

        :param reason: Disconnect reason code (default: NORMAL).
        :type reason: TPDU_DisconnectReason
        """
        dr_tdpu = TPDU_DisconnectRequest()
        dr_tdpu.src_ref = self.__src_ref
        dr_tdpu.dst_ref = self.__dst_ref
        dr_tdpu.reason = reason
        self.close_raw(dr_tdpu)

    def close_raw(self, dr_tdpu: TPDU_DisconnectRequest) -> None:
        """
        Perform low-level connection close with a provided Disconnect Request TPDU.

        :param dr_tdpu: Pre-constructed DR TPDU to send.
        :type dr_tdpu: TPDU_DisconnectRequest
        """
        if not self.is_connected() or not self._valid:
            return

        self.send_tpdu(dr_tdpu)
        try:
            self.sock.close()
        except BrokenPipeError:
            pass
        self._connected = False
        self._valid = False

    def _propagate_errors(self, tpdu: TPDU) -> None:
        """
        Raise exceptions if a TPDU error message is received.


        :param tpdu: Received TPDU to check.
        :type tpdu: ~icspacket.proto.cotp.structs.TPDU
        :raises ConnectionError: If the TPDU is an Error TPDU.
        """
        if isinstance(tpdu, TPDU_Error):
            raise ConnectionError(f"Received COTP error: {tpdu.reject_cause}")

    def send_tpdu(self, tpdu: _TPDULike) -> None:
        """
        Serialize and send a TPDU over the transport connection.

        :param tpdu: TPDU instance to send.
        :type tpdu: ~icspacket.proto.cotp.structs.TPDU
        :raises ConnectionError: If the connection is not established.
        """
        if not self.is_connected():
            raise ConnectionError("Connection not established")

        tpdu_data = tpdu.build(add_checksum=self.protocol_class == TPDU_Class.CLASS4)
        logger.log(
            TRACE,
            "Sending (%s) TPDU in %d bytes (eot=%s)",
            tpdu.tpdu_code.name,
            len(tpdu_data),
            tpdu.nr.eot if isinstance(tpdu, TPDU_Data) else True,
        )
        try:
            self.sock.sendall(tpdu_data)
        except BrokenPipeError:
            raise ConnectionClosedError("Connection closed")

    def receive_tpdu(self):
        """
        Receive and parse a TPDU from the transport connection.

        :return: Parsed TPDU instance.
        :rtype: ~icspacket.proto.cotp.structs.TPDU
        :raises ConnectionError: If the connection is not established or closed.
        """
        if not self.is_connected():
            raise ConnectionError("Connection not established")

        # add size of TPKT header here
        size = 2**self.__tpdu_size.value
        if isinstance(self.sock, tpktsock):
            size += 4

        data = self.sock.recv(size)
        if not data:
            raise ConnectionClosedError("Connection closed")

        tpdu = parse_tpdu(data)
        logger.log(
            TRACE,
            "Received (%s) TPDU with %d bytes",
            tpdu.tpdu_code.name,
            len(data),
        )
        return tpdu

    @override
    def send_data(self, data: bytes) -> None:
        """
        Send user data segmented into DT (Data Transfer) TPDUs.

        :param data: User data to transmit.
        :type data: bytes
        :raises ConnectionError: If the connection is not valid or established.
        """
        if not self._valid:
            raise ConnectionError("Connection not established")

        offset = 0
        tpdu_nr = 0
        data_len = len(data)
        # We have to subtract the fixed TPDU size here
        max_tpdu_size = 2**self.__tpdu_size.value - 3
        while offset < data_len:
            chunk = data[offset : min(data_len, offset + max_tpdu_size)]
            offset += len(chunk)

            dt_tpdu = TPDU_Data()
            dt_tpdu.nr.eot = offset >= data_len
            dt_tpdu.nr.value = tpdu_nr
            dt_tpdu.user_data = chunk
            self.send_tpdu(dt_tpdu)
            tpdu_nr = (tpdu_nr + 1) % 0x7F

    @override
    def recv_data(self) -> bytes:
        """
        Receive user data segmented across multiple DT TPDUs (or just a single
        DT TPDU).

        :return: The complete reassembled user data stream.
        :rtype: bytes
        :raises ConnectionError: If the connection is not valid or a non-DT TPDU is received.
        """
        if not self._valid:
            raise ConnectionError("Connection not established")

        parts = []
        while True:
            tpdu = self.receive_tpdu()
            self._propagate_errors(tpdu)
            if not isinstance(tpdu, TPDU_Data):
                raise ConnectionError(
                    f"Expected DT TPDU, got TPDU with code={tpdu.tpdu_code}"
                )

            parts.append(tpdu.user_data)
            if tpdu.is_last:
                break

        return b"".join(parts)
