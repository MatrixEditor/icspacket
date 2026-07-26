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
"""CIP status, service, and object-class constants.

Collects the general status codes (See CIP Volume 1, Appendix B, clause
B-1, Table B-1.1 - CIP General Status Codes), the common service codes
(See CIP Volume 1, Appendix A, clause A-3 - CIP Common Services), and the
object-class codes (See CIP Volume 1, clause 4-3 - Class Code) that
protocol implementations need.
"""

import enum

from typing_extensions import override


class GeneralStatus(enum.IntEnum):
    """General status codes (See CIP Volume 1, clause B-1, Table B-1.1)."""

    SUCCESS = 0x00
    CONNECTION_FAILURE = 0x01
    RESOURCE_UNAVAILABLE = 0x02
    INVALID_PARAMETER_VALUE = 0x03
    PATH_SEGMENT_ERROR = 0x04
    PATH_DESTINATION_UNKNOWN = 0x05
    PARTIAL_TRANSFER = 0x06
    CONNECTION_LOST = 0x07
    SERVICE_NOT_SUPPORTED = 0x08
    INVALID_ATTRIBUTE_VALUE = 0x09
    ATTRIBUTE_LIST_ERROR = 0x0A
    ALREADY_IN_REQUESTED_MODE = 0x0B
    OBJECT_STATE_CONFLICT = 0x0C
    OBJECT_ALREADY_EXISTS = 0x0D
    ATTRIBUTE_NOT_SETTABLE = 0x0E
    PRIVILEGE_VIOLATION = 0x0F
    DEVICE_STATE_CONFLICT = 0x10
    REPLY_DATA_TOO_LARGE = 0x11
    FRAGMENTATION_OF_PRIMITIVE_VALUE = 0x12
    NOT_ENOUGH_DATA = 0x13
    ATTRIBUTE_NOT_SUPPORTED = 0x14
    TOO_MUCH_DATA = 0x15
    OBJECT_DOES_NOT_EXIST = 0x16
    SERVICE_FRAGMENTATION_SEQUENCE_NOT_IN_PROGRESS = 0x17
    NO_STORED_ATTRIBUTE_DATA = 0x18
    STORE_OPERATION_FAILURE = 0x19
    ROUTING_FAILURE_REQUEST_PACKET_TOO_LARGE = 0x1A
    ROUTING_FAILURE_RESPONSE_PACKET_TOO_LARGE = 0x1B
    MISSING_ATTRIBUTE_LIST_ENTRY = 0x1C
    INVALID_ATTRIBUTE_VALUE_LIST = 0x1D
    EMBEDDED_SERVICE_ERROR = 0x1E
    VENDOR_SPECIFIC = 0x1F
    INVALID_PARAMETER = 0x20
    WRITE_ONCE_VALUE_OR_MEDIUM_ALREADY_WRITTEN = 0x21
    INVALID_REPLY_RECEIVED = 0x22
    BUFFER_OVERFLOW = 0x23
    MESSAGE_FORMAT_ERROR = 0x24
    KEY_FAILURE_IN_PATH = 0x25
    PATH_SIZE_INVALID = 0x26
    UNEXPECTED_ATTRIBUTE_IN_LIST = 0x27
    INVALID_MEMBER = 0x28
    MEMBER_NOT_SETTABLE = 0x29
    GROUP_2_ONLY_SERVER_FAILURE = 0x2A
    UNKNOWN_MODBUS_ERROR = 0x2B


class CommonService(enum.IntEnum):
    """Common service codes (See CIP Volume 1, clause A-3 - CIP Common
    Services), plus the Connection Manager object's own service codes (See
    CIP Volume 1, clause 3-5.5).
    """

    GET_ATTRIBUTES_ALL = 0x01
    SET_ATTRIBUTE_ALL = 0x02
    GET_ATTRIBUTE_LIST = 0x03
    SET_ATTRIBUTE_LIST = 0x04
    RESET = 0x05
    START = 0x06
    STOP = 0x07
    CREATE = 0x08
    DELETE = 0x09
    MULTIPLE_SERVICE_PACKET = 0x0A
    APPLY_ATTRIBUTES = 0x0D
    GET_ATTRIBUTE_SINGLE = 0x0E
    SET_ATTRIBUTE_SINGLE = 0x10
    FIND_NEXT_OBJECT_INSTANCE = 0x11
    ERROR_RESPONSE = 0x14
    RESTORE = 0x15
    SAVE = 0x16
    NOP = 0x17
    GET_MEMBER = 0x18
    SET_MEMBER = 0x19
    INSERT_MEMBER = 0x1A
    REMOVE_MEMBER = 0x1B
    GROUP_SYNC = 0x1C

    # Connection Manager object services (See CIP Volume 1, clause 3-5.5).
    FORWARD_CLOSE = 0x4E
    UNCONNECTED_SEND = 0x52
    FORWARD_OPEN = 0x54
    GET_CONNECTION_DATA = 0x56
    SEARCH_CONNECTION_DATA = 0x57
    GET_CONNECTION_OWNER = 0x5A
    LARGE_FORWARD_OPEN = 0x5B


class ClassCode(enum.IntEnum):
    """Object class codes (See CIP Volume 1, clause 4-3 - Class Code, and
    Volume 1, Table 5-1.1 - Object Specifications in the CIP Object Library).

    ``DLR`` through ``PRP_NODES_TABLE`` are EtherNet/IP-specific object
    classes (See CIP Volume 2, clauses 5-6 through 5-14); ``TCP_IP_INTERFACE``
    and ``ETHERNET_LINK`` likewise (See CIP Volume 2, clauses 5-4 and 5-5).
    Every other member is defined in CIP Volume 1.
    """

    IDENTITY = 0x01
    MESSAGE_ROUTER = 0x02
    DEVICE_NET = 0x03
    """DeviceNet Object (See CIP Volume 1, clause 5-4; fully specified in
    CIP Volume 3, DeviceNet Adaptation of CIP)."""
    ASSEMBLY = 0x04
    CONNECTION = 0x05
    CONNECTION_MANAGER = 0x06
    REGISTER = 0x07
    DISCRETE_INPUT = 0x08
    DISCRETE_OUTPUT = 0x09
    ANALOG_INPUT = 0x0A
    ANALOG_OUTPUT = 0x0B
    PRESENCE_SENSING = 0x0E
    PARAMETER = 0x0F
    PARAMETER_GROUP = 0x10
    GROUP = 0x12
    DISCRETE_INPUT_GROUP = 0x1D
    DISCRETE_OUTPUT_GROUP = 0x1E
    DISCRETE_GROUP = 0x1F
    ANALOG_INPUT_GROUP = 0x20
    ANALOG_OUTPUT_GROUP = 0x21
    ANALOG_GROUP = 0x22
    POSITION_SENSOR = 0x23
    POSITION_CONTROLLER_SUPERVISOR = 0x24
    POSITION_CONTROLLER = 0x25
    BLOCK_SEQUENCER = 0x26
    COMMAND_BLOCK = 0x27
    MOTOR_DATA = 0x28
    CONTROL_SUPERVISOR = 0x29
    AC_DC_DRIVE = 0x2A
    ACKNOWLEDGE_HANDLER = 0x2B
    OVERLOAD = 0x2C
    SOFTSTART = 0x2D
    SELECTION = 0x2E
    S_DEVICE_SUPERVISOR = 0x30
    S_ANALOG_SENSOR = 0x31
    S_ANALOG_ACTUATOR = 0x32
    S_SINGLE_STAGE_CONTROLLER = 0x33
    S_GAS_CALIBRATION = 0x34
    TRIP_POINT = 0x35
    FILE = 0x37
    S_PARTIAL_PRESSURE = 0x38
    S_SENSOR_CALIBRATION = 0x40
    EVENT_LOG = 0x41
    MOTION_AXIS = 0x42
    TIME_SYNC = 0x43
    DLR = 0x47
    """Device Level Ring Object (See CIP Volume 2, clause 5-6)."""
    QOS = 0x48
    """QoS Object (See CIP Volume 2, clause 5-7)."""
    BASE_SWITCH = 0x51
    """Base Switch Object (See CIP Volume 2, clause 5-8)."""
    SNMP = 0x52
    """Simple Network Management (SNMP) Object (See CIP Volume 2, clause 5-9)."""
    POWER_MANAGEMENT = 0x53
    """Power Management Object (See CIP Volume 2, clause 5-10)."""
    RSTP_BRIDGE = 0x54
    """RSTP Bridge Object (See CIP Volume 2, clause 5-11)."""
    RSTP_PORT = 0x55
    """RSTP Port Object (See CIP Volume 2, clause 5-12)."""
    PRP = 0x56
    """Parallel Redundancy Protocol (PRP) Object (See CIP Volume 2, clause 5-13)."""
    PRP_NODES_TABLE = 0x57
    """PRP Nodes Table Object (See CIP Volume 2, clause 5-14)."""
    CONTROL_NET = 0xF0
    CONTROL_NET_OBJECT = 0xF1
    CONNECTION_CONFIGURATION = 0xF3
    """Connection Configuration Object (See CIP Volume 1, clause 5-48)."""
    PORT = 0xF4
    """Port object (See CIP Volume 1, clause 3-7)."""
    TCP_IP_INTERFACE = 0xF5
    ETHERNET_LINK = 0xF6


class CIPStatusError(Exception):
    """Exception raised when a CIP service response reports failure.

    ``additional_status`` contains the UINT16 words following the general
    status byte in a reply.  Context fields are optional because a decoder
    often sees the status before it has resolved the request path.
    """

    def __init__(
        self,
        general_status: GeneralStatus | int,
        additional_status: tuple[int, ...] | list[int] = (),
        *,
        service: int | enum.IntEnum | None = None,
        class_code: int | enum.IntEnum | None = None,
        instance: int | None = None,
        message: str | None = None,
    ) -> None:
        self.general_status: GeneralStatus | int = (
            GeneralStatus(general_status)
            if general_status in GeneralStatus._value2member_map_
            else int(general_status)
        )
        self.additional_status: tuple[int, ...] = tuple(
            int(value) & 0xFFFF for value in additional_status
        )
        self.service: int | enum.IntEnum | None = service
        self.class_code: int | enum.IntEnum | None = class_code
        self.instance: int | None = instance
        self.detail: str | None = message
        super().__init__(str(self))

    @property
    def status_name(self) -> str:
        """Human-readable name for the general status value."""

        return (
            self.general_status.name
            if isinstance(self.general_status, GeneralStatus)
            else "UNKNOWN"
        )

    @override
    def __str__(self) -> str:
        text = (
            f"CIP service failed: {self.status_name} (0x{int(self.general_status):02x})"
        )
        if self.additional_status:
            words = ", ".join(f"0x{word:04x}" for word in self.additional_status)
            text += f", additional status [{words}]"
        context: list[str] = []
        if self.service is not None:
            context.append(f"service=0x{int(self.service):02x}")
        if self.class_code is not None:
            context.append(f"class=0x{int(self.class_code):x}")
        if self.instance is not None:
            context.append(f"instance={self.instance}")
        if context:
            text += " (" + ", ".join(context) + ")"
        if self.detail:
            text += f": {self.detail}"
        return text


__all__ = ["CIPStatusError", "ClassCode", "CommonService", "GeneralStatus"]
