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
from dataclasses import dataclass
import datetime
import enum

from typing import Any, Literal
from caterpillar.fields import (
    DEFAULT_OPTION,
    Bytes,
    double,
    float32,
    uint8,
    uint64,
)
from caterpillar.model import bitfield, struct
from caterpillar.options import S_ADD_BYTES
from caterpillar.shortcuts import pack, unpack, BigEndian, F, this

from icspacket.proto.mms._mms import Data, FileAttributes, UtcTime
from icspacket.proto.mms.asn1types import FloatingPoint

_be_uint64 = BigEndian + uint64


class IEEE754Type(enum.IntEnum):
    """
    Enumeration representing supported IEEE 754 floating-point formats.

    The enumeration values encode the bit-width of the **exponent field**
    used in the floating-point representation. This width determines
    whether the format corresponds to a 32-bit or 64-bit IEEE 754 float.
    """

    __struct__ = uint8

    FLOAT32 = 8
    """ Single-precision floating-point type (8-bit exponent width)."""

    FLOAT64 = 11
    """Double-precision floating-point type (11-bit exponent width)."""


#: Mapping between IEEE754 exponent widths and their corresponding
#: serialization/deserialization strategies.
#: If no matching type is found, a byte sequence fallback is used.
_IEEE754_TYPES = {
    IEEE754Type.FLOAT32: BigEndian + float32,
    IEEE754Type.FLOAT64: BigEndian + double,
    # Fallback mechanism: default to raw byte representation
    DEFAULT_OPTION: Bytes(...),
}


@struct
class IEEE754PackedFloat:
    """
    Structured representation of a floating-point value encoded in IEEE 754
    format.

    This structure encapsulates both the **exponent width** (to distinguish
    between 32-bit and 64-bit IEEE 754 floating-point values) and the
    associated binary-encoded value.
    """

    exponent_width: IEEE754Type = IEEE754Type.FLOAT32
    """
    The exponent width that determines the floating-point format (either
    ``FLOAT32`` or ``FLOAT64``). Defaults to ``FLOAT32``.
    """

    value: F(this.exponent_width) >> _IEEE754_TYPES = 0
    """
    The floating-point value encoded according to the specified exponent width.
    If the width is not recognized, the raw bytes are stored instead.
    """


def create_floating_point_value(
    value: float, exp_width: Literal[8, 11] | None = None
) -> FloatingPoint:
    """Create a packed IEEE 754 floating-point representation.

    This function encodes a Python ``float`` into a binary representation
    according to the IEEE 754 standard. The precision of the representation
    is determined by the chosen exponent width.

    :param value: The Python floating-point value to be encoded.
    :type value: float
    :param exp_width: he exponent width specifying the IEEE 754 format, defaults
        to None
    :type exp_width: Literal[8, 11] | None, optional
    :return:  A wrapped binary representation of the floating-point value
         encoded in the specified IEEE 754 format.
    :rtype: FloatingPoint
    """
    packed_value = IEEE754PackedFloat(exp_width or IEEE754Type.FLOAT32, value)
    data = pack(packed_value)
    return FloatingPoint(data)


def get_floating_point_value(fp: FloatingPoint | bytes) -> float:
    """
    Decode a packed IEEE 754 floating-point value into a Python float.

    Example:

    >>> fp = FloatingPoint(b'\\x08Cb\\x00\\x00')
    >>> get_floating_point_value(fp)
    226.0

    :param fp: A :class:`FloatingPoint` object containing the encoded IEEE 754
        value or raw bytes.
    :type fp: FloatingPoint
    :return: The decoded Python floating-point value.
    :rtype: float
    :raises TypeError: If the exponent width does not match a recognized IEEE
        754 type (``FLOAT32`` or ``FLOAT64``).
    """
    value = fp.value if not isinstance(fp, bytes) else fp
    unpacked = unpack(IEEE754PackedFloat, value)
    if isinstance(unpacked.value, bytes):
        raise TypeError(f"Unknown exponent width: {unpacked.exponent_width}")

    return unpacked.value


@bitfield(order=BigEndian, options=[S_ADD_BYTES])
class Timestamp:
    """Structured bitfield representation of a timestamp value.

    .. versionadded:: 0.2.3
    """

    timeval: Bytes(4) = bytes(4)
    """4-byte unsigned integer representing the elapsed time in seconds."""

    fraction: Bytes(3) = bytes(3)
    """3-byte fractional component of the timestamp for sub-second precision."""

    leap_second_known: 1 = False
    """Indicates whether the occurrence of leap seconds is known."""

    clock_failure: 1 = False
    """Indicates whether a clock failure has been detected."""

    clock_not_synced: 1 = False
    """Indicates whether the clock is currently unsynchronized."""

    accuracy: 5 = 0
    """5-bit field encoding the accuracy of the timestamp."""

    @staticmethod
    def from_utc_time(utc_time: "UtcTime | bytes") -> "Timestamp":
        """
        Construct a :class:`Timestamp` object from a UTC time value.

        :param utc_time:
            Either a :class:`UtcTime` instance or an 8-byte raw buffer
            containing the encoded UTC time.
        :type utc_time: UtcTime | bytes
        :return: A deserialized :class:`Timestamp` instance.
        :rtype: Timestamp
        :raises ValueError:
            If the provided value does not have the expected 8-byte length.
        """
        value = utc_time.value if not isinstance(utc_time, bytes) else utc_time
        if len(value) != 8:
            raise ValueError(f"Invalid UTC time value: {value}")

        return unpack(Timestamp, value)

    @property
    def seconds(self) -> int:
        """
        Get the integral number of seconds stored in the timestamp.

        This property interprets the 4-byte ``timeval`` field as an
        unsigned 32-bit big-endian integer.

        :return: The number of elapsed seconds.
        :rtype: int
        """
        data: bytes = self.timeval
        return data[0] * (2**24) + data[1] * (2**16) + data[2] * (2**8) + data[3]

    @seconds.setter
    def seconds(self, value: int):
        """
        Set the integral number of seconds in the timestamp.

        The provided integer value is encoded into the 4-byte ``timeval``
        field using big-endian ordering. The fractional part is reset to
        zero whenever this setter is invoked.

        :param int value:
            The number of elapsed seconds to encode into the timestamp.
        """
        data = bytearray(4)
        data[0] = int((value / (2**24))) & 0xFF
        data[1] = int((value / (2**16))) & 0xFF
        data[2] = int((value / (2**8))) & 0xFF
        data[3] = value & 0xFF

        self.timeval = bytes(data)
        self.fraction = bytes(3)

    @property
    def datetime(self) -> datetime.datetime:
        """
        Get a :class:`datetime.datetime` object representing the timestamp.

        :return: A :class:`datetime.datetime` object representing the
            timestamp.
        :rtype: datetime.datetime
        """
        return datetime.datetime.fromtimestamp(self.seconds)


@dataclass(frozen=True)
class FileHandle:
    """Simple representation of an open file handle"""

    handle: int
    attributes: FileAttributes
