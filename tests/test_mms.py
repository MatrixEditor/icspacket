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
import datetime
import pytest

from icspacket.proto.cotp.connection import COTP_Connection
from icspacket.proto.mms._mms import Data
from icspacket.proto.mms.asn1types import (
    GetNameList_Request,
    MMSpdu,
    ParameterSupportOptions,
    ServiceSupportOptions,
)
from icspacket.proto.mms.acse import ACSEAuthenticationFailure, PasswordAuth
from icspacket.proto.mms.connection import MMS_Connection
from icspacket.proto.mms.data import (
    IEEE754Type,
    Timestamp,
    create_floating_point_value,
    get_floating_point_value,
    from_dict,
)
from icspacket.proto.mms.asn1types import Initiate_RequestPDU
from icspacket.proto.mms.util import new_initiate_request
from icspacket.proto.mms.exceptions import MMSUnknownServiceError

from ._util import faketpktsock, load_asset_cases


def test_create_floating_point_value() -> None:
    fp = create_floating_point_value(1.0)
    assert len(fp.value) != 0
    assert fp.value[0] == IEEE754Type.FLOAT32


def test_get_floating_point_value():
    fp = create_floating_point_value(1.0)
    assert len(fp.value) == 5
    assert get_floating_point_value(fp) == 1.0


def test_create_float64_value():
    fp = create_floating_point_value(1.0, IEEE754Type.FLOAT64)
    assert len(fp.value) == 9
    assert fp.value[0] == IEEE754Type.FLOAT64


def test_get_float64_value():
    fp = create_floating_point_value(1.0, IEEE754Type.FLOAT64)
    assert get_floating_point_value(fp) == 1.0


def test_timestamp():
    now = datetime.datetime.now()
    ts = Timestamp.from_datetime(now)
    # conversion removes milliseconds for now
    assert now != ts.datetime
    assert int(now.timestamp()) == ts.datetime.timestamp()


def test_build_data_object():
    data = from_dict({"integer": 1})
    assert data.present == Data.PRESENT.PR_integer
    assert data.integer == 1

    data = from_dict({"unsigned": 1})
    assert data.present == Data.PRESENT.PR_unsigned
    assert data.unsigned == 1

    with pytest.raises(KeyError):
        from_dict({"unknown": 1})


# ---------------------------------------------------------------------------
# INIT REQUEST PDU
# ---------------------------------------------------------------------------
def test_init_req__int_fields():
    pdu = Initiate_RequestPDU()
    pdu.localDetailCalling = 10
    assert pdu.localDetailCalling.value == 10

    pdu = Initiate_RequestPDU(localDetailCalling=10)
    assert pdu.localDetailCalling.value == 10


def test_init_req__cbb():
    cbb = ParameterSupportOptions(size=2)
    cbb.V_str1 = True
    cbb.V_str2 = True
    cbb.V_vnam = True
    cbb.V_valt = True
    cbb.V_vlis = True

    assert cbb.V_str1 is True
    assert cbb.V_str2 is True
    assert cbb.V_vnam is True
    assert cbb.V_valt is True
    assert cbb.V_vlis is True


def test_init_req__services_supported():
    support = ServiceSupportOptions()
    support.V_status = True
    support.V_getNameList = True
    support.V_identify = True
    # no V_rename
    support.V_read = True
    support.V_write = True
    support.V_getVariableAccessAttributes = True
    support.V_defineNamedVariableList = True
    support.V_getNamedVariableListAttributes = True
    support.V_deleteNamedVariableList = True
    support.V_getDomainAttributes = True
    support.V_kill = True
    support.V_readJournal = True
    support.V_writeJournal = True
    support.V_initializeJournal = True
    support.V_reportJournalStatus = True
    support.V_getCapabilityList = True
    support.V_fileOpen = True
    support.V_fileClose = True
    support.V_fileRead = True
    support.V_fileDelete = True
    support.V_fileDirectory = True
    support.V_informationReport = True
    support.V_conclude = True
    support.V_cancel = True


def test_init_req__build():
    pdu = new_initiate_request()
    assert pdu.initRequestDetail.servicesSupportedCalling.V_cancel is True
    assert pdu.proposedDataStructureNestingLevel.value == 10

    mmspdu = MMSpdu(initiate_RequestPDU=pdu)
    assert mmspdu.present == MMSpdu.PRESENT.PR_initiate_RequestPDU
    # make sure this works
    assert mmspdu.ber_encode() is not None


# ---------------------------------------------------------------------------
# GetNameList SERVICE
# ---------------------------------------------------------------------------
def test_mms_getnamelist__scope():
    # test that scope is copied correctly
    scope = GetNameList_Request.objectScope_TYPE()
    scope.vmdSpecific = None
    assert scope.present == GetNameList_Request.objectScope_TYPE.PRESENT.PR_vmdSpecific

    request = GetNameList_Request()
    request.objectScope = scope
    assert (
        request.objectScope.present
        == GetNameList_Request.objectScope_TYPE.PRESENT.PR_vmdSpecific
    )


# ---------------------------------------------------------------------------
# CONNECTIOn
# ---------------------------------------------------------------------------
DATA = load_asset_cases("mms")


def _setup_mms_connection(case_name: str) -> MMS_Connection:
    cotp_conn = COTP_Connection(sock=faketpktsock(DATA[case_name]))
    conn = MMS_Connection(cotp_conn)
    return conn


def test_mms_conn__acse_associate():
    conn = _setup_mms_connection("acse_associate_success")
    conn.associate(faketpktsock.FAKE_ADDRESS)


def test_mms_conn__acse_release():
    conn = _setup_mms_connection("acse_release_success")
    conn.associate(faketpktsock.FAKE_ADDRESS)
    conn.release()


def test_mms_conn__reject_service_request():
    conn = _setup_mms_connection("service_reject")
    conn.associate(faketpktsock.FAKE_ADDRESS)
    with pytest.raises(MMSUnknownServiceError):
        _ = conn.get_capabilities()


def test_mms_conn__auth_success():
    conn = _setup_mms_connection("auth_success")
    conn.association.authenticator = PasswordAuth("user2@testpw", "1.2.3", 1)
    conn.associate(faketpktsock.FAKE_ADDRESS)


def test_mms_conn__auth_reject():
    conn = _setup_mms_connection("auth_reject")
    conn.association.authenticator = PasswordAuth("abc2", "1.2.3", 1)
    with pytest.raises(ACSEAuthenticationFailure):
        conn.associate(faketpktsock.FAKE_ADDRESS)
