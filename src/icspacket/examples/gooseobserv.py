#!/usr/bin/env python
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
#
# Simple Script to
import argparse
import dataclasses
import datetime
import logging
import json

from typing import Any

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.markup import escape
from rich.text import Text
from rich.tree import Tree
from scapy.layers.l2 import Dot1Q, Ether

from icspacket.core import logger
from icspacket.proto.iec61850._iec61850 import (
    Data,
    IEC61850_Specific_Protocol,
)
from icspacket.proto.iec61850.goose import PDU, GOOSE_Client

from icspacket.examples.util import add_logging_options
from icspacket.proto.iec61850.path import ObjectReference
from icspacket.examples.mms_utility import data_to_str
from icspacket.proto.mms.data import get_floating_point_value, Timestamp


class PacketHandler:
    def __init__(self, args) -> None:
        self.console = Console()
        self.json_out = args.json
        self.json_minify = args.json_minify
        self.target_dataref = args.data
        self.target_dataset_ref = args.dataset
        self.target_goid = args.goid

    def include(self, pdu: IEC61850_Specific_Protocol) -> bool:
        if pdu.present == IEC61850_Specific_Protocol.PRESENT.PR_goosePdu:
            goose_pdu = pdu.goosePdu
            ref = ObjectReference.from_mmsref(goose_pdu.gocbRef)
            if self.target_dataref and ref != self.target_dataref:
                return False

            data_set = ObjectReference.from_mmsref(goose_pdu.datSet)
            if self.target_dataset_ref and data_set != self.target_dataset_ref:
                return False

            go_id = goose_pdu.goID
            if self.target_goid and go_id != self.target_goid:
                return False

            return True

    def on_message(self, pkt: Ether, pdu: PDU) -> None:
        vlan_pkt = pkt.getlayer(Dot1Q)
        dest: str = pkt.dst.lower()
        is_std = dest.startswith("01:0c:cd")

        address = dest[-5:]
        if vlan_pkt:
            logging.debug(
                "(G: %s) (VLAN %s) 802.1Q from %s", address, vlan_pkt.vlan, pkt.src
            )
        try:
            apdu = pdu.apdu(IEC61850_Specific_Protocol)
        except ValueError:
            return logging.error("Failed to parse GOOSE APDU")

        # logging.debug("(App: [b]%s[/]): [i]%s[/]", pdu.app_id,
        # apdu.present.name[3:])
        include = self.include(apdu)
        if not include:
            return

        logging.info(
            "(AppId: [b]%s[/]) %s > %s%s",
            pdu.app_id,
            pkt.src,
            pkt.dst,
            "" if is_std else " ([i]non-std dest[/])",
        )
        if apdu.present == IEC61850_Specific_Protocol.PRESENT.PR_goosePdu:
            goose_pdu = apdu.goosePdu
            assert goose_pdu  # this should never happen

            if self.json_out:
                return self._format_json(pkt, vlan_pkt, pdu, apdu)

            ref = ObjectReference.from_mmsref(goose_pdu.gocbRef)
            data_set = ObjectReference.from_mmsref(goose_pdu.datSet)
            go_id = goose_pdu.goID

            label = (
                f"[bold light_green]{goose_pdu.stNum}:{goose_pdu.sqNum}[/] [b]DATA[/]:"
                f"{ref} of [b]DATA_SET[/]:{data_set}"
            )
            if go_id:
                label = f"{label} ([b]{go_id}[/])"

            tree = Tree(label)
            tree.add(f"Simulation: {goose_pdu.simulation or False}")
            tree.add(f"ConfRev: {goose_pdu.confRev}")
            tree.add(f"NDSCom: {goose_pdu.ndsCom}")

            ts = Timestamp.from_utc_time(goose_pdu.time)
            dt = datetime.datetime.fromtimestamp(ts.seconds)
            tree.add(f"Time: {dt}")
            if goose_pdu.numDatSetEntries > 0:
                subtree = tree.add("Data Set Entries:")
                for i, value in enumerate(list(goose_pdu.allData)):
                    value_text = self._format_data(value)
                    text = Text(f"({i}) {value.present.name[3:]}: ")
                    text.append(value_text)
                    subtree.add(text)

            self.console.print(tree)

    def _format_data(self, data: Data) -> Any:
        highlighter = ReprHighlighter()
        text = Text()
        do_highlight = True
        match data.present:
            case Data.PRESENT.PR_floating_point:
                text.append(str(get_floating_point_value(data.floating_point)))
            case Data.PRESENT.PR_boolean:
                text.append(str(data.boolean))
            case Data.PRESENT.PR_integer:
                text.append(str(data.integer))
            case Data.PRESENT.PR_Unsigned:
                text.append(str(data.unsigned))
            case Data.PRESENT.PR_visible_string:
                text.append(escape(repr(data.visible_string or "<EMPTY>")))
            case Data.PRESENT.PR_objId:
                text.append(escape(repr(data.objId or "<EMPTY>")))
            case Data.PRESENT.PR_structure:
                text.append("{ ")
                first = True
                for element in list(data.structure):
                    element_text = self._format_data(element)
                    if not first:
                        text.append(", ")
                    else:
                        first = False
                    text.append(element_text)
                text.append(" }")
            case Data.PRESENT.PR_array:
                text.append("[ ")
                first = True
                for element in list(data.array):
                    element_text = self._format_data(element)
                    if not first:
                        text.append(", ")
                    else:
                        first = False
                    text.append(element_text)
                text.append(" ]")
            case Data.PRESENT.PR_bit_string:
                text.append(f"'{data.bit_string.value.to01()}'B")
                do_highlight = False
            case Data.PRESENT.PR_octet_string:
                text.append(f"'{data.octet_string.hex()}'H")
                do_highlight = False
            case Data.PRESENT.PR_utc_time:
                ts = Timestamp.from_utc_time(data.utc_time)
                dt = datetime.datetime.fromtimestamp(ts.seconds)
                text.append(str(dt))
                do_highlight = False
            case _:
                text.append(str(data_to_str(data)))
                do_highlight = False

        if do_highlight:
            highlighter.highlight(text)
        return text

    def _format_json(
        self, pkt: Ether, vlan_pkt: Dot1Q, pdu: PDU, apdu: IEC61850_Specific_Protocol
    ) -> None:
        apdu_json = json.loads(apdu.jer_encode())
        log_entry = {
            "src": pkt.src,
            "dst": pkt.dst,
            "vlan": vlan_pkt.vlan if vlan_pkt else None,
            "pdu": dataclasses.asdict(pdu),
        }
        del log_entry["pdu"]["raw_apdu"]
        log_entry["pdu"]["apdu"] = apdu_json
        self.console.print(
            json.dumps(log_entry, indent=2 if not self.json_minify else None)
        )


def cli_main():
    from icspacket import __version__

    parser = argparse.ArgumentParser(
        description="GOOSE Observer (requires administrative privileges)",
    )
    # fmt: off
    group = parser.add_argument_group("Output Options")
    group.add_argument("--json", action="store_true", help="Output as JSON", default=False)
    group.add_argument("--json-minify", action="store_true", help="Minify the JSON output", default=False)

    group = parser.add_argument_group("Filter Options")
    group.add_argument("--data", type=ObjectReference.from_mmsref, help="Filter on data set entry (DataName)", metavar="<LDName>/<LNName>.<FC>.<DataName>", default=None)
    group.add_argument("--dataset", type=ObjectReference.from_mmsref, help="Filter on data set name (DataName)", metavar="<LDName>/<LNName>.<DataName>", default=None)
    group.add_argument("--goid", type=str, help="Filter on GoID", metavar="GOID", default=None)

    group = parser.add_argument_group("Input Options")
    group.add_argument("-I", "--interface", action="append", help="Interface to listen on", dest="interfaces", default=None)
    group.add_argument("-P", "--pcap", action="append", help="Read packets from a PCAP file", dest="pcaps", default=None)
    # fmt: on
    add_logging_options(parser)

    args = parser.parse_args()
    if args.json:
        # disable all logging output except errors
        args.quiet = True

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    handler = PacketHandler(args)
    observer = GOOSE_Client(
        iface=args.interfaces, inputs=args.pcaps, callback=handler.on_message
    )
    if not args.pcaps:
        logging.info("Hit Ctrl+C to stop...")
        observer.listen_forever()
    else:
        observer.start()
        observer.stop(join=True)


if __name__ == "__main__":
    cli_main()
