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
import pytest

from icspacket.core.hexdump import hexdump


def test_empty_data():
    assert hexdump(b"") == ""


def test_default_width():
    assert hexdump(bytes(range(16))) == (
        "00000000:   00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f   ................\n"
    )


def test_single_line():
    assert hexdump(b"abcABC012") == (
        "00000000:   61 62 63 41 42 43 30 31 32                        abcABC...\n"
    )


def test_multiline_offsets():
    result = hexdump(bytes(range(48)))
    assert result == (
        "00000000:   00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f   ................\n"
        "00000010:   10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f   ................\n"
        "00000020:   20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f   ................\n"
    )


def test_short_last_line():
    result = hexdump(bytes(range(20)))
    assert result == (
        "00000000:   00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f   ................\n"
        "00000010:   10 11 12 13                                       ....\n"
    )


def test_ascii_column():
    data = bytes(
        [ord("a"), ord("Z"), ord("0"), ord(" "), ord("."), 0x00, 0xFF, ord("!"), 0x7F]
    )
    assert hexdump(data) == (
        "00000000:   61 5a 30 20 2e 00 ff 21 7f                        aZ.......\n"
    )


def test_custom_width():
    result = hexdump(bytes(range(20)), width=8)
    assert result == (
        "00000000:   00 01 02 03 04 05 06 07   ........\n"
        "00000008:   08 09 0a 0b 0c 0d 0e 0f   ........\n"
        "00000010:   10 11 12 13               ....\n"
    )


@pytest.mark.parametrize("width", [0, -1, -16])
def test_rejects_bad_width(width: int):
    with pytest.raises(ValueError):
        _ = hexdump(b"abc", width=width)
