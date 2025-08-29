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
import enum

from caterpillar.byteorder import LittleEndian
from caterpillar.fields import DEFAULT_OPTION, uint8, uint16, uint32, Pass

# ============================================================================ #
# DNP3 Constants and Enumerations
# ============================================================================ #

APDU_REQ_FUNC_MIN = 0
"""Minimum function code value for Application Layer requests."""

APDU_REQ_FUNC_MAX = 128
"""Maximum function code value for Application Layer requests."""

APDU_RESP_FUNC_MIN = 129
"""Minimum function code value for Application Layer responses."""

APDU_RESP_FUNC_MAX = 255
"""Maximum function code value for Application Layer responses."""


class FunctionCode(enum.IntEnum):
    """
    Application Layer Function Codes.

    Function codes define the type of operation performed by the
    Application Layer. They are carried in the first octet of an
    Application Protocol Data Unit (APDU).

    (See DNP3 Specification, Section 4.2.2.5)
    """

    __struct__ = uint8

    CONFIRM = 0
    """Master confirms receipt of an Application Layer fragment."""

    READ = 1
    """Outstation shall return the data specified in the request."""

    WRITE = 2
    """Outstation shall store the data specified in the request."""

    SELECT = 3
    """Outstation selects output points in preparation for an `OPERATE` command."""

    OPERATE = 4
    """Outstation activates output points selected by a prior `SELECT`."""

    DIRECT_OPERATE = 5
    """Outstation immediately actuates output points without requiring `SELECT`."""

    DIRECT_OPERATE_NR = 6
    """Same as `DIRECT_OPERATE` but without sending a response."""

    IMMED_FREEZE = 7
    """Outstation copies data values into a freeze buffer."""

    IMMED_FREEZE_NR = 8
    """Same as `IMMED_FREEZE` but without sending a response."""

    FREEZE_CLEAR = 9
    """Outstation copies data values into a freeze buffer and clears originals."""

    FREEZE_CLEAR_NR = 10
    """Same as `FREEZE_CLEAR` but without sending a response."""

    FREEZE_AT_TIME = 11
    """Outstation freezes data values at a specified time/interval."""

    FREEZE_AT_TIME_NR = 12
    """Same as `FREEZE_AT_TIME` but without sending a response."""

    COLD_RESTART = 13
    """Outstation performs a full reset of hardware and software."""

    WARM_RESTART = 14
    """Outstation performs a partial reset of the device."""

    INITIALIZE_DATA = 15
    """Obsolete — not to be used in new designs."""

    INITIALIZE_APPL = 16
    """Outstation places applications into ready-to-run state."""

    START_APPL = 17
    """Outstation starts the specified applications."""

    STOP_APPL = 18
    """Outstation stops the specified applications."""

    SAVE_CONFIG = 19
    """Deprecated — saving of configuration (do not use in new designs)."""

    ENABLE_UNSOLICITED = 20
    """Outstation enables unsolicited responses for specified points."""

    DISABLE_UNSOLICITED = 21
    """Outstation disables unsolicited responses for specified points."""

    ASSIGN_CLASS = 22
    """Outstation assigns points/events to one of the defined classes."""

    DELAY_MESSAGE = 23
    """Outstation reports processing/transmission delay time."""

    RECORD_CURRENT_TIME = 24
    """Outstation records the current time when the last octet is received."""

    OPEN_FILE = 25
    """Outstation opens a file."""

    CLOSE_FILE = 26
    """Outstation closes a file."""

    DELETE_FILE = 27
    """Outstation deletes a file."""

    GET_FILE_INFO = 28
    """Outstation retrieves information about a file."""

    AUTHENTICATE_FILE = 29
    """Outstation returns a file authentication key."""

    ABORT_FILE = 30
    """Outstation aborts an ongoing file transfer."""

    ACTIVATE_CONFIG = 31
    """Outstation activates a configuration."""

    AUTHENTICATE_REQ = 32
    """Master sends an authentication request requiring acknowledgement."""

    AUTH_REQ_NO_ACK = 33
    """Master sends an authentication request not requiring acknowledgement."""

    RESPONSE = 129
    """Application Layer response to a master request."""

    UNSOLICITED_RESPONSE = 130
    """Unsolicited Application Layer response from the outstation."""

    AUTHENTICATE_RESP = 131
    """Outstation issues an authentication response to the master."""


class ObjectPrefixCode(enum.IntEnum):
    """
    Object Prefix Codes.

    Define how objects are prefixed when encoded in an Application Layer
    message.
    (See DNP3 Specification, Section 4.2.2.7.3.2)
    """

    NONE = 0
    """Objects are encoded without any index prefix."""

    INDEX_8 = 1
    """Objects are prefixed with an 8-bit index."""

    INDEX_16 = 2
    """Objects are prefixed with a 16-bit index."""

    INDEX_32 = 3
    """Objects are prefixed with a 32-bit index."""

    OBJECT_SIZE_8 = 4
    """Objects are prefixed with an 8-bit object size."""

    OBJECT_SIZE_16 = 5
    """Objects are prefixed with a 16-bit object size."""

    OBJECT_SIZE_32 = 6
    """Objects are prefixed with a 32-bit object size."""

    RESERVED = 7
    """Reserved for future use."""


class RangeSpecifierCode(enum.IntEnum):
    """
    Range Specifier Codes.

    Indicate how ranges of objects are expressed in a qualifier field,
    including start/stop indexes, virtual addresses, or counts.
    (See DNP3 Specification, Section 4.2.2.7.3.3)
    """

    RANGE_8 = 0
    """Range field contains 1-octet start and stop indexes."""

    RANGE_16 = 1
    """Range field contains 2-octet start and stop indexes."""

    RANGE_32 = 2
    """Range field contains 4-octet start and stop indexes."""

    RANGE_8_VIRTUAL = 3
    """Range field contains 1-octet start and stop virtual addresses."""

    RANGE_16_VIRTUAL = 4
    """Range field contains 2-octet start and stop virtual addresses."""

    RANGE_32_VIRTUAL = 5
    """Range field contains 4-octet start and stop virtual addresses."""

    NONE = 6
    """No range field is used (implies all values)."""

    COUNT_8 = 7
    """Range field contains a 1-octet count of objects."""

    COUNT_16 = 8
    """Range field contains a 2-octet count of objects."""

    COUNT_32 = 9
    """Range field contains a 4-octet count of objects."""

    VARIABLE = 11
    """Variable format qualifier with a 1-octet object count."""


APDU_RANGE_TYPES = {
    RangeSpecifierCode.COUNT_8: uint8,
    RangeSpecifierCode.COUNT_16: LittleEndian + uint16,
    RangeSpecifierCode.COUNT_32: LittleEndian + uint32,
    RangeSpecifierCode.RANGE_8: uint8[2],
    RangeSpecifierCode.RANGE_16: LittleEndian + uint16[2],
    RangeSpecifierCode.RANGE_32: LittleEndian + uint32[2],
    RangeSpecifierCode.RANGE_8_VIRTUAL: uint8[2],
    RangeSpecifierCode.RANGE_16_VIRTUAL: LittleEndian + uint16[2],
    RangeSpecifierCode.RANGE_32_VIRTUAL: LittleEndian + uint32[2],
    DEFAULT_OPTION: Pass,
}

APDU_PREFIX_TYPES = {
    ObjectPrefixCode.INDEX_8: uint8,
    ObjectPrefixCode.INDEX_16: LittleEndian + uint16,
    ObjectPrefixCode.INDEX_32: LittleEndian + uint32,
    ObjectPrefixCode.OBJECT_SIZE_8: uint8,
    ObjectPrefixCode.OBJECT_SIZE_16: LittleEndian + uint16,
    ObjectPrefixCode.OBJECT_SIZE_32: LittleEndian + uint32,
    # Objects are packed without an index prefix.
    DEFAULT_OPTION: Pass,
}
