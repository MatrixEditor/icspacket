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
# Very basic approach to interact with a remote Modbus TCP peer. Currently,
# it supports the following operations:
#
#   - Tables: read, write (coils, discrete inputs, holding/input registers)
#   - identify (device identification objects)
#   - units (unit/slave identifier discovery)
#   - discover (coil/register address discovery)
import logging
import sys
import textwrap
from typing import Any

import cmd2
from rich import box
from rich.console import Console
from rich.table import Table
from typing_extensions import override

from icspacket.core.connection import ConnectionClosedError
from icspacket.examples.util import add_logging_options
from icspacket.examples.util.modbus import (
    add_modbus_connection_options,
    init_modbus_connection,
)
from icspacket.proto.modbus.connection import Modbus_Connection, ModbusProtocolError

_TABLES = {
    "coils": ("read_coils", "write_coils", "write_coil"),
    "discrete": ("read_discrete_inputs", None, None),
    "holding": ("read_holding_registers", "write_registers", "write_register"),
    "input": ("read_input_registers", None, None),
}


def _decode(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode()
        except UnicodeDecodeError:
            return value.hex()
    return str(value)


class ModbusClient(cmd2.Cmd):
    do_exit = cmd2.Cmd.do_quit

    def __init__(self, conn: Modbus_Connection) -> None:
        """Interactive Modbus client shell.

        This command-line shell keeps a single Modbus connection open for
        its entire lifetime and allows executing repeated read, write, and
        discovery operations against it without reconnecting between them.

        :param conn: Active Modbus connection instance
        :type conn: Modbus_Connection
        """
        super().__init__(
            allow_cli_args=False,
            allow_redirection=False,
        )
        self.__connection = conn
        self.console: Console = Console()
        self.prompt: str = "modbus> "
        # Echo the prompt and command back when input isn't a live TTY (e.g.
        # piped/scripted commands) so a redirected or recorded session stays
        # self-documenting. Real interactive terminals are unaffected since
        # they render their own input via prompt_toolkit.
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
    def conn(self) -> Modbus_Connection:
        """Return the underlying Modbus connection object."""
        return self.__connection

    def do_identify(self, _) -> None:
        """identify

        Retrieve device identification objects from the target Modbus server.
        """
        logging.info("Requesting device identification objects...")
        info = self.conn.read_device_information()
        for object_id, value in info.items():
            self.poutput(f"{object_id}: {_decode(value)}")

    do_id = do_identify

    # fmt: off
    read_parser = cmd2.Cmd2ArgumentParser()
    read_parser.add_argument("table", choices=list(_TABLES), help="Modbus data table")
    read_parser.add_argument("address", type=int, help="Zero-based starting address")
    read_parser.add_argument("-c", "--count", type=int, default=1, help="Number of items to read (default: 1)")
    # fmt: on

    @cmd2.with_argparser(read_parser)
    def do_read(self, args) -> None:
        """Read from a Modbus data table."""
        read_method, _, _ = _TABLES[args.table]
        logging.info(
            "Reading %d item(s) from '%s' table at address %d...",
            args.count,
            args.table,
            args.address,
        )
        values = getattr(self.conn, read_method)(args.address, count=args.count)

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Address", justify="right")
        table.add_column("Value", justify="left")
        for offset, value in enumerate(values):
            table.add_row(str(args.address + offset), str(value))
        self.console.print(table)

    do_r = do_read

    # fmt: off
    write_parser = cmd2.Cmd2ArgumentParser()
    write_parser.add_argument("table", choices=list(_TABLES), help="Modbus data table")
    write_parser.add_argument("address", type=int, help="Zero-based starting address")
    write_parser.add_argument("values", nargs="+", help="One or more values to write")
    # fmt: on

    @cmd2.with_argparser(write_parser)
    def do_write(self, args) -> None:
        """Write to a Modbus data table."""
        _, write_many, write_one = _TABLES[args.table]
        if write_one is None:
            return logging.error("Table %r is read-only", args.table)

        if args.table == "coils":
            values = [v.lower() in ("1", "true", "on", "yes") for v in args.values]
        else:
            values = [int(v, 0) for v in args.values]

        logging.info(
            "Writing %d value(s) to '%s' table at address %d...",
            len(values),
            args.table,
            args.address,
        )
        if len(values) == 1:
            getattr(self.conn, write_one)(args.address, values[0])
        else:
            getattr(self.conn, write_many)(args.address, values)

        logging.info("Write operation succeeded")

    do_w = do_write

    # fmt: off
    units_parser = cmd2.Cmd2ArgumentParser()
    units_parser.add_argument("-s", "--start", type=int, default=1, help="First unit id to probe, inclusive (default: 1)")
    units_parser.add_argument("-e", "--end", type=int, default=248, help="Last unit id to probe, exclusive (default: 248)")
    units_parser.add_argument("-i", "--identify", action="store_true", help="Also attempt to read device identification objects for each responsive unit id")
    # fmt: on

    @cmd2.with_argparser(units_parser)
    def do_units(self, args) -> None:
        """Discover which unit/slave identifiers respond on this connection."""
        logging.info("Scanning unit ids %d-%d...", args.start, args.end - 1)
        with self.console.status("Scanning unit ids..."):
            unit_ids = self.conn.get_unit_ids(start=args.start, end=args.end)

        if not unit_ids:
            return logging.warning("No responsive unit ids found")

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Unit ID", justify="right")
        if args.identify:
            table.add_column("Vendor", justify="left")
            table.add_column("Product", justify="left")
            table.add_column("Revision", justify="left")

        for unit_id in unit_ids:
            row = [str(unit_id)]
            if args.identify:
                vendor = product = revision = ""
                try:
                    info = self.conn.read_device_information(unit_id=unit_id)
                    vendor, product, revision = (
                        _decode(info.get(0)),
                        _decode(info.get(1)),
                        _decode(info.get(2)),
                    )
                except ModbusProtocolError:
                    pass  # not every device implements FC43 - leave columns blank
                row.extend([vendor, product, revision])
            table.add_row(*row)

        self.console.print(table)

    do_u = do_units

    # fmt: off
    discover_parser = cmd2.Cmd2ArgumentParser()
    discover_parser.add_argument("table", choices=list(_TABLES), nargs="?", default=None, help="Modbus data table to scan (default: scan all tables)")
    discover_parser.add_argument("-s", "--start", type=int, default=0, help="Zero-based starting address, inclusive (default: 0)")
    discover_parser.add_argument("-e", "--end", type=int, default=1000, help="Ending address, exclusive (default: 1000; widen e.g. --end 65536 for an exhaustive but much slower scan)")
    discover_parser.add_argument("-b", "--block-size", type=int, default=None, help="Maximum addresses to probe per request (default: table's protocol maximum)")
    # fmt: on

    @cmd2.with_argparser(discover_parser)
    def do_discover(self, args) -> None:
        """Discover which coil/register addresses are implemented on the target."""
        tables = [args.table] if args.table else list(_TABLES)

        result = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        result.add_column("Table", justify="left")
        result.add_column("Range", justify="left")
        result.add_column("Count", justify="right")

        found_any = False
        for table_name in tables:
            logging.info(
                "Scanning '%s' table, addresses %d-%d...",
                table_name,
                args.start,
                args.end - 1,
            )
            with self.console.status(f"Scanning '{table_name}' table..."):
                ranges = self.conn.get_table(
                    table_name,
                    start=args.start,
                    end=args.end,
                    block_size=args.block_size,
                )

            if not ranges:
                result.add_row(table_name, "-", "0")
                continue

            found_any = True
            for address_range in ranges:
                result.add_row(table_name, str(address_range), str(address_range.count))

        self.console.print(result)
        if not found_any:
            logging.warning(
                "No addresses found in %d-%d; try widening the range with --end",
                args.start,
                args.end,
            )

    do_d = do_discover
    do_scan = do_discover

    @override
    def pexcept(self, msg: Any, *, end: str = "\n", apply_style: bool = True) -> None:
        match msg:
            case ModbusProtocolError():
                return logging.error("Modbus request failed: %s", msg)
            case ConnectionClosedError():
                return logging.warning(str(msg))

        return super().pexcept(msg, end=end, apply_style=apply_style)


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
                if hasattr(ModbusClient, parser_name):
                    getattr(ModbusClient, parser_name).print_help()
                else:
                    parser.error(f"no such command: {values}")
            parser.exit()

    EPILOG = """\
    Examples:
        modbusclient.py <host> id
        modbusclient.py <host> read holding 0 -c 4
        modbusclient.py <host> write holding 0 1234
        modbusclient.py <host> write coils 0 true false true
        modbusclient.py --udp <host> read holding 0 -c 4
        modbusclient.py <host> units
        modbusclient.py <host> units --identify
        modbusclient.py <host> discover
        modbusclient.py <host> discover holding --end 65536
        modbusclient.py <host> -i           # drop into an interactive shell
        modbusclient.py <host>              # (no command) also starts the shell
    """

    parser = argparse.ArgumentParser(
        usage="%(prog)s [options] host [command [args...]]",
        description="Modbus TCP utility to read/write coils and registers",
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

    add_modbus_connection_options(parser)
    add_logging_options(parser)

    args, remaining = parser.parse_known_args()
    args.console = Console()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    conn = init_modbus_connection(
        args.host, args.port, args.unit, args.timeout, args.transport
    )
    if conn is None:
        sys.exit(1)

    client = ModbusClient(conn)
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
            logging.debug("Closing Modbus connection...")
            conn.close()
        except ConnectionClosedError:
            logging.debug("Connection was already closed by remote peer")


if __name__ == "__main__":
    cli_main()
