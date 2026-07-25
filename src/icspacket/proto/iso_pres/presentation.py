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
from dataclasses import dataclass
from typing import Any

from typing_extensions import override

from icspacket.core.connection import (
    ConnectionClosedError,
    ConnectionStateError,
    connection,
)
from icspacket.proto.cotp.connection import COTP_Connection
from icspacket.proto.iso_pres.iso8823 import (
    ARP_PPDU,
    ARU_PPDU,
    CPA_PPDU,
    CPR_PPDU,
    Abort_reason,
    Abort_type,
    Event_identifier,
    PresentaionContextItem,
    Presentation_context_identifier_list,
    Presentation_requirements,
    Result,
    User_data,
)
from icspacket.proto.iso_pres.util import (
    build_connect_ppdu,
    build_user_data,
    build_x410_user_data,
    presentation_context_id,
    presentation_context_transfer_syntaxes,
    user_data_get_single_asn1,
    validate_presentation_context_items,
)
from icspacket.proto.iso_ses.session import ISO_Session, SessionAbortError

TRANSFER_SYNTAX_BASIC = "2.1.1"


class ISO_PresentationContext:
    """Manages Presentation Context Items.

    Each entry pairs an ASN.1 *abstract syntax* with the encoding(s) - the
    *transfer syntaxes* - that this library is willing to use for it, which
    together tell the presentation layer how to interpret a given block of
    user data.

    This class is used to create, register, and remove contexts, and is
    passed to :class:`ISO_Presentation` to negotiate which contexts are valid
    during association.
    """

    def __init__(self) -> None:
        self.__items: dict[int, PresentaionContextItem] = {}
        self.__types: dict[int, type] = {}

    @property
    def items(self) -> dict[int, PresentaionContextItem]:
        """Dictionary of Presentation Context Items keyed by their ID."""
        return self.__items

    @property
    def asn1_types(self) -> dict[int, type]:
        """Dictionary mapping context IDs to ASN.1 decoding classes."""
        return self.__types

    def add(self, item: PresentaionContextItem, asn1_cls: type) -> None:
        """Register an existing Presentation Context Item and bind its ASN.1 class."""
        validate_presentation_context_items([item])
        context_id = presentation_context_id(item)
        if context_id in self.items:
            raise ValueError(f"Duplicate presentation context id {context_id}")

        self.items[context_id] = item
        self.asn1_types[context_id] = asn1_cls

    def new(
        self,
        name: str,
        ctx_id: int,
        asn1_cls: type,
        transfer_syntax: str | None = None,
    ) -> PresentaionContextItem:
        """Create and register a new Presentation Context Item.

        :param name: Abstract syntax name (object identifier or string).
        :param ctx_id: Unique Presentation Context Identifier.
        :param asn1_cls: ASN.1 decoding class for user data.
        :param transfer_syntax: Transfer syntax to bind. Defaults to Basic (2.1.1).
        :return: The created context item.
        :rtype: PresentaionContextItem
        """
        item = PresentaionContextItem()
        item.presentation_context_identifier = ctx_id
        item.abstract_syntax_name = name
        item.transfer_syntax_name_list.add(transfer_syntax or TRANSFER_SYNTAX_BASIC)
        self.add(item, asn1_cls)
        return item

    def remove(self, item: PresentaionContextItem) -> None:
        """Remove a Presentation Context Item and its ASN.1 binding."""
        del self.items[item.presentation_context_identifier.value]
        del self.asn1_types[item.presentation_context_identifier.value]


class PresentationRejectedError(ConnectionError):
    """
    Raised when the presentation provider rejects connection establishment.
    """

    def __init__(
        self,
        message: str = "Presentation connection rejected",
        *,
        provider_reason: Any | None = None,
        user_data: Any | None = None,
        context_results: list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_reason = provider_reason
        self.user_data = user_data
        self.context_results = context_results or []


class PresentationAbortError(ConnectionError):
    """
    Raised when the presentation connection is abnormally released.
    """

    def __init__(
        self,
        value: Any | None = None,
        provider: bool = False,
        *,
        provider_reason: Any | None = None,
        event_identifier: Any | None = None,
    ) -> None:
        super().__init__("Presentation connection aborted")
        self.value = value
        self.provider = provider
        self.provider_reason = provider_reason
        self.event_identifier = event_identifier


@dataclass(frozen=True)
class PresentationNegotiatedContext:
    """Presentation context selected into the defined context set."""

    context_id: int
    abstract_syntax_name: str
    transfer_syntax_name: str
    asn1_cls: type


@dataclass(frozen=True)
class PresentationReleaseResult:
    """Result of a presentation release attempt."""

    accepted: bool
    value: Any | None = None
    collision: bool = False


@dataclass(frozen=True)
class PresentationEvent:
    """Parsed presentation data or release event."""

    kind: str
    value: Any | None = None
    accepted: bool | None = None


@dataclass
class ISO_PresentationSettings:
    """Configuration settings for the Presentation layer.

    These settings influence how the Presentation connection (COPP) is
    established, specifically how selectors and protocol versions are
    negotiated.

    :param calling_selector: Local presentation selector, used to identify
        the calling application entity. If ``None``, no selector is included.
    :type calling_selector: bytes | None
    :param called_selector: Remote presentation selector, used to identify
        the destination application entity. If ``None``, no selector is included.
    :type called_selector: bytes | None
    :param use_version1: If ``True``, forces usage of COPP Version 1 semantics.
        If ``False``, negotiates a higher version (default).
    :type use_version1: bool
    :param custom_requirements: Optional presentation requirements to override
        defaults. If ``None``, a default requirements set is used.
    :type custom_requirements: Presentation_requirements | None
    """

    calling_selector: bytes | None = bytes.fromhex("00000001")
    called_selector: bytes | None = bytes.fromhex("00000001")
    use_version1: bool = False
    custom_requirements: Presentation_requirements | None = None


class ISO_Presentation(connection):
    """Client-side driver for the ISO Presentation protocol (X.226 / ISO 8823).

    Sitting directly on top of an :class:`ISO_Session`, this class takes care
    of negotiating presentation contexts and wrapping/unwrapping application
    data so callers can exchange decoded ASN.1 objects instead of raw bytes.
    Connection setup and teardown are driven by exchanging *PPDUs*
    (Presentation Protocol Data Units) with the peer.

    >>> session = ISO_Session(...) # may require COTP_Connection
    >>> presentation = ISO_Presentation(session)

    To make sure your application layer user data is decoded and encoded
    correctly, register a new context id:

    >>> presentation.presentation_context.new("1.2.3", 1, MyASN1Class)
    <Context_list.Member_TYPE>
    >>> presentation.init_session(("127.0.0.1", 1234))
    <MyASN1Class> # depending on server result and ctx_id

    :param session: Underlying ISO Session instance to use for transport.
    :type session: ISO_Session
    :param settings: Optional Presentation settings (selectors, version, requirements).
    :type settings: ISO_PresentationSettings | None
    :param context: Presentation context registry, managing context IDs and
        ASN.1 decoding classes.
    :type context: ISO_PresentationContext | None
    """

    settings: ISO_PresentationSettings
    """Configuration settings for the Presentation layer."""

    def __init__(
        self,
        session: ISO_Session,
        settings: ISO_PresentationSettings | None = None,
        context: ISO_PresentationContext | None = None,
    ):
        super().__init__()
        self.__session: ISO_Session = session
        self.__context: ISO_PresentationContext = context or ISO_PresentationContext()
        self._connected: bool = self.session.is_connected()
        self._valid: bool = self.session.is_valid()
        self.negotiated_contexts: dict[int, PresentationNegotiatedContext] = {}

        # public members
        self.settings = settings or ISO_PresentationSettings()

    @property
    def presentation_context(self) -> ISO_PresentationContext:
        """Registered Presentation Contexts.

        Provides both the raw context items and their ASN.1 decoding bindings.

        :return: The managed Presentation Context registry.
        :rtype: ISO_PresentationContext
        """
        return self.__context

    @property
    def session(self) -> ISO_Session:
        """Underlying Session object providing transport services."""
        return self.__session

    @property
    def transport(self) -> COTP_Connection:
        """Underlying COTP transport connection (OSI transport layer)."""
        return self.session.transport

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """Establish a Presentation connection.

        If already connected, the call is ignored. Otherwise, it delegates
        connection establishment to the Session layer.

        :param address: Network address tuple (host, port).
        :type address: tuple[str, int]
        """
        if self.is_connected():
            return

        self.session.connect(address)
        self._connected = True
        self._valid = False
        self.negotiated_contexts.clear()

    @override
    def close(self) -> None:
        """Close the Presentation connection.

        Delegates closure to the Session layer and marks the Presentation
        context as invalid.
        """
        if self.is_connected():
            self.session.close()
            self._valid = False
            self._connected = False
            self.negotiated_contexts.clear()

    def init_session(self, app_octets: bytes, address: tuple[str, int] | None):
        """Initialize a Presentation session (A-ASSOCIATE equivalent).

        Builds and transmits a *CP PPDU* (Connect Presentation PDU) carrying
        application data, registered presentation contexts, and optional selectors.
        Waits for a *CPA PPDU* (Connect Presentation Accept) in response.

        - Includes all registered Presentation Context Items in negotiation.
        - If ``calling_selector`` or ``called_selector`` are set, they are included
          in the PPDU for AE identification.
        - If ``use_version1`` is ``True``, forces negotiation of COPP v1.
        - If ``custom_requirements`` is provided, overrides default presentation
          requirements.

        :param app_octets: Encoded application-layer data to include in the CP PPDU.
        :type app_octets: bytes
        :param address: Optional address for connection establishment if the
            session is not already connected.
        :type address: tuple[str, int] | None
        :raises ConnectionError: If session initiation fails, invalid CPA received,
            or unsupported mode is negotiated.
        :return: Decoded user data if present in the CPA response, otherwise ``None``.
        :rtype: Any | None
        """
        proposed_contexts = list(self.presentation_context.items.values())
        ppdu = build_connect_ppdu(
            app_octets,
            calling_presentation_selector=self.settings.calling_selector,
            called_presentation_selector=self.settings.called_selector,
            use_version_1=self.settings.use_version1,
            requirements=self.settings.custom_requirements,
            pres_context_items=proposed_contexts,
        )
        pres_octets = ppdu.ber_encode()
        try:
            pres_result = self.session.init_session(pres_octets, address)
        except SessionAbortError as e:
            self._connected = False
            self._valid = False
            self.negotiated_contexts.clear()
            raise self._presentation_abort_error(e.user_data) from e

        self._connected = self.session.is_connected()
        if not pres_result:
            raise ConnectionError("Failed to initiate session, no response received!")

        try:
            cpa_ppdu = CPA_PPDU.ber_decode(pres_result)
        except ValueError:
            return self._decode_connect_reject(pres_result)

        params = cpa_ppdu.normal_mode_parameters
        if params is None:
            raise ConnectionError("Received CPA without normal-mode parameters")

        self._valid = True
        user_data = params.user_data
        if user_data is None:
            return None

        return self._decode_user_data(user_data)

    def _decode_connect_reject(self, pres_result: bytes) -> None:
        try:
            cpr_ppdu = CPR_PPDU.ber_decode(pres_result)
        except ValueError:
            raise ConnectionError(
                f"Received invalid presentation result: {pres_result.hex()}"
            )

        self._connected = False
        self._valid = False
        self.negotiated_contexts.clear()
        params = cpr_ppdu.normal_mode_parameters
        user_data = None
        if params.user_data is not None:
            user_data = self._decode_user_data(params.user_data)

        reason = params.provider_reason
        context_results = []
        result_list = params.presentation_context_definition_result_list
        if result_list is not None:
            context_results = list(
                result_list.value if hasattr(result_list, "value") else result_list
            )

        raise PresentationRejectedError(
            f"Presentation connection rejected: provider_reason={reason}",
            provider_reason=reason,
            user_data=user_data,
            context_results=context_results,
        )

    def _decode_user_data(self, user_data: User_data) -> Any:
        return user_data_get_single_asn1(user_data, context=self._asn1_decode_context())

    def _decode_user_data_octets(self, raw_data: bytes) -> Any:
        try:
            user_data = User_data.ber_decode(raw_data)
        except ValueError:
            raise TypeError(f"Received invalid user data: {raw_data.hex()}")

        return self._decode_user_data(user_data)

    def _asn1_decode_context(self) -> dict[int, type]:
        if not self.negotiated_contexts:
            return self.presentation_context.asn1_types

        return {
            context_id: negotiated.asn1_cls
            for context_id, negotiated in self.negotiated_contexts.items()
        }

    def _presentation_abort_error(
        self, raw_data: bytes | None
    ) -> PresentationAbortError:
        if raw_data is None:
            return PresentationAbortError(provider=True)

        try:
            abort_type = Abort_type.ber_decode(raw_data)
        except ValueError:
            try:
                return PresentationAbortError(
                    self._decode_user_data_octets(raw_data),
                    provider=False,
                )
            except (TypeError, ValueError):
                return PresentationAbortError(provider=True)

        if abort_type.present == Abort_type.PRESENT.PR_aru_ppdu:
            value = None
            params = abort_type.aru_ppdu.normal_mode_parameters
            if params is not None and params.user_data is not None:
                value = self._decode_user_data(params.user_data)
            return PresentationAbortError(value, provider=False)

        if abort_type.present == Abort_type.PRESENT.PR_arp_ppdu:
            arp = abort_type.arp_ppdu
            return PresentationAbortError(
                provider=True,
                provider_reason=(
                    None if arp.provider_reason is None else arp.provider_reason.value
                ),
                event_identifier=(
                    None if arp.event_identifier is None else arp.event_identifier.value
                ),
            )

        return PresentationAbortError(provider=True)

    def _build_context_identifier_list(
        self,
        pres_ctx_id: int,
    ) -> Presentation_context_identifier_list | None:
        negotiated = self.negotiated_contexts.get(pres_ctx_id)
        if negotiated is None:
            return None

        item = Presentation_context_identifier_list.Member_TYPE()
        item.presentation_context_identifier = pres_ctx_id
        item.transfer_syntax_name = negotiated.transfer_syntax_name

        context_list = Presentation_context_identifier_list()
        context_list.add(item)
        return context_list

    def _build_user_abort(
        self, octets: bytes | None = None, pres_ctx_id: int = 1
    ) -> bytes:
        params = ARU_PPDU.normal_mode_parameters_TYPE()
        if octets:
            self._ensure_negotiated_context(pres_ctx_id)
            params.presentation_context_identifier_list = (
                self._build_context_identifier_list(pres_ctx_id)
            )
            params.user_data = build_user_data(octets, pres_ctx_id)

        aru_ppdu = ARU_PPDU(normal_mode_parameters=params)
        return Abort_type(aru_ppdu=aru_ppdu).ber_encode()

    def _build_provider_abort(
        self,
        reason: Abort_reason.VALUES,
        event_identifier: Event_identifier.VALUES,
    ) -> bytes:
        arp_ppdu = ARP_PPDU(
            provider_reason=reason,
            event_identifier=event_identifier,
        )
        return Abort_type(arp_ppdu=arp_ppdu).ber_encode()

    def _abort_protocol_error(
        self,
        reason: Abort_reason.VALUES,
        event_identifier: Event_identifier.VALUES,
    ) -> None:
        abort_data = self._build_provider_abort(reason, event_identifier)
        self.session.abort_session(abort_data)
        self._connected = False
        self._valid = False
        self.negotiated_contexts.clear()

    def _ensure_negotiated_context(self, pres_ctx_id: int) -> None:
        if pres_ctx_id <= 0:
            raise ValueError("Presentation context identifier must be positive")

        if self.negotiated_contexts and pres_ctx_id not in self.negotiated_contexts:
            raise ConnectionStateError(
                f"Presentation context {pres_ctx_id} is not in the DCS"
            )

    def init_x410_session(
        self, user_octets: bytes, address: tuple[str, int] | None
    ) -> bytes:
        """Initialize a presentation session in X.410-1984 pass-through mode."""
        pres_octets = build_x410_user_data(user_octets).ber_encode()
        pres_result = self.session.init_session(pres_octets, address)
        self._connected = self.session.is_connected()
        self._valid = True
        if not pres_result:
            return b""

        try:
            user_data = User_data.ber_decode(pres_result)
        except ValueError:
            return pres_result

        if user_data.present == User_data.PRESENT.PR_simply_encoded_data:
            data = user_data.simply_encoded_data
            return data.value if hasattr(data, "value") else data
        return pres_result

    def close_session(
        self, octets: bytes, pres_ctx_id: int, graceful: bool = False
    ) -> Any | None:
        """Close the Presentation session.

        Sends a *CN/CPA termination sequence* (Finish) via the Session layer,
        optionally embedding user data.

        - If ``pres_ctx_id`` is provided, the user data is bound to the given
          Presentation Context Identifier.
        - If ``graceful`` is ``True``, waits for a *Disconnect* confirmation and
          returns decoded response data.
        - If ``graceful`` is ``False``, closes immediately.

        :param octets: Encoded application user data to include.
        :type octets: bytes
        :param pres_ctx_id: Optional presentation context ID for user data binding.
        :type pres_ctx_id: int | None
        :param graceful: Whether to perform graceful closure with peer acknowledgment.
        :type graceful: bool
        :raises ConnectionStateError: If session has not been initialized.
        :return: Decoded data from peer if ``graceful`` is ``True``.
        :rtype: Any | None
        """
        self._assert_connected()
        if not self._valid:
            raise ConnectionStateError("Session must be initialized before closing")

        result = self.close_session_result(octets, pres_ctx_id, graceful=graceful)
        return None if result is None else result.value

    def close_session_result(
        self, octets: bytes, pres_ctx_id: int, graceful: bool = False
    ) -> PresentationReleaseResult | None:
        """Close the Presentation session and return the release result."""
        self._assert_connected()
        if not self._valid:
            raise ConnectionStateError("Session must be initialized before closing")

        self._ensure_negotiated_context(pres_ctx_id)
        user_data = build_user_data(octets, pres_ctx_id)
        try:
            result = self.session.close_session_result(
                user_data.ber_encode(), graceful=graceful
            )
        except SessionAbortError as e:
            abort_error = self._presentation_abort_error(e.user_data)
            self._connected = False
            self._valid = False
            self.negotiated_contexts.clear()
            raise abort_error from e

        if result is None:
            return None

        value = None
        if result.user_data:
            value = self._decode_user_data_octets(result.user_data)

        if result.accepted:
            self._connected = False
            self._valid = False
            self.negotiated_contexts.clear()

        return PresentationReleaseResult(
            accepted=result.accepted,
            value=value,
            collision=result.collision,
        )

    def abort_session(self, octets: bytes | None = None, pres_ctx_id: int = 1) -> None:
        """Abort the Presentation session with optional user data.

        :param octets: Encoded application user data to include.
        :type octets: bytes | None
        :param pres_ctx_id: Presentation context ID for user data.
        :type pres_ctx_id: int
        """
        self._assert_connected()
        if not self._valid:
            raise ConnectionStateError("Session must be initialized before aborting")

        self.session.abort_session(self._build_user_abort(octets, pres_ctx_id))
        self._connected = False
        self._valid = False
        self.negotiated_contexts.clear()

    @override
    def send_data(self, octets: bytes, /) -> None:
        """Send raw user data.

        Delegates to :meth:`send_encoded_data`.

        :param octets: Encoded user data.
        :type octets: bytes
        """
        self._assert_connected()
        if not self._valid:
            raise ConnectionStateError("Session must be initialized before sending")

        if len(self.negotiated_contexts) != 1:
            raise ConnectionStateError(
                "send_data requires exactly one negotiated presentation context; "
                + "use send_encoded_data()"
            )

        pres_ctx_id = next(iter(self.negotiated_contexts))
        self.send_encoded_data(octets, pres_ctx_id)

    def send_encoded_data(self, octets: bytes, pres_ctx_id: int) -> None:
        """Send BER-encoded user data bound to a Presentation Context Identifier.

        :param octets: User data to encode.
        :type octets: bytes
        :param pres_ctx_id: Optional Presentation Context ID. If omitted, default
            context is used.
        :type pres_ctx_id: int | None
        :raises ConnectionStateError: If not connected.
        """
        self._assert_connected()
        if not self._valid:
            raise ConnectionStateError("Session must be initialized before sending")

        self._ensure_negotiated_context(pres_ctx_id)
        user_data = build_user_data(octets, presentation_context_id=pres_ctx_id)
        self.session.send_data(user_data.ber_encode())

    def send_x410_data(self, octets: bytes) -> None:
        """Send X.410-1984 mode user data without presentation contexts."""
        self._assert_connected()
        self.session.send_data(build_x410_user_data(octets).ber_encode())

    @override
    def recv_data(self) -> bytes:
        """Receive raw user data from the session.

        :return: Raw user data octets.
        :rtype: bytes
        """
        return self.session.recv_data()

    def recv_encoded_data(
        self,
        context: dict[int, type] | None = None,
    ) -> Any | None:
        """Receive and decode Presentation-encoded user data.

        Attempts to decode *User-data* PPDU from the session. If decoding fails,
        raises a type error.

        :param context: Optional decoding context mapping PCI IDs to classes. If
            omitted, the instance's default :attr:`presentation_context.asn1_types` is used.
        :type context: dict[int, type] | None
        :raises ConnectionClosedError: If no data is received (connection closed).
        :raises PresentationAbortError: If the peer aborts the presentation session.
        :raises TypeError: If decoding fails due to invalid BER.
        :return: Decoded ASN.1 object or ``None``.
        :rtype: Any | None
        """
        event = self.recv_event(context=context)
        if event.kind == "data":
            return event.value

        raise ConnectionStateError(f"Received presentation event {event.kind}")

    def recv_x410_data(self) -> bytes:
        """Receive X.410-1984 mode user data without presentation contexts."""
        self._assert_connected()
        raw_data = self.recv_data()
        if not raw_data:
            raise ConnectionClosedError

        user_data = User_data.ber_decode(raw_data)
        if user_data.present != User_data.PRESENT.PR_simply_encoded_data:
            raise TypeError(f"Received invalid X.410 user data: {raw_data.hex()}")
        data = user_data.simply_encoded_data
        return data.value if hasattr(data, "value") else data

    def recv_event(
        self,
        context: dict[int, type] | None = None,
    ) -> PresentationEvent:
        """Receive and classify the next presentation data or release event."""
        self._assert_connected()
        try:
            event = self.session.recv_event()
        except SessionAbortError as e:
            abort_error = self._presentation_abort_error(e.user_data)
            self._connected = False
            self._valid = False
            self.negotiated_contexts.clear()
            raise abort_error from e

        if not event.user_data:
            if event.kind in {"release_request", "release_response"}:
                if event.kind == "release_response" and event.accepted:
                    self._connected = False
                    self._valid = False
                    self.negotiated_contexts.clear()

                return PresentationEvent(
                    kind=event.kind,
                    value=None,
                    accepted=event.accepted,
                )

            raise ConnectionClosedError

        context = context or self._asn1_decode_context()
        try:
            user_data = User_data.ber_decode(event.user_data)
            value = user_data_get_single_asn1(user_data, context=context)
        except (ValueError, TypeError) as e:
            event_identifier = self._abort_event_identifier(event.kind)
            self._abort_protocol_error(
                Abort_reason.VALUES.V_invalid_ppdu_parameter_value,
                event_identifier,
            )
            raise PresentationAbortError(
                provider=True,
                provider_reason=Abort_reason.VALUES.V_invalid_ppdu_parameter_value,
                event_identifier=event_identifier,
            ) from e

        return PresentationEvent(
            kind=event.kind,
            value=value,
            accepted=event.accepted,
        )

    def _abort_event_identifier(self, event_kind: str) -> Event_identifier.VALUES:
        if event_kind == "release_request":
            return Event_identifier.VALUES.V_s_release_indication
        if event_kind == "release_response":
            return Event_identifier.VALUES.V_s_release_confirm
        return Event_identifier.VALUES.V_td_PPDU
