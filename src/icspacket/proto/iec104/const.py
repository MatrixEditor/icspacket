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
"""
IEC 60870-5-104 constants and enumerations.
"""
import enum

from caterpillar.fields import uint8

# ============================================================================ #
# Network / timing defaults
# ============================================================================ #
#
# Default parameter values as commonly shipped by IEC 60870-5-104 stacks,
# and the IANA-registered well-known port.

IEC104_DEFAULT_PORT = 2404
"""Well-known TCP port IEC 60870-5-104 outstations listen on (IANA-registered
as ``iec-104``)."""

T0_DEFAULT = 30
"""Default timeout *t0* (seconds): time allowed for the TCP connection to be
established."""

T1_DEFAULT = 15
"""Default timeout *t1* (seconds): time allowed for a send or test APDU to be
confirmed."""

T2_DEFAULT = 10
"""Default timeout *t2* (seconds, ``t2 < t1``): time before an S-format
acknowledgment must be sent if no I-format APDU is available to piggy-back
the acknowledgment on."""

T3_DEFAULT = 20
"""Default timeout *t3* (seconds): maximum idle time before a ``TESTFR``
APDU is sent to keep the connection alive."""

K_DEFAULT = 12
"""Default *k*: maximum number of outstanding (unacknowledged) I-format
APDUs the sender may have in flight at once."""

W_DEFAULT = 8
"""Default *w* (``w <= k``): number of received I-format APDUs after which
an S-format acknowledgment must be sent at the latest."""


# ============================================================================ #
# APCI - control field format markers
# ============================================================================ #
#
# (See IEC 60870-5-104, clause 5 - APCI structure)
#
# The two least significant bits of the first control octet select which of
# the three APCI formats the remaining three control octets follow. Bit 0
# alone already distinguishes I-format (0) from S/U-format (1); bit 1 then
# tells S-format (0) apart from U-format (1).

APCI_START = 0x68
"""Fixed start byte every APCI frame begins with."""

APCI_FORMAT_MASK = 0b11
"""Mask isolating the two format-selector bits from the first control octet."""


class APCIFormat(enum.IntEnum):
    """
    APCI control-field format selector, held in the low bit(s) of the
    control field's first octet.
    (See IEC 60870-5-104, clause 5.1)
    """

    I_FORMAT = 0b00
    """Information transfer format - carries an ASDU, sequenced by
    :class:`ControlField_I`'s ``send_seq``/``recv_seq``. Only bit 0
    (``= 0``) is significant; bit 1 is always transmitted as 0."""

    S_FORMAT = 0b01
    """Numbered supervisory function format - a bare acknowledgment,
    carrying only a ``recv_seq`` (:class:`ControlField_S`)."""

    U_FORMAT = 0b11
    """Unnumbered control function format - carries one of the
    ``STARTDT``/``STOPDT``/``TESTFR`` handshake functions
    (:class:`ControlField_U`, see :class:`UFormatFunction`)."""


class UFormatFunction(enum.IntFlag):
    """
    U-format control function bits.

    Each member is an independent single-bit flag inside the U-format
    control field's first octet (bits 2-7; bits 0-1 are always ``11``,
    see :attr:`APCIFormat.U_FORMAT`). Exactly one ``_ACT``/``_CON`` bit is
    set per U-format APDU.
    """

    __struct__ = uint8

    STARTDT_ACT = 0x04
    """Start data transfer - activation (client to server)."""

    STARTDT_CON = 0x08
    """Start data transfer - confirmation (server to client)."""

    STOPDT_ACT = 0x10
    """Stop data transfer - activation (client to server)."""

    STOPDT_CON = 0x20
    """Stop data transfer - confirmation (server to client)."""

    TESTFR_ACT = 0x40
    """Test frame - activation (either direction)."""

    TESTFR_CON = 0x80
    """Test frame - confirmation (either direction, answers ``TESTFR_ACT``)."""


# ============================================================================ #
# ASDU - Type identification
# ============================================================================ #


class TypeID(enum.IntEnum):
    """
    ASDU Type Identification.

    Identifies the structure and semantics of the information objects
    carried by an ASDU (Application Service Data Unit). Written into the
    first octet of every ASDU.
    (See IEC 60870-5-101, clause 7.2.2)

    File-transfer types (120-126) and the security-extension ``S_*`` types
    (81-95, defined by IEC 60870-5-7) are not modeled yet.
    """

    __struct__ = uint8

    # -- Phase A: monitor direction, without time tag ------------------- #

    M_SP_NA_1 = 1
    """Single-point information."""

    M_SP_TA_1 = 2
    """Single-point information with CP24Time2a time tag."""

    M_DP_NA_1 = 3
    """Double-point information."""

    M_DP_TA_1 = 4
    """Double-point information with CP24Time2a time tag."""

    M_ST_NA_1 = 5
    """Step position information."""

    M_ST_TA_1 = 6
    """Step position information with CP24Time2a time tag."""

    M_BO_NA_1 = 7
    """Bitstring of 32 bit."""

    M_BO_TA_1 = 8
    """Bitstring of 32 bit with CP24Time2a time tag."""

    M_ME_NA_1 = 9
    """Measured value, normalized value."""

    M_ME_TA_1 = 10
    """Measured value, normalized value with CP24Time2a time tag."""

    M_ME_NB_1 = 11
    """Measured value, scaled value."""

    M_ME_TB_1 = 12
    """Measured value, scaled value with CP24Time2a time tag."""

    M_ME_NC_1 = 13
    """Measured value, short floating point number."""

    M_ME_TC_1 = 14
    """Measured value, short floating point number with CP24Time2a time tag."""

    M_IT_NA_1 = 15
    """Integrated totals."""

    M_IT_TA_1 = 16
    """Integrated totals with CP24Time2a time tag."""

    M_EP_TA_1 = 17
    """Event of protection equipment with CP24Time2a time tag."""

    M_EP_TB_1 = 18
    """Packed start events of protection equipment with CP24Time2a time tag."""

    M_EP_TC_1 = 19
    """Packed output circuit information of protection equipment with
    CP24Time2a time tag."""

    M_PS_NA_1 = 20
    """Packed single-point information with status change detection."""

    M_ME_ND_1 = 21
    """Measured value, normalized value without quality descriptor."""

    # -- Phase B: monitor direction, with CP56Time2a tag (104-preferred) - #

    M_SP_TB_1 = 30
    """Single-point information with CP56Time2a time tag."""

    M_DP_TB_1 = 31
    """Double-point information with CP56Time2a time tag."""

    M_ST_TB_1 = 32
    """Step position information with CP56Time2a time tag."""

    M_BO_TB_1 = 33
    """Bitstring of 32 bit with CP56Time2a time tag."""

    M_ME_TD_1 = 34
    """Measured value, normalized value with CP56Time2a time tag."""

    M_ME_TE_1 = 35
    """Measured value, scaled value with CP56Time2a time tag."""

    M_ME_TF_1 = 36
    """Measured value, short floating point number with CP56Time2a time tag."""

    M_IT_TB_1 = 37
    """Integrated totals with CP56Time2a time tag."""

    M_EP_TD_1 = 38
    """Event of protection equipment with CP56Time2a time tag."""

    M_EP_TE_1 = 39
    """Packed start events of protection equipment with CP56Time2a time tag."""

    M_EP_TF_1 = 40
    """Packed output circuit information of protection equipment with
    CP56Time2a time tag."""

    S_IT_TC_1 = 41
    """Integrated totals containing time tagged security statistics
    (vendor-common extension carried in the base Type-ID space by several
    stacks)."""

    # -- Phase C: command direction ------------------------------------- #

    C_SC_NA_1 = 45
    """Single command."""

    C_DC_NA_1 = 46
    """Double command."""

    C_RC_NA_1 = 47
    """Regulating step command."""

    C_SE_NA_1 = 48
    """Set-point command, normalized value."""

    C_SE_NB_1 = 49
    """Set-point command, scaled value."""

    C_SE_NC_1 = 50
    """Set-point command, short floating point number."""

    C_BO_NA_1 = 51
    """Bitstring of 32 bit command."""

    C_SC_TA_1 = 58
    """Single command with CP56Time2a time tag."""

    C_DC_TA_1 = 59
    """Double command with CP56Time2a time tag."""

    C_RC_TA_1 = 60
    """Regulating step command with CP56Time2a time tag."""

    C_SE_TA_1 = 61
    """Set-point command, normalized value with CP56Time2a time tag."""

    C_SE_TB_1 = 62
    """Set-point command, scaled value with CP56Time2a time tag."""

    C_SE_TC_1 = 63
    """Set-point command, short floating point number with CP56Time2a
    time tag."""

    C_BO_TA_1 = 64
    """Bitstring of 32 bit command with CP56Time2a time tag."""

    # -- Phase D: system information & parameter commands ---------------- #

    M_EI_NA_1 = 70
    """End of initialization."""

    C_IC_NA_1 = 100
    """General interrogation command."""

    C_CI_NA_1 = 101
    """Counter interrogation command."""

    C_RD_NA_1 = 102
    """Read command."""

    C_CS_NA_1 = 103
    """Clock synchronization command."""

    C_TS_NA_1 = 104
    """Test command."""

    C_RP_NA_1 = 105
    """Reset process command."""

    C_CD_NA_1 = 106
    """Delay acquisition command."""

    C_TS_TA_1 = 107
    """Test command with CP56Time2a time tag."""

    P_ME_NA_1 = 110
    """Parameter of measured value, normalized value."""

    P_ME_NB_1 = 111
    """Parameter of measured value, scaled value."""

    P_ME_NC_1 = 112
    """Parameter of measured value, short floating point number."""

    P_AC_NA_1 = 113
    """Parameter activation."""


# ============================================================================ #
# ASDU - Cause of transmission
# ============================================================================ #


class CauseOfTransmission(enum.IntEnum):
    """
    Cause Of Transmission (COT).

    Explains *why* an ASDU was sent - e.g. spontaneously, in answer to an
    interrogation, or in response to a command - and occupies the lower 6
    bits of the ASDU header's second octet (see the ``cause`` field of
    :class:`~icspacket.proto.iec104.asdu.CauseOfTransmissionField`).
    (See IEC 60870-5-101, clause 7.2.3)
    """

    __struct__ = uint8

    PERIODIC = 1
    """Transmitted cyclically/periodically."""

    BACKGROUND_SCAN = 2
    """Transmitted as part of a background scan."""

    SPONTANEOUS = 3
    """Transmitted spontaneously (unsolicited, e.g. on a value change)."""

    INITIALIZED = 4
    """Transmitted after the outstation (re-)initialized."""

    REQUEST = 5
    """Transmitted in response to a read request."""

    ACTIVATION = 6
    """Command activation."""

    ACTIVATION_CON = 7
    """Command activation confirmation."""

    DEACTIVATION = 8
    """Command deactivation."""

    DEACTIVATION_CON = 9
    """Command deactivation confirmation."""

    ACTIVATION_TERMINATION = 10
    """Command activation termination."""

    RETURN_INFO_REMOTE = 11
    """Feedback caused by a remote command."""

    RETURN_INFO_LOCAL = 12
    """Feedback caused by a local command (e.g. local operator action)."""

    FILE_TRANSFER = 13
    """Transmitted as part of a file transfer."""

    AUTHENTICATION = 14
    """Authentication (IEC 62351 security extension)."""

    MAINTENANCE_OF_AUTH_SESSION_KEY = 15
    """Maintenance of authentication session key (IEC 62351)."""

    MAINTENANCE_OF_USER_ROLE_AND_UPDATE_KEY = 16
    """Maintenance of user role and update key (IEC 62351)."""

    INTERROGATED_BY_STATION = 20
    """Transmitted in response to a station (global) interrogation."""

    INTERROGATED_BY_GROUP_1 = 21
    """Transmitted in response to a group-1 interrogation."""

    INTERROGATED_BY_GROUP_2 = 22
    """Transmitted in response to a group-2 interrogation."""

    INTERROGATED_BY_GROUP_3 = 23
    """Transmitted in response to a group-3 interrogation."""

    INTERROGATED_BY_GROUP_4 = 24
    """Transmitted in response to a group-4 interrogation."""

    INTERROGATED_BY_GROUP_5 = 25
    """Transmitted in response to a group-5 interrogation."""

    INTERROGATED_BY_GROUP_6 = 26
    """Transmitted in response to a group-6 interrogation."""

    INTERROGATED_BY_GROUP_7 = 27
    """Transmitted in response to a group-7 interrogation."""

    INTERROGATED_BY_GROUP_8 = 28
    """Transmitted in response to a group-8 interrogation."""

    INTERROGATED_BY_GROUP_9 = 29
    """Transmitted in response to a group-9 interrogation."""

    INTERROGATED_BY_GROUP_10 = 30
    """Transmitted in response to a group-10 interrogation."""

    INTERROGATED_BY_GROUP_11 = 31
    """Transmitted in response to a group-11 interrogation."""

    INTERROGATED_BY_GROUP_12 = 32
    """Transmitted in response to a group-12 interrogation."""

    INTERROGATED_BY_GROUP_13 = 33
    """Transmitted in response to a group-13 interrogation."""

    INTERROGATED_BY_GROUP_14 = 34
    """Transmitted in response to a group-14 interrogation."""

    INTERROGATED_BY_GROUP_15 = 35
    """Transmitted in response to a group-15 interrogation."""

    INTERROGATED_BY_GROUP_16 = 36
    """Transmitted in response to a group-16 interrogation."""

    REQUESTED_BY_GENERAL_COUNTER = 37
    """Transmitted in response to a general counter interrogation."""

    REQUESTED_BY_GROUP_1_COUNTER = 38
    """Transmitted in response to a group-1 counter interrogation."""

    REQUESTED_BY_GROUP_2_COUNTER = 39
    """Transmitted in response to a group-2 counter interrogation."""

    REQUESTED_BY_GROUP_3_COUNTER = 40
    """Transmitted in response to a group-3 counter interrogation."""

    REQUESTED_BY_GROUP_4_COUNTER = 41
    """Transmitted in response to a group-4 counter interrogation."""

    UNKNOWN_TYPE_ID = 44
    """Negative confirmation: the Type-ID is not supported by the outstation."""

    UNKNOWN_COT = 45
    """Negative confirmation: the cause of transmission is not supported."""

    UNKNOWN_CA = 46
    """Negative confirmation: the Common Address is not configured."""

    UNKNOWN_IOA = 47
    """Negative confirmation: the Information Object Address is unknown."""


# ============================================================================ #
# Information elements - qualifier & state enumerations
# ============================================================================ #


class DoublePointValue(enum.IntEnum):
    """
    Double-point information value (DPI).

    The 2-bit value carried by :class:`~icspacket.proto.iec104.objects.elements.DIQ`
    and, in command direction, the state bits of
    :class:`~icspacket.proto.iec104.objects.elements.DCO`.
    (See IEC 60870-5-101, clause 7.2.6.2)
    """

    INTERMEDIATE = 0
    """Indeterminate/intermediate state (point is transitioning)."""

    OFF = 1
    """Determined OFF state."""

    ON = 2
    """Determined ON state."""

    INDETERMINATE = 3
    """Indeterminate state (fault)."""


class StepCommandValue(enum.IntEnum):
    """
    Regulating-step command value (RCS).

    The 2-bit value carried by the state bits of
    :class:`~icspacket.proto.iec104.objects.elements.RCO`. Structurally the
    same width/position as :class:`DoublePointValue`, but with distinct
    "lower/higher" semantics, so it is modeled as its own enum.
    (See IEC 60870-5-101, clause 7.2.6.17)
    """

    INVALID_0 = 0
    """Not permitted."""

    LOWER = 1
    """Regulating step: next step lower/DOWN."""

    HIGHER = 2
    """Regulating step: next step higher/UP."""

    INVALID_3 = 3
    """Not permitted."""


class QOI(enum.IntEnum):
    """
    Qualifier Of Interrogation command.

    Selects the scope of a general interrogation command (:data:`TypeID.C_IC_NA_1`):
    the whole station, or one of 16 interrogation groups configured on the
    outstation.
    (See IEC 60870-5-101, clause 7.2.6.22)
    """

    __struct__ = uint8

    STATION = 20
    """Interrogate the entire station (global/general interrogation)."""

    GROUP_1 = 21
    GROUP_2 = 22
    GROUP_3 = 23
    GROUP_4 = 24
    GROUP_5 = 25
    GROUP_6 = 26
    GROUP_7 = 27
    GROUP_8 = 28
    GROUP_9 = 29
    GROUP_10 = 30
    GROUP_11 = 31
    GROUP_12 = 32
    GROUP_13 = 33
    GROUP_14 = 34
    GROUP_15 = 35
    GROUP_16 = 36


class QCC_Request(enum.IntEnum):
    """
    Request qualifier (RQT) part of the Qualifier Of Counter interrogation
    Command (QCC).

    Occupies the lower 6 bits of the QCC octet; combine with a
    :class:`QCC_Freeze` member (upper 2 bits) to build a full
    :class:`~icspacket.proto.iec104.objects.elements.QCC` value.
    (See IEC 60870-5-101, clause 7.2.6.23)
    """

    GROUP_1 = 1
    GROUP_2 = 2
    GROUP_3 = 3
    GROUP_4 = 4
    GENERAL = 5
    """Request all counters (general/global counter interrogation)."""


class QCC_Freeze(enum.IntEnum):
    """
    Freeze qualifier (FRZ) part of the Qualifier Of Counter interrogation
    Command (QCC), occupying the upper 2 bits of the QCC octet.
    (See IEC 60870-5-101, clause 7.2.6.23)
    """

    READ = 0x00
    """Read the counter value(s) without freezing or resetting them."""

    FREEZE_WITHOUT_RESET = 0x40
    """Freeze the counter value(s) without resetting them."""

    FREEZE_WITH_RESET = 0x80
    """Freeze the counter value(s) and reset them afterwards."""

    COUNTER_RESET = 0xC0
    """Reset the counter value(s) without freezing them first."""


class QRP(enum.IntEnum):
    """
    Qualifier Of Reset Process command.
    (See IEC 60870-5-101, clause 7.2.6.27)
    """

    __struct__ = uint8

    NOT_USED = 0
    GENERAL_RESET = 1
    """Reset the entire process (outstation application)."""

    RESET_PENDING_INFO_WITH_TIME_TAG = 2
    """Reset all pending information with time tag."""


class QPA(enum.IntEnum):
    """
    Qualifier Of Parameter Activation command.
    (See IEC 60870-5-101, clause 7.2.6.25)
    """

    __struct__ = uint8

    NOT_USED = 0
    ACT_PREV_LOADED_PARAMETER = 1
    """(De)activate the previously loaded parameter set."""

    ACT_OBJECT_PARAMETER = 2
    """(De)activate the parameter of the addressed information object."""

    ACT_OBJECT_TRANSMISSION = 3
    """(De)activate cyclic/periodic transmission of the addressed object."""


class QPM_Kind(enum.IntEnum):
    """
    Kind-of-parameter part of the Qualifier of Parameter of Measured values
    (QPM), occupying the lower 6 bits of the QPM octet; bit 6 (``LPC``,
    "local parameter change") and bit 7 (``POP``, "parameter operation")
    are modeled as separate flags on
    :class:`~icspacket.proto.iec104.objects.elements.QPM`.
    (See IEC 60870-5-101, clause 7.2.6.24)
    """

    NOT_USED = 0
    THRESHOLD_VALUE = 1
    SMOOTHING_FACTOR = 2
    """Smoothing factor (filter time constant)."""

    LOW_LIMIT_FOR_TRANSMISSION = 3
    HIGH_LIMIT_FOR_TRANSMISSION = 4


class QOC(enum.IntEnum):
    """
    Qualifier Of Command, occupying bits 2-6 of the SCO/DCO/RCO octet (the
    ``qu`` field of :class:`~icspacket.proto.iec104.objects.elements.SCO`/
    :class:`~icspacket.proto.iec104.objects.elements.DCO`/
    :class:`~icspacket.proto.iec104.objects.elements.RCO`).
    (See IEC 60870-5-101, clause 7.2.6.26)
    """

    NO_ADDITIONAL_DEFINITION = 0
    """No additional definition - execute/terminate the command directly."""

    SHORT_PULSE_DURATION = 1
    """Output duration is determined by a system parameter."""

    LONG_PULSE_DURATION = 2
    """Output duration is determined by a system parameter (long)."""

    PERSISTENT_OUTPUT = 3
    """Output persists until a different command changes it."""


class COI_Cause(enum.IntEnum):
    """
    Cause-of-initialization value (the ``R`` sub-field, bits 0-6) carried
    by the fused :class:`~icspacket.proto.iec104.objects.elements.COI`
    octet of :data:`TypeID.M_EI_NA_1` (end of initialization). Bit 7 of
    that octet (``I``, "initialization after change of local parameters")
    is modeled as a separate flag on the :class:`.elements.COI` struct.
    (See IEC 60870-5-101, clause 7.2.6.21)
    """

    LOCAL_POWER_SWITCH_ON = 0
    """Local power switch on."""

    LOCAL_MANUAL_RESET = 1
    """Local manual reset."""

    REMOTE_RESET = 2
    """Remote reset."""
