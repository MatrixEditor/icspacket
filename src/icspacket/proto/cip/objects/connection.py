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
"""[ODVA CIP Vol 1] Wrappers for the CIP Connection Object (class 0x05) and
Connection Configuration Object (class 0xF3).

Connection Object instance attributes and diagnostics are defined
according to §3-4.4, Table 3-4.9. Connection Configuration Object
attributes are defined according to §5-48.
"""

from typing import ClassVar

from caterpillar.fields import uint8, uint16, uint32
from caterpillar.model import StructDefMixin
from caterpillar.shortcuts import LittleEndian, f, struct
from caterpillar.types import uint8_t, uint16_t, uint32_t

from ..const import ClassCode
from ..epath import EPATH
from ._base import CIP_EPATH, CIPAttribute, CIPObject


@struct(order=LittleEndian)
class ConnectionDiagnostics(StructDefMixin):
    """Selected Connection Object diagnostic attributes (See CIP Vol 1, §3-4.4,
    Table 3-4.9)."""

    state: uint8_t
    """Current operating state of this Connection instance."""

    instance_type: uint8_t
    """Marks this Connection instance as either an I/O connection or a
    Messaging (explicit) connection."""

    transport_class_trigger: uint8_t
    """Governs how this Connection transports its data."""

    produced_connection_size: uint16_t
    """Upper bound on how many bytes this Connection transmits."""

    consumed_connection_size: uint16_t
    """Upper bound on how many bytes this Connection receives."""

    expected_packet_rate: uint16_t
    """Sets the packet-timing expectation for this Connection."""

    produced_connection_id: uint32_t
    """Identifier attached to messages this Connection sends out on the
    subnet."""

    consumed_connection_id: uint32_t
    """Identifier expected on incoming messages this Connection reads from the
    subnet."""

    watchdog_timeout_action: uint8_t
    """Specifies the action taken when this Connection's inactivity/watchdog
    timer expires."""


class ConnectionObject(CIPObject):
    """Read-only diagnostic attributes of a Connection instance (See CIP Vol 1,
    §3-4.4, Table 3-4.9)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.CONNECTION

    state: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Connection state (attribute 1)."""

    instance_type: CIPAttribute[int] = CIPAttribute(2, uint8)
    """Connection instance type (attribute 2)."""

    transport_class_trigger: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Transport class and trigger byte (attribute 3)."""

    # Attribute 4 is the DeviceNet-only UINT produced connection ID variant.

    produced_connection_size: CIPAttribute[int] = CIPAttribute(7, uint16)
    """Produced connection size in bytes (attribute 7)."""

    consumed_connection_size: CIPAttribute[int] = CIPAttribute(8, uint16)
    """Consumed connection size in bytes (attribute 8)."""

    expected_packet_rate: CIPAttribute[int] = CIPAttribute(9, uint16)
    """Expected packet rate in milliseconds (attribute 9)."""

    produced_connection_id: CIPAttribute[int] = CIPAttribute(10, uint32)
    """CIP produced connection ID (attribute 10)."""

    consumed_connection_id: CIPAttribute[int] = CIPAttribute(11, uint32)
    """CIP consumed connection ID (attribute 11)."""

    watchdog_timeout_action: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Watchdog timeout action (attribute 12)."""

    produced_connection_path: CIPAttribute[EPATH] = CIPAttribute(14, CIP_EPATH)
    """Produced connection path (attribute 14)."""

    consumed_connection_path: CIPAttribute[EPATH] = CIPAttribute(16, CIP_EPATH)
    """Consumed connection path (attribute 16)."""

    def get_diagnostics(self) -> ConnectionDiagnostics:
        """Read selected diagnostic attributes as one structured value."""
        return ConnectionDiagnostics(
            self.state,
            self.instance_type,
            self.transport_class_trigger,
            self.produced_connection_size,
            self.consumed_connection_size,
            self.expected_packet_rate,
            self.produced_connection_id,
            self.consumed_connection_id,
            self.watchdog_timeout_action,
        )


@struct(order=LittleEndian)
class DeviceID(StructDefMixin):
    """Vendor/product identification quintuple (Connection Configuration Object
    attributes 3 and 11)."""

    vendor_id: uint16_t
    product_type: uint16_t
    product_code: uint16_t
    major_rev: uint8_t
    minor_rev: uint8_t


@struct(order=LittleEndian)
class ConnectionStatus(StructDefMixin):
    """Connection Configuration Object attribute 1 payload (See CIP Vol 1,
    §5-48.2.2.1)."""

    gen_status: uint8_t
    """General status code (See Table 5-48.5/5-48.6)."""

    reserved: uint8_t
    """Reserved, shall be zero."""

    ext_status: uint16_t
    """Extended status code."""


@struct(order=LittleEndian)
class NetConnectionParameters(StructDefMixin):
    """Connection Configuration Object attribute 5 payload: Forward_Open-shaped
    connection parameters (See CIP Vol 1, §5-48.2.2.5)."""

    conn_timeout: uint8_t
    """Connection timeout multiplier, as used in the Forward_Open request."""

    transport_class_trigger: uint8_t
    """Transport Class and Trigger byte, as used in the Forward_Open
    request."""

    rpi_ot: uint32_t
    """Originator to Target Requested Packet Interval, in microseconds."""

    net_ot: uint16_t
    """Originator to Target network connection parameters (size/type
    bitfield)."""

    rpi_to: uint32_t
    """Target to Originator Requested Packet Interval, in microseconds."""

    net_to: uint16_t
    """Target to Originator network connection parameters (size/type
    bitfield)."""


@struct(order=LittleEndian)
class LargeNetConnectionParameters(StructDefMixin):
    """Connection Configuration Object attribute 19 payload: large-format
    variant of :class:`NetConnectionParameters` (See CIP Vol 1, §5-48.2)."""

    conn_timeout: uint8_t
    """Connection timeout multiplier, as used in the Forward_Open request."""

    transport_class_trigger: uint8_t
    """Transport Class and Trigger byte, as used in the Forward_Open
    request."""

    rpi_ot: uint32_t
    """Originator to Target Requested Packet Interval, in microseconds."""

    net_ot: uint32_t
    """Originator to Target large-format network connection parameters
    (size/type bitfield)."""

    rpi_to: uint32_t
    """Target to Originator Requested Packet Interval, in microseconds."""

    net_to: uint32_t
    """Target to Originator large-format network connection parameters
    (size/type bitfield)."""


@struct(order=LittleEndian)
class ConnectionPathAttribute(StructDefMixin):
    """Connection Configuration Object attribute 6 payload (See CIP Vol 1,
    §5-48.2.2.6)."""

    open_path_size: uint8_t
    """Size of open_connection_path in bytes, as used in the Forward_Open
    request."""

    reserved: uint8_t
    """Reserved, shall be zero."""

    open_connection_path: f[EPATH, CIP_EPATH]
    """Connection path, as used in the Forward_Open request."""


class ConnectionConfigurationObject(CIPObject):
    """Creates, configures, and controls CIP connections in a device (See CIP
    Vol 1, §5-48).

    Attributes 13-17 and 20-22 (safety-only) are out of scope (See CIP
    Volume 5, CIP Safety).
    ``config_1_data``/``config_2_data``/``io_mapping`` each start with
    one or two leading count fields followed by vendor/format-specific
    bytes, and ``connection_name`` is a UTF-16 (STRING2) string; all
    four are exposed as raw bytes rather than a fixed schema.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.CONNECTION_CONFIGURATION

    connection_status: CIPAttribute[ConnectionStatus] = CIPAttribute(1, ConnectionStatus)
    """General/extended connection status (attribute 1, See Table
    5-48.5/5-48.6)."""

    connection_flags: CIPAttribute[int] = CIPAttribute(2, uint16)
    """Originator/Target role and O->T/T->O real-time transfer format bits
    (attribute 2, See Table 5-48.7)."""

    target_device_id: CIPAttribute[DeviceID] = CIPAttribute(3, DeviceID)
    """Identity of the connection's target device, for locating its EDS
    (attribute 3)."""

    cs_data_index_number: CIPAttribute[int] = CIPAttribute(4, uint32)
    """ControlNet Schedule Object connection_index value; ignored for target
    instances (attribute 4)."""

    net_connection_parameters: CIPAttribute[NetConnectionParameters] = CIPAttribute(
        5, NetConnectionParameters
    )
    """Forward_Open-shaped connection parameters: timeout, transport, RPIs, and
    sizes (attribute 5)."""

    connection_path: CIPAttribute[ConnectionPathAttribute] = CIPAttribute(
        6, ConnectionPathAttribute
    )
    """Forward_Open connection path, with its own byte-size prefix (attribute
    6)."""

    config_1_data: CIPAttribute[bytes] = CIPAttribute(7)
    """``UINT config_data_size`` prefix followed by that many bytes of Config
    #1 data (attribute 7)."""

    connection_name: CIPAttribute[bytes] = CIPAttribute(8)
    """``USINT name_size, USINT reserved(=0)`` prefix followed by a UTF-16
    (STRING2) connection name (attribute 8)."""

    io_mapping: CIPAttribute[bytes] = CIPAttribute(9)
    """``UINT format_number, UINT mapping_data_size`` prefix followed by that
    many bytes of mapping data; format matches class attribute 8 (attribute 9,
    See Table 5-48.4)."""

    config_2_data: CIPAttribute[bytes] = CIPAttribute(10)
    """``UINT config_data_size`` prefix followed by that many bytes of Config
    #2 data (attribute 10)."""

    proxy_device_id: CIPAttribute[DeviceID] = CIPAttribute(11, DeviceID)
    """Identity of the device that owns this instance's Forward_Open, e.g. for
    target/proxy setups (attribute 11)."""

    connection_disable: CIPAttribute[int] = CIPAttribute(12, uint8)
    """0 = enabled, 1 = disabled; required iff Open_Connection/Close_Connection are supported (attribute 12)."""

    net_connection_parameters_selection: CIPAttribute[int] = CIPAttribute(18, uint8)
    """Selects whether net_connection_parameters (0) or
    large_net_connection_parameters (1) is active (attribute 18)."""

    large_net_connection_parameters: CIPAttribute[LargeNetConnectionParameters] = (
        CIPAttribute(19, LargeNetConnectionParameters)
    )
    """Large-format variant of net_connection_parameters, required iff
    attribute 18 is supported (attribute 19)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Connection Configuration class attribute from instance 0 (See
        §5-48.1, Table 5-48.1)."""
        return self.get_attr(attribute, instance=0)

    def open_connection(self, request_data: bytes = b"") -> bytes:
        """Invoke Open_Connection (service 0x4C), opening this instance's
        connection."""
        return self.message(0x4C, request_data)

    def close_connection(self, request_data: bytes = b"") -> bytes:
        """Invoke Close_Connection (service 0x4D), closing this instance's
        connection."""
        return self.message(0x4D, request_data)

    def stop_connection(self, request_data: bytes = b"") -> bytes:
        """Invoke Stop_Connection (service 0x4E), stopping without deleting
        this instance's connection."""
        return self.message(0x4E, request_data)

    def change_start(self) -> bytes:
        """Invoke Change_Start (service 0x4F), beginning a class-wide
        configuration edit session."""
        return self.message(0x4F, instance=0)

    def get_status(self, request_data: bytes = b"") -> bytes:
        """Invoke Get_Status (service 0x50), reading status for multiple
        connections."""
        return self.message(0x50, request_data, instance=0)

    def change_complete(self, request_data: bytes = b"") -> bytes:
        """Invoke Change_Complete (service 0x51), committing a class-wide
        configuration edit session."""
        return self.message(0x51, request_data, instance=0)

    def audit_changes(self, request_data: bytes = b"") -> bytes:
        """Invoke Audit_Changes (service 0x52), inspecting pending
        configuration edits."""
        return self.message(0x52, request_data, instance=0)


__all__ = [
    "ConnectionDiagnostics",
    "ConnectionObject",
    "DeviceID",
    "ConnectionStatus",
    "NetConnectionParameters",
    "LargeNetConnectionParameters",
    "ConnectionPathAttribute",
    "ConnectionConfigurationObject",
]
