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

from icspacket.proto.tpkt import TPKT


def test_rfc1006_init():
    # TPKT consists of two parts: a packet-header and a TPDU. The format of the
    # header is constant regardless of the type of packet.
    tpkt = TPKT()

    # The version number MUST be set to 3
    assert tpkt.vrsn == 3


def test_rfc1006_pack():
    tpkt = TPKT()
    tpkt.tpdu = bytes(list(range(10)))

    packed_data = b"\x03\x00\x00\x0e\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
    assert tpkt.build() == packed_data


def test_rfc1006_unpack():
    packed_data = b"\x03\x00\x00\x0e\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"

    tpkt = TPKT.from_octets(packed_data)
    assert tpkt.tpdu == bytes(list(range(10)))


def test_rfc1006_invalid_length():
    packed_data = b"\x03\x00\x00\xff\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
    with pytest.raises(ValueError):
        tpkt = TPKT.from_octets(packed_data)
