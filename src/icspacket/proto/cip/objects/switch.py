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

"""[ODVA CIP Vol 2] Wrappers for EtherNet/IP switch management objects:
Device Level Ring (class 0x47, §5-6), QoS (class 0x48, §5-7), Base Switch
(class 0x51, §5-8), Simple Network Management (SNMP) (class 0x52, §5-9),
Power Management (class 0x53, §5-10), RSTP Bridge (class 0x54, §5-11), RSTP
Port (class 0x55, §5-12), Parallel Redundancy Protocol (PRP) (class 0x56,
§5-13), and PRP Nodes Table (class 0x57, §5-14).
"""

import ipaddress
from collections.abc import Collection
from typing import ClassVar

from caterpillar.fields import int32, net, uint8, uint16, uint32
from caterpillar.model import StructDefMixin
from caterpillar.shortcuts import LittleEndian, f, struct
from caterpillar.types import uint8_t, uint16_t, uint32_t

from ..const import ClassCode
from ..epath import EPATH
from ._base import (
    CIP_PREFIXED_EPATH,
    CIP_SHORT_STRING,
    CIP_STRING,
    CIPAttribute,
    CIPObject,
)

__all__ = [
    "BaseSwitchObject",
    "BridgeIdentifier",
    "DLRObject",
    "NetworkManagerIdentifier",
    "NodeAddress",
    "PRPNodesTableObject",
    "PRPObject",
    "PowerManagementObject",
    "PrpDuplicateDetectionCounters",
    "PrpInterfaceCounters",
    "PrpNodeEntry",
    "QoSObject",
    "RSTPBridgeObject",
    "RSTPPortObject",
    "RedundantGatewayConfig",
    "RingSupervisorConfig",
    "SNMPObject",
]


@struct(order=LittleEndian)
class NodeAddress(StructDefMixin):
    """IP/MAC address pair identifying a node on the ring (DLR Object
    attributes 6, 7, 10, and 15, See §5-6.3.2.1)."""

    ip: f[ipaddress.IPv4Address, net.IPv4Address]
    mac: f[str, net.MAC]


@struct(order=LittleEndian)
class RingSupervisorConfig(StructDefMixin):
    """DLR Object attribute 4 payload (See §5-6.3.2.1, Table 5-6.4)."""

    enable: uint8_t
    """1 = Ring Supervisor capability enabled for this device."""

    precedence: uint8_t
    """Priority used to select the active Ring Supervisor; 0 = highest."""

    beacon_interval: uint32_t
    """Beacon frame transmission interval, in microseconds."""

    beacon_timeout: uint32_t
    """Time without receiving a Beacon frame before declaring a ring fault, in
    microseconds."""

    vlan_id: uint16_t
    """VLAN ID used for DLR protocol frames."""


@struct(order=LittleEndian)
class RedundantGatewayConfig(StructDefMixin):
    """DLR Object attribute 13 payload (See §5-6.3.2.1, Table 5-6.9)."""

    enable: uint8_t
    """1 = Redundant Gateway capability enabled for this device."""

    gateway_precedence: uint8_t
    """Priority used to select the active gateway; 0 = highest."""

    advertise_interval: uint32_t
    """Advertise frame transmission interval, in microseconds."""

    advertise_timeout: uint32_t
    """Time without receiving an Advertise frame before declaring a fault, in
    microseconds."""

    learning_update_enable: uint8_t
    """1 = send a Link_Status/Neighbor_Check frame to speed up address-table
    updates on failover."""


class DLRObject(CIPObject):
    """Configures and monitors a Device Level Ring (DLR) network node (See CIP
    Vol 2, §5-6)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.DLR

    network_topology: CIPAttribute[int] = CIPAttribute(1, uint8)
    """0 = Linear, 1 = Ring (attribute 1)."""

    network_status: CIPAttribute[int] = CIPAttribute(2, uint8)
    """Current DLR network status (attribute 2, See Table 5-6.3)."""

    ring_supervisor_status: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Current Ring Supervisor status; valid only while
    ring_supervisor_config.enable is set (attribute 3)."""

    ring_supervisor_config: CIPAttribute[RingSupervisorConfig] = CIPAttribute(
        4, RingSupervisorConfig
    )
    """Ring Supervisor configuration (attribute 4)."""

    ring_faults_count: CIPAttribute[int] = CIPAttribute(5, uint16)
    """Number of times the ring has transitioned from Normal to Ring Fault
    state (attribute 5)."""

    last_active_node_on_port_1: CIPAttribute[NodeAddress] = CIPAttribute(6, NodeAddress)
    """IP/MAC address of the last node this device detected on Port 1
    (attribute 6)."""

    last_active_node_on_port_2: CIPAttribute[NodeAddress] = CIPAttribute(7, NodeAddress)
    """IP/MAC address of the last node this device detected on Port 2
    (attribute 7)."""

    ring_protocol_participants_count: CIPAttribute[int] = CIPAttribute(8, uint16)
    """Number of nodes that responded to the last Discover_Topology sequence
    (attribute 8)."""

    active_supervisor_address: CIPAttribute[NodeAddress] = CIPAttribute(10, NodeAddress)
    """IP/MAC address of the active Ring Supervisor (attribute 10)."""

    active_supervisor_precedence: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Precedence value of the active Ring Supervisor (attribute 11)."""

    capability_flags: CIPAttribute[int] = CIPAttribute(12, uint32)
    """Bitmap of DLR capabilities supported by this device (attribute 12, See
    Table 5-6.10)."""

    redundant_gateway_config: CIPAttribute[RedundantGatewayConfig] = CIPAttribute(
        13, RedundantGatewayConfig
    )
    """Redundant Gateway configuration (attribute 13)."""

    redundant_gateway_status: CIPAttribute[int] = CIPAttribute(14, uint8)
    """Current Redundant Gateway status (attribute 14, See Table 5-6.11)."""

    active_gateway_address: CIPAttribute[NodeAddress] = CIPAttribute(15, NodeAddress)
    """IP/MAC address of the active gateway (attribute 15)."""

    active_gateway_precedence: CIPAttribute[int] = CIPAttribute(16, uint8)
    """Precedence value of the active gateway (attribute 16)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a DLR class attribute from instance 0 (See §5-6.2, Table
        5-6.1)."""
        return self.get_attr(attribute, instance=0)

    def verify_fault_location(self) -> bytes:
        """Invoke Verify_Fault_Location (service 0x4B), requesting a beacon-
        based ring fault check."""
        return self._expect_empty(self.message(0x4B))

    def clear_rapid_faults(self) -> bytes:
        """Invoke Clear_Rapid_Faults (service 0x4C), re-arming rapid fault/
        restart counters."""
        return self._expect_empty(self.message(0x4C))

    def restart_sign_on(self) -> bytes:
        """Invoke Restart_Sign_On (service 0x4D), restarting the Sign_On
        sequence used to build the ring node list."""
        return self._expect_empty(self.message(0x4D))

    def clear_gateway_partial_fault(self) -> bytes:
        """Invoke Clear_Gateway_Partial_Fault (service 0x4E), clearing a
        Redundant Gateway partial fault condition."""
        return self._expect_empty(self.message(0x4E))


class QoSObject(CIPObject):
    """Configures 802.1Q tagging and DSCP values for EtherNet/IP traffic (See
    CIP Vol 2, §5-7)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.QOS

    dot1q_tag_enable: CIPAttribute[int] = CIPAttribute(1, uint8)
    """1 = send 802.1Q tagged frames for CIP and IEEE 1588 messages, default 0
    (attribute 1, conditional)."""

    dscp_ptp_event: CIPAttribute[int] = CIPAttribute(2, uint8)
    """DSCP value for PTP (IEEE 1588) event messages, default 59 (attribute 2,
    conditional)."""

    dscp_ptp_general: CIPAttribute[int] = CIPAttribute(3, uint8)
    """DSCP value for PTP (IEEE 1588) general messages, default 47 (attribute
    3, conditional)."""

    dscp_urgent: CIPAttribute[int] = CIPAttribute(4, uint8)
    """DSCP value for CIP transport class 0/1 Urgent priority messages,
    default 55 (attribute 4)."""

    dscp_scheduled: CIPAttribute[int] = CIPAttribute(5, uint8)
    """DSCP value for CIP transport class 0/1 Scheduled priority messages,
    default 47 (attribute 5)."""

    dscp_high: CIPAttribute[int] = CIPAttribute(6, uint8)
    """DSCP value for CIP transport class 0/1 High priority messages, default
    43 (attribute 6)."""

    dscp_low: CIPAttribute[int] = CIPAttribute(7, uint8)
    """DSCP value for CIP transport class 0/1 Low priority messages, default
    31 (attribute 7)."""

    dscp_explicit: CIPAttribute[int] = CIPAttribute(8, uint8)
    """DSCP value for CIP UCMM, transport class 2/3, and all other
    EtherNet/IP encapsulation messages, default 27 (attribute 8)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a QoS class attribute from instance 0 (See §5-7.3, Table
        5-7.2)."""
        return self.get_attr(attribute, instance=0)


class BaseSwitchObject(CIPObject):
    """Basic status information for a managed Ethernet switch device (See CIP
    Vol 2, §5-8).

    Devices implement no more than one instance. Attributes 6-8 are bitmaps
    packed across ``port_mask_size`` DWORDs (one bit per port) and attribute
    14 is a nested, variably-sized structure whose inner port-mask array is
    itself sized by ``port_mask_size``; all four are exposed as raw bytes
    rather than a fixed schema.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.BASE_SWITCH

    device_up_time: CIPAttribute[int] = CIPAttribute(1, uint32)
    """Seconds since the device was powered up (attribute 1)."""

    total_port_count: CIPAttribute[int] = CIPAttribute(2, uint32)
    """Number of physical ports available (attribute 2)."""

    system_firmware_version: CIPAttribute[str] = CIPAttribute(3, CIP_SHORT_STRING)
    """Human-readable System Firmware Version, empty if not configured
    (attribute 3)."""

    power_source: CIPAttribute[int] = CIPAttribute(4, uint16)
    """Bitmap of power source/supply status, 2 bits per source (attribute 4,
    See Table 5-8.4)."""

    port_mask_size: CIPAttribute[int] = CIPAttribute(5, uint16)
    """Number of DWORDs in each port-mask bitmap attribute, minimum 4
    (attribute 5)."""

    existing_ports: CIPAttribute[bytes] = CIPAttribute(6)
    """Bitmap (one bit per port) of ports physically present in the switch
    housing; size in DWORDs given by port_mask_size (attribute 6, optional)."""

    global_port_admin_state: CIPAttribute[bytes] = CIPAttribute(7)
    """Bitmap of each port's Admin state; size in DWORDs given by
    port_mask_size (attribute 7, optional)."""

    global_port_link_status: CIPAttribute[bytes] = CIPAttribute(8)
    """Bitmap of each port's link status; size in DWORDs given by
    port_mask_size (attribute 8)."""

    system_boot_loader_version: CIPAttribute[str] = CIPAttribute(9, CIP_SHORT_STRING)
    """Human-readable System Boot Loader Version, empty if not configured
    (attribute 9, optional)."""

    contact_status: CIPAttribute[int] = CIPAttribute(10, uint16)
    """Bitmap of switch contact closure status, 2 bits per contact (attribute
    10, optional, See Table 5-8.8)."""

    aging_time: CIPAttribute[int] = CIPAttribute(11, uint32)
    """Timeout in seconds for aging out dynamically-learned forwarding
    information, 0 = learning off, default 300 (attribute 11, optional)."""

    temperature_c: CIPAttribute[int] = CIPAttribute(12, int32)
    """Switch temperature in degrees Celsius (attribute 12, optional)."""

    temperature_f: CIPAttribute[int] = CIPAttribute(13, int32)
    """Switch temperature in degrees Fahrenheit (attribute 13, optional)."""

    resiliency_protocol_list: CIPAttribute[bytes] = CIPAttribute(14)
    """List of resiliency protocol entities used by the switch: a UINT count
    followed by, for each entry, a Resiliency Protocol Select value, a
    port-mask bitmap sized by port_mask_size, and a path to the protocol's
    own object (attribute 14, optional, See §5-8.3.3.7)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Base Switch class attribute from instance 0 (See §5-8.3.1,
        Table 5-8.2)."""
        return self.get_attr(attribute, instance=0)


@struct(order=LittleEndian)
class NetworkManagerIdentifier(StructDefMixin):
    """Network manager address (SNMP Object attributes 3 and 4, See
    §5-9.3.2.3)."""

    identifier_format: uint8_t
    """0 = unconfigured, 1 = IPv4 dotted-decimal, 2 = domain name."""

    identifier: f[str, CIP_STRING]
    """Address value; empty when identifier_format is 0."""


class SNMPObject(CIPObject):
    """Configures the SNMP Agent embedded in a device (See CIP Vol 2, §5-9).

    A device implementing this object provides exactly one instance.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.SNMP

    snmp_agent: CIPAttribute[int] = CIPAttribute(1, uint8)
    """1 = SNMP Agent enabled (default), 0 = disabled (attribute 1)."""

    snmp_agent_version: CIPAttribute[int] = CIPAttribute(2, uint8)
    """1 = SNMPv1, 3 = SNMPv3, 31 = bilingual SNMPv1+v3 (attribute 2)."""

    primary_network_manager: CIPAttribute[NetworkManagerIdentifier] = CIPAttribute(
        3, NetworkManagerIdentifier
    )
    """Primary Network Manager address that TrapPdus are sent to (attribute
    3)."""

    secondary_network_manager: CIPAttribute[NetworkManagerIdentifier] = CIPAttribute(
        4, NetworkManagerIdentifier
    )
    """Secondary Network Manager address that TrapPdus are sent to (attribute
    4)."""

    notifications: CIPAttribute[int] = CIPAttribute(5, uint8)
    """1 = sending of SNMP TrapPdus enabled (default), 0 = disabled (attribute
    5)."""

    trap_type: CIPAttribute[int] = CIPAttribute(6, uint8)
    """1 = TrapV1Pdu, 2 = TrapV2Pdu (requires snmp_agent_version 3 or 31)
    (attribute 6, optional)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an SNMP class attribute from instance 0 (See §5-9.3.1, Table
        5-9.2)."""
        return self.get_attr(attribute, instance=0)


class PowerManagementObject(CIPObject):
    """Marker wrapper for the Power Management Object (See CIP Vol 2, §5-10).

    Volume 2 defines no attributes or services of its own beyond the base
    object described in Volume 1: only the behavioral requirement that a
    device whose Sleeping state support is enabled (base object attribute 6)
    must accept Wake-on-LAN "Magic Packets" to exit that state. This class
    exists so :func:`~icspacket.proto.cip.objects.registry.object_for` can
    resolve class 0x53; the base Volume 1 attributes/services are out of
    scope here.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.POWER_MANAGEMENT


@struct(order=LittleEndian)
class BridgeIdentifier(StructDefMixin):
    """Combined 2-byte priority + 6-byte MAC bridge identifier (RSTP Bridge
    Object attribute 12; RSTP Port Object attributes 3, 15, and 17, See IEEE
    802.1D-2004 §17.18.6)."""

    priority: uint16_t
    mac: f[str, net.MAC]


class RSTPBridgeObject(CIPObject):
    """Configuration and diagnostic interface for RSTP at the bridge level
    (See CIP Vol 2, §5-11, IEEE 802.1D-2004 clause 17).

    Devices may implement multiple instances (e.g. one per VLAN).
    ``list_of_rstp_ports`` decodes greedily from its own Get_Attribute_Single
    response; its true length equals ``number_of_rstp_ports``.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.RSTP_BRIDGE

    bridge_object_identification: CIPAttribute[str] = CIPAttribute(1, CIP_SHORT_STRING)
    """Vendor-defined identification for this Bridge Object instance, empty
    if unused (attribute 1)."""

    bridge_identifier_priority: CIPAttribute[int] = CIPAttribute(2, uint16)
    """Manageable component of the Bridge Identifier, range 0-61440 in steps
    of 4096, default 32768 (attribute 2)."""

    transmit_hold_count: CIPAttribute[int] = CIPAttribute(3, uint16)
    """Limits the Port Transmit state machine's transmission rate, range
    1-10, default 6 (attribute 3)."""

    number_of_rstp_ports: CIPAttribute[int] = CIPAttribute(4, uint16)
    """Number of RSTP ports associated with this bridge, default 2 (attribute
    4)."""

    list_of_rstp_ports: CIPAttribute[Collection[int]] = CIPAttribute(5, uint16[...])
    """RSTP Port Object instance numbers associated with this bridge, one per
    number_of_rstp_ports (attribute 5)."""

    force_protocol_version: CIPAttribute[int] = CIPAttribute(6, uint16)
    """0 = STP compatibility mode, 2 = normal operation (default) (attribute
    6, optional)."""

    bridge_max_age: CIPAttribute[int] = CIPAttribute(7, uint16)
    """Maximum age (in 1/256s units) of information transmitted by this
    bridge while Root, range 6.0-40.0s, default 20.0s (attribute 7,
    optional)."""

    bridge_hello_time: CIPAttribute[int] = CIPAttribute(8, uint16)
    """Interval (in 1/256s units) between Configuration Message transmissions
    by Designated Ports, range 1.0-2.0s, default 2.0s (attribute 8,
    optional)."""

    bridge_forward_delay: CIPAttribute[int] = CIPAttribute(9, uint16)
    """Delay (in 1/256s units) used to transition Root/Designated Ports to
    Forwarding, range 4.0-30.0s, default 15.0s (attribute 9, optional)."""

    time_since_topology_change: CIPAttribute[int] = CIPAttribute(10, uint32)
    """Time (in 1/256s units) since the last topology change (attribute 10,
    optional)."""

    topology_change_count: CIPAttribute[int] = CIPAttribute(11, uint32)
    """Total number of topology changes detected since last reset (attribute
    11, optional)."""

    designated_root: CIPAttribute[BridgeIdentifier] = CIPAttribute(12, BridgeIdentifier)
    """Bridge Identifier of the root of the spanning tree (attribute 12,
    optional)."""

    root_cost: CIPAttribute[int] = CIPAttribute(13, uint32)
    """Cost of the path to the root as seen from this bridge, default 200,000
    for 100Mbps (attribute 13, optional)."""

    root_port: CIPAttribute[int] = CIPAttribute(14, uint16)
    """Port identifier of the port offering the lowest-cost path to the root,
    0 = undefined (attribute 14, optional)."""

    max_age: CIPAttribute[int] = CIPAttribute(15, uint16)
    """Actual Max Age value currently in use by this bridge (in 1/256s
    units), range 6.0-40.0s, default 20.0s (attribute 15, optional)."""

    hello_time: CIPAttribute[int] = CIPAttribute(16, uint16)
    """Actual Hello Time value currently in use by this bridge (in 1/256s
    units), range 1.0-2.0s, default 2.0s (attribute 16, optional)."""

    forward_delay: CIPAttribute[int] = CIPAttribute(17, uint16)
    """Actual Forward Delay value currently in use by this bridge (in 1/256s
    units), range 4.0-30.0s, default 15.0s (attribute 17, optional)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an RSTP Bridge class attribute from instance 0 (See
        §5-11.3.1, Table 5-11.2)."""
        return self.get_attr(attribute, instance=0)


class RSTPPortObject(CIPObject):
    """Configuration and diagnostic interface for RSTP at the port level (See
    CIP Vol 2, §5-12, IEEE 802.1D-2004 clause 17).

    At least 2 instances are required wherever :class:`RSTPBridgeObject` is
    implemented.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.RSTP_PORT

    bridge_object_instance: CIPAttribute[int] = CIPAttribute(1, uint16)
    """RSTP Bridge Object instance associated with this port, default 1
    (attribute 1)."""

    ethernet_link_instance: CIPAttribute[int] = CIPAttribute(2, uint16)
    """Ethernet Link Object instance associated with this port, default 0
    (attribute 2)."""

    reference_bridge_identifier: CIPAttribute[BridgeIdentifier] = CIPAttribute(
        3, BridgeIdentifier
    )
    """Bridge Identifier of the bridge this port is associated with
    (attribute 3)."""

    port_mac_address: CIPAttribute[str] = CIPAttribute(4, net.MAC)
    """MAC address unique to this port instance (attribute 4)."""

    rstp_port_enable: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0 = RSTP disabled (default), 1 = RSTP enabled (attribute 5)."""

    port_identifier_priority: CIPAttribute[int] = CIPAttribute(6, uint32)
    """Manageable component of the Port Identifier, range 0-240 in steps of
    16, default 128 (attribute 6)."""

    oper_edge_port: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Current operEdgePort value as determined by the Bridge Detection state
    machine, default 1/True (attribute 7)."""

    port_state: CIPAttribute[int] = CIPAttribute(8, uint16)
    """1=Disabled (default), 2=Blocking, 3=Listening, 4=Learning,
    5=Forwarding, 6=Broken (attribute 8)."""

    mcheck: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Set by management to force the Port Protocol Migration state machine
    to transmit RST BPDUs, default 0/False (attribute 9, optional)."""

    port_path_cost: CIPAttribute[int] = CIPAttribute(10, uint32)
    """Contribution of this port to the path cost of paths toward the
    spanning tree root, 0 = use automatically calculated default (attribute
    10, optional)."""

    port_admin_edge_port: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Administrative value of the Edge Port parameter, default 0/False
    (attribute 11, optional)."""

    admin_point_to_point_mac: CIPAttribute[int] = CIPAttribute(12, uint16)
    """0=forceTrue, 1=forceFalse, 2=auto (default) (attribute 12, optional)."""

    oper_point_to_point_mac: CIPAttribute[int] = CIPAttribute(13, uint16)
    """Operational point-to-point status of the attached LAN segment, default
    0/False (attribute 13, optional)."""

    port_role: CIPAttribute[int] = CIPAttribute(14, uint16)
    """0=Unknown (default), 1=Alternate/Backup, 2=Root, 3=Designated
    (attribute 14, optional)."""

    designated_root: CIPAttribute[BridgeIdentifier] = CIPAttribute(15, BridgeIdentifier)
    """Bridge Identifier recorded as Root in Configuration BPDUs for this
    port's segment (attribute 15, optional)."""

    designated_root_path_cost: CIPAttribute[int] = CIPAttribute(16, uint32)
    """Path cost of the Designated Port of this port's segment, default
    200,000 (attribute 16, optional)."""

    designated_bridge_identifier: CIPAttribute[BridgeIdentifier] = CIPAttribute(
        17, BridgeIdentifier
    )
    """Bridge Identifier this port considers the Designated Bridge for its
    segment (attribute 17, optional)."""

    designated_port: CIPAttribute[int] = CIPAttribute(18, uint16)
    """Port Identifier of the port on the Designated Bridge for this port's
    segment, default 0 (attribute 18, optional)."""

    forward_transitions_count: CIPAttribute[int] = CIPAttribute(19, uint32)
    """Number of times this port transitioned from Learning to Forwarding
    (attribute 19, optional)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an RSTP Port class attribute from instance 0 (See §5-12.3.1,
        Table 5-12.2)."""
        return self.get_attr(attribute, instance=0)


@struct(order=LittleEndian)
class PrpInterfaceCounters(StructDefMixin):
    """PRP Object attribute 8 payload (See §5-13.3.3.2, IEC 62439-3)."""

    transmit_count_a: uint32_t
    transmit_count_b: uint32_t
    transmit_count_c: uint32_t
    receive_count_a: uint32_t
    receive_count_b: uint32_t
    receive_count_c: uint32_t
    wrong_lan_a_count: uint32_t
    wrong_lan_b_count: uint32_t


@struct(order=LittleEndian)
class PrpDuplicateDetectionCounters(StructDefMixin):
    """PRP Object attribute 9 payload (See §5-13.3.3.3, IEC 62439-3)."""

    entries_unique_count_a: uint32_t
    entries_unique_count_b: uint32_t
    entries_duplicate_count_a: uint32_t
    entries_duplicate_count_b: uint32_t
    entries_multiple_count_a: uint32_t
    entries_multiple_count_b: uint32_t


class PRPObject(CIPObject):
    """Configuration and diagnostic interface for Parallel Redundancy
    Protocol (PRP) dual-LAN operation (See CIP Vol 2, §5-13, IEC 62439-3
    clause 4)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.PRP

    prp_enable: CIPAttribute[int] = CIPAttribute(1, uint8)
    """1 = PRP enabled, 0 = disabled (default) (attribute 1)."""

    node_type: CIPAttribute[int] = CIPAttribute(2, uint16)
    """0 = deprecated PRP Mode 0, 1 = PRP Mode 1 (default) (attribute 2)."""

    node_name: CIPAttribute[str] = CIPAttribute(3, CIP_SHORT_STRING)
    """Human-readable name of the PRP Link Redundancy Entity, empty if
    unconfigured (attribute 3)."""

    version_name: CIPAttribute[str] = CIPAttribute(4, CIP_SHORT_STRING)
    """Human-readable version name of the PRP Link Redundancy Entity
    (attribute 4)."""

    prp_mac_address: CIPAttribute[str] = CIPAttribute(5, net.MAC)
    """MAC address used by PRP (attribute 5)."""

    duplicate_discard: CIPAttribute[int] = CIPAttribute(6, uint16)
    """0 = doNotDiscard, 1 = discard (default) (attribute 6)."""

    transparent_reception: CIPAttribute[int] = CIPAttribute(7, uint16)
    """0 = removeRCT (default), 1 = passRCT (attribute 7)."""

    prp_interface_counters: CIPAttribute[PrpInterfaceCounters] = CIPAttribute(
        8, PrpInterfaceCounters
    )
    """Frame counters for Ports A/B and the interlink/DANP interface
    (attribute 8)."""

    prp_duplicate_detection_counters: CIPAttribute[PrpDuplicateDetectionCounters] = (
        CIPAttribute(9, PrpDuplicateDetectionCounters)
    )
    """Duplicate-detection entry counters for Ports A/B (attribute 9)."""

    prp_proxy_nodes_count: CIPAttribute[int] = CIPAttribute(10, uint32)
    """Number of nodes in the Proxy Nodes Table (attribute 10)."""

    proxy_nodes_table: CIPAttribute[Collection[str]] = CIPAttribute(11, net.MAC[...])
    """MAC addresses of nodes this device proxies for, one per
    prp_proxy_nodes_count (attribute 11); the Get_Member service (0x18) is
    required by the spec for indexed access but is not implemented here."""

    prp_nodes_table_path: CIPAttribute[EPATH] = CIPAttribute(12, CIP_PREFIXED_EPATH)
    """Path to this device's PRP Nodes Table object instance (attribute 12,
    optional)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a PRP class attribute from instance 0 (See §5-13.3.1, Table
        5-13.2)."""
        return self.get_attr(attribute, instance=0)


@struct(order=LittleEndian)
class PrpNodeEntry(StructDefMixin):
    """One entry in the PRP Nodes Table (PRP Nodes Table Object attribute 2,
    See §5-14.3.2, Table 5-14.2)."""

    mac: f[str, net.MAC]
    """MAC address of the source node, as advertised by its PRP Supervision
    frames."""

    time_last_seen_a: uint32_t
    """TimeTicks (1/100s) since the last frame from this node was received
    over LAN A, 0 upon registration."""

    time_last_seen_b: uint32_t
    """TimeTicks (1/100s) since the last frame from this node was received
    over LAN B, 0 upon registration."""


class PRPNodesTableObject(CIPObject):
    """Records PRP-capable nodes detected on the network (See CIP Vol 2,
    §5-14).

    Devices may implement one or more instances.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.PRP_NODES_TABLE

    prp_nodes_table_count: CIPAttribute[int] = CIPAttribute(1, uint32)
    """Number of nodes in the PRP Nodes Table (attribute 1)."""

    prp_nodes_table: CIPAttribute[Collection[PrpNodeEntry]] = CIPAttribute(
        2, PrpNodeEntry[...]
    )
    """PRP node entries, one per prp_nodes_table_count (attribute 2)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a PRP Nodes Table class attribute from instance 0 (See
        §5-14.3.1, Table 5-14.1)."""
        return self.get_attr(attribute, instance=0)
