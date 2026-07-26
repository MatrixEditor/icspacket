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
from icspacket.proto.bacnet.connection import BACnet_Connection


def init_bacnet_connection(
    address: str | None,
    name: str,
    instance: int,
    network: int,
    vendor_identifier: int,
    foreign_bbmd: str | None,
    foreign_ttl: int,
    bbmd_bdt: list[str] | None,
    timeout: float,
) -> BACnet_Connection | None:
    """
    Initialize and bind a local BACnet/IP endpoint.

    :param address: Local bind address in ``host[/prefixlen]`` form, or
        ``None`` for BACpypes3's default address resolution.
    :type address: str | None
    :param name: Local device object name.
    :type name: str
    :param instance: Local device object instance number.
    :type instance: int
    :param network: Local BACnet network number, or ``0`` if unknown.
    :type network: int
    :param vendor_identifier: BACnet vendor identifier to advertise.
    :type vendor_identifier: int
    :param foreign_bbmd: Address of a remote BBMD to register with as a
        foreign device, or ``None`` to disable.
    :type foreign_bbmd: str | None
    :param foreign_ttl: Foreign device registration time-to-live in
        seconds.
    :type foreign_ttl: int
    :param bbmd_bdt: Broadcast Distribution Table entries to configure if
        acting as a BBMD, or ``None``.
    :type bbmd_bdt: list[str] | None
    :param timeout: Default timeout in seconds for BACnet service calls.
    :type timeout: float

    :returns: A connected :class:`BACnet_Connection` instance on success,
        or ``None`` if binding the local endpoint failed.
    :rtype: BACnet_Connection | None
    """
    conn = BACnet_Connection(
        name=name,
        instance=instance,
        network=network,
        vendor_identifier=vendor_identifier,
        foreign_bbmd=foreign_bbmd,
        foreign_ttl=foreign_ttl,
        bbmd_bdt=bbmd_bdt,
        timeout=timeout,
    )
    logging.info(
        "Binding local BACnet/IP endpoint (%s, device %d)...",
        address or "auto-detected address",
        instance,
    )

    try:
        conn.connect(address)
    except ICSConnectionError as e:
        logging.error("Could not bind local BACnet endpoint: %s", e)
    except ConnectionError as e:
        logging.error("Encountered an error while binding local endpoint: %s", e)
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user")
    else:
        logging.debug("Local BACnet/IP endpoint bound (device %d)", instance)
        return conn


def add_bacnet_connection_options(parser: ArgumentParser) -> None:
    # fmt: off
    # ------------------------------------------------------------------------
    # Connection options
    # ------------------------------------------------------------------------
    conn_group = parser.add_argument_group("Connection Options", "Configure the local BACnet/IP device endpoint")
    conn_group.add_argument("-a", "--address", default=None, metavar="ADDR", help="Local bind address in host[/prefixlen] form, e.g. 192.168.1.50/24 (default: auto-detect)")
    conn_group.add_argument("--name", default="icspacket", help="Local device object name (default: icspacket)")
    conn_group.add_argument("--instance", type=int, default=999, metavar="ID", help="Local device object instance number (default: 999)")
    conn_group.add_argument("--network", type=int, default=0, metavar="NUM", help="Local BACnet network number (default: 0/unknown)")
    conn_group.add_argument("--vendor-id", type=int, dest="vendor_identifier", default=999, metavar="ID", help="BACnet vendor identifier to advertise (default: 999)")
    conn_group.add_argument("--foreign", dest="foreign_bbmd", default=None, metavar="BBMD", help="Register as a foreign device with this remote BBMD address")
    conn_group.add_argument("--foreign-ttl", type=int, default=30, metavar="SEC", help="Foreign device registration time-to-live in seconds (default: 30)")
    conn_group.add_argument("--bbmd", dest="bbmd_bdt", nargs="+", default=None, metavar="ENTRY", help="Act as a BBMD with these Broadcast Distribution Table entries")
    conn_group.add_argument("--timeout", type=float, default=4.0, metavar="SEC", help="Default timeout in seconds for BACnet service calls (default: 4.0)")
    # fmt: on
