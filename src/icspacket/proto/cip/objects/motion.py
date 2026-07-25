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
"""[ODVA CIP Vol 1] Wrappers for the CIP Motion Device family:

- Position Sensor (class 0x23, §5-23),
- Position Controller Supervisor (class 0x24, §5-24),
- Position Controller (class 0x25, §5-25),
- Block Sequencer (class 0x26, §5-26),
- Command Block (class 0x27, §5-27), and
- Motion Axis (class 0x42, §5-46).
"""

from collections.abc import Collection
from typing import ClassVar

from caterpillar.fields import int16, int32, int64, uint8, uint16, uint32
from caterpillar.model import StructDefMixin
from caterpillar.py import pack, unpack
from caterpillar.shortcuts import LittleEndian, struct
from caterpillar.types import int64_t, uint8_t

from ..const import ClassCode, CommonService
from ._base import CIPAttribute, CIPObject

__all__ = [
    "BlockSequencerObject",
    "CommandBlockObject",
    "GroupSyncResult",
    "MotionAxisObject",
    "PositionControllerObject",
    "PositionControllerSupervisorObject",
    "PositionSensorObject",
]


class PositionSensorObject(CIPObject):
    """Interface to an absolute position sensor (encoder/resolver), extended
    with zero offset and CAM (virtual limit switch) checking (See CIP Vol 1,
    §5-23).

    One and only one of ``position_value_unsigned``/``position_value_signed``
    is normally implemented (attributes 3/10). The CAM channel arrays
    (attributes 35-40) are each sized by ``num_cam_channels`` (attribute 34)
    and are exposed as raw bytes rather than a fixed schema; use the
    Get_Member/Set_Member services (0x18/0x19) to access individual
    elements.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.POSITION_SENSOR

    num_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attributes: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attribute IDs supported by this instance (attribute 2)."""

    position_value_unsigned: CIPAttribute[int] = CIPAttribute(3, uint32)
    """Current position, conditioned by
    ``value_bit_resolution``/``zero_offset`` (attribute 3)."""

    cam: CIPAttribute[int] = CIPAttribute(4, uint8)
    """Virtual CAM switch value: 0 = Off, 1 = On (attribute 4)."""

    value_bit_resolution: CIPAttribute[int] = CIPAttribute(5, uint8)
    """Position sensor resolution, in significant bits (attribute 5)."""

    zero_offset: CIPAttribute[int] = CIPAttribute(6, uint32)
    """Value added to the raw position to adjust the zero point (attribute
    6)."""

    cam_low_limit: CIPAttribute[int] = CIPAttribute(7, uint32)
    """Virtual CAM switch low limit; default 0 (attribute 7)."""

    cam_high_limit: CIPAttribute[int] = CIPAttribute(8, uint32)
    """Virtual CAM switch high limit; default 0 (attribute 8)."""

    auto_zero: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Rising edge sets ``zero_offset`` to the current position (attribute
    9)."""

    position_value_signed: CIPAttribute[int] = CIPAttribute(10, int32)
    """Current position, unconditioned by resolution/offset (attribute 10)."""

    position_sensor_type: CIPAttribute[int] = CIPAttribute(11, uint16)
    """0=Single-turn resolver, 1=Single-turn absolute encoder, 2=Multi-turn
    absolute encoder, ..., 8=Absolute linear encoder, 9=Absolute linear encoder
    w/ cyclic coding (attribute 11, See Table 5-23.8)."""

    direction_counting_toggle: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Defines the direction of increasing position value; default 0 (attribute
    12, required)."""

    commissioning_diagnostic_control: CIPAttribute[int] = CIPAttribute(13, uint8)
    """0 = OFF, 1 = ON (default); checks the encoder at standstill (attribute 13)."""

    scaling_function_control: CIPAttribute[int] = CIPAttribute(14, uint8)
    """0 = OFF, 1 = ON (default); converts physical_resolution_span (attribute
    42) to a numerical value (attribute 14)."""

    position_format: CIPAttribute[bytes] = CIPAttribute(15)
    """ENGUNIT-coded format of the position value; default is counts (attribute
    15)."""

    measuring_units_per_span: CIPAttribute[int] = CIPAttribute(16, uint32)
    """Distinguishable steps per one complete span; <= physical_resolution_span
    (attribute 16)."""

    total_measuring_range: CIPAttribute[int] = CIPAttribute(17, uint32)
    """Steps over the total measuring range; rotary encoders only (attribute
    17)."""

    position_measuring_increment: CIPAttribute[int] = CIPAttribute(18, uint32)
    """Smallest incremental change of the position value; default 1 (attribute
    18)."""

    preset_value: CIPAttribute[int] = CIPAttribute(19, int32)
    """Output position value is set to this value (attribute 19)."""

    cos_delta: CIPAttribute[int] = CIPAttribute(20, uint32)
    """Value for position change in Change-Of-State mode (attribute 20)."""

    position_state: CIPAttribute[int] = CIPAttribute(21, uint8)
    """Software limit switch state: bit 0 = out of range, bit 1 = range
    overflow, bit 2 = range underflow (attribute 21)."""

    position_low_limit: CIPAttribute[int] = CIPAttribute(22, int32)
    """Low limit position (attribute 22)."""

    position_high_limit: CIPAttribute[int] = CIPAttribute(23, int32)
    """High limit position (attribute 23)."""

    velocity_value: CIPAttribute[int] = CIPAttribute(24, int32)
    """Current speed, in the format defined by ``velocity_format``/
    ``velocity_resolution`` (attribute 24)."""

    velocity_format: CIPAttribute[bytes] = CIPAttribute(25)
    """ENGUINT-coded format of the velocity attributes; default 0x1f04 =
    counts/second (attribute 25)."""

    velocity_resolution: CIPAttribute[int] = CIPAttribute(26, uint32)
    """Smallest incremental change of ``velocity_value``; default 1 (attribute
    26)."""

    minimum_velocity_setpoint: CIPAttribute[int] = CIPAttribute(27, int32)
    """Minimum velocity trigger threshold; default 0x80000000 (attribute
    27)."""

    maximum_velocity_setpoint: CIPAttribute[int] = CIPAttribute(28, int32)
    """Maximum velocity trigger threshold; default 0xEFFFFFFF (attribute
    28)."""

    acceleration_value: CIPAttribute[int] = CIPAttribute(29, int32)
    """Current acceleration (positive) or deceleration (negative) (attribute
    29)."""

    acceleration_format: CIPAttribute[bytes] = CIPAttribute(30)
    """ENGUINT-coded format of the acceleration attributes; default 0x1500 =
    m/s2 (attribute 30)."""

    acceleration_resolution: CIPAttribute[int] = CIPAttribute(31, uint32)
    """Smallest incremental change of ``acceleration_value``; default 1
    (attribute 31)."""

    minimum_acceleration_setpoint: CIPAttribute[int] = CIPAttribute(32, int32)
    """Minimum acceleration trigger threshold; default 0x80000000 (attribute
    32)."""

    maximum_acceleration_setpoint: CIPAttribute[int] = CIPAttribute(33, int32)
    """Maximum acceleration trigger threshold; default 0xEFFFFFFF (attribute
    33)."""

    num_cam_channels: CIPAttribute[int] = CIPAttribute(34, uint8)
    """Number of independent CAM channels (attribute 34)."""

    cam_channel_state: CIPAttribute[bytes] = CIPAttribute(35)
    """Bit array (one bit per CAM channel) of CAM channel state; size defined
    by ``num_cam_channels`` (attribute 35)."""

    cam_channel_polarity: CIPAttribute[bytes] = CIPAttribute(36)
    """Bit array of CAM channel polarity; size defined by ``num_cam_channels``
    (attribute 36)."""

    cam_channel_enable: CIPAttribute[bytes] = CIPAttribute(37)
    """Bit array enabling each CAM channel; size defined by
    ``num_cam_channels`` (attribute 37)."""

    cam_low_limit_array: CIPAttribute[bytes] = CIPAttribute(38)
    """Array of DINT lower switch points, one per CAM channel (attribute
    38)."""

    cam_high_limit_array: CIPAttribute[bytes] = CIPAttribute(39)
    """Array of DINT upper switch points, one per CAM channel (attribute
    39)."""

    cam_hysteresis: CIPAttribute[bytes] = CIPAttribute(40)
    """Array of UINT hysteresis values, one per CAM channel (attribute 40)."""

    operating_status: CIPAttribute[int] = CIPAttribute(41, uint8)
    """Encoder diagnostic operating status (attribute 41)."""

    physical_resolution_span: CIPAttribute[int] = CIPAttribute(42, uint32)
    """Distinguishable steps per one complete span (attribute 42)."""

    num_spans: CIPAttribute[int] = CIPAttribute(43, uint16)
    """Number of turns for a rotary device; default 1 (attribute 43)."""

    alarms: CIPAttribute[int] = CIPAttribute(44, uint16)
    """Malfunction bitmap that could lead to an incorrect position value
    (attribute 44)."""

    supported_alarms: CIPAttribute[int] = CIPAttribute(45, uint16)
    """Bitmap of alarms supported by this instance (attribute 45)."""

    alarm_flag: CIPAttribute[int] = CIPAttribute(46, uint8)
    """0 = OK, 1 = an alarm has occurred (attribute 46)."""

    warnings: CIPAttribute[int] = CIPAttribute(47, uint16)
    """Bitmap of internal parameters exceeded (attribute 47)."""

    supported_warnings: CIPAttribute[int] = CIPAttribute(48, uint16)
    """Bitmap of warnings supported by this instance (attribute 48)."""

    warning_flag: CIPAttribute[int] = CIPAttribute(49, uint8)
    """0 = OK, 1 = a warning has occurred (attribute 49)."""

    operating_time: CIPAttribute[int] = CIPAttribute(50, uint32)
    """Encoder operating time, in tenths of an hour (attribute 50)."""

    offset_value: CIPAttribute[int] = CIPAttribute(51, int32)
    """Offset calculated by the preset function (attribute 51)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Position Sensor class attribute from instance 0 (See
        §5-23.2)."""
        return self.get_attr(attribute, instance=0)

    def reset(self, reset_type: int = 0) -> bytes:
        """Invoke Reset (0x05). ``reset_type``: 0 = emulate cycling power
        (default), 1 = restore out-of-box configuration then cycle power."""

        return self.message(
            CommonService.RESET, pack(reset_type, uint8, order=LittleEndian)
        )

    def apply_attributes(self) -> bytes:
        """Invoke Apply_Attributes (0x0D), activating configuration changes
        made by prior Set_Attribute_Single calls."""
        return self.message(0x0D)

    def restore(self) -> bytes:
        """Invoke Restore, reloading attribute values saved via
        :meth:`save`."""
        return self._expect_empty(self.message(CommonService.RESTORE))

    def save(self) -> bytes:
        """Invoke Save, persisting all attribute values to non-volatile
        storage."""
        return self._expect_empty(self.message(CommonService.SAVE))


class PositionControllerSupervisorObject(CIPObject):
    """Handles Position Controller error/fault management plus Home, Index, and
    Registration inputs (See CIP Vol 1, §5-24).

    Class attributes 32/33 (``Consumed``/``Produced Axis Selection
    Number``) route I/O Command/Response Message data to the axis number
    in range 1-7; read them via :meth:`get_class_attribute`.
    """
    CLASS_CODE: ClassVar[ClassCode] = ClassCode.POSITION_CONTROLLER_SUPERVISOR

    num_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""
    attributes: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attribute IDs supported by this instance (attribute 2)."""
    axis_number: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Axis number, same as the instance number, in range 1-7 (attribute 3)."""
    # Attribute 4 is reserved.

    general_fault: CIPAttribute[int] = CIPAttribute(5, uint8)
    """Logical OR of all fault condition flags; 1 = fault exists (attribute 5)."""

    command_message_type: CIPAttribute[int] = CIPAttribute(6, uint8)
    """I/O command message type sent by the controlling device, 1-0x1F
    (attribute 6)."""
    response_message_type: CIPAttribute[int] = CIPAttribute(7, uint8)
    """I/O response message type returned to the controlling device, 1-0x1F
    (attribute 7)."""
    fault_input: CIPAttribute[int] = CIPAttribute(8, uint8)
    """1 = fault input is active (attribute 8)."""

    fault_input_action: CIPAttribute[int] = CIPAttribute(9, uint8)
    """0=Command Output Generator off, 1=Hard stop, 2=Smooth stop, 3=No action
    (attribute 9)."""
    home_action: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Action taken when the armed home input triggers: 0=Generator off, 1=Hard
    stop, 2=Smooth stop, 3=No action, 4=Gate index (attribute 10)."""
    home_active_level: CIPAttribute[int] = CIPAttribute(11, uint8)
    """0 = active low, 1 = active high (attribute 11)."""

    home_arm: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Write 1 to arm the Home input; reads 0 once the trigger has occurred
    (attribute 12)."""
    index_action: CIPAttribute[int] = CIPAttribute(13, uint8)
    """0=Generator off, 1=Hard stop, 2=Smooth stop, 3=No action (attribute
    13)."""
    index_active_level: CIPAttribute[int] = CIPAttribute(14, uint8)
    """0 = active low, 1 = active high (attribute 14)."""

    index_arm: CIPAttribute[int] = CIPAttribute(15, uint8)
    """Write 1 to arm the Index input; reads 0 once the trigger has occurred
    (attribute 15)."""
    home_input_level: CIPAttribute[int] = CIPAttribute(16, uint8)
    """Actual level of the Home input (attribute 16)."""
    home_position: CIPAttribute[int] = CIPAttribute(17, int32)
    """Position captured when the Home input triggered (attribute 17)."""
    index_position: CIPAttribute[int] = CIPAttribute(18, int32)
    """Position captured when the Index input triggered (attribute 18)."""
    registration_action: CIPAttribute[int] = CIPAttribute(19, uint8)
    """0=Generator off, 1=Hard stop, 2=Smooth stop, 3=No action, 4=Go to Reg
    position offset, 5=Go to Reg position absolute (attribute 19)."""
    registration_active_level: CIPAttribute[int] = CIPAttribute(20, uint8)
    """0 = active low, 1 = active high (attribute 20)."""

    registration_arm: CIPAttribute[int] = CIPAttribute(21, uint8)
    """Write 1 to arm the Registration input; reads 0 once triggered (attribute
    21)."""
    registration_input_level: CIPAttribute[int] = CIPAttribute(22, uint8)
    """Actual level of the Registration input (attribute 22)."""
    registration_offset: CIPAttribute[int] = CIPAttribute(23, int32)
    """Offset/absolute position applied per ``registration_action`` (attribute
    23)."""
    registration_position: CIPAttribute[int] = CIPAttribute(24, int32)
    """Position captured when the Registration input triggered (attribute
    24)."""
    follow_enable: CIPAttribute[int] = CIPAttribute(25, uint8)
    """0 = following disabled, 1 = following enabled (attribute 25)."""

    follow_axis: CIPAttribute[int] = CIPAttribute(26, uint8)
    """0 = no following, 1-255 = axis to follow (attribute 26)."""

    follow_divisor: CIPAttribute[int] = CIPAttribute(27, int32)
    """Divides the Follow Axis position when computing the Command Position
    (attribute 27)."""
    follow_multiplier: CIPAttribute[int] = CIPAttribute(28, int32)
    """Multiplies the Follow Axis position when computing the Command Position
    (attribute 28)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Position Controller Supervisor class attribute from instance
        0 (See §5-24.2)."""
        return self.get_attr(attribute, instance=0)


class PositionControllerObject(CIPObject):
    """Performs profile velocity/position generation and handles motor drive
    unit I/O, limit switches, and registration (See CIP Vol 1, §5-25).

    Attribute 28 is reserved.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.POSITION_CONTROLLER

    num_attributes: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Number of attributes supported (attribute 1)."""

    attributes: CIPAttribute[Collection[int]] = CIPAttribute(2, uint8[...])
    """List of attribute IDs supported by this instance (attribute 2)."""

    mode: CIPAttribute[int] = CIPAttribute(3, uint8)
    """0 = Position mode (default), 1 = Velocity mode, 2 = Torque mode
    (attribute 3)."""

    position_units: CIPAttribute[int] = CIPAttribute(4, int32)
    """Actual position feedback counts equal to one position unit; default 1
    (attribute 4)."""

    profile_units: CIPAttribute[int] = CIPAttribute(5, int32)
    """Actual position feedback counts per second/second^2 equal to one profile
    unit; default 1 (attribute 5)."""

    target_position: CIPAttribute[int] = CIPAttribute(6, int32)
    """Profile move position, in position units (attribute 6, required)."""

    target_velocity: CIPAttribute[int] = CIPAttribute(7, int32)
    """Profile velocity, in profile units/second (attribute 7, required)."""

    acceleration: CIPAttribute[int] = CIPAttribute(8, int32)
    """Profile acceleration rate, in profile units/second^2 (attribute 8,
    required)."""

    deceleration: CIPAttribute[int] = CIPAttribute(9, int32)
    """Profile deceleration rate, in profile units/second^2 (attribute 9)."""

    incremental_position_flag: CIPAttribute[int] = CIPAttribute(10, uint8)
    """0 = ``target_position`` is absolute, 1 = incremental (attribute 10)."""

    load_data_profile_handshake: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Loads command data and starts/tracks a Profile Move (attribute 11,
    required, See §5-25.3.1.1)."""

    on_target_position: CIPAttribute[int] = CIPAttribute(12, uint8)
    """Set when the actual position is within the deadband (attribute 38) of
    the target position (attribute 12)."""

    actual_position: CIPAttribute[int] = CIPAttribute(13, int32)
    """Actual absolute position, in position units; write to redefine it
    (attribute 13)."""

    actual_velocity: CIPAttribute[int] = CIPAttribute(14, int32)
    """Actual velocity, in profile units/second (attribute 14)."""

    commanded_position: CIPAttribute[int] = CIPAttribute(15, int32)
    """Instantaneous calculated position (attribute 15)."""

    commanded_velocity: CIPAttribute[int] = CIPAttribute(16, int32)
    """Instantaneous calculated velocity, in profile units/second (attribute
    16)."""

    enable: CIPAttribute[int] = CIPAttribute(17, uint8)
    """Set to enable drive and feedback, clear to disable (attribute 17)."""

    profile_type: CIPAttribute[int] = CIPAttribute(18, uint8)
    """0 = Trapezoidal, 1 = S-Curve, 2 = Parabolic (attribute 18)."""

    profile_gain: CIPAttribute[int] = CIPAttribute(19, int32)
    """Vendor-specific gain for non-trapezoidal profiles (attribute 19)."""

    smooth_stop: CIPAttribute[int] = CIPAttribute(20, uint8)
    """Set to force deceleration to zero velocity at the programmed decel rate
    (attribute 20)."""

    hard_stop: CIPAttribute[int] = CIPAttribute(21, uint8)
    """Set to force immediate deceleration to zero velocity at max decel rate
    (attribute 21)."""

    jog_velocity: CIPAttribute[int] = CIPAttribute(22, int32)
    """Jogging velocity, in profile units/second (attribute 22)."""

    direction: CIPAttribute[int] = CIPAttribute(23, uint8)
    """Instantaneous direction: 0 = negative/reverse, 1 = positive/forward
    (attribute 23)."""

    reference_direction: CIPAttribute[int] = CIPAttribute(24, uint8)
    """0 = forward is clockwise, 1 = reverse is counter-clockwise (attribute 24)."""

    torque: CIPAttribute[int] = CIPAttribute(25, int32)
    """Output torque; 0 = no torque output (Torque mode only) (attribute 25)."""

    positive_torque_limit: CIPAttribute[int] = CIPAttribute(26, int32)
    """Maximum allowable torque output in the positive direction (attribute
    26)."""

    negative_torque_limit: CIPAttribute[int] = CIPAttribute(27, int32)
    """Maximum allowable torque output in the negative direction (attribute
    27)."""
    # Attribute 28 is reserved.

    wrap_around: CIPAttribute[int] = CIPAttribute(29, uint8)
    """Position wrap-around flag (Velocity mode only); resets when read
    (attribute 29)."""

    kp: CIPAttribute[int] = CIPAttribute(30, int16)
    """Proportional gain, range 0-32767 (attribute 30)."""

    ki: CIPAttribute[int] = CIPAttribute(31, int16)
    """Integral gain, range 0-32767 (attribute 31)."""

    kd: CIPAttribute[int] = CIPAttribute(32, int16)
    """Derivative gain, range 0-32767 (attribute 32)."""

    max_ki: CIPAttribute[int] = CIPAttribute(33, int16)
    """Integration limit, range 0-32767 (attribute 33)."""

    ki_mode: CIPAttribute[int] = CIPAttribute(34, uint8)
    """0 = use Ki term always, 1 = use Ki only when stopped/holding position
    (attribute 34)."""

    velocity_feed_forward: CIPAttribute[int] = CIPAttribute(35, int16)
    """Velocity feed forward gain, range 0-32767 (attribute 35)."""

    accel_feed_forward: CIPAttribute[int] = CIPAttribute(36, int16)
    """Acceleration feed forward gain, range 0-32767 (attribute 36)."""

    sample_rate: CIPAttribute[int] = CIPAttribute(37, int16)
    """Update sample rate, in microseconds (attribute 37)."""

    position_deadband: CIPAttribute[int] = CIPAttribute(38, uint8)
    """Window preventing axis hunting, range 0-255 (attribute 38)."""

    feedback_enable: CIPAttribute[int] = CIPAttribute(39, uint8)
    """Tracks ``enable`` (attribute 17); can be cleared independently for drive
    offset adjustments (attribute 39)."""

    feedback_resolution: CIPAttribute[int] = CIPAttribute(40, int32)
    """Feedback counts per revolution of the position feedback device
    (attribute 40)."""

    motor_resolution: CIPAttribute[int] = CIPAttribute(41, int32)
    """Motor steps per revolution of the motor (attribute 41)."""

    position_tracking_gain: CIPAttribute[int] = CIPAttribute(42, int32)
    """Gain for stepper position maintenance via position feedback (attribute
    42)."""

    max_correction_velocity: CIPAttribute[int] = CIPAttribute(43, uint16)
    """Position maintenance value to prevent stepper stalls, in counts/second
    (attribute 43)."""

    max_static_following_error: CIPAttribute[int] = CIPAttribute(44, int32)
    """Maximum following error allowed while stopped and holding position
    (attribute 44)."""

    max_dynamic_following_error: CIPAttribute[int] = CIPAttribute(45, int32)
    """Maximum following error allowed while in motion (attribute 45)."""

    following_error_action: CIPAttribute[int] = CIPAttribute(46, uint8)
    """0=Generator off, 1=Hard stop, 2=Smooth stop, 3=No action (attribute
    46)."""

    following_error_fault: CIPAttribute[int] = CIPAttribute(47, uint8)
    """Set when a following error occurs (attribute 47)."""

    actual_following_error: CIPAttribute[int] = CIPAttribute(48, int32)
    """Actual following error, in position feedback counts (attribute 48)."""

    hard_limit_action: CIPAttribute[int] = CIPAttribute(49, uint8)
    """0=Generator off, 1=Hard stop, 2=Smooth stop (attribute 49)."""

    forward_limit: CIPAttribute[int] = CIPAttribute(50, uint8)
    """Set when the forward hard limit is active (attribute 50)."""

    reverse_limit: CIPAttribute[int] = CIPAttribute(51, uint8)
    """Set when the reverse hard limit is active (attribute 51)."""

    soft_limit_enable: CIPAttribute[int] = CIPAttribute(52, uint8)
    """When set, motion beyond the soft limits results in a motor stop
    (attribute 52)."""

    soft_limit_action: CIPAttribute[int] = CIPAttribute(53, uint8)
    """0=Generator off, 1=Hard stop, 2=Smooth stop (attribute 53)."""

    positive_soft_limit_position: CIPAttribute[int] = CIPAttribute(54, int32)
    """Soft limit positive boundary, in position units (attribute 54)."""

    negative_soft_limit_position: CIPAttribute[int] = CIPAttribute(55, int32)
    """Soft limit negative boundary, in position units (attribute 55)."""

    positive_limit_triggered: CIPAttribute[int] = CIPAttribute(56, uint8)
    """Set when a positive hard limit stop occurs (attribute 56)."""

    negative_limit_triggered: CIPAttribute[int] = CIPAttribute(57, uint8)
    """Set when a negative hard limit stop occurs (attribute 57)."""

    load_data_complete: CIPAttribute[int] = CIPAttribute(58, uint8)
    """Set once valid I/O command message data has been loaded (attribute 58,
    required, See §5-25.3.1.2)."""

class BlockSequencerObject(CIPObject):
    """Executes a Command Block or chain of linked Command Blocks (See CIP Vol
    1, §5-26)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.BLOCK_SEQUENCER

    block: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Instance number of the starting Command Block, 1-255 (attribute 1,
    required)."""

    block_execute: CIPAttribute[int] = CIPAttribute(2, uint8)
    """Set to execute the block chain starting at ``block``; reads cleared once
    the chain is done (attribute 2, required)."""

    current_block: CIPAttribute[int] = CIPAttribute(3, uint8)
    """Instance number of the currently executing Command Block (attribute 3,
    required)."""

    block_fault: CIPAttribute[int] = CIPAttribute(4, uint8)
    """Set on a Wait Equals time-out or an invalid Command Block; execution
    stops.

    Reset when ``block_fault_code`` is read (attribute 4, required).
    """

    block_fault_code: CIPAttribute[int] = CIPAttribute(5, uint8)
    """0=No fault, 1=Invalid/empty block data, 2=Command time-out (Wait
    Equals), 3=Execution fault (attribute 5)."""

    counter: CIPAttribute[int] = CIPAttribute(6, int32)
    """Positive-only counter usable for sequencing loops (attribute 6)."""

class CommandBlockObject(CIPObject):
    """Defines one command in a Block Sequencer chain (See CIP Vol 1, §5-27).

    Attributes 3-7 change meaning based on ``block_command`` and are
    therefore exposed as raw bytes (their wire type is only determined at
    runtime by that value); decode/encode them per the command tables below
    (See §5-27.3 for the full definitions):

    - 1 Modify Attribute: 3=target_class (USINT), 4=target_instance (USINT),
      5=attribute # (USINT), 6=attribute data (per attribute #).
    - 2 Wait Equals: 3=target_class (USINT), 4=target_instance (USINT),
      5=attribute # (USINT), 6=compare time-out ms (DINT), 7=compare data
      (per attribute #).
    - 3 Conditional Link Greater Than / 4 Conditional Link Less Than:
      3=target_class (USINT), 4=target_instance (USINT), 5=attribute #
      (USINT), 6=compare link # (USINT), 7=compare data (per attribute #).
    - 5 Decrement Counter: no additional attributes.
    - 6 Delay: 3=delay in milliseconds (DINT).
    - 7 Trajectory / 8 Trajectory and Wait: 3=target position (DINT),
      4=target velocity (DINT), 5=incremental flag (BOOL).
    - 9 Velocity Change: 3=target velocity (DINT).
    - 10 Goto Home: 3=home offset (DINT), 4=target velocity (DINT).
    - 11 Goto Index: 3=index offset (DINT), 4=target velocity (DINT).
    - 12 Goto Registration Position: 3=registration offset (DINT), 4=target
      velocity (DINT).
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.COMMAND_BLOCK

    block_command: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Selects the command format used by attributes 3-7, 1-12 (attribute 1,
    required)."""

    block_link: CIPAttribute[int] = CIPAttribute(2, uint8)
    """Instance number of the next Command Block to execute once this one is
    done (attribute 2, required)."""

    data_3: CIPAttribute[bytes] = CIPAttribute(3)
    """Command-dependent parameter (attribute 3, See class docstring)."""

    data_4: CIPAttribute[bytes] = CIPAttribute(4)
    """Command-dependent parameter (attribute 4, See class docstring)."""

    data_5: CIPAttribute[bytes] = CIPAttribute(5)
    """Command-dependent parameter (attribute 5, See class docstring)."""

    data_6: CIPAttribute[bytes] = CIPAttribute(6)
    """Command-dependent parameter (attribute 6, See class docstring)."""

    data_7: CIPAttribute[bytes] = CIPAttribute(7)
    """Command-dependent parameter (attribute 7, See class docstring)."""
@struct(order=LittleEndian)
class GroupSyncResult(StructDefMixin):
    """GroupSync service response payload (attribute-less service; See
    §5-46.28.1, Table 5-46.65)."""

    synchronized: uint8_t
    """``1`` if the drive is presently group synchronized to the IEEE-1588 time
    master, ``0`` otherwise."""

    system_time_offset: int64_t
    """The drive's current System Time Offset, in nanoseconds (CIP Sync
    absolute)."""


class MotionAxisObject(CIPObject):
    """One axis of a CIP Motion drive (See CIP Vol 1, §5-46).

    This object's real-world attribute space spans hundreds of IDs across
    many functional categories (motor nameplate, feedback, event capture,
    command reference generation, position/velocity/acceleration/torque/
    current/frequency control loops, stopping/braking, DC bus, power/thermal
    management, exception/fault/alarm handling, statistics, and more; See
    §5-46.9 through §5-46.26) and its own connection-data-shaped class
    attributes (10/11). Modeling it exhaustively is out of scope here; only
    the small set of attributes required unconditionally for every axis
    instance - regardless of Control Mode/Method - are exposed below.
    Anything else remains reachable via the inherited
    :meth:`~CIPObject.get`/:meth:`~CIPObject.set` with the attribute ID from
    the relevant spec section.

    Class attributes 14-20 (Node Control/Status/Fault/Alarm and Controller
    Update Period/Time Offset/Time Stamp) govern the CIP Sync communications
    node behind this axis and are available via :meth:`get_class_attribute`.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.MOTION_AXIS

    control_mode: CIPAttribute[int] = CIPAttribute(80, uint8)
    """4-bit Motor Control enumeration (bits 0-3; bits 4-7 reserved): 0=No
    Control, 1=Position Control, 2=Velocity Control, 3=Acceleration Control,
    4=Torque Control, 5=Current Control (attribute 80, required for all axes,
    See §5-46.8.2)."""

    control_method: CIPAttribute[int] = CIPAttribute(81, uint8)
    """0=No Control, 1=Frequency Control (open loop V/Hz), 2=PI Vector Control
    (closed loop) (attribute 81, required for all axes, See §5-46.8.3)."""

    feedback_configuration: CIPAttribute[int] = CIPAttribute(82, uint8)
    """4-bit Feedback Selection enumeration (bits 0-3; bits 4-7 reserved):

    0=No Feedback, 1=Master Feedback, 2=Motor Feedback, 3=Load Feedback,
    4=Dual Feedback (attribute 82, required for all axes, See
    §5-46.10.2).
    """

    feedback_master_select: CIPAttribute[int] = CIPAttribute(83, uint8)
    """Logical feedback channel assigned when ``feedback_configuration`` is
    Master Feedback: 1=Feedback 1, 2=Feedback 2, ... (attribute 83, required
    for all axes)."""

    status_data_set: CIPAttribute[int] = CIPAttribute(94, uint8)
    """Bitmap selecting which status attributes are produced to the controller
    over the Device-to-Controller Connection (attribute 94, required for all
    axes, See §5-46.17.4)."""

    axis_state: CIPAttribute[int] = CIPAttribute(650, uint8)
    """0=Initializing, 1=Pre-Charge, 2=Stopped, 3=Starting, 4=Running,
    5=Testing, 6=Stopping, 7=Aborting, 8=Major Faulted, 9=Start Inhibited,
    10=Shutdown (attribute 650, required for all axes)."""

    axis_status: CIPAttribute[int] = CIPAttribute(651, uint32)
    """Bitmap of internal axis status conditions, e.g. Local Control, Alarm, DC
    Bus Up, Power Structure Enabled, ...

    (attribute 651, required for all axes, See §5-46.17.2).
    """

    axis_status_mfg: CIPAttribute[int] = CIPAttribute(652, uint32)
    """Vendor-specific axis status bitmap (attribute 652, required for all
    axes)."""

    axis_io_status: CIPAttribute[int] = CIPAttribute(653, uint32)
    """Bitmap of standard digital I/O state, e.g. Enable/Home/Registration/
    Overtravel inputs (attribute 653, required for all axes, See
    §5-46.17.3)."""

    axis_io_status_mfg: CIPAttribute[int] = CIPAttribute(654, uint32)
    """Vendor-specific digital I/O status bitmap (attribute 654, required for
    all axes)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Motion Axis class attribute from instance 0 (See §5-46.5)."""
        return self.get_attr(attribute, instance=0)

    def group_sync(self, system_time_offset: int) -> GroupSyncResult:
        """Invoke GroupSync (0x1C), passing the controller's current System
        Time Offset and checking whether this drive is presently synchronized
        with the controller's Motion Group (See §5-46.28.1)."""
        request = pack(system_time_offset, int64, order=LittleEndian)
        response = self.message(CommonService.GROUP_SYNC, request)
        return unpack(GroupSyncResult, response, order=LittleEndian)
