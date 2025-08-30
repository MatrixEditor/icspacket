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
#   - Reads values from an outstation
import logging
import sys
import argparse
import textwrap

from rich.console import Console

from icspacket.core import logger
from icspacket.proto.dnp3.const import FunctionCode
from icspacket.proto.dnp3.master import DNP3_Master
from icspacket.proto.dnp3.objects.coding import unpack_objects
from icspacket.proto.dnp3.objects.util import new_class_data_request, as_variation0

from icspacket.examples.util import add_logging_options
from icspacket.examples.dnp3dump import dump_objects
from icspacket.proto.dnp3.objects.variations import get_group_name


def parse_target(target_spec: str) -> tuple[int, str, int] | None:
    # format: <link_addr>@<host>[:<port>]
    if "@" not in target_spec:
        return logging.error(
            "Invalid target specification: %s, expected <link_addr>@<host>[:<port>]",
            target_spec,
        )

    link_addr, target_spec = target_spec.split("@", 1)
    if ":" in target_spec:
        host, port = target_spec.split(":", 1)
    else:
        host = target_spec
        port = 20000
    return int(link_addr), host, int(port)


class DNP3Reader:
    def __init__(self, master: DNP3_Master) -> None:
        self.master = master
        self.console = Console()

    def run(self, args):
        classes = []
        if args.class0 or args.all_classes:
            classes.append(0)
        if args.class1 or args.all_classes:
            classes.append(1)
        if args.class2 or args.all_classes:
            classes.append(2)
        if args.class3 or args.all_classes:
            classes.append(3)

        if args.group is not None and len(classes) > 0:
            logging.warning(
                "Group and class options are mutually exclusive, ignoring class options"
            )

        if args.group is not None:
            group = get_group_name(args.group)
            group = (
                f"[b]{group}[/] ({args.group})"
                if group is not None
                else str(args.group)
            )

            objects = as_variation0(args.group)
            status = f"Reading data objects from group {group}..."
        else:
            if len(classes) == 0:
                logging.error("No classes specified")
                return

            objects = new_class_data_request(*classes)
            status = f"Reading data objects from classes {tuple(classes)}..."

        with self.console.status(status):
            apdu = self.master.request(FunctionCode.READ, objects)

        if apdu is None:
            logging.error("No response from outstation")
            return

        logging.debug(
            "Received response from outstation with code %s", apdu.function.name
        )
        if apdu.iin is not None:
            if apdu.iin.no_func_code_support:
                return logging.error(
                    "Outstation does not support function code %s",
                    FunctionCode.READ,
                )

        raw_objects = apdu.objects
        if not raw_objects:
            logging.info("No data returned from outstation")
            return

        try:
            objects = unpack_objects(apdu.objects)
            tree = dump_objects(objects)
            self.console.print(tree)
        except Exception as e:
            return logging.error("Failed to unpack objects: %s", e)


def cli_main():
    from icspacket import __version__

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    # fmt: off
    group = parser.add_argument_group("Connection Options")
    group.add_argument("-t", "--target", type=str, help="Target host (IP address or hostname) to establish the connection (default port is 20000)", metavar="<link_addr>@<host>[:<port>]", required=True)
    group.add_argument("-l", "--listen", type=int, help="Local link address to use, default is 1", metavar="LINK_ADDR", default=1)
    group.add_argument("--timeout", type=float, metavar="SEC", help="Timeout in seconds for link-level operations (default: None)", default=None)

    group = parser.add_argument_group("Request Options")
    group.add_argument("-G", "--group", type=int, help="DNP3 object group number", metavar="ID")
    class0_groups = """\
        Group         Description
        -----         -----------
        1             Binary Input
        3             Double-bit Binary Input
        10            Binary Output Status
        20            Counter
        21            Frozen Counter
        30            Analog Input
        31            Frozen Analog Input
        40            Analog Output Status
        87            Data Set
        101           Binary-Coded Dec imal Integer
        102           Unsigned Integer—8-bit
        110           Octet String
        121           Security Statistics
    """
    group.add_argument("-class0", action="store_true", help=f"Request class 0 objects. The outstation will include some or all of the \nfollowing objects in its response:\n{textwrap.dedent(class0_groups)}\n", default=False)
    class1_groups = """\
        Group         Description
        -----         -----------
        2             Binary Input Event
        4             Double-bit Binary Input Event
        11            Binary Output Event
        13            Binary Output Command Event
        22            Counter Event
        23            Frozen Counter Event
        32            Analog Input Event
        33            Frozen Analog Input Event
        42            Analog Output Event
        43            Analog Output Command Event
        70            File Transfer
        88            Data Set Event
        111           Octet String Event
        113           Virtual Terminal Event
        120           Authentication
        122           Security Statistics Event
    """
    group.add_argument("-class1", action="store_true", help=f"Request class 1 objects. The response will include none (null response), some, \nor all of the following objects:\n{textwrap.dedent(class1_groups)}\n", default=False)
    class2_groups = """-- same as class 1 --"""
    group.add_argument("-class2", action="store_true", help=f"Request class 2 objects. The response will include none (null response), \nsome, or all of the following objects:\n{textwrap.dedent(class2_groups)}", default=False)
    class3_groups = """-- same as class 1 --"""
    group.add_argument("-class3", action="store_true", help=f"Request class 3 objects. The response will include none (null response), \nsome, or all of the following objects:\n{textwrap.dedent(class3_groups)}", default=False)
    group.add_argument("--all-classes", action="store_true", help="Request objects from all classes", default=False)
    # fmt: on
    add_logging_options(parser)

    args = parser.parse_args()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    master = DNP3_Master(link_addr=args.listen)
    remote_addr = parse_target(args.target)
    if remote_addr is None:
        sys.exit(1)

    try:
        logging.info("Connecting to outstation (%04d) at %s:%d...", *remote_addr)
        master.associate(remote_addr)
        master.transport.link.sock.settimeout(args.timeout)
    except ConnectionError as e:
        logging.error("Could not connect to outstation: %s", e)
        sys.exit(1)
    else:
        logging.debug("Successfully connected to outstation (%04d)", remote_addr[0])

    try:
        reader = DNP3Reader(master)
        reader.run(args)
    except KeyboardInterrupt:
        logging.warning("Operation cancelled by user")
    except Exception as e:
        logging.exception("Encountered an unexpected exception:", e)
    finally:
        logging.debug("Disconnecting from outstation...")
        master.release(0.1)


if __name__ == "__main__":
    cli_main()
