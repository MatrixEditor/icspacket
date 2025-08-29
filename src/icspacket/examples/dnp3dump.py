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
#   - Simple utility to display the contents of DNP3 data objects within a
#     packet.
import logging
import pathlib
import sys


from rich.console import Console
from rich.tree import Tree
from rich.highlighter import ReprHighlighter
from rich.text import Text

from icspacket.core import hexdump
from icspacket.examples.util import add_logging_options
from icspacket.proto.dnp3.application import APDU
from icspacket.proto.dnp3.link import LPDU
from icspacket.proto.dnp3.objects.coding import DNP3Objects, unpack_objects
from icspacket.proto.dnp3.objects.variations import (
    get_group_name,
    get_variation,
    get_variation_desc,
)


def dump_objects(objects: DNP3Objects) -> Tree:
    tree = Tree("Data Objects:")
    highlighter = ReprHighlighter()
    for group_id, variations in objects.items():
        group_name = get_group_name(group_id)
        for variation_id, values in variations.items():
            label = (
                f"Object(s): [b]{group_name}[/] (Obj: {group_id}, Var: {variation_id})"
            )
            variation = get_variation(group_id, variation_id)
            if values is not None:
                if isinstance(values.range, list):
                    label = f"{label} [Range: {values.range[0]}-{values.range[1] + 1}]"
                else:
                    label = f"{label} [Count: {values.range}]"
                subtree = tree.add(label)
                obj_name = get_variation_desc(group_id, variation_id).split(" - ")[-1]
                if not variation.is_packed:
                    for obj in values:
                        label = f"{obj_name} [{obj.index}]: "
                        if obj.prefix is not None:
                            label += f"(prefix: {obj.prefix}) "
                        instance = obj.instance
                        if isinstance(instance, (int, str, bytes)):
                            if type(instance) == bytes:
                                # dump bytes as hexdump
                                dump = hexdump.hexdump(instance)
                                instance = f"\n{dump}"

                            subtree.add(f"{label}{instance}")
                        else:
                            obj_tree = subtree.add(label)
                            for field in dir(instance):
                                if field.startswith("_"):
                                    continue
                                value = getattr(instance, field)
                                text = Text(f"{field}: {value}")
                                highlighter.highlight(text)
                                if value is not None:
                                    obj_tree.add(text)
                else:
                    if isinstance(values.range, list):
                        for i in range(values.range[0], values.range[1] + 1):
                            label = f"{obj_name} [{i}]: {values[i].instance}"
                            subtree.add(label)
                    else:
                        label = f"{obj_name}: 0b" + "".join(
                            map(lambda o: str(o.instance), values)
                        )
                        subtree.add(label)
            else:
                tree.add(f"{label} (Empty)")
    return tree


def cli_main():
    import argparse

    from icspacket import __version__
    from icspacket.core import logger

    def hexorfile(value: str) -> bytes:
        try:
            return bytes.fromhex(value)
        except ValueError:
            return pathlib.Path(value).read_bytes()

    parser = argparse.ArgumentParser()
    # fmt: off
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-apdu", type=hexorfile, default=None, help="Complete APDU (Application Layer) protocol data as hex string or file", metavar="<HEX|FILE>")
    group.add_argument("-lpdu", type=hexorfile, default=None, help="Complete LPDU (Link Layer) protocol data as hex string or file", metavar="<HEX|FILE>")
    group.add_argument("-objects", type=hexorfile, default=None, help="Raw object data as hex string or file", metavar="<HEX|FILE>")

    group = parser.add_argument_group("Output Options")
    group.add_argument("-dict", action="store_true", help="Print DNP3 object dictionary", default=False)
    # fmt: on

    add_logging_options(parser)

    args = parser.parse_args()
    if not args.apdu and not args.lpdu and not args.objects:
        parser.error("Either -apdu or -lpdu or -objects must be specified")

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    console = Console()
    apdu_raw = args.apdu
    if args.lpdu and not args.objects:
        try:
            lpdu = LPDU.from_octets(args.lpdu)
        except Exception as e:
            logging.error(
                "Could not parse LPDU: %s\n%s", str(e), hexdump.hexdump(args.lpdu)
            )
            sys.exit(1)

        control = []
        control.append(lpdu.control.direction.name)
        code = None
        if lpdu.control.primary_message:
            control.append("PRM")
            code = lpdu.control.pri2sec_code
        else:
            code = lpdu.control.sec2pri_code

        logging.info(
            "Parsed %s (%d) LPDU (%s) from: %#06x, to: %#06x",
            code.name,
            code.value,
            ", ".join(control),
            lpdu.source,
            lpdu.destination,
        )

        apdu_raw = lpdu.tpdu.app_fragment
        if not lpdu.tpdu.final_segment or not lpdu.tpdu.first_segment:
            logging.warning(
                "LPDU contains an APDU that was sent in multiple fragments. "
                + "Multiple fragments are not supported yet!"
            )

    if not args.objects:
        try:
            apdu = APDU.from_octets(apdu_raw)
        except Exception as e:
            logging.exception(
                "Could not parse APDU: %s\n%s", str(e), hexdump.hexdump(apdu_raw)
            )
            sys.exit(1)

        control = []
        if apdu.control.first_fragment:
            control.append("FIR")
        if apdu.control.final_fragment:
            control.append("FIN")
        if apdu.control.need_confirmation:
            control.append("CON")
        if apdu.control.unsolicited_response:
            control.append("UNS")

        logging.info(
            "Parsed %s (%d) APDU (%s), SEQ: %d",
            apdu.function.name,
            apdu.function.value,
            ", ".join(control),
            apdu.control.sequence,
        )
        if not apdu.control.final_fragment or not apdu.control.first_fragment:
            logging.warning("Multiple fragments not supported yet!")
            sys.exit(1)

        if apdu.iin is not None:
            tree = Tree("Internal Indications (IIN):")
            for attr, name in [
                ("device_restart", "Device Restart"),
                ("device_trouble", "Device Trouble"),
                ("local_control", "Some Output Points are in local mode"),
                ("need_time", "Time Synchronization Required"),
                ("class_3_events", "Additional Class 3 Event Data is available"),
                ("class_2_events", "Additional Class 2 Event Data is available"),
                ("class_1_events", "Additional Class 1 Event Data is available"),
                ("broadcast", "Broadcast Message Received"),
                ("config_corrupt", "Configuration Corrupt"),
                ("already_executing", "Operation is already executing"),
                ("event_buffer_overflow", "Event Buffer Overflow"),
                ("parameter_error", "Parameter Error"),
                ("object_unknown", "Object Unknown"),
                ("no_func_code_support", "Function Code not implemented"),
            ]:
                if getattr(apdu.iin, attr):
                    tree.add(name)

            if len(tree.children) > 0:
                console.print(tree, "")
            else:
                logging.info("No Internal Indications (IIN)")
        else:
            logging.info("No Internal Indications (IIN)")

    raw_objects = args.objects or apdu.objects
    if raw_objects:
        try:
            objects = unpack_objects(raw_objects)
        except Exception as e:
            logging.error("Could not parse objects: %s", str(e))
            sys.exit(1)

        if args.dict:
            console.print(objects)
        else:
            tree = dump_objects(objects)
            console.print(tree)
    else:
        logging.info("No Data Object(s)")


if __name__ == "__main__":
    cli_main()
