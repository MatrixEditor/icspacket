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
from string import ascii_letters
from io import StringIO

#: Precomputed set of valid ASCII letter byte values.
#:
#: This constant contains the UTF-8 encoded byte values of all ASCII
#: alphabetic characters (`A–Z`, `a–z`). It is used by :func:`hexdump`
#: to determine whether a byte should be rendered as its literal character
#: or replaced with a placeholder (`.`) in the ASCII output column.
ascii_letters_bytes = set(ascii_letters.encode("utf-8"))


def hexdump(data: bytes, width: int = 16) -> str:
    """Return a formatted hexadecimal dump of raw byte data.

    This function produces a classic "hexdump"-style representation of
    binary data, consisting of three columns:

      1. **Offset column** - the byte offset of the line start, shown
         as an 8-digit hexadecimal number with leading zeros.
      2. **Hex column** - the raw bytes rendered as two-digit hexadecimal
         values separated by spaces.
      3. **ASCII column** - a human-readable view of printable characters
         corresponding to the data. Bytes that are not part of the ASCII
         alphabet (see :data:`ascii_letters_bytes`) are replaced with
         a dot (`.`).

    **This function is the most basic approach to dumping binary data.**

    :param data:
        The binary input buffer to be formatted.
    :type data: bytes

    :param width:
        The number of bytes to display per line. Defaults to ``16``.
        Each line will contain at most this many bytes, followed by
        the ASCII column.
    :type width: int, optional

    :return:
        A string containing the formatted hexdump, with newline
        terminators at the end of each row.
    :rtype: str

    :raises ValueError:
        If ``width`` is less than 1, the function cannot partition the data.

    **Example**::

        >>> data = b"Hello, MMS!"
        >>> print(hexdump(data, width=8))
        00000000:   48 65 6c 6c 6f 2c 20 4d   Hello,.M
        00000008:   4d 53 21                  MS!

    .. note::
        Unlike the standard UNIX ``hexdump`` tool, this implementation
        aligns the ASCII column strictly to the byte width, and considers
        only alphabetic ASCII characters as printable. Other values such as
        digits or symbols will be replaced with ``.``.
    """
    if width < 1:
        raise ValueError("hexdump width must be >= 1")

    windows_size = min(len(data), width)
    result = StringIO()
    for index in range(0, len(data), windows_size):
        offset = index * windows_size
        chunk = data[index : index + windows_size]

        chunk_hex = chunk.hex(sep=" ")
        chunk_ascii = [chr(b) if b in ascii_letters_bytes else "." for b in chunk]
        suffix = "".join(chunk_ascii)

        if len(chunk_ascii) < width:
            suffix = ("   " * (width - len(chunk_ascii))) + suffix
        _ = result.write(f"{offset:08x}:   {chunk_hex}   {suffix}\n")
    return result.getvalue()
