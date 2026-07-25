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
from dataclasses import dataclass, field
from typing import TypeVar
from typing_extensions import override

from caterpillar.exception import StructException
from icspacket.core.connection import (
    connection,
    ConnectionError,
    ConnectionClosedError,
    ConnectionStateError,
)
from icspacket.proto.iso_ses.tsdu import TSDU
from icspacket.proto.iso_ses.spdu import PGI_Code, SPDU, SPDU_Category, SPDU_Codes
from icspacket.proto.iso_ses.values import (
    PI_Code,
    PV_ProtocolOptions,
    PV_SessionRequirements,
    PV_TransportDisconnect,
    PV_VersionNumber,
)
from icspacket.proto.iso_ses.util import (
    build_abort_spdu,
    build_connect_spdu,
    build_data_tsdu,
    build_finish_spdu,
)
from icspacket.proto.cotp.connection import COTP_Connection


T = TypeVar("T")


class SessionDataError(ConnectionError):
    """
    Raised when session data exchange fails or unexpected SPDU content is
    received.
    """


class SessionRejectedError(ConnectionError):
    """
    Raised when a session connection request is explicitly rejected by the peer.
    """

    def __init__(
        self,
        message: str = "Session rejected by peer",
        *,
        reason_code: int | None = None,
        user_data: bytes | None = None,
    ) -> None:
        super().__init__(message)
        self.reason_code: int | None = reason_code
        self.user_data: bytes | None = user_data


class SessionAbortError(ConnectionError):
    """
    Raised when an abnormal release SPDU is received.
    """

    def __init__(self, user_data: bytes | None = None) -> None:
        super().__init__("Session aborted by peer")
        self.user_data: bytes | None = user_data


@dataclass(frozen=True)
class SessionEvent:
    """Parsed session data or release event."""

    kind: str
    user_data: bytes | None = None
    accepted: bool | None = None


@dataclass(frozen=True)
class SessionReleaseResult:
    """
    Result of an orderly release attempt.
    """

    accepted: bool
    user_data: bytes | None = None
    collision: bool = False


@dataclass(frozen=True)
class ISO_SessionNegotiation:
    """Negotiated X.225 session values for the established connection."""

    version: int
    requirements: PV_SessionRequirements
    extended: bool
    send_tsdu_max: int | None = None
    receive_tsdu_max: int | None = None


@dataclass
class ISO_SessionSettings:
    """Encapsulates (X.225 / ISO 8327-1) negotiation settings.

    :param calling_ses_sel: Calling session selector.
    :type calling_ses_sel: bytes
    :param called_ses_sel: Called session selector.
    :type called_ses_sel: bytes
    :param session_req: Session requirements parameter vector.
    :type session_req: PV_SessionRequirements
    :param version: Session protocol version (default 2).
    :type version: int
    :param extended: Whether extended SPDU formats are enabled.
    :type extended: bool
    """

    calling_ses_sel: bytes = bytes.fromhex("0001")
    called_ses_sel: bytes = bytes.fromhex("0001")
    session_req: PV_SessionRequirements = field(
        default_factory=PV_SessionRequirements.default
    )
    version: int = 2
    extended: bool = False

    def __post_init__(self) -> None:
        if self.version not in (1, 2):
            raise ValueError("Session protocol version must be 1 or 2")


class ISO_Session(connection):
    """
    Implements the Connection-oriented Session Protocol (COSP) (ITU X.225 / ISO
    8327-1) endpoint on top of COTP.

    Provides session connection establishment, data transfer, and orderly
    release services using SPDUs (Session Protocol Data Units). This class
    ensures proper sequencing and validation of SPDUs according to ISO Session
    protocol semantics.

    :param transport: Underlying COTP transport connection.
    :type transport: COTP_Connection
    :param settings: Session negotiation settings.
    :type settings: ISO_SessionSettings | None
    """

    settings: ISO_SessionSettings
    """Currently applied session settings"""

    def __init__(
        self,
        transport: COTP_Connection,
        settings: ISO_SessionSettings | None = None,
    ):
        super().__init__()
        self.__transport = transport
        self._connected: bool = transport.is_connected()
        self._valid: bool = False
        self.negotiated: ISO_SessionNegotiation | None = None

        # publicly available settings
        self.settings = settings or ISO_SessionSettings()

    @property
    def transport(self) -> COTP_Connection:
        """Associated transport connection."""
        return self.__transport

    @override
    def send_data(self, octets: bytes, /) -> None:
        """
        Send user data wrapped in a session TSDU.

        .. note::
            The session must already be initialized with an ACCEPT SPDU.

        :param octets: User data payload.
        :type octets: bytes
        :raises ConnectionStateError: If the session is not initialized.
        """
        self._assert_connected()
        if not self.is_valid():
            raise ConnectionStateError(
                "Session must be initialized before sending data"
            )

        tsdu = build_data_tsdu(octets)
        self.send_tsdu(tsdu)

    def send_tsdu(self, tsdu: TSDU, /) -> None:
        """
        Send a fully constructed TSDU over the transport connection.

        :param tsdu: Transport Service Data Unit.
        :type tsdu: TSDU
        """
        self._assert_connected()
        try:
            encoded = tsdu.build()
        except StructException as e:
            raise ValueError(
                "Could not build TSDU: maybe wrong parameter value?"
            ) from e

        if (
            self.is_valid()
            and self.negotiated is not None
            and self.negotiated.send_tsdu_max is not None
            and len(encoded) > self.negotiated.send_tsdu_max
        ):
            raise SessionDataError("TSDU exceeds negotiated maximum size")

        self.transport.send_data(encoded)

    @override
    def recv_data(self) -> bytes:
        """
        Receive user data from the session.

        :return: Extracted user data payload.
        :rtype: bytes
        :raises SessionAbortError: If the peer aborts the session.
        :raises SessionDataError: If the expected SPDU sequence is not found.
        """
        event = self.recv_event()
        if event.kind != "data":
            raise SessionDataError(f"Expected session data, got {event.kind}")
        return event.user_data or b""

    def recv_event(self) -> SessionEvent:
        """
        Receive and classify the next session event.

        :return: Parsed session event.
        :rtype: SessionEvent
        :raises SessionAbortError: If the peer aborts the session.
        :raises SessionDataError: If the TSDU is empty or malformed.
        """
        tsdu = self.recv_tsdu()
        if not tsdu.spdus:
            raise SessionDataError("Received an empty TSDU")

        first = tsdu.spdus[0]
        if first.category == SPDU_Category.CATEGORY_0:
            if len(tsdu.spdus) != 2:
                raise SessionDataError(
                    "Expected basic GIVE_TOKENS + DATA_TRANSFER TSDU"
                )

            first, data_spdu = tsdu.spdus
            if first.code != SPDU_Codes.GIVE_TOKENS_SPDU:
                raise SessionDataError(f"Unexpected category 0 SPDU: {first.name}")

            if (
                data_spdu.category != SPDU_Category.CATEGORY_2
                or data_spdu.code != SPDU_Codes.DATA_TRANSFER_SPDU
            ):
                raise SessionDataError(
                    "Expected DATA_TRANSFER_SPDU after GIVE_TOKENS, got "
                    + f"{data_spdu.name}"
                )

            return SessionEvent(
                kind="data",
                user_data=data_spdu.user_information,
            )

        user_data = first.parameter_by_id(PGI_Code.USER_DATA)
        user_octets = None if user_data is None else user_data.value

        match first.code:
            case SPDU_Codes.FINISH_SPDU:
                return SessionEvent(
                    kind="release_request",
                    user_data=user_octets,
                )
            case SPDU_Codes.DISCONNECT_SPDU:
                return SessionEvent(
                    kind="release_response",
                    user_data=user_octets,
                    accepted=True,
                )
            case SPDU_Codes.NOT_FINISHED_SPDU:
                return SessionEvent(
                    kind="release_response",
                    user_data=user_octets,
                    accepted=False,
                )
            case SPDU_Codes.ABORT_SPDU:
                self._handle_abort_spdu(first)
                raise SessionAbortError(user_octets)
            case _:
                raise SessionDataError(f"Unexpected session SPDU: {first.name}")

    def recv_tsdu(self) -> TSDU:
        """
        Receive and parse a TSDU from the transport connection.

        :return: Parsed TSDU object.
        :rtype: TSDU
        """
        self._assert_connected()
        try:
            data = self.transport.recv_data()
            return TSDU.from_octets(data)
        except ConnectionClosedError as e:
            self._connected = False
            self._valid = False
            self.negotiated = None
            raise SessionAbortError() from e
        except (IndexError, ValueError, StructException) as e:
            self._valid = False
            self.negotiated = None
            raise SessionDataError("Malformed session TSDU received") from e

    @override
    def close(self) -> None:
        """
        Close the session and underlying transport connection immediately.
        """
        self._connected = False
        self._valid = False
        self.negotiated = None
        self.transport.close()

    def close_session(self, pres_octets: bytes, graceful: bool = False) -> bytes | None:
        """Attempt an orderly session release.

        This method does not close the connection if graceful is set **and**
        user data is returned by the peer.

        :param pres_octets: User data to include in FINISH SPDU.
        :type pres_octets: bytes
        :param graceful: Whether to expect and validate a DISCONNECT_SPDU.
        :type graceful: bool
        :return: Optional user data returned by peer during graceful release.
        :rtype: bytes | None
        :raises SessionDataError: If graceful close fails due to unexpected SPDU.
        """
        result = self.close_session_result(pres_octets, graceful)
        return None if result is None else result.user_data

    def close_session_result(
        self, pres_octets: bytes, graceful: bool = False
    ) -> SessionReleaseResult | None:
        """Attempt an orderly session release and return its result.

        :param pres_octets: User data to include in FINISH SPDU.
        :type pres_octets: bytes
        :param graceful: Whether to expect and validate a release response.
        :type graceful: bool
        :return: Release result, or ``None`` if the session was not open.
        :rtype: SessionReleaseResult | None
        :raises SessionAbortError: If the peer aborts during release.
        :raises SessionDataError: If graceful close receives an unexpected event.
        """
        if not self.is_connected() or not self.is_valid():
            return None

        self.send_tsdu(TSDU(build_finish_spdu(user_data=pres_octets)))
        if graceful:
            event = self.recv_event()
            if event.kind == "release_request":
                return SessionReleaseResult(
                    accepted=False,
                    user_data=event.user_data,
                    collision=True,
                )

            if event.kind != "release_response":
                raise SessionDataError(
                    "Could not close session gracefully, expected release response"
                    + f" but got {event.kind} instead"
                )

            if event.accepted:
                self.close()

            return SessionReleaseResult(
                accepted=bool(event.accepted),
                user_data=event.user_data,
            )

        self.close()
        return SessionReleaseResult(accepted=True)

    def abort_session(self, pres_octets: bytes | None = None) -> None:
        """Abort the session with an ABORT SPDU.

        :param pres_octets: Optional presentation-layer user data.
        :type pres_octets: bytes | None
        """
        if not self.is_connected() or not self.is_valid():
            return

        tsdu = TSDU(
            build_abort_spdu(
                user_data=pres_octets,
                release_transport=True,
                user_abort=pres_octets is not None,
            )
        )
        try:
            self.send_tsdu(tsdu)
        finally:
            self.close()

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """
        Connect the underlying transport if not already connected.

        :param address: Target address (host, port).
        :type address: tuple[str, int]
        """
        if not self.transport.is_connected():
            self.transport.connect(address)
            self._connected = True

    def init_session(
        self, pres_octets: bytes, address: tuple[str, int] | None = None
    ) -> bytes:
        """
        Initialize a session by sending CONNECT SPDU and awaiting ACCEPT SPDU.

        :param pres_octets: Presentation-layer user data to include.
        :type pres_octets: bytes
        :param address: Optional (host, port) if transport not yet connected.
        :type address: tuple[str, int] | None
        :return: User data returned by peer in ACCEPT SPDU.
        :rtype: bytes
        :raises ValueError: If address is required but not provided.
        :raises SessionDataError: If unexpected SPDU is received in response.
        :raises SessionRejectedError: If peer rejects the session.
        """
        if not self.is_connected():
            if address is None:
                raise ValueError("Must specify address if not connected")
            self.connect(address)

        self._assert_connected()
        self.send_tsdu(
            TSDU(
                build_connect_spdu(
                    extended=self.settings.extended,
                    version2=self.settings.version != 1,
                    requirements=self.settings.session_req,
                    called_ses_sel=self.settings.called_ses_sel,
                    calling_ses_sel=self.settings.calling_ses_sel,
                    user_data=pres_octets,
                )
            )
        )

        tsdu = self.recv_tsdu()
        if len(tsdu.spdus) != 1:
            raise SessionDataError(
                f"Expected a single SPDU in TSDU, got {len(tsdu.spdus)} instead"
            )

        spdu = tsdu.spdus[0]
        match spdu.code:
            case SPDU_Codes.ACCEPT_SPDU:
                self._handle_accept_spdu(spdu)
            case SPDU_Codes.REFUSE_SPDU:
                self._handle_refuse_spdu(spdu)
            case SPDU_Codes.ABORT_SPDU:
                self._handle_connect_abort_spdu(spdu)
            case _:
                raise SessionRejectedError(
                    f"Target did not accept session request (SPDU {spdu.name})"
                )

        parameter = spdu.parameter_by_id(PGI_Code.USER_DATA)
        return b"" if not parameter else parameter.value

    def _handle_accept_spdu(self, spdu: SPDU) -> None:
        try:
            selected_version = self._selected_version(spdu)
            accepted_requirements = self._accepted_requirements(spdu)
            # Some MMS stacks return 0x0000 here despite accepting the CONNECT.
            # Treat that as a responder echo of the valid client proposal.
            if accepted_requirements.is_empty:
                accepted_requirements = self.settings.session_req

            selected_requirements = self.settings.session_req.update(
                accepted_requirements
            )
            options = self._protocol_options(spdu)
            send_tsdu_max, receive_tsdu_max = self._tsdu_maximum_size(spdu)
        except (SessionDataError, ValueError) as e:
            self.close()
            raise SessionDataError(f"Invalid ACCEPT SPDU: {e}") from e

        self.negotiated = ISO_SessionNegotiation(
            version=selected_version,
            requirements=selected_requirements,
            extended=self.settings.extended and options.extended,
            send_tsdu_max=send_tsdu_max,
            receive_tsdu_max=receive_tsdu_max,
        )
        self._valid = True

    def _handle_refuse_spdu(self, spdu: SPDU) -> None:
        parameter = spdu.parameter_by_id(PI_Code.REASON_CODE)
        self.close()

        if parameter is None or not parameter.value:
            raise SessionRejectedError()

        if not isinstance(parameter.value, bytes):
            raise SessionDataError("REFUSE Reason Code parameter is malformed")

        reason_code = parameter.value[0]
        user_data = parameter.value[1:] or None
        raise SessionRejectedError(
            f"Session rejected by peer (reason {reason_code})",
            reason_code=reason_code,
            user_data=user_data,
        )

    def _handle_connect_abort_spdu(self, spdu: SPDU) -> None:
        parameter = spdu.parameter_by_id(PGI_Code.USER_DATA)
        self._handle_abort_spdu(spdu)
        raise SessionAbortError(None if parameter is None else parameter.value)

    def _handle_abort_spdu(self, spdu: SPDU) -> None:
        """Invalidate the session and release COTP only when the peer requests it."""

        parameter = spdu.parameter_by_id(PI_Code.TRANSPORT_DISCONNECT)
        self._valid = False
        self.negotiated = None
        if (
            parameter is not None
            and isinstance(parameter.value, PV_TransportDisconnect)
            and parameter.value.release_transport
        ):
            self.close()

    def _selected_version(self, spdu: SPDU) -> int:
        response = self._typed_parameter(
            spdu,
            PI_Code.VERSION_NUMBER,
            PV_VersionNumber,
        )
        if response is None:
            response = PV_VersionNumber(version1=True, version2=False)

        if self.settings.version == 2 and response.version2:
            return 2
        if self.settings.version == 1 and response.version1:
            return 1

        raise SessionDataError("ACCEPT selected no supported protocol version")

    def _accepted_requirements(self, spdu: SPDU) -> PV_SessionRequirements:
        requirements = self._typed_parameter(
            spdu,
            PI_Code.SESSION_REQUIREMENT,
            PV_SessionRequirements,
        )
        if requirements is not None:
            return requirements

        return PV_SessionRequirements(
            half_duplex=True,
            minor_sync=True,
            activity_management=True,
            capability_data_exchange=True,
            exceptions=True,
        )

    def _protocol_options(self, spdu: SPDU) -> PV_ProtocolOptions:
        options = self._typed_parameter(
            spdu,
            PI_Code.PROTOCOL_OPTIONS,
            PV_ProtocolOptions,
        )
        return PV_ProtocolOptions(extended=False) if options is None else options

    def _tsdu_maximum_size(self, spdu: SPDU) -> tuple[int | None, int | None]:
        maximum_size = self._typed_parameter(
            spdu,
            PI_Code.TSDU_MAXIMUM_SIZE,
            int,
        )
        if maximum_size is None:
            return None, None

        send_tsdu_max = maximum_size >> 16
        receive_tsdu_max = maximum_size & 0xFFFF
        return send_tsdu_max or None, receive_tsdu_max or None

    @staticmethod
    def _typed_parameter(
        spdu: SPDU,
        code: PI_Code,
        value_type: type[T],
    ) -> T | None:
        parameter = spdu.parameter_by_id(code)
        if parameter is None:
            return None
        if not isinstance(parameter.value, value_type):
            raise SessionDataError(f"ACCEPT {code.name} parameter is malformed")
        return parameter.value
