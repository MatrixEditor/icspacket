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
# pyright: reportUnusedCallResult=false, reportGeneralTypeIssues=false
#
# Very basic approach to interact with BACnet/IP peers. Currently, it
# supports the following operations:
#
#   - Discovery: whois, whohas
#   - Objects: read, write, rpm, wpm, objects/discover/scan, identify
#   - Change-of-Value: subscribe
#   - BBMD: bdt, fdt
import ast
import logging
import sys
import textwrap
import time
from typing import Any

import cmd2
from rich import box
from rich.console import Console
from rich.table import Table
from typing_extensions import override

from icspacket.core.connection import ConnectionClosedError
from icspacket.examples.util import add_logging_options
from icspacket.examples.util.bacnet import (
    add_bacnet_connection_options,
    init_bacnet_connection,
)
from icspacket.proto.bacnet.connection import BACnet_Connection, BACnetProtocolError

_IDENTIFY_PROPERTIES = (
    "object-name",
    "vendor-name",
    "model-name",
    "firmware-revision",
    "application-software-version",
    "protocol-version",
    "protocol-revision",
)


def _parse_value(raw: str) -> Any:
    """Parse a CLI-supplied value, preferring a Python literal (numbers,
    booleans, quoted strings) and otherwise passing it through unchanged
    so BACnet enumeration names (``active``/``inactive``) and the
    priority-relinquish token (``null``) reach :mod:`bacpypes3` verbatim -
    it casts plain values to the property's declared datatype itself."""
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return raw


class BACnetClient(cmd2.Cmd):
    do_exit = cmd2.Cmd.do_quit

    def __init__(self, conn: BACnet_Connection) -> None:
        """Interactive BACnet/IP client shell.

        This command-line shell keeps a single local BACnet/IP endpoint
        bound for its entire lifetime and allows executing repeated
        discovery, read, write, and subscription operations against any
        number of remote devices without rebinding between them.

        :param conn: Active BACnet connection instance
        :type conn: BACnet_Connection
        """
        super().__init__(
            allow_cli_args=False,
            allow_redirection=False,
        )
        self.__connection = conn
        self.console: Console = Console()
        self.prompt: str = "bacnet> "
        self.echo: bool = True
        # disable default commands
        del [
            cmd2.Cmd.do_alias,
            cmd2.Cmd.do_edit,
            cmd2.Cmd.do_macro,
            cmd2.Cmd.do_py,
            cmd2.Cmd.do_run_pyscript,
            cmd2.Cmd.do_run_script,
            cmd2.Cmd.do_set,
            cmd2.Cmd.do_shell,
            cmd2.Cmd.do_shortcuts,
        ]
        self.remove_settable("debug")

    @property
    def conn(self) -> BACnet_Connection:
        """Return the underlying BACnet connection object."""
        return self.__connection

    # fmt: off
    whois_parser: cmd2.Cmd2ArgumentParser = cmd2.Cmd2ArgumentParser()
    whois_parser.add_argument("address", nargs="?", default=None, help="Unicast target address, or omit to broadcast on the local network")
    whois_parser.add_argument("-l", "--low", type=int, default=None, dest="low_limit", help="Lower bound of the device instance range to query")
    whois_parser.add_argument("-u", "--high", type=int, default=None, dest="high_limit", help="Upper bound of the device instance range to query")
    whois_parser.add_argument("-t", "--timeout", type=float, default=None, help="Override the connection's default timeout for this request")
    # fmt: on

    @cmd2.with_argparser(whois_parser)
    def do_whois(self, args) -> None:
        """Discover devices via a Who-Is/I-Am exchange."""
        logging.info("Sending Who-Is (%s)...", args.address or "broadcast")
        devices = self.conn.who_is(
            args.low_limit, args.high_limit, args.address, timeout=args.timeout
        )
        if not devices:
            return logging.warning("No I-Am responses received")

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Device", justify="left")
        table.add_column("Address", justify="left")
        table.add_column("Max APDU", justify="right")
        table.add_column("Segmentation", justify="left")
        table.add_column("Vendor ID", justify="right")
        for d in devices:
            table.add_row(
                str(d.device_identifier),
                str(d.address),
                str(d.max_apdu_length_accepted),
                str(d.segmentation_supported),
                str(d.vendor_id),
            )
        self.console.print(table)

    do_wi = do_whois

    # fmt: off
    whohas_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    whohas_parser.add_argument("address", nargs="?", default=None, help="Unicast target address, or omit to broadcast on the local network")
    whohas_group = whohas_parser.add_mutually_exclusive_group(required=True)
    whohas_group.add_argument("-o", "--object-id", dest="object_identifier", default=None, help="Object identifier to search for, e.g. analog-input,1")
    whohas_group.add_argument("-n", "--name", dest="object_name", default=None, help="Object name to search for")
    whohas_parser.add_argument("-l", "--low", type=int, default=None, dest="low_limit", help="Lower bound of the device instance range to query")
    whohas_parser.add_argument("-u", "--high", type=int, default=None, dest="high_limit", help="Upper bound of the device instance range to query")
    whohas_parser.add_argument("-t", "--timeout", type=float, default=None, help="Override the connection's default timeout for this request")
    # fmt: on

    @cmd2.with_argparser(whohas_parser)
    def do_whohas(self, args) -> None:
        """Discover which device(s) hold a given object via Who-Has/I-Have."""
        target = args.object_identifier or args.object_name
        logging.info(
            "Sending Who-Has for %r (%s)...", target, args.address or "broadcast"
        )
        results = self.conn.who_has(
            args.low_limit,
            args.high_limit,
            args.object_identifier,
            args.object_name,
            args.address,
            timeout=args.timeout,
        )
        if not results:
            return logging.warning("No I-Have responses received")

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Device", justify="left")
        table.add_column("Object", justify="left")
        table.add_column("Name", justify="left")
        for r in results:
            table.add_row(
                str(r.device_identifier), str(r.object_identifier), r.object_name or ""
            )
        self.console.print(table)

    do_wh = do_whohas

    # fmt: off
    read_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    read_parser.add_argument("address", help="Target device's network address")
    read_parser.add_argument("object", help="Object identifier, e.g. analog-input,1")
    read_parser.add_argument("property", help="Property identifier, e.g. present-value")
    read_parser.add_argument("-i", "--index", type=int, default=None, dest="array_index", help="Optional array index, for array-valued properties")
    read_parser.add_argument("-t", "--timeout", type=float, default=None, help="Override the connection's default timeout for this request")
    # fmt: on

    @cmd2.with_argparser(read_parser)
    def do_read(self, args) -> None:
        """Read a single property from an object on a remote device."""
        logging.info(
            "Reading %s.%s from %s...", args.object, args.property, args.address
        )
        value = self.conn.read_property(
            args.address,
            args.object,
            args.property,
            args.array_index,
            timeout=args.timeout,
        )
        self.console.print(f"[bold]{args.object}.{args.property}[/] = {value!r}")

    do_r = do_read

    # fmt: off
    write_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    write_parser.add_argument("address", help="Target device's network address")
    write_parser.add_argument("object", help="Object identifier, e.g. analog-value,1")
    write_parser.add_argument("property", help="Property identifier, e.g. present-value")
    write_parser.add_argument("value", help="New value, parsed as a Python literal if possible (e.g. 72.5); otherwise passed through as-is (e.g. active, inactive, null)")
    write_parser.add_argument("-i", "--index", type=int, default=None, dest="array_index", help="Optional array index, for array-valued properties")
    write_parser.add_argument("-p", "--priority", type=int, default=None, help="Optional commandable priority (1-16)")
    write_parser.add_argument("-t", "--timeout", type=float, default=None, help="Override the connection's default timeout for this request")
    # fmt: on

    @cmd2.with_argparser(write_parser)
    def do_write(self, args) -> None:
        """Write a single property on an object on a remote device."""
        value = _parse_value(args.value)
        logging.info(
            "Writing %r to %s.%s on %s...",
            value,
            args.object,
            args.property,
            args.address,
        )
        self.conn.write_property(
            args.address,
            args.object,
            args.property,
            value,
            array_index=args.array_index,
            priority=args.priority,
            timeout=args.timeout,
        )
        logging.info("Write operation succeeded")

    do_w = do_write

    # fmt: off
    rpm_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    rpm_parser.add_argument("address", help="Target device's network address")
    rpm_parser.add_argument("-o", "--object", dest="objects", action="append", required=True, metavar="OBJECT:PROP[,PROP...]", help="Object identifier and comma-separated property identifiers to read, e.g. 'analog-input,1:present-value,units' (repeatable)")
    rpm_parser.add_argument("-t", "--timeout", type=float, default=None, help="Override the connection's default timeout for this request")
    # fmt: on

    @cmd2.with_argparser(rpm_parser)
    def do_rpm(self, args) -> None:
        """Read multiple properties, possibly across multiple objects, in a single ReadPropertyMultiple request."""
        parameter_list = []
        for spec in args.objects:
            object_identifier, sep, props = spec.partition(":")
            if not sep or not props:
                return logging.error(
                    "Invalid --object spec %r (expected OBJECT:PROP[,PROP...])", spec
                )
            parameter_list.append((object_identifier, props.split(",")))

        logging.info(
            "Reading %d object(s) from %s via ReadPropertyMultiple...",
            len(parameter_list),
            args.address,
        )
        results = self.conn.read_property_multiple(
            args.address, parameter_list, timeout=args.timeout
        )

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Object", justify="left")
        table.add_column("Property", justify="left")
        table.add_column("Index", justify="right")
        table.add_column("Value", justify="left")
        for obj_id, prop_id, arr_idx, value in results:
            table.add_row(
                str(obj_id),
                str(prop_id),
                "" if arr_idx is None else str(arr_idx),
                repr(value),
            )
        self.console.print(table)

    # fmt: off
    wpm_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    wpm_parser.add_argument("address", help="Target device's network address")
    wpm_parser.add_argument("-w", "--write", dest="writes", action="append", required=True, metavar="OBJECT:PROP:VALUE[:INDEX[:PRIORITY]]", help="One property write, e.g. 'analog-value,1:present-value:72.5' or '...:72.5::8' for priority 8 (repeatable)")
    wpm_parser.add_argument("-t", "--timeout", type=float, default=None, help="Override the connection's default timeout applied to each individual write")
    # fmt: on

    @cmd2.with_argparser(wpm_parser)
    def do_wpm(self, args) -> None:
        """Write multiple properties (one WriteProperty request per item; not an atomic operation - see write_property_multiple)."""
        values = []
        for spec in args.writes:
            parts = spec.split(":")
            if len(parts) < 3:
                return logging.error(
                    "Invalid --write spec %r (expected OBJECT:PROP:VALUE[:INDEX[:PRIORITY]])",
                    spec,
                )
            object_identifier, property_identifier, raw_value = parts[:3]
            array_index = int(parts[3]) if len(parts) > 3 and parts[3] else None
            priority = int(parts[4]) if len(parts) > 4 and parts[4] else None
            values.append(
                (
                    object_identifier,
                    property_identifier,
                    _parse_value(raw_value),
                    array_index,
                    priority,
                )
            )

        logging.info("Writing %d value(s) to %s...", len(values), args.address)
        results = self.conn.write_property_multiple(
            args.address, values, timeout=args.timeout
        )

        failures = 0
        for (object_identifier, property_identifier, *_), error in zip(values, results):
            if error is None:
                self.console.print(
                    f"[bold]{object_identifier}.{property_identifier}[/] = [green]OK[/]"
                )
            else:
                failures += 1
                self.console.print(
                    f"[bold]{object_identifier}.{property_identifier}[/] = [red]FAILED[/] ({error})"
                )

        if failures:
            logging.warning("%d of %d write(s) failed", failures, len(values))
        else:
            logging.info("All writes succeeded")

    # fmt: off
    objects_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    objects_parser.add_argument("address", help="Target device's network address")
    objects_parser.add_argument("-d", "--device-id", dest="device_identifier", default=None, help="Device object identifier, e.g. device,1234 (default: resolved via who-is)")
    objects_parser.add_argument("-V", "--values", action="store_true", default=False, help="Also read each object's present-value property")
    objects_parser.add_argument("-t", "--timeout", type=float, default=None, help="Timeout in seconds applied to each individual property read")
    # fmt: on

    @cmd2.with_argparser(objects_parser)
    def do_objects(self, args) -> None:
        """Enumerate the objects exposed by a remote device (via its object-list property)."""
        logging.info("Reading object list from %s...", args.address)
        with self.console.status("Scanning objects..."):
            objects = self.conn.scan_objects(
                args.address,
                device_identifier=args.device_identifier,
                values=args.values,
                timeout=args.timeout,
            )

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Object", justify="left")
        table.add_column("Name", justify="left")
        if args.values:
            table.add_column("Value", justify="left")
        for obj in objects:
            row = [str(obj.object_identifier), obj.object_name or ""]
            if args.values:
                row.append("" if obj.present_value is None else repr(obj.present_value))
            table.add_row(*row)
        self.console.print(table)

    do_discover = do_objects
    do_scan = do_objects

    # fmt: off
    identify_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    identify_parser.add_argument("address", help="Target device's network address")
    identify_parser.add_argument("-d", "--device-id", dest="device_identifier", default=None, help="Device object identifier, e.g. device,1234 (default: resolved via who-is)")
    identify_parser.add_argument("-t", "--timeout", type=float, default=None, help="Timeout in seconds applied to each individual property read")
    # fmt: on

    @cmd2.with_argparser(identify_parser)
    def do_identify(self, args) -> None:
        """Read a device's identification properties (vendor/model/firmware/...)."""
        device_identifier = args.device_identifier
        if device_identifier is None:
            devices = self.conn.who_is(address=args.address, timeout=args.timeout)
            if not devices:
                return logging.error(
                    "Could not resolve device identifier for %s: no I-Am response",
                    args.address,
                )
            device_identifier = devices[0].device_identifier

        logging.info("Requesting device identification properties...")
        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Property", justify="left")
        table.add_column("Value", justify="left")
        for prop in _IDENTIFY_PROPERTIES:
            try:
                value = self.conn.read_property(
                    args.address, device_identifier, prop, timeout=args.timeout
                )
                table.add_row(prop, str(value))
            except BACnetProtocolError:
                pass  # not every device implements every identification property
        self.console.print(table)

    do_id = do_identify

    # fmt: off
    subscribe_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    subscribe_parser.add_argument("address", help="Target device's network address")
    subscribe_parser.add_argument("object", help="Object identifier to monitor, e.g. analog-input,1")
    subscribe_parser.add_argument("-c", "--confirmed", action="store_true", default=False, help="Request confirmed (vs. unconfirmed) notifications")
    subscribe_parser.add_argument("-l", "--lifetime", type=int, default=None, metavar="SEC", help="Subscription lifetime in seconds (default: bacpypes3's default/indefinite)")
    subscribe_parser.add_argument("--duration", type=float, default=None, metavar="SEC", help="Stop after this many seconds (default: run until Ctrl+C)")
    subscribe_parser.add_argument("--count", type=int, default=None, metavar="N", help="Stop after receiving this many notifications (default: unlimited)")
    # fmt: on

    @cmd2.with_argparser(subscribe_parser)
    def do_subscribe(self, args) -> None:
        """Subscribe to Change-of-Value (COV) notifications for an object."""
        logging.info(
            "Subscribing to %s on %s (confirmed=%s)...",
            args.object,
            args.address,
            args.confirmed,
        )
        sub = self.conn.subscribe_cov(
            args.address,
            args.object,
            confirmed=args.confirmed,
            lifetime=args.lifetime,
        )
        deadline = time.monotonic() + args.duration if args.duration else None
        received = 0

        try:
            while deadline is None or time.monotonic() < deadline:
                poll_timeout = 1.0
                if deadline is not None:
                    poll_timeout = min(
                        poll_timeout, max(0.0, deadline - time.monotonic())
                    )

                item = sub.next_value(timeout=poll_timeout)
                if item is None:
                    continue

                property_identifier, value = item
                self.console.print(f"[bold]{property_identifier}[/] = {value!r}")
                received += 1
                if args.count and received >= args.count:
                    break
        except KeyboardInterrupt:
            logging.info("Subscription cancelled by user")
        finally:
            logging.debug(
                "Closing subscription (%d notification(s) received)...", received
            )
            sub.close()

    do_sub = do_subscribe

    # fmt: off
    bdt_parser: cmd2.Cmd2ArgumentParser  = cmd2.Cmd2ArgumentParser()
    bdt_parser.add_argument("address", help="Target BBMD's network address")
    bdt_parser.add_argument("-t", "--timeout", type=float, default=None, help="Override the connection's default timeout for this request")
    # fmt: on

    @cmd2.with_argparser(bdt_parser)
    def do_bdt(self, args) -> None:
        """Read a remote BBMD's Broadcast Distribution Table."""
        logging.info("Reading Broadcast Distribution Table from %s...", args.address)
        entries = self.conn.read_broadcast_distribution_table(
            args.address, timeout=args.timeout
        )
        if not entries:
            return logging.warning("BDT is empty")

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Entry", justify="left")
        for entry in entries:
            table.add_row(str(entry))
        self.console.print(table)

    # fmt: off
    fdt_parser = cmd2.Cmd2ArgumentParser()
    fdt_parser.add_argument("address", help="Target BBMD's network address")
    fdt_parser.add_argument("-t", "--timeout", type=float, default=None, help="Override the connection's default timeout for this request")
    # fmt: on

    @cmd2.with_argparser(fdt_parser)
    def do_fdt(self, args) -> None:
        """Read a remote BBMD's Foreign Device Table."""
        logging.info("Reading Foreign Device Table from %s...", args.address)
        entries = self.conn.read_foreign_device_table(
            args.address, timeout=args.timeout
        )
        if not entries:
            return logging.warning("FDT is empty")

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Entry", justify="left")
        for entry in entries:
            table.add_row(str(entry))
        self.console.print(table)

    @override
    def pexcept(
        self,
        exception: Any,
        *,
        end: str = "\n",
        apply_style: bool = True,
        **kwargs: Any,
    ) -> None:
        match exception:
            case BACnetProtocolError():
                return logging.error("BACnet request failed: %s", exception)
            case ConnectionClosedError():
                return logging.warning(str(exception))

        return super().pexcept(exception, end=end, apply_style=apply_style, **kwargs)


def cli_main() -> None:
    import argparse

    from icspacket import __version__
    from icspacket.core import logger

    class _HelpAction(argparse.Action):
        def __init__(
            self,
            option_strings,
            dest=argparse.SUPPRESS,
            default=argparse.SUPPRESS,
            help=None,
        ):
            super(_HelpAction, self).__init__(
                option_strings=option_strings,
                dest=dest,
                default=default,
                nargs="?",
                help=help,
            )

        def __call__(self, parser, namespace, values, option_string=None):
            if not values:
                parser.print_help()
            else:
                parser_name = f"{values}_parser"
                if hasattr(BACnetClient, parser_name):
                    getattr(BACnetClient, parser_name).print_help()
                else:
                    parser.error(f"no such command: {values}")
            parser.exit()

    EPILOG = """\
    Examples:
        bacnetclient.py whois
        bacnetclient.py whois --low 1000 --high 2000
        bacnetclient.py read <address> analog-input,1 present-value
        bacnetclient.py write <address> analog-value,1 present-value 72.5 -p 8
        bacnetclient.py objects <address> --values
        bacnetclient.py identify <address>
        bacnetclient.py rpm <address> -o analog-input,1:present-value,units
        bacnetclient.py subscribe <address> analog-input,1 --duration 30
        bacnetclient.py bdt <address>
        bacnetclient.py --foreign <bbmd-address> whois   # register as a foreign device first
        bacnetclient.py -i           # drop into an interactive shell
        bacnetclient.py              # (no command) also starts the shell
    """

    parser = argparse.ArgumentParser(
        usage="%(prog)s [options] [command [args...]]",
        description="BACnet/IP utility to discover devices/objects and read/write properties",
        epilog=textwrap.dedent(EPILOG),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Continue in interactive mode after executing the first command (only if given)",
        default=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action=_HelpAction,
        help="Show this help message and exit. Optionally: show help for command",
        default=None,
        dest="help",
    )

    add_bacnet_connection_options(parser)
    add_logging_options(parser)

    args, remaining = parser.parse_known_args()
    args.console = Console()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    conn = init_bacnet_connection(
        args.address,
        args.name,
        args.instance,
        args.network,
        args.vendor_identifier,
        args.foreign_bbmd,
        args.foreign_ttl,
        args.bbmd_bdt,
        args.timeout,
    )
    if conn is None:
        sys.exit(1)

    client = BACnetClient(conn)
    try:
        if remaining:
            client.onecmd_plus_hooks(" ".join(remaining))

        if not remaining or args.interactive:
            client.cmdloop()
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user...")
    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)
        sys.exit(1)
    finally:
        try:
            logging.debug("Closing BACnet connection...")
            conn.close()
        except ConnectionClosedError:
            logging.debug("Connection was already closed by remote peer")


if __name__ == "__main__":
    cli_main()
