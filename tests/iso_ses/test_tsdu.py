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

from icspacket.proto.iso_ses.tsdu import TSDU
from icspacket.proto.iso_ses.spdu import SPDU, SPDU_Category, SPDU_Codes

# ---------------------------------------------------------------------------
# TSDU TESTS
# ---------------------------------------------------------------------------

def test_tsdu_concatenation():
    cat0 = SPDU(SPDU_Codes.GIVE_TOKENS_SPDU, category=SPDU_Category.CATEGORY_0)
    cat2 = SPDU(SPDU_Codes.DATA_TRANSFER_SPDU)
    cat2.user_information = b"x"
    tsdu = TSDU()
    tsdu.spdus.append(cat0)
    tsdu.spdus.append(cat2)
    built = tsdu.build()
    parsed_tsdu = TSDU.from_octets(built)
    assert parsed_tsdu.spdus[0].category == SPDU_Category.CATEGORY_0
    assert parsed_tsdu.spdus[1].category == SPDU_Category.CATEGORY_2
    assert parsed_tsdu.spdus[1].user_information == b"x"

def test_tsdu_invalid_category0_length():
    # Category 0 SPDU with LI != 0 should fail
    cat0_raw = bytes([SPDU_Codes.GIVE_TOKENS_SPDU, 1, 0x00])
    with pytest.raises(ValueError):
        TSDU.from_octets(cat0_raw)