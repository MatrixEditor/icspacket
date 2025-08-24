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
from caterpillar.shortcuts import unpack, pack

from icspacket.proto.iso_ses.values import (
    PV_VersionNumber,
    PV_TokenSetting,
    PV_SessionRequirements,
    PV_EnclosureItem,
)


# ---------------------------------------------------------------------------
# PV TYPES TESTS
# ---------------------------------------------------------------------------
def test_pv_version_number_bits():
    pv = PV_VersionNumber(version1=True, version2=False)
    assert pv.version1 is True
    assert pv.version2 is False
    raw = pack(pv)
    pv2 = unpack(PV_VersionNumber, raw)
    assert pv2.version1 is True
    assert pv2.version2 is False


def test_pv_token_setting_pairs():
    pv = PV_TokenSetting(release=2, activity=1, sync=0, data=3)
    assert pv.release == 2
    assert pv.activity == 1
    assert pv.sync == 0
    assert pv.data == 3
    pv2 = unpack(PV_TokenSetting, pack(pv))
    assert pv2.release == 2


def test_pv_session_requirements_flags():
    pv = PV_SessionRequirements(expedited=True, duplex=True, half_duplex=False)
    assert pv.expedited
    assert pv.duplex
    raw = pack(pv)
    pv2 = unpack(PV_SessionRequirements, raw)
    assert pv2.duplex
    assert not pv2.half_duplex


def test_pv_enclosure_item_start_end():
    pv = PV_EnclosureItem(start=True, end=False)
    assert pv.start
    assert not pv.end
    pv2 = unpack(PV_EnclosureItem, pack(pv))
    assert pv2.start
