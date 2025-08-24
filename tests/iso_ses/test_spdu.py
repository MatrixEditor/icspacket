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

from caterpillar.shortcuts import pack, unpack

from icspacket.proto.iso_ses.spdu import (
    SPDU,
    LI,
    LI_Extended,
    PGI_Code,
    Px_Unit,
    SPDU_Category,
    SPDU_Codes,
)
from icspacket.proto.iso_ses.tsdu import TSDU
from icspacket.proto.iso_ses.values import PI_Code, PV_EnclosureItem


# ---------------------------------------------------------------------------
# LI FIELD TESTS
# ---------------------------------------------------------------------------
def test_li_single_octet():
    li = LI(extended=False)
    buf = pack(42, li)
    assert buf == bytes([42])
    assert unpack(li, buf) == 42
    assert LI.octet_size(42) == 1


def test_li_extended_octet():
    # Value > 254 should trigger 3-octet encoding
    value = 300
    buf = pack(value, LI_Extended)
    # First octet should be 0xFF, followed by big-endian length
    assert buf[0] == 0xFF
    assert unpack(LI_Extended, buf) == value
    assert LI.octet_size(value) == 3


# ---------------------------------------------------------------------------
# SPDU TESTS
# ---------------------------------------------------------------------------
def test_spdu_basic_encoding_decoding():
    spdu = SPDU(SPDU_Codes.CONNECT_SPDU, category=SPDU_Category.CATEGORY_1)
    spdu.parameters.clear()
    built = spdu.build()
    spdu2 = SPDU.from_octets(built, category=SPDU_Category.CATEGORY_1)
    assert spdu2.code == SPDU_Codes.CONNECT_SPDU


def test_spdu_user_information_detection():
    spdu = SPDU(SPDU_Codes.DATA_TRANSFER_SPDU)
    spdu.user_information = b"hello"
    assert spdu.has_user_information
    built = spdu.build()
    parsed = SPDU.from_octets(built)
    assert parsed.user_information == b"hello"


def test_spdu_with_enclosure_item_suppresses_user_info():
    # Add Enclosure Item with bit 2 set (0x02)
    spdu = SPDU(SPDU_Codes.DATA_TRANSFER_SPDU)
    enclosure_pi = Px_Unit(pi=PI_Code.ENCLOSUREITEM, value=PV_EnclosureItem(end=True))
    spdu.parameters.append(enclosure_pi)
    assert not spdu.has_user_information


def test_parse_accept_sdpu():
    data = bytes.fromhex(
        "0e8505061301001601021402000034020001c1733171a003800101a26a830400000001a5123007800100"
        + "81025101300780010081025101614e304c020101a0476145a107060528ca220203a203020100a305a1"
        + "03020100be2e282c020103a027a9258002053981010582010583010aa416800101810305f100820c03"
        + "ee1c000000000000000118"
    )
    tsdu = TSDU.from_octets(data)
    assert len(tsdu.spdus) == 1  # one ACCEPT SPDU

    spdu = tsdu.spdus[0]
    assert spdu.code == SPDU_Codes.ACCEPT_SPDU
    assert len(spdu.user_information) == 0
    assert len(spdu.parameter_by_id(PGI_Code.USER_DATA).value) != 0
