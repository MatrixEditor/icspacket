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

from icspacket.proto.iec61850.classes import FC, LN_Class, LN_Group
from icspacket.proto.iec61850.path import DataObjectReference, ObjectReference


# ---------------------------------------------------------------------------
# ObjectReference
# ---------------------------------------------------------------------------
def test_iecref_ld():
    ref = ObjectReference.from_mmsref("beagleGenericIO")
    assert ref.ldname == "beagleGenericIO"
    assert ref.lnname is None
    assert str(ref) == "beagleGenericIO"
    assert repr(ref) == repr("beagleGenericIO")


def test_iecref_ln():
    ref = ObjectReference.from_mmsref("beagleGenericIO/LLN0")
    assert ref.ldname == "beagleGenericIO"
    assert ref.lnname == "LLN0"
    assert ref.lnclass == LN_Class.LLN0
    assert ref.lngroup == LN_Group.L


def test_iecref_build_ln():
    ref = ObjectReference("beagleGenericIO") / "LLN0"
    assert ref.ldname == "beagleGenericIO"
    assert ref.lnname == "LLN0"
    assert ref.lnclass == LN_Class.LLN0
    assert ref.lngroup == LN_Group.L


def test_iecref_ln_functional_constraint():
    ref = DataObjectReference.from_mmsref("beagleGenericIO/LLN0$MX")
    assert ref.ldname == "beagleGenericIO"
    assert ref.lnname == "LLN0"
    assert ref.lnclass == LN_Class.LLN0
    assert ref.lngroup == LN_Group.L
    assert ref.functional_constraint == FC.MX
    assert ref.mmsref == "beagleGenericIO/LLN0$MX"


def test_iecref_ln_data():
    ref = DataObjectReference.from_mmsref(
        "beagleGenericIO/GGIO_FSCC1$SP$Schd2$setSrcRef"
    )
    assert ref.ldname == "beagleGenericIO"
    assert ref.lnname == "GGIO_FSCC1"
    assert ref.lnclass == LN_Class.GGIO
    assert ref.functional_constraint == FC.SP
    assert ref.name(0) == "Schd2"
