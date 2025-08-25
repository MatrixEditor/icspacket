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

from icspacket.proto.mms import MMS_IMPL_ID
from icspacket.proto.mms.asn1types import (
    GetNameList_Request,
    Initiate_RequestPDU,
    ObjectClass,
    ObjectName,
    ParameterSupportOptions,
    ServiceSupportOptions,
    VariableAccessSpecification,
)

# some handy aliases
BasicObjectClassType = ObjectClass.basicObjectClass_VALUES
"""Alias for the MMS ``ObjectClass.basicObjectClass`` enumeration values."""

DomainSpecificName = ObjectName.domain_specific_TYPE
"""Alias for the MMS ``ObjectName.domain-specific`` choice type."""

ObjectScope = GetNameList_Request.objectScope_TYPE
"""Alias for the MMS ``GetNameList-Request.objectScope`` type."""

VariableAccessItem = VariableAccessSpecification.listOfVariable_TYPE.Member_TYPE
"""Alias for the MMS ``VariableAccessSpecification.listOfVariable.Member`` type."""

DEFAULT_MAX_CALLED = 10
"""Default value for ``proposedMaxServOutstandingCalled`` in an Initiate-Request."""

DEFAULT_MAX_CALLING = 10
"""Default value for ``proposedMaxServOutstandingCalling`` in an Initiate-Request."""

DEFAULT_MAX_DATA_NESTING_DEPTH = 10
"""Default value for ``proposedDataStructureNestingLevel`` in an Initiate-Request."""


def new_initiate_request(
    *,
    local_detail_calling: int | None = None,
    max_serv_outstanding_called: int = DEFAULT_MAX_CALLED,
    max_serv_outstanding_calling: int = DEFAULT_MAX_CALLING,
    data_nesting_depth: int | None = DEFAULT_MAX_DATA_NESTING_DEPTH,
    version_number: int | None = None,
    options: ServiceSupportOptions | None = None,
) -> Initiate_RequestPDU:
    """
    Build a new MMS ``Initiate-RequestPDU``.

    This utility simplifies construction of the Initiate Service
    defined in **ISO 9506-1, §8.2**.

    :param local_detail_calling: Local detail identifier of the calling
        MMS-user's implementation. If not provided, defaults to the
        global ``MMS_IMPL_ID``.
    :type local_detail_calling: int | None
    :param max_serv_outstanding_called: Proposed maximum number of
        outstanding transactions for the called MMS-user.
    :type max_serv_outstanding_called: int
    :param max_serv_outstanding_calling: Proposed maximum number of
        outstanding transactions for the calling MMS-user.
    :type max_serv_outstanding_calling: int
    :param data_nesting_depth: Proposed maximum nesting depth of MMS
        data elements. If ``None``, indicates unlimited nesting. Must
        be between 0 and 255.
    :type data_nesting_depth: int | None
    :param version_number: Proposed MMS protocol version number. Defaults
        to 1 if not specified.
    :type version_number: int | None
    :param options: Supported service options of the calling MMS-user.
        If not provided, defaults to the return value of
        :func:`default_support_options`.
    :type options: ServiceSupportOptions | None
    :raises ValueError: If ``data_nesting_depth`` is outside the range
        [0, 255].
    :return: A fully constructed MMS Initiate-Request PDU.
    :rtype: Initiate_RequestPDU

    .. seealso::
        ISO 9506-1 §8.2, "Initiate Service"
    """
    if local_detail_calling is None:
        local_detail_calling = MMS_IMPL_ID

    if data_nesting_depth is not None and not 0 <= data_nesting_depth <= 255:
        raise ValueError("proposedDataStructureNestingLevel must be between 0 and 255")

    pdu = Initiate_RequestPDU()
    pdu.localDetailCalling = local_detail_calling
    pdu.proposedMaxServOutstandingCalled = max_serv_outstanding_called
    pdu.proposedMaxServOutstandingCalling = max_serv_outstanding_calling

    if data_nesting_depth is not None:
        # in 8.2.1.1.4:
        # Absence of this parameter shall indicate an unlimited number of
        # nesting levels.
        pdu.proposedDataStructureNestingLevel = data_nesting_depth

    details = Initiate_RequestPDU.initRequestDetail_TYPE()
    details.proposedVersionNumber = version_number or 1

    cbb = ParameterSupportOptions(size=2)
    # fixed support options: str1, str2, vnam, vlis, valt
    cbb.V_str1 = True
    cbb.V_str2 = True
    cbb.V_vnam = True
    cbb.V_valt = True
    cbb.V_vlis = True
    details.proposedParameterCBB = cbb

    if options is None:
        options = default_support_options()
    details.servicesSupportedCalling = options

    pdu.initRequestDetail = details
    return pdu


def default_support_options() -> ServiceSupportOptions:
    """
    Return a default set of MMS service support options.

    This function enables a calling MMS-user to quickly declare support
    for a representative set of services, without manually toggling each
    option. The defaults include:

    - Status, Identify, Kill
    - GetNameList, GetVariableAccessAttributes
    - Define/Get/Delete Named Variable List
    - Read, Write
    - Journal services (Read, Write, Initialize, Status report)
    - File services (Open, Close, Read, Delete, Directory)
    - Miscellaneous (InformationReport, Conclude, Cancel, GetCapabilityList)

    :return: A populated ``ServiceSupportOptions`` structure.
    :rtype: ServiceSupportOptions
    """
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
    return support


def basic_object_class(class_: BasicObjectClassType, /) -> ObjectClass:
    """
    Construct an MMS ``ObjectClass`` using a basic object class value.

    :param class_: Basic object class value (from :data:`BasicObjectClassType`).
    :type class_: BasicObjectClassType
    :return: A new ``ObjectClass`` instance.
    :rtype: ObjectClass
    """
    return ObjectClass(basicObjectClass=class_)


def domain_object_name(domain: str, item: str) -> ObjectName:
    """
    Construct a domain-specific MMS ``ObjectName``.

    :param domain: Domain identifier.
    :type domain: str
    :param item: Item identifier within the domain.
    :type item: str
    :return: A new domain-specific ``ObjectName``.
    :rtype: ObjectName
    """
    name = ObjectName()
    name.domain_specific = DomainSpecificName()
    name.domain_specific.domainID = domain
    name.domain_specific.itemID = item
    return name


def domain_variable_access(domain: str, name: str) -> VariableAccessItem:
    """
    Construct a domain-specific MMS variable access specification.

    :param domain: Domain identifier containing the variable.
    :type domain: str
    :param name: Name of the variable within the domain.
    :type name: str
    :return: A new variable access item for the given domain object.
    :rtype: VariableAccessItem
    """
    variable = VariableAccessItem()
    variable.variableSpecification.name = domain_object_name(domain, name)
    return variable


def vmd_variable_access(name: str) -> VariableAccessItem:
    """
    Construct an MMS variable access specification for a VMD-specific variable.

    :param name: Name of the VMD-specific variable.
    :type name: str
    :return: A new variable access item for the given VMD object.
    :rtype: VariableAccessItem
    """
    variable = VariableAccessItem()
    variable.variableSpecification.name = ObjectName(vmd_specific=name)
    return variable


def object_name_to_string(name: ObjectName) -> str:
    """
    Convert an MMS ``ObjectName`` to a string representation.

    :param name: The ``ObjectName`` to convert.
    :type name: ObjectName
    :return: A string representation of the object name.
    :rtype: str
    """
    domain = item = None
    match name.present:
        case ObjectName.PRESENT.PR_aa_specific:
            item = name.aa_specific
        case ObjectName.PRESENT.PR_domain_specific:
            domain = name.domain_specific.domainID
            item = name.domain_specific.itemID
        case ObjectName.PRESENT.PR_vmd_specific:
            item = name.vmd_specific

    if domain:
        return f"{domain.value}/{item.value}"
    else:
        return item.value
