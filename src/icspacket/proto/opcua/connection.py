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
"""\
High-level OPC-UA connection wrapper built on top of :mod:`asyncua`.
"""
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from asyncua import ua
from asyncua.common.subscription import SubEvent
from asyncua.sync import (
    Client as _SyncClient,
)
from asyncua.sync import (
    Subscription,
    SyncNode,
)
from asyncua.sync import (
    Subscription as _SyncSubscription,
)
from asyncua.ua.uaerrors import UaError
from typing_extensions import Self, override

from icspacket.core.connection import (
    ConnectionClosedError,
    ConnectionError,
    ConnectionNotEstablished,
    connection,
)

logger = logging.getLogger(__name__)

__all__ = [
    "BrowseNode",
    "OPCUAProtocolError",
    "OPCUA_Connection",
    "OPCUA_Subscription",
    "discover_endpoints",
]


class OPCUAProtocolError(ConnectionError):
    """
    Raised when an OPC-UA service request fails at the application level.

    This wraps errors reported by :mod:`asyncua` (e.g. ``BadNodeIdUnknown``,
    ``BadUserAccessDenied``) so callers can catch a single icspacket
    exception type regardless of the underlying library.
    """


@dataclass
class BrowseNode:
    """
    A node discovered while browsing an OPC-UA server's address space, as
    returned by :meth:`OPCUA_Connection.browse_details`.

    :ivar node_id: The node's NodeId.
    :vartype node_id: ua.NodeId
    :ivar browse_name: The node's (non-localized) browse name.
    :vartype browse_name: str
    :ivar display_name: The node's human-readable display name.
    :vartype display_name: str
    :ivar node_class: The node's class, e.g. ``Object``, ``Variable`` or
        ``Method``.
    :vartype node_class: ua.NodeClass
    :ivar type_definition: The node's type definition NodeId (e.g. the
        ``VariableType``/``ObjectType`` it was instantiated from), or
        ``None`` if it has none.
    :vartype type_definition: ua.NodeId | None
    :ivar value: The node's current value, if requested via
        ``values=True`` and the node is a ``Variable``. ``None``
        otherwise, or if the value could not be read.
    :vartype value: Any
    :ivar children: Child nodes, populated only when browsed with
        ``recursive=True``.
    :vartype children: list[BrowseNode]
    """

    node_id: ua.NodeId
    browse_name: str
    display_name: str
    node_class: ua.NodeClass
    type_definition: ua.NodeId | None = None
    value: Any = None
    children: list["BrowseNode"] = field(default_factory=list)

    @override
    def __str__(self) -> str:
        label = self.display_name or self.browse_name or self.node_id.to_string()
        text = f"{label} [{self.node_class.name}] ({self.node_id.to_string()})"
        if self.value is not None:
            text += f" = {self.value!r}"
        return text


def _build_endpoint_url(address: tuple[str, int] | str) -> str:
    if isinstance(address, str):
        return address if "://" in address else f"opc.tcp://{address}"

    host, port = address
    return f"opc.tcp://{host}:{port}"


def discover_endpoints(
    address: tuple[str, int] | str, timeout: float = 4.0
) -> list[ua.EndpointDescription]:
    """Discover the endpoints advertised by an OPC-UA server.

    Performs a lightweight, sessionless ``GetEndpoints`` service call:
    no authentication, secure channel security, or application session
    is established. Useful for probing which security policies, modes,
    and user token types a server supports *before* configuring a full
    :class:`OPCUA_Connection`.

    :param address: Either a full ``opc.tcp://host:port[/path]``
        endpoint URL, or a plain ``(host, port)`` tuple.
    :type address: tuple[str, int] | str
    :param timeout: Timeout in seconds for the discovery call.
    :type timeout: float
    :returns: The list of endpoints advertised by the server.
    :rtype: list[ua.EndpointDescription]
    :raises ConnectionError: If the discovery call fails.
    """
    url = _build_endpoint_url(address)
    client = _SyncClient(url, timeout=timeout)
    try:
        return client.connect_and_get_server_endpoints()
    except Exception as e:
        raise ConnectionError(f"Failed to discover endpoints at {url}: {e}") from e
    finally:
        # connect_and_get_server_endpoints() opens and tears down its own
        # secure channel/socket internally, but the sync Client always owns
        # a background ThreadLoop thread (started in __init__) that only
        # stops once disconnect() is called - without this, the thread (and
        # the process) would leak/hang forever.
        try:
            client.disconnect()
        except Exception:
            logger.debug(
                "Cleanup after endpoint discovery raised", exc_info=True
            )


class OPCUA_Connection(connection):
    """
    Synchronous OPC-UA client connection built on :mod:`asyncua`.

    This class provides a thin wrapper around
    :class:`asyncua.sync.Client`, exposing node browsing/read/write as
    simple Python methods.

    Example:

    .. code-block:: python

        conn = OPCUA_Connection()
        conn.connect(("192.168.1.50", 4840))
        value = conn.read_value("ns=2;i=2")
        conn.write_value("ns=2;i=3", "FAULT")
        conn.close()

    .. note::
       NodeId syntax is entirely server-defined: some servers assign
       numeric identifiers (``ns=2;i=2``), others string identifiers
       (``ns=2;s=Device1.Temperature``). Use :meth:`browse` (or
       :func:`discover_endpoints` for a server's security settings) to
       find the actual identifiers exposed by a given server instead of
       assuming either form.

    :param timeout: Timeout in seconds for OPC-UA service calls.
    :type timeout: float
    :param username: Optional username for username/password authentication.
    :type username: str | None
    :param password: Optional password for username/password authentication.
    :type password: str | None
    :param security_policy: Secure channel security policy name, e.g.
        ``"Basic256Sha256"``, ``"Aes128Sha256RsaOaep"`` or
        ``"Aes256Sha256RsaPss"``. ``None`` (the default) disables
        secure channel security entirely (``SecurityPolicy#None``).
    :type security_policy: str | None
    :param security_mode: Message security mode to request, ``"Sign"``
        or ``"SignAndEncrypt"``. Only relevant when ``security_policy``
        is set.
    :type security_mode: str
    :param certificate: Path to the client's application instance
        certificate (PEM/DER), required when ``security_policy`` is set.
    :type certificate: str | None
    :param private_key: Path to the private key matching
        ``certificate``, required when ``security_policy`` is set.
    :type private_key: str | None
    :param private_key_password: Password protecting ``private_key``,
        if it is encrypted.
    :type private_key_password: str | None
    :param server_certificate: Expected server certificate (PEM/DER).
        If omitted, it is auto-discovered via an unauthenticated
        ``GetEndpoints`` call, matching the requested policy/mode.
    :type server_certificate: str | None
    :param user_certificate: Certificate used for X509 user identity
        token authentication (distinct from channel security). Defaults
        to ``certificate`` when unset and ``user_private_key`` is given.
    :type user_certificate: str | None
    :param user_private_key: Private key matching ``user_certificate``.
        Defaults to ``private_key`` when unset.
    :type user_private_key: str | None
    :param user_private_key_password: Password protecting
        ``user_private_key``, if it is encrypted.
    :type user_private_key_password: str | None
    """

    def __init__(
        self,
        timeout: float = 4.0,
        username: str | None = None,
        password: str | None = None,
        security_policy: str | None = None,
        security_mode: str = "SignAndEncrypt",
        certificate: str | None = None,
        private_key: str | None = None,
        private_key_password: str | None = None,
        server_certificate: str | None = None,
        user_certificate: str | None = None,
        user_private_key: str | None = None,
        user_private_key_password: str | None = None,
    ) -> None:
        super().__init__()
        self.timeout: float = timeout
        self.username: str | None = username
        self.password: str | None = password
        self.security_policy: str | None = security_policy
        self.security_mode: str = security_mode
        self.certificate: str | None = certificate
        self.private_key: str | None = private_key
        self.private_key_password: str | None = private_key_password
        self.server_certificate: str | None = server_certificate
        self.user_certificate: str | None = user_certificate
        self.user_private_key: str | None = user_private_key
        self.user_private_key_password: str | None = user_private_key_password
        self._client: _SyncClient | None = None

    @property
    def client(self) -> _SyncClient:
        """The underlying :class:`asyncua.sync.Client` instance."""
        if self._client is None:
            raise ConnectionNotEstablished
        return self._client

    @override
    def connect(self, address: tuple[str, int] | str) -> None:
        """Connect and create a session with an OPC-UA server.

        :param address: Either a full ``opc.tcp://host:port[/path]``
            endpoint URL, or a plain ``(host, port)`` tuple.
        :type address: tuple[str, int] | str
        :raises ConnectionError: If the connection or session creation
            fails, or if the security configuration is incomplete/invalid.
        """
        url = _build_endpoint_url(address)
        client = _SyncClient(url, timeout=self.timeout)
        if self.username is not None:
            client.set_user(self.username)
        if self.password is not None:
            client.set_password(self.password)

        try:
            if self.security_policy is not None:
                self._apply_security(client)
            if self.user_certificate or self.user_private_key:
                self._apply_user_identity(client)

            client.connect()
        except Exception as e:
            # client.connect() may fail after the background ThreadLoop
            # thread (started eagerly in _SyncClient.__init__) is already
            # running, or after a secure channel/session was partially
            # negotiated. disconnect() unconditionally tears down the
            # thread loop (and is safe/idempotent-tolerant on a
            # partially-established client) - without this call, the
            # thread leaks forever and keeps the process alive.
            try:
                client.disconnect()
            except Exception:
                logger.debug(
                    "Cleanup after failed OPC-UA connect raised", exc_info=True
                )
            raise ConnectionError(
                f"Failed to connect to OPC-UA server at {url}: {e}"
            ) from e

        self._client = client
        self._connected: bool = True
        self._valid: bool = True

    def _apply_security(self, client: _SyncClient) -> None:
        """Configure secure channel security (policy/mode/certificates)."""
        if not self.certificate or not self.private_key:
            raise ConnectionError(
                "security_policy requires both certificate and private_key"
            )

        key_part = self.private_key
        if self.private_key_password:
            key_part = f"{self.private_key}::{self.private_key_password}"

        parts = [self.security_policy, self.security_mode, self.certificate, key_part]
        if self.server_certificate:
            parts.append(self.server_certificate)

        try:
            client.set_security_string(",".join(map(str, parts)))
        except UaError as e:
            raise ConnectionError(f"Invalid OPC-UA security configuration: {e}") from e

    def _apply_user_identity(self, client: _SyncClient) -> None:
        """Configure X509 certificate-based user identity token authentication."""
        cert = self.user_certificate or self.certificate
        key = self.user_private_key or self.private_key
        if not cert or not key:
            raise ConnectionError(
                "Certificate-based user authentication requires a "
                + "certificate and private key"
            )

        client.load_client_certificate(cert)
        client.load_private_key(key, password=self.user_private_key_password)

    @override
    def close(self) -> None:
        """Disconnect the OPC-UA session and secure channel.

        Idempotent: calling this more than once, or before a connection
        was ever established, is a no-op.

        :raises ConnectionClosedError: If the underlying client reports
            the connection as already/unexpectedly closed.
        """
        if self._client is not None:
            client, self._client = self._client, None
            self._connected = False
            self._valid = False
            try:
                client.disconnect()
            except RuntimeError as e:
                raise ConnectionClosedError(
                    f"OPC-UA connection was already closed: {e}"
                ) from e

    def get_node(self, node_id: str | ua.NodeId) -> SyncNode:
        """Resolve a node by its NodeId string (e.g. ``ns=2;s=MyVariable``).

        :param node_id: NodeId string or :class:`~asyncua.ua.NodeId` instance.
        :type node_id: str | ua.NodeId
        :returns: The resolved node handle.
        :rtype: SyncNode
        """
        self._assert_connected()
        try:
            return self.client.get_node(node_id)
        except UaError as e:
            raise OPCUAProtocolError(f"Failed to resolve node {node_id!r}: {e}") from e

    def read_value(self, node_id: str | ua.NodeId) -> Any:
        """Read the current value of a node's Value attribute.

        :param node_id: Target node's NodeId.
        :type node_id: str | ua.NodeId
        :returns: The decoded Python value.
        :raises OPCUAProtocolError: If the read service call fails.
        """
        try:
            return self.get_node(node_id).get_value()
        except UaError as e:
            raise OPCUAProtocolError(f"Failed to read node {node_id!r}: {e}") from e

    def write_value(self, node_id: str | ua.NodeId, value: Any) -> None:
        """Write a value to a node's Value attribute.

        :param node_id: Target node's NodeId.
        :type node_id: str | ua.NodeId
        :param value: New value to write (a plain Python value or a
            :class:`~asyncua.ua.Variant`).
        :raises OPCUAProtocolError: If the write service call fails.
        """
        try:
            self.get_node(node_id).set_value(value)
        except UaError as e:
            raise OPCUAProtocolError(f"Failed to write node {node_id!r}: {e}") from e

    def browse(self, node_id: str | ua.NodeId | None = None) -> list[SyncNode]:
        """List the children of a node (or the Objects folder by default).

        :param node_id: NodeId to browse, or ``None`` for the root
            ``Objects`` folder.
        :type node_id: str | ua.NodeId | None
        :returns: Child node handles.
        :rtype: list[SyncNode]
        """
        self._assert_connected()
        node = self.get_node(node_id) if node_id is not None else self.client.get_objects_node()
        try:
            return list(node.get_children())
        except UaError as e:
            raise OPCUAProtocolError(f"Failed to browse node {node_id!r}: {e}") from e

    # REVISIT: must be renamed or moved into client (not a lib function)
    def browse_details(
        self,
        node_id: str | ua.NodeId | None = None,
        *,
        recursive: bool = False,
        max_depth: int = 10,
        values: bool = False,
    ) -> list[BrowseNode]:
        """List a node's children with rich per-node metadata attached.

        Unlike :meth:`browse`, which only returns bare node handles (one
        extra round-trip per child is then needed just to resolve a
        name), this issues a single ``Browse`` service call per level to
        retrieve every child's NodeId, BrowseName, DisplayName,
        NodeClass and TypeDefinition together.

        Example:

        .. code-block:: python

            conn = OPCUA_Connection()
            conn.connect(("192.168.1.50", 4840))
            for child in conn.browse_details(recursive=True, values=True):
                print(child)

        :param node_id: NodeId to browse, or ``None`` for the root
            ``Objects`` folder.
        :type node_id: str | ua.NodeId | None
        :param recursive: If ``True``, also recursively browse every
            discovered child, building a full tree instead of a single
            level. A node reachable via more than one reference path
            (or an outright reference cycle) is only ever expanded once;
            repeat occurrences are still listed, just without children.
        :type recursive: bool
        :param max_depth: Maximum number of levels to descend when
            ``recursive`` is set (ignored otherwise). A server's address
            space can be very large (e.g. the standard ``Server``
            diagnostics subtree), so this bounds a scan's depth by
            default.
        :type max_depth: int
        :param values: If ``True``, also read and attach the current
            value of every ``Variable`` node encountered (one extra
            round-trip per variable). A failed read (e.g. no read
            access) is ignored, leaving :attr:`BrowseNode.value` as
            ``None`` rather than aborting the browse.
        :type values: bool
        :returns: The requested node's children, in server-defined
            order, with ``.children`` populated recursively when
            ``recursive`` is set.
        :rtype: list[BrowseNode]
        :raises OPCUAProtocolError: If browsing fails.
        """
        self._assert_connected()
        root = (
            self.get_node(node_id)
            if node_id is not None
            else self.client.get_objects_node()
        )
        visited: set[str] = {root.nodeid.to_string()}
        return self._browse_details(
            root,
            recursive=recursive,
            max_depth=max_depth,
            values=values,
            visited=visited,
            depth=1,
        )

    def _browse_details(
        self,
        node: SyncNode,
        *,
        recursive: bool,
        max_depth: int,
        values: bool,
        visited: set[str],
        depth: int,
    ) -> list[BrowseNode]:
        try:
            descriptions = node.get_children_descriptions()
        except UaError as e:
            raise OPCUAProtocolError(f"Failed to browse node {node}: {e}") from e

        result: list[BrowseNode] = []
        for description in descriptions:
            node_class = ua.NodeClass(description.NodeClass)
            type_definition = description.TypeDefinition
            entry = BrowseNode(
                node_id=description.NodeId,
                browse_name=description.BrowseName.Name or "",
                display_name=description.DisplayName.Text or "",
                node_class=node_class,
                type_definition=(
                    None if type_definition.is_null() else type_definition
                ),
            )
            if values and node_class == ua.NodeClass.Variable:
                try:
                    entry.value = self.client.get_node(description.NodeId).get_value()
                except UaError:
                    logger.debug(
                        "Failed to read value of %s", description.NodeId,
                        exc_info=True,
                    )

            result.append(entry)

            if recursive and depth < max_depth:
                key = description.NodeId.to_string()
                if key not in visited:
                    visited.add(key)
                    child_node = self.client.get_node(description.NodeId)
                    entry.children = self._browse_details(
                        child_node,
                        recursive=True,
                        max_depth=max_depth,
                        values=values,
                        visited=visited,
                        depth=depth + 1,
                    )

        return result

    def create_subscription(
        self,
        node_ids: Sequence[str | ua.NodeId],
        interval: float = 500.0,
    ) -> "OPCUA_Subscription":
        """Create a data-change subscription for one or more nodes.

        The returned :class:`OPCUA_Subscription` operates in
        "iterator mode": notifications are buffered internally by
        :mod:`asyncua` and retrieved on demand via
        :meth:`OPCUA_Subscription.next_event` or by iterating over it
        directly, rather than via a registered callback handler.

        :param node_ids: One or more NodeIds to monitor for value changes.
        :type node_ids: Sequence[str | ua.NodeId]
        :param interval: Requested publishing interval in milliseconds.
        :type interval: float
        :returns: A handle yielding data-change events as they arrive.
        :rtype: OPCUA_Subscription
        :raises OPCUAProtocolError: If the subscription cannot be created.
        """
        self._assert_connected()
        nodes = [self.get_node(node_id) for node_id in node_ids]
        try:
            sub = self.client.create_subscription(interval, handler=None)
            sub.subscribe_data_change(nodes)
        except UaError as e:
            raise OPCUAProtocolError(f"Failed to create subscription: {e}") from e
        return OPCUA_Subscription(sub)


class OPCUA_Subscription:
    """
    Handle for an active OPC-UA data-change subscription.

    Returned by :meth:`OPCUA_Connection.create_subscription`. Wraps
    :class:`asyncua.sync.Subscription` in iterator mode: no callback
    handler is registered, notifications are buffered internally and
    retrieved on demand.

    Example:

    .. code-block:: python

        sub = conn.create_subscription(["ns=2;i=2", "ns=2;i=3"])
        for event in sub:
            print(event.node, event.value)
        sub.close()

    Also usable as a context manager, which calls :meth:`close` on exit:

    .. code-block:: python

        with conn.create_subscription(["ns=2;i=2"]) as sub:
            event = sub.next_event(timeout=5.0)
    """

    def __init__(self, subscription: _SyncSubscription) -> None:
        self._subscription: Subscription = subscription
        self._closed: bool = False

    def next_event(self, timeout: float | None = None) -> SubEvent | None:
        """Wait for and return the next data-change/event notification.

        :param timeout: Maximum time in seconds to wait, or ``None`` to
            block indefinitely.
        :type timeout: float | None
        :returns: The next event, or ``None`` if ``timeout`` elapsed.
        :rtype: SubEvent | None
        """
        return self._subscription.next_event(timeout=timeout)

    def __iter__(self):
        return iter(self._subscription)

    def close(self) -> None:
        """Delete the subscription on the server and release resources.

        Idempotent: safe to call more than once.
        """
        if not self._closed:
            self._closed = True
            self._subscription.delete()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
