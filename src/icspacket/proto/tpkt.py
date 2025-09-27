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
# pyright: reportInvalidTypeForm=false
import socket
import logging
import queue

from typing_extensions import override

from caterpillar.shortcuts import pack, struct, BigEndian, this, unpack
from caterpillar.fields import Bytes, uint8, uint16

from icspacket.core.logger import TRACE


logger = logging.getLogger(__name__)


# [RFC 1006] - ISO Transport Service on top of the TCP
@struct(order=BigEndian)
class TPKT:
    """TPKT header structure as defined in [RFC 1006] section 6.

    This class models the ISO transport service packetization layer on top
    of TCP, which introduces a simple 4-byte header in front of each TPDU.
    """

    # fmt: off
    vrsn        : uint8                              = 3
    """
    Version number of the TPKT protocol. This value is fixed to ``3``. If any
    other value is received, the packet should be considered invalid.
    """

    reserved    : uint8                              = 0
    """Reserved for future use"""

    length      : uint16                             = 0
    """Total length of the TPKT in octets, including the 4-byte header."""

    tpdu        : Bytes(this.length - 4)       = b""
    """
    The encapsulated TPDU bytes. The size is determined by ``length - 4``.
    """
    # fmt: on

    @staticmethod
    def from_octets(octets: bytes) -> "TPKT":
        """Deserialize a TPKT from a raw byte sequence.

        :param octets: Byte buffer containing at least one full TPKT.
        :type octets: bytes
        :raises ValueError: If the ``length`` field does not match the actual
            number of received octets.
        :return: Parsed TPKT instance.
        :rtype: TPKT
        """
        obj = unpack(TPKT, octets)
        if obj.length != len(obj.tpdu) + 4:
            raise ValueError(
                f"Invalid length: expected {obj.length}, got {len(obj.tpdu) + 4}. "
                + "This error could indicate a buffer size being too small."
            )
        return obj

    def build(self) -> bytes:
        """Serialize the TPKT into its octet representation.

        Updates the ``length`` field based on the TPDU size and produces a
        byte sequence suitable for transmission over TCP.

        :return: Encoded TPKT packet.
        :rtype: bytes
        """
        # contains the length of entire packet in octets, including
        # packet-header
        self.length = len(self.tpdu) + 4
        return pack(self, TPKT)

#: Convenience constant for decoding 16-bit unsigned integers in
#: big-endian byte order. Used internally for parsing TPKT headers.
#:
#: .. versionadded:: 0.2.4
_U16_BE = BigEndian + uint16


class tpktsock(socket.socket):
    """Socket wrapper that transparently applies TPKT encapsulation.

    This class extends :class:`socket.socket` to provide automatic
    encoding and decoding of **ISO 8073 (TPKT)** headers for
    connection-oriented transport protocols. Applications can use
    :class:`tpktsock` as a drop-in replacement for raw sockets when
    working with TPKT-based communication.

    **Enhancements since 0.2.4:**

    - An internal :class:`queue.Queue` (``in_queue``) is now used to
      buffer partially received or multiple consecutive TPKT PDUs.
    - Improved handling of cases where more than one PDU arrives
      in a single TCP segment. Excess packets are queued for later
      retrieval.
    - Extended validation ensures incomplete headers are safely
      discarded and logged.

    .. versionchanged:: 0.2.4
       Added internal buffering and support for multiple PDUs per TCP segment.
    """

    #: Internal queue for buffered TPKT PDUs awaiting delivery.
    #:
    #: .. versionadded:: 0.2.4
    in_queue: queue.Queue[bytes]

    def __init__(
        self,
        family: int = -1,
        type: int = -1,
        proto: int = -1,
        fileno: int | None = None,
    ) -> None:
        super().__init__(family, type, proto, fileno)
        self.in_queue = queue.Queue()

    def __del__(self):
        if not self.in_queue.empty():
            logger.warning("Leaking %d TPKTs", self.in_queue.qsize())

    def unpack_tpkt(self, octets: bytes) -> bytes:
        """Unpack a TPKT-encapsulated buffer.

        :param octets: Raw bytes received from the socket.
        :type octets: bytes
        :return: Extracted TPDU payload.
        :rtype: bytes
        """
        if not octets:
            return b""

        logger.log(TRACE, "Received %d bytes from socket", len(octets))
        tpkt = TPKT.from_octets(octets)
        if tpkt.length < len(octets):
            logger.warning(
                "Received more than one TPKT: %s < %s. Second packet will be discarded",
                tpkt.length,
                len(octets),
            )
        logger.log(TRACE, "Header complete (message size = %d)", len(tpkt.tpdu))
        return tpkt.tpdu

    @override
    def recv(self, bufsize: int, flags: int = 0, /) -> bytes:
        """
        Receive a TPKT-encapsulated payload.

        If multiple PDUs are present in a single TCP segment, the
        first is returned immediately and subsequent ones are stored
        in :attr:`in_queue` for later retrieval.

        :param bufsize:
            Maximum number of bytes to read from the socket.
        :type bufsize: int
        :param flags:
            Optional flags passed through to the underlying
            :func:`socket.socket.recv`.
        :type flags: int
        :return:
            The payload of a single decoded TPKT PDU.
        :rtype: bytes

        :raises ValueError:
            If the received header length is inconsistent with the
            actual payload size.

        .. versionchanged:: 0.2.4
           Now returns buffered PDUs if available and supports
           handling multiple PDUs per TCP segment.
        """
        if not self.in_queue.empty():
            return self.in_queue.get()

        data = super().recv(bufsize, flags)
        if not data:
            return b""

        logger.log(TRACE, "Received %d bytes from socket", len(data))
        tpkt = TPKT.from_octets(data)
        self.in_queue.put(tpkt.tpdu)
        logger.log(TRACE, "Header complete (message size = %d)", len(tpkt.tpdu))

        if tpkt.length < len(data):
            logger.log(TRACE, "Received more than one TPKT")
            remaining = data[tpkt.length :]
            if len(remaining) < 4:
                logger.warning(
                    "Received more than one TPKT: %s < %s. Second packet will be discarded",
                    tpkt.length,
                    len(data),
                )
                return self.in_queue.get()

            actual_size = unpack(_U16_BE, remaining[2:])
            size = actual_size - len(remaining)
            if size <= 0:
                next_pkt = super().recv(size, flags)
            else:
                next_pkt = b""

            tpkt = TPKT.from_octets(remaining + next_pkt)
            self.in_queue.put(tpkt.tpdu)
            logger.log(
                TRACE, "Header complete (2nd message size = %d)", len(tpkt.tpdu)
            )

        return self.recv(bufsize, flags)

    @override
    def recvfrom(self, bufsize: int, flags: int = 0, /) -> tuple[bytes, tuple]:
        """Receive a TPKT packet along with the sender's address.

        :param bufsize: Maximum number of bytes to receive.
        :type bufsize: int
        :param flags: Optional socket flags.
        :type flags: int, optional
        :return: A tuple of (TPDU bytes, sender address).
        :rtype: tuple[bytes, tuple]
        """
        data, address = super().recvfrom(bufsize, flags)
        return (self.unpack_tpkt(data), address)

    @override
    def send(self, data: bytes, flags: int = 0, /) -> int:
        """Send TPDU bytes, encapsulated into a TPKT.

        :param data: The raw TPDU bytes to send.
        :type data: bytes
        :param flags: Optional socket flags.
        :type flags: int, optional
        :return: Number of bytes sent.
        :rtype: int
        """
        pkt = TPKT(tpdu=data)
        return super().send(pkt.build(), flags)

    @override
    def sendall(self, data: bytes, flags: int = 0, /) -> None:
        """Send all TPDU bytes, encapsulated into a TPKT.

        Ensures the entire buffer is transmitted, as in the standard
        :func:`socket.socket.sendall`.

        :param data: The raw TPDU bytes to send.
        :type data: bytes
        :param flags: Optional socket flags.
        :type flags: int, optional
        """
        pkt = TPKT(tpdu=data)
        logger.log(TRACE, "Sending %d+4 bytes to socket", len(data))
        return super().sendall(pkt.build(), flags)

    @override
    def sendto(self, data: bytes, address: tuple, /) -> int:
        """Send TPDU bytes, encapsulated into a TPKT, to a specific address.

        :param data: The raw TPDU bytes to send.
        :type data: bytes
        :param address: Destination address (host, port).
        :type address: tuple
        :return: Number of bytes sent.
        :rtype: int
        """
        pkt = TPKT(tpdu=data)
        logger.log(TRACE, "Sending %d+4 bytes to socket", len(data))
        return super().sendto(pkt.build(), address)
