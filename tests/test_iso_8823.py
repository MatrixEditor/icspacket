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

from icspacket.proto.iso_pres.iso8823 import (
    CPA_PPDU,
    CP_type,
    Context_list,
    Fully_encoded_data,
    Mode_selector,
    PDV_list,
    User_data,
)
from icspacket.proto.iso_pres.util import build_connect_ppdu

from ._util import asn1_decode


def test_cpa_ppdu__decode():
    asn1_decode(
        CPA_PPDU,
        expected="""\
        CPA-PPDU ::= {
            mode-selector: Mode-selector ::= {
                mode-value: 1
            }
            normal-mode-parameters: normal-mode-parameters ::= {
                responding-presentation-selector: 00 00 00 01
                presentation-context-definition-result-list: Presentation-context-definition-result-list ::= {
                    SEQUENCE ::= {
                        result: 0
                        transfer-syntax-name: { 2.1.1 }
                    }
                    SEQUENCE ::= {
                        result: 0
                        transfer-syntax-name: { 2.1.1 }
                    }
                }
                presentation-requirements: 00 (6 bits unused)
                user-data: Fully-encoded-data ::= {
                    PDV-list ::= {
                        presentation-context-identifier: 1
                        presentation-data-values:
                            61 49 80 02 07 80 A1 07 06 05 28 CA 22 02 03 A2
                            03 02 01 00 A3 05 A1 03 02 01 00 BE 2E 28 2C 02
                            01 03 A0 27 A9 25 80 02 7D 00 81 01 0A 82 01 08
                            83 01 05 A4 16 80 01 01 81 03 05 E1 00 82 0C 03
                            EE 08 00 00 04 00 00 00 00 01 ED
                    }
                }
            }
        }
        """,
        data="3179a003800101a272830400000001a5123007800100810251013007800100810251018802060061"
        + "523050020101a04b614980020780a107060528ca220203a203020100a305a103020100be2e282c02"
        + "0103a027a92580027d0081010a820108830105a416800101810305e100820c03ee08000004000000"
        + "0001ed18",
    )


def test_context_list__init():
    context_list = Context_list()
    assert len(context_list) == 0


def test_context_list__add_direct():
    context_list = Context_list()

    item = Context_list.Member_TYPE()
    item.presentation_context_identifier.value = 1
    item.abstract_syntax_name.value = "1.2.3.4"
    item.transfer_syntax_name_list.add("1.2.3.4")

    assert item.presentation_context_identifier.value == 1
    assert item.transfer_syntax_name_list[0] == "1.2.3.4"

    context_list.add(item)
    assert len(context_list) == 1
    assert context_list[0].presentation_context_identifier.value == 1


def test_context_list__add_by_conversion():
    context_list = Context_list()

    item = Context_list.Member_TYPE()
    item.presentation_context_identifier = 1
    item.abstract_syntax_name = "1.2.3.4"
    item.transfer_syntax_name_list.add("1.2.3.4")

    context_list.add(item)
    assert len(context_list) == 1
    assert context_list[0].abstract_syntax_name.value == "1.2.3.4"


def test_context_def_list__init_by_conversion():
    item = Context_list.Member_TYPE()
    item.presentation_context_identifier = 1

    parameters = CP_type.normal_mode_parameters_TYPE()
    parameters.presentation_context_definition_list = [item]
    assert len(parameters.presentation_context_definition_list.value) == 1


def test_pdv_list__init():
    pdv_list = PDV_list()
    pdv_list.presentation_context_identifier = 1
    pdv_list.transfer_syntax_name = "1.2.3.4"

    assert pdv_list.presentation_context_identifier.value == 1
    assert pdv_list.transfer_syntax_name.value == "1.2.3.4"


def test_pdv_list__single_asn1_type():
    pdv_list = PDV_list()
    pdv_list.presentation_data_values.single_ASN1_type = b"foobar"

    assert pdv_list.presentation_data_values.single_ASN1_type == b"foobar"


def test_fully_encoded_data__init():
    pdv_list = PDV_list()
    pdv_list.presentation_context_identifier = 1
    pdv_list.transfer_syntax_name = "1.2.3.4"
    pdv_list.presentation_data_values.single_ASN1_type = b"foobar"

    data = Fully_encoded_data()
    data.add(pdv_list)

    assert len(data) == 1
    assert data[0].presentation_data_values.single_ASN1_type == b"foobar"


def test_user_data__from_fully_encoded_data():
    pdv_list = PDV_list()
    pdv_list.presentation_context_identifier = 1
    pdv_list.transfer_syntax_name = "1.2.3.4"
    pdv_list.presentation_data_values.single_ASN1_type = b"foobar"

    data = Fully_encoded_data()
    data.add(pdv_list)

    user_data = User_data(fully_encoded_data=data)
    assert user_data.present == User_data.PRESENT.PR_fully_encoded_data
    assert len(user_data.fully_encoded_data) == 1


def test_build_connect_pdu():
    ppdu = build_connect_ppdu(b"foobar")
    assert (
        ppdu.mode_selector.mode_value.value
        == Mode_selector.mode_value_VALUES.V_normal_mode
    )
    # make sure this works
    assert ppdu.ber_encode() is not None
