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
from icspacket.proto.cip.connection import CIP_Connection


def init_cip_connection(
    host: str,
    port: int = CIP_Connection.DEFAULT_PORT,
    timeout: float | None = None,
) -> CIP_Connection | None:
    """
    Initialize and connect an EtherNet/IP TCP connection to a remote peer.

    :param host: Target host (IP address or hostname).
    :param port: Target EtherNet/IP TCP port.
    :param timeout: Connection timeout in seconds, or ``None`` for the default.
    :returns: A connected :class:`CIP_Connection`, or ``None`` on failure.
    """
    conn = CIP_Connection(timeout=timeout or 10.0)
    logging.info("Connecting to EtherNet/IP peer %s:%d...", host, port)

    try:
        conn.connect((host, port))
    except ConnectionRefusedError:
        logging.error("Failed to connect to %s with port %d (connection refused)", host, port)
    except ICSConnectionError as exc:
        logging.error("Could not connect to EtherNet/IP server: %s", exc)
    except ConnectionError as exc:
        logging.error("Encountered an error while connecting to target: %s", exc)
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user")
    else:
        logging.debug("Connected to EtherNet/IP peer at %s:%d", host, port)
        return conn
    return None


def add_cip_connection_options(parser: ArgumentParser, *, include_host: bool = True) -> None:
    # fmt: off
    # ------------------------------------------------------------------------
    # Connection options
    # ------------------------------------------------------------------------
    conn_group = parser.add_argument_group(
        "Connection Options",
        "Specify EtherNet/IP transport settings and target host information",
    )
    conn_group.add_argument(
        "-p", "--port", type=int, default=CIP_Connection.DEFAULT_PORT,
        help=f"Port of the target EtherNet/IP server (default: {CIP_Connection.DEFAULT_PORT})",
    )
    conn_group.add_argument(
        "--timeout", type=float, metavar="SEC", default=10.0,
        help="Timeout in seconds for transport-level operations (default: 10s)",
    )
    if include_host:
        add_cip_target_argument(conn_group)
    # fmt: on


def add_cip_target_argument(parser: ArgumentParser) -> None:
    parser.add_argument(
        "host", type=str,
        help="Target host (IP address or hostname) to establish the EtherNet/IP connection",
    )


__all__ = ["add_cip_connection_options", "add_cip_target_argument", "init_cip_connection"]
