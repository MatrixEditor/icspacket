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

from icspacket.proto.iec104.apci import APCI
from icspacket.proto.iec104.asdu import ASDU, ASDU_Header
from icspacket.proto.iec104.const import (
    APCIFormat,
    CauseOfTransmission,
    TypeID,
    UFormatFunction,
)
from icspacket.proto.iec104.objects import coding, information
from icspacket.proto.iec104.objects.coding import InformationObject
from icspacket.proto.iec104.objects.elements import (
    SIQ,
)


# ---------------------------------------------------------------------------
# APCI framing
# ---------------------------------------------------------------------------
def test_apci_startdt_act():
    apci = APCI.startdt_act()
    assert apci.to_bytes() == bytes.fromhex("680407000000")

    parsed = APCI.from_bytes(bytes.fromhex("680407000000"))
    assert parsed.format == APCIFormat.U_FORMAT
    assert parsed.control.function == UFormatFunction.STARTDT_ACT


def test_apci_startdt_con():
    apci = APCI.startdt_con()
    assert apci.to_bytes() == bytes.fromhex("68040b000000")

    parsed = APCI.from_bytes(bytes.fromhex("68040b000000"))
    assert parsed.format == APCIFormat.U_FORMAT
    assert parsed.control.function == UFormatFunction.STARTDT_CON


@pytest.mark.parametrize(
    "function",
    [
        UFormatFunction.STARTDT_ACT,
        UFormatFunction.STARTDT_CON,
        UFormatFunction.STOPDT_ACT,
        UFormatFunction.STOPDT_CON,
        UFormatFunction.TESTFR_ACT,
        UFormatFunction.TESTFR_CON,
    ],
)
def test_apci_u_format(function):
    apci = APCI.u_format(function)
    data = apci.to_bytes()
    assert len(data) == 6  # start + length + 4 control octets, no ASDU

    parsed = APCI.from_bytes(data)
    assert parsed.format == APCIFormat.U_FORMAT
    assert parsed.control.function == function
    assert parsed.to_bytes() == data


def test_apci_i_format():
    payload = b"\x01\x02\x03"
    apci = APCI.i_format(send_seq=5, recv_seq=7, asdu=payload)
    data = apci.to_bytes()

    parsed = APCI.from_bytes(data)
    assert parsed.format == APCIFormat.I_FORMAT
    assert parsed.control.send_seq == 5
    assert parsed.control.recv_seq == 7
    assert parsed.asdu == payload
    assert parsed.to_bytes() == data


def test_apci_s_format():
    apci = APCI.s_format(recv_seq=42)
    data = apci.to_bytes()

    parsed = APCI.from_bytes(data)
    assert parsed.format == APCIFormat.S_FORMAT
    assert parsed.control.recv_seq == 42
    assert parsed.to_bytes() == data


# ---------------------------------------------------------------------------
# ASDU header + SQ-bit dependent information-object repetition
# ---------------------------------------------------------------------------
def test_asdu_individually_addressed_objects():
    """sq=0: every information object carries its own IOA."""
    asdu = ASDU(header=ASDU_Header(type_id=TypeID.M_SP_NA_1, common_address=1))
    objects = [
        InformationObject(
            ioa=100, element=information.SinglePointInformation(status=SIQ(spi=True))
        ),
        InformationObject(
            ioa=250, element=information.SinglePointInformation(status=SIQ(spi=False))
        ),
    ]
    data = asdu.build(objects, sq=False)

    parsed = ASDU.from_bytes(data)
    assert parsed.header.vsq.sq is False
    assert parsed.header.vsq.number == 2
    decoded = parsed.decode_objects()
    assert [o.ioa for o in decoded] == [100, 250]
    assert decoded[0].element.status.spi is True
    assert decoded[1].element.status.spi is False
    assert parsed.build(decoded, sq=False) == data


def test_asdu_sequential_addressed_objects():
    """sq=1: only the first object carries an IOA; the rest are ioa+i."""
    asdu = ASDU(header=ASDU_Header(type_id=TypeID.M_SP_NA_1, common_address=1))
    objects = [
        InformationObject(
            ioa=300, element=information.SinglePointInformation(status=SIQ(spi=True))
        ),
        InformationObject(
            ioa=301, element=information.SinglePointInformation(status=SIQ(spi=False))
        ),
        InformationObject(
            ioa=302, element=information.SinglePointInformation(status=SIQ(spi=True))
        ),
    ]
    data = asdu.build(objects, sq=True)

    parsed = ASDU.from_bytes(data)
    assert parsed.header.vsq.sq is True
    assert parsed.header.vsq.number == 3
    decoded = parsed.decode_objects()
    assert [o.ioa for o in decoded] == [300, 301, 302]
    assert parsed.build(decoded, sq=True) == data


def test_asdu_pack_iobjects_rejects_non_contiguous_ioa_when_sq():
    objects = [
        InformationObject(ioa=1, element=information.SinglePointInformation()),
        InformationObject(ioa=5, element=information.SinglePointInformation()),
    ]
    with pytest.raises(ValueError):
        coding.pack_information_objects(TypeID.M_SP_NA_1, objects, sq=True)


def test_asdu_header_cot_and_common_address():
    header = ASDU_Header(type_id=TypeID.C_IC_NA_1, common_address=1234)
    header.cot.cause = int(CauseOfTransmission.ACTIVATION)
    header.cot.test = True
    header.originator_address = 7

    data = header.to_bytes()
    parsed = ASDU_Header.from_bytes(data)
    assert parsed.type_id == TypeID.C_IC_NA_1
    assert parsed.common_address == 1234
    assert parsed.cot.cause == int(CauseOfTransmission.ACTIVATION)
    assert parsed.cot.test is True
    assert parsed.originator_address == 7
    assert parsed.to_bytes() == data


# ---------------------------------------------------------------------------
# Information-object registry and per-Type-ID struct round-trips
# ---------------------------------------------------------------------------
def test_all_information_classes_are_registered():
    for name in information.__all__:
        cls = getattr(information, name)
        type_id = getattr(cls, "TYPE_ID")
        entry = coding.get_asdu_type(type_id)
        assert entry is not None, f"{name} (TYPE_ID={type_id!r}) not registered"
        assert entry.type_id == type_id
        assert coding.get_asdu_type_desc(type_id)  # non-empty description


@pytest.mark.parametrize("name", information.__all__)
def test_information_object_zero_arg(name):
    """Every information-object struct must construct with zero args (no
    None-default landmines) and pack/unpack/repack byte-identically."""
    cls = getattr(information, name)
    instance = cls()
    data = instance.to_bytes()

    parsed = cls.from_bytes(data)
    assert parsed.to_bytes() == data
