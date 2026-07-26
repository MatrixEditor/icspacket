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

"""[ODVA CIP Vol 1] Wrappers for the objects that bind groups of other CIP
objects together: Group (class 0x12, §5-16), Discrete Input Group (class 0x1D,
§5-17), Discrete Output Group (class 0x1E, §5-18), Discrete Group (class 0x1F,
§5-19), Analog Input Group (class 0x20, §5-20), Analog Output Group (class
0x21, §5-21), and Analog Group (class 0x22, §5-22)."""

from collections.abc import Collection
from typing import ClassVar

from caterpillar.fields import uint8, uint16, uint32
from caterpillar.model import StructDefMixin
from caterpillar.shortcuts import LittleEndian, struct
from caterpillar.types import uint16_t

from ..const import ClassCode
from ._base import CIPAttribute, CIPObject
from .point import decode_analog_value, encode_analog_value

__all__ = [
    "AnalogGroupObject",
    "AnalogInputGroupObject",
    "AnalogOutputGroupObject",
    "DiscreteGroupObject",
    "DiscreteInputGroupObject",
    "DiscreteOutputGroupObject",
    "GroupBinding",
    "GroupObject",
]


@struct(order=LittleEndian)
class GroupBinding(StructDefMixin):
    """One ``{Class ID, Instance ID}`` entry in a class-heterogeneous group's
    Binding list."""

    class_id: uint16_t
    """Class code of the bound object."""

    instance_id: uint16_t
    """Instance ID of the bound object."""


#: Binding list schema for groups whose members may span several classes
#: (Group, Discrete Group, Analog Group): a greedy array of {class, instance}.
GROUP_BINDING_LIST = GroupBinding[...]
#: Binding list schema for groups whose members are all a single known class
#: (Discrete/Analog Input/Output Group): a greedy array of bare instance IDs.
POINT_BINDING_LIST = uint16[...]


class GroupObject(CIPObject):
    """Binds other objects (e.g. AIP, AOP, DIP, DOP, or their groups) together
    (See CIP Vol 1, §5-16)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.GROUP

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by the group (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    number_of_bound_instances: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Number of points bound to this group (attribute 3)."""

    binding: CIPAttribute[Collection[GroupBinding]] = CIPAttribute(
        4, GROUP_BINDING_LIST
    )
    """List of ``{class_id, instance_id}`` entries bound to this group
    (attribute 4)."""

    status: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0 = good, 1 = alarm state, for the whole group (attribute 5)."""

    owner_vendor_id: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Vendor ID of the group's owner (attribute 6)."""

    owner_serial_number: CIPAttribute[int] = CIPAttribute(7, uint32)
    """32-bit serial number of the group's owner (attribute 7)."""


class DiscreteInputGroupObject(CIPObject):
    """Binds a group of Discrete Input Point objects (See CIP Vol 1, §5-17)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.DISCRETE_INPUT_GROUP

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by the device (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    number_of_bound_instances: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Number of points bound to this group (attribute 3)."""

    binding: CIPAttribute[Collection[int]] = CIPAttribute(4, POINT_BINDING_LIST)
    """Instance IDs of the Discrete Input Points bound to this group (attribute
    4)."""

    status: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0 = OK, 1 = product-specific alarm or status, for all bound points (attribute 5)."""

    off_on_delay: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Shared filter time in microseconds for an off-to-on transition, default
    0 (attribute 6)."""

    on_off_delay: CIPAttribute[int] = CIPAttribute(7, uint16)
    """Shared filter time in microseconds for an on-to-off transition, default
    0 (attribute 7)."""


class DiscreteOutputGroupObject(CIPObject):
    """Binds a group of Discrete Output Point objects (See CIP Vol 1,
    §5-18)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.DISCRETE_OUTPUT_GROUP

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by the device (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    number_of_bound_instances: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Number of points bound to this group (attribute 3)."""

    binding: CIPAttribute[Collection[int]] = CIPAttribute(4, POINT_BINDING_LIST)
    """Instance IDs of the Discrete Output Points bound to this group
    (attribute 4)."""

    status: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0 = OK, 1 = product-specific alarm or status, for all bound points (attribute 5)."""

    command: CIPAttribute[int] = CIPAttribute(6, uint8)
    """Changes state of all bound DOPs: 0 = idle, 1 = run (attribute 6, required)."""

    fault_action: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Shared state after a recoverable failure: 0 = use fault_value, 1 = hold last state (attribute 7)."""

    fault_value: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Shared user-defined value for use with fault_action (attribute 8)."""

    idle_action: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Shared state while idle: 0 = use idle_value, 1 = hold last state (attribute 9)."""

    idle_value: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Shared user-defined value for use with idle_action (attribute 10)."""


class DiscreteGroupObject(CIPObject):
    """Binds a group of discrete objects spanning more than one class (See CIP
    Vol 1, §5-19)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.DISCRETE_GROUP

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by the group (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    number_of_bound_instances: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Number of points in this group (attribute 3)."""

    binding: CIPAttribute[Collection[GroupBinding]] = CIPAttribute(
        4, GROUP_BINDING_LIST
    )
    """List of ``{class_id, instance_id}`` entries bound to this group
    (attribute 4)."""

    status: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0 = good, 1 = alarm state, for the whole group (attribute 5)."""


class AnalogInputGroupObject(CIPObject):
    """Binds a group of Analog Input Point objects (See CIP Vol 1, §5-20)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.ANALOG_INPUT_GROUP

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by the group (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    number_of_bound_instances: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Number of points in a group (attribute 3)."""

    binding: CIPAttribute[Collection[int]] = CIPAttribute(4, POINT_BINDING_LIST)
    """Instance IDs of the Analog Input Points bound to this group (attribute
    4)."""

    status: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0 = good, 1 = alarm state, for the whole group (attribute 5)."""

    owner_vendor_id: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Vendor ID of the group's owner (attribute 6)."""

    owner_serial_number: CIPAttribute[int] = CIPAttribute(7, uint32)
    """32-bit serial number of the group's owner (attribute 7)."""

    value_data_type: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Shared AIP Value wire type: 0=INT (default), 1=REAL, 2=USINT, ...,
    9=LREAL (attribute 8)."""

    # Attribute 9 is reserved for CIP.

    temp_mode: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Temperature scale for a temperature value: 0 = Celsius, 1 = Fahrenheit (attribute 10)."""


class AnalogOutputGroupObject(CIPObject):
    """Binds a group of Analog Output Point objects (See CIP Vol 1, §5-21)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.ANALOG_OUTPUT_GROUP

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by the group (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    number_of_bound_instances: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Number of bindings in the group (attribute 3)."""

    binding: CIPAttribute[Collection[int]] = CIPAttribute(4, POINT_BINDING_LIST)
    """Instance IDs of the Analog Output Points bound to this group (attribute
    4)."""

    status: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0 = good, 1 = alarm state, for the whole group (attribute 5)."""

    owner_vendor_id: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Vendor ID of the group's owner (attribute 6)."""

    owner_serial_number: CIPAttribute[int] = CIPAttribute(7, uint32)
    """32-bit serial number of the group's owner (attribute 7)."""

    value_data_type: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Shared wire type for any bound Value/fault_value/idle_value: 0=INT
    (default), ..., 9=LREAL (attribute 8)."""

    command: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Changes state of bound AOPs: 0 = idle, 1 = run (attribute 9, required)."""

    fault_action: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Output value to go to on fault: 0=use fault_value, 1=hold last state
    (default), 2=low limit, 3=high limit (attribute 10)."""

    fault_value: CIPAttribute[bytes] = CIPAttribute(11)
    """Shared fault value; wire type selected by value_data_type, required if
    fault_action is implemented (attribute 11)."""

    idle_action: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Output value to go to on idle: 0=use idle_value, 1=hold last state
    (default), 2=low limit, 3=high limit (attribute 12)."""

    idle_value: CIPAttribute[bytes] = CIPAttribute(13)
    """Shared idle value; wire type selected by value_data_type, required if
    idle_action is implemented (attribute 13)."""

    def read_fault_value(self) -> object:
        """Read and decode ``fault_value`` according to the current
        ``value_data_type``."""
        return decode_analog_value(self.get(11), self.value_data_type)

    def write_fault_value(self, value: object, *, instance: int | None = None) -> bytes:
        """Encode and write ``fault_value`` according to the current
        ``value_data_type``."""
        return self.set_empty(
            11, encode_analog_value(value, self.value_data_type), instance=instance
        )

    def read_idle_value(self) -> object:
        """Read and decode ``idle_value`` according to the current
        ``value_data_type``."""
        return decode_analog_value(self.get(13), self.value_data_type)

    def write_idle_value(self, value: object, *, instance: int | None = None) -> bytes:
        """Encode and write ``idle_value`` according to the current
        ``value_data_type``."""
        return self.set_empty(
            13, encode_analog_value(value, self.value_data_type), instance=instance
        )


class AnalogGroupObject(CIPObject):
    """Binds a group of analog objects spanning more than one class (See CIP
    Vol 1, §5-22)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.ANALOG_GROUP

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by the group (attribute 1)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(2)
    """List of supported attribute IDs, one USINT each (attribute 2)."""

    number_of_bound_instances: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Number of points in a group (attribute 3)."""

    binding: CIPAttribute[Collection[GroupBinding]] = CIPAttribute(4, GROUP_BINDING_LIST)
    """List of ``{class_id, instance_id}`` entries bound to this group
    (attribute 4)."""

    status: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0 = good, 1 = alarm state, for the whole group (attribute 5)."""

    owner_vendor_id: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Vendor ID of the group's owner (attribute 6)."""

    owner_serial_number: CIPAttribute[int] = CIPAttribute(7, uint32)
    """32-bit serial number of the group's owner (attribute 7)."""

    value_data_type: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Shared wire type propagated to all bound objects' Value: 0=INT
    (default), ..., 9=LREAL (attribute 8)."""
