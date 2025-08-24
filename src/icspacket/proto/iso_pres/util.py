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
from typing import Any
from icspacket.proto.iso_pres.iso8823 import (
    CP_type,
    Fully_encoded_data,
    Mode_selector,
    PDV_list,
    PresentaionContextItem,
    Presentation_requirements,
    Protocol_version,
    User_data,
    Called_presentation_selector,
    Calling_presentation_selector,
)


def build_connect_ppdu(
    user_data: bytes,
    pres_context_id: int | None = None,
    *,
    calling_presentation_selector: bytes | None = None,
    called_presentation_selector: bytes | None = None,
    use_version_1: bool = False,
    requirements: Presentation_requirements | None = None,
    pres_context_items: list[PresentaionContextItem] | None = None,
) -> CP_type:
    """
    Construct a ``CP-type`` (CONNECT PPDU) for initiating a COPP session.

    Assembles a presentation-layer connection request including version,
    selectors, requirements, context definitions, and user data (ASN.1 payloads
    wrapped in PDV-lists).

    :param user_data: Encoded ASN.1 payload to embed into
                      the user data field.
    :type user_data: bytes
    :param pres_context_id: Identifier for the presentation context
                            associated with the ``user_data``.
                            Defaults to ``1`` if not provided.
    :type pres_context_id: int | None
    :param calling_presentation_selector: Optional selector identifying
                                          the calling presentation entity.
    :type calling_presentation_selector: bytes | None
    :param called_presentation_selector: Optional selector identifying
                                         the called presentation entity.
    :type called_presentation_selector: bytes | None
    :param use_version_1: If ``True``, explicitly requests version 1
                          of the Presentation protocol.
                          Defaults to ``False`` (version negotiation left open).
    :type use_version_1: bool
    :param requirements: Presentation requirements field. If not set,
                         a default empty ``Presentation_requirements``
                         instance is used.
    :type requirements: Presentation_requirements | None
    :param pres_context_items: Optional list of presentation context
                               definitions (e.g., abstract syntax +
                               transfer syntax pairs).
    :type pres_context_items: list[PresentaionContextItem] | None
    :return: A fully-formed ``CP-type`` connect PDU.
    :rtype: CP_type

    .. note::
       This constructs only a ``normal-mode`` connect PDU.
       X.226 also defines other connection modes and negotiation
       structures that may be added in future extensions.
    """
    ppdu = CP_type()

    # normal mode supported
    mode_selector = Mode_selector()
    mode_selector.mode_value = Mode_selector.mode_value_VALUES.V_normal_mode
    ppdu.mode_selector = mode_selector

    parameters = CP_type.normal_mode_parameters_TYPE()
    if use_version_1:
        version = Protocol_version()
        version.V_version_1 = True
        parameters.protocol_version = version

    if called_presentation_selector:
        parameters.called_presentation_selector = Called_presentation_selector(
            called_presentation_selector
        )

    if calling_presentation_selector:
        parameters.calling_presentation_selector = Calling_presentation_selector(
            calling_presentation_selector
        )

    if pres_context_items:
        parameters.presentation_context_definition_list = pres_context_items

    if not requirements:
        requirements = Presentation_requirements()

    parameters.presentation_requirements = requirements

    parameters.user_data = build_user_data(
        user_data, presentation_context_id=pres_context_id or 1
    )
    ppdu.normal_mode_parameters = parameters
    return ppdu


def build_user_data(
    user_data: bytes,
    presentation_context_id: int,
) -> User_data:
    """
    Build a ``User_data`` structure wrapping raw ASN.1 data.

    This creates a ``PDV-list`` entry with the given presentation
    context identifier, assigning the payload as a
    ``single-ASN1-type``.

    :param user_data: Encoded ASN.1 payload to embed.
    :type user_data: bytes
    :param presentation_context_id: Identifier for the presentation
                                    context under which the payload
                                    is interpreted.
    :type presentation_context_id: int
    :return: A ``User_data`` element containing fully encoded data.
    :rtype: User_data

    .. note::
       This helper assumes **single ASN.1 type** encoding.
       If multiple PDVs or different encodings (octet-aligned,
       arbitrary) are needed, the construction must be extended.
    """
    pdv_list = PDV_list()
    pdv_list.presentation_context_identifier.value = presentation_context_id
    pdv_list.presentation_data_values.single_ASN1_type = user_data

    data = User_data()
    fully_encoded_data = Fully_encoded_data()
    fully_encoded_data.add(pdv_list)
    data.fully_encoded_data = fully_encoded_data
    return data


def user_data_get_single_asn1(
    user_data: User_data, *, context: dict[int, type] | None = None
) -> Any:
    """
    Extract and decode a single ASN.1 object from ``User_data``.

    Validates that the input is fully encoded, contains exactly
    one ``PDV-list``, and that the encoding is of type
    ``single-ASN1-type``. The payload is then decoded using the
    ASN.1 class mapped to the presentation context identifier.

    :param user_data: The presentation user data structure to inspect.
    :type user_data: User_data
    :param context: Mapping of presentation context identifiers to
                    ASN.1 classes that implement a ``ber_decode`` method.
                    If not provided, defaults to an empty map (error
                    if lookup fails).
    :type context: dict[int, type[Any]] | None
    :raises ValueError: If the data is not fully encoded,
                        contains multiple PDVs,
                        has an unexpected data type,
                        or references an unknown context id.
    :return: The decoded ASN.1 object.
    :rtype: Any

    .. warning::
       This function assumes that the ``context`` dictionary
       correctly maps presentation context identifiers to
       decodable ASN.1 types. Incorrect mappings may lead to
       misinterpretation of payloads.
    """
    pres_context = context or {}
    if user_data.present != User_data.PRESENT.PR_fully_encoded_data:
        raise ValueError("Expected fully encoded data")

    encoded_data = user_data.fully_encoded_data
    assert encoded_data is not None  # MUST be present

    if len(encoded_data) != 1:
        raise ValueError("Expected a single PDV list in fully encoded data")

    pdv_list = encoded_data[0]
    if pdv_list.presentation_context_identifier.value not in pres_context:
        raise ValueError(
            f"Unknown presentation context id {pdv_list.presentation_context_identifier.value}"
        )

    if (
        pdv_list.presentation_data_values.present
        != PDV_list.presentation_data_values_TYPE.PRESENT.PR_single_ASN1_type
    ):
        raise ValueError(
            f"Expected single ASN1 type, got {pdv_list.presentation_data_values.present}"
        )

    asn1_cls = pres_context[pdv_list.presentation_context_identifier.value]
    return asn1_cls.ber_decode(pdv_list.presentation_data_values.single_ASN1_type)
