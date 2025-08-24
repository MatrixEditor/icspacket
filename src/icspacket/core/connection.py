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


class ConnectionError(Exception):
    """
    Base exception for all connection-related errors.

    Subclasses provide more specific context, e.g. closed connections
    or invalid states. Intended for use by higher-level protocol
    handlers to unify error handling across different transports.
    """


class ConnectionClosedError(ConnectionError):
    """
    Raised when an operation is attempted on a connection that
    has already been cleanly or forcibly closed.
    """


class ConnectionNotEstablished(ConnectionError):
    """
    Raised when an operation requires an active connection but
    none has been established yet.

    Typically triggered by calling ``send_data()`` or ``recv_data()``
    before ``connect()``.
    """


class ConnectionStateError(ConnectionError):
    """
    Raised when a connection is in an invalid state for the
    requested operation.

    Examples include:
      - Attempting to connect twice without closing.
      - Attempting to reuse a connection marked invalid.
    """


class connection:
    """
    Generic base class for connection-oriented protocols.

    Provides the essential API surface for establishing, validating,
    transmitting, and closing a connection. This base class does not
    assume any particular transport; concrete implementations must
    supply the mechanics (e.g., TCP sockets, serial lines, virtual
    channels).
    """

    def __init__(self):
        self._connected = False
        self._valid = False

    def is_connected(self) -> bool:
        """
        Check if the connection is established.

        :return: ``True`` if the connection is currently open and
                 usable, ``False`` otherwise.
        :rtype: bool
        """
        return self._connected

    def _assert_connected(self) -> None:
        """
        Internal helper to enforce an established connection.

        :raises ConnectionNotEstablished: If no active connection
                                          is present.
        """
        if not self.is_connected():
            raise ConnectionNotEstablished

    def is_valid(self) -> bool:
        """
        Verify whether the connection remains valid.

        This flag is set by subclasses to indicate that the
        underlying transport is still operational. By default
        it returns the internal ``_valid`` attribute.

        :return: ``True`` if the connection is marked valid,
                 ``False`` otherwise.
        :rtype: bool
        """
        return self._valid

    def connect(self, address: tuple[str, int]) -> None:
        """
        Establish the underlying connection.

        Must be overridden by subclasses. Expected to perform
        protocol-specific setup such as TCP handshakes, serial
        port configuration, or security negotiation.

        :param address: Target address or endpoint identifier.
                        Typically a (host, port) tuple for TCP,
                        but may vary by protocol.
        :type address: tuple[str, int]
        :raises ConnectionError: If the connection attempt fails.
        """
        raise NotImplementedError("connect() must be implemented by subclass")

    def close(self) -> None:
        """
        Close the connection and update state.

        Must be overridden by subclasses. Should ensure resources
        are released and internal flags are reset.

        :raises ConnectionError: If closing fails or is unsupported.
        """
        raise NotImplementedError("close() must be implemented by subclass")

    def send_data(self, octets: bytes, /) -> None:
        """
        Send raw data over the connection.

        Must be implemented by subclasses to handle transport-specific
        framing and transmission.

        :param octets: Byte string to send across the connection.
        :type octets: bytes
        :raises ConnectionNotEstablished: If no active connection exists.
        :raises ConnectionClosedError: If the connection was closed
                                       during transmission.
        """
        raise NotImplementedError("send_data() must be implemented by subclass")

    def recv_data(self) -> bytes:
        """
        Receive raw data from the connection.

        Must be implemented by subclasses. Expected to block or wait
        until at least one unit of data is available, depending on
        transport semantics.

        :return: The received octets.
        :rtype: bytes
        :raises ConnectionNotEstablished: If called before connection
                                          setup.
        :raises ConnectionClosedError: If the connection was closed
                                       while awaiting data.
        """
        raise NotImplementedError("recv_data() must be implemented by subclass")
