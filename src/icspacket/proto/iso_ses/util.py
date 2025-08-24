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
from collections.abc import Iterable
from icspacket.proto.iso_ses.spdu import (
    SPDU,
    PGI_Code,
    Px_Unit,
    SPDU_Category,
    SPDU_Codes,
)
from icspacket.proto.iso_ses.tsdu import TSDU
from icspacket.proto.iso_ses.values import (
    PI_Code,
    PV_ProtocolOptions,
    PV_SessionRequirements,
    PV_VersionNumber,
)


def build_connect_spdu(
    *,
    extended: bool = False,
    version2: bool = True,
    requirements: PV_SessionRequirements | None = None,
    called_ses_sel: bytes | None = None,
    calling_ses_sel: bytes | None = None,
    user_data: bytes | None = None,
    extra_parameters: Iterable[Px_Unit] | None = None,
) -> SPDU:
    """
    Construct a ``CONNECT SPDU`` (Session Protocol Data Unit).

    This initiates a COSP (X.225 / ISO 8327) session connection,
    encoding protocol version, session requirements, session
    selectors, and optional user data.

    :param extended: If ``True``, enables extended protocol
                     options (e.g. extended addressing or token handling).
                     Defaults to ``False``.
    :type extended: bool
    :param version2: If ``True``, enables version 2 of the
                     session protocol. If ``False``, version 1 is set.
                     Defaults to ``True``.
    :type version2: bool
    :param requirements: Session requirements parameter block.
                         If omitted, defaults to an empty
                         ``PV_SessionRequirements`` instance.
    :type requirements: PV_SessionRequirements | None
    :param called_ses_sel: Selector of the called session entity.
                           Used for identifying the target service access point.
    :type called_ses_sel: bytes | None
    :param calling_ses_sel: Selector of the calling session entity.
                            Used for identifying the initiating SAP.
    :type calling_ses_sel: bytes | None
    :param user_data: Optional user data to carry within the SPDU.
                      Typically contains higher-layer negotiation payload.
    :type user_data: bytes | None
    :param extra_parameters: Additional session parameter elements
                             (e.g. for vendor-specific extensions).
    :type extra_parameters: Iterable[Px_Unit] | None
    :return: A fully constructed ``SPDU`` representing a connection request.
    :rtype: SPDU

    .. note::
       Future implementations may include negotiation of additional
       protocol features (e.g., token assignment, activity management,
       or session layer QoS). These can be injected via
       ``extra_parameters`` to remain forward-compatible.
    """
    if not requirements:
        requirements = PV_SessionRequirements()

    spdu = SPDU(SPDU_Codes.CONNECT_SPDU)
    accept_item = spdu.add_parameter(PGI_Code.ACCEPT_ITEM, [])
    # version number
    version = PV_VersionNumber()
    version.version1 = not version2
    version.version2 = bool(version2)
    _ = accept_item.add_parameter(PI_Code.VERSION_NUMBER, version)

    # protocol options
    options = PV_ProtocolOptions()
    options.extended = extended
    _ = accept_item.add_parameter(PI_Code.PROTOCOL_OPTIONS, options)

    # session requirements
    _ = spdu.add_parameter(PI_Code.SESSION_REQUIREMENT, requirements)

    if called_ses_sel:
        _ = accept_item.add_parameter(PI_Code.CALLED_SESSION_SELECTOR, called_ses_sel)

    if calling_ses_sel:
        _ = accept_item.add_parameter(PI_Code.CALLING_SESSION_SELECTOR, calling_ses_sel)

    # user data
    if user_data:
        _ = spdu.add_parameter(PGI_Code.USER_DATA, user_data)

    if extra_parameters:
        spdu.parameters.extend(extra_parameters)
    return spdu


def build_data_tsdu(
    user_data: bytes,
    *,
    extra_parameters: Iterable[Px_Unit] | None = None,
) -> TSDU:
    """Construct a ``DATA TSDU`` (Transport Service Data Unit).

    :param user_data: User payload to carry inside the
                      ``DATA_TRANSFER_SPDU``.
    :type user_data: bytes
    :param extra_parameters: Optional session parameter extensions
                             to append to the ``DATA_TRANSFER_SPDU``.
    :type extra_parameters: Iterable[Px_Unit] | None
    :return: A fully constructed ``TSDU`` containing the encapsulated SPDUs.
    :rtype: TSDU
    """
    tsdu = TSDU()
    _ = tsdu.add_spdu(SPDU_Codes.GIVE_TOKENS_SPDU, SPDU_Category.CATEGORY_0)
    spdu = tsdu.add_spdu(SPDU_Codes.DATA_TRANSFER_SPDU)
    spdu.user_information = user_data
    if extra_parameters:
        spdu.parameters.extend(extra_parameters)
    return tsdu


def build_finish_spdu(
    *,
    user_data: bytes | None = None,
    extra_parameters: Iterable[Px_Unit] | None = None,
) -> SPDU:
    """
    Construct a ``FINISH SPDU`` for orderly session release.

    Encapsulates optional user data and any protocol-specific
    extension parameters, signaling graceful termination of
    the COSP session.

    :param user_data: Optional user data to include in the SPDU
                      (e.g., end-of-session diagnostics or higher-layer
                      release information).
    :type user_data: bytes | None
    :param extra_parameters: Additional parameters to extend SPDU
                             capabilities for session release.
    :type extra_parameters: Iterable[Px_Unit] | None
    :return: A fully constructed ``SPDU`` representing session termination.
    :rtype: SPDU
    """
    spdu = SPDU(SPDU_Codes.FINISH_SPDU)
    if user_data:
        _ = spdu.add_parameter(PGI_Code.USER_DATA, user_data)
    if extra_parameters:
        spdu.parameters.extend(extra_parameters)
    return spdu
