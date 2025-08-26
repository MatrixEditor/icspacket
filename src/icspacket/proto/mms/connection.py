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
import logging

from typing_extensions import override

from icspacket.core.connection import connection
from icspacket.proto.tpkt import tpktsock
from icspacket.proto.cotp.connection import COTP_Connection
from icspacket.proto.iso_ses.session import ISO_Session, ISO_SessionSettings
from icspacket.proto.iso_pres.presentation import (
    ISO_Presentation,
    ISO_PresentationSettings,
)
from icspacket.proto.mms import MMS_ABSTRACT_SYNTAX_NAME, MMS_PRESENTATION_CONTEXT_ID
from icspacket.proto.mms.asn1types import (
    ABRT_source,
    AccessResult,
    AdditionalService_Request,
    AdditionalService_Response,
    Address,
    Conclude_RequestPDU,
    Confirmed_ErrorPDU,
    Confirmed_RequestPDU,
    ConfirmedServiceRequest,
    ConfirmedServiceResponse,
    Data,
    DataAccessError,
    DirectoryEntry,
    DomainName,
    FileClose_Request,
    FileDelete_Request,
    FileDirectory_Request,
    FileName,
    FileOpen_Request,
    FileRead_Request,
    FileRename_Request,
    GetCapabilityList_Request,
    GetDomainAttributes_Request,
    GetDomainAttributes_Response,
    GetNameList_Request,
    GetVariableAccessAttributes_Request,
    GetVariableAccessAttributes_Response,
    Identifier,
    Identify_Request,
    Initiate_RequestPDU,
    MMSpdu,
    ObjectClass,
    ObjectName,
    Read_Request,
    RejectPDU,
    Release_request_reason,
    ServiceError,
    Status_Request,
    StatusResponse,
    VariableAccessSpecification,
    VMDReset_Request,
    VMDStop_Request,
    Write_Request,
)
from icspacket.proto.mms.data import FileHandle
from icspacket.proto.mms.util import (
    ObjectScope,
    VariableAccessItem,
    new_initiate_request,
)
from icspacket.proto.mms.acse import (
    Association,
    Authenticator,
)
from icspacket.proto.mms.exceptions import (
    MMSConnectionError,
    MMSServiceError,
    MMSUnknownServiceError,
)

logger = logging.getLogger(__name__)


class MMS_Connection(connection):
    """
    Implementation of the MMS (Manufacturing Message Specification) connection
    handling (ISO 9506-1,2).

    This class provides a high-level MMS service endpoint on top of the ISO OSI stack.
    It integrates the following layers into a single connection object:

    .. code-block:: text

        +-----------------------------+
        | MMS (ISO 9506)              |
        +-----------------------------+
        | ACSE Association            |
        +-----------------------------+
        | ISO Presentation (ISO 8823) |
        +-----------------------------+
        | ISO Session (ISO 8327)      |
        +-----------------------------+
        | Transport (COTP, RFC 905)   |
        +-----------------------------+
        | TPKT / TCP                  |
        +-----------------------------+

    The class encapsulates these layers so that MMS service primitives such as
    :meth:`associate`, :meth:`release`, :meth:`abort`, and :meth:`close` can be
    directly invoked by the user without manually handling lower-layer PDUs.

    Establishing an MMS association to a remote server:

    .. code-block:: python

        from mms.connection import MMS_Connection

        # Create MMS connection
        mms_conn = MMS_Connection()

        # Connect and associate with a peer MMS user
        mms_conn.associate(("192.168.1.100", 102))
        assert mms_conn.is_valid():

        # Release the association in an orderly manner
        mms_conn.release()

    :param cotp_conn: Optional transport layer (COTP) connection to use. If not provided,
        a new :class:`COTP_Connection` is created using the default TPKT socket.
    :type cotp_conn: COTP_Connection | None
    :param session_config: Optional ISO Session settings, passed down to the session layer.
    :type session_config: ISO_SessionSettings | None
    :param presentation_config: Optional ISO Presentation settings, passed to the
        presentation layer.
    :type presentation_config: ISO_PresentationSettings | None
    :param auth: Optional ACSE :class:`Authenticator` instance for authentication handling.
    :type auth: Authenticator | None
    """

    def __init__(
        self,
        cotp_conn: COTP_Connection | None = None,
        session_config: ISO_SessionSettings | None = None,
        presentation_config: ISO_PresentationSettings | None = None,
        auth: Authenticator | None = None,
    ):
        # First, initialize the connection class and invalidate this connection
        super().__init__()

        # If the transport layer connection is not provided, create one
        if cotp_conn is None:
            cotp_conn = COTP_Connection(sock_cls=tpktsock)

        # We only store the presentation layer here. Transport layer can be accessed via
        # the session
        self.__presentation = ISO_Presentation(
            ISO_Session(cotp_conn, session_config),
            presentation_config,
        )
        self.__assoc = Association(
            presentation=self.presentation,
            pres_ctx_id=MMS_PRESENTATION_CONTEXT_ID,
            syntax_name=MMS_ABSTRACT_SYNTAX_NAME,
            asn1_cls=MMSpdu,
            authenticator=auth,
        )
        self._connected = self.presentation.is_connected()
        self.__invoke_id = 0

    # ---------------------------------------------------------------------- #
    # Properties
    # ---------------------------------------------------------------------- #
    @property
    def session(self) -> ISO_Session:
        """
        The ISO Session layer object.

        :return: Underlying ISO Session instance.
        :rtype: ISO_Session
        """
        return self.presentation.session

    @property
    def transport(self) -> COTP_Connection:
        """
        The transport layer (COTP) connection.

        :return: Underlying COTP transport connection.
        :rtype: COTP_Connection
        """
        return self.session.transport

    @property
    def presentation(self) -> ISO_Presentation:
        """
        The ISO Presentation layer object.

        :return: The presentation layer instance for this MMS connection.
        :rtype: ISO_Presentation
        """
        return self.__presentation

    @property
    def association(self) -> Association:
        """
        The ACSE Association handler for this MMS connection.

        :return: Association object responsible for ACSE/MMS binding.
        :rtype: Association
        """
        return self.__assoc

    @property
    def next_invoke_id(self) -> int:
        """
        Increment and return the next available invoke-id.

        This value is used to uniquely identify outstanding MMS service
        requests.

        :return: Next invoke identifier.
        :rtype: int
        """
        self.__invoke_id += 1
        return self.__invoke_id

    @property
    def invoke_id(self) -> int:
        """
        The current invoke-id counter.

        :return: Current invoke identifier.
        :rtype: int
        """
        return self.__invoke_id

    # ---------------------------------------------------------------------- #
    # MMS Connection Operations
    # ---------------------------------------------------------------------- #
    @override
    def connect(self, address: tuple[str, int]) -> None:
        """
        Establish a transport/session/presentation connection.

        If the connection is already established, this call is ignored.

        :param address: Remote address (host, port) to connect to.
        :type address: tuple[str, int]
        """
        if self.is_connected():
            return  # simply ignore this call to connect()

        self.association.connect(address)
        self._connected = self.association.is_connected()

    def associate(
        self,
        address: tuple[str, int] | None = None,
        request: Initiate_RequestPDU | None = None,
    ) -> None:
        """6.9.1 M-ASSOCIATE Service (ISO 9506-1).

        Establishes an MMS association with a peer MMS-user.

        This method performs the ACSE and MMS-level handshake by sending an
        Initiate Request PDU and validating the Initiate Response PDU.

        :param address: Optional peer address (host, port). If provided,
            a transport connection is established first.
        :type address: tuple[str, int] | None
        :param request: Optional Initiate Request PDU. If not provided,
            a default one is created using :func:`new_initiate_request`.
        :type request: Initiate_RequestPDU | None
        :raises MMSConnectionError: If the peer responds with an MMS error PDU.
        :raises TypeError: If the peer responds with an unexpected PDU type.
        """
        if self.is_valid():
            return

        if address:
            self.connect(address)

        # M-ASSOCIATE.req
        request = request or new_initiate_request()
        mms_pdu = MMSpdu(initiate_RequestPDU=request)

        raw_data = self.association.create(address, mms_pdu.ber_encode())
        try:
            # M-ASSOCIATE.cnf
            mms_pdu = MMSpdu.ber_decode(raw_data)
        except ValueError:
            raise TypeError(f"Received invalid ACSE associated data: {raw_data.hex()}")

        if mms_pdu.present == MMSpdu.PRESENT.PR_initiate_RequestPDU:
            raise MMSConnectionError(mms_pdu.initiate_ErrorPDU.value)

        if mms_pdu.present != MMSpdu.PRESENT.PR_initiate_ResponsePDU:
            raise TypeError(f"Received invalid MMS response: {mms_pdu.present}")

        self._valid = True

    def release(
        self,
        reason: Release_request_reason.VALUES | None = None,
        graceful: bool = False,
    ) -> None:
        """6.9.2 M-RELEASE Service (ISO 9506-1).

        Terminate the association in an orderly manner.

        :param reason: Optional release reason.
        :type reason: Release_request_reason.VALUES | None
        :param graceful: If ``True``, attempt a graceful release.
        :type graceful: bool
        """
        if not self.is_connected():
            return

        self.association.release(reason, graceful)
        self._connected = False
        self._valid = False

    def abort(self, source: ABRT_source.VALUES | None = None) -> None:
        """6.9.4 M-U-ABORT Service (ISO 9506-1).

        Abruptly terminate the association without completing an orderly
        release handshake.

        :param source: Optional abort source identifier.
        :type source: ABRT_source.VALUES | None
        """
        self.association.abort(source)
        self._connected = False
        self._valid = False

    @override
    def close(self) -> None:
        """
        Close the MMS association and underlying presentation connection.

        This performs a Conclude handshake (``Conclude-Request`` /
        ``Conclude-Response``). If the peer responds with an error,
        :class:`MMSConnectionError` is raised.

        :raises MMSConnectionError: If the peer responds with a conclude error.
        :raises TypeError: If the peer responds with an unexpected PDU.
        """
        if not self.is_connected():
            return

        pdu = Conclude_RequestPDU()
        pdu.value = None
        mms_pdu = MMSpdu(conclude_RequestPDU=pdu)
        self.send_mms_data(mms_pdu)

        response = self.recv_mms_data()
        match response.present:
            case MMSpdu.PRESENT.PR_conclude_ErrorPDU:
                raise MMSConnectionError(response.conclude_ErrorPDU.value)
            case MMSpdu.PRESENT.PR_conclude_ResponsePDU:
                self.presentation.close()
                self._valid = False
                self._connected = False
            case _:
                raise TypeError(f"Received invalid MMS response: {response.present}")

    # ---------------------------------------------------------------------- #
    # Data Exchange
    # ---------------------------------------------------------------------- #
    @override
    def send_data(self, octets: bytes, /) -> None:
        """
        Send raw BER-encoded MMS data.

        :param octets: BER-encoded MMS PDU.
        :type octets: bytes
        :raises AssertionError: If the connection is not established.
        """
        self._assert_connected()
        self.presentation.send_encoded_data(octets, MMS_PRESENTATION_CONTEXT_ID)

    def send_mms_data(self, pdu: MMSpdu, /) -> None:
        """
        Send an MMS PDU after BER encoding.

        :param pdu: MMS PDU to send.
        :type pdu: MMSpdu
        """
        self.send_data(pdu.ber_encode())

    def recv_mms_data(self) -> MMSpdu:
        """
        Receive and decode an MMS PDU.

        :return: Decoded MMS PDU.
        :rtype: MMSpdu
        :raises TypeError: If the received data is not an MMS PDU.
        """
        pdu = self.presentation.recv_encoded_data()
        if not isinstance(pdu, MMSpdu):
            raise TypeError(f"Received invalid MMS data: {type(pdu)}")
        return pdu

    # ---------------------------------------------------------------------------
    # 10 VMD Support Services
    # ---------------------------------------------------------------------------
    def get_status(
        self, ex_derivation: bool = False
    ) -> tuple[
        StatusResponse.vmdLogicalStatus_VALUES, StatusResponse.vmdPhysicalStatus_VALUES
    ]:
        """10.3 Status Service

        The *Status* service is used by an MMS client to determine the
        general condition or health of a VMD (Virtual Manufacturing Device).

        :param ex_derivation: If ``True``, requests an *extended derivation*
                              of the status response. This influences how the
                              server derives the logical and physical VMD status
                              (see ISO 9506-1, 10.3.1.1.1).
        :type ex_derivation: bool

        :returns: A tuple ``(logical_status, physical_status)``, where:

            * ``logical_status`` is of type
              :class:`StatusResponse.vmdLogicalStatus_VALUES`.
            * ``physical_status`` is of type
              :class:`StatusResponse.vmdPhysicalStatus_VALUES`.

        :rtype: tuple

        Example:

        >>> logical, physical = mms_conn.get_status()
        >>> print(f"Logical VMD status: {logical!r}, Physical VMD status: {physical!r}")
        """
        request = Status_Request()
        # 10.3.1.1.1 Extended Derivation
        # This parameter, of type boolean, shall indicate which method is to be
        # used to derive the Status response.
        request.value = ex_derivation

        service = ConfirmedServiceRequest(status=request)
        response = self.service_request(service)
        status = response.status.value
        return (status.vmdLogicalStatus, status.vmdPhysicalStatus)

    def get_name_list(
        self,
        object_class: ObjectClass,
        scope: ObjectScope | None = None,
    ) -> list[str]:
        """10.5 GetNameList Service

        The *GetNameList* service requests the list (or a subset) of object
        names defined at the VMD. The server may return the list in segments
        if it is too long to fit in a single response.

        :param object_class: The class of objects for which names are requested.
            For example: ``ObjectClass.namelist.domain``.
        :type object_class: ObjectClass
        :param scope: Optional scope of the name list request. If not provided,
            defaults to VMD-specific scope.
        :type scope: GetNameList_Request.objectScope_TYPE or None

        :returns: A list of object identifiers.
        :rtype: list[str]

        :raises ValueError: If the MMS server returns an invalid response.

        Example:

        >>> domains = mms_conn.get_name_list(ObjectClass.domain)
        >>> print("Available domains:", domains)
        """
        identifiers = []
        request = GetNameList_Request()
        # This parameter shall specify the object class of the object name to be
        # returned by the responding MMS-user.
        request.objectClass = object_class

        # This parameter shall indicate the scope of the object name list to be
        # returned.
        if scope is None:
            scope = GetNameList_Request.objectScope_TYPE()
            scope.vmdSpecific = None

        request.objectScope = scope

        service = ConfirmedServiceRequest(getNameList=request)
        response = self.service_request(service)
        name_list = response.getNameList
        if name_list is None:
            raise ValueError("Received invalid GetNameList response")

        identifiers.extend(list(name_list.listOfIdentifier))
        more_follows = name_list.moreFollows
        while more_follows:
            # 10.5.1.2.2 More Follows
            # This parameter, of type boolean, shall indicate whether additional
            # GetNameList requests are necessary to retrieve all of the
            # requested information. If true, more requests are necessary (if
            # the MMS client wishes to retrieve more data).
            request.continueAfter = identifiers[-1]
            service = ConfirmedServiceRequest(getNameList=request)
            response = self.service_request(service)
            assert response.present == ConfirmedServiceResponse.getNameList
            identifiers.extend(list(response.getNameList.listOfIdentifier))
            more_follows = response.getNameList.moreFollows

        return identifiers

    def identify(self) -> tuple[str, str, str]:
        """10.6 Identify Service

        The *Identify* service retrieves the vendor, model, and revision
        information of the remote MMS VMD.

        :returns: A tuple ``(vendor_name, model_name, revision)`` with all
            fields mandatory as per ISO 9506-2.
        :rtype: tuple[str, str, str]

        >>> vendor, model, revision = mms_conn.identify()
        >>> print(f"Device: {vendor} {model} (rev {revision})")
        """
        request = Identify_Request()
        service = ConfirmedServiceRequest(identify=request)
        response = self.service_request(service)
        identify = response.identify
        return (
            identify.vendorName.value,  # M (mandatory)
            identify.modelName.value,  # M (mandatory)
            identify.revision.value,  # M (mandatory)
        )

    def get_capabilities(self) -> list[str]:
        """10.8 GetCapabilityList Service

        The *GetCapabilityList* service requests the list of services or
        features supported by the remote MMS server. Like *GetNameList*,
        the response may be segmented and require multiple follow-up requests.

        :returns: A list of capability strings supported by the server.
        :rtype: list[str]

        Example:

        >>> caps = mms_conn.get_capabilities()
        >>> print("Server capabilities:", caps)
        """
        request = GetCapabilityList_Request()
        service = ConfirmedServiceRequest(getCapabilityList=request)
        response = self.service_request(service)

        capabilities = []
        # same as in get_name_list
        capabilities.extend(list(response.getCapabilityList.listOfCapabilities))
        more_follows = response.getCapabilityList.moreFollows
        while more_follows:
            # This parameter, of type boolean, shall indicate whether additional
            # GetCapabilityList requests are necessary to retrieve more of the
            # requested information.
            service.getCapabilityList.continueAfter = capabilities[-1]
            response = self.service_request(service)

            capabilities.extend(list(response.getCapabilityList.listOfCapabilities))
            more_follows = response.getCapabilityList.moreFollows
        return capabilities

    def vmd_stop(self) -> None:
        request = VMDStop_Request()
        service = AdditionalService_Request(vMDStop=request)
        # request.value = None
        _ = self.additional_service_request(service)

    def vmd_reset(self) -> None:
        request = VMDReset_Request()
        service = AdditionalService_Request(vMDReset=request)
        # request.value = None
        _ = self.additional_service_request(service)

    # ---------------------------------------------------------------------------
    # 14 Variable Access Services
    # ---------------------------------------------------------------------------
    def read_variables(
        self,
        *pos_variables: VariableAccessItem,
        variables: list[VariableAccessItem] | None = None,
        spec_in_result: bool = False,
        list_name: ObjectName | None = None,
    ) -> list[AccessResult]:
        """14.6 Variable Read Service

        Reads one or more variables or an entire variable list from the
        remote MMS server.

        :param pos_variables: Positional list of variables to read.
        :type pos_variables: VariableAccessItem
        :param variables: Alternative way of specifying variables via keyword.
        :type variables: list[VariableAccessItem] or None
        :param spec_in_result: If ``True``, requests that the server return
            the *VariableAccessSpecification* in the response (14.6.1.1.1).
            Usually ``False`` for efficiency.
        :type spec_in_result: bool
        :param list_name: If set, references a named variable list to read
            instead of individual variables.
        :type list_name: ObjectName or None

        :returns: A list of :class:`AccessResult` objects, one per variable read.
        :rtype: list[AccessResult]

        :raises ValueError: If no variables or list_name is provided, or if both
            are specified at once.

        Example (read two variables):

        >>> var1 = VariableAccessItem(name=ObjectName(vmd_specific="TempSensor1"))
        >>> var2 = VariableAccessItem(name=ObjectName(vmd_specific="TempSensor2"))
        >>> results = mms_conn.read_variables(var1, var2)
        >>> for res in results:
        ...     print(res.success)  # AccessResult can be success or failure
        """
        variables = variables or []
        if len(pos_variables) > 0:
            variables.extend(pos_variables)

        if len(variables) == 0:
            if list_name is None:
                raise ValueError(
                    "Need at least one variable or a variable list name to read"
                )
        else:
            if list_name is not None:
                raise ValueError(
                    "Can't specify both list of variables and variable list name"
                )

        request = Read_Request()
        # 14.6.1.1.1 Specification With Result
        # This boolean parameter shall indicate whether (true) or not (false) the
        # Variable Access Specification parameter is requested in the Result(+)
        # parameter of the response primitive, if issued.
        request.specificationWithResult = spec_in_result
        if list_name is None:
            request.variableAccessSpecification.listOfVariable = list(variables)
        else:
            request.variableAccessSpecification.variableListName = list_name

        service = ConfirmedServiceRequest(read=request)
        response = self.service_request(service)
        read_result = response.read

        return list(read_result.listOfAccessResult)

    def write_variable(
        self,
        variable: VariableAccessSpecification.listOfVariable_TYPE.Member_TYPE,
        value: Data,
    ) -> DataAccessError | None:
        """14.7 Variable Write Service

        Writes the value of a single variable at the MMS server.

        :param variable: The target variable to be written.
        :type variable: VariableAccessSpecification.listOfVariable_TYPE.Member_TYPE
        :param value: The value to write, encoded as MMS :class:`Data`.
        :type value: Data

        :returns: ``None`` on success, or a :class:`DataAccessError` if the
            write failed for this variable.
        :rtype: DataAccessError or None

        Example (write a new integer value):

        >>> var = VariableAccessItem(name=ObjectName(vmd_specific="SetPoint"))
        >>> data = Data()
        >>> data.integer = 42
        >>> err = mms_conn.write_variable(var, data)
        >>> print("Write successful" if err is None else f"Failed: {err}")
        """
        request = Write_Request()
        request.variableAccessSpecification.listOfVariable = [variable]
        request.listOfData = [value]

        service = ConfirmedServiceRequest(write=request)
        response = self.service_request(service, need_response=False)
        if response is not None:
            write_results = response.write
            # this automatically returns None on success
            return write_results[0].failure.value

    def variable_attributes(
        self, *, name: ObjectName | None = None, address: Address | None = None
    ) -> GetVariableAccessAttributes_Response:
        """14.9 GetVariableAccessAttributes Service

        Retrieves metadata describing a variable, such as its type,
        address, and whether it is deletable or modifiable.

        :param name: The object name of the variable to query.
        :type name: ObjectName or None
        :param address: The variable's address (alternative to name).
        :type address: Address or None

        :returns: The variable access attributes response from the MMS server.
        :rtype: GetVariableAccessAttributes_Response

        :raises ValueError: If neither ``name`` nor ``address`` is specified,
            or if both are given at the same time.

        Example (query attributes by name):

        >>> obj = ObjectName(vmd_specific="TempSensor1")
        >>> attrs = mms_conn.variable_attributes(name=obj)
        >>> print("Type description:", attrs.typeDescription)
        """
        if not name and not address:
            raise ValueError("Need either name or address")

        if name and address:
            raise ValueError("Can't specify both name and address")

        request = GetVariableAccessAttributes_Request()
        if name:
            request.name = name
        else:
            request.address = address

        service = ConfirmedServiceRequest(getVariableAccessAttributes=request)
        response = self.service_request(service)
        return response.getVariableAccessAttributes

    # ---------------------------------------------------------------------------
    # 11 Domain Services
    # ---------------------------------------------------------------------------
    def domain_get_attributes(
        self, domain: DomainName | str
    ) -> GetDomainAttributes_Response:
        request = GetDomainAttributes_Request(domain)
        service = ConfirmedServiceRequest(getDomainAttributes=request)
        response = self.service_request(service)
        return response.getDomainAttributes

    # ---------------------------------------------------------------------------
    # Annex D - File Management
    # ---------------------------------------------------------------------------
    def file_open(self, name: FileName, offset: int = 0) -> FileHandle:
        """D.3 FileOpen Service

        Opens a file in the MMS server's virtual filestore and returns a
        handle used for subsequent file operations (read, close, etc.).

        :param name: The file name to open.
        :type name: FileName
        :param offset: Initial byte offset from which to start reading.
            Defaults to ``0`` (beginning of the file).
        :type offset: int, optional

        :returns: A file handle including the FRSM ID and file attributes.
        :rtype: FileHandle

        Example (complete):
        >>> # Open a file for reading
        >>> handle = mms_conn.file_open(FileName(["/logs/system.log"]))
        >>> # Read complete file
        >>> data = mms_conn.file_read(handle)
        >>> print(data.decode("utf-8")[:200])  # show first 200 characters
        >>> # Close the file handle
        >>> mms_conn.file_close(handle)
        """
        request = FileOpen_Request()
        request.fileName = name
        request.initialPosition = offset

        service = ConfirmedServiceRequest(fileOpen=request)
        response = self.service_request(service)
        handle = FileHandle(
            response.fileOpen.frsmID.value, response.fileOpen.fileAttributes
        )
        return handle

    def file_read_chunk(self, handle: FileHandle | int) -> tuple[bytes, bool]:
        """D.4 FileRead (chunked)

        Reads a chunk of data from an open file handle.

        :param handle: A :class:`FileHandle` or raw FRSM ID.
        :type handle: FileHandle or int

        :returns: A tuple ``(data, more_follows)`` where:
            - ``data`` is a bytes object containing the chunk read.
            - ``more_follows`` is a boolean indicating if further reads are required.
        :rtype: tuple[bytes, bool]

        >>> chunk, more = mms_conn.file_read_chunk(handle)
        >>> print(len(chunk), "bytes read, more follows?", more)
        """
        fp = handle.handle if isinstance(handle, FileHandle) else handle
        request = FileRead_Request(fp)
        service = ConfirmedServiceRequest(fileRead=request)
        response = self.service_request(service)

        data = response.fileRead.fileData
        more_follows = response.fileRead.moreFollows
        return data, bool(more_follows)

    def file_read(self, handle: FileHandle | int) -> bytes:
        """D.4 FileRead (complete)

        Reads the entire content of a file by repeatedly fetching
        chunks until ``moreFollows`` is false.

        :param handle: A :class:`FileHandle` or raw FRSM ID.
        :type handle: FileHandle or int

        :returns: Complete file contents as bytes.
        :rtype: bytes
        """
        more_follows = True
        result = []
        while more_follows:
            chunk, more_follows = self.file_read_chunk(handle)
            result.append(chunk)

        return b"".join(result)

    def file_close(self, handle: FileHandle | int) -> None:
        """D.5 FileClose Service

        Closes an open file handle. This releases the FRSM ID
        allocated by the server.

        :param handle: A :class:`FileHandle` or raw FRSM ID.
        :type handle: FileHandle or int
        """
        fp = handle.handle if isinstance(handle, FileHandle) else handle
        request = FileClose_Request(fp)
        service = ConfirmedServiceRequest(fileClose=request)
        _ = self.service_request(service)

    def file_rename(self, old_name: FileName, new_name: FileName) -> None:
        """D.6 FileRename Service

        Renames a file in the server's virtual filestore.

        :param old_name: The current file name.
        :type old_name: FileName
        :param new_name: The new file name to assign.
        :type new_name: FileName

        Example:

        >>> mms_conn.file_rename(FileName(["/logs/old.log"]),
        ...                      FileName(["/logs/new.log"]))
        """
        request = FileRename_Request(currentFileName=old_name, newFileName=new_name)
        service = ConfirmedServiceRequest(fileRename=request)
        _ = self.service_request(service)

    def file_delete(self, name: FileName) -> None:
        """D.7 FileDelete Service

        Deletes a file from the MMS server's virtual filestore.

        :param name: The file name to delete.
        :type name: FileName

        Example:

        >>> mms_conn.file_delete(FileName(["/logs/obsolete.log"]))
        """
        request = FileDelete_Request(name)
        service = ConfirmedServiceRequest(fileDelete=request)
        _ = self.service_request(service)

    def list_directory(self, name: FileName | None = None) -> list[DirectoryEntry]:
        """D.8 FileDirectory Service

        Retrieves directory listings or file attributes from the
        server's virtual filestore.

        :param name: Optional file or directory name pattern. If omitted,
            the server returns an implementation-defined default set.
        :type name: FileName or None

        :returns: List of directory entries, possibly spanning multiple responses.
        :rtype: list[DirectoryEntry]

        Example:

        >>> entries = mms_conn.list_directory()
        >>> for e in entries:
        ...     print(e.fileName[0], e.fileAttributes.fileSize)
        """
        request = FileDirectory_Request()
        # D.8.1.1.1 File Specification
        # This optional parameter, of type FileName, shall, when present,
        # identify a file or group of files in the MMS server's virtual
        # filestore whose attributes are desired. Omission of this parameter
        # shall indicate that the attributes of an implementation defined
        # default group of files are being requested.
        if name is not None:
            request.fileSpecification = name
        else:
            request.fileSpecification = None

        service = ConfirmedServiceRequest(fileDirectory=request)
        response = self.service_request(service)
        entries = list(response.fileDirectory.listOfDirectoryEntry)
        more_follows = response.fileDirectory.moreFollows
        while more_follows:
            request.continueAfter = entries[-1]
            response = self.service_request(service)
            entries.extend(list(response.fileDirectory.listOfDirectoryEntry))
            more_follows = response.fileDirectory.moreFollows
        return entries

    # ---------------------------------------------------------------------------
    # Service Requests
    # ---------------------------------------------------------------------------
    def additional_service_request(
        self, request: AdditionalService_Request
    ) -> AdditionalService_Response:
        """
        Issues an MMS **Additional Service** request (ISO 9506-1:1990, Clause 19).

        This is a specialized helper that wraps an
        :class:`~AdditionalService_Request` in a
        :class:`~ConfirmedServiceRequest` and dispatches it via
        :meth:`service_request`.

        It is rarely used directly, but provides a template for invoking
        "non-standardized" or vendor-specific services.

        :param request: The additional service request to send.
        :type request: AdditionalService_Request

        :returns: The decoded additional service response from the server.
        :rtype: AdditionalService_Response

        Example:

        >>> req = AdditionalService_Request()
        >>> # populate request with service-specific fields
        >>> resp = mms_conn.additional_service_request(req)
        >>> print(resp)
        """
        service = ConfirmedServiceRequest(additionalService=request)
        response = self.service_request(service)
        return response.additionalService

    def service_request(
        self,
        request: ConfirmedServiceRequest,
        need_response: bool = True,
    ) -> ConfirmedServiceResponse:
        """
        Issues a **generic MMS Confirmed Service Request** and returns
        the corresponding Confirmed Service Response.

        This is the central method through which *all* MMS services
        are ultimately invoked. Higher-level convenience wrappers
        (e.g., :meth:`read_variables`, :meth:`file_open`, etc.)
        construct the appropriate
        :class:`~ConfirmedServiceRequest` and delegate to this method.

        **Workflow:**

        1. A new :class:`Confirmed_RequestPDU` is allocated and
            tagged with the next available ``invokeID``.
        2. The caller-supplied ``request`` is embedded into the PDU.
        3. The request is wrapped into an :class:`MMSpdu`.
        4. Transmission is performed using
            :meth:`send_mms_data`.
        5. A response is awaited via :meth:`recv_mms_data`.
        6. Any detected service error is normalized using
            :meth:`_error_from_service_response`.
        7. The decoded :class:`ConfirmedServiceResponse`
            is returned to the caller.

        :param request: The service request PDU, e.g.
            :class:`Read_Request`, :class:`FileOpen_Request`, etc.,
            wrapped in a :class:`ConfirmedServiceRequest`.
        :type request: ConfirmedServiceRequest

        :param need_response: Whether a response is required.
            If ``False``, the method will still wait for the server
            response (ISO 9506-2 requires this) but certain services
            may ignore the payload.
        :type need_response: bool, optional

        :raises MMSConnectionError: If the response indicates a service error.
        :raises MMSServiceError: For generic or protocol-level failures.
        :raises MMSUnknownServiceError: If the service response cannot
            be mapped to a known type.

        :returns: The ``service`` component of the decoded
            :class:`ConfirmedServiceResponse`, containing the
            service-specific result (e.g. a :class:`Read_Response`).
        :rtype: ConfirmedServiceResponse

        Example:

        >>> # Manually constructing a Read request
        >>> read_req = Read_Request()
        >>> read_req.variableAccessSpecification.listOfVariable = [var]
        >>> csr = ConfirmedServiceRequest(read=read_req)
        >>> resp = mms_conn.service_request(csr)
        >>> print(resp.read.listOfAccessResult)
        """
        pdu = Confirmed_RequestPDU()
        pdu.invokeID = self.next_invoke_id
        pdu.service = request

        mms_pdu = MMSpdu(confirmed_RequestPDU=pdu)
        self.send_mms_data(mms_pdu)
        response = self.recv_mms_data()
        error = self._error_from_service_response(request, response, need_response)
        if error is not None:
            raise error

        return response.confirmed_ResponsePDU.service

    # --- private ugly code
    def _error_from_service_response(
        self,
        request: ConfirmedServiceRequest,
        response: MMSpdu,
        need_response: bool,
    ) -> Exception | None:
        if response.present == MMSpdu.PRESENT.PR_confirmed_ErrorPDU:
            return self._error_from_pdu(
                request.present.name, response.confirmed_ErrorPDU
            )

        if response.present == MMSpdu.PRESENT.PR_rejectPDU:
            # unknown service
            reason = response.rejectPDU.rejectReason
            assert (
                reason.present
                == RejectPDU.rejectReason_TYPE.PRESENT.PR_confirmed_requestPDU
            )
            match reason.confirmed_requestPDU:
                case RejectPDU.rejectReason_TYPE.confirmed_requestPDU_VALUES.V_unrecognized_service:
                    return MMSUnknownServiceError(
                        f"Peer rejected unrecognized service request of type: {request.present.name[3:]!r}"
                    )
                case _:
                    return MMSServiceError(
                        f"Failed service request of type: {request.present!r} with "
                        + f"reason: {reason.confirmed_requestPDU}"
                    )

        if response.present != MMSpdu.PRESENT.PR_confirmed_ResponsePDU:
            if not need_response:
                return None

            return MMSServiceError(
                f"Received invalid MMS response: {response.present!r} - "
                + f"expected response for {request.present!r}"
            )

        pdu = response.confirmed_ResponsePDU
        if not pdu:
            return MMSServiceError(
                f"Failed service request of type: {request.present!r} (empty response)"
            )

        if pdu.invokeID.value != self.invoke_id:
            return MMSServiceError(
                f"Response invokeID ({pdu.invokeID}) does not match "
                + f"request invokeID ({self.invoke_id})"
            )

        if pdu.service.present != request.present:
            return MMSServiceError(
                f"Response service type ({pdu.service.present!r}) does not match "
                + f"request service type ({request.present!r})"
            )

        return None

    def _error_from_pdu(self, name: str, errpr_pdu: Confirmed_ErrorPDU) -> Exception:
        error = errpr_pdu.serviceError
        class_ = error.errorClass
        msg = f"{class_.present.name}: Failed request of type {name!r}"
        # fmt: off
        match class_.present:
            case ServiceError.errorClass_TYPE.PRESENT.PR_vmd_state:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.vmd_state.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_application_reference:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.application_reference.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_definition:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.definition.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_resource:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.resource.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_service:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.service.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_service_preempt:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.service_preempt.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_time_resolution:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.time_resolution.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_access:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.access.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_initiate:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.initiate.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_conclude:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.conclude.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_cancel:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.cancel.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_file:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.file.name!r}")
            case ServiceError.errorClass_TYPE.PRESENT.PR_others:
                return MMSConnectionError(error, f"{msg}, reason: {error.errorClass.others!r}")
            case _:
                return MMSConnectionError(error, msg)
        # fmt: on
