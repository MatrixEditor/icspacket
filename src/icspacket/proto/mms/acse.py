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

from abc import ABC, abstractmethod
from typing import Any
from typing_extensions import override

from icspacket.core.connection import (
    ConnectionClosedError,
    ConnectionNotEstablished,
    ConnectionStateError,
    connection,
)
from icspacket.proto.iso_pres.presentation import ISO_Presentation
from icspacket.proto.mms import (
    MMS_ABSTRACT_SYNTAX_NAME,
    MMS_PRESENTATION_CONTEXT_ID,
)

# Export everything from ASCE-1 bundled with MMS. FOr ease of use, the EXTERNAL
# type is exported here again.
from icspacket.proto.mms._mms import (
    Name,
    DomainName,
    RDNSequence,
    RelativeDistinguishedName,
    AttributeTypeAndValue,
    ACSE_apdu,
    AARQ_apdu,
    AARE_apdu,
    RLRQ_apdu,
    RLRE_apdu,
    ABRT_apdu,
    ABRT_diagnostic,
    ABRT_source,
    ACSE_requirements,
    Application_context_name_list,
    Application_context_name,
    AP_title,
    AE_qualifier,
    AP_title_form1,
    AE_qualifier_form1,
    AP_title_form2,
    AE_qualifier_form2,
    AE_title,
    AE_title_form1,
    AE_title_form2,
    AE_invocation_identifier,
    AP_invocation_identifier,
    Associate_result,
    Associate_source_diagnostic,
    Association_information,
    Authentication_value,
    Implementation_data,
    Mechanism_name,
    Release_request_reason,
    Release_response_reason,
    EXTERNAL,
)

ACSE_ABSTRACT_SYNTAX_NAME = "2.2.1.0.1"
ACSE_PRESENTATION_CONTEXT_ID = 1

logger = logging.getLogger(__name__)


def build_release_request(reason: Release_request_reason.VALUES) -> RLRQ_apdu:
    """Build an ACSE Release Request (RLRQ) APDU.

    This constructs a Release Request PDU according to ISO 8650 / X.227,
    which is used by an ACSE service user to signal the intention to
    terminate an established association.

    :param reason: Release request reason (e.g., normal release).
    :type reason: Release_request_reason.VALUES
    :return: Encoded ACSE Release Request APDU.
    :rtype: RLRQ_apdu
    """
    return RLRQ_apdu(reason=Release_request_reason(reason))


def build_abort_request(
    source: ABRT_source.VALUES,
    *,
    diagnostic: ABRT_diagnostic.VALUES | None = None,
    user_data: bytes | None = None,
    presentation_context_id: int | None = None,
) -> ABRT_apdu:
    """Build an ACSE Abort Request (ABRT) APDU.

    This creates an abort PDU for immediate termination of an ACSE
    association. It can optionally include diagnostic information and
    user data.

    :param source: Identifies whether the abort was initiated by ACSE service
        user or provider.
    :type source: ABRT_source.VALUES
    :param diagnostic: Optional diagnostic code providing reason for abort.
    :type diagnostic: ABRT_diagnostic.VALUES | None
    :param user_data: Optional user data payload to include with the abort.
    :type user_data: bytes | None
    :param presentation_context_id: Context identifier for encoding user data.
    :type presentation_context_id: int | None
    :return: Encoded ACSE Abort APDU.
    :rtype: ABRT_apdu

    :raises ValueError: If user data is provided without a valid presentation
        context identifier.
    """
    pdu = ABRT_apdu()
    pdu.abort_source = ABRT_source(source)

    if diagnostic is not None:
        pdu.abort_diagnostic = ABRT_diagnostic(diagnostic)

    if user_data is not None:
        value = EXTERNAL()
        value.indirect_reference = presentation_context_id
        value.encoding.single_ASN1_type = user_data
        pdu.user_information = [value]

    return pdu


def build_associate_request(
    user_data: bytes,
    *,
    application_context_name: str | None = None,
    presentation_context_id: int | None = None,
    auth_mechanism_name: str | None = None,
    auth_token: Authentication_value | None = None,
) -> AARQ_apdu:
    """Build an ACSE Association Request (AARQ) APDU.


    This constructs an AARQ PDU for establishing an ACSE association.
    Both the *application-context-name* and *presentation-context-identifier*
    must be supplied together; otherwise, defaults for MMS are applied.


    :param user_data: Encoded user data payload.
    :type user_data: bytes
    :param application_context_name: Optional application context name.
    :type application_context_name: str | None
    :param presentation_context_id: Optional context identifier.
    :type presentation_context_id: int | None
    :return: Encoded ACSE Association Request APDU.
    :rtype: AARQ_apdu

    :raises ValueError: If only one of application_context_name or
        presentation_context_id is provided.

    .. note::

        If neither parameter is given, MMS defaults are used:
        ``MMS_ABSTRACT_SYNTAX_NAME`` and ``MMS_PRESENTATION_CONTEXT_ID``.
    """
    if presentation_context_id and not application_context_name:
        raise ValueError(
            "Cannot specify presentation-context-identifier without application-context-name"
        )

    if application_context_name and not presentation_context_id:
        raise ValueError(
            "Cannot specify application-context-name without presentation-context-identifier"
        )

    if not application_context_name:
        application_context_name = MMS_ABSTRACT_SYNTAX_NAME

    if not presentation_context_id:
        presentation_context_id = MMS_PRESENTATION_CONTEXT_ID

    apdu = AARQ_apdu()
    apdu.application_context_name.value = application_context_name

    version = AARQ_apdu.protocol_version_TYPE()
    version.V_version1 = True
    apdu.protocol_version = version

    value = EXTERNAL()
    value.indirect_reference = presentation_context_id
    value.encoding.single_ASN1_type = user_data
    apdu.user_information = [value]

    if auth_mechanism_name:
        if auth_token is None:
            raise ValueError(
                "auth_token must be provided when auth_mechanism_name is specified"
            )

        apdu.mechanism_name = auth_mechanism_name
        apdu.calling_authentication_value = auth_token
    return apdu


class ACSEConnectionError(ConnectionError):
    """
    Base exception for ACSE-level failures.

    Raised when association control messages (AARQ, AARE, ABRT, RLRQ, RLRE)
    cannot be successfully exchanged or processed. Subclasses distinguish
    between authentication failures, protocol negotiation errors, and
    other association-specific issues.
    """


class ACSEAuthenticationFailure(ACSEConnectionError):
    """
    Raised when ACSE authentication fails.

    This typically occurs during association setup (AARQ/AARE exchange),
    if the peer rejects the provided credentials or the
    authentication mechanism is not recognized.
    """


class Authenticator(ABC):
    """
    Abstract base class for ACSE authenticators.

    Implementations are responsible for populating an ``AARQ-apdu`` with
    the appropriate authentication information (mechanism OID, tokens,
    AP-title/AE-qualifier if applicable).

    Subclasses can implement different authentication mechanisms as
    specified in ISO 8650 (e.g., password).
    """

    @abstractmethod
    def prepare_association(Self, aarq: AARQ_apdu) -> None:
        """
        Populate an ``AARQ-apdu`` with authentication credentials.

        :param aarq: Association Request APDU to modify before sending
                     to the peer.
        :type aarq: AARQ_apdu

        .. note::
           This method should not send the APDU itself, only update
           its authentication-related fields. The caller is responsible
           for encoding and transmission.
        """


class PasswordAuth(Authenticator):
    """
    Annex B: Password-based authentication mechanism.

    Implements the ACSE-defined password mechanism
    ``{ joint-iso-itu-t(2) association-control(2) authentication-mechanism(3) password-1(1) }``.

    This authenticator inserts a cleartext password into the
    ``calling-authentication-value`` field of the ``AARQ-apdu``,
    along with optional application entity identifiers.

    .. warning::
       Password authentication is considered weak and should
       generally only be used in test environments or legacy systems.

    :param password: The cleartext password used for authentication.
    :type password: str
    :param ap_title: Application Process Title (AP-title) identifying
                        the calling entity.
    :type ap_title: str
    :param qualifier: Application Entity (AE) qualifier for the calling entity.
    :type qualifier: int
    """

    MECHANISM_NAME = "2.2.3.1"
    """
    Object identifier for ACSE password authentication.

    ASN.1 notation:
    ``{ joint-iso-itu-t(2) association-control(2) authentication-mechanism(3) password-1(1) }``
    """

    def __init__(self, password: str, ap_title: str, qualifier: int) -> None:
        super().__init__()
        self.__password = password
        # changable parameters
        self.title = ap_title
        self.qualifier = qualifier

    @property
    def password(self) -> str:
        """
        :return: The configured password.
        :rtype: str
        """
        return self.__password

    @override
    def prepare_association(self, aarq: AARQ_apdu) -> None:
        """
        Populate the given ``AARQ-apdu`` with password-based
        authentication fields.

        Sets the mechanism name to ``PasswordAuth.MECHANISM_NAME``,
        inserts the password into ``calling-authentication-value``,
        and fills in the ``calling-AP-title`` and
        ``calling-AE-qualifier``.

        :param aarq: Association Request APDU to modify.
        :type aarq: AARQ_apdu
        """
        token = Authentication_value()
        token.charstring = self.password

        aarq.mechanism_name = PasswordAuth.MECHANISM_NAME
        aarq.calling_authentication_value = token

        title = AP_title()
        title.ap_title_form2 = self.title
        aarq.calling_AP_title = title

        qualifier = AE_qualifier()
        qualifier.ae_qualifier_form2 = self.qualifier
        aarq.calling_AE_qualifier = qualifier


class Association(connection):
    """Implements ACSE association management.

    This class provides establishment, release, and abort of associations
    using the ACSE protocol (ISO 8650 / X.227). It operates on top of the
    Presentation service and ensures proper mapping of user data into the
    negotiated presentation context.

    Example with MMS:

    >>> pres = ISO_Presentation(...)
    >>> assoc = Association(pres, MMS_PRESENTATION_CONTEXT_ID, MMS_ABSTRACT_SYNTAX_NAME, MMSpdu)
    >>> assoc.create(("127.0.0.1", 1234))
    <MMSpdu>

    :param presentation: Active presentation layer connection.
    :type presentation: ISO_Presentation
    :param pres_ctx_id: Optional initial presentation context identifier.
    :type pres_ctx_id: int | None
    :param syntax_name: Optional abstract syntax name for user data.
    :type syntax_name: str | None
    :param asn1_cls: ASN.1 type class bound to the context, if known.
    :type asn1_cls: type | None
    """

    def __init__(
        self,
        presentation: ISO_Presentation,
        pres_ctx_id: int | None = None,
        syntax_name: str | None = None,
        asn1_cls: type | None = None,
        authenticator: Authenticator | None = None,
    ):
        super().__init__()
        self.__presentation = presentation

        self._connected = self.presentation.is_connected()
        # register ACSE service
        _ = self.presentation.presentation_context.new(
            ACSE_ABSTRACT_SYNTAX_NAME,
            ACSE_PRESENTATION_CONTEXT_ID,
            ACSE_apdu,
        )

        self.authenticator = authenticator
        self.pres_ctx_id = pres_ctx_id
        self.pres_syntax_name = syntax_name
        if pres_ctx_id is not None and syntax_name and asn1_cls:
            _ = self.presentation.presentation_context.new(
                syntax_name, pres_ctx_id, asn1_cls
            )

    @property
    def presentation(self) -> ISO_Presentation:
        """Underlying presentation service bound to this ACSE association."""
        return self.__presentation

    @override
    def close(self) -> None:
        """Close the ACSE association and underlying presentation connection."""
        if self.is_connected():
            self.presentation.close()
            self._valid = False
            self._connected = False

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """Connect the underlying presentation service.

        :param address: Remote address tuple (host, port).
        :type address: tuple[str, int]
        """
        self.presentation.connect(address=address)
        self._connected = True

    def create(
        self,
        address: tuple[str, int] | None = None,
        user_data: bytes | None = None,
        pres_ctx_id: int | None = None,
        syntax_name: str | None = None,
        asn1_cls: type | None = None,
    ) -> bytes:
        """Establish an ACSE association (AARQ/AARE exchange).

        This method sends an Association Request (AARQ) and waits for an
        Association Response (AARE). On success, the association becomes
        valid and returns the negotiated user information.

        :param address: Optional remote address for initiating the session.
        :type address: tuple[str, int] | None
        :param user_data: Optional user data to include in the AARQ.
        :type user_data: bytes | None
        :param pres_ctx_id: Presentation context identifier to use.
        :type pres_ctx_id: int | None
        :param syntax_name: Application context name to negotiate.
        :type syntax_name: str | None
        :param asn1_cls: ASN.1 class for decoding user data.
        :type asn1_cls: type | None
        :return: Associated user information payload.
        :rtype: bytes

        :raises ACSEConnectionError: If association negotiation fails.
        :raises ConnectionError: If already connected.

        .. note::
            Both ``pres_ctx_id`` and ``syntax_name`` must be provided, unless
            defaults are set using the constructor.
        """
        # 7.1 Association establishment
        if self.is_valid():
            raise ConnectionError("Already connected")

        pres_ctx_id = pres_ctx_id or self.pres_ctx_id
        if pres_ctx_id is None:
            raise ACSEConnectionError(
                "ACSE association failed - no presentation context ID."
            )

        syntax_name = syntax_name or self.pres_syntax_name
        if syntax_name is None:
            raise ACSEConnectionError(
                "ACSE association failed - no application context name."
            )

        if asn1_cls is not None:
            if pres_ctx_id not in self.presentation.presentation_context.asn1_types:
                _ = self.presentation.presentation_context.new(
                    syntax_name, pres_ctx_id, asn1_cls
                )

        aarq = build_associate_request(
            user_data or b"",
            presentation_context_id=pres_ctx_id,
            application_context_name=syntax_name,
        )
        if self.authenticator is not None:
            self.authenticator.prepare_association(aarq)

        apdu = ACSE_apdu(aarq=aarq)
        try:
            apdu = self.presentation.init_session(apdu.ber_encode(), address)
            self._connected = True
        except ConnectionClosedError:
            if self.authenticator:
                raise ACSEAuthenticationFailure

            raise ACSEConnectionError(
                "ACSE association failed - connection closed by peer. Maybe missing credentials?"
            )

        if not apdu:
            raise ACSEConnectionError("ACSE association failed - no response received")

        if not isinstance(apdu, ACSE_apdu):
            raise ACSEConnectionError(f"Received invalid ACSE response: {type(apdu)}")

        if apdu.present != ACSE_apdu.PRESENT.PR_aare:
            raise ACSEConnectionError(
                f"Received invalid ACSE response: {apdu.present} (expected AARE)"
            )

        match apdu.aare.result.value:
            case Associate_result.VALUES.V_rejected_transient:
                raise ACSEConnectionError("ACSE association failed - rejected")
            case Associate_result.VALUES.V_rejected_permanent:
                raise ACSEConnectionError(
                    "ACSE association failed - rejected permanent"
                )
            case _:
                pass  # fall through

        user_info = apdu.aare.user_information
        if user_info is None or len(user_info) != 1:
            raise ACSEConnectionError("ACSE association failed - no user info received")

        acse_data = user_info[0]
        if acse_data.indirect_reference != pres_ctx_id:
            raise ACSEConnectionError(
                f"Received invalid ACSE response: reference={acse_data.indirect_reference}, "
                + f"expected={pres_ctx_id}"
            )

        raw_data = acse_data.encoding.single_ASN1_type
        if raw_data is None:
            raise ACSEConnectionError(
                f"Received invalid ACSE associated data: {acse_data.encoding.present}"
            )

        self._valid = True
        self.pres_ctx_id = pres_ctx_id
        if pres_ctx_id not in self.presentation.presentation_context.asn1_types:
            if asn1_cls is None:
                raise ConnectionStateError(
                    "ACSE target user data type not registered in presentation context"
                )
        return raw_data

    def release(
        self,
        reason: Release_request_reason.VALUES | None = None,
        graceful: bool = False,
    ) -> None:
        """Release the ACSE association.

        Sends a Release Request (RLRQ). Depending on ``graceful``, this
        either allows an orderly release or immediately terminates.

        :param reason: Reason code for release (default = normal).
        :type reason: Release_request_reason.VALUES, optional
        :param graceful: If True, perform graceful closure; otherwise force.
        :type graceful: bool, optional

        :raises ConnectionClosedError: If no release response is received in non-graceful mode.
        :raises ACSEConnectionError: If an invalid response is returned.
        """
        self._assert_connected()
        request = build_release_request(
            reason or Release_request_reason.VALUES.V_normal
        )
        acse_pdu = ACSE_apdu(rlrq=request)
        response = self.presentation.close_session(
            acse_pdu.ber_encode(),
            ACSE_PRESENTATION_CONTEXT_ID,
            graceful=graceful,
        )
        if graceful:
            try:
                if response is None:
                    # here, we expect some data
                    raise ConnectionClosedError

                try:
                    acse_response = ACSE_apdu.ber_decode(response)
                except ValueError:
                    raise ACSEConnectionError(
                        f"Received invalid ACSE response: {response.hex()}"
                    )

                if acse_response.present != ACSE_apdu.PRESENT.PR_rlrq:
                    logger.warning(
                        "Received unexpected ACSE release response: %s",
                        acse_response.present,
                    )
            finally:
                # make sure to clean up afterwads
                self.presentation.close()

        self._connected = False
        self._valid = False

    def abort(
        self,
        source: ABRT_source.VALUES | None = None,
        user_data: bytes | None = None,
        pres_context_id: int | None = None,
    ) -> None:
        """Abort the ACSE association.

        Immediately terminates the association by sending an Abort (ABRT)
        APDU. Optionally includes diagnostic info and user data.

        :param source: Abort initiator (default: ACSE service user).
        :type source: ABRT_source.VALUES, optional
        :param user_data: Optional encoded user data to send.
        :type user_data: bytes, optional
        :param pres_context_id: Context identifier for user data.
        :type pres_context_id: int, optional
        """
        if source is None:
            source = ABRT_source.VALUES.V_acse_service_user

        acse_pdu = ACSE_apdu(
            abrt=build_abort_request(
                source,
                user_data=user_data,
                presentation_context_id=pres_context_id,
            )
        )
        self.presentation.close_session(
            acse_pdu.ber_encode(),
            ACSE_PRESENTATION_CONTEXT_ID,
        )
        self._connected = False
        self._valid = False

    @override
    def send_data(self, octets: bytes, /) -> None:
        """Send encoded user data via ACSE.

        The data is wrapped into the negotiated presentation context.

        :param octets: Encoded ASN.1 payload.
        :type octets: bytes
        :raises ConnectionNotEstablished: If no presentation context is bound.
        """
        self._assert_connected()
        if self.pres_ctx_id is None:
            raise ConnectionNotEstablished(
                "ACSE connection not established - no presentation context ID. "
                + "Use create() to setup an association."
            )

        self.presentation.send_encoded_data(octets, pres_ctx_id=self.pres_ctx_id)

    @override
    def recv_data(self) -> bytes:
        """Not supported.

        Raw data reception is disallowed in ACSE. Use ``recv_encoded_data``
        instead.
        """
        raise NotADirectoryError(
            "ACSE does not support receiving raw data. Use recv_encoded_data() instead."
        )

    def recv_encoded_data(self) -> Any | None:
        """Receive user data through ACSE association.

        Retrieves encoded user information, decoding it according to the
        negotiated ASN.1 type for the active presentation context.

        :return: Decoded user data instance or ``None``.
        :rtype: Any | None
        :raises ConnectionNotEstablished: If association has no context ID.
        :raises ConnectionStateError: If no ASN.1 type is registered for the context.
        """
        self._assert_connected()
        if self.pres_ctx_id is None:
            raise ConnectionNotEstablished(
                "ACSE connection not established - no presentation context ID. "
                + "Use create() to setup an association."
            )

        if self.pres_ctx_id not in self.presentation.presentation_context.asn1_types:
            raise ConnectionStateError(
                f"ACSE target user data type({self.pres_ctx_id}) not registered "
                + "in presentation context"
            )

        return self.presentation.recv_encoded_data()


__all__ = [  # noqa
    "AARE_apdu",
    "AARQ_apdu",
    "ABRT_apdu",
    "ABRT_diagnostic",
    "ABRT_source",
    "ACSE_ABSTRACT_SYNTAX_NAME",
    "ACSE_apdu",
    "ACSE_PRESENTATION_CONTEXT_ID",
    "ACSE_requirements",
    "ACSEAuthenticationFailure",
    "ACSEConnectionError",
    "AE_invocation_identifier",
    "AE_qualifier_form1",
    "AE_qualifier_form2",
    "AE_qualifier",
    "AE_title_form1",
    "AE_title_form2",
    "AE_title",
    "AP_invocation_identifier",
    "AP_title_form1",
    "AP_title_form2",
    "AP_title",
    "Application_context_name_list",
    "Application_context_name",
    "Associate_result",
    "Associate_source_diagnostic",
    "Association_information",
    "Association",
    "AttributeTypeAndValue",
    "Authentication_value",
    "Authenticator",
    "build_abort_request",
    "build_associate_request",
    "build_release_request",
    "DomainName",
    "EXTERNAL",
    "Implementation_data",
    "Mechanism_name",
    "Name",
    "PasswordAuth",
    "RDNSequence",
    "RelativeDistinguishedName",
    "Release_request_reason",
    "Release_response_reason",
    "RLRE_apdu",
    "RLRQ_apdu",
]
