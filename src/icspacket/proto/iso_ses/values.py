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
# pyright: reportInvalidTypeForm=false, reportGeneralTypeIssues=false, reportAssignmentType=false

# [ITU X.225] – Connection-oriented session protocol
# Common Parameter Values (PV)

import enum

from caterpillar.model import EnumFactory
from caterpillar.py import bitfield, f, uint32, BigEndian
from caterpillar.types import int6_t, int1_t, int3_t, int7_t


# ---------------------------------------------------------------------------
# PI Codes - parameter identifiers for commonly used PVs
# ---------------------------------------------------------------------------
class PI_Code(enum.IntEnum):
    """Common **Parameter Identifier** (PI) codes - X.225 8.3

    .. note::

        - Not all PI codes are mapped to PV implementations here; only those
          with common, structured bitfield encodings are represented.
        - Other PIs may be treated as raw byte values in other parts of the
          parser.
    """

    # fmt: off
    CALLED_SS_USER_REFERENCE            = 9
    CALLING_SS_USER_REFERENCE           = 10
    COMMON_REFERENCE                    = 11
    ADDITIONAL_REFERENCE_INFORMATION    = 12
    SYNC_TYPE_ITEM                      = 15
    TOKEN_ITEM                          = 16
    TRANSPORT_DISCONNECT                = 17
    PROTOCOL_OPTIONS                    = 19
    SESSION_REQUIREMENT                 = 20
    TSDU_MAXIMUM_SIZE                   = 21
    VERSION_NUMBER                      = 22
    INITIAL_SERIAL_NUMBER               = 23
    PREPARE_TYPE                        = 24
    ENCLOSUREITEM                       = 25
    TOKEN_SETTING_ITEM                  = 26
    RESYNC_TYPE                         = 27
    ACTIVITY_IDENTIFIER                 = 41
    SERIAL_NUMBER                       = 42
    REFLECT_PARAMETER                   = 49
    REASON_CODE                         = 50
    CALLING_SESSION_SELECTOR            = 51
    CALLED_SESSION_SELECTOR             = 52
    SECOND_RESYNC_TYPE                  = 53
    SECOND_SERIAL_NUMBER                = 54
    SECOND_INITIAL_SERIAL_NUMBER        = 55
    UPPER_LIMIT_SERIAL_NUMBER           = 56
    LARGE_INITIAL_SERIAL_NUMBER         = 57
    LARGE_SECOND_INITIAL_SERIAL_NUMBER  = 58
    DATA_OVERFLOW                       = 60
    # fmt: on


# ---------------------------------------------------------------------------
# PV: Version Number
# ---------------------------------------------------------------------------


@bitfield
class PV_VersionNumber:
    """Version Number PV - X.225

    Indicates which protocol versions are **proposed** for use over this session
    connection.
    """

    # fmt: off
    reserved: int6_t = 0

    version2 : f[bool, 1] = True
    """True if **Protocol Version 2** is proposed."""

    version1 : f[bool, 1] = False
    """True if **Protocol Version 1** is proposed."""
    # fmt: on


# ---------------------------------------------------------------------------
# PV: Token Setting Item
# ---------------------------------------------------------------------------
class PV_TokenSettingPairType(enum.IntEnum):
    """Enumerated meaning of a **token-setting bit pair**

    Each token position is indicated using a 2-bit value:

    - 0 - Token initially with the initiator
    - 1 - Token initially with the responder
    - 2 - Token location decided by the SS-user ("user's choice")
    - 3 - Reserved

    """

    INITIATOR = 0
    RESPONDER = 1
    USERS_CHOICE = 2
    RESERVED = 3


@bitfield
class PV_TokenSetting:
    """Token Setting Item PV - X.225

    If present, indicates the **initial position** of the protocol's tokens.
    """

    # fmt: off
    release: f[PV_TokenSettingPairType, (2, EnumFactory(PV_TokenSettingPairType))]  = PV_TokenSettingPairType.INITIATOR
    """Initial position of the **release token**."""

    activity: f[PV_TokenSettingPairType, (2, EnumFactory(PV_TokenSettingPairType))] = PV_TokenSettingPairType.INITIATOR
    """Initial position of the **activity token**."""

    sync: f[PV_TokenSettingPairType, (2, EnumFactory(PV_TokenSettingPairType))]     = PV_TokenSettingPairType.INITIATOR
    """Initial position of the **synchronization token**."""

    data: f[PV_TokenSettingPairType, (2, EnumFactory(PV_TokenSettingPairType))]     = PV_TokenSettingPairType.INITIATOR
    """Initial position of the **data token**."""
    # fmt: on


# ---------------------------------------------------------------------------
# PV: Token Item
# ---------------------------------------------------------------------------
@bitfield
class PV_TokenItem:
    """Token Item PV - X.225

    Indicates which tokens are **requested** by the called SS-user.
    """

    _reserved_1: int1_t = 0
    release_token: f[bool, 1] = False
    """Request for the **release token**."""

    _reserved_2: int1_t = 0
    activity_token: f[bool, 1] = False
    """Request for the **activity token**."""

    _reserved_3: int1_t = 0
    sync_minor_token: f[bool, 1] = False
    """Request for the **minor sync token**."""

    _reserved_4: int1_t = 0
    data_token: f[bool, 1] = False
    """Request for the **data token**."""


# ---------------------------------------------------------------------------
# PV: Transport Disconnect
# ---------------------------------------------------------------------------
@bitfield
class PV_TransportDisconnect:
    """Transport Disconnect PV - X.225.

    Indicates whether the transport connection is released or retained, and
    carries the abort reason bits used by the ABORT SPDU.
    """

    # fmt: off
    _reserved: f[int, 3] = 0
    implementation_restriction: f[bool, 1] = False
    no_reason: f[bool, 1] = False

    protocol_error: f[bool, 1] = False
    """Protocol error"""

    user_abort: f[bool, 1] = False
    """User abort"""

    release_transport: f[bool, 1] = True
    """transport connection is released"""

    keep_transport: f[bool, 1] = False
    """transport connection is kept"""
    # fmt: on


# ---------------------------------------------------------------------------
# PV: Session Requirements
# ---------------------------------------------------------------------------
@bitfield(order=BigEndian)  # because of 16 bits in spec layout
class PV_SessionRequirements:
    """Session Requirements PV - X.225

    Indicates the functional units proposed by the **calling SS-user**.
    """

    _reserved: int3_t = 0
    data_separation: f[bool, 1] = False
    """Functional unit: Data separation"""

    symmetric_sync: f[bool, 1] = False
    """Functional unit: Symmetric synchronization"""

    typed: f[bool, 1] = False
    """Functional unit: Typed data"""

    exceptions: f[bool, 1] = False
    """Functional unit: Exceptions"""

    capability_data_exchange: f[bool, 1] = False
    """Functional unit: Capability data exchange"""

    negotiated_release: f[bool, 1] = False
    """Functional unit: Negotiated release"""

    activity_management: f[bool, 1] = False
    """Functional unit: Activity management"""

    resync: f[bool, 1] = False
    """Functional unit: Resynchronization"""

    major_sync: f[bool, 1] = False
    """Functional unit: Major synchronization"""

    minor_sync: f[bool, 1] = False
    """Functional unit: Minor synchronization"""

    expedited: f[bool, 1] = False
    """Functional unit: Expedited data"""

    duplex: f[bool, 1] = False
    """Functional unit: Full-duplex"""

    half_duplex: f[bool, 1] = False
    """Functional unit: Half-duplex"""


# ---------------------------------------------------------------------------
# PV: Enclosure Item
# ---------------------------------------------------------------------------
@bitfield
class PV_EnclosureItem:
    """Enclosure Item PV - X.225

    Indicates whether this SPDU is the **start** and/or **end** of an SSDU.
    """

    _reserved: int6_t = 0
    end: f[bool, 1] = False
    """True if this SPDU is the **end** of the SSDU."""

    start: f[bool, 1] = False
    """True if this SPDU is the **start** of the SSDU."""


# ---------------------------------------------------------------------------
# PV: Protocol Options
# ---------------------------------------------------------------------------
@bitfield
class PV_ProtocolOptions:
    """Protocol Options PV - X.225 §8.3.19

    Indicates whether the initiator can receive **extended concatenated SPDUs**.
    """

    _reserved: int7_t = 0
    extended: f[bool, 1] = False
    """True if extended concatenated SPDUs are supported."""


PV_TYPES = {
    PI_Code.VERSION_NUMBER: PV_VersionNumber,
    PI_Code.TOKEN_SETTING_ITEM: PV_TokenSetting,
    PI_Code.SESSION_REQUIREMENT: PV_SessionRequirements,
    PI_Code.TSDU_MAXIMUM_SIZE: uint32,
    PI_Code.ENCLOSUREITEM: PV_EnclosureItem,
    PI_Code.TOKEN_ITEM: PV_TokenItem,
    PI_Code.PROTOCOL_OPTIONS: PV_ProtocolOptions,
    PI_Code.TRANSPORT_DISCONNECT: PV_TransportDisconnect,
}
"""Mapping from PI codes to their associated **Parameter Value** types.

This table is used during SPDU parameter decoding to instantiate the right PV
object.
"""
