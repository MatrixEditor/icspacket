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
# Very basic approach to interact with a remote OPC-UA peer. Currently, it
# supports the following operations:
#
#   - Endpoints: discover (no authentication required)
#   - Nodes: browse, read, write
#   - Subscriptions: data-change notifications
import ast
import logging
import sys
import textwrap
import time

from asyncua import ua
from rich.live import Live
from rich.markup import escape
from rich.table import Table
from rich.tree import Tree

from icspacket.core.connection import (
    ConnectionClosedError,
)
from icspacket.core.connection import (
    ConnectionError as ICSConnectionError,
)
from icspacket.examples.util import add_logging_options
from icspacket.examples.util.opcua import (
    add_opcua_connection_options,
    init_opcua_connection,
)
from icspacket.proto.opcua.connection import (
    BrowseNode,
    OPCUA_Connection,
    OPCUAProtocolError,
    discover_endpoints,
)


def do_endpoints(args, conn: OPCUA_Connection | None) -> None:
    address = args.host if "://" in args.host else (args.host, args.port)
    logging.info(f"Discovering endpoints at {args.host}...")
    try:
        endpoints = discover_endpoints(address, timeout=args.timeout)
    except ICSConnectionError as e:
        logging.error("Endpoint discovery failed: %s", e)
        sys.exit(1)

    table = Table(title=f"OPC-UA endpoints at {args.host}")
    table.add_column("Endpoint URL")
    table.add_column("Security Policy")
    table.add_column("Security Mode")
    table.add_column("User Token Types")
    for ep in endpoints:
        policy = ep.SecurityPolicyUri.rsplit("#", 1)[-1] if ep.SecurityPolicyUri else "None"
        mode = ua.MessageSecurityMode(ep.SecurityMode).name.rstrip("_")
        tokens = ", ".join(sorted({token.TokenType.name for token in ep.UserIdentityTokens})) or "-"
        table.add_row(ep.EndpointUrl, policy, mode, tokens)
    args.console.print(table)


def _node_label(node: BrowseNode) -> str:
    name = node.display_name or node.browse_name or node.node_id.to_string()
    label = f"{escape(name)}  [dim]\\[{node.node_class.name}][/dim] [dim]{escape(node.node_id.to_string())}[/dim]"
    if node.value is not None:
        label += f"\n    [italic]= {escape(repr(node.value))}[/italic]"
    return label


def _add_nodes(tree: Tree, nodes: list[BrowseNode]) -> None:
    for node in nodes:
        branch = tree.add(_node_label(node))
        if node.children:
            _add_nodes(branch, node.children)


def do_browse(args, conn: OPCUA_Connection) -> None:
    root_label = args.node or "Objects"
    logging.info(f"Browsing children of {root_label}...")

    kwargs = {"recursive": args.recursive, "values": args.values}
    if args.maxdepth is not None:
        kwargs["max_depth"] = args.maxdepth

    with args.console.status("Browsing..."):
        children = conn.browse_details(args.node, **kwargs)

    root = Tree(f"[bold]{escape(root_label)}[/]")
    with Live(root, vertical_overflow="visible", console=args.console):
        _add_nodes(root, children)


def do_read(args, conn: OPCUA_Connection) -> None:
    logging.info(f"Reading value of {args.node}...")
    value = conn.read_value(args.node)
    args.console.print(f"[bold]{args.node}[/] = {value!r}")


def do_write(args, conn: OPCUA_Connection) -> None:
    try:
        value = ast.literal_eval(args.value)
    except (ValueError, SyntaxError):
        value = args.value

    logging.info(f"Writing {value!r} to {args.node}...")
    conn.write_value(args.node, value)
    logging.info("Write operation succeeded")


def do_subscribe(args, conn: OPCUA_Connection) -> None:
    logging.info(
        f"Subscribing to {len(args.node)} node(s) (interval={args.interval}ms)..."
    )
    sub = conn.create_subscription(args.node, interval=args.interval)
    deadline = time.monotonic() + args.duration if args.duration else None
    received = 0

    try:
        while deadline is None or time.monotonic() < deadline:
            poll_timeout = 1.0
            if deadline is not None:
                poll_timeout = min(poll_timeout, max(0.0, deadline - time.monotonic()))

            event = sub.next_event(timeout=poll_timeout)
            if event is None:
                continue

            value = getattr(event, "value", event)
            node = getattr(event, "node", "?")
            args.console.print(f"[bold]{node}[/] = {value!r}")
            received += 1
            if args.count and received >= args.count:
                break
    except KeyboardInterrupt:
        logging.info("Subscription cancelled by user")
    finally:
        logging.debug(f"Closing subscription ({received} event(s) received)...")
        sub.close()


def cli_main() -> None:
    import argparse

    from rich.console import Console

    from icspacket import __version__
    from icspacket.core import logger

    EPILOG = """\
    Examples:
        opcuaclient.py endpoints <host>
        opcuaclient.py browse <host>
        opcuaclient.py browse "ns=2;i=1" <host>
        opcuaclient.py browse --recursive --values <host>
        opcuaclient.py browse -r --maxdepth 3 <host>
        opcuaclient.py read "ns=2;i=2" <host>
        opcuaclient.py write "ns=2;i=3" "'FAULT'" <host>
        opcuaclient.py subscribe "ns=2;i=2" "ns=2;i=4" --duration 30 <host>

    Note: <host> must always be the last argument on the command line --
    "subscribe" options (--interval/--duration/--count) are consumed by
    argparse's subparser and must appear *before* <host>, not after it.
    """

    parser = argparse.ArgumentParser(
        description="OPC-UA utility to discover, browse, read/write and subscribe to node values",
        epilog=textwrap.dedent(EPILOG),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # fmt: off
    # ------------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------------
    services = parser.add_subparsers(title="Services", description="Available OPC-UA service operations", metavar="SERVICE")

    endpoints = services.add_parser("endpoints", aliases=["e", "discover"], help="Discover server endpoints (security policies/modes/user tokens) without authenticating")
    endpoints.set_defaults(func=do_endpoints, needs_connection=False)

    browse = services.add_parser("browse", aliases=["b"], help="List the children of a node")
    browse.set_defaults(func=do_browse)
    browse.add_argument("node", nargs="?", default=None, help="NodeId to browse (default: Objects folder)")
    browse.add_argument("-r", "--recursive", action="store_true", default=False, help="Recursively browse into child nodes instead of a single level")
    browse.add_argument("--maxdepth", type=int, metavar="DEPTH", default=None, help="Maximum depth to descend when --recursive is set (default: 10)")
    browse.add_argument("-V", "--values", action="store_true", default=False, help="Read and display the current value of each Variable node")

    read = services.add_parser("read", aliases=["r"], help="Read a node's current value")
    read.set_defaults(func=do_read)
    read.add_argument("node", type=str, help="NodeId to read, e.g. 'ns=2;i=2'")

    write = services.add_parser("write", aliases=["w"], help="Write a node's value")
    write.set_defaults(func=do_write)
    write.add_argument("node", type=str, help="NodeId to write, e.g. 'ns=2;i=3'")
    write.add_argument("value", type=str, help="Value to write (parsed as a Python literal if possible)")

    subscribe = services.add_parser("subscribe", aliases=["sub", "s"], help="Subscribe to data-change notifications for one or more nodes")
    subscribe.set_defaults(func=do_subscribe)
    subscribe.add_argument("node", type=str, nargs="+", help="One or more NodeIds to monitor for value changes")
    subscribe.add_argument("--interval", type=float, metavar="MS", default=500.0, help="Requested publishing interval in milliseconds (default: 500)")
    subscribe.add_argument("--duration", type=float, metavar="SEC", default=None, help="Stop after this many seconds (default: run until Ctrl+C)")
    subscribe.add_argument("--count", type=int, metavar="N", default=None, help="Stop after receiving this many events (default: unlimited)")
    # fmt: on

    add_opcua_connection_options(parser)
    add_logging_options(parser)

    args = parser.parse_args()
    args.console = Console()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    func = getattr(args, "func", None)
    if func is None:
        logging.error("No service selected, quitting...")
        sys.exit(1)

    conn = None
    if getattr(args, "needs_connection", True):
        conn = init_opcua_connection(
            args.host,
            args.port,
            args.timeout,
            args.username,
            args.password,
            args.security_policy,
            args.security_mode,
            args.certificate,
            args.private_key,
            args.private_key_password,
            args.server_certificate,
            args.user_certificate,
            args.user_private_key,
            args.user_private_key_password,
        )
        if conn is None:
            sys.exit(1)

    try:
        func(args, conn)
    except OPCUAProtocolError as e:
        logging.error("OPC-UA request failed: %s", e)
    except ICSConnectionError as e:
        logging.error("OPC-UA connection error: %s", e)
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user...")
    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)
        sys.exit(1)
    finally:
        if conn is not None:
            try:
                logging.debug("Closing OPC-UA connection...")
                conn.close()
            except ConnectionClosedError:
                logging.debug("Connection was already closed by remote peer")


if __name__ == "__main__":
    cli_main()
