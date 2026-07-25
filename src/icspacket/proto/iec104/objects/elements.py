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
# pyright: reportGeneralTypeIssues=false, reportUninitializedInstanceVariable=false, reportInvalidTypeForm=false
"""
Information elements: the reusable field-level building blocks that the
per-Type-ID structs in :mod:`icspacket.proto.iec104.objects.information` are
composed from.
"""

import datetime
import enum

from caterpillar.py import (
    LittleEndian,
    StructDefMixin,
    bitfield,
    f,
    struct,
    uint8,
)
from caterpillar.types import (
    float32_t,
    int16_t,
    int32_t,
    uint8_t,
    uint16_t,
    uint32_t,
)

from icspacket.proto.iec104.const import (
    QOC,
    DoublePointValue,
    StepCommandValue,
)

__all__ = [
    "BCR",
    "BSI32",
    "COI",
    "DCO",
    "DIQ",
    "NVA",
    "QCC",
    "QDP",
    "QDS",
    "QOS",
    "QPM",
    "R32",
    "RCO",
    "SCD",
    "SCO",
    "SEP",
    "SIQ",
    "SVA",
    "VTI",
    "CP16Time2a",
    "CP24Time2a",
    "CP56Time2a",
    "OutputCircuitInfo",
    "StartEvent",
]


# --------------------------------------------------------------------------
# Status/quality elements
# --------------------------------------------------------------------------
# /7.2.6.1 Single-point information (SIQ)
@bitfield
class SIQ:
    """
    Single-point Information with quality descriptor (SIQ).
    (See IEC 60870-5-101, clause 7.2.6.1)
    """

    iv: f[bool, 1] = False
    """Invalid: the value is not correctly determined by the source."""

    nt: f[bool, 1] = False
    """Not topical: the most recent update was not received."""

    sb: f[bool, 1] = False
    """Substituted: the value was provided by input of an operator/automatic
    source instead of the process."""

    bl: f[bool, 1] = False
    """Blocked: the value is blocked from transmission/update at the
    source (e.g. maintenance)."""

    reserved: f[int, 3] = 0
    """Reserved, always transmitted as 0."""

    spi: f[bool, 1] = False
    """Single-point information value (the actual on/off state)."""


# /7.2.6.2 Double-point information (DIQ)
@bitfield
class DIQ:
    """
    Double-point Information with quality descriptor (DIQ).
    (See IEC 60870-5-101, clause 7.2.6.2)
    """

    iv: f[bool, 1] = False
    """Invalid."""

    nt: f[bool, 1] = False
    """Not topical."""

    sb: f[bool, 1] = False
    """Substituted."""

    bl: f[bool, 1] = False
    """Blocked."""

    reserved: f[int, 2] = 0
    """Reserved, always transmitted as 0."""

    dpi: f[DoublePointValue | int, 2] = DoublePointValue.INTERMEDIATE
    """Double-point information value, see :class:`~icspacket.proto.iec104.const.DoublePointValue`."""


# /7.2.6.3 Quality descriptor (QDS), standalone
@bitfield
class QDS:
    """
    Quality Descriptor (QDS), used as a standalone element following a bare
    value (e.g. :class:`NVA`, :class:`SVA`, :class:`R32`, :class:`BSI32`).
    (See IEC 60870-5-101, clause 7.2.6.3)
    """

    iv: f[bool, 1] = False
    """Invalid."""

    nt: f[bool, 1] = False
    """Not topical."""

    sb: f[bool, 1] = False
    """Substituted."""

    bl: f[bool, 1] = False
    """Blocked."""

    reserved: f[int, 3] = 0
    """Reserved, always transmitted as 0."""

    ov: f[bool, 1] = False
    """Overflow: the value is beyond its representable range."""


# /7.2.6.4 Quality descriptor for events of protection equipment (QDP)
@bitfield
class QDP:
    """
    Quality Descriptor for events of Protection equipment (QDP), used as a
    standalone element alongside :class:`StartEvent`/:class:`OutputCircuitInfo`.
    (See IEC 60870-5-101, clause 7.2.6.4)
    """

    iv: f[bool, 1] = False
    """Invalid."""

    nt: f[bool, 1] = False
    """Not topical."""

    sb: f[bool, 1] = False
    """Substituted."""

    bl: f[bool, 1] = False
    """Blocked."""

    ei: f[bool, 1] = False
    """Elapsed time invalid."""

    reserved: f[int, 3] = 0
    """Reserved, always transmitted as 0."""


# --------------------------------------------------------------------------
# Value elements
# --------------------------------------------------------------------------
# /7.2.6.5 Value with transient state indication (VTI)
@struct(kw_only=True)
class VTI(StructDefMixin):
    """
    Value with Transient state Indication (VTI) - a transformer/tap-changer
    step position.

    The raw octet packs a signed 7-bit step position with the transient
    flag at bit 7; since :func:`~caterpillar.py.bitfield` sub-byte fields
    only support unsigned values (see :attr:`raw_value`), the signed
    value is exposed via the :attr:`value` property using the same +/-128
    wraparound rule as the reference implementations.
    (See IEC 60870-5-101, clause 7.2.6.5)
    """

    octet: uint8_t = 0
    """Raw octet: bit 7 = transient flag, bits 0-6 = unsigned step position."""

    @property
    def transient(self) -> bool:
        """Whether the addressed device is currently in a transient
        (moving) state."""
        return bool(self.octet & 0x80)

    @transient.setter
    def transient(self, value: bool) -> None:
        self.octet = (self.octet & 0x7F) | (0x80 if value else 0x00)

    @property
    def raw_value(self) -> int:
        """Unsigned 7-bit step position (0-127), as transmitted on the wire."""
        return self.octet & 0x7F

    @property
    def value(self) -> int:
        """Signed step position (-64..63)."""
        raw = self.raw_value
        return raw - 128 if raw > 63 else raw

    @value.setter
    def value(self, value: int) -> None:
        if value < 0:
            value += 128
        self.octet = (self.octet & 0x80) | (value & 0x7F)


#: Bitstring of 32 bit (BSI) - a bare 32-bit bitstring value.
#: (See IEC 60870-5-101, clause 7.2.6.13)
BSI32 = uint32_t

#: Normalized value (NVA) - a bare 16-bit signed fixed-point value spanning
#: the range -1 (0x8000) to 1 - 2^-15 (0x7FFF).
#: (See IEC 60870-5-101, clause 7.2.6.6)
NVA = int16_t

#: Scaled value (SVA) - a bare 16-bit signed integer value.
#: (See IEC 60870-5-101, clause 7.2.6.7)
SVA = int16_t

#: Short floating point number (R32/FLT) - IEEE 754 single-precision.
#: (See IEC 60870-5-101, clause 7.2.6.8)
R32 = float32_t


# /7.2.6.9 Binary counter reading (BCR)
@struct(order=LittleEndian, kw_only=True)
class BCR(StructDefMixin):
    """
    Binary Counter Reading (BCR).

    Unlike :class:`NVA`/:class:`SVA`/:class:`R32`, the standard defines BCR
    as a single fused 5-octet element (counter value plus its own
    sequence/carry/adjusted/invalid flags) rather than a bare value
    expected to be paired with a separate :class:`QDS`.
    (See IEC 60870-5-101, clause 7.2.6.9)
    """

    value: int32_t = 0
    """32-bit signed binary counter value."""

    flags: uint8_t = 0
    """Raw flags octet: bit 7 = invalid, bit 6 = adjusted, bit 5 = carry,
    bits 0-4 = sequence number."""

    @property
    def invalid(self) -> bool:
        """Invalid: the counter value is not valid."""
        return bool(self.flags & 0x80)

    @invalid.setter
    def invalid(self, value: bool) -> None:
        self.flags = (self.flags & 0x7F) | (0x80 if value else 0x00)

    @property
    def adjusted(self) -> bool:
        """Adjusted: the counter value was adjusted (e.g. after a clock sync)."""
        return bool(self.flags & 0x40)

    @adjusted.setter
    def adjusted(self, value: bool) -> None:
        self.flags = (self.flags & 0xBF) | (0x40 if value else 0x00)

    @property
    def carry(self) -> bool:
        """Carry: an overflow occurred since the last freeze/reset."""
        return bool(self.flags & 0x20)

    @carry.setter
    def carry(self, value: bool) -> None:
        self.flags = (self.flags & 0xDF) | (0x20 if value else 0x00)

    @property
    def sequence(self) -> int:
        """Sequence number, incremented on every freeze/reset."""
        return self.flags & 0x1F

    @sequence.setter
    def sequence(self, value: int) -> None:
        self.flags = (self.flags & 0xE0) | (value & 0x1F)


# --------------------------------------------------------------------------
# Command qualifiers
# --------------------------------------------------------------------------
# /7.2.6.15 Single command (SCO)
@bitfield
class SCO:
    """
    Single Command (SCO).
    (See IEC 60870-5-101, clause 7.2.6.15)
    """

    se: f[bool, 1] = False
    """Select/Execute: ``True`` selects the command for later execution
    (see clause 7.2.7 select-before-operate); ``False`` executes directly."""

    qu: f[QOC | int, 5] = QOC.NO_ADDITIONAL_DEFINITION
    """Qualifier of command, see :class:`~icspacket.proto.iec104.const.QOC`."""

    reserved: f[int, 1] = 0
    """Reserved, always transmitted as 0."""

    scs: f[bool, 1] = False
    """Single command state (the commanded on/off value)."""


# /7.2.6.16 Double command (DCO)
@bitfield
class DCO:
    """
    Double Command (DCO).
    (See IEC 60870-5-101, clause 7.2.6.16)
    """

    se: f[bool, 1] = False
    """Select/Execute."""

    qu: f[QOC | int, 5] = QOC.NO_ADDITIONAL_DEFINITION
    """Qualifier of command, see :class:`~icspacket.proto.iec104.const.QOC`."""

    dcs: f[DoublePointValue | int, 2] = DoublePointValue.INTERMEDIATE
    """Double command state, see :class:`~icspacket.proto.iec104.const.DoublePointValue`."""


# /7.2.6.17 Regulating step command (RCO)
@bitfield
class RCO:
    """
    Regulating step Command (RCO).
    (See IEC 60870-5-101, clause 7.2.6.17)
    """

    se: f[bool, 1] = False
    """Select/Execute."""

    qu: f[QOC | int, 5] = QOC.NO_ADDITIONAL_DEFINITION
    """Qualifier of command, see :class:`~icspacket.proto.iec104.const.QOC`."""

    rcs: f[StepCommandValue | int, 2] = StepCommandValue.INVALID_0
    """Regulating step command state, see
    :class:`~icspacket.proto.iec104.const.StepCommandValue`."""


# /7.2.6.39 Qualifier of set-point command (QOS)
@bitfield
class QOS:
    """
    Qualifier Of Set-point command (QOS).

    Accompanies :data:`~icspacket.proto.iec104.const.TypeID.C_SE_NA_1`/
    ``NB_1``/``NC_1`` set-point commands. Unlike :class:`QOC`, the
    qualifier value (``ql``) has no broadly standardized enumeration beyond
    ``0`` (default/no additional definition) - it is left as a plain
    integer rather than an enum.
    (See IEC 60870-5-101, clause 7.2.6.39)
    """

    se: f[bool, 1] = False
    """Select/Execute."""

    ql: f[int, 7] = 0
    """Qualifier value; ``0`` means "default", other values are
    reserved/vendor-specific."""


#: Qualifier Of Counter interrogation Command (QCC) - a bare octet built by
#: OR-ing a :class:`~icspacket.proto.iec104.const.QCC_Freeze` value (already
#: pre-shifted into bits 6-7) with a
#: :class:`~icspacket.proto.iec104.const.QCC_Request` value (bits 0-5), e.g.
#: ``int(QCC_Freeze.FREEZE_WITH_RESET) | int(QCC_Request.GENERAL)``.
#: (See IEC 60870-5-101, clause 7.2.6.23)
QCC = uint8_t


# /7.2.6.24 Qualifier of parameter of measured value (QPM)
@bitfield
class QPM:
    """
    Qualifier of Parameter of Measured value (QPM).
    (See IEC 60870-5-101, clause 7.2.6.24)
    """

    pop: f[bool, 1] = False
    """Parameter Operation: ``True`` means the parameter is currently not
    in operation."""

    lpc: f[bool, 1] = False
    """Local Parameter Change: the parameter was changed locally at the
    outstation since the last transmission."""

    kpa: f[int, 6] = 0
    """Kind of parameter, see
    :class:`~icspacket.proto.iec104.const.QPM_Kind`."""


# --------------------------------------------------------------------------
# System elements
# --------------------------------------------------------------------------
# /7.2.6.21 Cause of initialization (COI)
@bitfield
class COI:
    """
    Cause Of Initialization (COI) - carried by
    :data:`~icspacket.proto.iec104.const.TypeID.M_EI_NA_1` (end of
    initialization).
    (See IEC 60870-5-101, clause 7.2.6.21)
    """

    i: f[bool, 1] = False
    """``True`` if (re)initialization was caused by a local change of
    parameters; ``False`` for a plain (re)start."""

    cause: f[int, 7] = 0
    """The reason for (re)initialization; interpret with
    :class:`~icspacket.proto.iec104.const.COI_Cause`."""


# --------------------------------------------------------------------------
# Packed/protection-equipment elements
# --------------------------------------------------------------------------
# /7.2.6.40 Status and status change detection (SCD)
@struct(order=LittleEndian)
class SCD(StructDefMixin):
    """
    Status and status Change Detection (SCD) - 16 packed single-point
    statuses plus their change-detection flags, used by
    :data:`~icspacket.proto.iec104.const.TypeID.M_PS_NA_1`.
    (See IEC 60870-5-101, clause 7.2.6.40)
    """

    status: uint16_t = 0
    """Bit ``n`` (0-15) is the current status of point ``n`` in the group."""

    changed: uint16_t = 0
    """Bit ``n`` (0-15) is set if point ``n``'s status changed since the
    last transmission."""


class StartEvent(enum.IntFlag):
    """
    Start Event of protection equipment (SPE) bit flags - which phase(s) of
    a protective relay started operating.
    (See IEC 60870-5-101, clause 7.2.6.11)
    """

    __struct__ = uint8

    GS = 0x01
    """General start of operation."""

    SL1 = 0x02
    """Start of operation, phase L1."""

    SL2 = 0x04
    """Start of operation, phase L2."""

    SL3 = 0x08
    """Start of operation, phase L3."""

    SIE = 0x10
    """Start of operation, IE (earth current)."""

    SRD = 0x20
    """Start of operation in reverse direction."""


class OutputCircuitInfo(enum.IntFlag):
    """
    Output Circuit Information (OCI) bit flags - which phase(s) a
    protective relay commanded its output circuit(s) on.
    (See IEC 60870-5-101, clause 7.2.6.12)
    """

    __struct__ = uint8

    GC = 0x01
    """General command to output circuit."""

    CL1 = 0x02
    """Command to output circuit, phase L1."""

    CL2 = 0x04
    """Command to output circuit, phase L2."""

    CL3 = 0x08
    """Command to output circuit, phase L3."""


# /7.2.6.10 Single event of protection equipment (SEP)
@bitfield
class SEP:
    """
    Single Event of Protection equipment (SEP).

    Unlike :class:`StartEvent`/:class:`OutputCircuitInfo` (which are
    transmitted as a bit-flag byte alongside a *separate* :class:`QDP`
    byte), SEP fuses a 2-bit event state with :class:`QDP`'s quality bits
    into one byte - matching the standard's own definition of SEP as a
    single element (mirrors :class:`SIQ`/:class:`DIQ`'s value+quality
    fusion).
    (See IEC 60870-5-101, clause 7.2.6.10)
    """

    iv: f[bool, 1] = False
    """Invalid."""

    nt: f[bool, 1] = False
    """Not topical."""

    sb: f[bool, 1] = False
    """Substituted."""

    bl: f[bool, 1] = False
    """Blocked."""

    ei: f[bool, 1] = False
    """Elapsed time invalid."""

    reserved: f[int, 1] = 0
    """Reserved, always transmitted as 0."""

    es: f[DoublePointValue | int, 2] = DoublePointValue.INTERMEDIATE
    """Event state (reuses :class:`~icspacket.proto.iec104.const.DoublePointValue`'s
    numbering: 0=indeterminate, 1=off, 2=on, 3=indeterminate)."""


# --------------------------------------------------------------------------
# Time tags
# --------------------------------------------------------------------------
# /7.2.6.19 Three-octet binary time (CP24Time2a - "24" refers to the day
# cycle it spans, not its length)
#: Two-octet binary time (CP16Time2a) - a bare elapsed-time value in
#: milliseconds (0-65535), with no validity flag. Used by protection-
#: equipment elapsed-time fields and :data:`~icspacket.proto.iec104.const.TypeID.C_CD_NA_1`.
#: (See IEC 60870-5-101, clause 7.2.6.20)
CP16Time2a = uint16_t


@struct(order=LittleEndian, kw_only=True)
class CP24Time2a(StructDefMixin):
    """
    Three-octet binary time CP24Time2a.
    (See IEC 60870-5-101, clause 7.2.6.19)
    """

    milliseconds: uint16_t = 0
    """Milliseconds within the current minute (0-59999); combines both the
    seconds and millisecond parts, see :attr:`second`/:attr:`millisecond`."""

    octet3: uint8_t = 0
    """Raw octet: bit 7 = invalid, bit 6 = substituted, bits 0-5 = minute."""

    @property
    def second(self) -> int:
        """The whole-seconds part of :attr:`milliseconds`."""
        return self.milliseconds // 1000

    @property
    def millisecond(self) -> int:
        """The sub-second remainder part of :attr:`milliseconds`."""
        return self.milliseconds % 1000

    @property
    def minute(self) -> int:
        """Minute within the hour (0-59)."""
        return self.octet3 & 0x3F

    @minute.setter
    def minute(self, value: int) -> None:
        self.octet3 = (self.octet3 & 0xC0) | (value & 0x3F)

    @property
    def substituted(self) -> bool:
        """The value was provided by input of an operator/automatic source."""
        return bool(self.octet3 & 0x40)

    @substituted.setter
    def substituted(self, value: bool) -> None:
        self.octet3 = (self.octet3 & 0xBF) | (0x40 if value else 0x00)

    @property
    def invalid(self) -> bool:
        """Invalid: the value is not correctly determined by the source."""
        return bool(self.octet3 & 0x80)

    @invalid.setter
    def invalid(self, value: bool) -> None:
        self.octet3 = (self.octet3 & 0x7F) | (0x80 if value else 0x00)


# /7.2.6.18 Seven-octet binary time (CP56Time2a)
@struct(order=LittleEndian, kw_only=True)
class CP56Time2a(StructDefMixin):
    """
    Seven-octet binary time CP56Time2a - the 104-preferred, fully-qualified
    time tag (date plus time-of-day).
    (See IEC 60870-5-101, clause 7.2.6.18)
    """

    milliseconds: uint16_t = 0
    """Milliseconds within the current minute (0-59999); combines both the
    seconds and millisecond parts, see :attr:`second`/:attr:`millisecond`."""

    octet3: uint8_t = 0
    """Raw octet: bit 7 = invalid, bit 6 = substituted, bits 0-5 = minute."""

    octet4: uint8_t = 0
    """Raw octet: bit 7 = summer time, bits 5-6 = reserved, bits 0-4 = hour."""

    octet5: uint8_t = 1
    """Raw octet: bits 5-7 = day of week, bits 0-4 = day of month."""

    octet6: uint8_t = 1
    """Raw octet: bits 4-7 = reserved, bits 0-3 = month."""

    octet7: uint8_t = 0
    """Raw octet: bit 7 = reserved, bits 0-6 = year."""

    @property
    def second(self) -> int:
        """The whole-seconds part of :attr:`milliseconds`."""
        return self.milliseconds // 1000

    @property
    def millisecond(self) -> int:
        """The sub-second remainder part of :attr:`milliseconds`."""
        return self.milliseconds % 1000

    @property
    def minute(self) -> int:
        """Minute within the hour (0-59)."""
        return self.octet3 & 0x3F

    @minute.setter
    def minute(self, value: int) -> None:
        self.octet3 = (self.octet3 & 0xC0) | (value & 0x3F)

    @property
    def substituted(self) -> bool:
        """The value was provided by input of an operator/automatic source."""
        return bool(self.octet3 & 0x40)

    @substituted.setter
    def substituted(self, value: bool) -> None:
        self.octet3 = (self.octet3 & 0xBF) | (0x40 if value else 0x00)

    @property
    def invalid(self) -> bool:
        """Invalid: the value is not correctly determined by the source."""
        return bool(self.octet3 & 0x80)

    @invalid.setter
    def invalid(self, value: bool) -> None:
        self.octet3 = (self.octet3 & 0x7F) | (0x80 if value else 0x00)

    @property
    def hour(self) -> int:
        """Hour within the day (0-23)."""
        return self.octet4 & 0x1F

    @hour.setter
    def hour(self, value: int) -> None:
        self.octet4 = (self.octet4 & 0xE0) | (value & 0x1F)

    @property
    def summer_time(self) -> bool:
        """Daylight saving/summer time is in effect."""
        return bool(self.octet4 & 0x80)

    @summer_time.setter
    def summer_time(self, value: bool) -> None:
        self.octet4 = (self.octet4 & 0x7F) | (0x80 if value else 0x00)

    @property
    def day_of_month(self) -> int:
        """Day of the month (1-31)."""
        return self.octet5 & 0x1F

    @day_of_month.setter
    def day_of_month(self, value: int) -> None:
        self.octet5 = (self.octet5 & 0xE0) | (value & 0x1F)

    @property
    def day_of_week(self) -> int:
        """ISO-8601 day of the week (1=Monday..7=Sunday); ``0`` if unused."""
        return (self.octet5 & 0xE0) >> 5

    @day_of_week.setter
    def day_of_week(self, value: int) -> None:
        self.octet5 = (self.octet5 & 0x1F) | ((value & 0x07) << 5)

    @property
    def month(self) -> int:
        """Month within the year (1-12)."""
        return self.octet6 & 0x0F

    @month.setter
    def month(self, value: int) -> None:
        self.octet6 = (self.octet6 & 0xF0) | (value & 0x0F)

    @property
    def year(self) -> int:
        """Year within the century (0-99), relative to a locally-configured
        reference century."""
        return self.octet7 & 0x7F

    @year.setter
    def year(self, value: int) -> None:
        self.octet7 = (self.octet7 & 0x80) | (value % 100 & 0x7F)

    @classmethod
    def from_datetime(cls, dt: datetime.datetime) -> "CP56Time2a":
        """
        Build a :class:`CP56Time2a` from a :class:`datetime.datetime`.

        :param dt: The timestamp to encode; only ``second``/``microsecond``
            through ``year`` are used (:attr:`invalid`/:attr:`substituted`/
            :attr:`summer_time` all default to ``False``).
        :type dt: datetime.datetime
        :return: The encoded timestamp.
        """
        ts = cls(milliseconds=dt.second * 1000 + dt.microsecond // 1000)
        ts.minute = dt.minute
        ts.hour = dt.hour
        ts.day_of_month = dt.day
        ts.day_of_week = dt.isoweekday()
        ts.month = dt.month
        ts.year = dt.year % 100
        return ts

    def to_datetime(self, *, century: int = 2000) -> datetime.datetime:
        """
        Convert to a :class:`datetime.datetime`.

        :param century: Added to :attr:`year` since the wire format only
            carries a 2-digit year; defaults to the 2000s (valid until 2099).
        :type century: int
        :return: The decoded timestamp.
        """
        return datetime.datetime(
            year=century + self.year,
            month=self.month or 1,
            day=self.day_of_month or 1,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.millisecond * 1000,
        )
