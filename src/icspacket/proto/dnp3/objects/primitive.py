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
Primitive data types and bit string representations used in the DNP3 object library.

This module defines the canonical mappings between DNP3's primitive object
types and Python equivalents (e.g., UINT8, INT32, FLT32). It also includes
implementations for bit string objects (BSTRn, DBSTRn) as described in
section 11.3.3 of the DNP3 specification.

Two kinds of bit string encodings are implemented:

- **BSTRn**: Packed bit strings, where each bit represents a boolean value.
- **DBSTRn**: Double-bit strings, where each pair of bits encodes a
  double-bit state (used, for example, to represent binary inputs with
  intermediate states).

.. note::

    These types are used internally by the unpacking and packing mechanisms
    when parsing or constructing DNP3 Application Layer objects.
"""

# 11.3 Primitive data types
import datetime
from io import BytesIO, StringIO
import math
import bitarray
from caterpillar.byteorder import LittleEndian
from caterpillar.context import CTX_STREAM
from caterpillar.fields import (
    Bytes,
    String,
    Transformer,
    UInt,
    float32,
    float64,
    int16,
    int32,
    singleton,
    uint16,
    uint24,
    uint32,
    uint8,
)
from caterpillar.shortcuts import G


UINT8 = uint8
"""8-bit unsigned integer."""

UINT16 = uint16
"""16-bit unsigned integer."""

UINT24 = uint24
"""24-bit unsigned integer."""

UINT32 = uint32
"""32-bit unsigned integer."""

INT16 = int16
"""16-bit signed integer."""

INT32 = int32
"""32-bit signed integer."""

VSTR = String
"""Variable-length string."""

OSTR = Bytes
"""Octet string (arbitrary-length byte sequence)."""

FLT32 = float32
"""32-bit IEEE-754 floating point."""

FLT64 = float64
"""64-bit IEEE-754 floating point."""


@singleton
class DNP3TIME(Transformer):
    """48-bit DNP3 timestamp type.

    This type represents a DNP3-compliant timestamp using a 48-bit unsigned
    integer. The timestamp is encoded as the number of **milliseconds since
    the Unix epoch (1970-01-01 00:00:00 UTC)**.

    It provides automatic conversion between the raw integer form and a
    :class:`datetime.datetime` object when decoding, while encoding supports
    either integer millisecond values or datetime objects.
    """

    def __init__(self) -> None:
        super().__init__(LittleEndian + UInt(48))

    def decode(self, parsed: int, context) -> datetime.datetime | int:
        """Decode a 48-bit integer timestamp into a datetime object.

        :param parsed: The parsed integer value representing milliseconds
            since the Unix epoch.
        :type parsed: int
        :param context: Transformation context (unused in this implementation).
        :type context: Any
        :return: A :class:`datetime.datetime` object if the value is within
            the valid timestamp range, otherwise the raw integer value.
        :rtype: datetime.datetime | int
        """
        try:
            return datetime.datetime.fromtimestamp(parsed / 1000)
        except ValueError:
            return parsed

    def encode(self, obj: int | datetime.datetime, context) -> int:
        """Encode a datetime object or integer into a 48-bit millisecond value.

        :param obj: The timestamp to encode, either as a datetime or an integer
            number of milliseconds since the Unix epoch.
        :type obj: int | datetime.datetime
        :param context: Transformation context (unused in this implementation).
        :type context: Any
        :return: The encoded timestamp as an integer in milliseconds.
        :rtype: int
        """
        if isinstance(obj, datetime.datetime):
            obj = int(obj.timestamp()) * 1000
        return int(obj)


class BCD(Transformer):
    """Binary-coded decimal (BCD) type.

    Implements DNP3 section 11.3.6: *Binary-coded decimal values use the notation
    BCDn, where ``n`` represents the number of BCD characters. For example,
    ``BCD8`` requires 8 BCD characters.*

    Each BCD character is stored in 4 bits (a nibble). Two characters are packed
    into a single byte in little-endian order.
    """

    def __init__(self, count: int) -> None:
        """Decode BCD bytes into a string of decimal digits.

        :param parsed: Encoded binary-coded decimal bytes.
        :type parsed: bytes
        :param context: Transformation context (unused in this implementation).
        :type context: Any
        :return: The decoded decimal string, e.g. "1234".
        :rtype: str
        """
        # Each BCD character requires 4 bits
        super().__init__(Bytes(count / 2))

    def decode(self, parsed: bytes, context) -> str:
        """Encode a string of decimal digits into BCD bytes.

        :param obj: The decimal string to encode. A '-' character may be used
            to represent a nibble value of 10.
        :type obj: str
        :param context: Transformation context (unused in this implementation).
        :type context: Any
        :return: Encoded BCD bytes.
        :rtype: bytes
        """
        string = StringIO()
        for byte in parsed:
            # because of little endian encoding
            low_number = (byte & 0b11110000) >> 4
            high_number = byte & 0b00001111
            if high_number >= 10:
                _ = string.write("-")
            else:
                _ = string.write(str(high_number))
            _ = string.write(str(low_number))
        return string.getvalue()

    def encode(self, obj: str, context) -> bytes:
        packed = BytesIO()
        for i in range(0, len(obj), 2):
            low_number_str = obj[i]
            high_number_str = obj[i + 1]
            if high_number_str == "-":
                high_number = 10
            else:
                high_number = int(high_number_str)
            low_number = int(low_number_str)
            _ = packed.write(high_number | low_number << 4)

        return packed.getvalue()


class BSTRn:
    """Packed bit string (BSTRn) representation.

    This class implements the parsing and serialization of packed bit
    strings used in DNP3 objects. Each bit encodes a boolean value,
    with the least significant bit occupying the lowest bit position
    in a field.

    For example, a 10-bit bit string will be encoded into 2 octets.
    When unpacked, it is represented as a :class:`bitarray.bitarray`
    with little-endian ordering.
    """

    def count(self, obj: bitarray.bitarray) -> int:
        """Return the number of bits in the given bit string.

        :param obj: The bit string.
        :type obj: bitarray.bitarray
        :return: The number of bits.
        :rtype: int
        """
        return len(obj)

    def __size__(self, context) -> int:
        """Compute the number of octets required to represent the bit string.

        :param context: Serialization context containing range information.
        :type context: dict
        :return: The number of octets needed.
        :rtype: int
        """
        count: int = G.range_count(context)
        return math.ceil(count / 8)

    def __type__(self) -> type:
        """Return the Python type used to represent this value.

        :return: :class:`bitarray.bitarray`
        :rtype: type
        """
        return bitarray.bitarray

    def __call__(self, *args, **kwargs) -> bitarray.bitarray:
        """Construct a new empty bit string.

        :return: A new empty bitarray.
        :rtype: bitarray.bitarray
        """
        return bitarray.bitarray()

    def __unpack__(self, context):
        """Unpack a packed bit string from the stream.

        The least significant bit of the string is placed at the
        lowest position within the field.

        :param context: Serialization context containing the input stream.
        :type context: dict
        :return: A list of unpacked bit values (0 or 1).
        :rtype: list[int]
        """
        obj = context[CTX_STREAM].read(self.__size__(context))
        packed_values = bitarray.bitarray(obj, endian="little")
        return packed_values.tolist()

    def __pack__(self, obj: bitarray.bitarray | bytes | list[int], context) -> None:
        """Pack a bit string into the stream.

        :param obj: The bit string to pack. Can be a :class:`bitarray.bitarray`,
            a raw byte string, or a list of bits.
        :type obj: bitarray.bitarray | bytes | list[int]
        :param context: Serialization context containing the output stream.
        :type context: dict
        :raises ValueError: If an integer is provided (unsupported).
        """
        if isinstance(obj, int):
            raise ValueError("BSTRn cannot be packed from an int")

        if isinstance(obj, list):
            obj = bitarray.bitarray(obj, endian="little")

        if isinstance(obj, bitarray.bitarray):
            obj = obj.tobytes()

        context[CTX_STREAM].write(obj)


class DBSTRn:
    """Double-bit string (DBSTRn) representation.

    This class implements parsing and serialization of double-bit
    strings, where each pair of bits encodes a state. For example:

    - ``00`` → intermediate or indeterminate state
    - ``01`` → determined OFF
    - ``10`` → determined ON
    - ``11`` → reserved

    Each octet encodes four double-bit values.

    Internally, unpacked values are represented as lists of integers.
    """

    def __size__(self, context) -> int:
        """Compute the number of octets required to represent the double-bit string.

        :param context: Serialization context containing range information.
        :type context: dict
        :return: The number of octets needed.
        :rtype: int
        """
        count: int = G.range_count(context)
        return math.ceil(count / 4)

    def count(self, obj: list[int]) -> int:
        """Return the number of double-bit values in the list.

        :param obj: List of double-bit values.
        :type obj: list[int]
        :return: The number of double-bit values.
        :rtype: int
        """
        return len(obj) * 2

    def __type__(self) -> type:
        """Return the Python type used to represent this value.

        :return: :class:`list`
        :rtype: type
        """
        return list

    def __call__(self, *args, **kwds) -> list[int]:
        """Construct a new empty double-bit string.

        :return: An empty list.
        :rtype: list[int]
        """
        return []

    def __unpack__(self, context):
        """Unpack a double-bit string from the stream.

        :param context: Serialization context containing the input stream.
        :type context: dict
        :return: A list of integer double-bit values.
        :rtype: list[int]
        """
        obj = context[CTX_STREAM].read(self.__size__(context))
        packed_values = bitarray.bitarray(obj, endian="little")
        return [
            int(packed_values[i : i + 2], 2) for i in range(0, len(packed_values), 2)
        ]

    def __pack__(self, obj: list[int] | bitarray.bitarray | bytes, context) -> None:
        """Pack a double-bit string into the stream.

        :param obj: The double-bit string to pack. Can be a list of integers,
            a :class:`bitarray.bitarray`, or a raw byte string.
        :type obj: list[int] | bitarray.bitarray | bytes
        :param context: Serialization context containing the output stream.
        :type context: dict
        :raises ValueError: If an integer is provided (unsupported).
        """
        if isinstance(obj, int):
            raise ValueError("DBSTRn cannot be packed from an int")

        if isinstance(obj, list):
            obj = bitarray.bitarray(self.count(obj), endian="little")
            for i in range(0, len(obj), 2):
                obj[i : i + 2] = bitarray.bitarray(format(obj[i : i + 2], "02b"))

        if isinstance(obj, bitarray.bitarray):
            obj = obj.tobytes()

        context[CTX_STREAM].write(obj)
