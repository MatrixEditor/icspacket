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

"""[ODVA CIP Vol 1] Wrappers for the "Hierarchy of Semiconductor Equipment
Devices" object family:

- S-Device Supervisor (class 0x30, §5-35),
- S-Analog Sensor (class 0x31, §5-36),
- S-Analog Actuator (class 0x32, §5-37),
- S-Single Stage Controller (class 0x33, §5-38),
- S-Gas Calibration (class 0x34, §5-39),
- Trip Point (class 0x35, §5-40),
- S-Partial Pressure (class 0x38, §5-43), and
- S-Sensor Calibration (class 0x40, §5-44).

Every object in this family is managed by the S-Device Supervisor Object
and shares its "Subclass" extensibility mechanism: instance/class
attribute 99 reports whether a subclass is active (0 = none) and, if so,
IDs 81-96 (instance) / 96 (class) and downward are redefined by that
subclass. Subclass-specific attributes/services (e.g. S-Device
Supervisor's "Power Generator" subclass) are vendor/profile specific and
out of scope here, consistent with this library's treatment of other
device-profile extensions.
"""

from collections.abc import Collection
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
from caterpillar.model import StructDefMixin
from caterpillar.py import pack, unpack
from caterpillar.shortcuts import LittleEndian, struct
from caterpillar.types import float32_t, uint8_t, uint16_t, uint32_t

from ..const import ClassCode, CommonService
from ..epath import EPATH
from ._base import CIP_EPATH, CIP_SHORT_STRING, CIPAttribute, CIPObject

__all__ = [
    "ELEMENTARY_DATA_TYPES",
    "CIPDateAndTime",
    "CreateRangeRequest",
    "CreateRangeResult",
    "FullScale",
    "GasCalibrationEntry",
    "GroupEnableRequest",
    "PartialPressureInstanceEntry",
    "PartialPressureReading",
    "SAnalogActuatorObject",
    "SAnalogSensorObject",
    "SDeviceSupervisorObject",
    "SGasCalibrationObject",
    "SPartialPressureObject",
    "SSensorCalibrationObject",
    "SSingleStageControllerObject",
    "SensorCalibrationEntry",
    "TripPointObject",
    "decode_elementary_value",
    "encode_elementary_value",
]


@struct(order=LittleEndian)
class CIPDateAndTime(StructDefMixin):
    """CIP ``DATE_AND_TIME`` value (See CIP Vol 1, Appendix C, C-6.2)."""

    time_of_day: uint32_t
    """Milliseconds since midnight."""

    date: uint16_t
    """Days since 1972-01-01."""


#: CIP Elementary Data Type code (Appendix C-6.1, Table C-6.1) -> wire
#: schema. Used by the S-Analog Sensor/Actuator and S-Single Stage
#: Controller "Data Type"/"Gain Data Type"/"CV Data Type" attributes to
#: select the wire type of their Data-Type-dependent companion
#: attributes. Only the numeric elementary types are mapped; BOOL and
#: non-numeric types (STRING, BYTE/WORD/..., STIME/DATE/...) have no
#: fixed numeric meaning here and decode to raw bytes.
ELEMENTARY_DATA_TYPES: dict[int, Any] = {
    0xC2: int8,  # SINT
    0xC3: int16,  # INT
    0xC4: int32,  # DINT
    0xC5: int64,  # LINT
    0xC6: uint8,  # USINT
    0xC7: uint16,  # UINT
    0xC8: uint32,  # UDINT
    0xC9: uint64,  # ULINT
    0xCA: float32,  # REAL
    0xCB: float64,  # LREAL
}


def decode_elementary_value(data: bytes, data_type: int) -> int | float | bytes:
    """Decode a Data-Type-dependent attribute payload using its companion Data
    Type attribute's Appendix C-6.1 code."""
    schema = ELEMENTARY_DATA_TYPES.get(data_type)
    return unpack(schema, data, order=LittleEndian) if schema is not None else data


def encode_elementary_value(value: int | float | bytes, data_type: int) -> bytes:
    """Encode a Data-Type-dependent attribute payload using its companion Data
    Type attribute's Appendix C-6.1 code."""
    schema = ELEMENTARY_DATA_TYPES.get(data_type)
    return (
        pack(value, schema, order=LittleEndian) if schema is not None else bytes(value)
    )


@struct(order=LittleEndian)
class FullScale(StructDefMixin):
    """Full Scale amount + ENGUNITS code pair, shared by the S-Gas Calibration
    and S-Sensor Calibration objects' ``full_scale`` attribute (See
    §5-39.2/§5-44.3, Table 5-39.2/5-44.2)."""

    amount: float32_t
    """The amount of measured parameter corresponding to full scale."""

    units: uint16_t
    """ENGUNITS code for ``amount`` (See Appendix D)."""


@struct(order=LittleEndian)
class GasCalibrationEntry(StructDefMixin):
    """One S-Gas Calibration Get_All_Instances response element (See §5-39.5,
    Table 5-39.5)."""

    instance_id: uint16_t
    gas_standard_number: uint16_t
    valid_sensor_instance: uint16_t


@struct(order=LittleEndian)
class SensorCalibrationEntry(StructDefMixin):
    """One S-Sensor Calibration Get_All_Instances response element (See
    §5-44.7.2, Table 5-44.5)."""

    instance_id: uint16_t
    calibration_id_number: uint16_t
    valid_sensor_instance: uint16_t


@struct(order=LittleEndian)
class PartialPressureInstanceEntry(StructDefMixin):
    """One S-Partial Pressure Get_Instance_List response element (See
    §5-43.4.2, Table 5-43.11)."""

    instance_number: uint16_t
    instance_type: uint8_t
    amu: float32_t
    ending_amu: float32_t
    gas_standard_number: uint16_t


@struct(order=LittleEndian)
class PartialPressureReading(StructDefMixin):
    """One Get_Pressures/Get_All_Pressures response element (See §5-43.4.3/
    §5-43.4.4, Table 5-43.12/5-43.13)."""

    instance_id: uint16_t
    partial_pressure: float32_t


@struct(order=LittleEndian)
class CreateRangeRequest(StructDefMixin):
    """Create_Range (0x4B) request parameters (See §5-43.4.1, Table 5-43.9)."""

    start_amu: float32_t
    end_amu: float32_t
    num_instances: uint16_t
    starting_id: uint16_t
    """First instance ID to create; 0 = use next available."""

    group_id: uint8_t
    """Group value assigned to the created instances."""


@struct(order=LittleEndian)
class CreateRangeResult(StructDefMixin):
    """Create_Range (0x4B) success response (See §5-43.4.1, Table 5-43.10)."""

    starting_id: uint16_t
    ending_id: uint16_t


@struct(order=LittleEndian)
class GroupEnableRequest(StructDefMixin):
    """Group_Enable (0x4F) request parameters (See §5-43.4.5, Table
    5-43.14)."""

    enable: uint8_t
    """0 = Disable, 1 = Enable."""

    group_id: uint8_t
    """Affects every instance whose ``group_id`` attribute has this value."""


class SDeviceSupervisorObject(CIPObject):
    """Manages application object state, exceptions and behavior shared by
    every object in the Hierarchy of Semiconductor Equipment Devices (See CIP
    Vol 1, §5-35).

    Class attr 1 (Revision, fixed at 2) and class attr 99 (Subclass) are
    available via :meth:`get_class_attribute`. ``exception_detail_alarm``/
    ``exception_detail_warning`` (attributes 13/14) are each a STRUCT of
    three (Size:USINT, Detail:BYTE[Size]) sub-structures - Common,
    Device-specific and Manufacturer-specific - and are kept as raw bytes
    due to that nested variable-length shape.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.S_DEVICE_SUPERVISOR

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by the object instance (attribute 1)."""

    attribute_list: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attributes supported by the object instance (attribute 2)."""

    device_type: CIPAttribute[str] = CIPAttribute(3, CIP_SHORT_STRING)
    """Specific Device Model within the SEMI S/A hierarchy, max 8 characters
    (attribute 3, required)."""

    semi_standard_revision_level: CIPAttribute[str] = CIPAttribute(4, CIP_SHORT_STRING)
    """SEMI S/A Network Standard revision, e.g. ``"E54-0997"`` (attribute 4,
    required)."""

    manufacturer_name: CIPAttribute[str] = CIPAttribute(5, CIP_SHORT_STRING)
    """Max 20 characters (attribute 5, required)."""

    manufacturer_model_number: CIPAttribute[str] = CIPAttribute(6, CIP_SHORT_STRING)
    """Max 20 characters, manufacturer specified (attribute 6, required)."""

    software_revision_level: CIPAttribute[str] = CIPAttribute(7, CIP_SHORT_STRING)
    """Max 6 characters (attribute 7, required)."""

    hardware_revision_level: CIPAttribute[str] = CIPAttribute(8, CIP_SHORT_STRING)
    """Max 6 characters (attribute 8, required)."""

    manufacturer_serial_number: CIPAttribute[str] = CIPAttribute(9, CIP_SHORT_STRING)
    """Max 30 characters, manufacturer specified (attribute 9)."""

    device_configuration: CIPAttribute[str] = CIPAttribute(10, CIP_SHORT_STRING)
    """Max 50 characters, manufacturer specified free-form configuration info
    (attribute 10)."""

    device_status: CIPAttribute[int] = CIPAttribute(11, uint8)
    """0=Undefined, 1=Self Testing, 2=Idle, 3=Self-Test Exception, 4=Executing,
    5=Abort, 6=Critical Fault, 51-99=Device Specific, 100-255=Vendor Specific
    (attribute 11, required)."""

    exception_status: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Bit 7=0: Basic method, device/profile specific bits 0-6.

    Bit 7=1: Expanded method - bit 0=common alarm, 1=device alarm, 2=mfg alarm,
    4=common warning, 5=device warning, 6=mfg warning (attribute 12,
    required).
    """

    exception_detail_alarm: CIPAttribute[bytes] = CIPAttribute(13)
    """Common/Device/Manufacturer alarm detail bitmaps; present only if
    Expanded method and exception_status bit 7 conditions apply (attribute
    13)."""

    exception_detail_warning: CIPAttribute[bytes] = CIPAttribute(14)
    """Common/Device/Manufacturer warning detail bitmaps, same shape as
    exception_detail_alarm (attribute 14)."""

    alarm_enable: CIPAttribute[int] = CIPAttribute(15, uint8)
    """Enables alarm exception reporting (attribute 15, required)."""

    warning_enable: CIPAttribute[int] = CIPAttribute(16, uint8)
    """Enables warning exception reporting (attribute 16, required)."""

    time: CIPAttribute[CIPDateAndTime] = CIPAttribute(17, CIPDateAndTime)
    """The device's internal realtime clock (attribute 17)."""

    clock_power_cycle_behavior: CIPAttribute[int] = CIPAttribute(18, uint8)
    """0=clock always resets on power cycle [default], 1=stored in NV memory at
    power down, 2=battery-backed and free-running (attribute 18)."""

    last_maintenance_date: CIPAttribute[int] = CIPAttribute(19, uint16)
    """DATE the device was last serviced (attribute 19)."""

    next_scheduled_maintenance_date: CIPAttribute[int] = CIPAttribute(20, uint16)
    """DATE the device should next be serviced (attribute 20)."""

    scheduled_maintenance_expiration_timer: CIPAttribute[int] = CIPAttribute(21, int16)
    """Countdown to the next scheduled maintenance (attribute 21)."""

    scheduled_maintenance_expiration_warning_enable: CIPAttribute[int] = CIPAttribute(
        22, uint8
    )
    """Enables a warning when scheduled_maintenance_expiration_timer expires;
    required if Calibration Expiration is supported (attribute 22)."""

    run_hours: CIPAttribute[int] = CIPAttribute(23, uint32)
    """Hours the device has had power applied, resolution 1 hour, stored in NV
    memory (attribute 23)."""

    endpoint: CIPAttribute[int] = CIPAttribute(24, uint8)
    """0=Endpoint not obtained, 1=Endpoint obtained by the current recipe
    step's algorithm (attribute 24)."""

    recipe: CIPAttribute[int] = CIPAttribute(25, uint16)
    """Selects the endpoint algorithm to use (attribute 25)."""

    subclass: CIPAttribute[int] = CIPAttribute(99, uint16)
    """0=No subclass, 1=Power Generator (attribute 99)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an S-Device Supervisor class attribute from instance 0 (See
        §5-35.1)."""
        return self.get_attr(attribute, instance=0)

    def reset(self) -> bytes:
        """Invoke Reset, returning the device to the Self-Testing state (See
        §5-35.4)."""
        return self._expect_empty(self.message(CommonService.RESET))

    def start(self) -> bytes:
        """Invoke Start, moving the device to the Executing state (See
        §5-35.4)."""
        return self._expect_empty(self.message(CommonService.START))

    def stop(self) -> bytes:
        """Invoke Stop, moving the device to the Idle state (optional, See
        §5-35.4)."""
        return self._expect_empty(self.message(CommonService.STOP))

    def abort(self) -> bytes:
        """Invoke Abort (0x4B), moving the device to the Abort state (See
        §5-35.5.1)."""
        return self._expect_empty(self.message(0x4B))

    def recover(self) -> bytes:
        """Invoke Recover (0x4C), moving the device out of the Abort state to
        Idle (See §5-35.5.2)."""
        return self._expect_empty(self.message(0x4C))

    def perform_diagnostics(self, test_id: int = 0) -> bytes:
        """Invoke Perform_Diagnostics (0x4E): 0=Standard, 64-127=Device
        Specific, 128-255=Manufacturer Specific.

        Response shape is implementation-specific and returned
        unmodified (See §5-35.5.3).
        """
        request = pack(test_id, uint8, order=LittleEndian)
        return self.message(0x4E, request)


class SAnalogSensorObject(CIPObject):
    """Models an analog sensor reading in the Hierarchy of Semiconductor
    Equipment Devices (See CIP Vol 1, §5-36).

    ``value`` and its related attributes (``full_scale``, ``offset_a``,
    ``offset_b``, ``gain``, ``unity_gain_reference``, the alarm/warning
    trip points and hysteresis, ``safe_value``, ``overrange``,
    ``underrange`` and ``produce_trigger_delta``) are all "INT or
    specified by Data Type" - their wire type is only known at runtime
    from ``data_type``/``offset_a_data_type``/``gain_data_type``, so they
    are exposed as raw bytes; use :func:`decode_elementary_value`/
    :func:`encode_elementary_value` (or :meth:`read_value`/
    :meth:`write_value` for ``value`` itself) once the relevant Data Type
    attribute is known.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.S_ANALOG_SENSOR

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by this object instance (attribute 1)."""

    attribute_list: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attributes supported by this object instance (attribute 2)."""

    data_type: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Appendix C-6.1 code selecting the wire type of ``value`` and related
    attributes; settable only in the Idle state (attribute 3)."""

    data_units: CIPAttribute[bytes] = CIPAttribute(4)
    """ENGUNITS context of ``value`` and related attributes, settable only in
    the Idle state (attribute 4, See Appendix D)."""

    reading_valid: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0=Value is valid, 1=invalid (attribute 5)."""

    value: CIPAttribute[bytes] = CIPAttribute(6)
    """The corrected sensor reading: Value = Gain * (Sensor Reading +
    Offset-A) + Offset-B (attribute 6, required)."""

    status: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Bit 0=High Alarm, 1=Low Alarm, 2=High Warning, 3=Low Warning (attribute
    7, required)."""

    alarm_enable: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Enables setting the alarm status bits (attribute 8)."""

    warning_enable: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Enables setting the warning status bits (attribute 9)."""

    full_scale: CIPAttribute[bytes] = CIPAttribute(10)
    """The full-scale value, in the same data type/units as ``value``
    (attribute 10)."""

    offset_a_data_type: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Appendix C-6.1 code for ``offset_a``, if it is not the same type as
    ``value`` (attribute 11)."""

    offset_a: CIPAttribute[bytes] = CIPAttribute(12)
    """Amount added to the raw sensor reading before ``gain`` is applied
    (attribute 12)."""

    gain_data_type: CIPAttribute[int] = CIPAttribute(13, uint8)
    """Appendix C-6.1 code for ``gain``/``unity_gain_reference``, required if
    ``gain`` is not REAL (attribute 13)."""

    gain: CIPAttribute[bytes] = CIPAttribute(14)
    """Multiplier applied to (Sensor Reading + Offset-A); REAL unless
    gain_data_type says otherwise, default 1.0 (attribute 14)."""

    unity_gain_reference: CIPAttribute[bytes] = CIPAttribute(15)
    """Value of ``gain`` equivalent to a gain of 1.0, used to normalize it
    (attribute 15)."""

    offset_b: CIPAttribute[bytes] = CIPAttribute(16)
    """Amount added to Value after ``gain`` is applied, default 0 (attribute
    16)."""

    alarm_trip_point_high: CIPAttribute[bytes] = CIPAttribute(17)
    """Value above which a High Alarm occurs, default = max for the data
    type (attribute 17)."""

    alarm_trip_point_low: CIPAttribute[bytes] = CIPAttribute(18)
    """Value below which a Low Alarm occurs, default = min for the data type
    (attribute 18)."""

    alarm_hysteresis: CIPAttribute[bytes] = CIPAttribute(19)
    """Recovery margin to clear an Alarm condition, default 0 (attribute
    19)."""

    alarm_settling_time: CIPAttribute[int] = CIPAttribute(20, uint16)
    """Milliseconds a trip condition must persist before the Alarm bit is set
    (attribute 20)."""

    warning_trip_point_high: CIPAttribute[bytes] = CIPAttribute(21)
    """Value above which a High Warning occurs (attribute 21)."""

    warning_trip_point_low: CIPAttribute[bytes] = CIPAttribute(22)
    """Value below which a Low Warning occurs (attribute 22)."""

    warning_hysteresis: CIPAttribute[bytes] = CIPAttribute(23)
    """Recovery margin to clear a Warning condition, default 0 (attribute
    23)."""

    warning_settling_time: CIPAttribute[int] = CIPAttribute(24, uint16)
    """Milliseconds a trip condition must persist before the Warning bit is set
    (attribute 24)."""

    safe_state: CIPAttribute[int] = CIPAttribute(25, uint8)
    """Behavior for states other than Executing, default 0 (attribute 25)."""

    safe_value: CIPAttribute[bytes] = CIPAttribute(26)
    """Value used for safe_state = Use Safe Value, default 0 (attribute
    26)."""

    autozero_enable: CIPAttribute[int] = CIPAttribute(27, uint8)
    """Enables an automatic zero-adjust cycle (attribute 27)."""

    autozero_status: CIPAttribute[int] = CIPAttribute(28, uint8)
    """Status of the autozero_enable cycle (attribute 28)."""

    autorange_enable: CIPAttribute[int] = CIPAttribute(29, uint8)
    """Enables automatic range selection (attribute 29)."""

    range_multiplier: CIPAttribute[float] = CIPAttribute(30, float32)
    """Current multiplier applied by the autorange_enable mechanism (attribute
    30)."""

    averaging_time: CIPAttribute[int] = CIPAttribute(31, uint16)
    """Milliseconds over which readings are averaged (attribute 31)."""

    overrange: CIPAttribute[bytes] = CIPAttribute(32)
    """Value above which Reading Valid is set to invalid, default = max for
    the data type (attribute 32)."""

    underrange: CIPAttribute[bytes] = CIPAttribute(33)
    """Value below which Reading Valid is set to invalid, default = min for
    the data type (attribute 33)."""

    produce_trigger_delta: CIPAttribute[bytes] = CIPAttribute(34)
    """Change in Value required to trigger a Change-of-State production; 0 =
    disabled (attribute 34)."""

    calibration_object_instance: CIPAttribute[int] = CIPAttribute(35, uint16)
    """S-Sensor Calibration object instance active for this instance; 0 =
    disabled (attribute 35)."""

    produce_trigger_delta_type: CIPAttribute[int] = CIPAttribute(36, uint8)
    """Appendix C-6.1 code for produce_trigger_delta, if not the same type as
    ``value`` (attribute 36)."""

    value_descriptor: CIPAttribute[str] = CIPAttribute(37, CIP_SHORT_STRING)
    """User defined name of the sensed parameter, max 20 characters (attribute
    37)."""

    subclass: CIPAttribute[int] = CIPAttribute(99, uint16)
    """0=No subclass, 1=Flow Diagnostics, 2=Heat Transfer Vacuum Gauge,
    3=Capacitance Manometer, 4=Cold Cathode Ion Gauge, 5=Hot Cathode Ion Gauge,
    6=Transfer Function (attribute 99)."""

    def read_value(self) -> int | float | bytes:
        """Read and decode ``value`` according to the current ``data_type``."""
        return decode_elementary_value(self.value, self.data_type)

    def write_value(self, value: int | float | bytes) -> bytes:
        """Encode and write ``value`` according to the current
        ``data_type``."""
        return self.set_empty(6, encode_elementary_value(value, self.data_type))

    def zero_adjust(self, target_value: int | float | bytes = 0) -> bytes:
        """Invoke Zero_Adjust (0x4B): asks the device to modify Offset-A and/or
        Offset-B so that ``value`` equals ``target_value``, encoded per
        ``data_type`` (default 0, See §5-36.5.1)."""
        request = encode_elementary_value(target_value, self.data_type)
        return self._expect_empty(self.message(0x4B, request))

    def gain_adjust(self, target_value: int | float | bytes) -> bytes:
        """Invoke Gain_Adjust (0x4C): asks the device to modify ``gain`` so
        that ``value`` equals ``target_value``, encoded per ``data_type`` (See
        §5-36.5.1)."""
        request = encode_elementary_value(target_value, self.data_type)
        return self._expect_empty(self.message(0x4C, request))


class SAnalogActuatorObject(CIPObject):
    """Models an analog actuator drive signal in the Hierarchy of Semiconductor
    Equipment Devices (See CIP Vol 1, §5-37).

    ZERO corresponds to the powered-off/not-actuated state, which may or
    may not equal the physically de-energized position depending on
    device wiring. ``value`` and its related attributes are all "INT or
    specified by Data Type" and, as with :class:`SAnalogSensorObject`,
    are exposed as raw bytes with :meth:`read_value`/:meth:`write_value`
    provided for ``value`` itself. This object has no object-specific
    services; its behavior is entirely managed by
    :class:`SDeviceSupervisorObject`.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.S_ANALOG_ACTUATOR

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by this object instance (attribute 1)."""

    attribute_list: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attributes supported by this object instance (attribute 2)."""

    data_type: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Appendix C-6.1 code selecting the wire type of ``value`` and related
    attributes; settable only in the Idle state (attribute 3)."""

    data_units: CIPAttribute[bytes] = CIPAttribute(4)
    """ENGUNITS context of ``value``, settable only in the Idle state
    (attribute 4, See Appendix D)."""

    override: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0=normal [default]; any other value overrides the physical actuator and
    ``value`` is ignored (attribute 5, required)."""

    value: CIPAttribute[bytes] = CIPAttribute(6)
    """The uncorrected analog output value, default 0 (attribute 6,
    required)."""

    status: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Alarm/Warning state of this object instance, default 0 (attribute 7,
    required)."""

    alarm_enable: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Enables setting the alarm status bit, default disabled (attribute 8)."""

    warning_enable: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Enables setting the warning status bit, default disabled (attribute
    9)."""

    offset: CIPAttribute[bytes] = CIPAttribute(10)
    """Amount added to Value prior to the application of gain, default 0
    (attribute 10)."""

    bias: CIPAttribute[bytes] = CIPAttribute(11)
    """Amount added to Value after the application of gain, default 0
    (attribute 11)."""

    gain_data_type: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Appendix C-6.1 code for ``gain``/``unity_gain_reference``, required if
    ``gain`` is not REAL (attribute 12)."""

    gain: CIPAttribute[bytes] = CIPAttribute(13)
    """Scales Value prior to driving the physical actuator; REAL unless
    gain_data_type says otherwise, default 1.0 (attribute 13)."""

    unity_gain_reference: CIPAttribute[bytes] = CIPAttribute(14)
    """Value of ``gain`` equivalent to a gain of 1.0, default 1.0 (attribute
    14)."""

    alarm_trip_point_high: CIPAttribute[bytes] = CIPAttribute(15)
    """Value above which an Alarm occurs, default = max for the data type
    (attribute 15)."""

    alarm_trip_point_low: CIPAttribute[bytes] = CIPAttribute(16)
    """Value below which an Alarm occurs, default = min for the data type
    (attribute 16)."""

    alarm_hysteresis: CIPAttribute[bytes] = CIPAttribute(17)
    """Recovery margin to clear an Alarm condition, default 0 (attribute
    17)."""

    warning_trip_point_high: CIPAttribute[bytes] = CIPAttribute(18)
    """Value above which a Warning occurs, default = max for the data type
    (attribute 18)."""

    warning_trip_point_low: CIPAttribute[bytes] = CIPAttribute(19)
    """Value below which a Warning occurs, default = min for the data type
    (attribute 19)."""

    warning_hysteresis: CIPAttribute[bytes] = CIPAttribute(20)
    """Recovery margin to clear a Warning condition, default 0 (attribute
    20)."""

    safe_state: CIPAttribute[int] = CIPAttribute(21, uint8)
    """Behavior for states other than Execute, default 0 (attribute 21)."""

    safe_value: CIPAttribute[bytes] = CIPAttribute(22)
    """Value used for safe_state = Use Safe Value, default 0 (attribute
    22)."""

    subclass: CIPAttribute[int] = CIPAttribute(99, uint16)
    """0=No subclass (attribute 99)."""

    def read_value(self) -> int | float | bytes:
        """Read and decode ``value`` according to the current ``data_type``."""
        return decode_elementary_value(self.value, self.data_type)

    def write_value(self, value: int | float | bytes) -> bytes:
        """Encode and write ``value`` according to the current
        ``data_type``."""
        return self.set_empty(6, encode_elementary_value(value, self.data_type))


class SSingleStageControllerObject(CIPObject):
    """Models a closed-loop controller (Setpoint / Process Variable /
    Control Variable) in the Hierarchy of Semiconductor Equipment Devices
    (See CIP Vol 1, §5-38): ``Process Variable = Setpoint``, achieved by
    driving ``control_variable``.

    ``setpoint``/``process_variable`` (data_type-dependent) and
    ``control_variable`` (cv_data_type-dependent, Get-only) are exposed as
    raw bytes with dedicated decode/encode helpers; ``alarm_error_band``/
    ``warning_error_band``/``safe_value`` share ``setpoint``'s data type
    but are secondary and stay raw. This object has no object-specific
    services.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.S_SINGLE_STAGE_CONTROLLER

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported in this object instance (attribute 1)."""

    attribute_list: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attributes supported in this object instance (attribute 2)."""

    data_type: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Appendix C-6.1 code selecting the wire type of ``setpoint``/
    ``process_variable`` and related attributes (attribute 3)."""

    data_units: CIPAttribute[bytes] = CIPAttribute(4)
    """ENGUNITS context of ``setpoint``/``process_variable`` (attribute 4, See
    Appendix D)."""

    control_mode: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0=Normal [default], 1=Zero/Off/Closed, 2=Full/On/Open, 3=Hold, 4=Safe
    State, 64-127=Device Specific, 128-255=Vendor Specific (attribute 5)."""

    setpoint: CIPAttribute[bytes] = CIPAttribute(6)
    """The desired value for process_variable, default 0 (attribute 6,
    required)."""

    process_variable: CIPAttribute[bytes] = CIPAttribute(7)
    """The measured process parameter; required unless this device has no
    internal sensor, default 0 (attribute 7)."""

    cv_data_type: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Appendix C-6.1 code selecting the wire type of ``control_variable``
    (attribute 8)."""

    control_variable: CIPAttribute[bytes] = CIPAttribute(9)
    """The controller's drive signal output; required unless this device has no
    internal actuator, default 0 (attribute 9)."""

    status: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Bit 0=Alarm Exception, 1=Warning Exception, default 0 (attribute 10,
    required)."""

    alarm_enable: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Enables setting the Alarm status bit (attribute 11)."""

    warning_enable: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Enables setting the Warning status bit (attribute 12)."""

    alarm_settling_time: CIPAttribute[int] = CIPAttribute(13, uint16)
    """Milliseconds allowed for the control loop to settle within
    alarm_error_band, default 0 (attribute 13)."""

    alarm_error_band: CIPAttribute[bytes] = CIPAttribute(14)
    """Allowed Setpoint/Process Variable deviation before an Alarm timer
    starts, default 0 (attribute 14)."""

    warning_settling_time: CIPAttribute[int] = CIPAttribute(15, uint16)
    """Milliseconds allowed for the control loop to settle within
    warning_error_band, default 0 (attribute 15)."""

    warning_error_band: CIPAttribute[bytes] = CIPAttribute(16)
    """Allowed Setpoint/Process Variable deviation before a Warning timer
    starts, default 0 (attribute 16)."""

    safe_state: CIPAttribute[int] = CIPAttribute(17, uint8)
    """Behavior for states other than Executing, default 0 (attribute 17)."""

    safe_value: CIPAttribute[bytes] = CIPAttribute(18)
    """Value used for safe_state = Use Safe Value, default 0 (attribute
    18)."""

    ramp_rate: CIPAttribute[int] = CIPAttribute(19, uint32)
    """Milliseconds to reach Setpoint; 0 = disabled [default] (attribute
    19)."""

    subclass: CIPAttribute[int] = CIPAttribute(99, uint16)
    """0=No subclass, 1=PID & Source Select, 2=DC Generator, 3=RF Generator,
    4=Frequency Control (attribute 99)."""

    def read_setpoint(self) -> int | float | bytes:
        """Read and decode ``setpoint`` according to the current
        ``data_type``."""
        return decode_elementary_value(self.setpoint, self.data_type)

    def write_setpoint(self, value: int | float | bytes) -> bytes:
        """Encode and write ``setpoint`` according to the current
        ``data_type``."""
        return self.set_empty(6, encode_elementary_value(value, self.data_type))

    def read_process_variable(self) -> int | float | bytes:
        """Read and decode ``process_variable`` according to the current
        ``data_type``."""
        return decode_elementary_value(self.process_variable, self.data_type)

    def write_process_variable(self, value: int | float | bytes) -> bytes:
        """Encode and write ``process_variable`` according to the current
        ``data_type``."""
        return self.set_empty(7, encode_elementary_value(value, self.data_type))

    def read_control_variable(self) -> int | float | bytes:
        """Read and decode ``control_variable`` according to the current
        ``cv_data_type``."""
        return decode_elementary_value(self.control_variable, self.cv_data_type)


class SGasCalibrationObject(CIPObject):
    """Holds calibration parameters for one gas type of an associated S-Analog
    Sensor object (selected via that object's ``calibration_object_instance``
    attribute) (See CIP Vol 1, §5-39).

    Instances typically add manufacturer specific calibration parameters
    at attribute IDs > 100.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.S_GAS_CALIBRATION

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attribute_list: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attributes supported by this object instance (attribute 2)."""

    gas_standard_number: CIPAttribute[int] = CIPAttribute(3, uint16)
    """SEMI E52 Gas Type Number; 0 = no gas type specified [default]
    (attribute 3, required)."""

    valid_sensor_instance: CIPAttribute[int] = CIPAttribute(4, uint16)
    """S-Analog Sensor object instance ID this instance is valid for; 0 = none
    [default] (attribute 4, required)."""

    gas_symbol: CIPAttribute[str] = CIPAttribute(5, CIP_SHORT_STRING)
    """Gas type name, e.g. ``"N2"`` (attribute 5)."""

    full_scale: CIPAttribute[FullScale] = CIPAttribute(6, FullScale)
    """Full Scale of the device using this instance, default (0, 0) (attribute
    6)."""

    additional_scaler: CIPAttribute[float] = CIPAttribute(7, float32)
    """Extra correction factor multiplied to the reading, e.g. to reuse this
    calibration for a different gas; default 1.0 (attribute 7)."""

    calibration_date: CIPAttribute[int] = CIPAttribute(8, uint16)
    """DATE this instance was last calibrated, default 0 (attribute 8)."""

    calibration_gas_number: CIPAttribute[int] = CIPAttribute(9, uint16)
    """Gas number used to calibrate this instance, default 0 (attribute 9)."""

    gas_correction_factor: CIPAttribute[float] = CIPAttribute(10, float32)
    """Simple correction factor alternative to a full algorithm, default 1.0
    (attribute 10)."""

    subclass: CIPAttribute[int] = CIPAttribute(99, uint16)
    """0=No subclass, 1=Standard T & P (attribute 99)."""

    def get_all_instances(self) -> Collection[GasCalibrationEntry]:
        """Invoke the class-level Get_All_Instances (0x4B): lists every
        instance with its Gas Standard Number and valid sensor instance (See
        §5-39.5)."""
        response = self.message(0x4B, instance=0)
        return unpack(GasCalibrationEntry[uint16::], response, order=LittleEndian)


class TripPointObject(CIPObject):
    """Compares a Source input value to High/Low trip points and drives a
    Destination output accordingly, e.g. to model a discrete alarm output
    derived from an analog input (See CIP Vol 1, §5-40).

    ``high_trip_point``/``low_trip_point``/``hysteresis``/``input`` are all
    "INT or based on Data Type attribute" and are exposed as raw bytes;
    ``input`` gets :meth:`read_input`/:meth:`write_input` decode helpers
    since it is this object's primary measured value. ``source``/
    ``destination`` are bare (whole-payload) Packed EPATHs identifying the
    attributes that feed Input and receive Output, respectively.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.TRIP_POINT

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attribute_list: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attributes supported by this object instance (attribute 2)."""

    high_trip_point: CIPAttribute[bytes] = CIPAttribute(3)
    """Value at or above which a trip condition occurs; at least one of
    high_trip_point/low_trip_point is required, default 0 (attribute 3)."""

    high_trip_enable: CIPAttribute[int] = CIPAttribute(4, uint8)
    """Enables the High Trip Point setting, default enabled (attribute 4)."""

    low_trip_point: CIPAttribute[bytes] = CIPAttribute(5)
    """Value at or below which a trip condition occurs; at least one of
    high_trip_point/low_trip_point is required, default 0 (attribute 5)."""

    low_trip_enable: CIPAttribute[int] = CIPAttribute(6, uint8)
    """Enables the Low Trip Point setting, default enabled (attribute 6)."""

    status: CIPAttribute[int] = CIPAttribute(7, uint8)
    """0=trip condition unasserted, 1=asserted (attribute 7, required)."""

    polarity: CIPAttribute[int] = CIPAttribute(8, uint8)
    """0=Normal (Output = Status), 1=Reverse (Output = Status inverted)
    (attribute 8)."""

    override: CIPAttribute[int] = CIPAttribute(9, uint8)
    """0=Normal, 1=Force FALSE, 2=Force TRUE, 3=Freeze Status and Output; may
    also be set internally by the device (attribute 9)."""

    hysteresis: CIPAttribute[bytes] = CIPAttribute(10)
    """Recovery margin the Input must cross to clear a trip condition, same
    data type as the trip points, default 0 (attribute 10)."""

    delay: CIPAttribute[int] = CIPAttribute(11, uint16)
    """Milliseconds a trip condition must exist before being reported in
    Status, default 0 (attribute 11)."""

    destination: CIPAttribute[EPATH] = CIPAttribute(12, CIP_EPATH)
    """Path of the destination attribute that Output is written to (attribute
    12, required)."""

    output: CIPAttribute[int] = CIPAttribute(13, uint8)
    """Status as a function of Polarity (attribute 13, required)."""

    source: CIPAttribute[EPATH] = CIPAttribute(14, CIP_EPATH)
    """Path of the source attribute that Input is read from (attribute 14,
    required)."""

    input: CIPAttribute[bytes] = CIPAttribute(15)
    """Value retrieved from Source and compared to the trip points (attribute
    15, required)."""

    data_units: CIPAttribute[bytes] = CIPAttribute(16)
    """ENGUNITS context of Input/trip points/Hysteresis, mirrors the source
    attribute's units (attribute 16)."""

    data_type: CIPAttribute[int] = CIPAttribute(17, uint8)
    """Appendix C-6.1 code for Input/trip points/Hysteresis; default = INT
    (attribute 17)."""

    subclass: CIPAttribute[int] = CIPAttribute(99, uint16)
    """0=No subclass (attribute 99)."""

    def read_input(self) -> int | float | bytes:
        """Read and decode ``input`` according to the current ``data_type``."""
        return decode_elementary_value(self.input, self.data_type)

    def write_input(self, value: int | float | bytes) -> bytes:
        """Encode and write ``input`` according to the current
        ``data_type``."""
        return self.set_empty(15, encode_elementary_value(value, self.data_type))


class SPartialPressureObject(CIPObject):
    """Scans the partial pressure of one configured AMU, AMU range or gas
    species, e.g. for a mass spectrometer (See CIP Vol 1, §5-43).

    Class attributes 32-39 (Filament Control/Status, Reading Invalid,
    Emission Current, Multiplier On/Voltage, Samples, Scan Count) are only
    available via :meth:`get_class_attribute`/:meth:`set_class_attribute`,
    per this library's convention of never declaring typed descriptors for
    class-level attributes.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.S_PARTIAL_PRESSURE

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported by this object instance (attribute 1)."""

    attribute_list: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attributes supported by this object instance (attribute 2)."""

    instance_type: CIPAttribute[int] = CIPAttribute(3, uint8)
    """0=AMU [default], 1=AMU Range, 2=Gas Species, 51-99=Device Specific,
    100-255=Vendor Specific (attribute 3, required)."""

    amu: CIPAttribute[float] = CIPAttribute(4, float32)
    """Atomic Mass Unit, or Starting AMU for an AMU Range instance, default 0
    (attribute 4)."""

    ending_amu: CIPAttribute[float] = CIPAttribute(5, float32)
    """Ending AMU for an AMU Range type instance (attribute 5)."""

    gas_standard_number: CIPAttribute[int] = CIPAttribute(6, uint16)
    """SEMI E52 Gas Species Type Number; 0 = none specified [default]
    (attribute 6)."""

    status: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Alarm and Warning state of this object instance (attribute 7,
    required)."""

    alarm_high_enable: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Enables setting the Alarm High status bit, default disabled (attribute
    8)."""

    alarm_low_enable: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Enables setting the Alarm Low status bit, default disabled (attribute
    9)."""

    warning_high_enable: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Enables setting the Warning High status bit, default disabled (attribute
    10)."""

    warning_low_enable: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Enables setting the Warning Low status bit, default disabled (attribute
    11)."""

    instance_enable: CIPAttribute[int] = CIPAttribute(12, uint8)
    """0=disable [default], 1=normal scan rate, 2=double scan rate,
    51-99=Device Specific, 100-255=Vendor Specific (attribute 12, required)."""

    partial_pressure: CIPAttribute[float] = CIPAttribute(13, float32)
    """The measured partial pressure of the specified AMU, in
    ``pressure_units`` (attribute 13, required)."""

    pressure_units: CIPAttribute[bytes] = CIPAttribute(14)
    """ENGUNITS context of partial_pressure; default = Torr (attribute 14,
    See Appendix D)."""

    dwell_time: CIPAttribute[int] = CIPAttribute(15, uint16)
    """Milliseconds of acquisition time for this AMU; 0 = fastest possible
    [default] (attribute 15)."""

    electron_energy: CIPAttribute[float] = CIPAttribute(16, float32)
    """Electron Impact Ionization Voltage in eV, default factory configured
    (attribute 16)."""

    report_threshold: CIPAttribute[float] = CIPAttribute(17, float32)
    """Level above which partial_pressure is reported by Get_Pressures, default
    0 (attribute 17)."""

    alarm_trip_point_high: CIPAttribute[float] = CIPAttribute(18, float32)
    """Value above which an Alarm occurs, default = max for its data type
    (attribute 18)."""

    alarm_trip_point_low: CIPAttribute[float] = CIPAttribute(19, float32)
    """Value below which an Alarm occurs, default = min for its data type
    (attribute 19)."""

    alarm_hysteresis: CIPAttribute[float] = CIPAttribute(20, float32)
    """Recovery margin to clear an Alarm condition, default 0 (attribute
    20)."""

    warning_trip_point_high: CIPAttribute[float] = CIPAttribute(21, float32)
    """Value above which a Warning occurs, default = max for its data type
    (attribute 21)."""

    warning_trip_point_low: CIPAttribute[float] = CIPAttribute(22, float32)
    """Value below which a Warning occurs, default = min for its data type
    (attribute 22)."""

    warning_hysteresis: CIPAttribute[float] = CIPAttribute(23, float32)
    """Recovery margin to clear a Warning condition, default 0 (attribute
    23)."""

    group_id: CIPAttribute[int] = CIPAttribute(24, uint8)
    """Group (0-255) this instance belongs to, for Group_Enable (attribute
    24)."""

    subclass: CIPAttribute[int] = CIPAttribute(99, uint16)
    """0=No Subclass (attribute 99)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an S-Partial Pressure class attribute from instance 0, e.g.
        Filament Status (33) or Reading Invalid (34) (See §5-43.1)."""
        return self.get_attr(attribute, instance=0)

    def set_class_attribute(self, attribute: int, value: bytes) -> bytes:
        """Write an S-Partial Pressure class attribute at instance 0, e.g.
        Filament Control (32) (See §5-43.1)."""
        return self.set_empty(attribute, value, instance=0)

    def create(self) -> bytes:
        """Invoke Create at the class level, allocating a new S-Partial
        Pressure instance (See §5-43.3)."""
        return self.message(CommonService.CREATE, instance=0)

    def delete_all(self) -> bytes:
        """Invoke Delete at the class level, removing every instance (See
        §5-43.3)."""
        return self._expect_empty(self.message(CommonService.DELETE, instance=0))

    def delete(self) -> bytes:
        """Invoke Delete on this instance (See §5-43.3)."""
        return self._expect_empty(self.message(CommonService.DELETE))

    def create_range(
        self,
        start_amu: float,
        end_amu: float,
        num_instances: int,
        starting_id: int = 0,
        group_id: int = 0,
    ) -> CreateRangeResult:
        """Invoke the class-level Create_Range (0x4B): creates
        ``num_instances`` evenly spaced instances covering ``start_amu``
        to ``end_amu``. ``starting_id`` = 0 uses the first available
        contiguous ID range (See §5-43.4.1)."""
        request = pack(
            CreateRangeRequest(start_amu, end_amu, num_instances, starting_id, group_id),
            CreateRangeRequest,
            order=LittleEndian,
        )
        response = self.message(0x4B, request, instance=0)
        return unpack(CreateRangeResult, response, order=LittleEndian)

    def get_instance_list(self) -> Collection[PartialPressureInstanceEntry]:
        """Invoke the class-level Get_Instance_List (0x4C): lists every enabled
        instance with its AMU configuration (See §5-43.4.2)."""
        response = self.message(0x4C, instance=0)
        return unpack(
            PartialPressureInstanceEntry[uint16::], response, order=LittleEndian
        )

    def get_pressures(self) -> Collection[PartialPressureReading]:
        """Invoke the class-level Get_Pressures (0x4D): lists every enabled
        Partial Pressure above its report_threshold (See §5-43.4.3)."""
        response = self.message(0x4D, instance=0)
        return unpack(PartialPressureReading[uint16::], response, order=LittleEndian)

    def get_all_pressures(self) -> Collection[PartialPressureReading]:
        """Invoke the class-level Get_All_Pressures (0x4E): lists every enabled
        Partial Pressure, irrespective of report_threshold (See §5-43.4.4)."""
        response = self.message(0x4E, instance=0)
        return unpack(PartialPressureReading[uint16::], response, order=LittleEndian)

    def group_enable(self, enable: bool, group_id: int) -> bytes:
        """Invoke the class-level Group_Enable (0x4F): enables/disables every
        instance whose ``group_id`` attribute matches (See §5-43.4.5)."""
        request = pack(
            GroupEnableRequest(1 if enable else 0, group_id),
            GroupEnableRequest,
            order=LittleEndian,
        )
        return self._expect_empty(self.message(0x4F, request, instance=0))


class SSensorCalibrationObject(CIPObject):
    """Holds calibration parameters for one application of an associated
    S-Analog Sensor object (selected via that object's
    ``calibration_object_instance`` attribute) (See CIP Vol 1, §5-44).

    Attributes 16-31 are reserved for manufacturer defined calibration
    coefficients and are not modeled individually; use :meth:`get`/
    :meth:`set` with the desired attribute ID if a device implements
    them.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.S_SENSOR_CALIBRATION

    number_of_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attribute_list: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attributes supported by this object instance (attribute 2)."""

    calibration_id_number: CIPAttribute[int] = CIPAttribute(3, uint16)
    """Identifies the calibration, e.g. fluid type; default 0 (attribute 3,
    required)."""

    valid_sensor_instance: CIPAttribute[int] = CIPAttribute(4, uint16)
    """S-Analog Sensor object instance ID this instance is valid for; 0 = none
    [default] (attribute 4, required)."""

    calibration_name: CIPAttribute[str] = CIPAttribute(5, CIP_SHORT_STRING)
    """Representation of the calibration, e.g. material type, max 50 characters
    (attribute 5)."""

    full_scale: CIPAttribute[FullScale] = CIPAttribute(6, FullScale)
    """Full Scale of the device using this instance, default (0, 0) (attribute
    6)."""

    additional_scaler: CIPAttribute[float] = CIPAttribute(7, float32)
    """Extra correction factor multiplied to the reading, default 1.0
    (attribute 7)."""

    calibration_date: CIPAttribute[int] = CIPAttribute(8, uint16)
    """DATE this instance was last calibrated, default 0 (attribute 8)."""

    temperature_data_units: CIPAttribute[bytes] = CIPAttribute(9)
    """ENGUNITS context of ``temperature`` (attribute 9)."""

    temperature: CIPAttribute[float] = CIPAttribute(10, float32)
    """Temperature this calibration was made for/at (attribute 10)."""

    pressure_data_units: CIPAttribute[bytes] = CIPAttribute(11)
    """ENGUNITS context of ``pressure`` (attribute 11)."""

    pressure: CIPAttribute[float] = CIPAttribute(12, float32)
    """Pressure this calibration was made for/at (attribute 12)."""

    coefficient_a: CIPAttribute[float] = CIPAttribute(13, float32)
    """The "a" term in the quadratic correction y = ax^2 + bx + c (attribute
    13)."""

    coefficient_b: CIPAttribute[float] = CIPAttribute(14, float32)
    """The "b" term in the quadratic correction y = ax^2 + bx + c (attribute
    14)."""

    coefficient_c: CIPAttribute[float] = CIPAttribute(15, float32)
    """The "c" term in the quadratic correction y = ax^2 + bx + c (attribute
    15)."""

    subclass: CIPAttribute[int] = CIPAttribute(99, uint16)
    """0=No subclass (attribute 99)."""

    def get_all_instances(self) -> Collection[SensorCalibrationEntry]:
        """Invoke the class-level Get_All_Instances (0x4B): lists every
        instance with its Calibration ID Number and valid sensor instance (See
        §5-44.7)."""
        response = self.message(0x4B, instance=0)
        return unpack(SensorCalibrationEntry[uint16::], response, order=LittleEndian)
