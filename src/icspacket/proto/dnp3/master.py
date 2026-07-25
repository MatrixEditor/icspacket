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
import threading
from collections.abc import Callable, Collection
from queue import Queue
from typing import Generic, Literal

from typing_extensions import TypeVar, override, overload

from icspacket.core.connection import (
    ConnectionClosedError,
    ConnectionNotEstablished,
    connection,
)
from icspacket.core.connection import (
    ConnectionError as ICSConnectionError,
)
from icspacket.core.hexdump import hexdump
from icspacket.core.logger import TRACE, TRACE_PACKETS
from icspacket.proto.dnp3.application import APDU, APDU_SEQ_MAX
from icspacket.proto.dnp3.const import FunctionCode
from icspacket.proto.dnp3.link import (
    LPDU,
    LinkDirection,
    LinkPrimaryFunctionCode,
    LinkSecondaryFunctionCode,
)
from icspacket.proto.dnp3.objects.coding import (
    DNP3Objects,
    pack_objects,
)
from icspacket.proto.dnp3.transport import (
    TPDU,
    TPDU_APPLICATION_MAX_LENGTH,
    TPDU_SEQUENCE_MAX,
)

logger = logging.getLogger(__name__)

DEFAULT_RESPONSE_TIMEOUT = 30.0


_UnsolicitedResponseCallback = Callable[[APDU], None]
_APDUCallback = Callable[["DNP3_Master", APDU], None]


class DNP3_Task:
    """Abstract base class for a DNP3 task.

    A DNP3 task represents a unit of work that the Master initiates, such as
    sending a request and handling its response. Each task is responsible
    for preparing an APDU for transmission and for processing the received
    APDU messages once a response arrives.

    Subclasses implement specific task behavior, such as blocking until
    a response is received or executing a callback when a response is
    available.

    :ivar sequence: Application layer sequence number associated with the
        task. Initialized to ``-1`` and updated when the APDU is transmitted.
    :vartype sequence: int
    """

    def __init__(self) -> None:
        """Initialize a new DNP3 task with an unset sequence number."""
        self.sequence: int = -1

    def prepare_transmit(self, master: "DNP3_Master") -> APDU:
        """Prepare the APDU for transmission.

        Subclasses must implement this to return the request APDU that will
        be sent to the outstation.

        :param master: The DNP3 master instance initiating the transmission.
        :type master: DNP3_Master
        :return: The APDU to transmit.
        :rtype: APDU
        :raises NotImplementedError: If the method is not overridden in
            a subclass.
        """
        raise NotImplementedError

    def on_message(self, master: "DNP3_Master", message: APDU) -> None:
        """Handle a received APDU message.

        This is called when the Master receives a response APDU for the
        task. The default implementation does nothing.

        :param master: The DNP3 master instance handling the message.
        :type master: DNP3_Master
        :param message: The received APDU response.
        :type message: APDU
        """
        pass


class BlockingTask(DNP3_Task):
    """Blocking DNP3 task.

    This task type blocks the caller until a response is received or the
    wait is interrupted. It is suitable for synchronous workflows where the
    Master must wait for the result before proceeding.

    :ivar request: The request APDU to send to the outstation.
    :vartype request: APDU
    :ivar event: A threading event used to signal when a response has been
        received.
    :vartype event: threading.Event
    :ivar message: The response APDU received from the outstation. ``None``
        until a response is available.
    :vartype message: APDU | None
    """

    def __init__(self, request: APDU, event: threading.Event) -> None:
        """Initialize a blocking task.

        :param request: The request APDU to transmit.
        :type request: APDU
        :param event: The event object to notify when a response arrives.
        :type event: threading.Event
        """
        super().__init__()
        self.event: threading.Event = event
        self.request: APDU = request
        self.message: APDU | None = None

    @override
    def on_message(self, master: "DNP3_Master", message: APDU) -> None:
        """Store the received message and notify the waiting thread.

        :param master: The DNP3 master instance that received the message.
        :type master: DNP3_Master
        :param message: The received APDU.
        :type message: APDU
        """
        self.message = message
        self.event.set()

    @override
    def prepare_transmit(self, master: "DNP3_Master") -> APDU:
        """Return the request APDU to be transmitted.

        :param master: The DNP3 master instance initiating the transmission.
        :type master: DNP3_Master
        :return: The request APDU.
        :rtype: APDU
        """
        return self.request

    def wait(self, timeout: float | None = None) -> bool:
        """Block until the response event is set.

        This method waits for the outstation's response to arrive.

        :param timeout: Optional timeout in seconds.
        :type timeout: float | None
        :return: ``True`` if a response arrived, otherwise ``False``.
        :rtype: bool
        """
        return self.event.wait(timeout)


class NonBlockingTask(DNP3_Task):
    """Non-blocking DNP3 task.

    This task type does not block the caller. Instead, it uses a callback
    mechanism that is executed when a response APDU is received. This is
    suitable for asynchronous workflows or event-driven applications.

    :ivar request: The request APDU to send to the outstation.
    :vartype request: APDU
    :ivar callback: Optional callback to be executed when a response is
        received. The callback receives the Master instance and the APDU
        as arguments.
    :vartype callback: _APDUCallback | None
    """

    def __init__(self, request: APDU, callback: _APDUCallback | None) -> None:
        """Initialize a non-blocking task.

        :param request: The request APDU to transmit.
        :type request: APDU
        :param callback: The callback function to execute when a response is
            received. May be ``None`` if no callback is needed.
        :type callback: _APDUCallback | None
        """
        super().__init__()
        self.callback: _APDUCallback | None = callback
        self.request: APDU = request

    @override
    def prepare_transmit(self, master: "DNP3_Master") -> APDU:
        """Return the request APDU to be transmitted.

        :param master: The DNP3 master instance initiating the transmission.
        :type master: DNP3_Master
        :return: The request APDU.
        :rtype: APDU
        """
        return self.request

    @override
    def on_message(self, master: "DNP3_Master", message: APDU) -> None:
        """Invoke the callback with the received APDU.

        If a callback is defined, it is executed with the Master instance and
        the received APDU. Any exceptions raised in the callback are caught
        and logged.

        :param master: The DNP3 master instance that received the message.
        :type master: DNP3_Master
        :param message: The received APDU response.
        :type message: APDU
        """
        try:
            if self.callback:
                self.callback(master, message)
        except Exception:
            logger.exception("Uncaught callback exception")


class DNP3_Link(connection):
    """Implements the DNP3 Link Layer.

    This class drives one endpoint of a DNP3 link connection, moving Link
    Protocol Data Units (LPDUs) between a master and an outstation over a
    transport medium such as TCP. It is responsible for:

    - Encapsulation of octet streams into LPDUs.
    - Validation of source/destination addresses.
    - Handling link-layer function codes (e.g., `UNCONFIRMED_USER_DATA`,
      `REQUEST_LINK_STATUS`, `LINK_STATUS`, `NOT_SUPPORTED`).
    - Forwarding valid user data to the upper layer.

    The class maintains an internal input queue of received LPDUs that have
    passed validation and are intended for the upper layers.

    :param src: The source link-layer address of this endpoint.
    :type src: int
    :param dst: The expected destination address of the remote peer.
    :type dst: int
    :param sock: Optional pre-initialized TCP socket. If ``None``, a new
        socket will be created.
    :type sock: socket.socket | None
    :param mode: Link direction, either MASTER or OUTSTATION.
    :type mode: LinkDirection
    """

    def __init__(
        self,
        src: int,
        dst: int,
        sock: socket.socket | None = None,
        mode: LinkDirection = LinkDirection.MASTER,
    ) -> None:
        super().__init__()
        self.__src: int = src
        self.__dst: int = dst
        self.__dir: LinkDirection = mode
        self.__in_queue: Queue[LPDU] = Queue()
        self.__rx_buffer: bytearray = bytearray()

        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock: socket.socket = sock

    @property
    def in_queue(self) -> Queue[LPDU]:
        """Queue of validated inbound LPDUs.

        Only LPDUs that pass address and direction checks are placed into
        this queue for higher-layer consumption.

        :rtype: Queue[LPDU]
        """
        return self.__in_queue

    @property
    def mode(self) -> LinkDirection:
        """Link direction of this endpoint.

        :rtype: LinkDirection
        """
        return self.__dir

    @property
    def source(self) -> int:
        """The source address of this endpoint.

        :rtype: int
        """
        return self.__src

    @property
    def destination(self) -> int:
        """The expected destination address of the peer.

        :rtype: int
        """
        return self.__dst

    @destination.setter
    def destination(self, dst: int) -> None:
        self.__dst = dst

    @override
    def send_data(self, octets: bytes, /) -> None:
        """Send user data as an unconfirmed LPDU.

        The octets are wrapped into a Link Layer frame with the
        function code `UNCONFIRMED_USER_DATA` and transmitted.

        :param octets: The application/user data to send.
        :type octets: bytes
        :raises ConnectionError: If the socket is not connected.
        """
        self._assert_connected()
        lpdu = LPDU()
        lpdu.control.function_code = LinkPrimaryFunctionCode.UNCONFIRMED_USER_DATA
        lpdu.control.direction = LinkDirection.MASTER
        lpdu.control.primary_message = True
        # raw bytes assignment is possible too
        lpdu.user_data = octets
        self.send_lpdu(lpdu)

    def send_lpdu(self, lpdu: LPDU) -> None:
        """Send a fully constructed LPDU.

        This method sets the LPDU's source and destination before
        serializing and transmitting it over the socket.

        :param lpdu: The LPDU to send.
        :type lpdu: LPDU
        :raises ConnectionError: If the socket is not connected.
        """
        self._assert_connected()
        lpdu.source = self.source
        lpdu.destination = self.destination
        self.sock.sendall(lpdu.build())

    @override
    def recv_data(self) -> bytes:
        """Receive raw LPDU octets from the socket.

        Reads up to 292 bytes, which is the maximum LPDU size
        (according to the Link Layer specification, length field max 255
        plus headers).

        :return: Raw bytes read from the socket.
        :rtype: bytes
        :raises ConnectionError: If the socket is not connected.
        """
        self._assert_connected()
        # Link Layer LENGTH field (Section 9.2.4.1.2): its encoded range runs
        # from 5 (header only, no user data) up to 255, which is why the
        # largest complete LPDU - header plus CRCs - tops out at 292 bytes.
        octets = self.sock.recv(292)
        if octets == b"":
            self._connected: bool = False
            self._valid: bool = False
            raise ConnectionClosedError("Socket closed while receiving DNP3 data")

        return octets

    def send_ack(self) -> None:
        """Send a link-layer ACK response."""
        self._assert_connected()
        lpdu = LPDU()
        lpdu.control.function_code = LinkSecondaryFunctionCode.ACK
        lpdu.control.direction = LinkDirection.MASTER
        lpdu.control.primary_message = False
        self.send_lpdu(lpdu)

    def send_link_status(self, request: LPDU) -> None:
        """Send a link status response.

        Constructs an LPDU with function code `LINK_STATUS`
        and transmits it.

        :param request: The received REQUEST_LINK_STATUS LPDU.
        :type request: LPDU
        :raises ConnectionError: If the socket is not connected.

        .. versionchanged:: 0.2.2
            Added ``request`` parameter.
        """
        self._assert_connected()
        lpdu = LPDU()
        lpdu.control.function_code = LinkSecondaryFunctionCode.LINK_STATUS
        lpdu.control.direction = LinkDirection.MASTER
        lpdu.control.primary_message = False
        self.send_lpdu(lpdu)

    def send_not_supported(self) -> None:
        """Send a 'Not Supported' response.

        Constructs an LPDU with function code `NOT_SUPPORTED`
        and transmits it.

        :raises ConnectionError: If the socket is not connected.
        """
        self._assert_connected()
        lpdu = LPDU()
        lpdu.control.function_code = LinkSecondaryFunctionCode.NOT_SUPPORTED
        lpdu.control.direction = LinkDirection.MASTER
        lpdu.control.primary_message = False
        self.send_lpdu(lpdu)

    def _process_lpdu(self, lpdu: LPDU, raw_octets: bytes) -> bool:
        """Validate and process a received LPDU.

        Performs address and direction checks. Depending on the function
        code, the LPDU may be forwarded to the upper layer, trigger a
        link-status response, or a not-supported response.

        :param lpdu: The parsed LPDU.
        :type lpdu: LPDU
        :param raw_octets: The raw octets from which the LPDU was parsed.
        :type raw_octets: bytes
        :return: ``True`` if the LPDU should be forwarded to the upper layer,
            ``False`` otherwise.
        :rtype: bool
        """
        if lpdu.control.direction == self.mode:
            logger.log(
                TRACE,
                (
                    "[LINK] Received master-to-master LPDU"
                    if self.mode == LinkDirection.MASTER
                    else "Received secondary-to-secondary LPDU"
                ),
                lpdu,
            )
            return False

        if lpdu.destination != self.source:
            logger.log(
                TRACE,
                "[LINK] Received unexpected LPDU with destination address %#04x, expected %#04x",
                lpdu.destination,
                self.source,
            )
            return False

        if lpdu.source != self.destination:
            logger.log(
                TRACE,
                "[LINK] Received unexpected LPDU with source address %#04x, expected %#04x",
                lpdu.source,
                self.destination,
            )
            return False

        if lpdu.control.primary_message:
            try:
                code = lpdu.control.pri2sec_code
            except ValueError:
                logger.log(
                    TRACE_PACKETS,
                    "[LINK] Primary function code not supported:\n%s",
                    hexdump(raw_octets),
                )
                self.send_not_supported()
                return False

            logger.log(
                TRACE_PACKETS,
                "[LINK] Received primary LPDU with code %s\n%s",
                code.name,
                hexdump(raw_octets),
            )
            match code:
                case LinkPrimaryFunctionCode.UNCONFIRMED_USER_DATA:
                    return True
                case LinkPrimaryFunctionCode.CONFIRMED_USER_DATA:
                    self.send_ack()
                    return True
                case (
                    LinkPrimaryFunctionCode.RESET_LINK_STATES
                    | LinkPrimaryFunctionCode.TEST_LINK_STATES
                ):
                    self.send_ack()
                case LinkPrimaryFunctionCode.REQUEST_LINK_STATUS:
                    logger.log(TRACE, "Peer requested link status")
                    self.send_link_status(lpdu)
                case _:  # pyright: ignore[reportUnnecessaryComparison]
                    logger.log(
                        TRACE_PACKETS,
                        "Function code <%s> not supported:\n%s",
                        code.name,
                        hexdump(raw_octets),
                    )
                    self.send_not_supported()
            return False

        try:
            code = lpdu.control.sec2pri_code
        except ValueError:
            logger.log(
                TRACE_PACKETS,
                "[LINK] Ignoring unknown secondary function code:\n%s",
                hexdump(raw_octets),
            )
            return False

        logger.log(
            TRACE_PACKETS,
            "[LINK] Received secondary LPDU with code %s\n%s",
            code.name,
            hexdump(raw_octets),
        )
        if code == LinkSecondaryFunctionCode.NACK:
            logger.log(TRACE, "[LINK] Peer returned link-layer NACK")
        elif code == LinkSecondaryFunctionCode.NOT_SUPPORTED:
            logger.log(
                TRACE, "[LINK] Peer does not support the requested link function"
            )
        return False

    def _read_until_buffered(self, min_size: int) -> None:
        while len(self.__rx_buffer) < min_size:
            self.__rx_buffer.extend(self.recv_data())

    def _next_raw_lpdu(self) -> bytes:
        sync = b"\x05\x64"
        while True:
            self._read_until_buffered(3)

            sync_offset = self.__rx_buffer.find(sync)
            if sync_offset < 0:
                del self.__rx_buffer[:-1]
                continue

            if sync_offset > 0:
                del self.__rx_buffer[:sync_offset]

            self._read_until_buffered(3)
            if self.__rx_buffer[2] < 5:
                del self.__rx_buffer[:2]
                continue

            length = LPDU.full_length(self.__rx_buffer[2])
            self._read_until_buffered(length)

            raw_lpdu = bytes(self.__rx_buffer[:length])
            del self.__rx_buffer[:length]
            return raw_lpdu

    def recv_lpdu(self) -> LPDU:
        """Receive and parse the next valid LPDU.

        This method handles fragmented reception (multiple LPDUs in
        one read) and incomplete frames. Valid frames that pass link
        validation are placed in the inbound queue.

        :return: The next valid LPDU for the upper layer.
        :rtype: LPDU
        :raises ConnectionError: If the socket is not connected.
        """
        while self.in_queue.empty():
            raw_lpdu = self._next_raw_lpdu()
            try:
                lpdu = LPDU.from_octets(raw_lpdu)
            except Exception as e:
                logger.log(
                    TRACE,
                    "[LINK] Ignoring invalid LPDU: %s\n%s",
                    e,
                    hexdump(raw_lpdu),
                )
                continue

            if self._process_lpdu(lpdu, raw_lpdu):
                self.in_queue.put(lpdu)

        return self.in_queue.get()

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """Connect the socket to the specified peer address.

        :param address: Peer address as a tuple of (host, port).
        :type address: tuple[str, int]
        """
        if self.is_connected():
            return

        self.sock.connect(address)
        self._connected = True
        self._valid = True

    @override
    def close(self) -> None:
        """Close the underlying socket connection."""
        if self.is_connected():
            self.sock.close()
            self._connected = False
            self._valid = False


_LinkT = TypeVar("_LinkT", bound=DNP3_Link, default=DNP3_Link)


class DNP3_Transport(connection, Generic[_LinkT]):
    """DNP3 Transport Layer implementation.

    This class implements the transport layer of the DNP3 protocol, providing
    fragmentation and reassembly of Application Protocol Data Units (APDUs)
    into Transport Protocol Data Units (TPDUs). It sits above the Link Layer
    (:class:`DNP3_Link`) and ensures that application data is transmitted in
    compliance with the transport rules defined in the DNP3 standard.

    Key responsibilities of this layer include:

    * Fragmenting application data into transport segments (1-249 octets each).
    * Wrapping each fragment into a TPDU with proper sequence numbering.
    * Reassembling received TPDUs into complete APDUs.
    * Detecting and handling unsolicited responses, optionally invoking a
      user-provided callback.

    :param link: The link layer object that provides LPDU transmission and reception.
    :type link: DNP3_Link
    :param unsolicited_callback: Optional callback function invoked when an unsolicited
        response APDU is received from the outstation.
    :type unsolicited_callback: Callable[[APDU], None] | None
    """

    def __init__(
        self,
        link: _LinkT,
        unsolicited_callback: _UnsolicitedResponseCallback | None = None,
    ) -> None:
        super().__init__()
        self.__link: _LinkT = link
        self.callback: _UnsolicitedResponseCallback | None = unsolicited_callback
        self.sequence: int = 0
        self._connected: bool = self.link.is_connected()
        self._valid: bool = self.link.is_valid()

    @property
    def link(self) -> _LinkT:
        """Return the underlying link layer object.

        :return: The active :class:`DNP3_Link` instance.
        :rtype: DNP3_Link
        """
        return self.__link

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """Establish a connection through the link layer.

        This method delegates the connection setup to the underlying
        :class:`DNP3_Link` object, updating the transport connection state.

        :param address: A tuple containing the IP address and port number of the outstation.
        :type address: tuple[str, int]
        """
        self.link.connect(address)
        self._connected = self.link.is_connected()
        self._valid = self.link.is_valid()

    @override
    def close(self) -> None:
        """Close the transport connection.

        This method closes the link layer connection and updates the
        internal connection status.
        """
        self.link.close()
        self._connected = self.link.is_connected()
        self._valid = self.link.is_valid()

    def next_sequence(self) -> int:
        """Get the next transport sequence number.

        The transport layer maintains an internal 6-bit sequence counter
        used for ordering TPDUs. After reaching the maximum value, the
        counter wraps around to zero.

        :return: The current transport sequence number before incrementing.
        :rtype: int
        """
        sequence = self.sequence
        self.sequence = (self.sequence + 1) % TPDU_SEQUENCE_MAX
        return sequence

    @override
    def send_data(self, octets: bytes, /) -> None:
        """Send application data through the transport layer.

        This method fragments the given application data into one or more
        TPDUs (each up to 249 octets). Each TPDU is assigned sequence
        numbers and FIR/FIN flags. The fragments are then transmitted via
        the link layer.

        :param octets: The application data bytes to transmit.
        :type octets: bytes
        :raises ConnectionError: If the transport connection is not established.
        """
        self._assert_connected()
        # Cap each segment at TPDU_APPLICATION_MAX_LENGTH (249) octets of
        # application data, splitting larger payloads across several segments.
        if len(octets) > TPDU_APPLICATION_MAX_LENGTH:
            fragments = [
                octets[i : min(len(octets), i + TPDU_APPLICATION_MAX_LENGTH)]
                for i in range(0, len(octets), TPDU_APPLICATION_MAX_LENGTH)
            ]
        else:
            fragments = [octets]

        for i, fragment in enumerate(fragments):
            tpdu = TPDU()
            tpdu.first_segment = i == 0
            tpdu.final_segment = i == len(fragments) - 1
            tpdu.sequence = self.next_sequence()
            tpdu.app_fragment = fragment
            self.link.send_data(bytes(tpdu))

    @override
    def recv_data(self) -> bytes:
        """Receive and reassemble application data from the transport layer.

        This method collects one or more TPDUs received from the link layer
        and reconstructs the original APDU. It validates transport sequence
        numbers to ensure proper ordering. Unsolicited responses are detected
        and optionally passed to the callback without being returned to the caller.

        :return: The fully reassembled APDU bytes.
        :rtype: bytes
        :raises ConnectionError: If the transport connection is not established.
        """
        self._assert_connected()
        while True:
            fragments: list[bytes] = []
            expected_sequence = None
            while True:
                lpdu = self.link.recv_lpdu()
                tpdu = lpdu.user_data
                if tpdu is None:
                    continue

                logger.log(
                    TRACE,
                    "[TRANSPORT] Received TPDU with sequence %d, FIR: %s, FIN: %s, "
                    + "size: %d",
                    tpdu.sequence,
                    tpdu.first_segment,
                    tpdu.final_segment,
                    len(tpdu.app_fragment),
                )

                if expected_sequence is None:
                    if not tpdu.first_segment:
                        logger.log(
                            TRACE,
                            "[TRANSPORT] Ignoring TPDU without first-segment flag",
                        )
                        continue
                    expected_sequence = tpdu.sequence
                elif tpdu.first_segment:
                    logger.log(
                        TRACE,
                        "[TRANSPORT] Restarting reassembly on unexpected FIR segment",
                    )
                    fragments.clear()
                    expected_sequence = tpdu.sequence

                if tpdu.sequence != expected_sequence:
                    logger.log(
                        TRACE,
                        "[TRANSPORT] Received unexpected TPDU with sequence %d, "
                        + "expected %d",
                        tpdu.sequence,
                        expected_sequence,
                    )
                    fragments.clear()
                    expected_sequence = None
                    continue

                fragments.append(tpdu.app_fragment)
                expected_sequence = (expected_sequence + 1) % TPDU_SEQUENCE_MAX
                if tpdu.final_segment:
                    break

            apdu_octets = b"".join(fragments)
            logger.log(
                TRACE, "[TRANSPORT] Reassembled APDU in %d bytes", len(apdu_octets)
            )

            if self.callback:
                try:
                    apdu = APDU.from_octets(apdu_octets)
                except Exception:
                    return apdu_octets

                if (
                    apdu.control.unsolicited_response
                    or apdu.function == FunctionCode.UNSOLICITED_RESPONSE
                ):
                    logger.log(
                        TRACE,
                        "[TRANSPORT] Received unsolicited response with sequence %d",
                        apdu.control.sequence,
                    )
                    try:
                        self.callback(apdu)
                    except Exception as e:
                        logger.warning(
                            "[TRANSPORT] Error while processing unsolicited "
                            + "response: %s",
                            e,
                        )
                    continue

            return apdu_octets


class DNP3_Master(Generic[_LinkT]):
    """DNP3 Master (Application Layer interface).

    This class provides the master-side interface of the DNP3 protocol stack,
    built on top of the transport and link layers. It manages request/response
    exchanges with an outstation, schedules tasks, and assigns application
    sequence numbers. The master does not implement actual application logic -
    instead, it delegates handling to user-defined :class:`DNP3_Task` objects.

    This implementation supports:

    * Establishing and releasing associations with outstations.
    * Submitting tasks that generate and transmit APDUs.
    * Assigning and cycling application sequence numbers.
    * Supporting both blocking and non-blocking request patterns.
    * Optionally dispatching requests without expecting a return
      (:meth:`submit_noreturn`).

    Example::

        master = DNP3_Master(link_addr=0x0001)
        # connect to remote at 127.0.0.1:20000 with link addr 1024
        master.associate((1024, "127.0.0.1", 20000))

        # request class 1 objects
        objects = new_class_data_request(1)
        result = master.request(FunctionCode.READ, objects)

    :param link_addr: The source link-layer address of the master.
    :type link_addr: int
    :param initial_seq: Optional initial application sequence number.
        Defaults to ``0`` if not provided.
    :type initial_seq: int | None
    :param sock: Optional socket to bind the link layer to. If omitted,
        a new socket will be created when associating with an outstation.
    :type sock: socket.socket | None
    """

    def __init__(
        self,
        link_addr: int,
        initial_seq: int | None = None,
        sock: socket.socket | None = None,
        link_cls: type[_LinkT] | None = None,
    ) -> None:
        # fmt: off
        super().__init__()
        self.__link_addr: int = link_addr
        self.__transport: DNP3_Transport[_LinkT] | None = None
        self.__tasks: dict[int, DNP3_Task] = {}
        self.__sequence: int = initial_seq or 0
        self.__background: DNP3_Background = DNP3_Background(self)  # pyright: ignore[reportArgumentType]
        self.__socket: socket.socket | None = sock
        self._valid: bool = False
        self.link_cls: type[_LinkT] = (
            link_cls or DNP3_Link
        )  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def tasks(self) -> Collection[DNP3_Task]:
        """Return the currently registered tasks.

        :return: A collection of active tasks indexed by sequence number.
        :rtype: Collection[DNP3_Task]
        """
        return self.__tasks.values()

    @property
    def transport(self) -> DNP3_Transport[_LinkT]:
        """Return the transport layer instance.

        :return: The active :class:`DNP3_Transport` object.
        :rtype: DNP3_Transport
        """
        if self.__transport is None:
            raise ValueError("No DNP3 Transport set!")

        return self.__transport

    @property
    def sequence(self) -> int:
        """Return the current application sequence number.

        The sequence number is incremented and wrapped automatically
        whenever a request is submitted.

        :return: The current APDU sequence number.
        :rtype: int
        """
        return self.__sequence

    def get_task(self, sequence: int) -> DNP3_Task | None:
        """Retrieve a task by its sequence number.

        :param sequence: The sequence number of the task to fetch.
        :type sequence: int
        :return: The corresponding :class:`DNP3_Task`, or ``None`` if not found.
        :rtype: DNP3_Task | None
        """
        return self.__tasks.get(sequence)

    def pop_task(self, sequence: int) -> DNP3_Task | None:
        """Remove and return a task by its sequence number.

        :param sequence: The sequence number of the task to remove.
        :type sequence: int
        :return: The removed :class:`DNP3_Task`, or ``None`` if not found.
        :rtype: DNP3_Task | None
        """
        return self.__tasks.pop(sequence, None)

    def associate(
        self,
        address: tuple[int, str, int],
        link_cls: type[_LinkT] | None = None,
    ) -> None:
        """Establish an association with an outstation.

        This method sets up the underlying link and transport layers,
        connects to the given host/port, and starts background processing
        of incoming messages.

        :param address: A tuple of the form ``(link_addr, host, port)``.
        :type address: tuple[int, str, int]
        :param link_cls: Optional link layer class to use. If not provided,
            the default :class:`DNP3_Link` will be used.
        :type link_cls: type[DNP3_Link]
        :raises ValueError: If the provided address tuple is invalid.

        .. versionchanged:: 0.2.2
            Added ``link_cls`` parameter.
        """
        if self._valid:
            return

        if len(address) != 3:
            raise ValueError("Invalid address - expected (link_addr, host, port)")

        if link_cls:
            self.link_cls = link_cls

        link_dst, host, port = address
        self.__transport = DNP3_Transport(
            (self.link_cls)(sock=self.__socket, src=self.__link_addr, dst=link_dst)
        )
        self.__transport.connect((host, port))
        self._valid = True
        self.__background.start()

    def release(self, timeout: float | None = None) -> None:
        """Release the association with the outstation.

        This method stops the background thread, closes the transport
        connection, and invalidates the master instance.

        :param timeout: Optional timeout (in seconds) to wait for the
            background thread to join.
        :type timeout: float | None
        """
        if not self._valid:
            return

        self.__background.stop.set()
        self.__background.join(timeout)
        if self.__transport is not None:
            self.__transport.close()
        for task in self.__tasks.values():
            if isinstance(task, BlockingTask):
                task.event.set()
        self.__tasks.clear()
        self._valid = False
        self.__background = DNP3_Background(self)

    def submit_task(self, task: DNP3_Task) -> None:
        """Submit a task and register it for response handling.

        The task will be assigned the current application sequence number,
        which is then incremented. The request APDU is built by the task
        and transmitted through the transport layer.

        :param task: The task to be submitted.
        :type task: DNP3_Task
        :raises ConnectionError: If the task fails to produce a valid APDU.
        """
        if not self._valid:
            raise ConnectionNotEstablished("Not associated with an outstation")

        sequence = self.sequence
        task.sequence = sequence
        apdu = task.prepare_transmit(self)
        if apdu is None:
            raise ConnectionError("Unable to build APDU for task")

        apdu.control.sequence = sequence
        self.__tasks[sequence] = task
        try:
            self.transport.send_data(bytes(apdu))
        except Exception:
            _ = self.pop_task(sequence)
            raise
        self.__sequence = (sequence + 1) % APDU_SEQ_MAX

    def submit_noreturn(self, task: DNP3_Task) -> None:
        """Submit a task without expecting a response.

        Unlike :meth:`submit_task`, the task is not registered for later
        lookup, meaning no response will be matched or delivered.

        :param task: The task to be submitted.
        :type task: DNP3_Task
        :raises ConnectionError: If the task fails to produce a valid APDU.
        """
        if not self._valid:
            raise ConnectionNotEstablished("Not associated with an outstation")

        apdu = task.prepare_transmit(self)
        if apdu is None:
            raise ConnectionError("Unable to build APDU for task")

        sequence = self.sequence
        apdu.control.sequence = sequence
        self.__sequence = (sequence + 1) % APDU_SEQ_MAX
        self.transport.send_data(bytes(apdu))

    def send_confirm(self, sequence: int, unsolicited: bool = False) -> None:
        """Send an application-layer confirmation APDU.

        :param sequence: Application sequence number being confirmed.
        :type sequence: int
        :param unsolicited: Whether this confirms an unsolicited response.
        :type unsolicited: bool
        """
        if not self._valid:
            raise ConnectionNotEstablished("Not associated with an outstation")

        apdu = APDU()
        apdu.control.first_fragment = True
        apdu.control.final_fragment = True
        apdu.control.unsolicited_response = unsolicited
        apdu.control.sequence = sequence % APDU_SEQ_MAX
        apdu.function = FunctionCode.CONFIRM
        self.transport.send_data(bytes(apdu))

    def transmit(
        self,
        request: APDU,
        block: bool = True,
        callback: _APDUCallback | None = None,
        noreturn: bool = False,
        timeout: float | None = DEFAULT_RESPONSE_TIMEOUT,
    ) -> APDU | None:
        """Transmit a request APDU to the outstation.

        This method provides both blocking and non-blocking transmission
        modes. In blocking mode, it waits for the corresponding response
        before returning. In non-blocking mode, the provided callback will
        be invoked when the response is received.

        :param request: The APDU to transmit.
        :type request: APDU
        :param block: Whether to wait for the response. Defaults to ``True``.
        :type block: bool
        :param callback: Optional callback to invoke with the response in
            non-blocking mode.
        :type callback: Callable[["DNP3_Master", APDU], None] | None
        :param noreturn: If ``True``, the request is sent without expecting
            a response.
        :type noreturn: bool
        :param timeout: Optional blocking response timeout in seconds.
        :type timeout: float | None
        :return: The received APDU if in blocking mode, otherwise ``None``.
        :rtype: APDU | None
        :raises TimeoutError: If blocking mode times out.
        """
        if block:
            message_received = threading.Event()
            task = BlockingTask(request, message_received)
            self.submit_task(task)
            if not task.wait(timeout):
                self.pop_task(task.sequence)
                raise TimeoutError("Timed out waiting for DNP3 response")
            return task.message

        task = NonBlockingTask(request, callback)
        if noreturn:
            self.submit_noreturn(task)
        else:
            self.submit_task(task)

    def request(
        self,
        function: FunctionCode,
        objects: DNP3Objects | None = None,
        need_confirm: bool = False,
        block: bool = True,
        callback: _APDUCallback | None = None,
        noreturn: bool = False,
        timeout: float | None = DEFAULT_RESPONSE_TIMEOUT,
    ) -> APDU | None:
        """Build and transmit a request APDU.

        This is the high-level entry point for sending function code requests
        to an outstation. Optionally, objects can be included, confirmation
        can be requested, and the call may be synchronous or asynchronous.

        :param function: The DNP3 application function code.
        :type function: FunctionCode
        :param objects: Optional collection of DNP3 objects to include.
        :type objects: DNP3Objects | None
        :param need_confirm: Whether a confirmation is required.
        :type need_confirm: bool
        :param block: Whether to wait for the response.
        :type block: bool
        :param callback: Callback to invoke in asynchronous mode.
        :type callback: Callable[["DNP3_Master", APDU], None] | None
        :param noreturn: If ``True``, send without expecting a response.
        :type noreturn: bool
        :param timeout: Optional blocking response timeout in seconds.
        :type timeout: float | None
        :return: The APDU response in blocking mode, otherwise ``None``.
        :rtype: APDU | None
        :raises ValueError: If both ``need_confirm`` and ``noreturn`` are set.
        """
        apdu = APDU()
        apdu.control.sequence = self.sequence
        apdu.control.first_fragment = True
        apdu.control.final_fragment = True
        apdu.control.need_confirmation = need_confirm
        if need_confirm and noreturn:
            raise ValueError("Cannot specify both need_confirm and noreturn")

        apdu.function = function
        if objects:
            apdu.objects = pack_objects(objects)

        if block:
            return self.transmit(apdu, timeout=timeout)
        else:
            _ = self.transmit(apdu, block=False, callback=callback, noreturn=noreturn)
            return None


class DNP3_Background(threading.Thread):
    """Background listener thread for a DNP3 master.

    This thread continuously receives octets from the master's transport
    layer, parses them into APDUs, and dispatches the results to the
    corresponding task based on the application sequence number.

    The listener operates in daemon mode, meaning it will not prevent
    application shutdown. It is started automatically by
    :meth:`DNP3_Master.associate` and terminated by
    :meth:`DNP3_Master.release`.

    :param master: The :class:`DNP3_Master` instance that owns this background
        listener.
    :type master: DNP3_Master
    """

    def __init__(self, master: DNP3_Master) -> None:
        super().__init__(daemon=True)
        self.master: DNP3_Master = master
        #: Event flag used to signal termination of the thread.
        #: :type: threading.Event
        self.stop: threading.Event = threading.Event()

    @override
    def run(self) -> None:
        """Thread entry point.

        This method repeatedly reads data from the master's transport layer
        until :attr:`stop` is set or a connection error occurs. Each received
        frame is decoded into an :class:`APDU`. If the APDU is not an
        unsolicited response, it is delivered to the task registered under
        the APDU's sequence number.
        """
        while not self.stop.is_set():
            try:
                octets = self.master.transport.recv_data()
            except (OSError, ICSConnectionError):
                self.stop.set()
                break

            apdu = APDU.from_octets(octets)
            if apdu.control.need_confirmation:
                self.master.send_confirm(
                    apdu.control.sequence,
                    apdu.control.unsolicited_response
                    or apdu.function == FunctionCode.UNSOLICITED_RESPONSE,
                )

            if (
                apdu.function != FunctionCode.UNSOLICITED_RESPONSE
                and not apdu.control.unsolicited_response
            ):
                task = self.master.pop_task(apdu.control.sequence)
                if task:
                    task.on_message(self.master, apdu)
