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
    CPA_PPDU,
    Mode_selector,
    Presentation_requirements,
    User_data,
    PresentaionContextItem,
)
from icspacket.proto.iso_ses.session import ISO_Session
from icspacket.proto.iso_pres.util import (
    build_connect_ppdu,
    build_user_data,
    user_data_get_single_asn1,
)

TRANSFER_SYNTAX_BASIC = "2.1.1"


class ISO_PresentationContext:
    """Manages Presentation Context Items.

    Each Presentation Context defines how user data is interpreted by
    binding an *abstract syntax* (ASN.1 type) to one or more *transfer syntaxes*.

    This class is used to create, register, and remove contexts, and is
    passed to :class:`ISO_Presentation` to negotiate which contexts are valid
    during association.
    """

    def __init__(self) -> None:
        self.__items = {}
        self.__types = {}

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
        self.items[item.presentation_context_identifier.value] = item
        self.asn1_types[item.presentation_context_identifier.value] = asn1_cls

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

    calling_selector: bytes | None = None
    called_selector: bytes | None = None
    use_version1: bool = False
    custom_requirements: Presentation_requirements | None = None


class ISO_Presentation(connection):
    """Implements the ISO Presentation protocol (X.226 / ISO 8823).

    The Presentation layer sits above the Session layer and provides
    context negotiation and user data encapsulation. It uses *PPDUs*
    (Presentation Protocol Data Units) for connection establishment and
    termination.

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
        self.__session = session
        self.__context = context or ISO_PresentationContext()
        self._connected = self.session.is_connected()
        self._valid = self.session.is_valid()

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
        ppdu = build_connect_ppdu(
            app_octets,
            calling_presentation_selector=self.settings.calling_selector,
            called_presentation_selector=self.settings.called_selector,
            use_version_1=self.settings.use_version1,
            requirements=self.settings.custom_requirements,
            pres_context_items=list(self.presentation_context.items.values()),
        )
        pres_octets = ppdu.ber_encode()
        pres_result = self.session.init_session(pres_octets, address)
        self._connected = self.session.is_connected()
        if not pres_octets:
            raise ConnectionError("Failed to initiate session, no response received!")

        try:
            cpa_ppdu = CPA_PPDU.ber_decode(pres_result)
        except ValueError:
            raise ConnectionError(
                f"Received invalid presentation result: {pres_result.hex()}"
            )

        if (
            cpa_ppdu.mode_selector.mode_value
            != Mode_selector.mode_value_VALUES.V_normal_mode
        ):
            raise ConnectionError(
                f"Unsupported CPA mode: {cpa_ppdu.mode_selector.mode_value}"
            )

        self._valid = True
        user_data = cpa_ppdu.normal_mode_parameters.user_data
        if user_data is None:
            return None

        return user_data_get_single_asn1(
            user_data, context=self.presentation_context.asn1_types
        )

    def close_session(
        self, octets: bytes, pres_ctx_id: int, graceful: bool = False
    ) -> None:
        """Close the Presentation session.

        Sends a *CN/CPA termination sequence* (Finish) via the Session layer,
        optionally embedding user data.

        - If ``pres_ctx_id`` is provided, the user data is bound to the given
          Presentation Context Identifier.
        - If ``graceful`` is ``True``, waits for a *Disconnect* confirmation and
          returns raw response data.
        - If ``graceful`` is ``False``, closes immediately.

        :param octets: Encoded application user data to include.
        :type octets: bytes
        :param pres_ctx_id: Optional presentation context ID for user data binding.
        :type pres_ctx_id: int | None
        :param graceful: Whether to perform graceful closure with peer acknowledgment.
        :type graceful: bool
        :raises ConnectionStateError: If session has not been initialized.
        :return: Raw data from peer if ``graceful`` is ``True``.
        :rtype: bytes | None
        """
        self._assert_connected()
        if not self._valid:
            raise ConnectionStateError("Session must be initialized before closing")

        user_data = build_user_data(octets, pres_ctx_id)
        raw_data = self.session.close_session(user_data.ber_encode(), graceful=graceful)
        if graceful:
            return raw_data

        self._connected = False
        self._valid = False

    @override
    def send_data(self, octets: bytes, /) -> None:
        """Send raw user data.

        Delegates to :meth:`send_encoded_data`.

        :param octets: Encoded user data.
        :type octets: bytes
        """
        self.send_encoded_data(octets, 0)

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
        user_data = build_user_data(octets, presentation_context_id=pres_ctx_id)
        self.session.send_data(user_data.ber_encode())

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
        :raises TypeError: If decoding fails due to invalid BER.
        :return: Decoded ASN.1 object or ``None``.
        :rtype: Any | None
        """
        self._assert_connected()
        raw_data = self.recv_data()
        if not raw_data:
            raise ConnectionClosedError

        try:
            user_data = User_data.ber_decode(raw_data)
        except ValueError:
            raise TypeError(f"Received invalid user data: {raw_data.hex()}")

        context = context or self.presentation_context.asn1_types
        return user_data_get_single_asn1(user_data, context=context)
