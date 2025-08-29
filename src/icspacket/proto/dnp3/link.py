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
import enum
import math

import crcmod.predefined

from caterpillar.shortcuts import this, struct, bitfield, LittleEndian
from caterpillar.fields import singleton, uint16, uint8
from caterpillar.model import EnumFactory, pack, unpack
from caterpillar.context import CTX_STREAM
from caterpillar.exception import ValidationError

from icspacket.proto.dnp3.application import APDU
from icspacket.proto.dnp3.transport import TPDU


Crc16DNP = crcmod.predefined.mkCrcFun("crc-16-dnp")

# The minimum header length (only header)
LPDU_HEADER_MIN_LENGTH = 5
"""Minimum number of bytes required to represent an LPDU header."""

# The maximum header length
LPDU_HEADER_MAX_LENGTH = 255
"""Maximum possible size of an LPDU header in bytes."""

# The maximum number of user data octets that a single frame can hold is 250
LPDU_USER_DATA_MAX_LENGTH = LPDU_HEADER_MAX_LENGTH - LPDU_HEADER_MIN_LENGTH
"""Maximum user data size (250 bytes) that a single LPDU can contain."""


class LinkDirection(enum.IntEnum):
    """
    Direction indicator bit for the DNP3 link layer (DIR field).

    (See DNP3 Specification, Section 9.2.4.1.3.1)
    """

    MASTER = 1
    """Indicates a frame sent from a Master device."""

    OUTSTATION = 0
    """Indicates a frame sent from an Outstation device."""


class LinkPrimaryFunctionCode(enum.IntEnum):
    """
    Primary-to-Secondary function codes for the Link Layer.

    These codes are valid when the PRM bit is set (PRM = 1).
    (See DNP3 Specification, Table 9-1)
    """

    RESET_LINK_STATES = 0
    """Reset link states."""

    TEST_LINK_STATES = 2
    """Test link states."""

    CONFIRMED_USER_DATA = 3
    """Confirmed user data transfer."""

    UNCONFIRMED_USER_DATA = 4
    """Unconfirmed user data transfer."""

    REQUEST_LINK_STATUS = 9
    """Request link status."""


class LinkSecondaryFunctionCode(enum.IntEnum):
    """
    Secondary-to-Primary function codes for the Link Layer.

    These codes are valid when the PRM bit is clear (PRM = 0).
    (See DNP3 Specification, Table 9-2)
    """

    ACK = 0
    """Acknowledgement."""

    NACK = 1
    """Negative acknowledgement."""

    LINK_STATUS = 11
    """Report link status."""

    NOT_SUPPORTED = 15
    """Function code not supported."""


@bitfield
class LinkControl:
    """
    Control field of the Link Layer Protocol Data Unit (LPDU).

    Stores metadata about the frame direction, initiator,
    error handling, and function code.
    (See DNP3 Specification, Section 9.2.4.1.3)
    """

    direction: (1, EnumFactory(LinkDirection)) = LinkDirection.MASTER
    """DIR bit. Indicates the physical origin of the frame (Master/Outstation)."""

    primary_message: 1 = False
    """PRM bit.

    - ``True`` :octicon:`arrow-right` Frame initiates a transaction.
    - ``False`` :octicon:`arrow-right` Frame completes a transaction.
    """

    frame_count_bit: 1 = False
    """FCB bit. Used in primary-to-secondary frames to detect loss or duplication."""

    frame_count_valid: 1 = False
    """FCV bit. Specifies whether the secondary station must examine the FCB."""

    function_code: 4 = 0
    """Function code field identifying the service or command type."""

    @property
    def data_flow_control(self) -> bool:
        """
        Report data flow availability (DFC bit).

        Indicates insufficient Data Link Layer buffer capacity.

        :return: ``True`` if buffer space is insufficient, ``False`` otherwise.
        :rtype: bool
        """
        return self.frame_count_valid

    @property
    def pri2sec_code(self) -> LinkPrimaryFunctionCode:
        """
        Interpret the function code for Primary-to-Secondary frames.

        :return: Link layer function code for PRM = 1.
        :rtype: LinkPrimaryFunctionCode
        """
        return LinkPrimaryFunctionCode(self.function_code)

    @property
    def sec2pri_code(self) -> LinkSecondaryFunctionCode:
        """
        Interpret the function code for Secondary-to-Primary frames.

        :return: Link layer function code for PRM = 0.
        :rtype: LinkSecondaryFunctionCode
        """
        return LinkSecondaryFunctionCode(self.function_code)


@singleton
class LinkUserData:
    """
    Encapsulates user data blocks inside an LPDU.

    Each block consists of up to 16 bytes of data followed by a 16-bit CRC.
    (See DNP3 Specification, Section 9.2.4.4)
    """

    def __type__(self):
        return bytes

    def __size__(self, context) -> int:
        """
        Calculate the size of the user data field.

        The size is determined at runtime based on the LPDU length field.

        :param context: Parsing context.
        :type context: dict
        :raises NotImplementedError: Always, since size is computed dynamically.
        """
        raise NotImplementedError

    def __unpack__(self, context):
        """
        Unpack and validate user data from the input stream.

        Reads the user data in chunks of up to 16 bytes,
        verifying each block against its CRC.

        :param context: Parsing context with active input stream.
        :type context: dict
        :raises ValueError: If a CRC mismatch is detected.
        :return: Reassembled TPDU from unpacked user data.
        :rtype: TPDU
        """
        length = this.length(context) - LPDU_HEADER_MIN_LENGTH
        user_data = bytearray()
        while length > 0:
            size = min(length, 16)
            chunk_data = context[CTX_STREAM].read(size)
            chunk_crc = uint16.__unpack__(context)
            expected_crc = Crc16DNP(chunk_data)
            if expected_crc != chunk_crc:
                raise ValidationError(
                    f"CRC error: expected {expected_crc}, got {chunk_crc}"
                )

            user_data.extend(chunk_data)
            length -= size

        return unpack(TPDU, bytes(user_data)) if user_data else None

    def __pack__(self, obj, context):
        """
        Pack user data into LPDU chunks with CRCs.

        Splits the data into 16-byte chunks, computes CRC for each,
        and writes them sequentially.

        :param obj: User data to pack (converted to bytes).
        :type obj: TPDU | bytes
        :param context: Output packing context with writable stream.
        :type context: dict
        """
        data = bytes(obj)
        length = len(data)
        while length > 0:
            size = min(length, 16)
            chunk_data, data = data[:size], data[size:]
            context[CTX_STREAM].write(chunk_data)
            uint16.__pack__(Crc16DNP(chunk_data), context)
            length -= size


@struct(order=LittleEndian)
class LPDU:
    """
    Link-layer Protocol Data Unit (LPDU).

    Each LPDU consists of a fixed header block and a variable-length
    sequence of data blocks, each terminated by a 16-bit CRC.
    (See DNP3 Specification, Section 9.2.4)
    """

    start: b"\x05\x64"
    """Sync bytes marking the start of every LPDU (0x05, 0x64)."""

    length: uint8 = 0
    """Length field.
    Number of non-CRC bytes following the header. Includes CONTROL,
    DESTINATION, SOURCE, and USER DATA fields."""

    control: LinkControl = None
    """Control field containing direction, function, and status flags."""

    destination: uint16 = 0
    """Destination address of the data link frame."""

    source: uint16 = 0
    """Source address of the data link frame."""

    crc16: uint16 = 0
    """CRC checksum for the LPDU header block."""

    user_data: LinkUserData = b""
    """Payload data field containing one or more user data chunks."""

    def __post_init__(self):
        self.control = self.control or LinkControl()

    def build(self) -> bytes:
        """
        Construct a serialized LPDU with correct length.

        :return: Encoded LPDU bytes.
        :rtype: bytes
        """
        self.length = LPDU_HEADER_MIN_LENGTH + len(bytes(self.user_data))
        self.crc16 = 0
        header_octets = pack(self)[:8]
        self.crc16 = Crc16DNP(header_octets)
        return pack(self)

    @staticmethod
    def full_length(length: int) -> int:
        base_length = 3  # +(start, length)
        base_length += 2  # +(crc of header)
        base_length += length
        # +(crc of user data)
        base_length += math.ceil((length - LPDU_HEADER_MIN_LENGTH) / 16) * 2
        return base_length

    def __bytes__(self):
        """
        Get the byte representation of the LPDU.

        :return: Encoded LPDU bytes.
        :rtype: bytes
        """
        return self.build()

    @staticmethod
    def from_octets(data: bytes) -> "LPDU":
        """
        Parse an LPDU from a raw byte sequence.

        .. versionchanged:: 0.2.0
            Renamed from ``from_bytes`` to ``from_octets``

        :param data: Encoded LPDU bytes.
        :type data: bytes
        :return: Decoded LPDU instance.
        :rtype: LPDU
        """
        return unpack(LPDU, data)

    @property
    def apdu(self) -> APDU:
        """
        Parse the APDU contained in the TPDU.
        """
        return self.user_data.apdu

    @property
    def tpdu(self) -> TPDU:
        """
        The TPDU contained in the LPDU.
        """
        return self.user_data
