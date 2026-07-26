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
# pyright: reportUnusedCallResult=false
import logging
from argparse import ArgumentParser

from icspacket.core.connection import ConnectionError as ICSConnectionError
from icspacket.proto.opcua.connection import OPCUA_Connection


def init_opcua_connection(
    host: str,
    port: int,
    timeout: float | None = None,
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
) -> OPCUA_Connection | None:
    """
    Initialize and connect an OPC-UA session to a remote peer.

    :param host: Target host, a plain hostname/IP address, or a full
        ``opc.tcp://host:port[/path]`` endpoint URL.
    :type host: str
    :param port: Target TCP port number (ignored if ``host`` is a full URL).
    :type port: int
    :param timeout: Timeout in seconds for OPC-UA service calls, or
        ``None`` for default.
    :type timeout: float | None, optional
    :param username: Optional username for username/password authentication.
    :type username: str | None, optional
    :param password: Optional password for username/password authentication.
    :type password: str | None, optional
    :param security_policy: Secure channel security policy name (see
        :class:`~icspacket.proto.opcua.connection.OPCUA_Connection`).
    :type security_policy: str | None, optional
    :param security_mode: Message security mode, ``"Sign"`` or
        ``"SignAndEncrypt"``.
    :type security_mode: str, optional
    :param certificate: Path to the client's application instance certificate.
    :type certificate: str | None, optional
    :param private_key: Path to the private key matching ``certificate``.
    :type private_key: str | None, optional
    :param private_key_password: Password protecting ``private_key``.
    :type private_key_password: str | None, optional
    :param server_certificate: Expected server certificate, auto-discovered
        via ``GetEndpoints`` when omitted.
    :type server_certificate: str | None, optional
    :param user_certificate: Certificate for X509 user identity token
        authentication (defaults to ``certificate``).
    :type user_certificate: str | None, optional
    :param user_private_key: Private key for ``user_certificate`` (defaults
        to ``private_key``).
    :type user_private_key: str | None, optional
    :param user_private_key_password: Password protecting ``user_private_key``.
    :type user_private_key_password: str | None, optional

    :returns: A connected :class:`OPCUA_Connection` instance on success,
        or ``None`` if the connection failed.
    :rtype: OPCUA_Connection | None

    Example:
    >>> conn = init_opcua_connection("192.168.1.100", 4840)
    >>> if conn:
    ...     print("Connected to OPC-UA peer!")
    """
    address = host if "://" in host else (host, port)
    conn = OPCUA_Connection(
        timeout=timeout or 4.0,
        username=username,
        password=password,
        security_policy=security_policy,
        security_mode=security_mode,
        certificate=certificate,
        private_key=private_key,
        private_key_password=private_key_password,
        server_certificate=server_certificate,
        user_certificate=user_certificate,
        user_private_key=user_private_key,
        user_private_key_password=user_private_key_password,
    )
    logging.info(f"Connecting to OPC-UA peer {host}...")

    try:
        conn.connect(address)
    except ConnectionRefusedError:
        logging.error(f"Failed to connect to {host} (connection refused)")
    except ICSConnectionError as e:
        logging.error("Could not connect to OPC-UA server: %s", e)
    except ConnectionError as e:
        logging.error("Encountered an error while connecting to target: %s", e)
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user")
    else:
        logging.debug(f"Connected to OPC-UA peer at {host}")
        return conn


def add_opcua_connection_options(parser: ArgumentParser) -> None:
    # fmt: off
    # ------------------------------------------------------------------------
    # Authentication options
    # ------------------------------------------------------------------------
    auth_group = parser.add_argument_group("Authentication Options", "Username/password authentication for the OPC-UA session")
    auth_group.add_argument("--username", type=str, default=None, help="Username for username/password authentication")
    auth_group.add_argument("--password", type=str, default=None, help="Password for username/password authentication")

    # ------------------------------------------------------------------------
    # Security options
    # ------------------------------------------------------------------------
    sec_group = parser.add_argument_group("Security Options", "Secure channel encryption and certificate-based user authentication")
    sec_group.add_argument("--security-policy", type=str, choices=["Basic256Sha256", "Aes128Sha256RsaOaep", "Aes256Sha256RsaPss"], default=None, help="Secure channel security policy (default: none, i.e. SecurityPolicy#None)")
    sec_group.add_argument("--security-mode", type=str, choices=["Sign", "SignAndEncrypt"], default="SignAndEncrypt", help="Secure channel message security mode (default: SignAndEncrypt, ignored unless --security-policy is set)")
    sec_group.add_argument("--certificate", type=str, metavar="PATH", default=None, help="Client application instance certificate (PEM/DER), required with --security-policy")
    sec_group.add_argument("--private-key", type=str, metavar="PATH", default=None, help="Private key (PEM/DER) matching --certificate, required with --security-policy")
    sec_group.add_argument("--private-key-password", type=str, default=None, help="Password protecting --private-key, if encrypted")
    sec_group.add_argument("--server-certificate", type=str, metavar="PATH", default=None, help="Expected server certificate (PEM/DER); auto-discovered via GetEndpoints if omitted")
    sec_group.add_argument("--user-certificate", type=str, metavar="PATH", default=None, help="Certificate for X509 user identity token authentication (defaults to --certificate)")
    sec_group.add_argument("--user-private-key", type=str, metavar="PATH", default=None, help="Private key for --user-certificate (defaults to --private-key)")
    sec_group.add_argument("--user-private-key-password", type=str, default=None, help="Password protecting --user-private-key, if encrypted")

    # ------------------------------------------------------------------------
    # Connection options
    # ------------------------------------------------------------------------
    conn_group = parser.add_argument_group("Connection Options", "Specify transport layer settings and target host information")
    conn_group.add_argument("-p", "--port", type=int, help="TCP port of the target OPC-UA server (default: 4840, ignored if host is a full URL)", default=4840)
    conn_group.add_argument("--timeout", type=float, metavar="SEC", help="Timeout in seconds for OPC-UA service calls (default: 4s)", default=4.0)
    conn_group.add_argument("host", type=str, help="Target host (IP address or hostname), or a full opc.tcp:// endpoint URL")
    # fmt: on
