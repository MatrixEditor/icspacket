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
import enum

from icspacket.core.connection import ConnectionNotEstablished
from icspacket.proto.iec61850.path import ObjectReference
from icspacket.proto.mms._mms import (
    AccessResult,
    Data,
    DataAccessError,
    DirectoryEntry,
    GetVariableAccessAttributes_Response,
)
from icspacket.proto.mms.connection import MMS_Connection
from icspacket.proto.mms.util import (
    BasicObjectClassType,
    NamedVariableSpecificationItem,
    ObjectScope,
    VariableAccessItem,
    basic_object_class,
)


class ACSI_Class(enum.Enum):
    """
    Enumeration of ACSI class models as per IEC 61850.

    Each entry defines a mapping from the abstract ACSI model into the
    concrete MMS object class that is used for encoding.
    """

    DATA = "DataObject"
    DATA_SET = "DataSet"
    BRCB = "BufferedReportControlBlock"
    URCB = "UnbufferedReportControlBlock"
    LCB = "LogControlBlock"
    LOG = "SettingGroupControlBlock"
    SGCB = "Log"
    GoCB = "GooseControlBlock"
    GsCB = "GSSEControlBlock"
    MSVCB = "MulticastSampledValueControlBlock"
    USVCB = "UnicastSampledValueControlBlock"

    def object_class(self) -> BasicObjectClassType:
        """
        Map the ACSI class to its corresponding MMS `BasicObjectClassType`.

        :returns: The MMS object class type.
        :rtype: BasicObjectClassType
        """
        match self:
            case ACSI_Class.DATA_SET:
                return BasicObjectClassType.V_namedVariableList
            case ACSI_Class.LOG:
                return BasicObjectClassType.V_journal
            case _:
                return BasicObjectClassType.V_namedVariable


class IED_Client:
    """
    IEC 61850 **Intelligent Electronic Device (IED) client** implementation
    that provides access to ACSI services mapped to MMS.

    This class abstracts MMS connection handling and exposes ACSI services
    such as retrieving server directories, logical device directories,
    logical node directories, and reading/writing values of DataObjects.

    A client may either be initialized with an existing
    :class:`MMS_Connection` or can establish its own association
    to a remote MMS peer.

    >>> with IED_Client(("127.0.0.1", 102)) as client:
    ...     devices = client.get_server_directory()
    ...     for dev in devices:
    ...         print(dev)

    :param address: Optional IP/port tuple for automatic association.
    :type address: tuple[str, int] | None
    :param conn: Pre-established MMS connection, if available.
    :type conn: MMS_Connection | None
    """

    def __init__(
        self,
        address: tuple[str, int] | None = None,
        conn: MMS_Connection | None = None,
    ) -> None:
        self.__conn = conn
        if address:
            self.associate(address)

    @property
    def mms_conn(self) -> MMS_Connection:
        """
        Return the active MMS connection object.

        :returns: The established MMS connection.
        :rtype: MMS_Connection

        :raises ConnectionNotEstablished: If no MMS connection is available.
        """
        if not self.__conn:
            raise ConnectionNotEstablished("Not associated with an MMS peer")

        return self.__conn

    def associate(self, address: tuple[str, int] | None = None) -> None:
        """
        Establish an association with a remote MMS server.

        :param address: The address (IP, port) of the remote peer.
        :type address: tuple[str, int] | None
        """
        if not self.__conn:
            self.__conn = MMS_Connection()

        if self.mms_conn.is_valid():
            return

        self.mms_conn.associate(address)

    def release(self) -> None:
        """
        Release the MMS association if active.
        """
        if self.mms_conn.is_valid():
            self.mms_conn.release()

    def __enter__(self) -> "IED_Client":
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    # ----------------------- ACSI Services ------------------------------- #

    # ---------------------------------------------------------------------- #
    # Server class service
    # ---------------------------------------------------------------------- #
    def get_server_directory(self) -> list[ObjectReference]:
        """
        Retrieve the list of **logical devices** available on the server.

        Maps ACSI GetServerDirectory :octicon:`arrow-right` MMS GetNameList.

        :returns: A list of logical device references.
        :rtype: list[ObjectReference]

        >>> client.get_server_directory()
        ["LD1", "LD2"]
        """
        # LOGICAL-DEVICE class:
        # The ACSI request maps to an MMS GetNameList request
        result = self.mms_conn.get_name_list(
            basic_object_class(BasicObjectClassType.V_domain)
        )
        return list(map(ObjectReference.from_mmsref, result))

    def get_server_file_directory(self) -> list[DirectoryEntry]:
        """
        Retrieve the list of **files** stored on the server.

        Maps ACSI FileDirectory :octicon:`arrow-right` MMS FileDirectory.

        :returns: List of file directory entries.
        :rtype: list[DirectoryEntry]
        """
        # FILE class
        # The ACSI request maps to an MMS FileDirectory request
        return self.mms_conn.list_directory()

    # ---------------------------------------------------------------------- #
    # 11 Logical device model
    # ---------------------------------------------------------------------- #
    def get_logical_device_directory(
        self, ld_name: str | ObjectReference, /
    ) -> list[ObjectReference]:
        """
        Retrieve the list of **logical nodes** inside a logical device.

        Maps ACSI GetLogicalDeviceDirectory :octicon:`arrow-right` MMS GetNameList.

        :param ld_name: Logical device name or reference.
        :type ld_name: str | ObjectReference
        :returns: List of logical node references.
        :rtype: list[ObjectReference]
        """
        # The ACSI request GetLogicalDeviceDirectory maps to an MMS GetNameList
        # request.
        object_class = basic_object_class(BasicObjectClassType.V_namedVariable)
        scope = ObjectScope(domainSpecific=str(ld_name))
        entries = self.mms_conn.get_name_list(object_class, scope)
        return [
            ObjectReference.from_mmsref(f"{ld_name}/{entry}")
            for entry in entries
            # The NamedVariable objects returned may contain more objects than
            # solely logical nodes.Therefore, the MMS ObjectName will need to be
            # filtered by the application using the MMS  GetNameList-Request on
            # the client side based upon the naming standards within this
            # document (e.g. a NamedVariable that has no ‘$’ character).
            if "$" not in entry
        ]

    # ---------------------------------------------------------------------- #
    # 12 Logical node model
    # ---------------------------------------------------------------------- #
    def get_logical_node_directory(
        self,
        lnref: ObjectReference,
        /,
        acsi_class: ACSI_Class | None = None,
    ) -> list[ObjectReference]:
        """
        Retrieve the **data objects** of a logical node.

        Maps ACSI GetLogicalNodeDirectory :octicon:`arrow-right` MMS GetNameList.

        :param lnref: Reference to the logical node.
        :type lnref: ObjectReference
        :param acsi_class: Optional ACSI class filter.
        :type acsi_class: ACSI_Class | None
        :returns: List of child object references.
        :rtype: list[ObjectReference]

        >>> ln = ObjectReference("LD1", "MMXU1")
        >>> client.get_logical_node_directory(ln)
        ["LD1/MMXU1.A.phsA", "LD1/MMXU1.A.phsB"]
        """
        # The scope of the request shall be the scope of the LogicalNode
        # (typically within the scope of a particular domain).
        match acsi_class:
            case ACSI_Class.DATA_SET:
                # maps to NamedVariableList
                target = BasicObjectClassType.V_namedVariableList
            case ACSI_Class.LOG:
                # maps to Journal
                target = BasicObjectClassType.V_journal
            case _:
                # maps to NamedVariable
                target = BasicObjectClassType.V_namedVariable

        object_class = basic_object_class(target)
        scope = ObjectScope(domainSpecific=lnref.ldname)
        entries = self.mms_conn.get_name_list(object_class, scope)
        data_references = [
            ObjectReference.from_mmsref(f"{lnref.ldname}/{entry}") for entry in entries
        ]
        # we return all CHILDREN here without the node itself
        return [
            ref
            for ref in data_references
            if ref.lnname == lnref.lnname and len(ref.parts) > 2
        ]

    def get_all_data_values(self, lnref: ObjectReference, /) -> AccessResult:
        """
        Read **all data values** of a logical node.

        Maps ACSI GetAllDataValues :octicon:`arrow-right` MMS Read.

        :param lnref: Reference to the logical node.
        :type lnref: ObjectReference
        :returns: Access result containing all values.
        :rtype: AccessResult
        :raises ValueError: If multiple results are returned.
        """
        access = VariableAccessItem()
        access.variableSpecification.name = lnref.mms_name
        result = self.mms_conn.read_variables(access)
        if len(result) != 1:
            raise ValueError(f"Expected 1 result, got {len(result)}")
        return result[0]

    # ---------------------------------------------------------------------- #
    # 13 DataObject, DataAttribute, SubDataAttribute model
    # ---------------------------------------------------------------------- #
    def get_data_values(self, datref: ObjectReference, /) -> AccessResult:
        """
        Read the value of a **DataObject or DataAttribute**.

        Maps ACSI GetDataValues :octicon:`arrow-right` MMS Read.

        :param datref: DataObject reference.
        :type datref: ObjectReference
        :returns: Access result for the object.
        :rtype: AccessResult
        """
        # The ACSI GetDataValues service shall be mapped to the MMS read service.
        return self.get_all_data_values(datref)

    def set_data_values(
        self,
        datref: ObjectReference,
        /,
        value: Data,
    ) -> DataAccessError | None:
        """
        Write the value of a **DataObject or DataAttribute**.

        Maps ACSI SetDataValues :octicon:`arrow-right` MMS Write.

        :param datref: DataObject reference.
        :type datref: ObjectReference
        :param value: Value to be written.
        :type value: Data
        :returns: Error code if write fails, otherwise None.
        :rtype: DataAccessError | None
        """
        # T he ACSI SetDataValues service shall be mapped to the MMS Write service.
        # same as in get_all_data_values
        access = VariableAccessItem()
        access.variableSpecification.name = datref.mms_name
        return self.mms_conn.write_variable(value, variable=access)

    def get_data_directory(
        self, datref: ObjectReference, /
    ) -> GetVariableAccessAttributes_Response:
        """
        Retrieve the **attributes of a DataObject**.

        Maps ACSI GetDataDirectory :octicon:`arrow-right` MMS GetVariableAccessAttributes.

        :param datref: DataObject reference.
        :type datref: ObjectReference
        :returns: Variable access attributes.
        :rtype: GetVariableAccessAttributes_Response
        """
        # The ACSI GetDataDirectory service shall be mapped to the MMS
        # GetVariableAccessAttributes service.
        return self.mms_conn.variable_attributes(name=datref.mms_name)

    # This service shall be the same as GetDataDirectory
    get_data_definition = get_data_directory

    # ---------------------------------------------------------------------- #
    # 14 Data set class model
    # ---------------------------------------------------------------------- #
    def get_dataset_values(self, datref: ObjectReference, /) -> list[AccessResult]:
        """
        Retrieve all values of a **data set**.

        Maps ACSI GetDataSetValues :octicon:`arrow-right` MMS Read.

        :param datref: DataSet reference.
        :type datref: ObjectReference
        :returns: List of access results for each element.
        :rtype: list[AccessResult]
        """
        # The ACSI GetDataSetValues service shall be mapped to the MMS read
        # service.
        access = VariableAccessItem()
        access.variableSpecification.name = datref.mms_name
        # specificationWithResult: Shall be TRUE
        return self.mms_conn.read_variables(
            list_name=datref.mms_name, spec_in_result=True
        )

    def set_dataset_values(
        self, datref: ObjectReference, values: list[Data], /
    ) -> DataAccessError | None:
        """
        Write values to a **data set**.

        Maps ACSI SetDataSetValues :octicon:`arrow-right` MMS Write.

        :param datref: DataSet reference.
        :type datref: ObjectReference
        :param values: List of data values to write.
        :type values: list[Data]
        :returns: Error code if write fails, otherwise None.
        :rtype: DataAccessError | None
        """
        # The ACSI SetDataSetValues service shall be mapped to the MMS write
        # service.
        access = VariableAccessItem()
        access.variableSpecification.name = datref.mms_name
        return self.mms_conn.write_variable(values, list_name=datref.mms_name)

    def get_dataset_directory(
        self, datref: ObjectReference, /
    ) -> list[NamedVariableSpecificationItem]:
        """
        Retrieve the directory of a **data set**.

        Maps ACSI GetDataSetDirectory :octicon:`arrow-right` MMS VariableListAttributes.

        :param datref: DataSet reference.
        :type datref: ObjectReference
        :returns: List of variables contained in the dataset.
        :rtype: list[NamedVariableSpecificationItem]
        """
        return list(
            self.mms_conn.variable_list_attributes(datref.mms_name).listOfVariable
        )
