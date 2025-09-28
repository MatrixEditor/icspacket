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
import json
import logging
import sys

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.prompt import Prompt

from icspacket.core import logger
from icspacket.examples.mms_utility import data_to_str
from icspacket.examples.util import add_logging_options
from icspacket.proto.iec61850.classes import FC, ControlModel
from icspacket.proto.iec61850.client import IED_Client
from icspacket.examples.util.mms import (
    add_mms_connection_options,
    init_mms_connection,
)
from icspacket.proto.iec61850.control import LastApplError
from icspacket.proto.iec61850.path import DataObjectReference


def cli2data(value: str) -> Any | None:
    path = Path(value)
    try:
        if path.exists() and path.is_file():
            with path.open() as fp:
                doc = json.load(fp)
        else:
            doc = json.loads(value)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON value format: {value!r} - {e}")
        return None

    if isinstance(doc, dict) and "value" in doc:
        doc = doc["value"]
    return doc


def parse_origin(origin: str) -> tuple[int, bytes]:
    if ":" not in origin:
        logging.warning(f"Invalid origin format: {origin!r}")
        return 0, bytes()

    cat, id = origin.split(":")
    try:
        ident = bytes.fromhex(id)
    except ValueError:
        ident = id.encode()
    return int(cat), ident


def cli_main():
    from icspacket import __version__

    parser = argparse.ArgumentParser(
        description="IED operate tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # fmt: off
    group = parser.add_argument_group("Target Options")
    group.add_argument("-t", "--target", metavar="[LDName/]LNName.[FC].DataName", default=None, help=(
        "Target data node to control. If missing the logical device (LDName), the service will first be \n"
        "queried for the default logical device and then the data node (DataName) will be used. \n"
        "Functional Constrains (FC) is optional as this will always be the CO (Control)."
    ), required=True)
    group.add_argument("--check", action="store_true", help="Queries the value after successful operation.")

    group = parser.add_argument_group("Value Options")
    group = group.add_mutually_exclusive_group(required=True)
    group.add_argument("--value", metavar="VALUE", default=None, dest="var_value", help=(
        "Value to write to variable(s). JSON format is used for structured data. "
        "Alternatively, a file path containing the JSON can be specified.")
    )
    group.add_argument("--toggle", action="store_true", help="Toggle the value of the specified variable (queries first and assumes boolean).")

    group = parser.add_argument_group("Control Options")
    group.add_argument("--origin", metavar="CAT:ID", default=None, help=(
        "The origin of the control request. \n"
        "If not specified the default origin will be used."
    ))
    group.add_argument("--synchro-check", action="store_true", help="Enables synchro check for the control request.")
    group.add_argument("--interlock-check", action="store_true", help="Enables interlock check for the control request.")
    # fmt: on
    add_mms_connection_options(parser)
    add_logging_options(parser)

    args = parser.parse_args()
    args.console = Console()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    if args.var_value is None:
        if not args.toggle:
            logging.error("Must specify --value or --toggle")
            parser.print_usage()
    else:
        args.var_value = cli2data(args.var_value)
        if args.var_value is None:
            sys.exit(1)

    conn = init_mms_connection(
        args.host,
        args.port,
        args.auth,
        args.auth_stdin,
    )
    if conn is None:
        sys.exit(1)

    client = IED_Client(conn=conn)
    if "/" not in args.target:
        # search for logical devices
        devices = client.get_server_directory()
        if len(devices) == 0:
            logging.error("No logical devices found")
            sys.exit(1)

        if len(devices) == 1:
            logging.info(f"Automatically selecting {devices[0]} as logical device")
            args.target = f"{devices[0]}/{args.target}"
        else:
            ldname = Prompt.ask(
                "Multiple logical devices found, please select one",
                choices=devices,
                default=devices[0],
            )
            args.target = f"{ldname}/{args.target}"

    ref = DataObjectReference.from_mmsref(args.target)
    parts = ref.parts
    # Always change constraint to CO, even if not present
    ref = DataObjectReference(ref.ldname, ref.lnname, FC.CO.name, parts[-1])
    logging.debug(f"Requesting control model information about {parts[-1]}...")
    try:
        co = client.control(ref)
        logging.info(f"Control model for node: {co.model.name}")
    except ConnectionError:
        logging.error(
            "Failed to request control model information - is node really present?"
        )
        sys.exit(1)

    if args.synchro_check:
        co.synchro_check = True
    if args.interlock_check:
        co.interlock_check = True
    if args.origin:
        co.origin_cat, co.origin_ident = parse_origin(args.origin)

    if args.toggle:
        logging.debug("Toggle: Requesting current value for node...")
        value = client.get_data_values(ref / "Oper" / "ctlVal")
        if value.failure:
            logging.error("Failed to get value: %s", value.failure.value)
            sys.exit(1)

        current = value.success.boolean
        args.var_value = not current
        logging.info(
            f"Value will be changed from {str(current).upper()} -> [b]{str(not current).upper()}[/]"
        )
    else:
        logging.info(f"Value will be changed to: {args.var_value!r}")

    try:
        match co.model:
            case ControlModel.DIRECT_NORMAL:
                logging.debug("Direct Control Nodel: Writing value...")
                error = client.operate(co, ctl_val=args.var_value)
                if error:
                    logging.error("Failed to start opertation: %s", repr(error.value))
                    sys.exit(1)

            case ControlModel.DIRECT_ENHANCED:
                if error := client.operate(co, ctl_val=args.var_value):
                    logging.error("Failed to start opertation: %s", repr(error.value))
                    sys.exit(1)

                with args.console.status("Waiting for operation to complete..."):
                    _ = client.await_command_termination()

            case ControlModel.SBO_NORMAL:
                logging.debug("Selecting node before operation (SBO)...")
                if error := client.select(co):
                    logging.error("Failed to select node: %s", repr(error.value))
                    sys.exit(1)

                if error := client.operate(co, ctl_val=args.var_value):
                    logging.error("Failed to start opertation: %s", repr(error.value))
                    sys.exit(1)

            case ControlModel.SBO_ENHANCED:
                logging.debug("Selecting node with value before operation (SBOw)...")
                if error := client.select_with_value(co, ctl_val=args.var_value):
                    logging.error("Failed to select node: %s", repr(error.value))
                    sys.exit(1)

                if error := client.operate(co, ctl_val=args.var_value):
                    logging.error("Failed to start opertation: %s", repr(error.value))
                    sys.exit(1)

                with args.console.status("Waiting for operation to complete..."):
                    _ = client.await_command_termination()
    except LastApplError as e:
        logging.error(
            "Failed to operate on node %s: [bold red]%s[/], cause: [red]%s",
            parts[-1],
            e.error.name,
            e.cause.name,
        )
    except ConnectionError as e:
        logging.error(
            "Failed to request control model information - is node really present?"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        logging.warning("Operation cancelled by user")
    else:
        logging.info(f"Successfully completed operation on {parts[-1]}!")

        if args.check:
            value = client.get_data_values(ref / "Oper" / "ctlVal")
            success = value.success
            if success:
                args.console.print(f"Current value: {data_to_str(success)}")
            else:
                logging.error("Failed to get value: %s", value.failure.value)


if __name__ == "__main__":
    cli_main()
