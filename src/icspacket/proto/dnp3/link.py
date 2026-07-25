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
import math
from collections.abc import Callable

import crcmod.predefined
from caterpillar.abc import _ContextLike
from caterpillar.context import CTX_STREAM
from caterpillar.exception import ValidationError
from caterpillar.py import (
    EnumFactory,
    Invisible,
    LittleEndian,
    bitfield,
    f,
    pack,
    singleton,
    struct,
    this,
    uint16,
    unpack,
)
from caterpillar.types import uint8_t, uint16_t

from icspacket.proto.dnp3.application import APDU
from icspacket.proto.dnp3.transport import TPDU

Crc16DNP: Callable[[bytes], int] = crcmod.predefined.mkCrcFun("crc-16-dnp")

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
    Values for the DNP3 link layer's direction bit (DIR field), used by this
    library to tag which kind of station produced a frame.

    (See DNP3 Specification, Section 9.2.4.1.3.1)
    """

    MASTER = 1
    """Marks a frame as originating from a Master device."""

    OUTSTATION = 0
    """Marks a frame as originating from an Outstation device."""


class LinkPrimaryFunctionCode(enum.IntEnum):
    """
    Function codes this library uses for frames traveling from a primary
    station to a secondary station.

    These codes are valid when the PRM bit is set (PRM = 1).
    (See DNP3 Specification, Table 9-1)
    """

    RESET_LINK_STATES = 0
    """Resets the secondary station's link-layer state."""

    TEST_LINK_STATES = 2
    """Tests whether the secondary station's link layer is still responsive."""

    CONFIRMED_USER_DATA = 3
    """Carries user data that the secondary station must acknowledge."""

    UNCONFIRMED_USER_DATA = 4
    """Carries user data that does not require an acknowledgement."""

    REQUEST_LINK_STATUS = 9
    """Asks the secondary station to report its current link status."""


class LinkSecondaryFunctionCode(enum.IntEnum):
    """
    Function codes this library uses for frames traveling from a secondary
    station back to a primary station.

    These codes are valid when the PRM bit is clear (PRM = 0).
    (See DNP3 Specification, Table 9-2)
    """

    ACK = 0
    """Confirms that the previous frame from the primary station was accepted."""

    NACK = 1
    """Reports that the previous frame from the primary station was rejected."""

    LINK_STATUS = 11
    """Carries the secondary station's answer to a `REQUEST_LINK_STATUS` query."""

    NOT_SUPPORTED = 15
    """Tells the primary station that the requested link function code is
    not implemented."""


@bitfield
class LinkControl:
    """
    This bitfield models the LPDU's control octet, exposing a frame's
    direction, transaction role, retry-detection flags, and function code
    as individual attributes instead of raw bits.
    (See DNP3 Specification, Section 9.2.4.1.3)
    """

    direction: f[LinkDirection | int, (1, EnumFactory(LinkDirection))] = (
        LinkDirection.MASTER
    )
    """DIR bit. Records which kind of station - Master or Outstation -
    originated the frame."""

    primary_message: f[bool, 1] = False
    """PRM bit.

    - ``True`` :octicon:`arrow-right` This frame opens a new transaction.
    - ``False`` :octicon:`arrow-right` This frame completes an existing transaction.
    """

    frame_count_bit: f[bool, 1] = False
    """FCB bit. Toggled on primary-to-secondary frames so the secondary
    station can detect lost or duplicated frames."""

    frame_count_valid: f[bool, 1] = False
    """FCV bit. Tells the secondary station whether it should pay attention
    to the FCB carried in this frame."""

    function_code: f[int, 4] = 0
    """Raw 4-bit function code; decode it with :attr:`pri2sec_code` or
    :attr:`sec2pri_code` depending on whether this is a primary or
    secondary frame."""

    @property
    def data_flow_control(self) -> bool:
        """
        Expose the DFC bit as a boolean.

        A ``True`` value signals that the sending station's Data Link
        Layer receive buffer has too little free space to accept more data.

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
    Handles the variable-length user-data portion of an LPDU during
    (de)serialization: this library reads and writes it in blocks of up to
    16 payload bytes, each immediately followed by its own 16-bit CRC.
    (See DNP3 Specification, Section 9.2.4.4)
    """

    def __type__(self):
        return bytes

    def __size__(self, context: _ContextLike) -> int:
        """
        Calculate the size of the user data field.

        The size is determined at runtime based on the LPDU length field.

        :param context: Parsing context.
        :type context: dict
        :raises NotImplementedError: Always, since size is computed dynamically.
        """
        raise NotImplementedError

    def __unpack__(self, context: _ContextLike) -> TPDU | None:
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
        length: int = this.length(context) - LPDU_HEADER_MIN_LENGTH
        user_data = bytearray()
        while length > 0:
            size = min(length, 16)
            chunk_data: bytes = context[CTX_STREAM].read(size)
            chunk_crc = uint16.__unpack__(context)
            expected_crc = Crc16DNP(chunk_data)
            if expected_crc != chunk_crc:
                raise ValidationError(
                    f"CRC error: expected {expected_crc}, got {chunk_crc}"
                )

            user_data.extend(chunk_data)
            length -= size

        return unpack(TPDU, bytes(user_data)) if user_data else None

    def __pack__(self, obj: TPDU | None, context: _ContextLike):
        """
        Pack user data into LPDU chunks with CRCs.

        Splits the data into 16-byte chunks, computes CRC for each,
        and writes them sequentially.

        :param obj: User data to pack (converted to bytes).
        :type obj: TPDU | bytes
        :param context: Output packing context with writable stream.
        :type context: dict
        """
        if obj is not None:
            data = bytes(obj)
            length = len(data)
            while length > 0:
                size = min(length, 16)
                chunk_data, data = data[:size], data[size:]
                context[CTX_STREAM].write(chunk_data)
                uint16.__pack__(Crc16DNP(chunk_data), context)
                length -= size


@struct(order=LittleEndian, kw_only=True)
class LPDU:
    """
    Link-layer Protocol Data Unit (LPDU).

    This struct models a complete LPDU as a fixed-size header followed by
    zero or more variable-length data blocks, each one closed off with its
    own 16-bit CRC.
    (See DNP3 Specification, Section 9.2.4)
    """

    start: f[bytes, b"\x05\x64"] = Invisible()
    """Fixed two-byte sync sequence (0x05, 0x64) at the start of every LPDU."""

    length: uint8_t = 0
    """Length field: count of the non-CRC bytes that follow it, spanning the
    CONTROL, DESTINATION, SOURCE, and USER DATA fields."""

    control: LinkControl = None  # pyright: ignore[reportAssignmentType]
    """Control octet for the frame, modeled by :class:`LinkControl`, holding
    the direction, function code, and status flags."""

    destination: uint16_t = 0
    """Address of the data-link frame's destination station."""

    source: uint16_t = 0
    """Address of the data-link frame's source station."""

    crc16: uint16_t = 0
    """Checksum protecting the LPDU header block."""

    user_data: f[TPDU | None, LinkUserData] = None
    """The frame's payload, held as one or more user-data chunks via
    :class:`LinkUserData`."""

    def __post_init__(self):
        self.control = self.control or LinkControl()

    def build(self) -> bytes:
        """
        Construct a serialized LPDU with correct length.

        :return: Encoded LPDU bytes.
        :rtype: bytes
        """
        self.length = LPDU_HEADER_MIN_LENGTH + len(bytes(self.user_data or b""))
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
        return self.tpdu.apdu

    @property
    def tpdu(self) -> TPDU:
        """
        The TPDU contained in the LPDU.
        """
        if self.user_data is None:
            raise ValueError("LPDU does not store a TPDU")

        return self.user_data
