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
# pyright: reportUnannotatedClassAttribute=false
"""
Per-Type-ID information-object structs.

Each class here models the information-object payload of exactly one ASDU
Type-ID (see :class:`icspacket.proto.iec104.const.TypeID`), composed from
the reusable primitives in :mod:`icspacket.proto.iec104.objects.elements`.
Every class self-registers with
:func:`icspacket.proto.iec104.objects.coding.asdu_type` at import time.

Field order matches wire order: a value/status element first, its
:class:`~icspacket.proto.iec104.objects.elements.QDS` quality descriptor
(when the standard keeps it separate) second, and a time tag
(:class:`~icspacket.proto.iec104.objects.elements.CP56Time2a` or
:class:`~icspacket.proto.iec104.objects.elements.CP16Time2a`) last.

Not implemented yet:
file-transfer types (``F_*``, 120-126), the ``S_*`` security-extension
types, and legacy CP24Time2a-tagged monitor types (``M_*_TA_1``, the
101-only time form superseded by CP56Time2a in 104 deployments).
"""
from dataclasses import field

from caterpillar.py import LittleEndian, StructDefMixin, struct
from caterpillar.types import uint16_t

from icspacket.proto.iec104.const import QOI, QPA, QRP, TypeID
from icspacket.proto.iec104.objects.coding import asdu_type
from icspacket.proto.iec104.objects.elements import (
    BCR,
    BSI32,
    COI,
    DCO,
    DIQ,
    NVA,
    QCC,
    QDP,
    QDS,
    QOS,
    QPM,
    R32,
    RCO,
    SCD,
    SCO,
    SEP,
    SIQ,
    SVA,
    VTI,
    CP16Time2a,
    CP56Time2a,
    OutputCircuitInfo,
    StartEvent,
)

__all__ = [
    "Bitstring32",
    "Bitstring32Command",
    "Bitstring32CommandWithCP56Time2a",
    "Bitstring32WithCP56Time2a",
    "ClockSynchronizationCommand",
    "CounterInterrogationCommand",
    "DelayAcquisitionCommand",
    "DoubleCommand",
    "DoubleCommandWithCP56Time2a",
    "DoublePointInformation",
    "DoublePointWithCP56Time2a",
    "EndOfInitialization",
    "EventOfProtectionEquipment",
    "IntegratedTotals",
    "IntegratedTotalsWithCP56Time2a",
    "InterrogationCommand",
    "MeasuredValueNormalized",
    "MeasuredValueNormalizedNoQuality",
    "MeasuredValueNormalizedWithCP56Time2a",
    "MeasuredValueScaled",
    "MeasuredValueScaledWithCP56Time2a",
    "MeasuredValueShort",
    "MeasuredValueShortWithCP56Time2a",
    "PackedOutputCircuitInfo",
    "PackedSinglePointWithSCD",
    "PackedStartEventsOfProtectionEquipment",
    "ParameterActivation",
    "ParameterNormalizedValue",
    "ParameterScaledValue",
    "ParameterShortValue",
    "ReadCommand",
    "ResetProcessCommand",
    "SetpointCommandNormalized",
    "SetpointCommandNormalizedWithCP56Time2a",
    "SetpointCommandScaled",
    "SetpointCommandScaledWithCP56Time2a",
    "SetpointCommandShort",
    "SetpointCommandShortWithCP56Time2a",
    "SingleCommand",
    "SingleCommandWithCP56Time2a",
    "SinglePointInformation",
    "SinglePointWithCP56Time2a",
    "StepCommand",
    "StepCommandWithCP56Time2a",
    "StepPositionInformation",
    "StepPositionWithCP56Time2a",
    "TestCommand",
    "TestCommandWithCP56Time2a",
]


# ============================================================================ #
# Phase A - monitor direction, without time tag
# ============================================================================ #
@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SinglePointInformation(StructDefMixin):
    """Single-point information."""

    TYPE_ID = TypeID.M_SP_NA_1

    status: SIQ = field(default_factory=SIQ)
    """See :class:`~icspacket.proto.iec104.objects.elements.SIQ`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class DoublePointInformation(StructDefMixin):
    """Double-point information."""

    TYPE_ID = TypeID.M_DP_NA_1

    status: DIQ = field(default_factory=DIQ)
    """See :class:`~icspacket.proto.iec104.objects.elements.DIQ`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class StepPositionInformation(StructDefMixin):
    """Step position information (transformer/tap-changer position)."""

    TYPE_ID = TypeID.M_ST_NA_1

    value: VTI = field(default_factory=VTI)
    """See :class:`~icspacket.proto.iec104.objects.elements.VTI`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class Bitstring32(StructDefMixin):
    """Bitstring of 32 bit."""

    TYPE_ID = TypeID.M_BO_NA_1

    value: BSI32 = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.BSI32`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class MeasuredValueNormalized(StructDefMixin):
    """Measured value, normalized value."""

    TYPE_ID = TypeID.M_ME_NA_1

    value: NVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.NVA`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class MeasuredValueScaled(StructDefMixin):
    """Measured value, scaled value."""

    TYPE_ID = TypeID.M_ME_NB_1

    value: SVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.SVA`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class MeasuredValueShort(StructDefMixin):
    """Measured value, short floating point number."""

    TYPE_ID = TypeID.M_ME_NC_1

    value: R32 = 0.0
    """See :class:`~icspacket.proto.iec104.objects.elements.R32`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class IntegratedTotals(StructDefMixin):
    """Integrated totals."""

    TYPE_ID = TypeID.M_IT_NA_1

    value: BCR = field(default_factory=BCR)
    """See :class:`~icspacket.proto.iec104.objects.elements.BCR`. Unlike the
    other Phase A monitor types, BCR already carries its own flags, so no
    separate :class:`QDS` follows it on the wire."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class PackedSinglePointWithSCD(StructDefMixin):
    """Packed single-point information with status change detection."""

    TYPE_ID = TypeID.M_PS_NA_1

    status: SCD = field(default_factory=SCD)
    """See :class:`~icspacket.proto.iec104.objects.elements.SCD`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class MeasuredValueNormalizedNoQuality(StructDefMixin):
    """Measured value, normalized value without quality descriptor."""

    TYPE_ID = TypeID.M_ME_ND_1

    value: NVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.NVA`. Bare - no
    :class:`QDS` follows (the ``_ND_1`` variant exists specifically to save
    bandwidth by omitting it)."""


# ============================================================================ #
# Phase B - monitor direction, with CP56Time2a tag (104-preferred)
# ============================================================================ #
@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SinglePointWithCP56Time2a(StructDefMixin):
    """Single-point information with CP56Time2a time tag."""

    TYPE_ID = TypeID.M_SP_TB_1

    status: SIQ = field(default_factory=SIQ)
    """See :class:`~icspacket.proto.iec104.objects.elements.SIQ`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class DoublePointWithCP56Time2a(StructDefMixin):
    """Double-point information with CP56Time2a time tag."""

    TYPE_ID = TypeID.M_DP_TB_1

    status: DIQ = field(default_factory=DIQ)
    """See :class:`~icspacket.proto.iec104.objects.elements.DIQ`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class StepPositionWithCP56Time2a(StructDefMixin):
    """Step position information with CP56Time2a time tag."""

    TYPE_ID = TypeID.M_ST_TB_1

    value: VTI = field(default_factory=VTI)
    """See :class:`~icspacket.proto.iec104.objects.elements.VTI`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class Bitstring32WithCP56Time2a(StructDefMixin):
    """Bitstring of 32 bit with CP56Time2a time tag."""

    TYPE_ID = TypeID.M_BO_TB_1

    value: BSI32 = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.BSI32`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class MeasuredValueNormalizedWithCP56Time2a(StructDefMixin):
    """Measured value, normalized value with CP56Time2a time tag."""

    TYPE_ID = TypeID.M_ME_TD_1

    value: NVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.NVA`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class MeasuredValueScaledWithCP56Time2a(StructDefMixin):
    """Measured value, scaled value with CP56Time2a time tag."""

    TYPE_ID = TypeID.M_ME_TE_1

    value: SVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.SVA`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class MeasuredValueShortWithCP56Time2a(StructDefMixin):
    """Measured value, short floating point number with CP56Time2a time
    tag."""

    TYPE_ID = TypeID.M_ME_TF_1

    value: R32 = 0.0
    """See :class:`~icspacket.proto.iec104.objects.elements.R32`."""

    quality: QDS = field(default_factory=QDS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDS`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class IntegratedTotalsWithCP56Time2a(StructDefMixin):
    """Integrated totals with CP56Time2a time tag."""

    TYPE_ID = TypeID.M_IT_TB_1

    value: BCR = field(default_factory=BCR)
    """See :class:`~icspacket.proto.iec104.objects.elements.BCR`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class EventOfProtectionEquipment(StructDefMixin):
    """Event of protection equipment with CP56Time2a time tag."""

    TYPE_ID = TypeID.M_EP_TD_1

    status: SEP = field(default_factory=SEP)
    """See :class:`~icspacket.proto.iec104.objects.elements.SEP`."""

    elapsed_time: CP16Time2a = 0
    """Relay operating/elapsed time, see
    :class:`~icspacket.proto.iec104.objects.elements.CP16Time2a`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class PackedStartEventsOfProtectionEquipment(StructDefMixin):
    """Packed start events of protection equipment with CP56Time2a time
    tag."""

    TYPE_ID = TypeID.M_EP_TE_1

    events: StartEvent = StartEvent(0)
    """See :class:`~icspacket.proto.iec104.objects.elements.StartEvent`."""

    quality: QDP = field(default_factory=QDP)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDP`."""

    relay_duration: CP16Time2a = 0
    """Relay duration time, see
    :class:`~icspacket.proto.iec104.objects.elements.CP16Time2a`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class PackedOutputCircuitInfo(StructDefMixin):
    """Packed output circuit information of protection equipment with
    CP56Time2a time tag."""

    TYPE_ID = TypeID.M_EP_TF_1

    info: OutputCircuitInfo = OutputCircuitInfo(0)
    """See
    :class:`~icspacket.proto.iec104.objects.elements.OutputCircuitInfo`."""

    quality: QDP = field(default_factory=QDP)
    """See :class:`~icspacket.proto.iec104.objects.elements.QDP`."""

    operating_time: CP16Time2a = 0
    """Relay operating time, see
    :class:`~icspacket.proto.iec104.objects.elements.CP16Time2a`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


# ============================================================================ #
# Phase C - command direction
# ============================================================================ #
@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SingleCommand(StructDefMixin):
    """Single command."""

    TYPE_ID = TypeID.C_SC_NA_1

    command: SCO = field(default_factory=SCO)
    """See :class:`~icspacket.proto.iec104.objects.elements.SCO`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class DoubleCommand(StructDefMixin):
    """Double command."""

    TYPE_ID = TypeID.C_DC_NA_1

    command: DCO = field(default_factory=DCO)
    """See :class:`~icspacket.proto.iec104.objects.elements.DCO`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class StepCommand(StructDefMixin):
    """Regulating step command."""

    TYPE_ID = TypeID.C_RC_NA_1

    command: RCO = field(default_factory=RCO)
    """See :class:`~icspacket.proto.iec104.objects.elements.RCO`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SetpointCommandNormalized(StructDefMixin):
    """Set-point command, normalized value."""

    TYPE_ID = TypeID.C_SE_NA_1

    value: NVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.NVA`."""

    qualifier: QOS = field(default_factory=QOS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QOS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SetpointCommandScaled(StructDefMixin):
    """Set-point command, scaled value."""

    TYPE_ID = TypeID.C_SE_NB_1

    value: SVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.SVA`."""

    qualifier: QOS = field(default_factory=QOS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QOS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SetpointCommandShort(StructDefMixin):
    """Set-point command, short floating point number."""

    TYPE_ID = TypeID.C_SE_NC_1

    value: R32 = 0.0
    """See :class:`~icspacket.proto.iec104.objects.elements.R32`."""

    qualifier: QOS = field(default_factory=QOS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QOS`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class Bitstring32Command(StructDefMixin):
    """Bitstring of 32 bit command."""

    TYPE_ID = TypeID.C_BO_NA_1

    value: BSI32 = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.BSI32`. Bare -
    unlike :class:`Bitstring32`, no :class:`QDS` follows for this
    Type-ID."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SingleCommandWithCP56Time2a(StructDefMixin):
    """Single command with CP56Time2a time tag."""

    TYPE_ID = TypeID.C_SC_TA_1

    command: SCO = field(default_factory=SCO)
    """See :class:`~icspacket.proto.iec104.objects.elements.SCO`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class DoubleCommandWithCP56Time2a(StructDefMixin):
    """Double command with CP56Time2a time tag."""

    TYPE_ID = TypeID.C_DC_TA_1

    command: DCO = field(default_factory=DCO)
    """See :class:`~icspacket.proto.iec104.objects.elements.DCO`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class StepCommandWithCP56Time2a(StructDefMixin):
    """Regulating step command with CP56Time2a time tag."""

    TYPE_ID = TypeID.C_RC_TA_1

    command: RCO = field(default_factory=RCO)
    """See :class:`~icspacket.proto.iec104.objects.elements.RCO`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SetpointCommandNormalizedWithCP56Time2a(StructDefMixin):
    """Set-point command, normalized value with CP56Time2a time tag."""

    TYPE_ID = TypeID.C_SE_TA_1

    value: NVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.NVA`."""

    qualifier: QOS = field(default_factory=QOS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QOS`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SetpointCommandScaledWithCP56Time2a(StructDefMixin):
    """Set-point command, scaled value with CP56Time2a time tag."""

    TYPE_ID = TypeID.C_SE_TB_1

    value: SVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.SVA`."""

    qualifier: QOS = field(default_factory=QOS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QOS`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class SetpointCommandShortWithCP56Time2a(StructDefMixin):
    """Set-point command, short floating point number with CP56Time2a time
    tag."""

    TYPE_ID = TypeID.C_SE_TC_1

    value: R32 = 0.0
    """See :class:`~icspacket.proto.iec104.objects.elements.R32`."""

    qualifier: QOS = field(default_factory=QOS)
    """See :class:`~icspacket.proto.iec104.objects.elements.QOS`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class Bitstring32CommandWithCP56Time2a(StructDefMixin):
    """Bitstring of 32 bit command with CP56Time2a time tag."""

    TYPE_ID = TypeID.C_BO_TA_1

    value: BSI32 = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.BSI32`. Bare,
    see :class:`Bitstring32Command`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


# ============================================================================ #
# Phase D - system information & parameter commands
# ============================================================================ #
@asdu_type
@struct(order=LittleEndian, kw_only=True)
class EndOfInitialization(StructDefMixin):
    """End of initialization."""

    TYPE_ID = TypeID.M_EI_NA_1

    cause: COI = field(default_factory=COI)
    """See :class:`~icspacket.proto.iec104.objects.elements.COI`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class InterrogationCommand(StructDefMixin):
    """General interrogation command."""

    TYPE_ID = TypeID.C_IC_NA_1

    qualifier: QOI = QOI.STATION
    """Qualifier Of Interrogation, see
    :class:`~icspacket.proto.iec104.const.QOI`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class CounterInterrogationCommand(StructDefMixin):
    """Counter interrogation command."""

    TYPE_ID = TypeID.C_CI_NA_1

    qualifier: QCC = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.QCC`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class ReadCommand(StructDefMixin):
    """
    Read command.

    Carries no element payload at all - only the Information Object
    Address of the point being polled (modeled by the enclosing
    :class:`~icspacket.proto.iec104.objects.coding.InformationObject`, not
    by this class).
    """

    TYPE_ID = TypeID.C_RD_NA_1


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class ClockSynchronizationCommand(StructDefMixin):
    """Clock synchronization command."""

    TYPE_ID = TypeID.C_CS_NA_1

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class TestCommand(StructDefMixin):
    """
    Test command.

    Carries a Fixed test Bit Pattern (FBP) rather than any real value -
    used only to exercise the link without side effects.
    (See IEC 60870-5-101, clause 7.2.6.14)
    """

    TYPE_ID = TypeID.C_TS_NA_1

    fbp: uint16_t = 0x55AA
    """Fixed test bit pattern; conventionally ``0x55AA`` (wire bytes
    ``AA 55``, little-endian) on both activation and confirmation."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class ResetProcessCommand(StructDefMixin):
    """Reset process command."""

    TYPE_ID = TypeID.C_RP_NA_1

    qualifier: QRP = QRP.NOT_USED
    """Qualifier Of Reset Process, see
    :class:`~icspacket.proto.iec104.const.QRP`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class DelayAcquisitionCommand(StructDefMixin):
    """Delay acquisition command."""

    TYPE_ID = TypeID.C_CD_NA_1

    delay: CP16Time2a = 0
    """Transmission delay in milliseconds, see
    :class:`~icspacket.proto.iec104.objects.elements.CP16Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class TestCommandWithCP56Time2a(StructDefMixin):
    """Test command with CP56Time2a time tag."""

    TYPE_ID = TypeID.C_TS_TA_1

    fbp: uint16_t = 0x55AA
    """See :class:`TestCommand`."""

    timestamp: CP56Time2a = field(default_factory=CP56Time2a)
    """See :class:`~icspacket.proto.iec104.objects.elements.CP56Time2a`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class ParameterNormalizedValue(StructDefMixin):
    """Parameter of measured value, normalized value."""

    TYPE_ID = TypeID.P_ME_NA_1

    value: NVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.NVA`."""

    qualifier: QPM = field(default_factory=QPM)
    """See :class:`~icspacket.proto.iec104.objects.elements.QPM`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class ParameterScaledValue(StructDefMixin):
    """Parameter of measured value, scaled value."""

    TYPE_ID = TypeID.P_ME_NB_1

    value: SVA = 0
    """See :class:`~icspacket.proto.iec104.objects.elements.SVA`."""

    qualifier: QPM = field(default_factory=QPM)
    """See :class:`~icspacket.proto.iec104.objects.elements.QPM`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class ParameterShortValue(StructDefMixin):
    """Parameter of measured value, short floating point number."""

    TYPE_ID = TypeID.P_ME_NC_1

    value: R32 = 0.0
    """See :class:`~icspacket.proto.iec104.objects.elements.R32`."""

    qualifier: QPM = field(default_factory=QPM)
    """See :class:`~icspacket.proto.iec104.objects.elements.QPM`."""


@asdu_type
@struct(order=LittleEndian, kw_only=True)
class ParameterActivation(StructDefMixin):
    """Parameter activation."""

    TYPE_ID = TypeID.P_AC_NA_1

    qualifier: QPA = QPA.NOT_USED
    """Qualifier Of Parameter Activation, see
    :class:`~icspacket.proto.iec104.const.QPA`."""


