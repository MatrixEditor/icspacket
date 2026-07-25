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
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ClassVar

from typing_extensions import override

from icspacket.core.connection import (
    ConnectionClosedError,
    ConnectionNotEstablished,
    ConnectionStateError,
    connection,
)
from icspacket.proto.iso_pres.presentation import (
    ISO_Presentation,
    PresentationAbortError,
)
from icspacket.proto.iso_ses.session import SessionAbortError
from icspacket.proto.mms import (
    MMS_CONTEXT_NAME,
    MMS_PRESENTATION_CONTEXT_ID,
)

# Export everything from ASCE-1 bundled with MMS. For ease of use, the EXTERNAL
# type is exported here again.
from icspacket.proto.mms._mms import (
    EXTERNAL,
    AARE_apdu,
    AARQ_apdu,
    ABRT_apdu,
    ABRT_diagnostic,
    ABRT_source,
    ACSE_apdu,
    ACSE_requirements,
    AE_invocation_identifier,
    AE_qualifier,
    AE_qualifier_form1,
    AE_qualifier_form2,
    AE_title,
    AE_title_form1,
    AE_title_form2,
    AP_invocation_identifier,
    AP_title,
    AP_title_form1,
    AP_title_form2,
    Application_context_name,
    Application_context_name_list,
    Associate_result,
    Associate_source_diagnostic,
    Association_information,
    AttributeTypeAndValue,
    Authentication_value,
    DomainName,
    Implementation_data,
    Mechanism_name,
    Name,
    RDNSequence,
    RelativeDistinguishedName,
    Release_request_reason,
    Release_response_reason,
    RLRE_apdu,
    RLRQ_apdu,
)

ACSE_ABSTRACT_SYNTAX_NAME = "2.2.1.0.1"
ACSE_PRESENTATION_CONTEXT_ID = 1

logger = logging.getLogger(__name__)


ACSE_PROTOCOL_VERSION = 1


def _require_authentication_functional_unit(apdu: AARQ_apdu) -> None:
    requirements = apdu.sender_acse_requirements
    if requirements is None:
        requirements = ACSE_requirements()

    requirements.V_authentication = True
    apdu.sender_acse_requirements = requirements


def _build_context_name_list(
    names: Iterable[str] | Application_context_name_list | None,
) -> Application_context_name_list | None:
    if names is None or isinstance(names, Application_context_name_list):
        return names

    context_names = Application_context_name_list()
    for name in names:
        context_names.add(Application_context_name(name))
    return context_names


def _build_external(
    user_data: bytes,
    presentation_context_id: int,
    *,
    direct_reference: str | None = None,
) -> EXTERNAL:
    value = EXTERNAL()
    value.indirect_reference = presentation_context_id
    if direct_reference is not None:
        value.direct_reference = direct_reference
    value.encoding.single_ASN1_type = user_data
    return value


def _build_association_information(
    user_data: bytes | Iterable[EXTERNAL] | Association_information | None,
    presentation_context_id: int | None,
    *,
    direct_reference: str | None = None,
) -> Association_information | None:
    if user_data is None or isinstance(user_data, Association_information):
        return user_data

    if isinstance(user_data, bytes):
        if presentation_context_id is None:
            raise ValueError(
                "presentation_context_id must be provided when user_data is specified"
            )
        return Association_information(
            [
                _build_external(
                    user_data,
                    presentation_context_id,
                    direct_reference=direct_reference,
                )
            ]
        )

    return Association_information(user_data)


def _extract_single_user_information(
    user_information: Association_information | None,
    *,
    expected_context_id: int | None = None,
) -> bytes:
    if user_information is None or len(user_information) == 0:
        return b""

    if len(user_information) != 1:
        raise ACSEConnectionError("Expected exactly one ACSE user-information value")

    acse_data = user_information[0]
    if (
        expected_context_id is not None
        and acse_data.indirect_reference != expected_context_id
    ):
        raise ACSEConnectionError(
            "Received invalid ACSE user-information reference="
            + f"{acse_data.indirect_reference}, expected={expected_context_id}"
        )

    raw_data = acse_data.encoding.single_ASN1_type
    if raw_data is None:
        raise ACSEConnectionError(
            f"Received invalid ACSE associated data: {acse_data.encoding.present}"
        )

    return raw_data


def build_release_request(
    reason: Release_request_reason.VALUES,
    *,
    user_data: bytes | Iterable[EXTERNAL] | Association_information | None = None,
    presentation_context_id: int | None = None,
    direct_reference: str | None = None,
) -> RLRQ_apdu:
    """Build an ACSE Release Request (RLRQ) APDU.

    Packages the given release reason, plus any optional user data, into an
    :class:`RLRQ_apdu` ready to hand off to the association layer, kicking
    off the orderly shutdown handshake according to ISO 8650 / X.227.

    :param reason: Release request reason (e.g., normal release).
    :type reason: Release_request_reason.VALUES
    :return: Encoded ACSE Release Request APDU.
    :rtype: RLRQ_apdu
    """
    request = RLRQ_apdu(reason=Release_request_reason(reason))
    request.user_information = _build_association_information(
        user_data,
        presentation_context_id,
        direct_reference=direct_reference,
    )
    return request


def build_abort_request(
    source: ABRT_source.VALUES,
    *,
    diagnostic: ABRT_diagnostic.VALUES | None = None,
    user_data: bytes | Iterable[EXTERNAL] | Association_information | None = None,
    presentation_context_id: int | None = None,
    direct_reference: str | None = None,
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

    pdu.user_information = _build_association_information(
        user_data,
        presentation_context_id,
        direct_reference=direct_reference,
    )

    return pdu


def build_associate_request(
    user_data: bytes | Iterable[EXTERNAL] | Association_information | None = None,
    *,
    application_context_name: str | None = None,
    application_context_name_list: Iterable[str]
    | Application_context_name_list
    | None = None,
    presentation_context_id: int | None = None,
    auth_mechanism_name: str | None = None,
    auth_token: Authentication_value | None = None,
    protocol_version: bool = True,
    implementation_information: str | None = None,
    direct_reference: str | None = None,
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
        ``MMS_CONTEXT_NAME`` and ``MMS_PRESENTATION_CONTEXT_ID``.
    """
    if presentation_context_id is not None and not application_context_name:
        raise ValueError(
            "Cannot specify presentation-context-identifier without application-context-name"
        )

    if application_context_name and presentation_context_id is None:
        raise ValueError(
            "Cannot specify application-context-name without presentation-context-identifier"
        )

    if application_context_name is None:
        application_context_name = MMS_CONTEXT_NAME

    if presentation_context_id is None:
        presentation_context_id = MMS_PRESENTATION_CONTEXT_ID

    apdu = AARQ_apdu()
    apdu.application_context_name.value = application_context_name
    if protocol_version:
        version = AARQ_apdu.protocol_version_TYPE()
        version.V_version1 = True
        apdu.protocol_version = version

    apdu.user_information = _build_association_information(
        user_data,
        presentation_context_id,
        direct_reference=direct_reference,
    )

    context_name_list = _build_context_name_list(application_context_name_list)
    if context_name_list is not None:
        apdu.application_context_name_list = context_name_list
        requirements = apdu.sender_acse_requirements
        if requirements is None:
            requirements = ACSE_requirements()

        requirements.V_application_context_negotiation = True
        apdu.sender_acse_requirements = requirements

    if auth_mechanism_name and auth_token is None:
        raise ValueError(
            "auth_token must be provided when auth_mechanism_name is specified"
        )

    if auth_token is not None:
        if auth_mechanism_name:
            apdu.mechanism_name = auth_mechanism_name
        apdu.calling_authentication_value = auth_token
        _require_authentication_functional_unit(apdu)

    if implementation_information is not None:
        apdu.implementation_information = implementation_information

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


class ACSEAssociationRejected(ACSEConnectionError):
    """Raised when an AARE rejects association establishment."""

    def __init__(
        self,
        result: Associate_result.VALUES,
        diagnostic: Associate_source_diagnostic | None = None,
    ) -> None:
        super().__init__(f"ACSE association rejected: result={result}")
        self.result: Associate_result.VALUES = result
        self.diagnostic: Associate_source_diagnostic | None = diagnostic


class ACSEProtocolError(ACSEConnectionError):
    """Raised when an ACSE protocol error is detected."""


class ACSEReleaseRejected(ACSEConnectionError):
    """Raised when an orderly release receives a negative response."""

    def __init__(self, response: RLRE_apdu | None = None) -> None:
        super().__init__("ACSE release rejected by peer")
        self.response: RLRE_apdu | None = response


class ACSEReleaseCollision(ACSEConnectionError):
    """Raised when both peers initiate release concurrently."""

    def __init__(self, request: RLRQ_apdu | None = None) -> None:
        super().__init__("ACSE release collision")
        self.request: RLRQ_apdu | None = request


class ACSEAbortIndication(ACSEConnectionError):
    """Raised when an A-ABORT indication is received."""

    def __init__(
        self,
        source: ABRT_source.VALUES,
        user_information: Association_information | None = None,
        diagnostic: ABRT_diagnostic | None = None,
    ) -> None:
        super().__init__(f"ACSE abort received: source={source}")
        self.source: ABRT_source.VALUES = source
        self.user_information: Association_information | None = user_information
        self.diagnostic: ABRT_diagnostic | None = diagnostic


class ACSEProviderAbortIndication(ACSEConnectionError):
    """Raised when an A-P-ABORT indication is received."""

    def __init__(self, value: Any | None = None) -> None:
        super().__init__("ACSE provider abort received")
        self.value = value


@dataclass(frozen=True)
class ACSEEvent:
    """Parsed ACSE data or release event."""

    kind: str
    apdu: ACSE_apdu | None = None
    value: Any | None = None
    accepted: bool | None = None


class Authenticator(ABC):
    """
    Abstract base class for ACSE authenticators.

    Implementations are responsible for populating an ``AARQ-apdu`` with
    the appropriate authentication information (mechanism OID, tokens,
    AP-title/AE-qualifier if applicable).

    Subclasses can implement different authentication mechanisms
    according to ISO 8650 (e.g., password).
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

    def validate_associate_response(self, aare: AARE_apdu) -> None:
        """Validate authentication fields on an incoming AARE."""


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

    MECHANISM_NAME: ClassVar[str] = "2.2.3.1"
    """
    Object identifier for ACSE password authentication.

    ASN.1 notation:
    ``{ joint-iso-itu-t(2) association-control(2) authentication-mechanism(3) password-1(1) }``
    """

    def __init__(
        self,
        password: str,
        ap_title: str,
        qualifier: int,
        *,
        include_mechanism_name: bool = True,
        require_mechanism_name: bool = False,
    ) -> None:
        super().__init__()
        self.__password = password
        # changable parameters
        self.title: str = ap_title
        self.qualifier: int = qualifier
        self.include_mechanism_name: bool = include_mechanism_name
        self.require_mechanism_name: bool = require_mechanism_name

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

        if self.include_mechanism_name:
            aarq.mechanism_name = PasswordAuth.MECHANISM_NAME
        aarq.calling_authentication_value = token
        _require_authentication_functional_unit(aarq)

        title = AP_title()
        title.ap_title_form2 = self.title
        aarq.calling_AP_title = title

        qualifier = AE_qualifier()
        qualifier.ae_qualifier_form2 = self.qualifier
        aarq.calling_AE_qualifier = qualifier

    @override
    def validate_associate_response(self, aare: AARE_apdu) -> None:
        token = aare.responding_authentication_value
        if token is None and aare.mechanism_name is None:
            return
        self._validate_common(
            aare.mechanism_name,
            token,
            aare.responding_AP_title,
            aare.responding_AE_qualifier,
        )

    def _validate_common(
        self,
        mechanism_name: Mechanism_name | None,
        token: Authentication_value | None,
        title: AP_title | None,
        qualifier: AE_qualifier | None,
    ) -> None:
        mechanism_value = None if mechanism_name is None else mechanism_name.value
        if mechanism_value is None:
            if self.require_mechanism_name:
                error = ACSEAuthenticationFailure(
                    "ACSE password authentication mechanism name required"
                )
                error.diagnostic = (
                    ABRT_diagnostic.VALUES.V_authentication_mechanism_name_required
                )
                raise error
        elif mechanism_value != PasswordAuth.MECHANISM_NAME:
            error = ACSEAuthenticationFailure(
                "ACSE password authentication mechanism name not recognized"
            )
            error.diagnostic = (
                ABRT_diagnostic.VALUES.V_authentication_mechanism_name_not_recognized
            )
            raise error

        if token is None or token.present != Authentication_value.PRESENT.PR_charstring:
            error = ACSEAuthenticationFailure("ACSE password authentication required")
            error.diagnostic = ABRT_diagnostic.VALUES.V_authentication_required
            raise error

        if token.charstring != self.password:
            error = ACSEAuthenticationFailure("ACSE password authentication failed")
            error.diagnostic = ABRT_diagnostic.VALUES.V_authentication_failure
            raise error

        if title is not None and (
            title.present != AP_title.PRESENT.PR_ap_title_form2
            or title.ap_title_form2.value != self.title
        ):
            error = ACSEAuthenticationFailure("ACSE AP-title authentication failed")
            error.diagnostic = ABRT_diagnostic.VALUES.V_authentication_failure
            raise error

        if qualifier is not None and (
            qualifier.present != AE_qualifier.PRESENT.PR_ae_qualifier_form2
            or qualifier.ae_qualifier_form2.value != self.qualifier
        ):
            error = ACSEAuthenticationFailure("ACSE AE-qualifier authentication failed")
            error.diagnostic = ABRT_diagnostic.VALUES.V_authentication_failure
            raise error


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

        self._connected: bool = self.presentation.is_connected()
        # register ACSE service
        _ = self.presentation.presentation_context.new(
            ACSE_ABSTRACT_SYNTAX_NAME,
            ACSE_PRESENTATION_CONTEXT_ID,
            ACSE_apdu,
        )

        self.authenticator: Authenticator | None = authenticator
        self.pres_ctx_id: int | None = pres_ctx_id
        self.pres_syntax_name: str | None = syntax_name
        self.role: str | None = None
        self.acse_protocol_version: int = ACSE_PROTOCOL_VERSION
        self.requested_acse_requirements: ACSE_requirements | None = None
        self.accepted_acse_requirements: ACSE_requirements | None = None
        self.application_context_name: str | None = None
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
            self._valid: bool = False
            self._connected = False

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """Connect the underlying presentation service.

        :param address: Remote address tuple (host, port).
        :type address: tuple[str, int]
        """
        self.presentation.connect(address=address)
        self._connected = True

    def _validate_aare(
        self,
        aare: AARE_apdu,
        expected_application_context_name: str,
    ) -> None:
        if aare.application_context_name.value != expected_application_context_name:
            raise ACSEProtocolError(
                "AARE application context does not match the requested context: "
                + f"{aare.application_context_name.value!r}"
            )

        if self.authenticator is not None:
            # NOTE: ``responder-acse-requirements`` is an OPTIONAL field in the
            # AARE (ISO/IEC 8650 / X.227). Many real-world implementations
            # (e.g. libiec61850) accept the authentication and the association
            # overall without ever echoing the bit back. Only treat
            # this as a hard authentication failure when the responder
            # explicitly signals that the functional unit was *not* accepted;
            # otherwise defer to the authenticator's own response validation,
            # which already tolerates an AARE that omits the mechanism/token.
            requirements = aare.responder_acse_requirements
            if requirements is not None and not requirements.V_authentication:
                raise ACSEAuthenticationFailure(
                    "ACSE authentication functional unit was not accepted"
                )
            self.authenticator.validate_associate_response(aare)

    def _raise_for_aare_result(self, aare: AARE_apdu) -> None:
        if (
            aare.result_source_diagnostic is None
            or aare.result_source_diagnostic.present
            == Associate_source_diagnostic.PRESENT.PR_NOTHING
        ):
            raise ACSEProtocolError(
                "Received invalid AARE: missing result-source-diagnostic"
            )

        try:
            result_value = aare.result.value
        except AttributeError as e:
            raise ACSEConnectionError("Received invalid AARE: missing result") from e

        match result_value:
            case Associate_result.VALUES.V_accepted:
                return
            case (
                Associate_result.VALUES.V_rejected_transient
                | Associate_result.VALUES.V_rejected_permanent
            ):
                diagnostic = aare.result_source_diagnostic
                if (
                    self.authenticator
                    and diagnostic is not None
                    and (
                        diagnostic.present
                        == Associate_source_diagnostic.PRESENT.PR_acse_service_user
                        and diagnostic.acse_service_user
                        in {
                            Associate_source_diagnostic.acse_service_user_VALUES.V_authentication_mechanism_name_not_recognized,
                            Associate_source_diagnostic.acse_service_user_VALUES.V_authentication_mechanism_name_required,
                            Associate_source_diagnostic.acse_service_user_VALUES.V_authentication_failure,
                            Associate_source_diagnostic.acse_service_user_VALUES.V_authentication_required,
                        }
                    )
                ):
                    raise ACSEAuthenticationFailure(
                        f"ACSE authentication failed: {diagnostic.acse_service_user}"
                    )
                raise ACSEAssociationRejected(result_value, diagnostic)
            case _:
                raise ACSEConnectionError(
                    f"Received invalid AARE result: {result_value!r}"
                )

    def create(
        self,
        address: tuple[str, int] | None = None,
        user_data: bytes | None = None,
        pres_ctx_id: int | None = None,
        syntax_name: str | None = None,
        application_context_name: str | None = None,
        application_context_name_list: Iterable[str]
        | Application_context_name_list
        | None = None,
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

        expects_user_info = user_data is not None
        requested_application_context = application_context_name or syntax_name
        aarq = build_associate_request(
            user_data,
            presentation_context_id=pres_ctx_id,
            application_context_name=requested_application_context,
            application_context_name_list=application_context_name_list,
        )
        if self.authenticator is not None:
            self.authenticator.prepare_association(aarq)

        apdu = ACSE_apdu(aarq=aarq)
        try:
            apdu = self.presentation.init_session(apdu.ber_encode(), address)
            self._connected = True
        except (ConnectionClosedError, SessionAbortError, PresentationAbortError):
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

        self._raise_for_aare_result(apdu.aare)
        self._validate_aare(apdu.aare, requested_application_context)

        user_info = apdu.aare.user_information
        if user_info is None or len(user_info) == 0:
            if expects_user_info:
                raise ACSEConnectionError(
                    "ACSE association failed - no user info received"
                )

            self._valid = True
            self.role = "requestor"
            self.requested_acse_requirements = aarq.sender_acse_requirements
            self.accepted_acse_requirements = apdu.aare.responder_acse_requirements
            self.application_context_name = requested_application_context
            self.pres_ctx_id = pres_ctx_id
            return b""

        raw_data = _extract_single_user_information(
            user_info,
            expected_context_id=pres_ctx_id,
        )

        self._valid = True
        self.role = "requestor"
        self.requested_acse_requirements = aarq.sender_acse_requirements
        self.accepted_acse_requirements = apdu.aare.responder_acse_requirements
        self.application_context_name = requested_application_context
        self.pres_ctx_id = pres_ctx_id
        if (
            pres_ctx_id not in self.presentation.presentation_context.asn1_types
            and asn1_cls is None
        ):
            raise ConnectionStateError(
                "ACSE target user data type not registered in presentation context"
            )
        return raw_data

    def create_x410(
        self,
        address: tuple[str, int] | None = None,
        user_data: bytes | None = None,
    ) -> bytes:
        """Establish an X.410-1984 mode association without ACSE APDUs."""
        if self.is_valid():
            raise ConnectionError("Already connected")

        response = self.presentation.init_x410_session(user_data or b"", address)
        self._connected = True
        self._valid = True
        self.role = "requestor"
        self.application_context_name = None
        self.requested_acse_requirements = None
        self.accepted_acse_requirements = None
        return response

    def release(
        self,
        reason: Release_request_reason.VALUES | None = None,
        graceful: bool = True,
        user_data: bytes | None = None,
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
            reason or Release_request_reason.VALUES.V_normal,
            user_data=user_data,
            presentation_context_id=self.pres_ctx_id,
        )
        acse_pdu = ACSE_apdu(rlrq=request)
        try:
            release_result = self.presentation.close_session_result(
                acse_pdu.ber_encode(), ACSE_PRESENTATION_CONTEXT_ID, graceful=graceful
            )
        except PresentationAbortError as e:
            self._raise_for_presentation_abort(e.value)

        if graceful:
            if release_result is None or release_result.value is None:
                raise ConnectionClosedError

            acse_response = release_result.value
            if not isinstance(acse_response, ACSE_apdu):
                raise ACSEConnectionError(
                    f"Received invalid ACSE response: {type(acse_response)}"
                )

            if release_result.collision:
                if acse_response.present != ACSE_apdu.PRESENT.PR_rlrq:
                    raise ACSEConnectionError(
                        "Release collision did not contain RLRQ APDU: "
                        + f"{acse_response.present}"
                    )
                raise ACSEReleaseCollision(acse_response.rlrq)

            if acse_response.present != ACSE_apdu.PRESENT.PR_rlre:
                self.presentation.close()
                self._connected = False
                self._valid = False
                raise ACSEConnectionError(
                    f"Received unexpected ACSE release response: {acse_response.present}"
                )

            if not release_result.accepted:
                self._connected = True
                self._valid = True
                raise ACSEReleaseRejected(acse_response.rlre)

            reason_value = None
            if acse_response.rlre.reason is not None:
                reason_value = acse_response.rlre.reason.value
            if reason_value == Release_response_reason.VALUES.V_not_finished:
                self._connected = True
                self._valid = True
                raise ACSEReleaseRejected(acse_response.rlre)

        self._connected = False
        self._valid = False

    def abort(
        self,
        source: ABRT_source.VALUES | None = None,
        user_data: bytes | None = None,
        pres_context_id: int | None = None,
        diagnostic: ABRT_diagnostic.VALUES | None = None,
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
        elif source == ABRT_source.VALUES.V_acse_service_provider:
            raise ValueError(
                "ACSE service-provider abort source is reserved for protocol errors"
            )

        if diagnostic is not None:
            requirements = self.accepted_acse_requirements
            if requirements is None or not requirements.V_authentication:
                raise ValueError(
                    "ABRT diagnostic is only valid when authentication was negotiated"
                )

        target_pres_ctx_id = pres_context_id or self.pres_ctx_id
        session_version = self.presentation.session.settings.version
        if session_version == 1:
            if user_data is not None and target_pres_ctx_id is None:
                raise ValueError(
                    "pres_context_id must be provided when user_data is specified"
                )

            self.presentation.abort_session(
                user_data,
                target_pres_ctx_id or ACSE_PRESENTATION_CONTEXT_ID,
            )
        else:
            acse_pdu = ACSE_apdu(
                abrt=build_abort_request(
                    source,
                    diagnostic=diagnostic,
                    user_data=user_data,
                    presentation_context_id=target_pres_ctx_id,
                )
            )
            self.presentation.abort_session(
                acse_pdu.ber_encode(),
                ACSE_PRESENTATION_CONTEXT_ID,
            )
        self._connected = False
        self._valid = False

    def abort_protocol_error(
        self,
        diagnostic: ABRT_diagnostic.VALUES = ABRT_diagnostic.VALUES.V_protocol_error,
    ) -> None:
        """Abort the association as the ACSE service-provider."""
        session_version = self.presentation.session.settings.version
        if session_version == 1:
            self.presentation.abort_session()
        else:
            requirements = self.accepted_acse_requirements
            acse_pdu = ACSE_apdu(
                abrt=build_abort_request(
                    ABRT_source.VALUES.V_acse_service_provider,
                    diagnostic=diagnostic
                    if requirements is not None and requirements.V_authentication
                    else None,
                )
            )
            self.presentation.abort_session(
                acse_pdu.ber_encode(),
                ACSE_PRESENTATION_CONTEXT_ID,
            )
        self._connected = False
        self._valid = False

    def _raise_for_presentation_abort(self, value: Any | None = None) -> None:
        self._connected = False
        self._valid = False
        if isinstance(value, ACSE_apdu) and value.present == ACSE_apdu.PRESENT.PR_abrt:
            abrt = value.abrt
            raise ACSEAbortIndication(
                abrt.abort_source.value,
                abrt.user_information,
                abrt.abort_diagnostic,
            )

        raise ACSEProviderAbortIndication(value)

    def recv_event(self) -> ACSEEvent:
        """Receive and classify the next ACSE or user-data event."""
        self._assert_connected()
        try:
            event = self.presentation.recv_event()
        except PresentationAbortError as e:
            self._raise_for_presentation_abort(e.value)

        value = event.value
        if not isinstance(value, ACSE_apdu):
            return ACSEEvent(
                kind=event.kind,
                value=value,
                accepted=event.accepted,
            )

        match value.present:
            case ACSE_apdu.PRESENT.PR_rlrq:
                return ACSEEvent(
                    kind="release_request",
                    apdu=value,
                    value=value.rlrq,
                )
            case ACSE_apdu.PRESENT.PR_rlre:
                return ACSEEvent(
                    kind="release_response",
                    apdu=value,
                    value=value.rlre,
                    accepted=event.accepted,
                )
            case ACSE_apdu.PRESENT.PR_abrt:
                abrt = value.abrt
                self._connected = False
                self._valid = False
                raise ACSEAbortIndication(
                    abrt.abort_source.value,
                    abrt.user_information,
                    abrt.abort_diagnostic,
                )
            case _:
                self.abort_protocol_error()
                raise ACSEProtocolError(
                    f"Unexpected ACSE APDU in established association: {value.present}"
                )

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

    def send_x410_data(self, octets: bytes, /) -> None:
        """Send X.410-1984 mode user data without ACSE APCI."""
        self._assert_connected()
        self.presentation.send_x410_data(octets)

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

        event = self.recv_event()
        if event.kind == "data":
            return event.value

        if event.kind == "release_request":
            raise ConnectionStateError("Received A-RELEASE indication")

        if event.kind == "release_response":
            raise ConnectionStateError("Received unexpected A-RELEASE response")

        raise ACSEProtocolError(f"Unexpected ACSE event: {event.kind}")

    def recv_x410_data(self) -> bytes:
        """Receive X.410-1984 mode user data without ACSE APCI."""
        self._assert_connected()
        return self.presentation.recv_x410_data()


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
    "ACSEAbortIndication",
    "ACSEAssociationRejected",
    "ACSEAuthenticationFailure",
    "ACSEConnectionError",
    "ACSEEvent",
    "ACSEProviderAbortIndication",
    "ACSEProtocolError",
    "ACSEReleaseCollision",
    "ACSEReleaseRejected",
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
