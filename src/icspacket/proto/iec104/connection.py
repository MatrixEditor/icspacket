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
"""
IEC104_Connection - the APCI state machine (IEC 60870-5-104 framing layer).

(See IEC 60870-5-104, clause 5 - APCI structure, and clause 6 - APCI use on
the network layer, for the STARTDT/STOPDT/TESTFR handshake and the
I/S-format sequence-number bookkeeping this class implements.)
"""

import logging
import select
import socket
import threading
import time
from queue import Empty, Queue

from typing_extensions import override

from icspacket.core.connection import (
    ConnectionClosedError,
    ConnectionNotEstablished,
    connection,
)
from icspacket.core.connection import (
    ConnectionError as ICSConnectionError,
)
from icspacket.core.logger import TRACE
from icspacket.proto.iec104.apci import APCI, APCI_MAX_ASDU_LENGTH
from icspacket.proto.iec104.asdu import ASDU
from icspacket.proto.iec104.const import (
    K_DEFAULT,
    T0_DEFAULT,
    T1_DEFAULT,
    T2_DEFAULT,
    T3_DEFAULT,
    W_DEFAULT,
    APCIFormat,
    UFormatFunction,
)

__all__ = [
    "IEC104ProtocolError",
    "IEC104_Connection",
]

logger = logging.getLogger(__name__)

SEQ_MODULUS = 1 << 15
"""Modulus of the 15-bit ``V(S)``/``V(R)`` I-format sequence counters."""

_POLL_INTERVAL = 1.0
"""How often (seconds) the background reader wakes up to re-check
``t1``/``t2``/``t3`` while no frame is available to read."""


def _seq_distance(newer: int, older: int) -> int:
    """Number of sequence steps from ``older`` to ``newer``, modulo
    :data:`SEQ_MODULUS` (always non-negative, handles wraparound)."""
    return (newer - older) % SEQ_MODULUS


class IEC104ProtocolError(ICSConnectionError):
    """
    Raised when the peer violates the APCI state machine - an unexpected
    U-format reply, an out-of-sequence I-format ``N(S)``, or a confirmation
    that fails to arrive before ``t1`` elapses.
    """


class _Reader(threading.Thread):
    """
    Background reader thread for an :class:`IEC104_Connection`.

    Waits (via :func:`select.select`, bounded by :data:`_POLL_INTERVAL`) for
    either an incoming APCI frame or the next timer check, for as long as
    the owning connection remains valid. Runs in daemon mode so it never
    blocks interpreter shutdown.

    :param conn: The connection instance this thread reads for.
    """

    def __init__(self, conn: "IEC104_Connection") -> None:
        super().__init__(daemon=True)
        self.conn: IEC104_Connection = conn
        #: Set to request the loop stop at the next opportunity.
        self.stop: threading.Event = threading.Event()

    @override
    def run(self) -> None:
        conn = self.conn
        while not self.stop.is_set():
            try:
                readable, _, _ = select.select([conn.sock], [], [], _POLL_INTERVAL)
            except OSError:
                break  # socket closed concurrently (e.g. by close()/_fail())

            try:
                if readable:
                    conn.handle_apci(conn.read_one_apci())
                conn.check_timers()
            except (OSError, ICSConnectionError) as e:
                # ICSConnectionError also covers IEC104ProtocolError
                logger.log(TRACE, "[IEC104] Reader stopping: %s", e)
                conn._fail(str(e))
                break


class IEC104_Connection(connection):
    """
    Manages a single IEC 60870-5-104 TCP connection's APCI layer.

    Drives the ``STARTDT``/``STOPDT`` handshake, the I-format ``V(S)``/
    ``V(R)`` send/receive sequence counters and their ``k``/``w`` flow
    control window, automatic S-format acknowledgments, and the
    ``t1``/``t2``/``t3`` timers. :meth:`send_data`/:meth:`recv_data`
    exchange raw encoded ASDU bytes (this class's "user data"); :meth:`send_asdu`/
    :meth:`recv_asdu` are thin convenience wrappers around
    :class:`~icspacket.proto.iec104.asdu.ASDU`.

    Redundant/backup connections are out of scope: this class models
    exactly one TCP socket, matching this module's documented scope.

    Example:

    >>> conn = IEC104_Connection()
    >>> conn.connect(("127.0.0.1", 2404))  # 2404: IEC104_DEFAULT_PORT
    >>> conn.send_asdu(asdu)
    >>> response = conn.recv_asdu(timeout=10)
    >>> conn.close()

    :param sock: Existing TCP socket to use; a new one is created if omitted.
    :type sock: socket.socket | None
    :param t0: Connect timeout in seconds (default :data:`~icspacket.proto.iec104.const.T0_DEFAULT`).
    :type t0: float
    :param t1: Confirmation timeout in seconds (default :data:`~icspacket.proto.iec104.const.T1_DEFAULT`).
    :type t1: float
    :param t2: Acknowledgment timeout in seconds, ``t2 < t1`` (default :data:`~icspacket.proto.iec104.const.T2_DEFAULT`).
    :type t2: float
    :param t3: Idle/keepalive timeout in seconds (default :data:`~icspacket.proto.iec104.const.T3_DEFAULT`).
    :type t3: float
    :param k: Maximum outstanding unacknowledged I-format APDUs (default :data:`~icspacket.proto.iec104.const.K_DEFAULT`).
    :type k: int
    :param w: Received-APDU count triggering an S-format ack, ``w <= k`` (default :data:`~icspacket.proto.iec104.const.W_DEFAULT`).
    :type w: int
    :raises ValueError: If ``w > k``.
    """

    def __init__(
        self,
        sock: socket.socket | None = None,
        t0: float = T0_DEFAULT,
        t1: float = T1_DEFAULT,
        t2: float = T2_DEFAULT,
        t3: float = T3_DEFAULT,
        k: int = K_DEFAULT,
        w: int = W_DEFAULT,
    ) -> None:
        super().__init__()
        if w > k:
            raise ValueError(f"w ({w}) must be <= k ({k})")

        self.sock: socket.socket = sock or socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.t0: float = t0
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.k: int = k
        self.w: int = w

        # -- sequence/window state, guarded by __cond ---------------------- #
        self.__cond = threading.Condition()
        self.__send_seq = 0  # V(S): next send sequence number
        self.__recv_seq = 0  # V(R): next expected receive sequence number
        self.__ack_send_seq = 0  # last V(S) acknowledged by the peer
        self.__unacked_recv = 0  # received I-frames not yet ack'd by us
        self.__oldest_unacked_time: float | None = None
        self.__last_recv_ack_time: float | None = None

        # -- fields only ever touched from the (single) reader thread ----- #
        self.__testfr_pending_since: float | None = None
        self.__last_activity_time: float = 0.0

        self.__send_lock = threading.Lock()
        self.__stopdt_confirmed = threading.Event()
        self.__in_queue: Queue[bytes | None] = Queue()
        self.__reader: _Reader | None = None
        self.__fail_reason: str | None = None

    # -- connection lifecycle -------------------------------------------- #

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """
        Connect to ``address`` and perform the ``STARTDT`` handshake.

        Blocks until either ``STARTDT`` is confirmed or :attr:`t0`/:attr:`t1`
        elapses. Once confirmed, sequence counters are reset to zero and the
        background reader thread is started.

        :param address: ``(host, port)`` of the IEC-104 outstation.
        :type address: tuple[str, int]
        :raises ConnectionError: If the TCP connection itself fails.
        :raises IEC104ProtocolError: If ``STARTDT`` is not confirmed in time
            or the peer replies with something other than ``STARTDT_CON``.
        """
        if self.is_connected():
            return

        host, port = address
        self.sock.settimeout(self.t0)
        try:
            self.sock.connect((host, port))
        except OSError as e:
            raise ICSConnectionError(f"Failed to connect to {host}:{port}") from e

        self._connected: bool = True
        self.__reset_state()

        self.sock.settimeout(self.t1)
        try:
            self._send_apci(APCI.startdt_act())
            apci = self.read_one_apci()
        except (TimeoutError, OSError, ICSConnectionError) as e:
            self._close_socket()
            raise IEC104ProtocolError(
                "Timed out waiting for STARTDT confirmation (t1)"
            ) from e

        is_startdt_con = (
            apci.format == APCIFormat.U_FORMAT
            and apci.control.function == UFormatFunction.STARTDT_CON
        )
        if not is_startdt_con:
            self._close_socket()
            raise IEC104ProtocolError(
                f"Expected STARTDT confirmation, got format={apci.format!r}"
            )

        self._valid: bool = True
        self.sock.settimeout(None)
        self.__last_activity_time = time.monotonic()
        self.__reader = _Reader(self)
        self.__reader.start()
        logger.log(TRACE, "[IEC104] STARTDT confirmed; connected to %s:%d", host, port)

    def __reset_state(self) -> None:
        """Reset sequence/window/timer state for a fresh connection attempt."""
        with self.__cond:
            self.__send_seq = 0
            self.__recv_seq = 0
            self.__ack_send_seq = 0
            self.__unacked_recv = 0
            self.__oldest_unacked_time = None
            self.__last_recv_ack_time = None
        self.__testfr_pending_since = None
        self.__fail_reason = None
        self.__stopdt_confirmed.clear()
        while not self.__in_queue.empty():
            _ = self.__in_queue.get_nowait()

    @override
    def close(self) -> None:
        """
        Gracefully close the connection.

        Sends ``STOPDT act`` and waits (best-effort, bounded by :attr:`t1`)
        for ``STOPDT con`` before stopping the reader thread and closing the
        socket - matching :class:`~icspacket.proto.cotp.connection.COTP_Connection`'s
        best-effort disconnect style.
        """
        if not self.is_connected():
            return

        if self._valid:
            try:
                self.__stopdt_confirmed.clear()
                self._send_apci(APCI.stopdt_act())
                _ = self.__stopdt_confirmed.wait(self.t1)
            except (OSError, ICSConnectionError):
                pass

        self._valid = False
        reader, self.__reader = self.__reader, None
        if reader is not None:
            reader.stop.set()
            if threading.current_thread() is not reader:
                reader.join(timeout=self.t1)

        self._close_socket()
        self.__in_queue.put(None)

    def _close_socket(self) -> None:
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass
        self._connected = False
        self._valid = False

    def _fail(self, reason: str) -> None:
        """
        Mark the connection invalid after a protocol violation or I/O error
        observed by the reader thread, and unblock any thread waiting in
        :meth:`recv_data`/:meth:`send_data`/:meth:`close`.

        :param reason: Human-readable failure reason (logged and raised to
            any blocked :meth:`recv_data_timeout` caller).
        """
        self.__fail_reason = reason
        self._close_socket()
        with self.__cond:
            self.__cond.notify_all()
        self.__stopdt_confirmed.set()
        self.__in_queue.put(None)
        self.__reader = None

    # -- low-level framing -------------------------------------------------- #

    def _recv_exact(self, size: int) -> bytes:
        """
        Read exactly ``size`` bytes, looping over possibly-partial
        :meth:`socket.socket.recv` calls (TCP has no message boundaries).

        :raises ConnectionClosedError: If the peer closes the socket first.
        """
        chunks = bytearray()
        while len(chunks) < size:
            chunk = self.sock.recv(size - len(chunks))
            if not chunk:
                raise ConnectionClosedError(
                    "Socket closed while receiving an APCI frame"
                )
            chunks += chunk
        return bytes(chunks)

    def read_one_apci(self) -> APCI:
        """
        Blocking read of exactly one APCI frame.

        The frame's own length octet (see :class:`~icspacket.proto.iec104.apci.APCI`)
        is used to know exactly how many further bytes belong to it, so this
        never over-reads into the next frame.

        :raises ConnectionClosedError: If the peer closes the socket mid-frame.
        """
        header = self._recv_exact(2)
        length = header[1]
        rest = self._recv_exact(length) if length else b""
        return APCI.from_bytes(header + rest)

    def _send_apci(self, apci: APCI) -> None:
        data = apci.to_bytes()
        with self.__send_lock:
            try:
                self.sock.sendall(data)
            except OSError as e:
                raise ConnectionClosedError("Failed to send APCI frame") from e
        self.__last_activity_time = time.monotonic()
        logger.log(
            TRACE, "[IEC104] Sent %s frame (%d bytes)", apci.format.name, len(data)
        )

    # -- I-format send/recv (connection.send_data/recv_data override) ---- #

    @override
    def send_data(self, octets: bytes, /) -> None:
        """
        Send ``octets`` (a single encoded ASDU) as an I-format APCI frame.

        Blocks (bounded by :attr:`t1`) while the ``k`` send window is full,
        i.e. while :attr:`k` I-format APDUs are already unacknowledged.

        :param octets: Raw encoded ASDU bytes (see :meth:`~icspacket.proto.iec104.asdu.ASDU.build`).
        :type octets: bytes
        :raises ConnectionNotEstablished: If ``STARTDT`` has not been confirmed.
        :raises ValueError: If ``octets`` exceeds :data:`~icspacket.proto.iec104.apci.APCI_MAX_ASDU_LENGTH`.
        :raises IEC104ProtocolError: If the send window stays full past :attr:`t1`
            (per the same "no acknowledgment within t1" rule enforced by
            :meth:`check_timers`, this also fails the connection - matching
            what happens when the reader thread detects the same violation).
        :raises ConnectionClosedError: If the connection closes while waiting.
        """
        if not self._valid:
            raise ConnectionNotEstablished("STARTDT not confirmed")
        if len(octets) > APCI_MAX_ASDU_LENGTH:
            raise ValueError(
                f"ASDU too large ({len(octets)} > {APCI_MAX_ASDU_LENGTH} octets)"
            )

        with self.__cond:
            window_free = self.__cond.wait_for(
                lambda: (
                    not self._valid
                    or _seq_distance(self.__send_seq, self.__ack_send_seq) < self.k
                ),
                timeout=self.t1,
            )
            if not self._valid:
                raise ConnectionClosedError(
                    "Connection closed while waiting for send window"
                )
            if not window_free:
                reason = (
                    f"Send window full (k={self.k}); no acknowledgment within "
                    f"t1={self.t1}s"
                )
                # Same fatal outcome as check_timers() detecting this - fail
                # the connection here too instead of leaving it looking
                # "valid" while the peer has stopped acknowledging.
                self._fail(reason)
                raise IEC104ProtocolError(reason)

            send_seq = self.__send_seq
            recv_seq = self.__recv_seq
            if self.__oldest_unacked_time is None:
                self.__oldest_unacked_time = time.monotonic()
            self.__send_seq = (send_seq + 1) % SEQ_MODULUS
            # An I-format frame's N(R) piggy-backs an acknowledgment of
            # every peer frame received so far.
            self.__unacked_recv = 0
            self.__last_recv_ack_time = None

        self._send_apci(
            APCI.i_format(send_seq=send_seq, recv_seq=recv_seq, asdu=octets)
        )

    @override
    def recv_data(self) -> bytes:
        """
        Block until the next I-format ASDU payload is available.

        :raises ConnectionClosedError: If the connection closes/fails while waiting.
        :return: The raw encoded ASDU bytes.
        :rtype: bytes
        """
        return self.recv_data_timeout(None)

    def recv_data_timeout(self, timeout: float | None) -> bytes:
        """
        As :meth:`recv_data`, but with an explicit timeout.

        :param timeout: Maximum seconds to wait, or ``None`` to block forever.
        :type timeout: float | None
        :raises TimeoutError: If no ASDU arrives within ``timeout`` seconds.
        :raises ConnectionClosedError: If the connection closes/fails while waiting.
        :return: The raw encoded ASDU bytes.
        :rtype: bytes
        """
        try:
            item = self.__in_queue.get(timeout=timeout)
        except Empty as e:
            raise TimeoutError("Timed out waiting for an ASDU") from e

        if item is None:
            raise ConnectionClosedError(self.__fail_reason or "Connection closed")
        return item

    # -- ergonomic ASDU-typed wrappers -------------------------------------- #

    def send_asdu(self, asdu: ASDU) -> None:
        """Encode and send a complete :class:`~icspacket.proto.iec104.asdu.ASDU`."""
        self.send_data(asdu.to_bytes())

    def recv_asdu(self, timeout: float | None = None) -> ASDU:
        """
        Receive and decode the next :class:`~icspacket.proto.iec104.asdu.ASDU`.

        :param timeout: Maximum seconds to wait, or ``None`` to block forever.
        :type timeout: float | None
        """
        return ASDU.from_bytes(self.recv_data_timeout(timeout))

    # -- properties ---------------------------------------------------------- #

    @property
    def send_sequence(self) -> int:
        """Current ``V(S)`` send sequence number."""
        return self.__send_seq

    @property
    def recv_sequence(self) -> int:
        """Current ``V(R)`` receive sequence number."""
        return self.__recv_seq

    # -- APCI dispatch (invoked from the background reader thread) -------- #

    def handle_apci(self, apci: APCI) -> None:
        """
        Dispatch a received APCI frame to the appropriate handler.

        Called by :class:`_Reader`; not normally called directly.

        :raises IEC104ProtocolError: If an I-format frame's ``N(S)`` is out
            of sequence.
        """
        self.__last_activity_time = time.monotonic()
        fmt = apci.format
        if fmt == APCIFormat.I_FORMAT:
            self._handle_i_format(apci)
        elif fmt == APCIFormat.S_FORMAT:
            self._handle_ack(apci.control.recv_seq)
        else:
            self._handle_u_format(apci)

    def _handle_i_format(self, apci: APCI) -> None:
        control = apci.control
        with self.__cond:
            expected = self.__recv_seq
            if control.send_seq != expected:
                raise IEC104ProtocolError(
                    f"Unexpected N(S): expected {expected}, got {control.send_seq}"
                )

            self.__recv_seq = (control.send_seq + 1) % SEQ_MODULUS
            self.__unacked_recv += 1
            if self.__last_recv_ack_time is None:
                self.__last_recv_ack_time = time.monotonic()
            unacked_recv = self.__unacked_recv

        self._handle_ack(control.recv_seq)
        self.__in_queue.put(apci.asdu)

        if unacked_recv >= self.w:
            self._send_ack()

    def _handle_ack(self, recv_seq: int) -> None:
        with self.__cond:
            self.__ack_send_seq = recv_seq
            self.__oldest_unacked_time = (
                None if self.__ack_send_seq == self.__send_seq else time.monotonic()
            )
            self.__cond.notify_all()

    def _send_ack(self) -> None:
        with self.__cond:
            recv_seq = self.__recv_seq
            self.__unacked_recv = 0
            self.__last_recv_ack_time = None
        self._send_apci(APCI.s_format(recv_seq))

    def _handle_u_format(self, apci: APCI) -> None:
        function = apci.control.function
        if function == UFormatFunction.STARTDT_CON:
            logger.log(TRACE, "[IEC104] Received redundant STARTDT confirmation")
        elif function == UFormatFunction.STOPDT_CON:
            self.__stopdt_confirmed.set()
        elif function == UFormatFunction.TESTFR_ACT:
            self._send_apci(APCI.testfr_con())
        elif function == UFormatFunction.TESTFR_CON:
            self.__testfr_pending_since = None
        else:
            logger.warning(
                "[IEC104] Unexpected U-format function received: %r", function
            )

    # -- timers (invoked from the background reader thread) ---------------- #

    def check_timers(self) -> None:
        """
        Check the ``t1``/``t2``/``t3`` deadlines, sending an S-format
        acknowledgment or ``TESTFR act`` as needed.

        Called periodically by :class:`_Reader`; not normally called
        directly.

        :raises IEC104ProtocolError: If a confirmation (I-format ack or
            ``TESTFR``) fails to arrive before :attr:`t1` elapses.
        """
        now = time.monotonic()
        with self.__cond:
            oldest_unacked = self.__oldest_unacked_time
            last_recv_ack = self.__last_recv_ack_time

        if oldest_unacked is not None and (now - oldest_unacked) > self.t1:
            raise IEC104ProtocolError(
                f"No acknowledgment received within t1={self.t1}s"
            )
        if (
            self.__testfr_pending_since is not None
            and (now - self.__testfr_pending_since) > self.t1
        ):
            raise IEC104ProtocolError(
                f"No TESTFR confirmation received within t1={self.t1}s"
            )

        if last_recv_ack is not None and (now - last_recv_ack) > self.t2:
            self._send_ack()

        if (
            now - self.__last_activity_time
        ) > self.t3 and self.__testfr_pending_since is None:
            self.__testfr_pending_since = now
            self._send_apci(APCI.testfr_act())
