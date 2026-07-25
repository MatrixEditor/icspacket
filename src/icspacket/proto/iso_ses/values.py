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

# See ITU X.225 – Connection-oriented session protocol
# Common Parameter Values (PV)

from caterpillar.types import int1_t
import enum
from caterpillar.byteorder import BigEndian
from caterpillar.fields import uint32
from caterpillar.model import EnumFactory
from caterpillar.shortcuts import bitfield, f


# ---------------------------------------------------------------------------
# PI Codes - parameter identifiers for commonly used PVs
# ---------------------------------------------------------------------------
class PI_Code(enum.IntEnum):
    """Common **Parameter Identifier** (PI) codes. (See X.225, 8.3)

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
    """Version Number PV. (See X.225)

    Flags which protocol version(s) this endpoint is willing to run; sent in
    the CONNECT SPDU and echoed back in the ACCEPT SPDU once the peer has
    picked one.
    """

    # fmt: off
    reserved: f[int, 6] = 0

    version2 : f[bool, 1] = True
    """True if **Protocol Version 2** is proposed."""

    version1 : f[bool, 1] = False
    """True if **Protocol Version 1** is proposed."""
    # fmt: on


# ---------------------------------------------------------------------------
# PV: Token Setting Item
# ---------------------------------------------------------------------------
class PV_TokenSettingPairType(enum.IntEnum):
    """The four values a 2-bit token-setting slot can take.

    Each slot fixes where one of the session's tokens starts out:

    - 0 - held by the initiator from the start
    - 1 - held by the responder from the start
    - 2 - left for the SS-user to decide ("user's choice")
    - 3 - reserved, not currently assigned a meaning

    """

    INITIATOR = 0
    RESPONDER = 1
    USERS_CHOICE = 2
    RESERVED = 3


@bitfield
class PV_TokenSetting:
    """Token Setting Item PV. (See X.225)

    When present, assigns a starting holder to each of the four session
    tokens listed below, using the slot values from
    :class:`PV_TokenSettingPairType`.
    """

    # fmt: off
    release: f[PV_TokenSettingPairType | int, (2, EnumFactory(PV_TokenSettingPairType))]  = PV_TokenSettingPairType.INITIATOR
    """Initial position of the **release token**."""

    activity: f[PV_TokenSettingPairType | int, (2, EnumFactory(PV_TokenSettingPairType))] = PV_TokenSettingPairType.INITIATOR
    """Initial position of the **activity token**."""

    sync: f[PV_TokenSettingPairType | int, (2, EnumFactory(PV_TokenSettingPairType))]     = PV_TokenSettingPairType.INITIATOR
    """Initial position of the **synchronization token**."""

    data: f[PV_TokenSettingPairType | int, (2, EnumFactory(PV_TokenSettingPairType))]     = PV_TokenSettingPairType.INITIATOR
    """Initial position of the **data token**."""
    # fmt: on


# ---------------------------------------------------------------------------
# PV: Token Item
# ---------------------------------------------------------------------------
@bitfield
class PV_TokenItem:
    """Token Item PV. (See X.225)

    Each bit is a request flag the called SS-user sets to claim one of the
    four session tokens listed below.
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
    """Transport Disconnect PV. (See X.225)

    Carried in the ABORT SPDU: one bit says whether the transport connection
    should be released or kept alive, and the rest record which abort reason
    triggered the message.
    """

    # fmt: off
    _reserved: f[int, 3] = 0
    implementation_restriction: f[bool, 1] = False
    no_reason: f[bool, 1] = False
    protocol_error: f[bool, 1] = False
    user_abort: f[bool, 1] = False
    release_transport: f[bool, 1] = True
    # fmt: on


# ---------------------------------------------------------------------------
# PV: Session Requirements
# ---------------------------------------------------------------------------
@bitfield(order=BigEndian)  # because of 16 bits in spec layout
class PV_SessionRequirements:
    """Session Requirements PV. (See X.225)

    Sent by the calling SS-user in the CONNECT SPDU to advertise which
    optional functional units (listed below) it wants active for the
    session; the responder echoes back the subset it accepts in the ACCEPT
    SPDU.
    """

    _reserved: f[int, 3] = 0
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

    @classmethod
    def default(cls) -> "PV_SessionRequirements":
        """Return the default client functional-unit proposal."""
        return cls(
            duplex=True,
        )

    def update(self, accepted: "PV_SessionRequirements") -> "PV_SessionRequirements":
        """Return the functional units selected by both peers."""
        return type(self)(
            data_separation=self.data_separation and accepted.data_separation,
            symmetric_sync=self.symmetric_sync and accepted.symmetric_sync,
            typed=self.typed and accepted.typed,
            exceptions=self.exceptions and accepted.exceptions,
            capability_data_exchange=(
                self.capability_data_exchange and accepted.capability_data_exchange
            ),
            negotiated_release=self.negotiated_release and accepted.negotiated_release,
            activity_management=self.activity_management
            and accepted.activity_management,
            resync=self.resync and accepted.resync,
            major_sync=self.major_sync and accepted.major_sync,
            minor_sync=self.minor_sync and accepted.minor_sync,
            expedited=self.expedited and accepted.expedited,
            duplex=self.duplex and accepted.duplex,
            half_duplex=self.half_duplex and accepted.half_duplex,
        )

    @property
    def is_empty(self) -> bool:
        """Whether no functional units are proposed."""
        return not (
            self.data_separation
            or self.symmetric_sync
            or self.typed
            or self.exceptions
            or self.capability_data_exchange
            or self.negotiated_release
            or self.activity_management
            or self.resync
            or self.major_sync
            or self.minor_sync
            or self.expedited
            or self.duplex
            or self.half_duplex
        )


# ---------------------------------------------------------------------------
# PV: Enclosure Item
# ---------------------------------------------------------------------------
@bitfield
class PV_EnclosureItem:
    """Enclosure Item PV. (See X.225)

    Two independent flags marking whether the carrying SPDU is the start
    and/or the end of an SSDU.
    """

    _reserved: f[int, 6] = 0
    end: f[bool, 1] = False
    """True if this SPDU is the **end** of the SSDU."""

    start: f[bool, 1] = False
    """True if this SPDU is the **start** of the SSDU."""


# ---------------------------------------------------------------------------
# PV: Protocol Options
# ---------------------------------------------------------------------------
@bitfield
class PV_ProtocolOptions:
    """Protocol Options PV. (See X.225, §8.3.19)

    Single capability flag sent in the CONNECT SPDU and echoed in the ACCEPT
    SPDU, advertising support for receiving extended concatenated SPDUs.
    """

    _reserved: f[int, 7] = 0
    extended: f[bool, 1] = False
    """True if extended concatenated SPDUs are supported."""


# ---------------------------------------------------------------------------
# PV: Data Overflow
# ---------------------------------------------------------------------------
@bitfield
class PV_DataOverflow:
    """Data Overflow PV. (See X.225)"""

    _reserved: f[int, 7] = 0
    overflow: f[bool, 1] = True


PV_TYPES = {
    PI_Code.VERSION_NUMBER: PV_VersionNumber,
    PI_Code.TOKEN_SETTING_ITEM: PV_TokenSetting,
    PI_Code.SESSION_REQUIREMENT: PV_SessionRequirements,
    PI_Code.TSDU_MAXIMUM_SIZE: uint32,
    PI_Code.ENCLOSUREITEM: PV_EnclosureItem,
    PI_Code.TOKEN_ITEM: PV_TokenItem,
    PI_Code.TRANSPORT_DISCONNECT: PV_TransportDisconnect,
    PI_Code.PROTOCOL_OPTIONS: PV_ProtocolOptions,
    PI_Code.DATA_OVERFLOW: PV_DataOverflow,
}
"""Mapping from PI codes to their associated **Parameter Value** types.

This table is used during SPDU parameter decoding to instantiate the right PV
object.
"""
