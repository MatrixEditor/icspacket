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
IEC104_Master - client API layered over :class:`~icspacket.proto.iec104.connection.IEC104_Connection`.

Cause Of Transmission conventions:

- General/counter interrogation and every command (``C_SC_NA_1`` etc.) are
  sent with :data:`~icspacket.proto.iec104.const.CauseOfTransmission.ACTIVATION`
  and confirmed with ``ACTIVATION_CON``; interrogation additionally streams
  monitor data and finishes with ``ACTIVATION_TERMINATION``.
- The read command (``C_RD_NA_1``) is the one exception: both the request
  and its reply use :data:`~icspacket.proto.iec104.const.CauseOfTransmission.REQUEST`
  instead.

Unsolicited/spontaneous monitor-direction ASDUs (``COT=SPONTANEOUS``) can
arrive at any time, including interleaved with a pending request's replies.
Rather than silently dropping them, blocking methods forward any
non-matching ASDU seen while waiting to the optional ``on_unsolicited``
callback (or log it at :data:`~icspacket.core.logger.TRACE` level if unset).
When no request is pending, simply iterate a :class:`IEC104_Master` instance
(``for asdu in master: ...``) to consume the incoming ASDU stream directly.
"""
import datetime
import logging
import time
from collections.abc import Callable, Iterator

from typing_extensions import Self

from icspacket.core.connection import ConnectionClosedError
from icspacket.core.logger import TRACE
from icspacket.proto.iec104.asdu import ASDU, ASDU_Header
from icspacket.proto.iec104.connection import IEC104_Connection, IEC104ProtocolError
from icspacket.proto.iec104.const import (
    QOC,
    QOI,
    QRP,
    CauseOfTransmission,
    DoublePointValue,
    QCC_Freeze,
    QCC_Request,
    StepCommandValue,
    TypeID,
)
from icspacket.proto.iec104.objects.coding import InformationObject
from icspacket.proto.iec104.objects.elements import DCO, QOS, RCO, SCO, CP56Time2a
from icspacket.proto.iec104.objects.information import (
    ClockSynchronizationCommand,
    CounterInterrogationCommand,
    DoubleCommand,
    InterrogationCommand,
    ReadCommand,
    ResetProcessCommand,
    SetpointCommandNormalized,
    SetpointCommandScaled,
    SetpointCommandShort,
    SingleCommand,
    StepCommand,
    TestCommand,
)

__all__ = ["IEC104_Master"]

logger = logging.getLogger(__name__)


class IEC104_Master:
    """
    Ergonomic IEC 60870-5-104 client (controlling station) API.

    :param connection: Existing :class:`~icspacket.proto.iec104.connection.IEC104_Connection`
        to use; a new one (with default timers) is created if omitted.
    :type connection: IEC104_Connection | None
    :param on_unsolicited: Optional callback invoked with any ASDU observed
        while a blocking method is waiting for its own reply, but which does
        not match that reply (e.g. a spontaneous data change interleaved
        with a pending general interrogation). If omitted, such ASDUs are
        only logged at :data:`~icspacket.core.logger.TRACE` level.
    :type on_unsolicited: Callable[[~icspacket.proto.iec104.asdu.ASDU], None] | None
    """

    def __init__(
        self,
        connection: IEC104_Connection | None = None,
        *,
        on_unsolicited: Callable[[ASDU], None] | None = None,
    ) -> None:
        self.connection: IEC104_Connection = connection or IEC104_Connection()
        self.on_unsolicited: Callable[[ASDU], None] | None = on_unsolicited

    # -- connection lifecycle passthroughs --------------------------------- #

    def connect(self, address: tuple[str, int]) -> None:
        """Connect and perform the ``STARTDT`` handshake; see
        :meth:`~icspacket.proto.iec104.connection.IEC104_Connection.connect`."""
        self.connection.connect(address)

    def close(self) -> None:
        """Perform the ``STOPDT`` handshake and close the connection; see
        :meth:`~icspacket.proto.iec104.connection.IEC104_Connection.close`."""
        self.connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    # -- unsolicited/spontaneous ASDU stream -------------------------------- #

    def __iter__(self) -> Iterator[ASDU]:
        return self

    def __next__(self) -> ASDU:
        try:
            return self.connection.recv_asdu()
        except ConnectionClosedError:
            raise StopIteration from None

    def read_next(self, timeout: float | None = None) -> ASDU:
        """
        Return the next incoming ASDU, whatever it is.

        Only meaningful when no other blocking method (interrogation,
        command, ...) is concurrently waiting on the same connection - both
        ultimately consume the same single incoming-ASDU queue.

        :param timeout: Maximum seconds to wait, or ``None`` to block forever.
        :type timeout: float | None
        :raises TimeoutError: If no ASDU arrives within ``timeout`` seconds.
        :raises ConnectionClosedError: If the connection closes while waiting.
        """
        return self.connection.recv_asdu(timeout)

    # -- internal helpers ---------------------------------------------------- #

    def _send(
        self,
        type_id: TypeID,
        common_address: int,
        element: object,
        *,
        ioa: int = 0,
        cot: CauseOfTransmission = CauseOfTransmission.ACTIVATION,
    ) -> None:
        """Build a single-object ASDU and send it as I-format data."""
        asdu = ASDU(header=ASDU_Header(type_id=type_id, common_address=common_address))
        asdu.header.cot.cause = int(cot)
        octets = asdu.build([InformationObject(ioa=ioa, element=element)])
        self.connection.send_data(octets)

    def _await_match(
        self, timeout: float | None, predicate: Callable[[ASDU], bool]
    ) -> ASDU:
        """
        Block until an ASDU satisfying ``predicate`` is received.

        Any ASDU seen that does not satisfy ``predicate`` is forwarded to
        ``on_unsolicited`` (or logged and discarded) rather than lost.

        :raises TimeoutError: If no matching ASDU arrives within ``timeout``.
        :raises ConnectionClosedError: If the connection closes while waiting.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            remaining = None
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Timed out waiting for a matching ASDU reply")

            asdu = self.connection.recv_asdu(timeout=remaining)
            if predicate(asdu):
                return asdu

            if self.on_unsolicited is not None:
                self.on_unsolicited(asdu)
            else:
                logger.log(
                    TRACE,
                    "[IEC104] Discarding unrelated %s ASDU while awaiting a reply",
                    asdu.header.type_id.name,
                )

    @staticmethod
    def _raise_if_negative(asdu: ASDU, operation: str) -> ASDU:
        if asdu.header.cot.negative:
            raise IEC104ProtocolError(
                f"{operation} was negatively confirmed by the outstation "
                + f"(common address {asdu.header.common_address})"
            )
        return asdu

    def _activation_confirm(
        self, type_id: TypeID, operation: str, timeout: float | None
    ) -> ASDU:
        """Wait for ``type_id``'s ``ACTIVATION_CON``, raising on a negative
        confirmation."""
        confirm_cot = int(CauseOfTransmission.ACTIVATION_CON)
        asdu = self._await_match(
            timeout,
            lambda a: a.header.type_id == type_id and a.header.cot.cause == confirm_cot,
        )
        return self._raise_if_negative(asdu, operation)

    def _activation_sequence(
        self, type_id: TypeID, operation: str, timeout: float | None
    ) -> Iterator[ASDU]:
        """
        Wait for ``type_id``'s ``ACTIVATION_CON``, then yield every
        subsequently received ASDU (monitor data - and any interleaved
        spontaneous data - included) up to and including the matching
        ``ACTIVATION_TERMINATION``.

        Used by :meth:`general_interrogation`/:meth:`counter_interrogation`,
        the only two request types in this API that have a data-streaming
        phase between confirmation and termination.
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        def _remaining() -> float | None:
            return None if deadline is None else max(0.0, deadline - time.monotonic())

        yield self._activation_confirm(type_id, operation, _remaining())

        terminate_cot = int(CauseOfTransmission.ACTIVATION_TERMINATION)
        while True:
            asdu = self.connection.recv_asdu(timeout=_remaining())
            yield asdu
            if asdu.header.type_id == type_id and asdu.header.cot.cause == terminate_cot:
                return

    # -- system commands ---------------------------------------------------- #

    def general_interrogation(
        self,
        common_address: int,
        qoi: QOI = QOI.STATION,
        timeout: float | None = None,
    ) -> Iterator[ASDU]:
        """
        Issue a general (or group) interrogation and stream back the reply.

        :param common_address: Target station address.
        :type common_address: int
        :param qoi: Interrogation scope (default: whole station).
        :type qoi: ~icspacket.proto.iec104.const.QOI
        :param timeout: Maximum seconds to wait for each successive reply
            ASDU, or ``None`` to block forever.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If a reply does not arrive in time.
        :return: An iterator yielding the ``ACTIVATION_CON`` first, then
            every monitor-direction ASDU as it arrives, ending with (and
            including) the ``ACTIVATION_TERMINATION`` ASDU.
        :rtype: Iterator[~icspacket.proto.iec104.asdu.ASDU]
        """
        self._send(
            TypeID.C_IC_NA_1,
            common_address,
            InterrogationCommand(qualifier=qoi),
        )
        return self._activation_sequence(
            TypeID.C_IC_NA_1, "General interrogation", timeout
        )

    def counter_interrogation(
        self,
        common_address: int,
        request: QCC_Request = QCC_Request.GENERAL,
        freeze: QCC_Freeze = QCC_Freeze.READ,
        timeout: float | None = None,
    ) -> Iterator[ASDU]:
        """
        Issue a counter interrogation and stream back the reply.

        :param common_address: Target station address.
        :type common_address: int
        :param request: Counter group to request (default: all groups).
        :type request: ~icspacket.proto.iec104.const.QCC_Request
        :param freeze: Freeze/reset behavior (default: read without freezing).
        :type freeze: ~icspacket.proto.iec104.const.QCC_Freeze
        :param timeout: Maximum seconds to wait for each successive reply
            ASDU, or ``None`` to block forever.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If a reply does not arrive in time.
        :return: An iterator yielding the ``ACTIVATION_CON`` first, then
            every counter-value ASDU as it arrives, ending with (and
            including) the ``ACTIVATION_TERMINATION`` ASDU.
        :rtype: Iterator[~icspacket.proto.iec104.asdu.ASDU]
        """
        self._send(
            TypeID.C_CI_NA_1,
            common_address,
            CounterInterrogationCommand(qualifier=int(freeze) | int(request)),
        )
        return self._activation_sequence(
            TypeID.C_CI_NA_1, "Counter interrogation", timeout
        )

    def clock_sync(
        self,
        common_address: int,
        when: datetime.datetime | None = None,
        timeout: float | None = None,
    ) -> ASDU:
        """
        Synchronize the outstation's clock.

        Unlike interrogation, a clock sync only ever produces a single
        ``ACTIVATION_CON`` reply - there is no termination/streaming phase.

        :param common_address: Target station address.
        :type common_address: int
        :param when: Timestamp to send; defaults to the current local time.
        :type when: datetime.datetime | None
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU (its decoded object carries the
            timestamp actually applied, per some outstations' behavior).
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        when = when or datetime.datetime.now()
        self._send(
            TypeID.C_CS_NA_1,
            common_address,
            ClockSynchronizationCommand(timestamp=CP56Time2a.from_datetime(when)),
        )
        return self._activation_confirm(TypeID.C_CS_NA_1, "Clock synchronization", timeout)

    def test_command(
        self, common_address: int, timeout: float | None = None
    ) -> ASDU:
        """
        Send a test command (exercises the link without side effects).

        :param common_address: Target station address.
        :type common_address: int
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed,
            or the confirmation's fixed test pattern does not match.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU.
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(TypeID.C_TS_NA_1, common_address, TestCommand())
        asdu = self._activation_confirm(TypeID.C_TS_NA_1, "Test command", timeout)
        fbp = asdu.decode_objects()[0].element.fbp
        if fbp != 0x55AA:
            raise IEC104ProtocolError(
                "Test command confirmation carried an unexpected fixed test "
                + f"bit pattern: {fbp:#06x} (expected 0x55aa)"
            )
        return asdu

    def reset_process(
        self,
        common_address: int,
        qualifier: QRP = QRP.GENERAL_RESET,
        timeout: float | None = None,
    ) -> ASDU:
        """
        Send a reset process command.

        :param common_address: Target station address.
        :type common_address: int
        :param qualifier: Reset scope (default: reset the entire process).
        :type qualifier: ~icspacket.proto.iec104.const.QRP
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU.
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(
            TypeID.C_RP_NA_1, common_address, ResetProcessCommand(qualifier=qualifier)
        )
        return self._activation_confirm(TypeID.C_RP_NA_1, "Reset process", timeout)

    def read(
        self, common_address: int, ioa: int, timeout: float | None = None
    ) -> ASDU:
        """
        Poll the current value of a single information object.

        :param common_address: Target station address.
        :type common_address: int
        :param ioa: Information Object Address to read.
        :type ioa: int
        :param timeout: Maximum seconds to wait for the reply.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the read is negatively confirmed
            (e.g. unknown IOA).
        :raises TimeoutError: If the reply does not arrive in time.
        :return: The reply ASDU (its type depends on the point being read;
            decode with :meth:`~icspacket.proto.iec104.asdu.ASDU.decode_objects`).
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(
            TypeID.C_RD_NA_1,
            common_address,
            ReadCommand(),
            ioa=ioa,
            cot=CauseOfTransmission.REQUEST,
        )
        request_cot = int(CauseOfTransmission.REQUEST)
        asdu = self._await_match(
            timeout,
            lambda a: a.header.common_address == common_address
            and a.header.cot.cause == request_cot
            and any(o.ioa == ioa for o in a.decode_objects()),
        )
        return self._raise_if_negative(asdu, "Read command")

    # -- control-direction commands ------------------------------------------ #

    def single_command(
        self,
        common_address: int,
        ioa: int,
        value: bool,
        *,
        select: bool = False,
        qu: QOC = QOC.NO_ADDITIONAL_DEFINITION,
        timeout: float | None = None,
    ) -> ASDU:
        """
        Send a single command (on/off).

        Only performs one step of the select-before-operate sequence; call
        twice (``select=True`` then ``select=False``) to select then execute.

        :param common_address: Target station address.
        :type common_address: int
        :param ioa: Information Object Address to command.
        :type ioa: int
        :param value: Commanded state.
        :type value: bool
        :param select: ``True`` to select rather than directly execute.
        :type select: bool
        :param qu: Qualifier of command (pulse duration behavior).
        :type qu: ~icspacket.proto.iec104.const.QOC
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU.
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(
            TypeID.C_SC_NA_1,
            common_address,
            SingleCommand(command=SCO(se=select, qu=qu, scs=value)),
            ioa=ioa,
        )
        return self._activation_confirm(TypeID.C_SC_NA_1, "Single command", timeout)

    def double_command(
        self,
        common_address: int,
        ioa: int,
        value: DoublePointValue,
        *,
        select: bool = False,
        qu: QOC = QOC.NO_ADDITIONAL_DEFINITION,
        timeout: float | None = None,
    ) -> ASDU:
        """
        Send a double command (on/off/intermediate).

        Only performs one step of the select-before-operate sequence; call
        twice (``select=True`` then ``select=False``) to select then execute.

        :param common_address: Target station address.
        :type common_address: int
        :param ioa: Information Object Address to command.
        :type ioa: int
        :param value: Commanded state.
        :type value: ~icspacket.proto.iec104.const.DoublePointValue
        :param select: ``True`` to select rather than directly execute.
        :type select: bool
        :param qu: Qualifier of command (pulse duration behavior).
        :type qu: ~icspacket.proto.iec104.const.QOC
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU.
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(
            TypeID.C_DC_NA_1,
            common_address,
            DoubleCommand(command=DCO(se=select, qu=qu, dcs=value)),
            ioa=ioa,
        )
        return self._activation_confirm(TypeID.C_DC_NA_1, "Double command", timeout)

    def step_command(
        self,
        common_address: int,
        ioa: int,
        value: StepCommandValue,
        *,
        select: bool = False,
        qu: QOC = QOC.NO_ADDITIONAL_DEFINITION,
        timeout: float | None = None,
    ) -> ASDU:
        """
        Send a regulating step command (step up/down).

        Only performs one step of the select-before-operate sequence; call
        twice (``select=True`` then ``select=False``) to select then execute.

        :param common_address: Target station address.
        :type common_address: int
        :param ioa: Information Object Address to command.
        :type ioa: int
        :param value: Commanded step direction.
        :type value: ~icspacket.proto.iec104.const.StepCommandValue
        :param select: ``True`` to select rather than directly execute.
        :type select: bool
        :param qu: Qualifier of command (pulse duration behavior).
        :type qu: ~icspacket.proto.iec104.const.QOC
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU.
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(
            TypeID.C_RC_NA_1,
            common_address,
            StepCommand(command=RCO(se=select, qu=qu, rcs=value)),
            ioa=ioa,
        )
        return self._activation_confirm(TypeID.C_RC_NA_1, "Regulating step command", timeout)

    def setpoint_command_normalized(
        self,
        common_address: int,
        ioa: int,
        value: int,
        *,
        select: bool = False,
        ql: int = 0,
        timeout: float | None = None,
    ) -> ASDU:
        """
        Send a set-point command with a normalized (fixed-point) value.

        :param common_address: Target station address.
        :type common_address: int
        :param ioa: Information Object Address to command.
        :type ioa: int
        :param value: Normalized value, see
            :class:`~icspacket.proto.iec104.objects.elements.NVA`.
        :type value: int
        :param select: ``True`` to select rather than directly execute.
        :type select: bool
        :param ql: Qualifier value (``0``: default).
        :type ql: int
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU.
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(
            TypeID.C_SE_NA_1,
            common_address,
            SetpointCommandNormalized(value=value, qualifier=QOS(se=select, ql=ql)),
            ioa=ioa,
        )
        return self._activation_confirm(
            TypeID.C_SE_NA_1, "Set-point command (normalized)", timeout
        )

    def setpoint_command_scaled(
        self,
        common_address: int,
        ioa: int,
        value: int,
        *,
        select: bool = False,
        ql: int = 0,
        timeout: float | None = None,
    ) -> ASDU:
        """
        Send a set-point command with a scaled (16-bit signed integer) value.

        :param common_address: Target station address.
        :type common_address: int
        :param ioa: Information Object Address to command.
        :type ioa: int
        :param value: Scaled value, see
            :class:`~icspacket.proto.iec104.objects.elements.SVA`.
        :type value: int
        :param select: ``True`` to select rather than directly execute.
        :type select: bool
        :param ql: Qualifier value (``0``: default).
        :type ql: int
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU.
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(
            TypeID.C_SE_NB_1,
            common_address,
            SetpointCommandScaled(value=value, qualifier=QOS(se=select, ql=ql)),
            ioa=ioa,
        )
        return self._activation_confirm(
            TypeID.C_SE_NB_1, "Set-point command (scaled)", timeout
        )

    def setpoint_command_short(
        self,
        common_address: int,
        ioa: int,
        value: float,
        *,
        select: bool = False,
        ql: int = 0,
        timeout: float | None = None,
    ) -> ASDU:
        """
        Send a set-point command with a short floating point value.

        :param common_address: Target station address.
        :type common_address: int
        :param ioa: Information Object Address to command.
        :type ioa: int
        :param value: IEEE 754 single-precision value, see
            :class:`~icspacket.proto.iec104.objects.elements.R32`.
        :type value: float
        :param select: ``True`` to select rather than directly execute.
        :type select: bool
        :param ql: Qualifier value (``0``: default).
        :type ql: int
        :param timeout: Maximum seconds to wait for the confirmation.
        :type timeout: float | None
        :raises IEC104ProtocolError: If the activation is negatively confirmed.
        :raises TimeoutError: If the confirmation does not arrive in time.
        :return: The ``ACTIVATION_CON`` ASDU.
        :rtype: ~icspacket.proto.iec104.asdu.ASDU
        """
        self._send(
            TypeID.C_SE_NC_1,
            common_address,
            SetpointCommandShort(value=value, qualifier=QOS(se=select, ql=ql)),
            ioa=ioa,
        )
        return self._activation_confirm(
            TypeID.C_SE_NC_1, "Set-point command (short)", timeout
        )
