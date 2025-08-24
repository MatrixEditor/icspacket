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
# pyright: reportUnknownArgumentType=false
import pytest

from caterpillar.shortcuts import unpack

from icspacket.proto.cotp.connection import COTP_Connection
from icspacket.proto.cotp.structs import (
    ER_RejectCause,
    TPDU_AdditionalOptions,
    TPDU_ClassOption,
    TPDU_Class,
    TPDU_Code,
    TPDU_ConnectionConfirm,
    TPDU_ConnectionRequest,
    TPDU_Data,
    TPDU_DataAcknowledgement,
    TPDU_DisconnectConfirm,
    TPDU_DisconnectReason,
    TPDU_DisconnectRequest,
    TPDU_Error,
    TPDU_ExpeditedData,
    TPDU_ExpeditedDataAcknowledgement,
    TPDU_Number,
    TPDU_Reject,
    TPDU_Size,
    TPDU_TransitDelay,
    TPDU_ResidualErrorRate,
    Parameter,
    Parameter_Code,
    TPDU,
)
from tests._util import faketpktsock, load_asset_cases


# -------------------------------------------------
# BITFIELD TESTS
# -------------------------------------------------
def test_additional_options_defaults():
    # Default value:0000 0001.
    opts = TPDU_AdditionalOptions()
    assert bytes(opts) == b"\x01"  # Only last bit set


def test_additional_options_custom_values():
    opts = TPDU_AdditionalOptions(
        non_blocking=True,
        use_checksum_16bit=True,
    )
    assert opts.non_blocking is True
    assert opts.use_checksum_16bit is True
    data = bytes(opts)
    unpacked = unpack(TPDU_AdditionalOptions, data)
    assert unpacked == opts


def test_class_option_enum_and_bits():
    opt = TPDU_ClassOption(
        class_id=TPDU_Class.CLASS4,
        explicit_flow_control=True,
    )
    assert opt.class_id == TPDU_Class.CLASS4
    assert opt.explicit_flow_control
    raw = bytes(opt)
    restored = unpack(TPDU_ClassOption, raw)
    assert restored == opt


# -------------------------------------------------
# STRUCT TESTS
# -------------------------------------------------
def test_transit_delay_pack_unpack():
    delay = TPDU_TransitDelay(1, 2, 3, 4)
    assert delay.calling_target_value == 1
    assert delay.calling_maximum_acceptable == 2

    raw = bytes(delay)
    restored = unpack(TPDU_TransitDelay, raw)
    assert restored == delay


def test_residual_error_rate_pack_unpack():
    err = TPDU_ResidualErrorRate(1, 2, 3)
    raw = bytes(err)
    restored = unpack(TPDU_ResidualErrorRate, raw)
    assert restored == err


# -------------------------------------------------
# PARAMETER TESTS
# -------------------------------------------------
def test_parameter_with_known_type():
    param = Parameter(
        type_id=Parameter_Code.TPDU_SIZE,
        value=TPDU_Size.SIZE_512,
    )
    raw = bytes(param)
    restored = unpack(Parameter, raw)
    assert restored.type_id == Parameter_Code.TPDU_SIZE
    assert restored.value == TPDU_Size.SIZE_512


def test_parameter_with_unknown_type_bytes():
    param = Parameter(type_id=Parameter_Code.CALLED_T_SELECTOR, value=b"\xaa\xbb")
    raw = bytes(param)
    restored = unpack(Parameter, raw)
    assert restored.value == b"\xaa\xbb"


# -------------------------------------------------
# TPDU BASE TEST
# -------------------------------------------------
def test_tpdu_code_property():
    t = TPDU(li=0, code=(TPDU_Code.CR.value << 4))
    assert t.code != TPDU_Code.CR
    assert t.tpdu_code == TPDU_Code.CR


def test_tpdu_code_invalid_value():
    with pytest.raises(ValueError):
        _ = TPDU(li=0, code=0x00).tpdu_code


# -------------------------------------------------
# TPDU TESTS
# -------------------------------------------------
# fmt: off
@pytest.mark.parametrize(
    "pdu_cls,pdu_kwargs",
    [
        (TPDU, dict()), # Base type MUST be valid in all cases
        (TPDU_ConnectionRequest, dict(dst_ref=0x1234, src_ref=0x5678)),
        (TPDU_ConnectionConfirm, dict(dst_ref=0x1234, src_ref=0x5678)),
        (TPDU_DisconnectRequest, dict(dst_ref=0x1234, src_ref=0x5678, reason=TPDU_DisconnectReason.CONN_REFUSED)),
        (TPDU_DisconnectConfirm, dict(dst_ref=0x1234, src_ref=0x5678)),
        (TPDU_Data, dict(user_data=b"foobar")),
        (TPDU_ExpeditedData, dict(dst_ref=0x1234, ed_nr=TPDU_Number(eot=1), user_data=b"foobar")),
        (TPDU_DataAcknowledgement, dict(dst_ref=0x1234)),
        (TPDU_ExpeditedDataAcknowledgement, dict(dst_ref=0x1234, ed_nr=TPDU_Number(eot=1))),
        (TPDU_Reject, dict(dst_ref=0x1234, y_nr=0x5678)),
        (TPDU_Error, dict(dst_ref=0x1234, reject_cause=ER_RejectCause.REASON_NOT_SPECIFIED)),
    ],
)
# fmt: on
def test_pdu_build_and_validate(pdu_cls: type[TPDU], pdu_kwargs):
    pdu = pdu_cls(**pdu_kwargs)
    octets = pdu.build(add_checksum=True)

    parsed = pdu_cls.from_octets(octets)
    assert parsed.is_valid(), f"{pdu_cls.__name__} failed checksum validation"

    # Round-trip build
    rebuilt = parsed.build(add_checksum=False)
    assert rebuilt == octets, "Rebuilt octets differ from original"

# -------------------------------------------------
# CONNECTION TESTS
# -------------------------------------------------
DATA = load_asset_cases("cotp")

def test_cotp_conn__connect_():
    sock = faketpktsock(DATA["connect_success"])
    conn = COTP_Connection(sock=sock)
    conn.connect(faketpktsock.FAKE_ADDRESS)


def test_cotp_conn__connect_rejected():
    sock = faketpktsock(DATA["connect_reject"])
    conn = COTP_Connection(sock=sock)

    with pytest.raises(ConnectionRefusedError):
        # Simple connection refused error when server responds with a
        # DisconnectRequest packet
        conn.connect(faketpktsock.FAKE_ADDRESS)


def test_cotp_conn__recv_single_frame():
    sock = faketpktsock(DATA["recv_single_data"])
    conn = COTP_Connection(sock=sock)
    conn.connect(faketpktsock.FAKE_ADDRESS)

    data = conn.recv_data()
    assert len(data) == 58  # user data here


def test_cotp_conn__recv_multiple_frames():
    sock = faketpktsock(DATA["recv_multiple_data"])
    conn = COTP_Connection(sock=sock)
    conn.connect(faketpktsock.FAKE_ADDRESS)

    data = conn.recv_data()
    assert len(data) == 1171