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

from icspacket.proto.modbus.connection import Modbus_Connection

from icspacket.core.connection import ConnectionError as ICSConnectionError


def init_modbus_connection(
    host: str,
    port: int,
    unit_id: int,
    timeout: float | None = None,
    transport: str = "tcp",
) -> Modbus_Connection | None:
    """
    Initialize and connect a Modbus TCP/UDP connection to a remote peer.

    :param host: Target host (IP address or hostname).
    :type host: str
    :param port: Target port number.
    :type port: int
    :param unit_id: Default Modbus unit/slave identifier for requests.
    :type unit_id: int
    :param timeout: Connection timeout in seconds, or ``None`` for default.
    :type timeout: float | None, optional
    :param transport: Transport protocol, either ``"tcp"`` (default) or
        ``"udp"``.
    :type transport: str, optional

    :returns: A connected :class:`Modbus_Connection` instance on success,
        or ``None`` if the connection failed.
    :rtype: Modbus_Connection | None

    Example:
    >>> conn = init_modbus_connection("192.168.1.100", 502, unit_id=1)
    >>> if conn:
    ...     print("Connected to Modbus peer!")
    """
    conn = Modbus_Connection(unit_id=unit_id, timeout=timeout or 10.0, transport=transport)
    logging.info(
        f"Connecting to Modbus peer {host}:{port} (unit {unit_id}, {transport.upper()})..."
    )

    try:
        conn.connect((host, port))
    except ConnectionRefusedError:
        logging.error(
            f"Failed to connect to {host} with port {port} (connection refused)"
        )
    except ICSConnectionError as e:
        logging.error("Could not connect to Modbus server: %s", e)
    except ConnectionError as e:
        logging.error("Encountered an error while connecting to target: %s", e)
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user")
    else:
        logging.debug(f"Connected to Modbus peer at {host}:{port}")
        return conn


def add_modbus_connection_options(parser: ArgumentParser) -> None:
    # fmt: off
    # ------------------------------------------------------------------------
    # Connection options
    # ------------------------------------------------------------------------
    conn_group = parser.add_argument_group("Connection Options", "Specify transport layer settings and target host information")
    conn_group.add_argument("--udp", dest="transport", action="store_const", const="udp", default="tcp", help="Use Modbus/UDP instead of Modbus/TCP")
    conn_group.add_argument("-p", "--port", type=int, help="Port of the target Modbus server (default: 502)", default=502)
    conn_group.add_argument("-u", "--unit", type=int, metavar="ID", help="Modbus unit/slave identifier (default: 1)", default=1)
    conn_group.add_argument("--timeout", type=float, metavar="SEC", help="Timeout in seconds for transport-level operations (default: 10s)", default=10.0)
    conn_group.add_argument("host", type=str, help="Target host (IP address or hostname) to establish the Modbus connection")
    # fmt: on
