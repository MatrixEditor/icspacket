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

"""[ODVA CIP Vol 1] Wrappers for the discrete/analog I/O point objects:

Discrete Input Point (class 0x08, §5-9), Discrete Output Point (class
0x09, §5-10), Analog Input Point (class 0x0A, §5-11), and Analog Output
Point (class 0x0B, §5-12).
"""

from typing import Any, ClassVar

from caterpillar.fields import (
    float32,
    float64,
    int8,
    int16,
    int32,
    int64,
    uint8,
    uint16,
    uint32,
    uint64,
)
from caterpillar.py import pack, unpack
from caterpillar.shortcuts import LittleEndian

from ..const import ClassCode
from ._base import CIPAttribute, CIPObject

#: Attribute 8 (Value Data Type) code -> wire schema, shared by Analog Input
#: and Analog Output Point (See CIP Vol 1, §5-11.3/§5-12.2, Table 5-11.3/5-12.2).
#: Value 100 (vendor specific) has no fixed schema and decodes to raw bytes.
ANALOG_VALUE_TYPES: dict[int, Any] = {
    0: int16,  # INT (default)
    1: float32,  # REAL
    2: uint8,  # USINT
    3: int8,  # SINT
    4: int32,  # DINT
    5: int64,  # LINT
    6: uint16,  # UINT
    7: uint32,  # UDINT
    8: uint64,  # ULINT
    9: float64,  # LREAL
}


def decode_analog_value(data: bytes, value_data_type: int) -> int | float | bytes:
    """Decode an analog Value/Fault Value/Idle Value payload using its Value
    Data Type code."""
    schema = ANALOG_VALUE_TYPES.get(value_data_type)
    return unpack(schema, data, order=LittleEndian) if schema is not None else data


def encode_analog_value(value: int | float | bytes, value_data_type: int) -> bytes:
    """Encode an analog Value/Fault Value/Idle Value payload using its Value
    Data Type code."""
    schema = ANALOG_VALUE_TYPES.get(value_data_type)
    return (
        pack(value, schema, order=LittleEndian) if schema is not None else bytes(value)
    )


class DiscreteInputPointObject(CIPObject):
    """Models a discrete input, e.g. a toggle switch or screw terminal (See CIP
    Vol 1, §5-9)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.DISCRETE_INPUT

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by this product (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    value: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Input point value: 0 = off, 1 = on (attribute 3)."""

    status: CIPAttribute[int] = CIPAttribute(4, uint8)
    """0 = OK, 1 = product-specific alarm or status (attribute 4)."""

    off_on_delay: CIPAttribute[int] = CIPAttribute(5, uint16)
    """Filter time in microseconds for an off-to-on transition, default 0
    (attribute 5)."""

    on_off_delay: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Filter time in microseconds for an on-to-off transition, default 0
    (attribute 6)."""

    off_on_cycles: CIPAttribute[int] = CIPAttribute(7, uint32)
    """Total number of Off-to-On transitions of ``value``, default 0 (attribute
    7)."""


class DiscreteOutputPointObject(CIPObject):
    """Models a discrete output, e.g. a relay or LED (See CIP Vol 1, §5-10)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.DISCRETE_OUTPUT

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by this product (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    value: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Output point value: 0 = off, 1 = on (attribute 3)."""

    status: CIPAttribute[int] = CIPAttribute(4, uint8)
    """0 = OK, 1 = failure or alarm (attribute 4)."""

    fault_action: CIPAttribute[int] = CIPAttribute(5, uint8)
    """Action on ``value`` in the Recoverable Fault state: 0 = use fault_value, 1 = hold last state (attribute 5)."""

    fault_value: CIPAttribute[int] = CIPAttribute(6, uint8)
    """User-defined value applied when fault_action selects it (attribute
    6)."""

    idle_action: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Action on ``value`` when idle: 0 = use idle_value, 1 = hold last state (attribute 7)."""

    idle_value: CIPAttribute[int] = CIPAttribute(8, uint8)
    """User-defined value applied when idle_action selects it (attribute 8)."""

    run_idle_command: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Generates the Receive_Idle (0) or Receive_Ready_to_Run (1) event
    (attribute 9)."""

    flash: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Flash the output at ``flash_rate`` while ``value`` is on, default 0
    (attribute 10)."""

    flash_rate: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Flash frequency in Hz for the ``flash`` attribute (attribute 11)."""

    object_state: CIPAttribute[int] = CIPAttribute(12, uint8)
    """1=Non-Existent, 2=Available, 3=Idle, 4=Ready, 5=Run, 6=Recoverable
    Fault, 7=Unrecoverable Fault (attribute 12)."""

class AnalogInputPointObject(CIPObject):
    """Models an analog input channel (See CIP Vol 1, §5-11)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.ANALOG_INPUT

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by this point (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    value: CIPAttribute[bytes] = CIPAttribute(3)
    """Analog input value; wire type is selected by ``value_data_type``
    (defaults to INT) (attribute 3)."""

    status: CIPAttribute[int] = CIPAttribute(4, uint8)
    """0 = operating without alarms or faults, 1 = alarm or fault condition (attribute 4)."""

    owner_vendor_id: CIPAttribute[int] = CIPAttribute(5, uint16)
    """Vendor ID of the channel's owner (attribute 5)."""

    owner_serial_number: CIPAttribute[int] = CIPAttribute(6, uint32)
    """32-bit serial number of the channel's owner (attribute 6)."""

    input_range: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Input range the point is operating in, e.g. 0 = -10V to 10V (attribute 7, See Table 5-11.3)."""

    value_data_type: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Selects ``value``'s wire type: 0=INT (default), 1=REAL, 2=USINT, ...,
    9=LREAL (attribute 8)."""

    def read_value(self) -> int | float | bytes:
        """Read and decode ``value`` according to the current
        ``value_data_type``."""
        return decode_analog_value(self.value, self.value_data_type)


class AnalogOutputPointObject(CIPObject):
    """Models an analog output channel (See CIP Vol 1, §5-12)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.ANALOG_OUTPUT

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by this point (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    value: CIPAttribute[bytes] = CIPAttribute(3)
    """Analog output value; wire type is selected by ``value_data_type``
    (defaults to INT) (attribute 3)."""

    status: CIPAttribute[int] = CIPAttribute(4, uint8)
    """0 = operating without alarms or faults, 1 = alarm or fault condition (attribute 4)."""

    owner_vendor_id: CIPAttribute[int] = CIPAttribute(5, uint16)
    """Vendor ID of the channel's owner (attribute 5)."""

    owner_serial_number: CIPAttribute[int] = CIPAttribute(6, uint32)
    """32-bit serial number of the channel's owner (attribute 6)."""

    output_range: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Output range the channel is to use, e.g. 0 = 4mA to 20mA (attribute 7, See Table 5-12.2)."""
    value_data_type: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Selects ``value``/``fault_value``/``idle_value``'s wire type: 0=INT
    (default), ..., 9=LREAL (attribute 8)."""

    fault_action: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Output value to go to on fault: 0=hold last state (default), 1=low
    limit, 2=high limit, 3=use fault_value (attribute 9)."""

    idle_action: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Output value to go to on idle: 0=hold last state (default), 1=low limit,
    2=high limit, 3=use idle_value (attribute 10)."""

    fault_value: CIPAttribute[bytes] = CIPAttribute(11)
    """Value output in fault mode when fault_action selects it; required if
    fault_action is implemented (attribute 11)."""

    idle_value: CIPAttribute[bytes] = CIPAttribute(12)
    """Value output in idle mode when idle_action selects it (attribute 12)."""

    command: CIPAttribute[int] = CIPAttribute(13, uint8)
    """Changes the point to Idle (0) or Run (1) mode; required if idle_action
    is implemented (attribute 13)."""

    object_state: CIPAttribute[int] = CIPAttribute(14, uint8)
    """1=Non-Existent, 2=Available, 3=Idle, 4=Ready, 5=Run, 6=Recoverable
    Fault, 7=Unrecoverable Fault (attribute 14)."""

    def read_value(self) -> int | float | bytes:
        """Read and decode ``value`` according to the current
        ``value_data_type``."""
        return decode_analog_value(self.value, self.value_data_type)

    def write_value(self, value: int | float | bytes, *, instance: int | None = None) -> bytes:
        """Encode and write ``value`` according to the current
        ``value_data_type``."""
        return self.set_empty(
            3, encode_analog_value(value, self.value_data_type), instance=instance
        )


__all__ = [
    "ANALOG_VALUE_TYPES",
    "AnalogInputPointObject",
    "AnalogOutputPointObject",
    "DiscreteInputPointObject",
    "DiscreteOutputPointObject",
    "decode_analog_value",
    "encode_analog_value",
]
