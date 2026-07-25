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
#   - Reads values from an IEC 60870-5-104 outstation via general
#     interrogation, counter interrogation, or a single read command, and
#     dumps the received ASDUs.
import argparse
import dataclasses
import logging
import sys

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.text import Text
from rich.tree import Tree

from icspacket.core import logger
from icspacket.examples.util import add_logging_options
from icspacket.proto.iec104.asdu import ASDU
from icspacket.proto.iec104.const import (
    IEC104_DEFAULT_PORT,
    QOI,
    CauseOfTransmission,
)
from icspacket.proto.iec104.master import IEC104_Master
from icspacket.proto.iec104.objects.coding import get_asdu_type_desc


def parse_target(target_spec: str) -> tuple[str, int]:
    # format: <host>[:<port>]
    if ":" in target_spec:
        host, port = target_spec.rsplit(":", 1)
        return host, int(port)
    return target_spec, IEC104_DEFAULT_PORT


def cause_name(cause: int) -> str:
    try:
        return CauseOfTransmission(cause).name
    except ValueError:
        return str(cause)


def dump_asdu(asdu: ASDU) -> Tree:
    header = asdu.header
    type_desc = get_asdu_type_desc(header.type_id) or header.type_id.name
    flags: list[str] = []
    if header.cot.test:
        flags.append("TEST")
    if header.cot.negative:
        flags.append("NEGATIVE")
    flags_desc = f" [{', '.join(flags)}]" if flags else ""

    label = (
        f"[b]{type_desc}[/] ({header.type_id.name}={int(header.type_id)}), "
        f"COT={cause_name(header.cot.cause)}{flags_desc}, "
        f"CA={header.common_address}"
    )
    tree = Tree(label)
    highlighter = ReprHighlighter()

    try:
        objects = asdu.decode_objects()
    except Exception as e:
        tree.add(f"[red]Could not decode information objects: {e}[/]")
        return tree

    for obj in objects:
        obj_tree = tree.add(f"IOA={obj.ioa}")
        element = obj.element
        if element is None:
            obj_tree.add("(no payload)")
        elif dataclasses.is_dataclass(element):
            for field in dataclasses.fields(element):
                value = getattr(element, field.name)
                text = Text(f"{field.name}: {value}")
                highlighter.highlight(text)
                obj_tree.add(text)
        else:
            obj_tree.add(str(element))
    return tree


class IEC104Reader:
    def __init__(self, master: IEC104_Master) -> None:
        self.master: IEC104_Master = master
        self.console: Console = Console()

    def run(self, args) -> None:
        if args.read is not None:
            status = f"Reading IOA {args.read} at CA {args.common_address}..."
            with self.console.status(status):
                asdu = self.master.read(
                    args.common_address, args.read, timeout=args.timeout
                )
            self.console.print(dump_asdu(asdu))
            return

        if args.counter_interrogation:
            status = f"Issuing counter interrogation at CA {args.common_address}..."
            with self.console.status(status):
                results = list(
                    self.master.counter_interrogation(
                        args.common_address, timeout=args.timeout
                    )
                )
        else:
            status = f"Issuing general interrogation at CA {args.common_address}..."
            with self.console.status(status):
                results = list(
                    self.master.general_interrogation(
                        args.common_address, qoi=QOI(args.qoi), timeout=args.timeout
                    )
                )

        if not results:
            logging.info("No data returned from outstation")
            return

        for asdu in results:
            self.console.print(dump_asdu(asdu))


def cli_main():
    from icspacket import __version__

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Utility to read data from an outstation using the IEC 60870-5-104 protocol",
    )
    # fmt: off
    group = parser.add_argument_group("Connection Options")
    group.add_argument("-t", "--target", type=str, help=f"Target host (IP address or hostname) to establish the connection (default port is {IEC104_DEFAULT_PORT})", metavar="<host>[:<port>]", required=True)
    group.add_argument("-a", "--common-address", type=int, help="Common Address (CA) of the target station, default is 1", metavar="CA", default=1)
    group.add_argument("--timeout", type=float, metavar="SEC", help="Timeout in seconds for application-layer operations (default: None)", default=None)

    group = parser.add_argument_group("Request Options")
    group.add_argument("-r", "--read", type=int, metavar="IOA", help="Read a single information object by its Information Object Address, instead \nof performing an interrogation", default=None)
    group.add_argument("-ci", "--counter-interrogation", action="store_true", help="Issue a counter interrogation (C_CI_NA_1) instead of a general interrogation", default=False)
    group.add_argument("-qoi", type=int, metavar="QOI", help="Qualifier Of Interrogation for general interrogation, default is 20 (station)", default=int(QOI.STATION))
    # fmt: on
    add_logging_options(parser)

    args = parser.parse_args()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    address = parse_target(args.target)
    master = IEC104_Master()

    try:
        logging.info("Connecting to outstation at %s:%d...", *address)
        master.connect(address)
    except Exception as e:
        logging.error("Could not connect to outstation: %s", e)
        sys.exit(1)
    else:
        logging.debug("Successfully connected to outstation")

    try:
        reader = IEC104Reader(master)
        reader.run(args)
    except KeyboardInterrupt:
        logging.warning("Operation cancelled by user")
    except Exception:
        logging.exception("Encountered an unexpected exception:")
    finally:
        logging.debug("Disconnecting from outstation...")
        master.close()


if __name__ == "__main__":
    cli_main()
