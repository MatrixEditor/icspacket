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
import socket

import pytest
from caterpillar.exception import StructException
from caterpillar.fields import uint16, uint32
from caterpillar.model import pack, unpack
from caterpillar.shortcuts import LittleEndian

from icspacket.core.connection import ConnectionError, ConnectionStateError
from icspacket.proto.cip.connection import CIP_Connection, CIPProtocolError
from icspacket.proto.cip.connmgr import (
    ForwardCloseRequest,
    ForwardCloseResponse,
    ForwardOpenRequest,
    ForwardOpenResponse,
    LargeForwardOpenRequest,
    LargeNetworkConnectionParameters,
    NetworkConnectionParameters,
    NetworkConnectionType,
    UnconnectedSendRequest,
)
from icspacket.proto.cip.const import (
    CIPStatusError,
    ClassCode,
    CommonService,
    GeneralStatus,
)
from icspacket.proto.cip.cpf import (
    CPF,
    ConnectedAddressItem,
    ConnectedDataItem,
    CPFItem,
    CPFItemType,
    ListIdentityResponseItem,
    ListInterfacesResponseItem,
    ListServicesResponseItem,
    NullAddressItem,
    SequencedAddressItem,
    SockaddrInfo,
    UnconnectedDataItem,
)
from icspacket.proto.cip.encap import (
    EncapsulationCommand,
    EncapsulationPacket,
    RegisterSessionPayload,
    SendRRDataPayload,
    SendUnitDataPayload,
)
from icspacket.proto.cip.epath import (
    EPATH,
    DataSegment,
    ElectronicKeySegment,
    LogicalSegment,
    NetworkSegment,
    PortSegment,
    SymbolicSegment,
)
from icspacket.proto.cip.io import CIPIO_Connection, CIPIOError
from icspacket.proto.cip.msgrouter import (
    MessageRouterRequest,
    MessageRouterResponse,
    MultipleServicePacket,
)
from icspacket.proto.cip.objects._base import CIPAttributeReader
from icspacket.proto.cip.objects.assembly import AssemblyObject
from icspacket.proto.cip.objects.connection import (
    ConnectionDiagnostics,
    ConnectionObject,
)
from icspacket.proto.cip.objects.connmgr import ConnectionManagerObject
from icspacket.proto.cip.objects.ethlink import EthernetLinkObject
from icspacket.proto.cip.objects.identity import IdentityAttributes, IdentityObject
from icspacket.proto.cip.objects.msgrouter import MessageRouterObject
from icspacket.proto.cip.objects.registry import object_for
from icspacket.proto.cip.objects.tcpip import (
    InterfaceConfiguration,
    TCPIPInterfaceObject,
)


def test_cip_constants_and_status_error():
    assert CommonService.GET_ATTRIBUTE_SINGLE == 0x0E
    assert CommonService.SEARCH_CONNECTION_DATA == 0x57
    assert CommonService.GET_CONNECTION_OWNER == 0x5A
    assert ClassCode.ASSEMBLY == 0x04
    assert 0x2C not in GeneralStatus._value2member_map_
    error = CIPStatusError(GeneralStatus.PATH_SEGMENT_ERROR, [0x1234], service=0x0E)
    assert "PATH_SEGMENT_ERROR" in str(error)
    assert "0x1234" in str(error)


def test_epath_spec_style_logical_path():
    path = EPATH(
        LogicalSegment.class_id(0x04),
        LogicalSegment.instance_id(1),
        LogicalSegment.attribute_id(3),
    )
    encoded = path.to_bytes()
    assert encoded == bytes.fromhex("2004 2401 3003")
    decoded = EPATH.from_bytes(encoded)
    assert decoded.segments == path.segments


def test_epath_logical_kinds_and_extended_port():
    logical = EPATH(
        LogicalSegment.member_id(1),
        LogicalSegment.connection_point(2),
        LogicalSegment.special(3),
        LogicalSegment.service_id(4),
    )
    assert EPATH.from_bytes(logical.to_bytes()).segments == logical.segments
    extended = EPATH(
        PortSegment.new(0x1234, b"\x01\x02"),
        NetworkSegment.new(3, b"\xaa"),
        LogicalSegment.instance_id(1),
    )
    assert EPATH.from_bytes(extended.to_bytes()).segments == extended.segments
    variable = EPATH(
        NetworkSegment.new(0x10, b"\x01\x02"), LogicalSegment.instance_id(2)
    )
    assert EPATH.from_bytes(variable.to_bytes()).segments == variable.segments


def test_epath_extended_segments_and_packed_form():
    path = EPATH(
        PortSegment.new(1, 0),
        SymbolicSegment.new("Motor"),
        DataSegment.new(b"\x01\x02\x03\x04"),
        ElectronicKeySegment(
            vendor_id=1,
            device_type=2,
            product_code=3,
            major_revision=1,
            minor_revision=0,
        ),
    )
    encoded = path.to_bytes()
    assert len(encoded) % 2 == 0
    assert EPATH.from_bytes(encoded).segments == path.segments
    packed = path.to_bytes(packed=True)
    assert EPATH.from_bytes(packed, packed=True).segments == path.segments
    trailing_zero = EPATH(DataSegment.new(b"\x01\x00"))
    assert EPATH.from_bytes(trailing_zero.to_bytes()).segments == trailing_zero.segments


def test_invalid_epath_values():
    with pytest.raises((ValueError, StructException)):
        EPATH.from_bytes(b"\x20")


def test_cpf_item_and_discovery_items():
    cpf = CPF.new(
        NullAddressItem(),
        ConnectedAddressItem(0x12345678),
        UnconnectedDataItem(b"\x01\x02"),
        ListServicesResponseItem(1, 0x0100, "Communications"),
    )
    assert CPF.from_bytes(cpf.to_bytes()) == cpf

    # Table 2-6.3: 0x00B2 is "Unconnected message" (data item); 0x8003+ is
    # reserved for future expansion and must not be defined as a constant.
    assert CPFItemType.UNCONNECTED_DATA == 0x00B2
    assert not hasattr(CPFItemType, "UNCONNECTED_MESSAGE")
    assert not hasattr(CPFItemType, "LIST_INTERFACES")
    assert not hasattr(CPFItemType, "LIST_INTERFACES_RESPONSE")
    legacy_interfaces = CPF.from_bytes(bytes.fromhex("01000101040001000000")).values[0]
    assert isinstance(legacy_interfaces, ListInterfacesResponseItem)
    assert legacy_interfaces.protocol_version == 1
    assert legacy_interfaces.capability_flags == 0

    identity = ListIdentityResponseItem(
        socket_address=SockaddrInfo(port=44818, address="192.0.2.10"),
        vendor_id=1,
        device_type=14,
        product_code=2,
        product_name="device",
    )
    socket_data = identity.socket_address.to_bytes()
    assert socket_data[:8] == bytes.fromhex("0002af12c000020a")
    assert SockaddrInfo.from_bytes(socket_data) == identity.socket_address
    assert CPF.from_bytes(CPF.new(identity).to_bytes()).values == [identity]


def test_cip_caterpillar_structs():
    item = CPFItem(
        type_id=CPFItemType.UNCONNECTED_DATA,
        value=UnconnectedDataItem(b"\x01\x02\x03\x04"),
    )
    assert unpack(CPFItem, pack(item)) == item

    identity = IdentityAttributes(
        1,
        14,
        2,
        1,
        2,
        0x1234,
        0x10203040,
        "device",
        3,
    )
    assert unpack(IdentityAttributes, pack(identity)) == identity

    diagnostics = ConnectionDiagnostics(1, 2, 3, 4, 5, 6, 7, 8, 9)
    assert unpack(ConnectionDiagnostics, pack(diagnostics)) == diagnostics


def test_encapsulation_commands_and_nested_cpf():
    packet = EncapsulationPacket(
        command=EncapsulationCommand.SEND_RR_DATA,
        payload_raw=SendRRDataPayload(
            interface_handle=0,
            timeout=10,
            cpf=CPF.new(NullAddressItem(), UnconnectedDataItem(b"\x70\x00")),
        ),
        session_handle=0x10203040,
        sender_context=b"context!",
    )
    encoded = packet.to_bytes()
    assert encoded[:4] == bytes.fromhex("6f001200")
    assert EncapsulationPacket.from_bytes(encoded) == packet

    register = EncapsulationPacket(
        command=EncapsulationCommand.REGISTER_SESSION,
        payload_raw=RegisterSessionPayload(),
    )
    assert EncapsulationPacket.from_bytes(register.to_bytes()) == register


def test_encapsulation_and_cpf_reject_truncated_input():
    with pytest.raises((ValueError, StructException)):
        EncapsulationPacket.from_bytes(b"\x65\x00")
    with pytest.raises((ValueError, StructException)):
        EncapsulationPacket.from_bytes(
            EncapsulationPacket(
                command=EncapsulationCommand.NOP, payload_raw=b"abc"
            ).to_bytes()[:-1]
        )
    with pytest.raises((ValueError, StructException)):
        # too few bytes for even one CPFItem (count=1, but only 1 byte of
        # item data): raises directly from from_bytes().
        CPF.from_bytes(b"\x01\x00\x00")
    with pytest.raises((ValueError, StructException)):
        # header decodes, but its declared body length exceeds what follows.
        CPF.from_bytes(b"\x01\x00\xb2\x00\x02\x00\x01")
    with pytest.raises((ValueError, StructException)):
        RegisterSessionPayload.from_bytes(b"\x01\x00")
    with pytest.raises((ValueError, StructException)):
        SockaddrInfo.from_bytes(b"\0" * 15)


def test_message_router_request_response_and_multiple_service():
    path = EPATH(LogicalSegment.class_id(4), LogicalSegment.instance_id(1))
    request = MessageRouterRequest.new(CommonService.GET_ATTRIBUTES_ALL, path, b"\x01")
    assert MessageRouterRequest.from_bytes(request.to_bytes()) == request

    response = MessageRouterResponse.new(
        CommonService.GET_ATTRIBUTES_ALL,
        additional_status=[0x1234],
        response_data=b"\xaa\xbb",
    )
    assert MessageRouterResponse.from_bytes(response.to_bytes()) == response

    multiple = MultipleServicePacket()
    requests = [
        request,
        MessageRouterRequest.new(CommonService.GET_ATTRIBUTES_ALL, path),
    ]
    raw_multiple = multiple.build(requests)
    assert MultipleServicePacket.from_bytes(raw_multiple) == multiple


def test_message_router_rejects_malformed_messages():
    with pytest.raises((ValueError, StructException)):
        MessageRouterResponse.from_bytes(b"\x8e\x00\x00\x01")
    # The reply-bit-not-set / reserved-byte / echoed-service checks that
    # used to raise here were dropped along with validate(); msgrouter.py
    # is now a pure wire codec and decodes this cleanly.
    assert MessageRouterResponse.from_bytes(b"\x0e\x00\x00\x00").reply_service == 0x0E
    with pytest.raises((ValueError, StructException)):
        MessageRouterRequest.from_bytes(b"\x0e\x01\x20")
    with pytest.raises((ValueError, StructException)):
        MultipleServicePacket.from_bytes(b"\x01\x00\x04")


class _FakeCIPSocket:
    def __init__(self, responses):
        self.responses = bytearray(responses)
        self.sent = []
        self.timeout = None
        self.closed = False

    def settimeout(self, timeout):
        self.timeout = timeout

    def connect(self, address):
        self.address = address

    def sendall(self, data):
        self.sent.append(bytes(data))

    def recv(self, size):
        data = bytes(self.responses[:size])
        del self.responses[:size]
        return data

    def close(self):
        self.closed = True


def _cip_reply(command, payload, session_handle=0):
    return EncapsulationPacket(
        command=command, payload_raw=payload, session_handle=session_handle
    ).to_bytes()


def test_cip_connection_registers_and_gets_attribute():
    handle = 0x11223344
    register = _cip_reply(
        EncapsulationCommand.REGISTER_SESSION,
        RegisterSessionPayload(),
        session_handle=handle,
    )
    router = MessageRouterResponse.new(
        CommonService.GET_ATTRIBUTE_SINGLE, response_data=b"\x34\x12"
    )
    rr = _cip_reply(
        EncapsulationCommand.SEND_RR_DATA,
        SendRRDataPayload(
            cpf=CPF.new(NullAddressItem(), UnconnectedDataItem(router.to_bytes()))
        ),
        session_handle=handle,
    )
    sock = _FakeCIPSocket(register + rr)
    conn = CIP_Connection(sock=sock)
    conn.connect(("127.0.0.1", 44818))
    assert conn.is_connected() and conn.is_valid()
    assert conn.session_handle == handle
    assert conn.get_attribute_single(ClassCode.ASSEMBLY, 1, 3) == b"\x34\x12"
    assert sock.sent[0][:2] == b"\x65\x00"


def test_cip_connection_rejects_truncated_encapsulation_reply():
    sock = _FakeCIPSocket(b"\x65\x00")
    conn = CIP_Connection(sock=sock)
    conn._connected = True
    with pytest.raises((ConnectionError, CIPProtocolError)):
        conn.register_session()


def test_cip_unregister_session_does_not_wait_for_a_reply():
    # UnRegisterSession must not block on/consume a response.
    handle = 0x11223344
    sock = _FakeCIPSocket(b"")  # no bytes queued: a recv() would raise/hang
    conn = CIP_Connection(sock=sock)
    conn._connected = True
    conn._valid = True
    conn.session_handle = handle
    conn.unregister_session()
    assert conn.session_handle == 0
    assert not conn.is_valid()
    assert len(sock.sent) == 1
    assert sock.sent[0][:2] == b"\x66\x00"  # UnRegisterSession command


def test_connection_manager_forward_open_and_large_open_wire_layouts():
    path = EPATH(LogicalSegment.class_id(4), LogicalSegment.instance_id(1))
    params = NetworkConnectionParameters(
        connection_size=32,
        variable=False,
        priority=2,
        connection_type=NetworkConnectionType.POINT_TO_POINT,
    )
    request = ForwardOpenRequest.new(
        priority=1,
        timeout_ticks=2,
        o_to_t_connection_id=0x11223344,
        t_to_o_connection_id=0x55667788,
        connection_serial_number=0x1234,
        originator_vendor_id=0x5678,
        originator_serial_number=0x12345678,
        timeout_multiplier=3,
        o_to_t_rpi=100000,
        o_to_t_parameters=params,
        t_to_o_rpi=200000,
        t_to_o_parameters=params,
        transport_trigger=0xA3,
        connection_path=path,
    )
    assert request.to_bytes().hex() == (
        "01024433221188776655341278567856341203000000a08601002048"
        "400d03002048a30220042401"
    )
    assert ForwardOpenRequest.from_bytes(request.to_bytes()) == request

    large_params = LargeNetworkConnectionParameters(
        connection_size=0x1234,
        variable=True,
        priority=3,
        connection_type=NetworkConnectionType.POINT_TO_POINT,
    )
    large = LargeForwardOpenRequest.new(
        o_to_t_parameters=large_params,
        t_to_o_parameters=large_params,
        connection_path=path,
    )
    assert LargeForwardOpenRequest.from_bytes(large.to_bytes()) == large
    assert len(large.to_bytes()) == 44


def test_connection_manager_close_unconnected_and_response_validation():
    path = EPATH(LogicalSegment.class_id(6), LogicalSegment.instance_id(1))
    close = ForwardCloseRequest.new(
        priority=1,
        timeout_ticks=2,
        connection_serial_number=0x1234,
        originator_vendor_id=0x5678,
        originator_serial_number=0x12345678,
        connection_path=path,
    )
    assert ForwardCloseRequest.from_bytes(close.to_bytes()) == close
    close_response = ForwardCloseResponse.new(
        connection_serial_number=0x1234,
        originator_vendor_id=0x5678,
        originator_serial_number=0x12345678,
        application_reply_data=b"\xaa\xbb",
    )
    assert ForwardCloseResponse.from_bytes(close_response.to_bytes()) == close_response

    embedded = MessageRouterRequest.new(
        CommonService.GET_ATTRIBUTE_SINGLE, path, b"\x01"
    )
    unconnected = UnconnectedSendRequest.new(
        embedded, EPATH(LogicalSegment.class_id(4))
    )
    assert UnconnectedSendRequest.from_bytes(unconnected.to_bytes()) == unconnected
    with pytest.raises((ValueError, StructException)):
        ForwardOpenResponse.from_bytes(b"\0" * 25)
    with pytest.raises((ValueError, StructException)):
        UnconnectedSendRequest.from_bytes(unconnected.to_bytes()[:-1])


def test_unconnected_send_message_request_size_is_a_byte_count():
    # Table 3-5.22: Message_Request_Size counts bytes, not 16-bit words
    # (unlike Route_Path_Size, which does count words), and a single pad
    # byte follows the Message Request only when that byte count is odd.
    path = EPATH(LogicalSegment.class_id(4), LogicalSegment.instance_id(1))
    route = EPATH(LogicalSegment.class_id(4))

    even_request = MessageRouterRequest.new(CommonService.GET_ATTRIBUTE_SINGLE, path)
    even = UnconnectedSendRequest.new(even_request, route)
    assert len(even.message_request) % 2 == 0
    assert even.message_request_size == len(even.message_request)
    encoded = even.to_bytes()
    assert encoded[2:4] == uint16.to_bytes(
        even.message_request_size, order=LittleEndian
    )
    assert UnconnectedSendRequest.from_bytes(encoded) == even

    odd_request = MessageRouterRequest.new(
        CommonService.GET_ATTRIBUTE_SINGLE, path, b"\x99"
    )
    odd = UnconnectedSendRequest.new(odd_request, route)
    assert len(odd.message_request) % 2 == 1
    assert odd.message_request_size == len(odd.message_request)
    encoded_odd = odd.to_bytes()
    assert encoded_odd[2:4] == uint16.to_bytes(
        odd.message_request_size, order=LittleEndian
    )
    # header (4 bytes) + message request + 1 pad byte + route header (2 bytes) + route path
    assert len(encoded_odd) == 4 + len(odd.message_request) + 1 + 2 + len(
        route.to_bytes()
    )
    decoded_odd = UnconnectedSendRequest.from_bytes(encoded_odd)
    assert decoded_odd == odd
    assert decoded_odd.message_request == odd.message_request


def test_cip_connection_manager_methods_and_connected_unit_data(monkeypatch):
    conn = CIP_Connection(auto_register=False)
    conn._connected = True
    conn._valid = True
    conn.session_handle = 0x10203040
    path = EPATH(LogicalSegment.class_id(4), LogicalSegment.instance_id(1))
    request = ForwardOpenRequest.new(connection_path=path)
    response = ForwardOpenResponse(
        o_to_t_connection_id=0xAABBCCDD, t_to_o_connection_id=0x11223344
    )
    outer = MessageRouterResponse.new(
        CommonService.FORWARD_OPEN, response_data=response.to_bytes()
    )
    calls = []

    def fake_rr(data):
        calls.append(data)
        return outer.to_bytes()

    monkeypatch.setattr(conn, "send_rr_data", fake_rr)
    assert conn.forward_open(request) == response
    assert calls[0].service == CommonService.FORWARD_OPEN
    assert conn.connection_id == 0xAABBCCDD

    connected_response = MessageRouterResponse.new(
        CommonService.GET_ATTRIBUTE_SINGLE,
        response_data=b"\x34\x12",
    )
    connected_reply = EncapsulationPacket(
        command=EncapsulationCommand.SEND_UNIT_DATA,
        payload_raw=SendUnitDataPayload(
            interface_handle=0,
            timeout=0,
            cpf=CPF.new(
                ConnectedAddressItem(conn.connection_id),
                ConnectedDataItem(b"\0\0" + connected_response.to_bytes()),
            ),
        ),
        session_handle=conn.session_handle,
    )
    sock = _FakeCIPSocket(connected_reply.to_bytes())
    conn._sock = sock
    assert (
        conn.generic_message(CommonService.GET_ATTRIBUTE_SINGLE, path, connected=True)
        == b"\x34\x12"
    )
    sent = EncapsulationPacket.from_bytes(sock.sent[0])
    assert sent.command == EncapsulationCommand.SEND_UNIT_DATA
    assert isinstance(sent.payload, SendUnitDataPayload)
    assert sent.payload.timeout == 0
    with pytest.raises(ValueError):
        conn.send_unit_data(
            MessageRouterRequest.new(CommonService.GET_ATTRIBUTE_SINGLE, path)
        )


def test_cip_identity_object_decodes_attributes_and_reset(monkeypatch):
    conn = CIP_Connection(auto_register=False)
    conn._connected = True
    conn._valid = True
    calls = []
    all_data = b"\x34\x12\x0e\x00\x02\x00\x01\x02\x78\x56\x44\x33\x22\x11\x04test\x03"

    def fake_all(class_code, instance):
        calls.append(("all", class_code, instance))
        return all_data

    def fake_message(service, path, request_data=b"", **kwargs):
        calls.append(("message", service, path, request_data, kwargs))
        return b""

    monkeypatch.setattr(conn, "get_attributes_all", fake_all)
    monkeypatch.setattr(conn, "generic_message", fake_message)
    identity = IdentityObject(conn)
    attrs = identity.get_attributes()
    assert attrs.vendor_id == 0x1234
    assert attrs.product_name == "test"
    assert attrs.state == 3
    identity.reset(1)
    assert calls[0][:3] == ("all", ClassCode.IDENTITY, 1)
    assert calls[1][1] == CommonService.RESET
    assert calls[1][3] == b"\x01"


def test_cip_identity_get_all_accepts_missing_or_extended_attributes():
    conn = CIP_Connection(auto_register=False)
    identity = IdentityObject(conn)
    prefix = b"\x34\x12\x0e\x00\x02\x00\x01\x02\x78\x56\x44\x33\x22\x11\x04test"

    assert identity._decode_all(prefix).state == 0
    assert identity._decode_all(prefix + b"\x03\xaa\xbb\xcc").state == 3


def test_cip_core_object_wrappers_use_declarative_attribute_definitions(monkeypatch):
    conn = CIP_Connection(auto_register=False)
    conn._connected = True
    conn._valid = True
    attrs = {
        (ClassCode.MESSAGE_ROUTER, 1, 1): b"\x04\x00\x01\x00\x04\x00\xf5\x00\xf6\x00",
        (ClassCode.ASSEMBLY, 1, 3): b"\xaa\xbb",
        (ClassCode.ETHERNET_LINK, 1, 1): b"\x10\x00\x00\x00",
        (ClassCode.ETHERNET_LINK, 1, 3): b"\x00\x11\x22\x33\x44\x55",
        (ClassCode.TCP_IP_INTERFACE, 1, 6): b"\x04\x00host",
    }
    calls = []

    def fake_get(class_code, instance, attribute):
        calls.append(("get", class_code, instance, attribute))
        return attrs[(class_code, instance, attribute)]

    def fake_set(class_code, instance, attribute, value):
        calls.append(("set", class_code, instance, attribute, value))
        return b""

    monkeypatch.setattr(conn, "get_attribute_single", fake_get)
    monkeypatch.setattr(conn, "set_attribute_single", fake_set)
    assert EthernetLinkObject.attribute_definitions[1].attr_name == "interface_speed"
    assert EthernetLinkObject.attribute_definitions[1].schema is uint32
    assert hasattr(TCPIPInterfaceObject.attribute_definitions[4].schema, "from_bytes")
    assert MessageRouterObject(conn).object_list == [1, 4, 0xF5, 0xF6]
    assert AssemblyObject(conn).data == b"\xaa\xbb"
    assert EthernetLinkObject(conn).interface_speed == 16
    assert EthernetLinkObject(conn).physical_address == b"\x00\x11\x22\x33\x44\x55"
    assert TCPIPInterfaceObject(conn).host_name == "host"
    assert TCPIPInterfaceObject(conn).get_attr(6) == "host"
    AssemblyObject(conn).data = b"\x01"
    assert calls[-1] == ("set", ClassCode.ASSEMBLY, 1, 3, b"\x01")


def test_cip_attribute_reader_decodes_feasible_definitions():
    reader = CIPAttributeReader(
        b"\x10\x00\x00\x00\x20\x00\x00\x00\x00\x11\x22\x33\x44\x55",
    )
    values = reader.read_attributes(
        EthernetLinkObject.attribute_definitions, [1, 2, 3, 4]
    )

    assert values == {
        1: 16,
        2: 32,
        3: b"\x00\x11\x22\x33\x44\x55",
    }
    assert reader.read_remaining() == b""


def test_cip_object_attribute_definitions_reject_malformed_payloads(monkeypatch):
    conn = CIP_Connection(auto_register=False)
    conn._connected = True
    conn._valid = True
    path = EPATH(LogicalSegment.class_id(0xF6), LogicalSegment.instance_id(1))
    attrs = {
        (ClassCode.ETHERNET_LINK, 1, 1): b"\x10\x00\x00",
        (ClassCode.TCP_IP_INTERFACE, 1, 6): b"\x08\x00host",
        (ClassCode.CONNECTION, 1, 14): path.to_bytes(),
    }

    def fake_get(class_code, instance, attribute):
        return attrs[(class_code, instance, attribute)]

    monkeypatch.setattr(conn, "get_attribute_single", fake_get)
    with pytest.raises((ValueError, StructException)):
        EthernetLinkObject(conn).interface_speed
    with pytest.raises((ValueError, StructException)):
        TCPIPInterfaceObject(conn).host_name
    assert ConnectionObject(conn).produced_connection_path == path


def test_cip_object_set_empty_rejects_non_empty_response(monkeypatch):
    conn = CIP_Connection(auto_register=False)
    conn._connected = True
    conn._valid = True
    monkeypatch.setattr(
        conn,
        "set_attribute_single",
        lambda *_args, **_kwargs: b"\x00",
    )

    with pytest.raises(ValueError, match="expected an empty response"):
        AssemblyObject(conn).data = b"\x01"


def test_cip_tcpip_physical_link_object_strips_path_size_prefix(monkeypatch):
    # Vol2 §5-4.3.2.4: attribute 4 is STRUCT { UINT path_size (words), EPATH
    # path } -- the getter must strip the 2-byte word-count prefix before
    # decoding the EPATH, unlike Connection Object's raw (unprefixed) paths.
    conn = CIP_Connection(auto_register=False)
    conn._connected = True
    conn._valid = True
    path = EPATH(LogicalSegment.class_id(0xF6), LogicalSegment.instance_id(1))
    path_bytes = path.to_bytes()
    prefixed = uint16.to_bytes(len(path_bytes) // 2, order=LittleEndian) + path_bytes
    monkeypatch.setattr(conn, "get_attribute_single", lambda *_a, **_k: prefixed)
    assert TCPIPInterfaceObject(conn).physical_link_object == path

    config = InterfaceConfiguration(
        0x01020304, 0xFFFFFF00, 0, 0x08080808, 0x04040404, "example"
    )
    assert (
        InterfaceConfiguration.from_bytes(config.to_bytes(order=LittleEndian)) == config
    )


def test_cip_core_object_registry():
    conn = CIP_Connection(auto_register=False)
    assert isinstance(object_for(conn, ClassCode.IDENTITY), IdentityObject)
    assert isinstance(object_for(conn, ClassCode.ASSEMBLY, 3), AssemblyObject)
    assert isinstance(object_for(conn, ClassCode.MESSAGE_ROUTER), MessageRouterObject)
    assert isinstance(
        object_for(conn, ClassCode.CONNECTION_MANAGER), ConnectionManagerObject
    )
    assert isinstance(
        object_for(conn, ClassCode.TCP_IP_INTERFACE), TCPIPInterfaceObject
    )
    assert isinstance(object_for(conn, ClassCode.ETHERNET_LINK), EthernetLinkObject)
    with pytest.raises(ValueError):
        object_for(conn, 0x1234)


class _FakeIOSocket:
    """Loopback fake UDP socket for CIPIOConnection unit tests."""

    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self._inbox: list[bytes] = []
        self.bound: tuple[str, int] | None = None

    def settimeout(self, timeout: float) -> None:
        pass

    def setsockopt(self, level: int, optname: int, value: int) -> None:
        pass

    def bind(self, address: tuple[str, int]) -> None:
        self.bound = address

    def sendto(self, data: bytes, address: tuple[str, int]) -> None:
        self.sent.append(data)

    def queue_reply(self, data: bytes) -> None:
        self._inbox.append(data)

    def recvfrom(self, bufsize: int) -> tuple[bytes, tuple[str, int]]:
        if not self._inbox:
            raise OSError("no data queued")
        return self._inbox.pop(0), ("127.0.0.1", CIPIO_Connection.DEFAULT_PORT)

    def close(self) -> None:
        pass


def test_cip_io_connection_send_frames_sequenced_address_and_connected_data(
    monkeypatch,
):
    response = ForwardOpenResponse(
        o_to_t_connection_id=0x1111, t_to_o_connection_id=0x2222
    )
    fake = _FakeIOSocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)
    io_conn = CIPIO_Connection.from_forward_open(
        response, ("127.0.0.1", CIPIO_Connection.DEFAULT_PORT)
    )
    assert io_conn.header_format is True

    io_conn.send(b"\x01\x02\x03\x04")
    io_conn.send(b"\xaa\xbb")

    assert len(fake.sent) == 2
    first = CPF.from_bytes(fake.sent[0])
    address_item = first.values[0]
    data_item = first.values[1]
    assert isinstance(address_item, SequencedAddressItem)
    assert address_item.connection_id == 0x1111
    assert address_item.sequence_number == 0
    assert isinstance(data_item, ConnectedDataItem)
    # first 2 bytes are the connected sequence count, next 4 the Run/Idle
    # header (LE uint32, RUN=1), both little-endian
    assert data_item.data == b"\x00\x00\x01\x00\x00\x00\x01\x02\x03\x04"

    second = CPF.from_bytes(fake.sent[1])
    assert second.values[0].sequence_number == 1
    assert second.values[1].data == b"\x01\x00\x01\x00\x00\x00\xaa\xbb"
    io_conn.close()


def test_cip_io_connection_send_without_header_format_omits_run_idle(monkeypatch):
    response = ForwardOpenResponse(
        o_to_t_connection_id=0x1111, t_to_o_connection_id=0x2222
    )
    fake = _FakeIOSocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)
    io_conn = CIPIO_Connection.from_forward_open(
        response, ("127.0.0.1", CIPIO_Connection.DEFAULT_PORT), header_format=False
    )

    io_conn.send(b"\x01\x02\x03\x04")

    data_item = CPF.from_bytes(fake.sent[0]).values[1]
    assert data_item.data == b"\x00\x00\x01\x02\x03\x04"
    io_conn.close()


def test_cip_io_connection_open_binds_fixed_port(monkeypatch):
    response = ForwardOpenResponse(
        o_to_t_connection_id=0x1111, t_to_o_connection_id=0x2222
    )
    fake = _FakeIOSocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    io_conn = CIPIO_Connection.from_forward_open(response, ("127.0.0.1", 44818))
    assert fake.bound == ("0.0.0.0", CIPIO_Connection.DEFAULT_PORT)
    io_conn.close()


def test_cip_io_connection_recv_decodes_and_validates_connection_id(monkeypatch):
    response = ForwardOpenResponse(
        o_to_t_connection_id=0x1111, t_to_o_connection_id=0x2222
    )
    fake = _FakeIOSocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)
    io_conn = CIPIO_Connection.from_forward_open(
        response, ("127.0.0.1", CIPIO_Connection.DEFAULT_PORT)
    )

    reply = CPF.new(
        SequencedAddressItem(0x2222, 7),
        ConnectedDataItem(b"\x03\x00\xde\xad\xbe\xef"),
    ).to_bytes()
    fake.queue_reply(reply)
    assert io_conn.recv() == b"\xde\xad\xbe\xef"

    # wrong connection id must be rejected
    bad_reply = CPF.new(
        SequencedAddressItem(0x9999, 8),
        ConnectedDataItem(b"\x00\x00\x01"),
    ).to_bytes()
    fake.queue_reply(bad_reply)
    with pytest.raises(CIPIOError):
        io_conn.recv()
    io_conn.close()


def test_cip_io_connection_rejects_missing_items_or_double_open(monkeypatch):
    response = ForwardOpenResponse(
        o_to_t_connection_id=0x1111, t_to_o_connection_id=0x2222
    )
    fake = _FakeIOSocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)
    io_conn = CIPIO_Connection.from_forward_open(
        response, ("127.0.0.1", CIPIO_Connection.DEFAULT_PORT)
    )

    with pytest.raises(CIPIOError):
        io_conn.open(response, ("127.0.0.1", CIPIO_Connection.DEFAULT_PORT))

    only_data = CPF.new(ConnectedDataItem(b"\x00\x00\x01")).to_bytes()
    fake.queue_reply(only_data)
    with pytest.raises(CIPIOError):
        io_conn.recv()

    io_conn.close()
    with pytest.raises(CIPIOError):
        io_conn.send(b"\x01")
    with pytest.raises(CIPIOError):
        io_conn.recv()


def test_cip_connection_open_io_connection_reuses_current_forward_open_ids(monkeypatch):
    conn = CIP_Connection(auto_register=False)
    conn.address = ("127.0.0.1", 44818)
    conn.connection_id = 0x1111
    conn.originator_connection_id = 0x2222

    fake = _FakeIOSocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    io_conn = conn.open_io_connection()
    assert io_conn is conn._io_connection
    assert io_conn.o_to_t_connection_id == 0x1111
    assert io_conn.t_to_o_connection_id == 0x2222

    with pytest.raises(ConnectionStateError):
        conn.open_io_connection()

    conn.send_io_data(b"\x01\x02")
    assert len(fake.sent) == 1

    conn.close_io_connection()
    assert conn._io_connection is None
    with pytest.raises(ConnectionStateError):
        conn.send_io_data(b"\x01")


def test_cip_connection_open_io_connection_requires_prior_forward_open():
    conn = CIP_Connection(auto_register=False)
    with pytest.raises(ConnectionStateError):
        conn.open_io_connection()
