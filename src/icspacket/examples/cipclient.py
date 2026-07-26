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
# EtherNet/IP/CIP utility for discovery, explicit messages, and connection
# manager requests.
import argparse
import dataclasses
import logging
import sys
import textwrap
import time

from rich import box
from rich.table import Table

from icspacket.core.connection import ConnectionClosedError
from icspacket.examples.util import add_logging_options
from icspacket.examples.util.cip import (
    add_cip_connection_options,
    add_cip_target_argument,
    init_cip_connection,
)
from icspacket.proto.cip.connection import CIP_Connection, CIPProtocolError
from icspacket.proto.cip.connmgr import (
    ForwardCloseRequest,
    ForwardOpenRequest,
    LargeForwardOpenRequest,
    LargeNetworkConnectionParameters,
    NetworkConnectionParameters,
    NetworkConnectionType,
)
from icspacket.proto.cip.const import CIPStatusError, ClassCode, CommonService
from icspacket.proto.cip.epath import EPATH, LogicalSegment
from icspacket.proto.cip.io import CIPIO_Connection
from icspacket.proto.cip.msgrouter import MessageRouterRequest, MultipleServicePacket
from icspacket.proto.cip.objects._base import CIPAttributeReader, CIPObject
from icspacket.proto.cip.objects.assembly import AssemblyObject
from icspacket.proto.cip.objects.identity import IdentityObject
from icspacket.proto.cip.objects.registry import object_for


def _int(value: str) -> int:
    return int(value, 0)


def _hex(value: str) -> bytes:
    normalized = value.replace("0x", "").replace("0X", "")
    normalized = "".join(normalized.split()).replace("_", "")
    if len(normalized) % 2:
        raise ValueError(
            "byte values must contain an even number of hexadecimal digits"
        )
    try:
        return bytes.fromhex(normalized)
    except ValueError as exc:
        raise ValueError(f"invalid hexadecimal byte value: {value!r}") from exc


def _text(value: object) -> str:
    if isinstance(value, bytes):
        try:
            return value.decode()
        except UnicodeDecodeError:
            return f"0x{value.hex()}"
    return str(value)


def _bytes(value: bytes) -> str:
    return f"0x{value.hex()}" if value else "(empty)"


def _table(title: str, columns: tuple[str, ...], rows: list[list[str]]) -> Table:
    result = Table(title=title, safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
    for column in columns:
        result.add_column(column)
    for row in rows:
        result.add_row(*row)
    return result


def _resolve_object(conn: CIP_Connection, class_code: int, instance: int) -> CIPObject | None:
    try:
        return object_for(conn, class_code, instance)
    except ValueError:
        return None


def _decode_single(obj: CIPObject | None, instance: int, attribute: int, value: bytes) -> str:
    """Best-effort decode of one attribute's raw bytes via the resolved CIP
    object wrapper's declarative :class:`CIPAttribute` schema, if any.

    Instance 0 addresses class-level attributes (Revision, Max Instance,
    ...), which use a different, common layout that isn't modeled by
    per-instance ``attribute_definitions`` - those are left undecoded.
    """
    if obj is None or instance == 0:
        return "-"
    definition = obj.attribute_definitions.get(attribute)
    if definition is None or definition.schema is None:
        # No schema means the attribute is documented as opaque/raw bytes -
        # from_bytes() would just hand the same bytes back (potentially
        # re-decoded as confusing/invisible text via _text()), so there is
        # nothing meaningful to add beyond the raw "Value" column.
        return "-"
    try:
        return _text(definition.from_bytes(value))
    except Exception:
        return "(decode failed)"


def do_list_identity(args, conn: CIP_Connection) -> None:
    logging.info("Requesting ListIdentity discovery response...")
    items = conn.list_identity()
    rows = [
        [
            _text(item.socket_address.address),
            str(item.socket_address.port),
            str(item.vendor_id),
            str(item.device_type),
            str(item.product_code),
            f"{item.revision_major}.{item.revision_minor}",
            f"0x{item.serial_number:08x}",
            _text(item.product_name),
            str(item.state),
        ]
        for item in items
    ]
    args.console.print(
        _table(
            "ListIdentity",
            (
                "Address",
                "Port",
                "Vendor",
                "Type",
                "Product",
                "Revision",
                "Serial",
                "Name",
                "State",
            ),
            rows,
        )
    )
    if not items:
        logging.warning("No ListIdentity response items received")


def do_list_services(args, conn: CIP_Connection) -> None:
    logging.info("Requesting ListServices discovery response...")
    items = conn.list_services()
    rows = [
        [
            str(item.protocol_version),
            f"0x{item.capability_flags:04x}",
            _text(item.service_name),
        ]
        for item in items
    ]
    args.console.print(
        _table("ListServices", ("Protocol", "Capabilities", "Service"), rows)
    )
    if not items:
        logging.warning("No ListServices response items received")


def do_list_interfaces(args, conn: CIP_Connection) -> None:
    logging.info("Requesting ListInterfaces discovery response...")
    items = conn.list_interfaces()
    rows = [
        [str(item.protocol_version), f"0x{item.capability_flags:04x}"] for item in items
    ]
    args.console.print(_table("ListInterfaces", ("Protocol", "Capabilities"), rows))
    if not items:
        logging.warning("No ListInterfaces response items received")


def do_identity(args, conn: CIP_Connection) -> None:
    logging.info("Reading Identity Object instance %d...", args.instance)
    attrs = IdentityObject(conn, args.instance).get_attributes()
    rows = [
        ["Vendor ID", str(attrs.vendor_id)],
        ["Device Type", str(attrs.device_type)],
        ["Product Code", str(attrs.product_code)],
        ["Revision", f"{attrs.revision_major}.{attrs.revision_minor}"],
        ["Status", f"0x{attrs.status:04x}"],
        ["Serial Number", f"0x{attrs.serial_number:08x}"],
        ["Product Name", attrs.product_name],
        ["State", str(attrs.state)],
    ]
    args.console.print(_table("Identity Object", ("Attribute", "Value"), rows))


def _object_path(class_code: int, instance: int, attribute: int | None = None) -> EPATH:
    segments = [
        LogicalSegment.class_id(class_code),
        LogicalSegment.instance_id(instance),
    ]
    if attribute is not None:
        segments.append(LogicalSegment.attribute_id(attribute))
    return EPATH(*segments)


def _open_class3(conn: CIP_Connection, class_code: int, instance: int) -> None:
    """Open a minimal Class-3 explicit-message connection to (class_code, instance)."""

    conn.forward_open(connection_path=_object_path(class_code, instance))


def do_get(args, conn: CIP_Connection) -> None:
    logging.info(
        "Reading class 0x%x, instance %d, attribute %d...",
        args.class_code,
        args.instance,
        args.attribute,
    )
    if args.connected:
        logging.info(
            "Opening Class-3 connection to class 0x%x instance %d...",
            args.class_code,
            args.instance,
        )
        _open_class3(conn, args.class_code, args.instance)
    try:
        value = conn.generic_message(
            CommonService.GET_ATTRIBUTE_SINGLE,
            _object_path(args.class_code, args.instance, args.attribute),
            connected=args.connected,
        )
    finally:
        if args.connected:
            conn.forward_close()
    obj = _resolve_object(conn, args.class_code, args.instance)
    args.console.print(
        _table(
            "Get_Attribute_Single",
            ("Class", "Instance", "Attribute", "Connected", "Value", "Decoded"),
            [
                [
                    f"0x{args.class_code:x}",
                    str(args.instance),
                    str(args.attribute),
                    str(args.connected),
                    _bytes(value),
                    _decode_single(obj, args.instance, args.attribute, value),
                ]
            ],
        )
    )


def do_set(args, conn: CIP_Connection) -> None:
    value = _hex(args.value)
    logging.info(
        "Writing class 0x%x, instance %d, attribute %d...",
        args.class_code,
        args.instance,
        args.attribute,
    )
    if args.connected:
        logging.info(
            "Opening Class-3 connection to class 0x%x instance %d...",
            args.class_code,
            args.instance,
        )
        _open_class3(conn, args.class_code, args.instance)
    try:
        response = conn.generic_message(
            CommonService.SET_ATTRIBUTE_SINGLE,
            _object_path(args.class_code, args.instance, args.attribute),
            value,
            connected=args.connected,
        )
    finally:
        if args.connected:
            conn.forward_close()
    args.console.print(
        _table(
            "Set_Attribute_Single",
            ("Class", "Instance", "Attribute", "Connected", "Request", "Response"),
            [
                [
                    f"0x{args.class_code:x}",
                    str(args.instance),
                    str(args.attribute),
                    str(args.connected),
                    _bytes(value),
                    _bytes(response),
                ]
            ],
        )
    )


def do_get_all(args, conn: CIP_Connection) -> None:
    logging.info(
        "Reading all attributes of class 0x%x, instance %d...",
        args.class_code,
        args.instance,
    )
    obj = _resolve_object(conn, args.class_code, args.instance)
    if obj is not None and hasattr(obj, "get_attributes"):
        # Identity/TCP-IP-Interface/Ethernet-Link define a standard
        # Get_Attributes_All layout (CIP Vol 1 §5-2.3.2 / Vol 2 §5-4.4.2,
        # §5-5.3.2) that can be decoded into typed fields.
        attributes = obj.get_attributes()
        rows = [
            [field.name, str(getattr(attributes, field.name))]
            for field in dataclasses.fields(attributes)
        ]
        args.console.print(
            _table(
                f"Get_Attributes_All (class 0x{args.class_code:x}, instance {args.instance})",
                ("Attribute", "Value"),
                rows,
            )
        )
        return

    value = conn.get_attributes_all(args.class_code, args.instance)
    if obj is not None and obj.attribute_definitions and args.instance != 0:
        # Generic fallback for every other registered object: decode as
        # many declared attributes as possible, in ascending attribute-ID
        # order (CIP Vol 1 §4-4.4). CIPAttribute.stream_decodable stops the
        # walk cleanly at the first attribute that isn't safely
        # self-delimiting mid-stream, so any remainder is shown raw instead
        # of being misdecoded.
        try:
            reader = CIPAttributeReader(value)
            decoded = reader.read_attributes(obj.attribute_definitions)
            remainder = reader.read_remaining()
        except Exception:
            decoded, remainder = {}, b""
        if decoded:
            rows = [
                [
                    str(attribute),
                    obj.attribute_definitions[attribute].attr_name,
                    _text(decoded_value),
                ]
                for attribute, decoded_value in decoded.items()
            ]
            if remainder:
                rows.append(["-", "(undecoded remainder)", _bytes(remainder)])
            args.console.print(
                _table(
                    f"Get_Attributes_All (class 0x{args.class_code:x}, instance {args.instance})",
                    ("Attribute", "Name", "Value"),
                    rows,
                )
            )
            return

    # No declarative attribute schema is available for this class/instance
    # (e.g. Assembly/Connection/Connection Manager, CIP Vol 1 §5-5/§5-6/
    # §5-7, or a class-level instance 0 request) - fall back to displaying
    # the raw response bytes.
    args.console.print(
        _table(
            "Get_Attributes_All (raw)",
            ("Class", "Instance", "Value"),
            [[f"0x{args.class_code:x}", str(args.instance), _bytes(value)]],
        )
    )


def do_assembly_get(args, conn: CIP_Connection) -> None:
    logging.info("Reading Assembly instance %d data...", args.instance)
    data = AssemblyObject(conn, args.instance).data
    args.console.print(
        _table(
            "Assembly Data", ("Instance", "Value"), [[str(args.instance), _bytes(data)]]
        )
    )


def do_assembly_set(args, conn: CIP_Connection) -> None:
    value = _hex(args.value)
    logging.info(
        "Writing Assembly instance %d data (%d bytes)...", args.instance, len(value)
    )
    AssemblyObject(conn, args.instance).data = value
    args.console.print(
        _table(
            "Assembly Data",
            ("Instance", "Written"),
            [[str(args.instance), _bytes(value)]],
        )
    )


def do_unconnected_send(args, conn: CIP_Connection) -> None:
    path = _object_path(args.class_code, args.instance, args.attribute)
    request_data = _hex(args.data) if args.data else b""
    route_path = EPATH.from_bytes(_hex(args.route_path)) if args.route_path else EPATH()
    message = MessageRouterRequest.new(args.service, path, request_data)
    logging.info(
        "Sending Unconnected_Send (service 0x%x, class 0x%x, instance %d) via route path %s...",
        args.service,
        args.class_code,
        args.instance,
        args.route_path or "(local)",
    )
    response = conn.unconnected_send(
        message, route_path, priority=args.priority, timeout_ticks=args.timeout_ticks
    )
    args.console.print(
        _table(
            "Unconnected_Send",
            ("Service", "Class", "Instance", "Attribute", "Status", "Response"),
            [
                [
                    f"0x{args.service:x}",
                    f"0x{args.class_code:x}",
                    str(args.instance),
                    str(args.attribute) if args.attribute is not None else "-",
                    str(response.general_status),
                    _bytes(response.response_data),
                ]
            ],
        )
    )


def _multi_request(value: str) -> MessageRouterRequest:
    parts = value.split(":")
    if len(parts) < 3:
        raise ValueError(
            f"invalid multi-service request {value!r}; expected SERVICE:CLASS:INSTANCE[:ATTRIBUTE[:DATA]]"
        )
    service = _int(parts[0])
    class_code = _int(parts[1])
    instance = _int(parts[2])
    attribute = _int(parts[3]) if len(parts) > 3 and parts[3] not in ("", "-") else None
    data = _hex(parts[4]) if len(parts) > 4 and parts[4] else b""
    return MessageRouterRequest.new(
        service, _object_path(class_code, instance, attribute), data
    )


def do_multi(args, conn: CIP_Connection) -> None:
    packet = MultipleServicePacket()
    raw_multi = packet.build(args.requests)
    path = _object_path(ClassCode.MESSAGE_ROUTER, 1)
    if args.connected:
        logging.info("Opening Class-3 connection to the Message Router...")
        _open_class3(conn, ClassCode.MESSAGE_ROUTER, 1)
    logging.info(
        "Sending Multiple_Service_Packet with %d embedded service(s)...",
        len(args.requests),
    )
    try:
        raw = conn.generic_message(
            CommonService.MULTIPLE_SERVICE_PACKET,
            path,
            raw_multi,
            connected=args.connected,
        )
    finally:
        if args.connected:
            conn.forward_close()
    replies = MultipleServicePacket.from_bytes(raw).decode_replies()
    rows = [
        [
            str(index),
            f"0x{request.service:x}",
            str(reply.general_status),
            _bytes(reply.response_data),
        ]
        for index, (request, reply) in enumerate(zip(args.requests, replies))
    ]
    args.console.print(
        _table("Multiple_Service_Packet", ("#", "Service", "Status", "Response"), rows)
    )


def do_io_connect(args, conn: CIP_Connection) -> None:
    path = _path(args)
    params_cls = (
        LargeNetworkConnectionParameters if args.large else NetworkConnectionParameters
    )
    common = dict(
        priority=args.priority,
        timeout_ticks=args.timeout_ticks,
        o_to_t_connection_id=args.o_to_t_connection_id,
        t_to_o_connection_id=args.t_to_o_connection_id,
        connection_serial_number=args.connection_serial_number,
        originator_vendor_id=args.originator_vendor_id,
        originator_serial_number=args.originator_serial_number,
        timeout_multiplier=args.timeout_multiplier,
        o_to_t_rpi=args.o_to_t_rpi,
        o_to_t_parameters=params_cls(**_connection_parameters(args, "o_to_t")),
        t_to_o_rpi=args.t_to_o_rpi,
        t_to_o_parameters=params_cls(**_connection_parameters(args, "t_to_o")),
        transport_trigger=args.transport_trigger,
        connection_path=path,
    )
    request = (
        LargeForwardOpenRequest.new(**common)
        if args.large
        else ForwardOpenRequest.new(**common)
    )
    logging.info(
        "Sending %s request...", "Large_Forward_Open" if args.large else "Forward_Open"
    )
    response = conn.forward_open(request)
    logging.info(
        "Opening Class 0/1 I/O connection (O->T id=0x%08x, T->O id=0x%08x)...",
        response.o_to_t_connection_id,
        response.t_to_o_connection_id,
    )
    address = (conn.address[0], args.io_port) if args.io_port and conn.address else None
    conn.open_io_connection(
        response,
        address=address,
        header_format=not args.no_header_format,
        sequence_format=not args.no_sequence_format,
    )
    try:
        # `data` is already decoded by the `type=_hex` positional converter.
        data = args.data
        rows = []
        for cycle in range(args.cycles):
            conn.send_io_data(data)
            received = conn.recv_io_data()
            rows.append([str(cycle), _bytes(data), _bytes(received)])
            if cycle + 1 < args.cycles:
                time.sleep(args.interval)
        args.console.print(
            _table(
                "Class 0/1 I/O Exchange",
                ("Cycle", "Sent (O->T)", "Received (T->O)"),
                rows,
            )
        )
    finally:
        conn.close_io_connection()
        logging.info("Sending Forward_Close request...")
        conn.forward_close()


def _connection_parameters(args, prefix: str) -> dict:
    return dict(
        connection_size=getattr(args, f"{prefix}_size"),
        variable=getattr(args, f"{prefix}_variable"),
        priority=getattr(args, f"{prefix}_priority"),
        connection_type=getattr(args, f"{prefix}_type"),
        redundant_owner=getattr(args, f"{prefix}_redundant"),
    )


def _path(args):
    if (
        getattr(args, "o_to_t_connection_point", None) is not None
        or getattr(args, "t_to_o_connection_point", None) is not None
    ):
        # Assembly-object I/O connection path (CIP Vol 1, §3-4.3 / EIPScanner
        # convention): Class, Instance(config), ConnectionPoint(O->T),
        # ConnectionPoint(T->O), as empirically confirmed against lab/cip-io.
        segments = [
            LogicalSegment.class_id(args.path_class),
            LogicalSegment.instance_id(args.path_instance),
        ]
        if args.o_to_t_connection_point is not None:
            segments.append(
                LogicalSegment.connection_point(args.o_to_t_connection_point)
            )
        if args.t_to_o_connection_point is not None:
            segments.append(
                LogicalSegment.connection_point(args.t_to_o_connection_point)
            )
        return EPATH(*segments)
    return EPATH(
        LogicalSegment.class_id(args.path_class),
        LogicalSegment.instance_id(args.path_instance),
    )


def do_forward_open(args, conn: CIP_Connection) -> None:
    path = _path(args)
    params_cls = (
        LargeNetworkConnectionParameters if args.large else NetworkConnectionParameters
    )
    common = dict(
        priority=args.priority,
        timeout_ticks=args.timeout_ticks,
        o_to_t_connection_id=args.o_to_t_connection_id,
        t_to_o_connection_id=args.t_to_o_connection_id,
        connection_serial_number=args.connection_serial_number,
        originator_vendor_id=args.originator_vendor_id,
        originator_serial_number=args.originator_serial_number,
        timeout_multiplier=args.timeout_multiplier,
        o_to_t_rpi=args.o_to_t_rpi,
        o_to_t_parameters=params_cls(**_connection_parameters(args, "o_to_t")),
        t_to_o_rpi=args.t_to_o_rpi,
        t_to_o_parameters=params_cls(**_connection_parameters(args, "t_to_o")),
        transport_trigger=args.transport_trigger,
        connection_path=path,
    )
    request = (
        LargeForwardOpenRequest.new(**common)
        if args.large
        else ForwardOpenRequest.new(**common)
    )
    logging.info(
        "Sending %s request...", "Large_Forward_Open" if args.large else "Forward_Open"
    )
    response = conn.forward_open(request)
    args.console.print(
        _table(
            "Large_Forward_Open" if args.large else "Forward_Open",
            (
                "O->T Connection ID",
                "T->O Connection ID",
                "Serial",
                "Vendor",
                "Originator Serial",
                "O->T API",
                "T->O API",
                "Reply Data",
            ),
            [
                [
                    f"0x{response.o_to_t_connection_id:08x}",
                    f"0x{response.t_to_o_connection_id:08x}",
                    f"0x{response.connection_serial_number:04x}",
                    str(response.originator_vendor_id),
                    f"0x{response.originator_serial_number:08x}",
                    str(response.o_to_t_api),
                    str(response.t_to_o_api),
                    _bytes(response.application_reply_data),
                ]
            ],
        )
    )


def do_forward_close(args, conn: CIP_Connection) -> None:
    logging.info("Sending Forward_Close request...")
    response = conn.forward_close(
        ForwardCloseRequest.new(
            priority=args.priority,
            timeout_ticks=args.timeout_ticks,
            connection_serial_number=args.connection_serial_number,
            originator_vendor_id=args.originator_vendor_id,
            originator_serial_number=args.originator_serial_number,
            connection_path=_path(args),
        )
    )
    args.console.print(
        _table(
            "Forward_Close",
            ("Connection Serial", "Vendor", "Originator Serial", "Reply Data"),
            [
                [
                    f"0x{response.connection_serial_number:04x}",
                    str(response.originator_vendor_id),
                    f"0x{response.originator_serial_number:08x}",
                    _bytes(response.application_reply_data),
                ]
            ],
        )
    )


def _add_connection_id_options(
    parser: argparse.ArgumentParser, *, connection_ids: bool = False
) -> None:
    """Register the connection identification triple shared by Forward_Open,
    Forward_Close, and Large_Forward_Open.

    :param connection_ids: Also register the O->T/T->O connection ID pair
        that only Forward_Open/Large_Forward_Open assign.
    """

    group = parser.add_argument_group(
        "Connection Identification",
        "Identifies this connection instance to the target device",
    )
    group.add_argument(
        "--conn-serial", type=_int, default=0, dest="connection_serial_number",
        help="Serial number distinguishing this connection from others the originator has opened (default: 0)",
    )
    group.add_argument(
        "--orig-vendor-id", type=_int, default=0, dest="originator_vendor_id",
        help="Vendor ID identifying the originating device (default: 0)",
    )
    group.add_argument(
        "--orig-serial-number", type=_int, default=0, dest="originator_serial_number",
        help="Serial number identifying the originating device (default: 0)",
    )
    if connection_ids:
        group.add_argument(
            "--o2t-conn-id", type=_int, default=0, dest="o_to_t_connection_id",
            help="Connection ID this request assigns to the O->T (originator to target) direction (default: 0)",
        )
        group.add_argument(
            "--t2o-conn-id", type=_int, default=0, dest="t_to_o_connection_id",
            help="Connection ID this request assigns to the T->O (target to originator) direction (default: 0)",
        )


def _add_timing_options(
    parser: argparse.ArgumentParser, *, forward_open: bool = False
) -> None:
    """Register the Priority/Time_tick timeout pair shared by every
    Connection Manager request.

    :param forward_open: Also register the timeout multiplier and transport
        trigger fields that only Forward_Open/Large_Forward_Open carry.
    """

    group = parser.add_argument_group(
        "Timing",
        "Controls how long the target waits before timing out this request or connection",
    )
    group.add_argument(
        "--priority", type=_int, default=0,
        help="Priority/Time_tick value, paired with --timeout-ticks to determine the request timeout (default: 0)",
    )
    group.add_argument(
        "--timeout-ticks", type=_int, default=0,
        help="Tick count, paired with --priority's Time_tick value to determine the request timeout (default: 0)",
    )
    if forward_open:
        group.add_argument(
            "--timeout-multiplier", type=_int, default=0,
            help="Scale factor the target applies to the RPI when deriving this connection's inactivity timeout (default: 0)",
        )
        group.add_argument(
            "--transport-trigger", type=_int, default=0,
            help="Byte selecting this connection's transport class and production trigger behavior (default: 0)",
        )


#: (CLI flag prefix, attribute prefix, direction label, direction phrase)
#: driving the per-direction Network Connection Parameters options below.
_DIRECTIONS = (
    ("o2t", "o_to_t", "O->T", "originator to target"),
    ("t2o", "t_to_o", "T->O", "target to originator"),
)


def _add_connection_parameters_options(parser: argparse.ArgumentParser) -> None:
    """Register the per-direction RPI and Network Connection Parameters
    options used by Forward_Open/Large_Forward_Open, one argument group per
    data flow direction."""

    type_choices = ", ".join(f"{int(item)}={item.name}" for item in NetworkConnectionType)
    for flag_prefix, dest_prefix, label, direction in _DIRECTIONS:
        group = parser.add_argument_group(
            f"Network Connection Parameters ({label})",
            f"Data size, framing, and packet interval for the {direction} data flow",
        )
        group.add_argument(
            f"--{flag_prefix}-rpi", type=_int, default=0, dest=f"{dest_prefix}_rpi",
            help=f"Requested packet interval, in microseconds, for {direction} data (default: 0)",
        )
        group.add_argument(
            f"--{flag_prefix}-size", type=_int, default=0, dest=f"{dest_prefix}_size",
            help=f"Largest data size, in bytes, the {label} connection will carry (default: 0)",
        )
        group.add_argument(
            f"--{flag_prefix}-priority", type=_int, default=0, dest=f"{dest_prefix}_priority",
            help=f"{label} connection priority level: 0=Low, 1=High, 2=Scheduled, 3=Urgent (default: 0)",
        )
        group.add_argument(
            f"--{flag_prefix}-type", type=_int, default=0, dest=f"{dest_prefix}_type",
            choices=[int(item) for item in NetworkConnectionType],
            help=f"{label} connection type: {type_choices} (default: 0)",
        )
        group.add_argument(
            f"--{flag_prefix}-variable", action="store_true", dest=f"{dest_prefix}_variable",
            help=f"Use variable- rather than fixed-size framing for the {label} connection",
        )
        group.add_argument(
            f"--{flag_prefix}-redundant", action="store_true", dest=f"{dest_prefix}_redundant",
            help=f"Allow the {label} connection to be held open by more than one owner at a time",
        )


def _add_path_options(parser: argparse.ArgumentParser) -> None:
    """Register the Connection Path options identifying the object instance
    a connection is opened to, plus the optional Assembly connection points
    used by Class 0/1 I/O connections."""

    group = parser.add_argument_group(
        "Connection Path",
        "Identifies the object instance this connection is opened to",
    )
    group.add_argument(
        "--path-class", type=_int, default=0x04,
        help="Connection path class (default: 0x04)",
    )
    group.add_argument(
        "--path-instance", type=_int, default=1,
        help="Connection path instance (default: 1)",
    )
    group.add_argument(
        "--o2t-conn-point", type=_int, default=None, dest="o_to_t_connection_point",
        help="Assembly connection point for O->T data; appends a ConnectionPoint segment (e.g. output assembly)",
    )
    group.add_argument(
        "--t2o-conn-point", type=_int, default=None, dest="t_to_o_connection_point",
        help="Assembly connection point for T->O data; appends a ConnectionPoint segment (e.g. input assembly)",
    )


def _add_forward_open_options(parser: argparse.ArgumentParser) -> None:
    """Register every option shared by Forward_Open and io-connect: request
    size, timing, connection identification, per-direction network
    connection parameters, and connection path."""

    parser.add_argument(
        "--large",
        action="store_true",
        help="Use Large_Forward_Open and 32-bit connection parameters",
    )
    _add_timing_options(parser, forward_open=True)
    _add_connection_id_options(parser, connection_ids=True)
    _add_connection_parameters_options(parser)
    _add_path_options(parser)


def cli_main() -> None:
    import argparse

    from rich.console import Console
    from icspacket import __version__
    from icspacket.core import logger

    EPILOG = """\
    Examples:
        cipclient.py list-identity <host>
        cipclient.py list-services <host>
        cipclient.py list-interfaces <host>
        cipclient.py identity <host>
        cipclient.py get 0x04 1 3 <host>
        cipclient.py get 0x04 1 3 --connected <host>
        cipclient.py set 0x04 1 3 deadbeef <host>
        cipclient.py get-all 0x01 1 <host>
        cipclient.py assembly-get 100 <host>
        cipclient.py assembly-set 150 aabbccdd <host>
        cipclient.py unconnected-send 0xe 0x01 1 1 <host>
        cipclient.py multi 0xe:0x1:1:1 0xe:0x1:1:7 <host>
        cipclient.py forward-open --path-class 0x04 --path-instance 1 <host>
        cipclient.py forward-close --conn-serial 1 <host>
        cipclient.py io-connect 00000000000000000000000000000000 \\
            --path-class 0x04 --path-instance 151 \\
            --o2t-conn-point 150 --t2o-conn-point 100 \\
            --conn-serial 1 --orig-vendor-id 1 --orig-serial-number 1 \\
            --o2t-conn-id 1 --t2o-conn-id 2 --cycles 5 <host>
    """
    parser = argparse.ArgumentParser(
        description="EtherNet/IP/CIP utility for discovery and explicit messages",
        epilog=textwrap.dedent(EPILOG),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # fmt: off
    services = parser.add_subparsers(
        title="Services",
        description="Available CIP service operations",
        metavar="SERVICE",
    )
    list_identity = services.add_parser("list-identity", aliases=["li"], help="Discover target identity information")
    list_identity.set_defaults(func=do_list_identity)
    list_services = services.add_parser("list-services", aliases=["ls"], help="Discover EtherNet/IP services")
    list_services.set_defaults(func=do_list_services)
    list_interfaces = services.add_parser("list-interfaces", aliases=["lif"], help="Discover EtherNet/IP interfaces")
    list_interfaces.set_defaults(func=do_list_interfaces)
    identity = services.add_parser("identity", aliases=["id"], help="Inspect the CIP Identity Object")
    identity.set_defaults(func=do_identity)
    identity.add_argument("-i", "--instance", type=_int, default=1, help="Identity Object instance (default: 1)")
    get = services.add_parser(
        "get",
        aliases=["read", "get-attribute-single"],
        help="Get_Attribute_Single by class, instance, and attribute",
    )
    get.set_defaults(func=do_get)
    get.add_argument("class_code", type=_int, help="CIP class code")
    get.add_argument("instance", type=_int, help="CIP object instance")
    get.add_argument("attribute", type=_int, help="CIP attribute ID")
    get.add_argument(
        "--connected", action="store_true",
        help="Open a Class-3 connection to (class, instance) and send the request over it",
    )
    set_attribute = services.add_parser(
        "set",
        aliases=["write", "set-attribute-single"],
        help="Set_Attribute_Single by class, instance, and attribute",
    )
    set_attribute.set_defaults(func=do_set)
    set_attribute.add_argument("class_code", type=_int, help="CIP class code")
    set_attribute.add_argument("instance", type=_int, help="CIP object instance")
    set_attribute.add_argument("attribute", type=_int, help="CIP attribute ID")
    set_attribute.add_argument("value", help="Value as hexadecimal bytes, e.g. deadbeef")
    set_attribute.add_argument(
        "--connected", action="store_true",
        help="Open a Class-3 connection to (class, instance) and send the request over it",
    )
    get_all = services.add_parser(
        "get-all",
        aliases=["gall", "get-attributes-all"],
        help="Get_Attributes_All by class and instance",
    )
    get_all.set_defaults(func=do_get_all)
    get_all.add_argument("class_code", type=_int, help="CIP class code")
    get_all.add_argument("instance", type=_int, help="CIP object instance")
    assembly_get = services.add_parser(
        "assembly-get", aliases=["asm-get"], help="Read Assembly Object instance data (attribute 3)"
    )
    assembly_get.set_defaults(func=do_assembly_get)
    assembly_get.add_argument("instance", type=_int, help="Assembly instance")
    assembly_set = services.add_parser(
        "assembly-set", aliases=["asm-set"], help="Write Assembly Object instance data (attribute 3)"
    )
    assembly_set.set_defaults(func=do_assembly_set)
    assembly_set.add_argument("instance", type=_int, help="Assembly instance")
    assembly_set.add_argument("value", help="Value as hexadecimal bytes, e.g. deadbeef")
    unconnected_send = services.add_parser(
        "unconnected-send",
        aliases=["uc-send"],
        help="Route a Message Router request through Connection Manager Unconnected_Send",
    )
    unconnected_send.set_defaults(func=do_unconnected_send)
    unconnected_send.add_argument("service", type=_int, help="Embedded CIP service code")
    unconnected_send.add_argument("class_code", type=_int, help="Embedded request CIP class code")
    unconnected_send.add_argument("instance", type=_int, help="Embedded request CIP object instance")
    unconnected_send.add_argument("attribute", type=_int, nargs="?", default=None, help="Embedded request CIP attribute ID")
    unconnected_send.add_argument("data", nargs="?", default="", help="Embedded request data as hexadecimal bytes")
    routing_group = unconnected_send.add_argument_group(
        "Routing", "Specifies the path to route the embedded request through"
    )
    routing_group.add_argument(
        "--route-path", default="", help="Route path as hexadecimal padded EPATH bytes (default: local)"
    )
    _add_timing_options(unconnected_send)
    multi = services.add_parser(
        "multi",
        aliases=["multi-service", "msp"],
        help="Send several CIP services in one Multiple_Service_Packet request",
    )
    multi.set_defaults(func=do_multi)
    multi.add_argument(
        "requests", nargs="+", type=_multi_request,
        metavar="SERVICE:CLASS:INSTANCE[:ATTRIBUTE[:DATA]]",
        help="One embedded service per argument, e.g. 0xe:0x4:1:3 for Get_Attribute_Single",
    )
    multi.add_argument("--connected", action="store_true", help="Send over an already open Class-3 connection")
    forward_open = services.add_parser("forward-open", aliases=["fo"], help="Open a Class-3 connection through Connection Manager")
    forward_open.set_defaults(func=do_forward_open)
    _add_forward_open_options(forward_open)
    forward_close = services.add_parser("forward-close", aliases=["fc"], help="Close a connection through Connection Manager")
    forward_close.set_defaults(func=do_forward_close)
    _add_timing_options(forward_close)
    _add_connection_id_options(forward_close)
    _add_path_options(forward_close)
    io_connect = services.add_parser(
        "io-connect",
        aliases=["io"],
        help="Open a Class 0/1 cyclic I/O (UDP) connection and exchange assembly data",
    )
    io_connect.set_defaults(func=do_io_connect)
    io_connect.add_argument("data", type=_hex, help="O->T assembly data to send each cycle, as hexadecimal bytes")
    io_group = io_connect.add_argument_group(
        "I/O Exchange", "Controls the Class 0/1 cyclic data exchange loop"
    )
    io_group.add_argument("--cycles", type=_int, default=1, help="Number of send/recv cycles (default: 1)")
    io_group.add_argument("--interval", type=float, default=1.0, help="Seconds to sleep between cycles (default: 1.0)")
    io_group.add_argument(
        "--io-port", type=_int, default=None,
        help=f"UDP port to exchange Class 0/1 data on, if different from the standard "
        f"port (default: {CIPIO_Connection.DEFAULT_PORT}); useful when the target's I/O "
        "port is remapped (e.g. behind NAT/port-forwarding)",
    )
    io_group.add_argument(
        "--no-header-format", action="store_true",
        help="Omit the 4-byte Run/Idle header from O->T datagrams (listen-only/input-only connections)",
    )
    io_group.add_argument(
        "--no-sequence-format", action="store_true",
        help="Omit the 16-bit connected sequence count prefix from O->T datagrams "
        "(targets that rely solely on the CPF-level sequence number, e.g. OpENer's sample assemblies)",
    )
    _add_forward_open_options(io_connect)
    # fmt: on
    add_cip_connection_options(parser, include_host=False)
    for service in (
        list_identity,
        list_services,
        list_interfaces,
        identity,
        get,
        set_attribute,
        get_all,
        assembly_get,
        assembly_set,
        unconnected_send,
        multi,
        forward_open,
        forward_close,
        io_connect,
    ):
        add_cip_target_argument(service)
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

    conn = init_cip_connection(args.host, args.port, args.timeout)
    if conn is None:
        sys.exit(1)
    try:
        func(args, conn)
    except (CIPStatusError, CIPProtocolError) as exc:
        logging.error("CIP request failed: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user...")
    except Exception as exc:
        logging.exception("An unexpected error occurred: %s", exc)
        sys.exit(1)
    finally:
        try:
            logging.debug("Closing EtherNet/IP connection...")
            conn.close()
        except ConnectionClosedError:
            logging.debug("Connection was already closed by remote peer")


if __name__ == "__main__":
    cli_main()
