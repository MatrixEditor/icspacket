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
import argparse
import logging
import sys


from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.text import Text
from rich.tree import Tree
from rich.live import Live
from rich.prompt import Prompt
from rich.markup import escape

from icspacket.core import logger
from icspacket.examples.util import add_logging_options
from icspacket.proto.iec61850.client import IED_Client
from icspacket.examples.util.mms import (
    add_mms_connection_options,
    init_mms_connection,
)
from icspacket.core import hexdump
from icspacket.proto.iec61850.classes import FC, DATA_Class
from icspacket.proto.iec61850.path import ObjectReference
from icspacket.proto.mms.asn1types import Data
from icspacket.proto.mms.exceptions import MMSConnectionError
from icspacket.proto.mms.data import get_floating_point_value
from icspacket.proto.mms.util import (
    BasicObjectClassType,
    ObjectScope,
    basic_object_class,
)


class IED_Discover:
    def __init__(self, client: IED_Client, args) -> None:
        self.client = client
        self.list_output = args.list
        self.device = args.device
        self.nodes: list[str] = []
        self.datasets = []
        self.console = Console()
        self.with_values = args.values
        self.no_path = args.no_path
        self.max_depth = args.maxdepth if args.maxdepth is not None else 100
        if args.node:
            self.nodes.append(args.node)

    def discover(self) -> None:
        logging.debug("Using logical device: %s", self.device)
        if len(self.nodes) == 0:
            with self.console.status("Enumerating logical nodes..."):
                nodes = self.client.mms_conn.get_name_list(
                    basic_object_class(BasicObjectClassType.V_namedVariable),
                    ObjectScope(domainSpecific=self.device),
                )
                self.nodes.extend(nodes)
        else:
            with self.console.status("Enumerating logical nodes..."):
                nodes = self.client.get_logical_node_directory(
                    ObjectReference(self.device, self.nodes[0])
                )
                self.nodes.extend(["$".join(node.parts[1:]) for node in nodes])

        try:
            nodes = self.client.mms_conn.get_name_list(
                basic_object_class(BasicObjectClassType.V_namedVariableList),
                ObjectScope(domainSpecific=self.device),
            )
            if nodes:
                for node in nodes:
                    ref = ObjectReference.from_mmsref(f"{self.device}/{node}")
                    if ref.lnname not in self.datasets:
                        self.datasets.append(ref.lnname)
                    self.datasets.append("$".join(ref.parts[1:]))
        except MMSConnectionError:
            pass

        if self.list_output:
            nodes = set(self.nodes + self.datasets)
            for node in sorted(nodes):
                ref = ObjectReference.from_mmsref(f"{self.device}/{node}")
                print(ref)
            return

        root = Tree(f"Logical nodes of [b]{self.device}[/]")
        with Live(root, vertical_overflow="visible", console=self.console):
            if len(self.nodes) > 0:
                tree = root.add("[b]DATA[/]")
                self.dump_nodes(tree, self.nodes)

            if len(self.datasets) > 0:
                tree = root.add("[b]DATA SET[/]")
                self.dump_nodes(tree, self.datasets, is_data=False)

    def dump_nodes(self, tree: Tree, nodes: list[str], is_data: bool = True):
        # Map each already-rendered node's full "$"-separated path to its
        # rich Tree node, so children can always look up their real parent
        # by path instead of relying on positional/depth bookkeeping (which
        # breaks if the server does not return entries strictly grouped by
        # logical node, e.g. interleaved dataset/RCB names across LNs).
        subtrees: dict[str, Tree] = {}
        for node in nodes:
            node_ref = ObjectReference.from_mmsref(f"{self.device}/{node}")
            if "$" not in node:
                label = str(node_ref.lnname)
                ln_class = node_ref.lnclass
                if ln_class:
                    label = f"{label} ({ln_class.value})"

                if not self.no_path:
                    label = label.ljust(100 - 8, ".")
                    label = f"{label} {node_ref}"

                subtrees[node] = tree.add(label)
                continue

            depth = node.count("$")
            if depth > self.max_depth:
                continue

            parent_key = node.rsplit("$", 1)[0]
            parent = subtrees.get(parent_key)
            if parent is None:
                logging.warning(
                    "Skipping node %r: parent node %r was not discovered",
                    node,
                    parent_key,
                )
                continue

            if depth == 1 and is_data:
                try:
                    fc = FC[node_ref.name(2)]
                    label = f"[{fc.name}] ({fc.value})"
                except KeyError:
                    label = f"[{node_ref.name(2)}] (unknown FC)"
                subtrees[node] = parent.add(label)
                continue
            else:
                name = node_ref.name(-1)
                label = f"{name} "
                if node.count("$") == 2 and is_data:
                    # try to resolve data class
                    data_class = DATA_Class.from_name(name)
                    if data_class:
                        label = f"{label}({data_class.value}) "

                if not self.no_path:
                    label = label.ljust(100 - (4 * (depth + 2)), ".")
                    label = f"{label} {node_ref}"

                text = Text(label)

                value = (
                    self.get_node_value(node_ref)
                    if is_data and self.with_values
                    else None
                )

                if value is not None:
                    text = text.append("\n").append(value)
                subtrees[node] = parent.add(text)

    def get_node_value(self, node_ref: ObjectReference) -> Text | None:
        if len(node_ref.parts) < 4:
            return None
        try:
            value = self.client.get_data_values(node_ref)
        except MMSConnectionError:
            return None

        data = value.success
        if data is None:
            return None

        highlighter = ReprHighlighter()
        text = Text()
        text.append(f"({data.present.name[3:].lower()})").append(": ")
        do_highlight = True
        match data.present:
            case Data.PRESENT.PR_boolean:
                text.append(str(data.boolean))
                highlighter.highlight(text)
            case Data.PRESENT.PR_floating_point:
                text.append(f"{get_floating_point_value(data.floating_point)}")
            case Data.PRESENT.PR_integer:
                text.append(str(data.integer))
            case Data.PRESENT.PR_unsigned:
                text.append(str(data.unsigned))
            case Data.PRESENT.PR_visible_string:
                text.append(escape(repr(data.visible_string or "<EMPTY>")))
            case Data.PRESENT.PR_objId:
                text.append(escape(repr(data.objId or "<EMPTY>")))
            case Data.PRESENT.PR_mMSString:
                text.append(escape(repr(data.mMSString or "<EMPTY>")))
            case Data.PRESENT.PR_octet_string:
                if data.octet_string:
                    text.append("\n").append(hexdump.hexdump(data.octet_string))
                else:
                    text.append("<EMPTY>")
                do_highlight = False
            case Data.PRESENT.PR_bit_string:
                text.append("0b").append(data.bit_string.value.to01())
            case Data.PRESENT.PR_binary_time:
                text.append(str(data.binary_time))
            case Data.PRESENT.PR_generalized_time:
                text.append(str(data.generalized_time))
            case Data.PRESENT.PR_bcd:
                text.append(str(data.bcd))
            case Data.PRESENT.PR_utc_time:
                if data.utc_time.value != bytes(8):
                    text.append("\n").append(hexdump.hexdump(data.utc_time.value))
                    do_highlight = False
                else:
                    text.append("<EMPTY>")
            case _:
                return None

        if do_highlight:
            highlighter.highlight(text)
        return text


def do_create_dataset(acsi: IED_Client, args) -> None:
    """Handle the `create-dataset` subcommand: dynamically create a data set."""
    dataset_ref = ObjectReference.from_mmsref(f"{args.device}/{args.dataset}")
    members = [
        ObjectReference.from_mmsref(f"{args.device}/{member}")
        for member in args.members
    ]
    acsi.create_dataset(dataset_ref, members)
    logging.info("Created data set: %s (%d member(s))", dataset_ref, len(members))


def do_delete_dataset(acsi: IED_Client, args) -> None:
    """Handle the `delete-dataset` subcommand: dynamically delete a data set."""
    dataset_ref = ObjectReference.from_mmsref(f"{args.device}/{args.dataset}")
    if acsi.delete_dataset(dataset_ref):
        logging.info("Deleted data set: %s", dataset_ref)
    else:
        logging.error("Data set not deleted (not found or not deletable): %s", dataset_ref)


def cli_main():
    from icspacket import __version__

    parser = argparse.ArgumentParser(
        description="IED enumeration tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # fmt: off
    group = parser.add_argument_group("Output Options")
    group.add_argument("-L", "--list", action="store_true", help="Output all discovered nodes as a list instead of a table/tree", default=False)
    group.add_argument("--maxdepth", type=int, metavar="DEPTH", help="Maximum node depth to display")
    group.add_argument("--no-path", action="store_true", help="Do not display the path to each node", default=False)
    group.add_argument("-V", "--values", action="store_true", help="Display node values", default=False)

    group = parser.add_argument_group("Target Options")
    group.add_argument("-D", "--device", type=str, metavar="NAME", help="Target logical device name (LDName) to use")
    group.add_argument("-N", "--node", type=str, metavar="NAME", help="Name of the target logical node (LNName) to display")
    # fmt; on
    add_mms_connection_options(parser)
    add_logging_options(parser)

    actions = parser.add_subparsers(title="Actions", description="Additional data set management operations (default: discover/display nodes)", dest="action", metavar="ACTION")

    create_dataset = actions.add_parser("create-dataset", help="Dynamically create a new data set on the target device")
    create_dataset.add_argument("dataset", type=str, metavar="LN.DATASET", help="Data set to create, e.g. 'LLN0.events'")
    create_dataset.add_argument("members", nargs="+", type=str, metavar="LN.DO[.DA]", help="Member reference(s) to include, e.g. 'LLN0.Mod.stVal'")

    delete_dataset = actions.add_parser("delete-dataset", help="Dynamically delete an existing data set on the target device")
    delete_dataset.add_argument("dataset", type=str, metavar="LN.DATASET", help="Data set to delete, e.g. 'LLN0.events'")

    args = parser.parse_args()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    conn = init_mms_connection(
        args.host,
        args.port,
        args.auth,
        args.auth_stdin,
        args.timeout,
        args.max_tpdu_size,
    )
    if conn is None:
        sys.exit(1)

    acsi = IED_Client(conn=conn)
    try:
        if not args.device:
            devices = acsi.get_server_directory()
            if len(devices) == 0:
                logging.error("No IEDs found")
                sys.exit(1)
            if len(devices) > 1:
                args.device = Prompt.ask(
                    "Multiple IEDs found, please specify one",
                    choices=list(map(str, devices)),
                )
            else:
                logging.info("Automatically selecting IED: %s", devices[0])
                args.device = str(devices[0])

        match getattr(args, "action", None):
            case "create-dataset":
                do_create_dataset(acsi, args)
            case "delete-dataset":
                do_delete_dataset(acsi, args)
            case _:
                discover = IED_Discover(acsi, args)
                discover.discover()
        # scan_remote(acsi, args)
    except KeyboardInterrupt:
        logging.error("Aborted by user")
    except Exception as e:
        logging.exception("Unexpected error: %s", e)
    finally:
        logging.debug("Disconnecting...")
        acsi.release()


if __name__ == "__main__":
    cli_main()
