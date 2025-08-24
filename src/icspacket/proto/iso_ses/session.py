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
from typing_extensions import override

from caterpillar.exception import StructException
from icspacket.core.connection import (
    connection,
    ConnectionError,
    ConnectionStateError,
)
from icspacket.proto.iso_ses.tsdu import TSDU
from icspacket.proto.iso_ses.spdu import PGI_Code, SPDU_Codes
from icspacket.proto.iso_ses.values import (
    PV_SessionRequirements,
)
from icspacket.proto.iso_ses.util import (
    build_connect_spdu,
    build_data_tsdu,
    build_finish_spdu,
)
from icspacket.proto.cotp.connection import COTP_Connection


class SessionDataError(ConnectionError):
    """
    Raised when session data exchange fails or unexpected SPDU content is
    received.
    """


class SessionRejectedError(ConnectionError):
    """
    Raised when a session connection request is explicitly rejected by the peer.
    """


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

    calling_ses_sel: bytes = bytes.fromhex("0000")
    called_ses_sel: bytes = bytes.fromhex("0000")
    session_req: PV_SessionRequirements = field(default_factory=PV_SessionRequirements)
    version: int = 2
    extended: bool = False


class ISO_Session(connection):
    """
    Implements the Connection-oriented Session Protocol (COSP) (ITU X.225 / ISO
    8327-1) endpoint on top of COTP.

    Provides session connection establishment, data transfer, and orderly
    release services using SPDUs (Session Protocol Data Units). This class
    ensures proper sequencing and validation of SPDUs as per ISO Session
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
        self._connected = transport.is_connected()
        self._valid = False

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
        self.transport.send_data(self._build_tsdu(tsdu))

    @override
    def recv_data(self) -> bytes:
        """
        Receive user data from the session.

        :return: Extracted user data payload.
        :rtype: bytes
        :raises SessionDataError: If the expected SPDU sequence is not found.
        """
        tsdu = self.recv_tsdu()
        # data transfer response should only store GIVE_TOKENS and DATA_TRANSFER
        if tsdu.spdus[0].code != SPDU_Codes.GIVE_TOKENS_SPDU:
            raise SessionDataError(
                f"Expected a TSDU with GIVE_TOKENS as first SPDU, got {tsdu.spdus[0].name}"
            )

        # NOTE - we just use the user information even if the received TSDU does
        # not specify them
        return tsdu.spdus[1].user_information

    def recv_tsdu(self) -> TSDU:
        """
        Receive and parse a TSDU from the transport connection.

        :return: Parsed TSDU object.
        :rtype: TSDU
        """
        self._assert_connected()
        data = self.transport.recv_data()
        return TSDU.from_octets(data)

    @override
    def close(self) -> None:
        """
        Close the session and underlying transport connection immediately.
        """
        self._connected = False
        self._valid = False
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
        if not self.is_connected() or not self.is_valid():
            return

        tsdu = TSDU()
        spdu = build_finish_spdu(user_data=pres_octets)
        tsdu.spdus.append(spdu)

        self.send_tsdu(tsdu)
        if graceful:
            tsdu = self.recv_tsdu()
            if (
                len(tsdu.spdus) == 1
                and tsdu.spdus[0].code != SPDU_Codes.DISCONNECT_SPDU
            ):
                raise SessionDataError(
                    "Could not close session gracefully, expected DISCONNECT_SPDU"
                    + f" but got {tsdu.spdus[0].name} instead"
                )

            user_data = tsdu.spdus[1].parameter_by_id(PGI_Code.USER_DATA)
            if user_data:
                return user_data.value

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
        tsdu = TSDU()
        spdu = build_connect_spdu(
            extended=self.settings.extended,
            version2=self.settings.version != 1,
            requirements=self.settings.session_req,
            called_ses_sel=self.settings.called_ses_sel,
            calling_ses_sel=self.settings.calling_ses_sel,
            user_data=pres_octets,
        )
        tsdu.spdus.append(spdu)
        self.send_tsdu(tsdu)

        tsdu = self.recv_tsdu()
        if len(tsdu.spdus) != 1:
            raise SessionDataError(
                f"Expected a single SPDU in TSDU, got {len(tsdu.spdus)} instead"
            )

        spdu = tsdu.spdus[0]
        if spdu.code != SPDU_Codes.ACCEPT_SPDU:
            raise SessionRejectedError(
                f"Target did not accept session request (SPDU {spdu.name})"
            )

        self._valid = True
        parameter = spdu.parameter_by_id(PGI_Code.USER_DATA)
        return b"" if not parameter else parameter.value

    def _build_tsdu(self, tsdu: TSDU) -> bytes:
        """Encode a TSDU into raw octets for transmission.

        :param tsdu: TSDU to encode.
        :type tsdu: TSDU
        :return: Encoded TSDU octet stream.
        :rtype: bytes
        :raises ValueError: If encoding fails due to invalid parameter values.
        """
        try:
            return tsdu.build()
        except StructException as e:
            raise ValueError(
                "Could not build TSDU: maybe wrong parameter value?"
            ) from e
