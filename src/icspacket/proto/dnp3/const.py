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
from caterpillar.fields import DEFAULT_OPTION, Pass, uint8, uint16, uint32

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

    Each member identifies one operation a master or outstation can invoke
    on its peer; this library writes the member's numeric value into the
    first octet of an Application Protocol Data Unit (APDU) to say which
    operation a given fragment represents.

    (See DNP3 Specification, Section 4.2.2.5)
    """

    __struct__ = uint8

    CONFIRM = 0
    """Sent by the master to acknowledge that it received an application fragment."""

    READ = 1
    """Asks the outstation to return the data identified in the request."""

    WRITE = 2
    """Asks the outstation to store the data supplied in the request."""

    SELECT = 3
    """Has the outstation prepare the requested output points, the first
    step of a select-before-operate sequence completed by `OPERATE`."""

    OPERATE = 4
    """Tells the outstation to activate the output points a prior `SELECT`
    already prepared."""

    DIRECT_OPERATE = 5
    """Tells the outstation to activate the named output points right away,
    skipping the `SELECT` step."""

    DIRECT_OPERATE_NR = 6
    """Behaves like `DIRECT_OPERATE`, except the outstation does not send
    back a response."""

    IMMED_FREEZE = 7
    """Tells the outstation to snapshot its current data values into a
    freeze buffer."""

    IMMED_FREEZE_NR = 8
    """Behaves like `IMMED_FREEZE`, except the outstation does not send
    back a response."""

    FREEZE_CLEAR = 9
    """Tells the outstation to snapshot its data values into a freeze buffer
    and then reset the originals."""

    FREEZE_CLEAR_NR = 10
    """Behaves like `FREEZE_CLEAR`, except the outstation does not send
    back a response."""

    FREEZE_AT_TIME = 11
    """Schedules the outstation to freeze its data values at a time or on an
    interval given in the request."""

    FREEZE_AT_TIME_NR = 12
    """Behaves like `FREEZE_AT_TIME`, except the outstation does not send
    back a response."""

    COLD_RESTART = 13
    """Asks the outstation to fully reset both its hardware and software."""

    WARM_RESTART = 14
    """Asks the outstation to perform a lighter, partial reset of the device."""

    INITIALIZE_DATA = 15
    """Obsolete; new designs must not send this code."""

    INITIALIZE_APPL = 16
    """Asks the outstation to bring the named application(s) into a
    ready-to-run state."""

    START_APPL = 17
    """Asks the outstation to start the application(s) named in the request."""

    STOP_APPL = 18
    """Asks the outstation to stop the application(s) named in the request."""

    SAVE_CONFIG = 19
    """Deprecated request to save configuration; avoid using it in new designs."""

    ENABLE_UNSOLICITED = 20
    """Asks the outstation to start sending unsolicited responses for the
    named points."""

    DISABLE_UNSOLICITED = 21
    """Asks the outstation to stop sending unsolicited responses for the
    named points."""

    ASSIGN_CLASS = 22
    """Asks the outstation to assign the named points or events to one of
    its event classes."""

    DELAY_MESSAGE = 23
    """Asks the outstation to report how much processing/transmission delay
    it is adding."""

    RECORD_CURRENT_TIME = 24
    """Asks the outstation to note its own clock value at the instant it
    receives this request's last octet."""

    OPEN_FILE = 25
    """Asks the outstation to open the file named in the request."""

    CLOSE_FILE = 26
    """Asks the outstation to close a previously opened file."""

    DELETE_FILE = 27
    """Asks the outstation to delete the file named in the request."""

    GET_FILE_INFO = 28
    """Asks the outstation to report information describing a file."""

    AUTHENTICATE_FILE = 29
    """Asks the outstation to return a key used to authenticate file access."""

    ABORT_FILE = 30
    """Asks the outstation to cancel a file transfer already in progress."""

    ACTIVATE_CONFIG = 31
    """Asks the outstation to switch to (activate) a previously loaded
    configuration."""

    AUTHENTICATE_REQ = 32
    """Sent by the master to start an authentication exchange that expects
    an acknowledgement."""

    AUTH_REQ_NO_ACK = 33
    """Sent by the master to start an authentication exchange that does not
    expect an acknowledgement."""

    RESPONSE = 129
    """Marks a fragment as the outstation's reply to a master's request."""

    UNSOLICITED_RESPONSE = 130
    """Marks a fragment as a response the outstation generated on its own,
    with no matching request from the master."""

    AUTHENTICATE_RESP = 131
    """Sent by the outstation to answer a master's authentication request."""


class ObjectPrefixCode(enum.IntEnum):
    """
    Object Prefix Codes.

    Selects how this library tags each object inside an encoded Application
    Layer message - with an index value, a size value, or no prefix at all.
    (See DNP3 Specification, Section 4.2.2.7.3.2)
    """

    NONE = 0
    """No prefix is written before each object."""

    INDEX_8 = 1
    """Each object is preceded by an 8-bit index value."""

    INDEX_16 = 2
    """Each object is preceded by a 16-bit index value."""

    INDEX_32 = 3
    """Each object is preceded by a 32-bit index value."""

    OBJECT_SIZE_8 = 4
    """Each object is preceded by its own size, encoded in 8 bits."""

    OBJECT_SIZE_16 = 5
    """Each object is preceded by its own size, encoded in 16 bits."""

    OBJECT_SIZE_32 = 6
    """Each object is preceded by its own size, encoded in 32 bits."""

    RESERVED = 7
    """Reserved for future use."""


class RangeSpecifierCode(enum.IntEnum):
    """
    Range Specifier Codes.

    Selects how this library encodes which objects a qualifier field
    addresses - as a start/stop index pair, a start/stop virtual-address
    pair, or a plain object count.
    (See DNP3 Specification, Section 4.2.2.7.3.3)
    """

    RANGE_8 = 0
    """Range field holds a pair of 1-octet start/stop index values."""

    RANGE_16 = 1
    """Range field holds a pair of 2-octet start/stop index values."""

    RANGE_32 = 2
    """Range field holds a pair of 4-octet start/stop index values."""

    RANGE_8_VIRTUAL = 3
    """Range field holds a pair of 1-octet start/stop virtual addresses."""

    RANGE_16_VIRTUAL = 4
    """Range field holds a pair of 2-octet start/stop virtual addresses."""

    RANGE_32_VIRTUAL = 5
    """Range field holds a pair of 4-octet start/stop virtual addresses."""

    NONE = 6
    """No range field follows; the request/response covers every value."""

    COUNT_8 = 7
    """Range field holds a single 1-octet object count instead of a
    start/stop pair."""

    COUNT_16 = 8
    """Range field holds a single 2-octet object count instead of a
    start/stop pair."""

    COUNT_32 = 9
    """Range field holds a single 4-octet object count instead of a
    start/stop pair."""

    VARIABLE = 11
    """Free-format qualifier whose range field is a single 1-octet object
    count."""


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
