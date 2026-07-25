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
"""[ODVA CIP Vol 1] Wrappers for the "Hierarchy of Motor Control Devices" object
group:

- Motor Data (class 0x28, §5-28),
- Control Supervisor (class 0x29, §5-29),
- AC/DC Drive (class 0x2A, §5-30),
- Acknowledge Handler (class 0x2B, §5-31),
- Overload (class 0x2C, §5-32), and
- Softstart (class 0x2D, §5-33).
"""

from collections.abc import Collection
from typing import ClassVar

from caterpillar.fields import int8, int16, int32, uint8, uint16, uint32

from ..const import ClassCode, CommonService
from ._base import CIP_SHORT_STRING, CIPAttribute, CIPObject

__all__ = [
    "ACDCDriveObject",
    "AcknowledgeHandlerObject",
    "ControlSupervisorObject",
    "MotorDataObject",
    "OverloadObject",
    "SoftstartObject",
]


class MotorDataObject(CIPObject):
    """Database of motor nameplate/rating parameters (See CIP Vol 1, §5-28).

    Attributes 6 and above are motor-type specific (AC vs. DC, See
    §5-28.2.1); both classes of motor share the same wire types for their
    common attribute IDs, so both are exposed unconditionally here.
    ``international_cat_number``/``international_manufacturer`` are STRINGI
    encoded and kept as raw bytes.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.MOTOR_DATA

    num_attr: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attributes: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attribute IDs supported by this instance (attribute 2)."""

    motor_type: CIPAttribute[int] = CIPAttribute(3, uint8)
    """0=Non-standard, 1=PM DC, 2=FC DC, 3=PM Synchronous, 6=Wound Rotor
    Induction, 7=Squirrel Cage Induction, 8=Stepper, ...

    (attribute 3, required).
    """

    cat_number: CIPAttribute[str] = CIPAttribute(4, CIP_SHORT_STRING)
    """Manufacturer's motor catalog (nameplate) number (attribute 4)."""

    manufacturer: CIPAttribute[str] = CIPAttribute(5, CIP_SHORT_STRING)
    """Manufacturer's name (attribute 5)."""

    rated_current: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Rated stator (AC) or armature (DC) current, Units: 100mA (attribute
    6)."""

    rated_voltage: CIPAttribute[int] = CIPAttribute(7, uint16)
    """Rated base (AC) or armature (DC) voltage, Units: V (attribute 7)."""

    rated_power: CIPAttribute[int] = CIPAttribute(8, uint32)
    """Rated power at rated frequency/max speed, Units: W (attribute 8)."""

    rated_freq: CIPAttribute[int] = CIPAttribute(9, uint16)
    """Rated electrical frequency, Units: Hz; AC motors only (attribute 9)."""

    rated_temp: CIPAttribute[int] = CIPAttribute(10, uint16)
    """Rated winding temperature, Units: degrees C (attribute 10)."""

    max_speed: CIPAttribute[int] = CIPAttribute(11, uint16)
    """Maximum allowed motor speed, Units: RPM (attribute 11)."""

    pole_count: CIPAttribute[int] = CIPAttribute(12, uint16)
    """Number of poles in the motor; AC motors only (attribute 12)."""

    torque_constant: CIPAttribute[int] = CIPAttribute(13, uint32)
    """Motor torque constant, Units: 0.001 x Nm/A (attribute 13)."""

    inertia: CIPAttribute[int] = CIPAttribute(14, uint32)
    """Rotor inertia, Units: 1e-6 x kg.m^2 (attribute 14)."""

    base_speed: CIPAttribute[int] = CIPAttribute(15, uint16)
    """Nominal speed at rated frequency/voltage, Units: RPM (attribute 15)."""

    rated_field_current: CIPAttribute[int] = CIPAttribute(16, uint32)
    """Rated field current, Units: mA; DC motors only (attribute 16)."""

    min_field_current: CIPAttribute[int] = CIPAttribute(17, uint32)
    """Minimum field current, Units: mA; DC motors only (attribute 17)."""

    rated_field_voltage: CIPAttribute[int] = CIPAttribute(18, uint16)
    """Rated field voltage, Units: V; DC motors only (attribute 18)."""

    service_factor: CIPAttribute[int] = CIPAttribute(19, uint8)
    """Service factor, Units: %; AC motors only (attribute 19)."""

    international_cat_number: CIPAttribute[bytes] = CIPAttribute(20)
    """STRINGI catalog name/number (attribute 20)."""

    international_manufacturer: CIPAttribute[bytes] = CIPAttribute(21)
    """STRINGI name of the motor manufacturer (attribute 21)."""

    serial_number: CIPAttribute[str] = CIPAttribute(22, CIP_SHORT_STRING)
    """Nameplate serial number of the motor (attribute 22)."""

    tag_name: CIPAttribute[str] = CIPAttribute(23, CIP_SHORT_STRING)
    """Plant's tag name for the motor (attribute 23)."""

    supply_style: CIPAttribute[int] = CIPAttribute(24, uint8)
    """0 = three phase, 1 = single phase (attribute 24)."""

    time_rating: CIPAttribute[int] = CIPAttribute(25, uint16)
    """Maximum continuous operation time, Units: minutes (attribute 25)."""

    inrush_current: CIPAttribute[int] = CIPAttribute(26, uint16)
    """Maximum inrush current, Units: 100mA (attribute 26)."""

    locked_rotor_code_letter: CIPAttribute[str] = CIPAttribute(27, CIP_SHORT_STRING)
    """NEMA MG-1 Code Letter for Locked Rotor kVA (attribute 27)."""

    design_letter: CIPAttribute[str] = CIPAttribute(28, CIP_SHORT_STRING)
    """IEC or NEMA Design Letter (attribute 28)."""

    thermal_protection: CIPAttribute[int] = CIPAttribute(29, uint8)
    """TRUE (nonzero) if the motor is marked "Thermally Protected" (attribute
    29)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Motor Data class attribute from instance 0 (See §5-28.1)."""
        return self.get_attr(attribute, instance=0)

    def restore(self) -> bytes:
        """Invoke Restore, reloading attribute values saved via
        :meth:`save`."""
        return self._expect_empty(self.message(CommonService.RESTORE))

    def save(self) -> bytes:
        """Invoke Save, persisting all attribute values to non-volatile
        storage."""
        return self._expect_empty(self.message(CommonService.SAVE))


class ControlSupervisorObject(CIPObject):
    """Models the run/stop/fault management state machine shared by motor
    control devices (See CIP Vol 1, §5-29): the State Transition Diagram and
    State Event Matrix (§5-29.5) govern how
    ``run1``/``run2``/``net_ctrl``/``fault_reset`` drive ``state``."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.CONTROL_SUPERVISOR

    num_attr: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attributes: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attribute IDs supported by this instance (attribute 2)."""

    run1: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Run/Stop command 1 (attribute 3, required, See Run/Stop Event
    Matrix)."""

    run2: CIPAttribute[int] = CIPAttribute(4, uint8)
    """Run/Stop command 2 (attribute 4, See Run/Stop Event Matrix)."""

    net_ctrl: CIPAttribute[int] = CIPAttribute(5, uint8)
    """Requests Run/Stop control to be local (0) or from the network (1)
    (attribute 5)."""

    state: CIPAttribute[int] = CIPAttribute(6, uint8)
    """0=Vendor Specific, 1=Startup, 2=Not_Ready, 3=Ready, 4=Enabled,
    5=Stopping, 6=Fault_Stop, 7=Faulted (attribute 6)."""

    running1: CIPAttribute[int] = CIPAttribute(7, uint8)
    """1 if (Enabled|Stopping|Fault_Stop) and Running1, else 0 (attribute
    7)."""

    running2: CIPAttribute[int] = CIPAttribute(8, uint8)
    """1 if (Enabled|Stopping|Fault_Stop) and Running2, else 0 (attribute
    8)."""

    ready: CIPAttribute[int] = CIPAttribute(9, uint8)
    """1 if Ready, Enabled, or Stopping, else 0 (attribute 9)."""

    faulted: CIPAttribute[int] = CIPAttribute(10, uint8)
    """1 if a fault has occurred (latched), else 0 (attribute 10)."""

    warning: CIPAttribute[int] = CIPAttribute(11, uint8)
    """1 if a warning is present (not latched), else 0 (attribute 11)."""

    fault_reset: CIPAttribute[int] = CIPAttribute(12, uint8)
    """0->1 transition requests a Fault Reset (attribute 12)."""

    fault_code: CIPAttribute[int] = CIPAttribute(13, uint16)
    """Code identifying the fault that caused/last caused a transition to
    Faulted (attribute 13)."""
    warn_code: CIPAttribute[int] = CIPAttribute(14, uint16)
    """Code identifying the lowest-numbered warning currently present
    (attribute 14)."""
    ctrl_from_net: CIPAttribute[int] = CIPAttribute(15, uint8)
    """Status of Run/Stop control source: 0=local, 1=network (attribute 15)."""

    net_fault_mode: CIPAttribute[int] = CIPAttribute(16, uint8)
    """Action on loss of CIP Network: 0=Fault+Stop, 1=Ignore, 2=Vendor specific
    (attribute 16)."""

    force_fault: CIPAttribute[int] = CIPAttribute(17, uint8)
    """0->1 transition forces a fault/trip (attribute 17)."""

    force_status: CIPAttribute[int] = CIPAttribute(18, uint8)
    """0 = not forced, nonzero = forced (attribute 18)."""

    delay: CIPAttribute[int] = CIPAttribute(19, int16)
    """ITIME delay (ms) before a fault/idle mode action takes effect (attribute
    19)."""

    net_idle_mode: CIPAttribute[int] = CIPAttribute(20, uint8)
    """Mode on reception of a CIP communication IDLE event (attribute 20, See
    Table 5-29.3)."""

    protect_mode: CIPAttribute[int] = CIPAttribute(21, uint8)
    """Mode on detection of a motor protection event (attribute 21, See Table
    5-29.3)."""

    cycle_count: CIPAttribute[int] = CIPAttribute(22, uint32)
    """Number of motor start operations recorded on the equipment (attribute
    22)."""

    fault_warning_code_style: CIPAttribute[int] = CIPAttribute(23, uint8)
    """0=device profile default, 1=DRIVECOM (16-bit), 2=Abbreviated (8-bit)
    (attribute 23)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Control Supervisor class attribute from instance 0 (See
        §5-29.1)."""
        return self.get_attr(attribute, instance=0)

    def reset(self) -> bytes:
        """Invoke Reset, resetting the drive to its start-up state."""
        return self._expect_empty(self.message(CommonService.RESET))


class ACDCDriveObject(CIPObject):
    """Models functions specific to an AC or DC drive: speed/torque/process
    control, ramping, and scaling (See CIP Vol 1, §5-30).

    Most measurement/reference attributes are scaled integers; the divisor
    is ``2 ** <attribute>_scale`` as documented on each attribute.
    ``process_data_units``/``speed_actual_data_units``/``speed_ref_data_units``
    select an ENGUNITS code from CIP Vol 1 Appendix D (not decoded elsewhere
    in this library), so they are kept as raw bytes.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.AC_DC_DRIVE

    num_attr: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attributes: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attribute IDs supported by this instance (attribute 2)."""

    at_reference: CIPAttribute[int] = CIPAttribute(3, uint8)
    """1 = drive actual is at its speed/torque reference (attribute 3)."""

    net_ref: CIPAttribute[int] = CIPAttribute(4, uint8)
    """Requests torque/speed reference to be local (0) or from the network (1)
    (attribute 4, required)."""

    net_proc: CIPAttribute[int] = CIPAttribute(5, uint8)
    """Requests process control reference to be local (0) or from the network
    (1) (attribute 5)."""

    drive_mode: CIPAttribute[int] = CIPAttribute(6, uint8)
    """0=Vendor specific, 1=Open loop speed, 2=Closed loop speed, 3=Torque,
    4=Process control, 5=Position control (attribute 6, required)."""

    speed_actual: CIPAttribute[int] = CIPAttribute(7, int16)
    """Actual drive speed, Units: RPM / 2**speed_scale (attribute 7,
    required)."""

    speed_ref: CIPAttribute[int] = CIPAttribute(8, int16)
    """Speed reference, Units: RPM / 2**speed_scale (attribute 8, required)."""

    current_actual: CIPAttribute[int] = CIPAttribute(9, int16)
    """Actual motor phase current, Units: 100mA / 2**current_scale (attribute
    9)."""

    current_limit: CIPAttribute[int] = CIPAttribute(10, int16)
    """Motor phase current limit, Units: 100mA / 2**current_scale (attribute
    10)."""

    torque_actual: CIPAttribute[int] = CIPAttribute(11, int16)
    """Actual torque, Units: Nm / 2**torque_scale (attribute 11)."""

    torque_ref: CIPAttribute[int] = CIPAttribute(12, int16)
    """Torque reference, Units: Nm / 2**torque_scale (attribute 12)."""

    process_actual: CIPAttribute[int] = CIPAttribute(13, int16)
    """Actual process control value, Units: % / 2**process_scale (attribute
    13)."""

    process_ref: CIPAttribute[int] = CIPAttribute(14, int16)
    """Process control reference set point, Units: % / 2**process_scale
    (attribute 14)."""

    power_actual: CIPAttribute[int] = CIPAttribute(15, int16)
    """Actual output power, Units: W / 2**power_scale (attribute 15)."""

    input_voltage: CIPAttribute[int] = CIPAttribute(16, int16)
    """Input voltage, Units: V / 2**voltage_scale (attribute 16)."""

    output_voltage: CIPAttribute[int] = CIPAttribute(17, int16)
    """Output voltage, Units: V / 2**voltage_scale (attribute 17)."""

    accel_time: CIPAttribute[int] = CIPAttribute(18, uint16)
    """Acceleration time from 0 to high_speed_limit, Units: ms / 2**time_scale
    (attribute 18)."""

    decel_time: CIPAttribute[int] = CIPAttribute(19, uint16)
    """Deceleration time from high_speed_limit to 0, Units: ms / 2**time_scale
    (attribute 19)."""

    low_speed_limit: CIPAttribute[int] = CIPAttribute(20, uint16)
    """Minimum speed limit, Units: RPM / 2**speed_scale (attribute 20)."""

    high_speed_limit: CIPAttribute[int] = CIPAttribute(21, uint16)
    """Maximum speed limit, Units: RPM / 2**speed_scale (attribute 21)."""

    speed_scale: CIPAttribute[int] = CIPAttribute(22, int8)
    """Speed scaling factor, range -128..127 (attribute 22)."""

    current_scale: CIPAttribute[int] = CIPAttribute(23, int8)
    """Current scaling factor, range -128..127 (attribute 23)."""

    torque_scale: CIPAttribute[int] = CIPAttribute(24, int8)
    """Torque scaling factor, range -128..127 (attribute 24)."""

    process_scale: CIPAttribute[int] = CIPAttribute(25, int8)
    """Process scaling factor, range -128..127 (attribute 25)."""

    power_scale: CIPAttribute[int] = CIPAttribute(26, int8)
    """Power scaling factor, range -128..127 (attribute 26)."""

    voltage_scale: CIPAttribute[int] = CIPAttribute(27, int8)
    """Voltage scaling factor, range -128..127 (attribute 27)."""

    time_scale: CIPAttribute[int] = CIPAttribute(28, int8)
    """Time scaling factor, range -128..127 (attribute 28)."""

    ref_from_net: CIPAttribute[int] = CIPAttribute(29, uint8)
    """Status of torque/speed reference: 0=local, 1=network (attribute 29)."""

    proc_from_net: CIPAttribute[int] = CIPAttribute(30, uint8)
    """Status of process control reference: 0=local, 1=network (attribute
    30)."""

    field_i_or_v: CIPAttribute[int] = CIPAttribute(31, uint8)
    """Selects Field Voltage (0) or Field Current (1) control for a DC drive
    (attribute 31)."""

    field_volt_ratio: CIPAttribute[int] = CIPAttribute(32, uint16)
    """Field voltage ratio, for voltage control of a DC drive (attribute
    32)."""

    field_current_setpoint: CIPAttribute[int] = CIPAttribute(33, uint16)
    """DC drive field current set point, Units: A / 2**current_scale (attribute
    33)."""

    field_weakening_enable: CIPAttribute[int] = CIPAttribute(34, uint8)
    """Enables (1) or disables (0) field weakening for a DC drive (attribute
    34)."""

    field_current_actual: CIPAttribute[int] = CIPAttribute(35, int16)
    """Actual field current for a DC drive, Units: A / 2**current_scale
    (attribute 35)."""

    field_min_current: CIPAttribute[int] = CIPAttribute(36, int16)
    """Minimum field current for a DC drive, Units: A / 2**current_scale
    (attribute 36)."""

    process_data_units: CIPAttribute[bytes] = CIPAttribute(37)
    """ENGUNITS code applied to process_actual/process_ref (attribute 37)."""

    speed_control: CIPAttribute[int] = CIPAttribute(38, uint8)
    """Bit flags requesting speed commands: bit0=Run, bit1=Idle, bit2=Standby,
    bit3=Coast (attribute 38, See Table 5-30.4)."""

    speed_status: CIPAttribute[int] = CIPAttribute(39, uint8)
    """Bit flags indicating current speed status (attribute 39, See Table
    5-30.4)."""

    speed_trip_time: CIPAttribute[int] = CIPAttribute(40, uint16)
    """Time speed_actual may exceed a vendor-specific hysteresis band, Units:

    ms / 2**time_scale (attribute 40).
    """

    max_rated_speed: CIPAttribute[int] = CIPAttribute(41, int16)
    """Vendor specific maximum rating, Units: RPM / 2**max_rated_speed_scale
    (attribute 41)."""

    max_rated_speed_scale: CIPAttribute[int] = CIPAttribute(42, int8)
    """Speed scaling for max_rated_speed, range -128..127 (attribute 42)."""

    speed_standby: CIPAttribute[int] = CIPAttribute(43, int16)
    """Speed setting used in Standby, Units: RPM / 2**speed_scale (attribute
    43)."""

    speed_actual_data_units: CIPAttribute[bytes] = CIPAttribute(44)
    """ENGUNITS code applied to speed_actual/speed_standby, default RPM
    (attribute 44)."""

    speed_ref_data_units: CIPAttribute[bytes] = CIPAttribute(45)
    """ENGUNITS code applied to
    speed_ref/max_rated_speed/low_speed_limit/high_speed_limit, default RPM
    (attribute 45)."""

    drive_on_hours: CIPAttribute[int] = CIPAttribute(46, int32)
    """Number of hours speed_actual has been > 0; does not roll over (attribute
    46)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an AC/DC Drive class attribute from instance 0 (See
        §5-30.1)."""
        return self.get_attr(attribute, instance=0)

    def restore(self) -> bytes:
        """Invoke Restore, reloading attribute values saved via
        :meth:`save`."""
        return self._expect_empty(self.message(CommonService.RESTORE))

    def save(self) -> bytes:
        """Invoke Save, persisting all attribute values to non-volatile
        storage."""
        return self._expect_empty(self.message(CommonService.SAVE))


class AcknowledgeHandlerObject(CIPObject):
    """Manages reception of message acknowledgments for a producing I/O
    application (See CIP Vol 1, §5-31).

    ``data_with_ack_path_list`` (attribute 7) is a list of heterogeneous
    (Connection Instance, CIP Path Length, CIP Path) tuples and is kept
    as raw bytes; ``ack_list`` (attribute 5) is a homogeneous UINT array
    with its own leading count, decoded directly.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.ACKNOWLEDGE_HANDLER

    acknowledge_timer: CIPAttribute[int] = CIPAttribute(1, uint16)
    """Time to wait for an acknowledge before resending, Units: ms, range
    1-65535, default 16 (attribute 1, required)."""

    retry_limit: CIPAttribute[int] = CIPAttribute(2, uint8)
    """Number of ack timeouts to wait before a RetryLimit_Reached event,
    default 1 (attribute 2)."""

    cos_producing_connection_instance: CIPAttribute[int] = CIPAttribute(3, uint16)
    """Connection instance whose producing I/O object is notified of ack
    events; Set while inactive, Get-only once active (attribute 3,
    required)."""

    ack_list_size: CIPAttribute[int] = CIPAttribute(4, uint8)
    """Maximum number of members in ack_list; 0 = dynamic (attribute 4)."""
    ack_list: CIPAttribute[Collection[int]] = CIPAttribute(5, uint16[uint8::])
    """Active connection instances currently receiving acks (attribute 5)."""

    data_with_ack_path_list_size: CIPAttribute[int] = CIPAttribute(6, uint8)
    """Maximum number of members in data_with_ack_path_list; 0 = dynamic (attribute 6)."""

    data_with_ack_path_list: CIPAttribute[bytes] = CIPAttribute(7)
    """List of (Connection Instance, CIP Path Length, CIP Path) used to forward
    data received with an acknowledgment (attribute 7)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an Acknowledge Handler class attribute from instance 0 (See
        §5-31.1)."""
        return self.get_attr(attribute, instance=0)

    def create(self) -> bytes:
        """Invoke Create at the class level, allocating a new Acknowledge
        Handler instance."""
        return self.message(CommonService.CREATE, instance=0)

    def delete_all(self) -> bytes:
        """Invoke Delete at the class level, removing all dynamically created
        instances."""
        return self._expect_empty(self.message(CommonService.DELETE, instance=0))

    def delete(self) -> bytes:
        """Invoke Delete on this instance."""
        return self._expect_empty(self.message(CommonService.DELETE))

    def add_ack_data_path(self, request_data: bytes) -> bytes:
        """Invoke Add_AckData_Path (service 0x4B) with a caller-built
        (Connection Instance, CIP Path Length, CIP Path) request payload."""
        return self.message(0x4B, request_data)

    def remove_ack_data_path(self, request_data: bytes) -> bytes:
        """Invoke Remove_AckData_Path (service 0x4C) with a caller-built
        Connection Instance request payload."""
        return self.message(0x4C, request_data)


class OverloadObject(CIPObject):
    """Models an AC motor overload protection device (See CIP Vol 1, §5-32)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.OVERLOAD

    num_attr: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attributes: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attribute IDs supported by this instance (attribute 2)."""

    trip_flc_set: CIPAttribute[int] = CIPAttribute(3, int16)
    """Overload full load current setting, Units: 100mA / 2**current_scale
    (attribute 3)."""

    trip_class: CIPAttribute[int] = CIPAttribute(4, uint8)
    """Trip class setting, range 0-200 (attribute 4)."""

    avg_current: CIPAttribute[int] = CIPAttribute(5, int16)
    """Average of the three phase currents, Units: 100mA / 2**current_scale
    (attribute 5)."""

    percent_phase_imbalance: CIPAttribute[int] = CIPAttribute(6, uint8)
    """Percent phase imbalance (attribute 6)."""

    percent_thermal_capacity: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Percent thermal capacity used (attribute 7)."""

    current_l1: CIPAttribute[int] = CIPAttribute(8, int16)
    """Actual motor phase current L1, Units: 100mA / 2**current_scale
    (attribute 8)."""

    current_l2: CIPAttribute[int] = CIPAttribute(9, int16)
    """Actual motor phase current L2, Units: 100mA / 2**current_scale
    (attribute 9)."""

    current_l3: CIPAttribute[int] = CIPAttribute(10, int16)
    """Actual motor phase current L3, Units: 100mA / 2**current_scale
    (attribute 10)."""

    ground_current: CIPAttribute[int] = CIPAttribute(11, int16)
    """Ground current, Units: 100mA / 2**current_scale (attribute 11)."""

    current_scale: CIPAttribute[int] = CIPAttribute(12, int8)
    """Current scaling factor, range -128..127, default 0 (attribute 12)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an Overload class attribute from instance 0 (See §5-32.1)."""
        return self.get_attr(attribute, instance=0)

    def restore(self) -> bytes:
        """Invoke Restore, reloading attribute values saved via
        :meth:`save`."""
        return self._expect_empty(self.message(CommonService.RESTORE))

    def save(self) -> bytes:
        """Invoke Save, persisting all attribute values to non-volatile
        storage."""
        return self._expect_empty(self.message(CommonService.SAVE))


class SoftstartObject(CIPObject):
    """Models a soft-start motor starter (See CIP Vol 1, §5-33)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.SOFTSTART
    num_attr: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attributes: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attribute IDs supported by this instance (attribute 2)."""

    at_reference: CIPAttribute[int] = CIPAttribute(3, uint8)
    """0 = not at reference, 1 = output at starting/stopping voltage reference (attribute 3, required)."""

    start_mode: CIPAttribute[int] = CIPAttribute(4, uint8)
    """0=No Ramp/No Limit, 1=Voltage Ramp, 2=Current Limit, 3=Ramp+Limit,
    10-255=Vendor specific (attribute 4, required)."""

    stop_mode: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0=Coast, 1=Ramp Down, 2=Brake, 10-255=Vendor specific (attribute 5)."""

    ramp_mode: CIPAttribute[int] = CIPAttribute(6, uint8)
    """0=Single Ramp, 1=Dual Contiguous Ramp, 2=Dual Independent Ramp
    (attribute 6)."""

    ramp_time1: CIPAttribute[int] = CIPAttribute(7, uint16)
    """First ramp duration, Units: tenths of seconds (attribute 7)."""

    initial_voltage1: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Starting voltage for the first ramp, Units: % of full line voltage
    (attribute 8)."""

    ramp_time2: CIPAttribute[int] = CIPAttribute(9, uint16)
    """Second ramp duration (Dual Ramp modes), Units: tenths of seconds
    (attribute 9)."""

    initial_voltage2: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Starting voltage for the second ramp, Units: % of full line voltage
    (attribute 10)."""

    rotation: CIPAttribute[int] = CIPAttribute(11, uint8)
    """0 = ABC phase rotation, 1 = CBA phase rotation (attribute 11)."""

    kick_start: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Enables (1) or disables (0) fixed-time kick start (attribute 12)."""

    kick_start_time: CIPAttribute[int] = CIPAttribute(13, uint8)
    """Kick start duration, Units: tenths of seconds (attribute 13)."""

    kick_start_voltage: CIPAttribute[int] = CIPAttribute(14, uint16)
    """Kick start voltage, Units: % of full line voltage (attribute 14)."""

    energy_saver: CIPAttribute[int] = CIPAttribute(15, uint8)
    """Enables (1) or disables (0) energy saver mode (attribute 15)."""

    decel_time: CIPAttribute[int] = CIPAttribute(16, uint16)
    """Ramp-to-stop/DC-brake duration, Units: tenths of seconds (attribute
    16)."""

    current_limit_set: CIPAttribute[int] = CIPAttribute(17, uint16)
    """Current limit for starting, Units: % of Motor Data rated_current
    (attribute 17)."""

    braking_current_set: CIPAttribute[int] = CIPAttribute(18, uint16)
    """DC braking current for stopping, Units: % of Motor Data rated_current
    (attribute 18)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Softstart class attribute from instance 0 (See §5-33.1)."""
        return self.get_attr(attribute, instance=0)

    def restore(self) -> bytes:
        """Invoke Restore, reloading attribute values saved via
        :meth:`save`."""
        return self._expect_empty(self.message(CommonService.RESTORE))

    def save(self) -> bytes:
        """Invoke Save, persisting all attribute values to non-volatile
        storage."""
        return self._expect_empty(self.message(CommonService.SAVE))
