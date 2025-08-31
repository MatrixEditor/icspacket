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
# pyright: reportUnusedCallResult=false, reportGeneralTypeIssues=false
#
# Description:
#   - Resolve remote link address using various techniques
__doc__ = """\
Resolve the link address of an outstation using the DNP3 protocol. This small
tool currently tries two methods:

1. Send a REQUEST_LINK_STATUS message to the outstation using the "Self"-address
   and wait for a response. Since the support of the "Self"-address is optional,
   this method may fail.
2. Wait for a REQUEST_LINK_STATUS message from the outstation. Section 9.2.6.5
   REQUEST_LINK_STATUS specifies that the outstation should periodically send
   this request.

Important: Make sure to set the right local link address (default is 1).
Sometimes the outstation will only accepts certain master link addresses.
"""
import logging
import sys
import argparse
from threading import Event
import timeit

from rich.console import Console

from icspacket.core import logger
from icspacket.proto.dnp3.link import LPDU, LinkDirection, LinkPrimaryFunctionCode
from icspacket.proto.dnp3.master import DNP3_Link, DNP3_Master

from icspacket.examples.util import add_logging_options


class CustomDNP3_Link(DNP3_Link):
    def __init__(
        self, src: int, dst: int, sock=None, mode=LinkDirection.MASTER
    ) -> None:
        super().__init__(src, dst, sock, mode)
        self._dst_set = Event()

    def _process_lpdu(self, lpdu: LPDU, raw_octets: bytes) -> bool:
        code = lpdu.control.pri2sec_code
        match code:
            case LinkPrimaryFunctionCode.REQUEST_LINK_STATUS:
                self.destination = lpdu.source
                self._dst_set.set()
        return super()._process_lpdu(lpdu, raw_octets)


def cli_main():
    from icspacket import __version__

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=__doc__)
    # fmt: off
    group = parser.add_argument_group("Connection Options")
    group.add_argument("host", type=str, help="Target host (IP address or hostname) to establish the connection")
    group.add_argument("-p", "--port", type=int, help="Target port (default is 20000)", metavar="PORT", default=20000)
    group.add_argument("-l", "--listen", type=int, help="Local link address to use, default is 1", metavar="LINK_ADDR", default=1)

    group = parser.add_argument_group("Resolution Options")
    group.add_argument("-no-self", action="store_true", help="Do not resolve remote link address using the 'self' address method")
    group.add_argument("-interval", type=float, metavar="S", help="Maximum polling interval of the outstation in milliseconds (default is 60s)", default=60.0)
    # fmt: on
    add_logging_options(parser)

    args = parser.parse_args()
    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    master = DNP3_Master(link_addr=args.listen)
    # as we don't know the outstation's link address, we can't it here
    remote_addr = (0, args.host, args.port)
    try:
        logging.info("Connecting to outstation (%04d) at %s:%d...", *remote_addr)
        master.associate(remote_addr, link_cls=CustomDNP3_Link)
    except ConnectionError as e:
        logging.error("Could not connect to outstation: %s", e)
        sys.exit(1)
    else:
        logging.debug("Successfully connected to outstation (%04d)", remote_addr[0])

    console = Console()
    link: CustomDNP3_Link = master.transport.link
    # 9.2.5.2.2 Self-address
    # Address 0xFFFC is called the “Self-address,” and it shall only appear in
    # the destination address field. Support for it is optional. Devices that
    # support this address, and have the self-address feature enabled, shall
    # process frames with destination address 0xFFFC as if the message had used
    # the device's unique individual address.
    if args.no_self:
        logging.info("Skipping self-address method")
    else:
        link.sock.settimeout(2)  # should be returned immediately
        logging.info(
            "Attempting to resolve remote link address using self-address method..."
        )

        link.destination = 0xFFFC
        lpdu = LPDU()
        lpdu.control.function_code = LinkPrimaryFunctionCode.REQUEST_LINK_STATUS
        lpdu.control.direction = LinkDirection.MASTER
        lpdu.control.primary_message = True
        link.send_lpdu(lpdu)  # source and will be populated here

        try:
            with console.status("Waiting for reply..."):
                lpdu = link.recv_lpdu()
        except TimeoutError:
            logging.warning("No response received - skipping self-address method")
        except KeyboardInterrupt:
            logging.error("Aborted")
            sys.exit(1)
        else:
            logging.info("Remote link address: %#04x", lpdu.source)
            sys.exit(0)

    # 9.2.6.5 Function code 9 - REQUEST_LINK_STATUS
    # When DNP3 is transported over a Network Connection Management Layer, the
    # REQUEST_LINK_STATUS function shall be periodically transmitted by both the
    # Master Station and the Outstation to verify that the connection is online
    # and active.
    link.sock.settimeout(args.interval)
    start = timeit.default_timer()
    try:
        with console.status(f"Waiting for link status ({args.interval:.2f}s)..."):
            while not link._dst_set.is_set():
                _ = link.recv_lpdu()
    except TimeoutError:
        pass
    except KeyboardInterrupt:
        logging.error("Aborted")
        sys.exit(1)

    remote_link_addr = link.destination
    if remote_link_addr in (0, 0xFFFC):
        logging.error("Could not resolve remote link address")
        sys.exit(1)

    end = timeit.default_timer()
    logging.debug("Received response after %.2fs", (end - start) * 1000000)
    logging.info(
        f"Received message from outstation with address: [b]{remote_link_addr}[/] ({remote_link_addr:#06x})"
    )


if __name__ == "__main__":
    cli_main()
