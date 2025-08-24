from enum import IntEnum as EXT_IntEnum
from typing import (
	Generic as EXT_Generic,
	TypeVar as EXT_TypeVar,
	Iterable as EXT_Iterable,
	type_check_only as EXT_type_check_only,
)
from typing_extensions import override as EXT_override

from bitarray import bitarray as EXT_bitarray


_PY_T = EXT_TypeVar("_PY_T")
_ASN_T = EXT_TypeVar("_ASN_T", bound="_Asn1Type")

@EXT_type_check_only
class _Asn1Type:
	@EXT_override
	def __repr__(self) -> str: ...
	@EXT_override
	def __str__(self) -> str: ...
	def is_valid(self) -> bool: ...
	def check_constraints(self) -> None: ...
	def ber_encode(self) -> bytes: ...
	@classmethod
	def ber_decode(cls: type[_ASN_T], data: bytes) -> _ASN_T: ...
	def cer_encode(self) -> bytes: ...
	@classmethod
	def cer_decode(cls: type[_ASN_T], data: bytes) -> _ASN_T: ...
	def der_encode(self) -> bytes: ...
	@classmethod
	def der_decode(cls: type[_ASN_T], data: bytes) -> _ASN_T: ...
	def xer_encode(self, /, *, canonical: bool = ...) -> bytes: ...
	@classmethod
	def xer_decode(cls: type[_ASN_T], data: bytes, /, *, canonical: bool = ...) -> _ASN_T: ...
	def jer_encode(self, /, *, minified: bool = ...) -> bytes: ...
	@classmethod
	def jer_decode(cls: type[_ASN_T], data: bytes, /, *, minified: bool = ...) -> _ASN_T: ...
	def to_text(self) -> bytes: ...

@EXT_type_check_only
class _Asn1BasicType(EXT_Generic[_PY_T], _Asn1Type):
	def __init__(self, value: _PY_T = ...) -> None: ...
	@property
	def value(self) -> _PY_T: ...
	@value.setter
	def value(self, value: _PY_T) -> None: ...


@EXT_type_check_only
class _Asn1BitStrType(_Asn1Type):
	def __init__(self, size: int = ...) -> None: ...
	@property
	def value(self) -> EXT_bitarray | bytes: ...
	@value.setter
	def value(self, value: EXT_bitarray | bytes) -> None: ...
	def clear(self) -> None: ...
	def set(self, bit: int, flag: bool) -> None: ...
	def get(self, bit: int) -> bool: ...
	def size(self) -> int: ...
	def resize(self, size: int) -> None: ...

### BEGIN GENERATED CODE ###
class EMBEDDED_PDV(_Asn1Type): # SEQUENCE

	class identification_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_syntaxes = 1
			PR_syntax = 2
			PR_presentation_context_id = 3
			PR_context_negotiation = 4
			PR_transfer_syntax = 5
			PR_fixed = 6

		@property
		def present(self) -> PRESENT: ...

		class syntaxes_TYPE(_Asn1Type): # SEQUENCE
			abstract: str
			transfer: str
			def __init__(
				self, /, *,
				abstract: str = ...,
				transfer: str = ...,
			) -> None: ...

		syntaxes: syntaxes_TYPE

		class context_negotiation_TYPE(_Asn1Type): # SEQUENCE
			presentation_context_id: int
			transfer_syntax: str
			def __init__(
				self, /, *,
				presentation_context_id: int = ...,
				transfer_syntax: str = ...,
			) -> None: ...

		context_negotiation: context_negotiation_TYPE
		syntax: str | None
		presentation_context_id: int | None
		transfer_syntax: str | None
		fixed: None | None
		def __init__(
			self, /, *,
			syntaxes: syntaxes_TYPE = ...,
			syntax: str = ...,
			presentation_context_id: int = ...,
			context_negotiation: context_negotiation_TYPE = ...,
			transfer_syntax: str = ...,
			fixed: None = ...,
		) -> None: ...

	identification: identification_TYPE
	data_value: bytes
	def __init__(
		self, /, *,
		identification: identification_TYPE = ...,
		data_value: bytes = ...,
	) -> None: ...

class TimeOfDay(_Asn1BasicType[bytes]):
	pass

class Identifier(_Asn1BasicType[str]):
	pass

class Integer8(_Asn1BasicType[int]):
	pass

class Integer16(_Asn1BasicType[int]):
	pass

class Integer32(_Asn1BasicType[int]):
	pass

class Unsigned8(_Asn1BasicType[int]):
	pass

class Unsigned16(_Asn1BasicType[int]):
	pass

class Unsigned32(_Asn1BasicType[int]):
	pass

class ObjectName(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_vmd_specific = 1
		PR_domain_specific = 2
		PR_aa_specific = 3

	@property
	def present(self) -> PRESENT: ...

	class domain_specific_TYPE(_Asn1Type): # SEQUENCE
		@property
		def domainID(self) -> Identifier: ...
		@domainID.setter
		def domainID(self, value: Identifier | str) -> None: ...
		@property
		def itemID(self) -> Identifier: ...
		@itemID.setter
		def itemID(self, value: Identifier | str) -> None: ...
		def __init__(
			self, /, *,
			domainID: Identifier = ...,
			itemID: Identifier = ...,
		) -> None: ...

	domain_specific: domain_specific_TYPE
	@property
	def vmd_specific(self) -> Identifier | None: ...
	@vmd_specific.setter
	def vmd_specific(self, value: Identifier | str | None) -> None: ...
	@property
	def aa_specific(self) -> Identifier | None: ...
	@aa_specific.setter
	def aa_specific(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		vmd_specific: Identifier = ...,
		domain_specific: domain_specific_TYPE = ...,
		aa_specific: Identifier = ...,
	) -> None: ...

class ObjectClass(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_basicObjectClass = 1
		PR_csObjectClass = 2

	@property
	def present(self) -> PRESENT: ...

	class basicObjectClass_VALUES(EXT_IntEnum):
		V_namedVariable = 0
		V_scatteredAccess = 1
		V_namedVariableList = 2
		V_namedType = 3
		V_semaphore = 4
		V_eventCondition = 5
		V_eventAction = 6
		V_eventEnrollment = 7
		V_journal = 8
		V_domain = 9
		V_programInvocation = 10
		V_operatorStation = 11
		V_dataExchange = 12
		V_accessControlList = 13

	basicObjectClass: basicObjectClass_VALUES | None

	class csObjectClass_VALUES(EXT_IntEnum):
		V_eventConditionList = 0
		V_unitControl = 1

	csObjectClass: csObjectClass_VALUES | None
	def __init__(
		self, /, *,
		basicObjectClass: basicObjectClass_VALUES = ...,
		csObjectClass: csObjectClass_VALUES = ...,
	) -> None: ...

class MMSString(_Asn1BasicType[str]):
	pass

class MMS255String(_Asn1BasicType[str]):
	pass

class FileName(_Asn1Type):
	def __init__(self, values: EXT_Iterable[str] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> str: ...
	def __setitem__(self, index: int, value: str) -> None: ...
	def add(self, value: str) -> None: ...
	def extend(self, values: EXT_Iterable[str]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class MMSpdu(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_confirmed_RequestPDU = 1
		PR_confirmed_ResponsePDU = 2
		PR_confirmed_ErrorPDU = 3
		PR_unconfirmed_PDU = 4
		PR_rejectPDU = 5
		PR_cancel_RequestPDU = 6
		PR_cancel_ResponsePDU = 7
		PR_cancel_ErrorPDU = 8
		PR_initiate_RequestPDU = 9
		PR_initiate_ResponsePDU = 10
		PR_initiate_ErrorPDU = 11
		PR_conclude_RequestPDU = 12
		PR_conclude_ResponsePDU = 13
		PR_conclude_ErrorPDU = 14

	@property
	def present(self) -> PRESENT: ...
	confirmed_RequestPDU: Confirmed_RequestPDU | None
	confirmed_ResponsePDU: Confirmed_ResponsePDU | None
	confirmed_ErrorPDU: Confirmed_ErrorPDU | None
	unconfirmed_PDU: Unconfirmed_PDU | None
	rejectPDU: RejectPDU | None
	cancel_RequestPDU: Cancel_RequestPDU | None
	cancel_ResponsePDU: Cancel_ResponsePDU | None
	cancel_ErrorPDU: Cancel_ErrorPDU | None
	initiate_RequestPDU: Initiate_RequestPDU | None
	initiate_ResponsePDU: Initiate_ResponsePDU | None
	initiate_ErrorPDU: Initiate_ErrorPDU | None
	@property
	def conclude_RequestPDU(self) -> Conclude_RequestPDU | None: ...
	@conclude_RequestPDU.setter
	def conclude_RequestPDU(self, value: Conclude_RequestPDU | None | None) -> None: ...
	@property
	def conclude_ResponsePDU(self) -> Conclude_ResponsePDU | None: ...
	@conclude_ResponsePDU.setter
	def conclude_ResponsePDU(self, value: Conclude_ResponsePDU | None | None) -> None: ...
	conclude_ErrorPDU: Conclude_ErrorPDU | None
	def __init__(
		self, /, *,
		confirmed_RequestPDU: Confirmed_RequestPDU = ...,
		confirmed_ResponsePDU: Confirmed_ResponsePDU = ...,
		confirmed_ErrorPDU: Confirmed_ErrorPDU = ...,
		unconfirmed_PDU: Unconfirmed_PDU = ...,
		rejectPDU: RejectPDU = ...,
		cancel_RequestPDU: Cancel_RequestPDU = ...,
		cancel_ResponsePDU: Cancel_ResponsePDU = ...,
		cancel_ErrorPDU: Cancel_ErrorPDU = ...,
		initiate_RequestPDU: Initiate_RequestPDU = ...,
		initiate_ResponsePDU: Initiate_ResponsePDU = ...,
		initiate_ErrorPDU: Initiate_ErrorPDU = ...,
		conclude_RequestPDU: Conclude_RequestPDU = ...,
		conclude_ResponsePDU: Conclude_ResponsePDU = ...,
		conclude_ErrorPDU: Conclude_ErrorPDU = ...,
	) -> None: ...

class Confirmed_RequestPDU(_Asn1Type): # SEQUENCE

	class listOfModifiers_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Modifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Modifier: ...
		def __setitem__(self, index: int, value: Modifier) -> None: ...
		def add(self, value: Modifier) -> None: ...
		def extend(self, values: EXT_Iterable[Modifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfModifiers: listOfModifiers_TYPE | None
	@property
	def invokeID(self) -> Unsigned32: ...
	@invokeID.setter
	def invokeID(self, value: Unsigned32 | int) -> None: ...
	service: ConfirmedServiceRequest
	service_ext: Request_Detail | None
	def __init__(
		self, /, *,
		invokeID: Unsigned32 = ...,
		listOfModifiers: listOfModifiers_TYPE = ...,
		service: ConfirmedServiceRequest = ...,
		service_ext: Request_Detail = ...,
	) -> None: ...

class Confirmed_ErrorPDU(_Asn1Type): # SEQUENCE
	@property
	def invokeID(self) -> Unsigned32: ...
	@invokeID.setter
	def invokeID(self, value: Unsigned32 | int) -> None: ...
	@property
	def modifierPosition(self) -> Unsigned32 | None: ...
	@modifierPosition.setter
	def modifierPosition(self, value: Unsigned32 | int | None) -> None: ...
	serviceError: ServiceError
	def __init__(
		self, /, *,
		invokeID: Unsigned32 = ...,
		modifierPosition: Unsigned32 = ...,
		serviceError: ServiceError = ...,
	) -> None: ...

class ConfirmedServiceRequest(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_status = 1
		PR_getNameList = 2
		PR_identify = 3
		PR_rename = 4
		PR_read = 5
		PR_write = 6
		PR_getVariableAccessAttributes = 7
		PR_defineNamedVariable = 8
		PR_defineScatteredAccess = 9
		PR_getScatteredAccessAttributes = 10
		PR_deleteVariableAccess = 11
		PR_defineNamedVariableList = 12
		PR_getNamedVariableListAttributes = 13
		PR_deleteNamedVariableList = 14
		PR_defineNamedType = 15
		PR_getNamedTypeAttributes = 16
		PR_deleteNamedType = 17
		PR_input = 18
		PR_output = 19
		PR_takeControl = 20
		PR_relinquishControl = 21
		PR_defineSemaphore = 22
		PR_deleteSemaphore = 23
		PR_reportSemaphoreStatus = 24
		PR_reportPoolSemaphoreStatus = 25
		PR_reportSemaphoreEntryStatus = 26
		PR_initiateDownloadSequence = 27
		PR_downloadSegment = 28
		PR_terminateDownloadSequence = 29
		PR_initiateUploadSequence = 30
		PR_uploadSegment = 31
		PR_terminateUploadSequence = 32
		PR_requestDomainDownload = 33
		PR_requestDomainUpload = 34
		PR_loadDomainContent = 35
		PR_storeDomainContent = 36
		PR_deleteDomain = 37
		PR_getDomainAttributes = 38
		PR_createProgramInvocation = 39
		PR_deleteProgramInvocation = 40
		PR_start = 41
		PR_stop = 42
		PR_resume = 43
		PR_reset = 44
		PR_kill = 45
		PR_getProgramInvocationAttributes = 46
		PR_obtainFile = 47
		PR_defineEventCondition = 48
		PR_deleteEventCondition = 49
		PR_getEventConditionAttributes = 50
		PR_reportEventConditionStatus = 51
		PR_alterEventConditionMonitoring = 52
		PR_triggerEvent = 53
		PR_defineEventAction = 54
		PR_deleteEventAction = 55
		PR_getEventActionAttributes = 56
		PR_reportEventActionStatus = 57
		PR_defineEventEnrollment = 58
		PR_deleteEventEnrollment = 59
		PR_alterEventEnrollment = 60
		PR_reportEventEnrollmentStatus = 61
		PR_getEventEnrollmentAttributes = 62
		PR_acknowledgeEventNotification = 63
		PR_getAlarmSummary = 64
		PR_getAlarmEnrollmentSummary = 65
		PR_readJournal = 66
		PR_writeJournal = 67
		PR_initializeJournal = 68
		PR_reportJournalStatus = 69
		PR_createJournal = 70
		PR_deleteJournal = 71
		PR_getCapabilityList = 72
		PR_fileOpen = 73
		PR_fileRead = 74
		PR_fileClose = 75
		PR_fileRename = 76
		PR_fileDelete = 77
		PR_fileDirectory = 78
		PR_additionalService = 79
		PR_getDataExchangeAttributes = 80
		PR_exchangeData = 81
		PR_defineAccessControlList = 82
		PR_getAccessControlListAttributes = 83
		PR_reportAccessControlledObjects = 84
		PR_deleteAccessControlList = 85
		PR_changeAccessControl = 86

	@property
	def present(self) -> PRESENT: ...
	@property
	def status(self) -> Status_Request | None: ...
	@status.setter
	def status(self, value: Status_Request | bool | None) -> None: ...
	getNameList: GetNameList_Request | None
	@property
	def identify(self) -> Identify_Request | None: ...
	@identify.setter
	def identify(self, value: Identify_Request | None | None) -> None: ...
	rename: Rename_Request | None
	read: Read_Request | None
	write: Write_Request | None
	getVariableAccessAttributes: GetVariableAccessAttributes_Request | None
	defineNamedVariable: DefineNamedVariable_Request | None
	defineScatteredAccess: DefineScatteredAccess_Request | None
	getScatteredAccessAttributes: GetScatteredAccessAttributes_Request | None
	deleteVariableAccess: DeleteVariableAccess_Request | None
	defineNamedVariableList: DefineNamedVariableList_Request | None
	getNamedVariableListAttributes: GetNamedVariableListAttributes_Request | None
	deleteNamedVariableList: DeleteNamedVariableList_Request | None
	defineNamedType: DefineNamedType_Request | None
	getNamedTypeAttributes: GetNamedTypeAttributes_Request | None
	deleteNamedType: DeleteNamedType_Request | None
	input: Input_Request | None
	output: Output_Request | None
	takeControl: TakeControl_Request | None
	relinquishControl: RelinquishControl_Request | None
	defineSemaphore: DefineSemaphore_Request | None
	deleteSemaphore: DeleteSemaphore_Request | None
	reportSemaphoreStatus: ReportSemaphoreStatus_Request | None
	reportPoolSemaphoreStatus: ReportPoolSemaphoreStatus_Request | None
	reportSemaphoreEntryStatus: ReportSemaphoreEntryStatus_Request | None
	initiateDownloadSequence: InitiateDownloadSequence_Request | None
	downloadSegment: DownloadSegment_Request | None
	terminateDownloadSequence: TerminateDownloadSequence_Request | None
	initiateUploadSequence: InitiateUploadSequence_Request | None
	uploadSegment: UploadSegment_Request | None
	terminateUploadSequence: TerminateUploadSequence_Request | None
	requestDomainDownload: RequestDomainDownload_Request | None
	requestDomainUpload: RequestDomainUpload_Request | None
	loadDomainContent: LoadDomainContent_Request | None
	storeDomainContent: StoreDomainContent_Request | None
	deleteDomain: DeleteDomain_Request | None
	getDomainAttributes: GetDomainAttributes_Request | None
	createProgramInvocation: CreateProgramInvocation_Request | None
	deleteProgramInvocation: DeleteProgramInvocation_Request | None
	start: Start_Request | None
	stop: Stop_Request | None
	resume: Resume_Request | None
	reset: Reset_Request | None
	kill: Kill_Request | None
	getProgramInvocationAttributes: GetProgramInvocationAttributes_Request | None
	obtainFile: ObtainFile_Request | None
	defineEventCondition: DefineEventCondition_Request | None
	deleteEventCondition: DeleteEventCondition_Request | None
	getEventConditionAttributes: GetEventConditionAttributes_Request | None
	reportEventConditionStatus: ReportEventConditionStatus_Request | None
	alterEventConditionMonitoring: AlterEventConditionMonitoring_Request | None
	triggerEvent: TriggerEvent_Request | None
	defineEventAction: DefineEventAction_Request | None
	deleteEventAction: DeleteEventAction_Request | None
	getEventActionAttributes: GetEventActionAttributes_Request | None
	reportEventActionStatus: ReportEventActionStatus_Request | None
	defineEventEnrollment: DefineEventEnrollment_Request | None
	deleteEventEnrollment: DeleteEventEnrollment_Request | None
	alterEventEnrollment: AlterEventEnrollment_Request | None
	reportEventEnrollmentStatus: ReportEventEnrollmentStatus_Request | None
	getEventEnrollmentAttributes: GetEventEnrollmentAttributes_Request | None
	acknowledgeEventNotification: AcknowledgeEventNotification_Request | None
	getAlarmSummary: GetAlarmSummary_Request | None
	getAlarmEnrollmentSummary: GetAlarmEnrollmentSummary_Request | None
	readJournal: ReadJournal_Request | None
	writeJournal: WriteJournal_Request | None
	initializeJournal: InitializeJournal_Request | None
	reportJournalStatus: ReportJournalStatus_Request | None
	createJournal: CreateJournal_Request | None
	deleteJournal: DeleteJournal_Request | None
	getCapabilityList: GetCapabilityList_Request | None
	fileOpen: FileOpen_Request | None
	fileRead: FileRead_Request | None
	fileClose: FileClose_Request | None
	fileRename: FileRename_Request | None
	fileDelete: FileDelete_Request | None
	fileDirectory: FileDirectory_Request | None
	additionalService: AdditionalService_Request | None
	getDataExchangeAttributes: GetDataExchangeAttributes_Request | None
	exchangeData: ExchangeData_Request | None
	defineAccessControlList: DefineAccessControlList_Request | None
	getAccessControlListAttributes: GetAccessControlListAttributes_Request | None
	reportAccessControlledObjects: ReportAccessControlledObjects_Request | None
	deleteAccessControlList: DeleteAccessControlList_Request | None
	changeAccessControl: ChangeAccessControl_Request | None
	def __init__(
		self, /, *,
		status: Status_Request = ...,
		getNameList: GetNameList_Request = ...,
		identify: Identify_Request = ...,
		rename: Rename_Request = ...,
		read: Read_Request = ...,
		write: Write_Request = ...,
		getVariableAccessAttributes: GetVariableAccessAttributes_Request = ...,
		defineNamedVariable: DefineNamedVariable_Request = ...,
		defineScatteredAccess: DefineScatteredAccess_Request = ...,
		getScatteredAccessAttributes: GetScatteredAccessAttributes_Request = ...,
		deleteVariableAccess: DeleteVariableAccess_Request = ...,
		defineNamedVariableList: DefineNamedVariableList_Request = ...,
		getNamedVariableListAttributes: GetNamedVariableListAttributes_Request = ...,
		deleteNamedVariableList: DeleteNamedVariableList_Request = ...,
		defineNamedType: DefineNamedType_Request = ...,
		getNamedTypeAttributes: GetNamedTypeAttributes_Request = ...,
		deleteNamedType: DeleteNamedType_Request = ...,
		input: Input_Request = ...,
		output: Output_Request = ...,
		takeControl: TakeControl_Request = ...,
		relinquishControl: RelinquishControl_Request = ...,
		defineSemaphore: DefineSemaphore_Request = ...,
		deleteSemaphore: DeleteSemaphore_Request = ...,
		reportSemaphoreStatus: ReportSemaphoreStatus_Request = ...,
		reportPoolSemaphoreStatus: ReportPoolSemaphoreStatus_Request = ...,
		reportSemaphoreEntryStatus: ReportSemaphoreEntryStatus_Request = ...,
		initiateDownloadSequence: InitiateDownloadSequence_Request = ...,
		downloadSegment: DownloadSegment_Request = ...,
		terminateDownloadSequence: TerminateDownloadSequence_Request = ...,
		initiateUploadSequence: InitiateUploadSequence_Request = ...,
		uploadSegment: UploadSegment_Request = ...,
		terminateUploadSequence: TerminateUploadSequence_Request = ...,
		requestDomainDownload: RequestDomainDownload_Request = ...,
		requestDomainUpload: RequestDomainUpload_Request = ...,
		loadDomainContent: LoadDomainContent_Request = ...,
		storeDomainContent: StoreDomainContent_Request = ...,
		deleteDomain: DeleteDomain_Request = ...,
		getDomainAttributes: GetDomainAttributes_Request = ...,
		createProgramInvocation: CreateProgramInvocation_Request = ...,
		deleteProgramInvocation: DeleteProgramInvocation_Request = ...,
		start: Start_Request = ...,
		stop: Stop_Request = ...,
		resume: Resume_Request = ...,
		reset: Reset_Request = ...,
		kill: Kill_Request = ...,
		getProgramInvocationAttributes: GetProgramInvocationAttributes_Request = ...,
		obtainFile: ObtainFile_Request = ...,
		defineEventCondition: DefineEventCondition_Request = ...,
		deleteEventCondition: DeleteEventCondition_Request = ...,
		getEventConditionAttributes: GetEventConditionAttributes_Request = ...,
		reportEventConditionStatus: ReportEventConditionStatus_Request = ...,
		alterEventConditionMonitoring: AlterEventConditionMonitoring_Request = ...,
		triggerEvent: TriggerEvent_Request = ...,
		defineEventAction: DefineEventAction_Request = ...,
		deleteEventAction: DeleteEventAction_Request = ...,
		getEventActionAttributes: GetEventActionAttributes_Request = ...,
		reportEventActionStatus: ReportEventActionStatus_Request = ...,
		defineEventEnrollment: DefineEventEnrollment_Request = ...,
		deleteEventEnrollment: DeleteEventEnrollment_Request = ...,
		alterEventEnrollment: AlterEventEnrollment_Request = ...,
		reportEventEnrollmentStatus: ReportEventEnrollmentStatus_Request = ...,
		getEventEnrollmentAttributes: GetEventEnrollmentAttributes_Request = ...,
		acknowledgeEventNotification: AcknowledgeEventNotification_Request = ...,
		getAlarmSummary: GetAlarmSummary_Request = ...,
		getAlarmEnrollmentSummary: GetAlarmEnrollmentSummary_Request = ...,
		readJournal: ReadJournal_Request = ...,
		writeJournal: WriteJournal_Request = ...,
		initializeJournal: InitializeJournal_Request = ...,
		reportJournalStatus: ReportJournalStatus_Request = ...,
		createJournal: CreateJournal_Request = ...,
		deleteJournal: DeleteJournal_Request = ...,
		getCapabilityList: GetCapabilityList_Request = ...,
		fileOpen: FileOpen_Request = ...,
		fileRead: FileRead_Request = ...,
		fileClose: FileClose_Request = ...,
		fileRename: FileRename_Request = ...,
		fileDelete: FileDelete_Request = ...,
		fileDirectory: FileDirectory_Request = ...,
		additionalService: AdditionalService_Request = ...,
		getDataExchangeAttributes: GetDataExchangeAttributes_Request = ...,
		exchangeData: ExchangeData_Request = ...,
		defineAccessControlList: DefineAccessControlList_Request = ...,
		getAccessControlListAttributes: GetAccessControlListAttributes_Request = ...,
		reportAccessControlledObjects: ReportAccessControlledObjects_Request = ...,
		deleteAccessControlList: DeleteAccessControlList_Request = ...,
		changeAccessControl: ChangeAccessControl_Request = ...,
	) -> None: ...

class AdditionalService_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_vMDStop = 1
		PR_vMDReset = 2
		PR_select = 3
		PR_alterPI = 4
		PR_initiateUCLoad = 5
		PR_uCLoad = 6
		PR_uCUpload = 7
		PR_startUC = 8
		PR_stopUC = 9
		PR_createUC = 10
		PR_addToUC = 11
		PR_removeFromUC = 12
		PR_getUCAttributes = 13
		PR_loadUCFromFile = 14
		PR_storeUCToFile = 15
		PR_deleteUC = 16
		PR_defineECL = 17
		PR_deleteECL = 18
		PR_addECLReference = 19
		PR_removeECLReference = 20
		PR_getECLAttributes = 21
		PR_reportECLStatus = 22
		PR_alterECLMonitoring = 23

	@property
	def present(self) -> PRESENT: ...
	@property
	def vMDStop(self) -> VMDStop_Request | None: ...
	@vMDStop.setter
	def vMDStop(self, value: VMDStop_Request | None | None) -> None: ...
	@property
	def vMDReset(self) -> VMDReset_Request | None: ...
	@vMDReset.setter
	def vMDReset(self, value: VMDReset_Request | bool | None) -> None: ...
	select: Select_Request | None
	alterPI: AlterProgramInvocationAttributes_Request | None
	initiateUCLoad: InitiateUnitControlLoad_Request | None
	uCLoad: UnitControlLoadSegment_Request | None
	uCUpload: UnitControlUpload_Request | None
	startUC: StartUnitControl_Request | None
	stopUC: StopUnitControl_Request | None
	createUC: CreateUnitControl_Request | None
	addToUC: AddToUnitControl_Request | None
	removeFromUC: RemoveFromUnitControl_Request | None
	getUCAttributes: GetUnitControlAttributes_Request | None
	loadUCFromFile: LoadUnitControlFromFile_Request | None
	storeUCToFile: StoreUnitControlToFile_Request | None
	deleteUC: DeleteUnitControl_Request | None
	defineECL: DefineEventConditionList_Request | None
	deleteECL: DeleteEventConditionList_Request | None
	addECLReference: AddEventConditionListReference_Request | None
	removeECLReference: RemoveEventConditionListReference_Request | None
	getECLAttributes: GetEventConditionListAttributes_Request | None
	reportECLStatus: ReportEventConditionListStatus_Request | None
	alterECLMonitoring: AlterEventConditionListMonitoring_Request | None
	def __init__(
		self, /, *,
		vMDStop: VMDStop_Request = ...,
		vMDReset: VMDReset_Request = ...,
		select: Select_Request = ...,
		alterPI: AlterProgramInvocationAttributes_Request = ...,
		initiateUCLoad: InitiateUnitControlLoad_Request = ...,
		uCLoad: UnitControlLoadSegment_Request = ...,
		uCUpload: UnitControlUpload_Request = ...,
		startUC: StartUnitControl_Request = ...,
		stopUC: StopUnitControl_Request = ...,
		createUC: CreateUnitControl_Request = ...,
		addToUC: AddToUnitControl_Request = ...,
		removeFromUC: RemoveFromUnitControl_Request = ...,
		getUCAttributes: GetUnitControlAttributes_Request = ...,
		loadUCFromFile: LoadUnitControlFromFile_Request = ...,
		storeUCToFile: StoreUnitControlToFile_Request = ...,
		deleteUC: DeleteUnitControl_Request = ...,
		defineECL: DefineEventConditionList_Request = ...,
		deleteECL: DeleteEventConditionList_Request = ...,
		addECLReference: AddEventConditionListReference_Request = ...,
		removeECLReference: RemoveEventConditionListReference_Request = ...,
		getECLAttributes: GetEventConditionListAttributes_Request = ...,
		reportECLStatus: ReportEventConditionListStatus_Request = ...,
		alterECLMonitoring: AlterEventConditionListMonitoring_Request = ...,
	) -> None: ...

class Request_Detail(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_otherRequests = 1
		PR_createProgramInvocation = 2
		PR_start = 3
		PR_resume = 4
		PR_defineEventCondition = 5
		PR_alterEventConditionMonitoring = 6
		PR_defineEventEnrollment = 7
		PR_alterEventEnrollment = 8

	@property
	def present(self) -> PRESENT: ...
	otherRequests: None | None
	@property
	def createProgramInvocation(self) -> CS_CreateProgramInvocation_Request | None: ...
	@createProgramInvocation.setter
	def createProgramInvocation(self, value: CS_CreateProgramInvocation_Request | int | None) -> None: ...
	start: CS_Start_Request | None
	resume: CS_Resume_Request | None
	defineEventCondition: CS_DefineEventCondition_Request | None
	alterEventConditionMonitoring: CS_AlterEventConditionMonitoring_Request | None
	defineEventEnrollment: CS_DefineEventEnrollment_Request | None
	alterEventEnrollment: CS_AlterEventEnrollment_Request | None
	def __init__(
		self, /, *,
		otherRequests: None = ...,
		createProgramInvocation: CS_CreateProgramInvocation_Request = ...,
		start: CS_Start_Request = ...,
		resume: CS_Resume_Request = ...,
		defineEventCondition: CS_DefineEventCondition_Request = ...,
		alterEventConditionMonitoring: CS_AlterEventConditionMonitoring_Request = ...,
		defineEventEnrollment: CS_DefineEventEnrollment_Request = ...,
		alterEventEnrollment: CS_AlterEventEnrollment_Request = ...,
	) -> None: ...

class Unconfirmed_PDU(_Asn1Type): # SEQUENCE
	service: UnconfirmedService
	service_ext: Unconfirmed_Detail | None
	def __init__(
		self, /, *,
		service: UnconfirmedService = ...,
		service_ext: Unconfirmed_Detail = ...,
	) -> None: ...

class UnconfirmedService(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_informationReport = 1
		PR_unsolicitedStatus = 2
		PR_eventNotification = 3

	@property
	def present(self) -> PRESENT: ...
	informationReport: InformationReport | None
	unsolicitedStatus: UnsolicitedStatus | None
	eventNotification: EventNotification | None
	def __init__(
		self, /, *,
		informationReport: InformationReport = ...,
		unsolicitedStatus: UnsolicitedStatus = ...,
		eventNotification: EventNotification = ...,
	) -> None: ...

class Unconfirmed_Detail(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_otherRequests = 1
		PR_eventNotification = 2

	@property
	def present(self) -> PRESENT: ...
	otherRequests: None | None
	eventNotification: CS_EventNotification | None
	def __init__(
		self, /, *,
		otherRequests: None = ...,
		eventNotification: CS_EventNotification = ...,
	) -> None: ...

class Confirmed_ResponsePDU(_Asn1Type): # SEQUENCE
	@property
	def invokeID(self) -> Unsigned32: ...
	@invokeID.setter
	def invokeID(self, value: Unsigned32 | int) -> None: ...
	service: ConfirmedServiceResponse
	service_ext: Response_Detail | None
	def __init__(
		self, /, *,
		invokeID: Unsigned32 = ...,
		service: ConfirmedServiceResponse = ...,
		service_ext: Response_Detail = ...,
	) -> None: ...

class ConfirmedServiceResponse(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_status = 1
		PR_getNameList = 2
		PR_identify = 3
		PR_rename = 4
		PR_read = 5
		PR_write = 6
		PR_getVariableAccessAttributes = 7
		PR_defineNamedVariable = 8
		PR_defineScatteredAccess = 9
		PR_getScatteredAccessAttributes = 10
		PR_deleteVariableAccess = 11
		PR_defineNamedVariableList = 12
		PR_getNamedVariableListAttributes = 13
		PR_deleteNamedVariableList = 14
		PR_defineNamedType = 15
		PR_getNamedTypeAttributes = 16
		PR_deleteNamedType = 17
		PR_input = 18
		PR_output = 19
		PR_takeControl = 20
		PR_relinquishControl = 21
		PR_defineSemaphore = 22
		PR_deleteSemaphore = 23
		PR_reportSemaphoreStatus = 24
		PR_reportPoolSemaphoreStatus = 25
		PR_reportSemaphoreEntryStatus = 26
		PR_initiateDownloadSequence = 27
		PR_downloadSegment = 28
		PR_terminateDownloadSequence = 29
		PR_initiateUploadSequence = 30
		PR_uploadSegment = 31
		PR_terminateUploadSequence = 32
		PR_requestDomainDownload = 33
		PR_requestDomainUpload = 34
		PR_loadDomainContent = 35
		PR_storeDomainContent = 36
		PR_deleteDomain = 37
		PR_getDomainAttributes = 38
		PR_createProgramInvocation = 39
		PR_deleteProgramInvocation = 40
		PR_start = 41
		PR_stop = 42
		PR_resume = 43
		PR_reset = 44
		PR_kill = 45
		PR_getProgramInvocationAttributes = 46
		PR_obtainFile = 47
		PR_defineEventCondition = 48
		PR_deleteEventCondition = 49
		PR_getEventConditionAttributes = 50
		PR_reportEventConditionStatus = 51
		PR_alterEventConditionMonitoring = 52
		PR_triggerEvent = 53
		PR_defineEventAction = 54
		PR_deleteEventAction = 55
		PR_getEventActionAttributes = 56
		PR_reportEventActionStatus = 57
		PR_defineEventEnrollment = 58
		PR_deleteEventEnrollment = 59
		PR_alterEventEnrollment = 60
		PR_reportEventEnrollmentStatus = 61
		PR_getEventEnrollmentAttributes = 62
		PR_acknowledgeEventNotification = 63
		PR_getAlarmSummary = 64
		PR_getAlarmEnrollmentSummary = 65
		PR_readJournal = 66
		PR_writeJournal = 67
		PR_initializeJournal = 68
		PR_reportJournalStatus = 69
		PR_createJournal = 70
		PR_deleteJournal = 71
		PR_getCapabilityList = 72
		PR_fileOpen = 73
		PR_fileRead = 74
		PR_fileClose = 75
		PR_fileRename = 76
		PR_fileDelete = 77
		PR_fileDirectory = 78
		PR_additionalService = 79
		PR_getDataExchangeAttributes = 80
		PR_exchangeData = 81
		PR_defineAccessControlList = 82
		PR_getAccessControlListAttributes = 83
		PR_reportAccessControlledObjects = 84
		PR_deleteAccessControlList = 85
		PR_changeAccessControl = 86

	@property
	def present(self) -> PRESENT: ...
	status: Status_Response | None
	getNameList: GetNameList_Response | None
	identify: Identify_Response | None
	@property
	def rename(self) -> Rename_Response | None: ...
	@rename.setter
	def rename(self, value: Rename_Response | None | None) -> None: ...
	read: Read_Response | None
	@property
	def write(self) -> Write_Response | None: ...
	@write.setter
	def write(self, value: Write_Response | list | None) -> None: ...
	getVariableAccessAttributes: GetVariableAccessAttributes_Response | None
	@property
	def defineNamedVariable(self) -> DefineNamedVariable_Response | None: ...
	@defineNamedVariable.setter
	def defineNamedVariable(self, value: DefineNamedVariable_Response | None | None) -> None: ...
	@property
	def defineScatteredAccess(self) -> DefineScatteredAccess_Response | None: ...
	@defineScatteredAccess.setter
	def defineScatteredAccess(self, value: DefineScatteredAccess_Response | None | None) -> None: ...
	getScatteredAccessAttributes: GetScatteredAccessAttributes_Response | None
	deleteVariableAccess: DeleteVariableAccess_Response | None
	@property
	def defineNamedVariableList(self) -> DefineNamedVariableList_Response | None: ...
	@defineNamedVariableList.setter
	def defineNamedVariableList(self, value: DefineNamedVariableList_Response | None | None) -> None: ...
	getNamedVariableListAttributes: GetNamedVariableListAttributes_Response | None
	deleteNamedVariableList: DeleteNamedVariableList_Response | None
	@property
	def defineNamedType(self) -> DefineNamedType_Response | None: ...
	@defineNamedType.setter
	def defineNamedType(self, value: DefineNamedType_Response | None | None) -> None: ...
	getNamedTypeAttributes: GetNamedTypeAttributes_Response | None
	deleteNamedType: DeleteNamedType_Response | None
	input: Input_Response | None
	@property
	def output(self) -> Output_Response | None: ...
	@output.setter
	def output(self, value: Output_Response | None | None) -> None: ...
	takeControl: TakeControl_Response | None
	@property
	def relinquishControl(self) -> RelinquishControl_Response | None: ...
	@relinquishControl.setter
	def relinquishControl(self, value: RelinquishControl_Response | None | None) -> None: ...
	@property
	def defineSemaphore(self) -> DefineSemaphore_Response | None: ...
	@defineSemaphore.setter
	def defineSemaphore(self, value: DefineSemaphore_Response | None | None) -> None: ...
	@property
	def deleteSemaphore(self) -> DeleteSemaphore_Response | None: ...
	@deleteSemaphore.setter
	def deleteSemaphore(self, value: DeleteSemaphore_Response | None | None) -> None: ...
	reportSemaphoreStatus: ReportSemaphoreStatus_Response | None
	reportPoolSemaphoreStatus: ReportPoolSemaphoreStatus_Response | None
	reportSemaphoreEntryStatus: ReportSemaphoreEntryStatus_Response | None
	@property
	def initiateDownloadSequence(self) -> InitiateDownloadSequence_Response | None: ...
	@initiateDownloadSequence.setter
	def initiateDownloadSequence(self, value: InitiateDownloadSequence_Response | None | None) -> None: ...
	downloadSegment: DownloadSegment_Response | None
	@property
	def terminateDownloadSequence(self) -> TerminateDownloadSequence_Response | None: ...
	@terminateDownloadSequence.setter
	def terminateDownloadSequence(self, value: TerminateDownloadSequence_Response | None | None) -> None: ...
	initiateUploadSequence: InitiateUploadSequence_Response | None
	uploadSegment: UploadSegment_Response | None
	@property
	def terminateUploadSequence(self) -> TerminateUploadSequence_Response | None: ...
	@terminateUploadSequence.setter
	def terminateUploadSequence(self, value: TerminateUploadSequence_Response | None | None) -> None: ...
	@property
	def requestDomainDownload(self) -> RequestDomainDownload_Response | None: ...
	@requestDomainDownload.setter
	def requestDomainDownload(self, value: RequestDomainDownload_Response | None | None) -> None: ...
	@property
	def requestDomainUpload(self) -> RequestDomainUpload_Response | None: ...
	@requestDomainUpload.setter
	def requestDomainUpload(self, value: RequestDomainUpload_Response | None | None) -> None: ...
	@property
	def loadDomainContent(self) -> LoadDomainContent_Response | None: ...
	@loadDomainContent.setter
	def loadDomainContent(self, value: LoadDomainContent_Response | None | None) -> None: ...
	@property
	def storeDomainContent(self) -> StoreDomainContent_Response | None: ...
	@storeDomainContent.setter
	def storeDomainContent(self, value: StoreDomainContent_Response | None | None) -> None: ...
	@property
	def deleteDomain(self) -> DeleteDomain_Response | None: ...
	@deleteDomain.setter
	def deleteDomain(self, value: DeleteDomain_Response | None | None) -> None: ...
	getDomainAttributes: GetDomainAttributes_Response | None
	@property
	def createProgramInvocation(self) -> CreateProgramInvocation_Response | None: ...
	@createProgramInvocation.setter
	def createProgramInvocation(self, value: CreateProgramInvocation_Response | None | None) -> None: ...
	@property
	def deleteProgramInvocation(self) -> DeleteProgramInvocation_Response | None: ...
	@deleteProgramInvocation.setter
	def deleteProgramInvocation(self, value: DeleteProgramInvocation_Response | None | None) -> None: ...
	@property
	def start(self) -> Start_Response | None: ...
	@start.setter
	def start(self, value: Start_Response | None | None) -> None: ...
	@property
	def stop(self) -> Stop_Response | None: ...
	@stop.setter
	def stop(self, value: Stop_Response | None | None) -> None: ...
	@property
	def resume(self) -> Resume_Response | None: ...
	@resume.setter
	def resume(self, value: Resume_Response | None | None) -> None: ...
	@property
	def reset(self) -> Reset_Response | None: ...
	@reset.setter
	def reset(self, value: Reset_Response | None | None) -> None: ...
	@property
	def kill(self) -> Kill_Response | None: ...
	@kill.setter
	def kill(self, value: Kill_Response | None | None) -> None: ...
	getProgramInvocationAttributes: GetProgramInvocationAttributes_Response | None
	@property
	def obtainFile(self) -> ObtainFile_Response | None: ...
	@obtainFile.setter
	def obtainFile(self, value: ObtainFile_Response | None | None) -> None: ...
	@property
	def defineEventCondition(self) -> DefineEventCondition_Response | None: ...
	@defineEventCondition.setter
	def defineEventCondition(self, value: DefineEventCondition_Response | None | None) -> None: ...
	deleteEventCondition: DeleteEventCondition_Response | None
	getEventConditionAttributes: GetEventConditionAttributes_Response | None
	reportEventConditionStatus: ReportEventConditionStatus_Response | None
	@property
	def alterEventConditionMonitoring(self) -> AlterEventConditionMonitoring_Response | None: ...
	@alterEventConditionMonitoring.setter
	def alterEventConditionMonitoring(self, value: AlterEventConditionMonitoring_Response | None | None) -> None: ...
	@property
	def triggerEvent(self) -> TriggerEvent_Response | None: ...
	@triggerEvent.setter
	def triggerEvent(self, value: TriggerEvent_Response | None | None) -> None: ...
	@property
	def defineEventAction(self) -> DefineEventAction_Response | None: ...
	@defineEventAction.setter
	def defineEventAction(self, value: DefineEventAction_Response | None | None) -> None: ...
	deleteEventAction: DeleteEventAction_Response | None
	getEventActionAttributes: GetEventActionAttributes_Response | None
	reportEventActionStatus: ReportEventActionStatus_Response | None
	@property
	def defineEventEnrollment(self) -> DefineEventEnrollment_Response | None: ...
	@defineEventEnrollment.setter
	def defineEventEnrollment(self, value: DefineEventEnrollment_Response | None | None) -> None: ...
	deleteEventEnrollment: DeleteEventEnrollment_Response | None
	alterEventEnrollment: AlterEventEnrollment_Response | None
	reportEventEnrollmentStatus: ReportEventEnrollmentStatus_Response | None
	getEventEnrollmentAttributes: GetEventEnrollmentAttributes_Response | None
	@property
	def acknowledgeEventNotification(self) -> AcknowledgeEventNotification_Response | None: ...
	@acknowledgeEventNotification.setter
	def acknowledgeEventNotification(self, value: AcknowledgeEventNotification_Response | None | None) -> None: ...
	getAlarmSummary: GetAlarmSummary_Response | None
	getAlarmEnrollmentSummary: GetAlarmEnrollmentSummary_Response | None
	readJournal: ReadJournal_Response | None
	@property
	def writeJournal(self) -> WriteJournal_Response | None: ...
	@writeJournal.setter
	def writeJournal(self, value: WriteJournal_Response | None | None) -> None: ...
	initializeJournal: InitializeJournal_Response | None
	reportJournalStatus: ReportJournalStatus_Response | None
	@property
	def createJournal(self) -> CreateJournal_Response | None: ...
	@createJournal.setter
	def createJournal(self, value: CreateJournal_Response | None | None) -> None: ...
	@property
	def deleteJournal(self) -> DeleteJournal_Response | None: ...
	@deleteJournal.setter
	def deleteJournal(self, value: DeleteJournal_Response | None | None) -> None: ...
	getCapabilityList: GetCapabilityList_Response | None
	fileOpen: FileOpen_Response | None
	fileRead: FileRead_Response | None
	@property
	def fileClose(self) -> FileClose_Response | None: ...
	@fileClose.setter
	def fileClose(self, value: FileClose_Response | None | None) -> None: ...
	@property
	def fileRename(self) -> FileRename_Response | None: ...
	@fileRename.setter
	def fileRename(self, value: FileRename_Response | None | None) -> None: ...
	@property
	def fileDelete(self) -> FileDelete_Response | None: ...
	@fileDelete.setter
	def fileDelete(self, value: FileDelete_Response | None | None) -> None: ...
	fileDirectory: FileDirectory_Response | None
	additionalService: AdditionalService_Response | None
	getDataExchangeAttributes: GetDataExchangeAttributes_Response | None
	exchangeData: ExchangeData_Response | None
	@property
	def defineAccessControlList(self) -> DefineAccessControlList_Response | None: ...
	@defineAccessControlList.setter
	def defineAccessControlList(self, value: DefineAccessControlList_Response | None | None) -> None: ...
	getAccessControlListAttributes: GetAccessControlListAttributes_Response | None
	reportAccessControlledObjects: ReportAccessControlledObjects_Response | None
	@property
	def deleteAccessControlList(self) -> DeleteAccessControlList_Response | None: ...
	@deleteAccessControlList.setter
	def deleteAccessControlList(self, value: DeleteAccessControlList_Response | None | None) -> None: ...
	changeAccessControl: ChangeAccessControl_Response | None
	def __init__(
		self, /, *,
		status: Status_Response = ...,
		getNameList: GetNameList_Response = ...,
		identify: Identify_Response = ...,
		rename: Rename_Response = ...,
		read: Read_Response = ...,
		write: Write_Response = ...,
		getVariableAccessAttributes: GetVariableAccessAttributes_Response = ...,
		defineNamedVariable: DefineNamedVariable_Response = ...,
		defineScatteredAccess: DefineScatteredAccess_Response = ...,
		getScatteredAccessAttributes: GetScatteredAccessAttributes_Response = ...,
		deleteVariableAccess: DeleteVariableAccess_Response = ...,
		defineNamedVariableList: DefineNamedVariableList_Response = ...,
		getNamedVariableListAttributes: GetNamedVariableListAttributes_Response = ...,
		deleteNamedVariableList: DeleteNamedVariableList_Response = ...,
		defineNamedType: DefineNamedType_Response = ...,
		getNamedTypeAttributes: GetNamedTypeAttributes_Response = ...,
		deleteNamedType: DeleteNamedType_Response = ...,
		input: Input_Response = ...,
		output: Output_Response = ...,
		takeControl: TakeControl_Response = ...,
		relinquishControl: RelinquishControl_Response = ...,
		defineSemaphore: DefineSemaphore_Response = ...,
		deleteSemaphore: DeleteSemaphore_Response = ...,
		reportSemaphoreStatus: ReportSemaphoreStatus_Response = ...,
		reportPoolSemaphoreStatus: ReportPoolSemaphoreStatus_Response = ...,
		reportSemaphoreEntryStatus: ReportSemaphoreEntryStatus_Response = ...,
		initiateDownloadSequence: InitiateDownloadSequence_Response = ...,
		downloadSegment: DownloadSegment_Response = ...,
		terminateDownloadSequence: TerminateDownloadSequence_Response = ...,
		initiateUploadSequence: InitiateUploadSequence_Response = ...,
		uploadSegment: UploadSegment_Response = ...,
		terminateUploadSequence: TerminateUploadSequence_Response = ...,
		requestDomainDownload: RequestDomainDownload_Response = ...,
		requestDomainUpload: RequestDomainUpload_Response = ...,
		loadDomainContent: LoadDomainContent_Response = ...,
		storeDomainContent: StoreDomainContent_Response = ...,
		deleteDomain: DeleteDomain_Response = ...,
		getDomainAttributes: GetDomainAttributes_Response = ...,
		createProgramInvocation: CreateProgramInvocation_Response = ...,
		deleteProgramInvocation: DeleteProgramInvocation_Response = ...,
		start: Start_Response = ...,
		stop: Stop_Response = ...,
		resume: Resume_Response = ...,
		reset: Reset_Response = ...,
		kill: Kill_Response = ...,
		getProgramInvocationAttributes: GetProgramInvocationAttributes_Response = ...,
		obtainFile: ObtainFile_Response = ...,
		defineEventCondition: DefineEventCondition_Response = ...,
		deleteEventCondition: DeleteEventCondition_Response = ...,
		getEventConditionAttributes: GetEventConditionAttributes_Response = ...,
		reportEventConditionStatus: ReportEventConditionStatus_Response = ...,
		alterEventConditionMonitoring: AlterEventConditionMonitoring_Response = ...,
		triggerEvent: TriggerEvent_Response = ...,
		defineEventAction: DefineEventAction_Response = ...,
		deleteEventAction: DeleteEventAction_Response = ...,
		getEventActionAttributes: GetEventActionAttributes_Response = ...,
		reportEventActionStatus: ReportEventActionStatus_Response = ...,
		defineEventEnrollment: DefineEventEnrollment_Response = ...,
		deleteEventEnrollment: DeleteEventEnrollment_Response = ...,
		alterEventEnrollment: AlterEventEnrollment_Response = ...,
		reportEventEnrollmentStatus: ReportEventEnrollmentStatus_Response = ...,
		getEventEnrollmentAttributes: GetEventEnrollmentAttributes_Response = ...,
		acknowledgeEventNotification: AcknowledgeEventNotification_Response = ...,
		getAlarmSummary: GetAlarmSummary_Response = ...,
		getAlarmEnrollmentSummary: GetAlarmEnrollmentSummary_Response = ...,
		readJournal: ReadJournal_Response = ...,
		writeJournal: WriteJournal_Response = ...,
		initializeJournal: InitializeJournal_Response = ...,
		reportJournalStatus: ReportJournalStatus_Response = ...,
		createJournal: CreateJournal_Response = ...,
		deleteJournal: DeleteJournal_Response = ...,
		getCapabilityList: GetCapabilityList_Response = ...,
		fileOpen: FileOpen_Response = ...,
		fileRead: FileRead_Response = ...,
		fileClose: FileClose_Response = ...,
		fileRename: FileRename_Response = ...,
		fileDelete: FileDelete_Response = ...,
		fileDirectory: FileDirectory_Response = ...,
		additionalService: AdditionalService_Response = ...,
		getDataExchangeAttributes: GetDataExchangeAttributes_Response = ...,
		exchangeData: ExchangeData_Response = ...,
		defineAccessControlList: DefineAccessControlList_Response = ...,
		getAccessControlListAttributes: GetAccessControlListAttributes_Response = ...,
		reportAccessControlledObjects: ReportAccessControlledObjects_Response = ...,
		deleteAccessControlList: DeleteAccessControlList_Response = ...,
		changeAccessControl: ChangeAccessControl_Response = ...,
	) -> None: ...

class AdditionalService_Response(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_vMDStop = 1
		PR_vMDReset = 2
		PR_select = 3
		PR_alterPI = 4
		PR_initiateUCLoad = 5
		PR_uCLoad = 6
		PR_uCUpload = 7
		PR_startUC = 8
		PR_stopUC = 9
		PR_createUC = 10
		PR_addToUC = 11
		PR_removeFromUC = 12
		PR_getUCAttributes = 13
		PR_loadUCFromFile = 14
		PR_storeUCToFile = 15
		PR_deleteUC = 16
		PR_defineECL = 17
		PR_deleteECL = 18
		PR_addECLReference = 19
		PR_removeECLReference = 20
		PR_getECLAttributes = 21
		PR_reportECLStatus = 22
		PR_alterECLMonitoring = 23

	@property
	def present(self) -> PRESENT: ...
	@property
	def vMDStop(self) -> VMDStop_Response | None: ...
	@vMDStop.setter
	def vMDStop(self, value: VMDStop_Response | None | None) -> None: ...
	vMDReset: VMDReset_Response | None
	@property
	def select(self) -> Select_Response | None: ...
	@select.setter
	def select(self, value: Select_Response | None | None) -> None: ...
	@property
	def alterPI(self) -> AlterProgramInvocationAttributes_Response | None: ...
	@alterPI.setter
	def alterPI(self, value: AlterProgramInvocationAttributes_Response | None | None) -> None: ...
	@property
	def initiateUCLoad(self) -> InitiateUnitControlLoad_Response | None: ...
	@initiateUCLoad.setter
	def initiateUCLoad(self, value: InitiateUnitControlLoad_Response | None | None) -> None: ...
	uCLoad: UnitControlLoadSegment_Response | None
	uCUpload: UnitControlUpload_Response | None
	@property
	def startUC(self) -> StartUnitControl_Response | None: ...
	@startUC.setter
	def startUC(self, value: StartUnitControl_Response | None | None) -> None: ...
	@property
	def stopUC(self) -> StopUnitControl_Response | None: ...
	@stopUC.setter
	def stopUC(self, value: StopUnitControl_Response | None | None) -> None: ...
	@property
	def createUC(self) -> CreateUnitControl_Response | None: ...
	@createUC.setter
	def createUC(self, value: CreateUnitControl_Response | None | None) -> None: ...
	@property
	def addToUC(self) -> AddToUnitControl_Response | None: ...
	@addToUC.setter
	def addToUC(self, value: AddToUnitControl_Response | None | None) -> None: ...
	@property
	def removeFromUC(self) -> RemoveFromUnitControl_Response | None: ...
	@removeFromUC.setter
	def removeFromUC(self, value: RemoveFromUnitControl_Response | None | None) -> None: ...
	getUCAttributes: GetUnitControlAttributes_Response | None
	@property
	def loadUCFromFile(self) -> LoadUnitControlFromFile_Response | None: ...
	@loadUCFromFile.setter
	def loadUCFromFile(self, value: LoadUnitControlFromFile_Response | None | None) -> None: ...
	@property
	def storeUCToFile(self) -> StoreUnitControlToFile_Response | None: ...
	@storeUCToFile.setter
	def storeUCToFile(self, value: StoreUnitControlToFile_Response | None | None) -> None: ...
	@property
	def deleteUC(self) -> DeleteUnitControl_Response | None: ...
	@deleteUC.setter
	def deleteUC(self, value: DeleteUnitControl_Response | None | None) -> None: ...
	@property
	def defineECL(self) -> DefineEventConditionList_Response | None: ...
	@defineECL.setter
	def defineECL(self, value: DefineEventConditionList_Response | None | None) -> None: ...
	@property
	def deleteECL(self) -> DeleteEventConditionList_Response | None: ...
	@deleteECL.setter
	def deleteECL(self, value: DeleteEventConditionList_Response | None | None) -> None: ...
	@property
	def addECLReference(self) -> AddEventConditionListReference_Response | None: ...
	@addECLReference.setter
	def addECLReference(self, value: AddEventConditionListReference_Response | None | None) -> None: ...
	@property
	def removeECLReference(self) -> RemoveEventConditionListReference_Response | None: ...
	@removeECLReference.setter
	def removeECLReference(self, value: RemoveEventConditionListReference_Response | None | None) -> None: ...
	getECLAttributes: GetEventConditionListAttributes_Response | None
	reportECLStatus: ReportEventConditionListStatus_Response | None
	@property
	def alterECLMonitoring(self) -> AlterEventConditionListMonitoring_Response | None: ...
	@alterECLMonitoring.setter
	def alterECLMonitoring(self, value: AlterEventConditionListMonitoring_Response | None | None) -> None: ...
	def __init__(
		self, /, *,
		vMDStop: VMDStop_Response = ...,
		vMDReset: VMDReset_Response = ...,
		select: Select_Response = ...,
		alterPI: AlterProgramInvocationAttributes_Response = ...,
		initiateUCLoad: InitiateUnitControlLoad_Response = ...,
		uCLoad: UnitControlLoadSegment_Response = ...,
		uCUpload: UnitControlUpload_Response = ...,
		startUC: StartUnitControl_Response = ...,
		stopUC: StopUnitControl_Response = ...,
		createUC: CreateUnitControl_Response = ...,
		addToUC: AddToUnitControl_Response = ...,
		removeFromUC: RemoveFromUnitControl_Response = ...,
		getUCAttributes: GetUnitControlAttributes_Response = ...,
		loadUCFromFile: LoadUnitControlFromFile_Response = ...,
		storeUCToFile: StoreUnitControlToFile_Response = ...,
		deleteUC: DeleteUnitControl_Response = ...,
		defineECL: DefineEventConditionList_Response = ...,
		deleteECL: DeleteEventConditionList_Response = ...,
		addECLReference: AddEventConditionListReference_Response = ...,
		removeECLReference: RemoveEventConditionListReference_Response = ...,
		getECLAttributes: GetEventConditionListAttributes_Response = ...,
		reportECLStatus: ReportEventConditionListStatus_Response = ...,
		alterECLMonitoring: AlterEventConditionListMonitoring_Response = ...,
	) -> None: ...

class Response_Detail(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_otherRequests = 1
		PR_status = 2
		PR_getProgramInvocationAttributes = 3
		PR_getEventConditionAttributes = 4

	@property
	def present(self) -> PRESENT: ...
	otherRequests: None | None
	status: CS_Status_Response | None
	getProgramInvocationAttributes: CS_GetProgramInvocationAttributes_Response | None
	getEventConditionAttributes: CS_GetEventConditionAttributes_Response | None
	def __init__(
		self, /, *,
		otherRequests: None = ...,
		status: CS_Status_Response = ...,
		getProgramInvocationAttributes: CS_GetProgramInvocationAttributes_Response = ...,
		getEventConditionAttributes: CS_GetEventConditionAttributes_Response = ...,
	) -> None: ...

class ServiceError(_Asn1Type): # SEQUENCE

	class errorClass_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_vmd_state = 1
			PR_application_reference = 2
			PR_definition = 3
			PR_resource = 4
			PR_service = 5
			PR_service_preempt = 6
			PR_time_resolution = 7
			PR_access = 8
			PR_initiate = 9
			PR_conclude = 10
			PR_cancel = 11
			PR_file = 12
			PR_others = 13

		@property
		def present(self) -> PRESENT: ...

		class vmd_state_VALUES(EXT_IntEnum):
			V_other = 0
			V_vmd_state_conflict = 1
			V_vmd_operational_problem = 2
			V_domain_transfer_problem = 3
			V_state_machine_id_invalid = 4

		vmd_state: vmd_state_VALUES | None

		class application_reference_VALUES(EXT_IntEnum):
			V_other = 0
			V_application_unreachable = 1
			V_connection_lost = 2
			V_application_reference_invalid = 3
			V_context_unsupported = 4

		application_reference: application_reference_VALUES | None

		class definition_VALUES(EXT_IntEnum):
			V_other = 0
			V_object_undefined = 1
			V_invalid_address = 2
			V_type_unsupported = 3
			V_type_inconsistent = 4
			V_object_exists = 5
			V_object_attribute_inconsistent = 6

		definition: definition_VALUES | None

		class resource_VALUES(EXT_IntEnum):
			V_other = 0
			V_memory_unavailable = 1
			V_processor_resource_unavailable = 2
			V_mass_storage_unavailable = 3
			V_capability_unavailable = 4
			V_capability_unknown = 5

		resource: resource_VALUES | None

		class service_VALUES(EXT_IntEnum):
			V_other = 0
			V_primitives_out_of_sequence = 1
			V_object_state_conflict = 2
			V_continuation_invalid = 4
			V_object_constraint_conflict = 5

		service: service_VALUES | None

		class service_preempt_VALUES(EXT_IntEnum):
			V_other = 0
			V_timeout = 1
			V_deadlock = 2
			V_cancel = 3

		service_preempt: service_preempt_VALUES | None

		class time_resolution_VALUES(EXT_IntEnum):
			V_other = 0
			V_unsupportable_time_resolution = 1

		time_resolution: time_resolution_VALUES | None

		class access_VALUES(EXT_IntEnum):
			V_other = 0
			V_object_access_unsupported = 1
			V_object_non_existent = 2
			V_object_access_denied = 3
			V_object_invalidated = 4

		access: access_VALUES | None

		class initiate_VALUES(EXT_IntEnum):
			V_other = 0
			V_max_services_outstanding_calling_insufficient = 3
			V_max_services_outstanding_called_insufficient = 4
			V_service_CBB_insufficient = 5
			V_parameter_CBB_insufficient = 6
			V_nesting_level_insufficient = 7

		initiate: initiate_VALUES | None

		class conclude_VALUES(EXT_IntEnum):
			V_other = 0
			V_further_communication_required = 1

		conclude: conclude_VALUES | None

		class cancel_VALUES(EXT_IntEnum):
			V_other = 0
			V_invoke_id_unknown = 1
			V_cancel_not_possible = 2

		cancel: cancel_VALUES | None

		class file_VALUES(EXT_IntEnum):
			V_other = 0
			V_filename_ambiguous = 1
			V_file_busy = 2
			V_filename_syntax_error = 3
			V_content_type_invalid = 4
			V_position_invalid = 5
			V_file_access_denied = 6
			V_file_non_existent = 7
			V_duplicate_filename = 8
			V_insufficient_space_in_filestore = 9

		file: file_VALUES | None
		others: int | None
		def __init__(
			self, /, *,
			vmd_state: vmd_state_VALUES = ...,
			application_reference: application_reference_VALUES = ...,
			definition: definition_VALUES = ...,
			resource: resource_VALUES = ...,
			service: service_VALUES = ...,
			service_preempt: service_preempt_VALUES = ...,
			time_resolution: time_resolution_VALUES = ...,
			access: access_VALUES = ...,
			initiate: initiate_VALUES = ...,
			conclude: conclude_VALUES = ...,
			cancel: cancel_VALUES = ...,
			file: file_VALUES = ...,
			others: int = ...,
		) -> None: ...

	errorClass: errorClass_TYPE

	class serviceSpecificInfo_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_obtainFile = 1
			PR_start = 2
			PR_stop = 3
			PR_resume = 4
			PR_reset = 5
			PR_deleteVariableAccess = 6
			PR_deleteNamedVariableList = 7
			PR_deleteNamedType = 8
			PR_defineEventEnrollment_Error = 9
			PR_fileRename = 10
			PR_additionalService = 11
			PR_changeAccessControl = 12

		@property
		def present(self) -> PRESENT: ...
		@property
		def obtainFile(self) -> ObtainFile_Error | None: ...
		@obtainFile.setter
		def obtainFile(self, value: ObtainFile_Error | int | None) -> None: ...
		start: Start_Error | None
		stop: Stop_Error | None
		resume: Resume_Error | None
		reset: Reset_Error | None
		deleteVariableAccess: DeleteVariableAccess_Error | None
		deleteNamedVariableList: DeleteNamedVariableList_Error | None
		deleteNamedType: DeleteNamedType_Error | None
		defineEventEnrollment_Error: DefineEventEnrollment_Error | None
		@property
		def fileRename(self) -> FileRename_Error | None: ...
		@fileRename.setter
		def fileRename(self, value: FileRename_Error | int | None) -> None: ...
		additionalService: AdditionalService_Error | None
		changeAccessControl: ChangeAccessControl_Error | None
		def __init__(
			self, /, *,
			obtainFile: ObtainFile_Error = ...,
			start: Start_Error = ...,
			stop: Stop_Error = ...,
			resume: Resume_Error = ...,
			reset: Reset_Error = ...,
			deleteVariableAccess: DeleteVariableAccess_Error = ...,
			deleteNamedVariableList: DeleteNamedVariableList_Error = ...,
			deleteNamedType: DeleteNamedType_Error = ...,
			defineEventEnrollment_Error: DefineEventEnrollment_Error = ...,
			fileRename: FileRename_Error = ...,
			additionalService: AdditionalService_Error = ...,
			changeAccessControl: ChangeAccessControl_Error = ...,
		) -> None: ...

	serviceSpecificInfo: serviceSpecificInfo_TYPE | None
	additionalCode: int | None
	additionalDescription: str | None
	def __init__(
		self, /, *,
		errorClass: errorClass_TYPE = ...,
		additionalCode: int = ...,
		additionalDescription: str = ...,
		serviceSpecificInfo: serviceSpecificInfo_TYPE = ...,
	) -> None: ...

class AdditionalService_Error(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_defineEcl = 1
		PR_addECLReference = 2
		PR_removeECLReference = 3
		PR_initiateUC = 4
		PR_startUC = 5
		PR_stopUC = 6
		PR_deleteUC = 7
		PR_loadUCFromFile = 8

	@property
	def present(self) -> PRESENT: ...
	defineEcl: DefineEventConditionList_Error | None
	addECLReference: AddEventConditionListReference_Error | None
	removeECLReference: RemoveEventConditionListReference_Error | None
	initiateUC: InitiateUnitControl_Error | None
	startUC: StartUnitControl_Error | None
	stopUC: StopUnitControl_Error | None
	deleteUC: DeleteUnitControl_Error | None
	loadUCFromFile: LoadUnitControlFromFile_Error | None
	def __init__(
		self, /, *,
		defineEcl: DefineEventConditionList_Error = ...,
		addECLReference: AddEventConditionListReference_Error = ...,
		removeECLReference: RemoveEventConditionListReference_Error = ...,
		initiateUC: InitiateUnitControl_Error = ...,
		startUC: StartUnitControl_Error = ...,
		stopUC: StopUnitControl_Error = ...,
		deleteUC: DeleteUnitControl_Error = ...,
		loadUCFromFile: LoadUnitControlFromFile_Error = ...,
	) -> None: ...

class Initiate_RequestPDU(_Asn1Type): # SEQUENCE

	class initRequestDetail_TYPE(_Asn1Type): # SEQUENCE
		@property
		def proposedVersionNumber(self) -> Integer16: ...
		@proposedVersionNumber.setter
		def proposedVersionNumber(self, value: Integer16 | int) -> None: ...
		@property
		def proposedParameterCBB(self) -> ParameterSupportOptions: ...
		@proposedParameterCBB.setter
		def proposedParameterCBB(self, value: ParameterSupportOptions | EXT_bitarray | int | bytes) -> None: ...
		@property
		def servicesSupportedCalling(self) -> ServiceSupportOptions: ...
		@servicesSupportedCalling.setter
		def servicesSupportedCalling(self, value: ServiceSupportOptions | EXT_bitarray | int | bytes) -> None: ...
		@property
		def additionalSupportedCalling(self) -> AdditionalSupportOptions | None: ...
		@additionalSupportedCalling.setter
		def additionalSupportedCalling(self, value: AdditionalSupportOptions | EXT_bitarray | int | bytes | None) -> None: ...
		@property
		def additionalCbbSupportedCalling(self) -> AdditionalCBBOptions | None: ...
		@additionalCbbSupportedCalling.setter
		def additionalCbbSupportedCalling(self, value: AdditionalCBBOptions | EXT_bitarray | int | bytes | None) -> None: ...
		privilegeClassIdentityCalling: str | None
		def __init__(
			self, /, *,
			proposedVersionNumber: Integer16 = ...,
			proposedParameterCBB: ParameterSupportOptions = ...,
			servicesSupportedCalling: ServiceSupportOptions = ...,
			additionalSupportedCalling: AdditionalSupportOptions = ...,
			additionalCbbSupportedCalling: AdditionalCBBOptions = ...,
			privilegeClassIdentityCalling: str = ...,
		) -> None: ...

	initRequestDetail: initRequestDetail_TYPE
	@property
	def localDetailCalling(self) -> Integer32 | None: ...
	@localDetailCalling.setter
	def localDetailCalling(self, value: Integer32 | int | None) -> None: ...
	@property
	def proposedMaxServOutstandingCalling(self) -> Integer16: ...
	@proposedMaxServOutstandingCalling.setter
	def proposedMaxServOutstandingCalling(self, value: Integer16 | int) -> None: ...
	@property
	def proposedMaxServOutstandingCalled(self) -> Integer16: ...
	@proposedMaxServOutstandingCalled.setter
	def proposedMaxServOutstandingCalled(self, value: Integer16 | int) -> None: ...
	@property
	def proposedDataStructureNestingLevel(self) -> Integer8 | None: ...
	@proposedDataStructureNestingLevel.setter
	def proposedDataStructureNestingLevel(self, value: Integer8 | int | None) -> None: ...
	def __init__(
		self, /, *,
		localDetailCalling: Integer32 = ...,
		proposedMaxServOutstandingCalling: Integer16 = ...,
		proposedMaxServOutstandingCalled: Integer16 = ...,
		proposedDataStructureNestingLevel: Integer8 = ...,
		initRequestDetail: initRequestDetail_TYPE = ...,
	) -> None: ...

class Initiate_ResponsePDU(_Asn1Type): # SEQUENCE

	class initResponseDetail_TYPE(_Asn1Type): # SEQUENCE
		@property
		def negotiatedVersionNumber(self) -> Integer16: ...
		@negotiatedVersionNumber.setter
		def negotiatedVersionNumber(self, value: Integer16 | int) -> None: ...
		@property
		def negotiatedParameterCBB(self) -> ParameterSupportOptions: ...
		@negotiatedParameterCBB.setter
		def negotiatedParameterCBB(self, value: ParameterSupportOptions | EXT_bitarray | int | bytes) -> None: ...
		@property
		def servicesSupportedCalled(self) -> ServiceSupportOptions: ...
		@servicesSupportedCalled.setter
		def servicesSupportedCalled(self, value: ServiceSupportOptions | EXT_bitarray | int | bytes) -> None: ...
		@property
		def additionalSupportedCalled(self) -> AdditionalSupportOptions | None: ...
		@additionalSupportedCalled.setter
		def additionalSupportedCalled(self, value: AdditionalSupportOptions | EXT_bitarray | int | bytes | None) -> None: ...
		@property
		def additionalCbbSupportedCalled(self) -> AdditionalCBBOptions | None: ...
		@additionalCbbSupportedCalled.setter
		def additionalCbbSupportedCalled(self, value: AdditionalCBBOptions | EXT_bitarray | int | bytes | None) -> None: ...
		privilegeClassIdentityCalled: str | None
		def __init__(
			self, /, *,
			negotiatedVersionNumber: Integer16 = ...,
			negotiatedParameterCBB: ParameterSupportOptions = ...,
			servicesSupportedCalled: ServiceSupportOptions = ...,
			additionalSupportedCalled: AdditionalSupportOptions = ...,
			additionalCbbSupportedCalled: AdditionalCBBOptions = ...,
			privilegeClassIdentityCalled: str = ...,
		) -> None: ...

	initResponseDetail: initResponseDetail_TYPE
	@property
	def localDetailCalled(self) -> Integer32 | None: ...
	@localDetailCalled.setter
	def localDetailCalled(self, value: Integer32 | int | None) -> None: ...
	@property
	def negotiatedMaxServOutstandingCalling(self) -> Integer16: ...
	@negotiatedMaxServOutstandingCalling.setter
	def negotiatedMaxServOutstandingCalling(self, value: Integer16 | int) -> None: ...
	@property
	def negotiatedMaxServOutstandingCalled(self) -> Integer16: ...
	@negotiatedMaxServOutstandingCalled.setter
	def negotiatedMaxServOutstandingCalled(self, value: Integer16 | int) -> None: ...
	@property
	def negotiatedDataStructureNestingLevel(self) -> Integer8 | None: ...
	@negotiatedDataStructureNestingLevel.setter
	def negotiatedDataStructureNestingLevel(self, value: Integer8 | int | None) -> None: ...
	def __init__(
		self, /, *,
		localDetailCalled: Integer32 = ...,
		negotiatedMaxServOutstandingCalling: Integer16 = ...,
		negotiatedMaxServOutstandingCalled: Integer16 = ...,
		negotiatedDataStructureNestingLevel: Integer8 = ...,
		initResponseDetail: initResponseDetail_TYPE = ...,
	) -> None: ...

class Initiate_ErrorPDU(_Asn1BasicType[ServiceError]):
	pass

class Conclude_RequestPDU(_Asn1BasicType[None]):
	pass

class Conclude_ResponsePDU(_Asn1BasicType[None]):
	pass

class Conclude_ErrorPDU(_Asn1BasicType[ServiceError]):
	pass

class Cancel_RequestPDU(_Asn1BasicType[Unsigned32]):
	pass

class Cancel_ResponsePDU(_Asn1BasicType[Unsigned32]):
	pass

class Cancel_ErrorPDU(_Asn1Type): # SEQUENCE
	@property
	def originalInvokeID(self) -> Unsigned32: ...
	@originalInvokeID.setter
	def originalInvokeID(self, value: Unsigned32 | int) -> None: ...
	serviceError: ServiceError
	def __init__(
		self, /, *,
		originalInvokeID: Unsigned32 = ...,
		serviceError: ServiceError = ...,
	) -> None: ...

class RejectPDU(_Asn1Type): # SEQUENCE

	class rejectReason_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_confirmed_requestPDU = 1
			PR_confirmed_responsePDU = 2
			PR_confirmed_errorPDU = 3
			PR_unconfirmedPDU = 4
			PR_pdu_error = 5
			PR_cancel_requestPDU = 6
			PR_cancel_responsePDU = 7
			PR_cancel_errorPDU = 8
			PR_conclude_requestPDU = 9
			PR_conclude_responsePDU = 10
			PR_conclude_errorPDU = 11

		@property
		def present(self) -> PRESENT: ...

		class confirmed_requestPDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_unrecognized_service = 1
			V_unrecognized_modifier = 2
			V_invalid_invokeID = 3
			V_invalid_argument = 4
			V_invalid_modifier = 5
			V_max_serv_outstanding_exceeded = 6
			V_max_recursion_exceeded = 8
			V_value_out_of_range = 9

		confirmed_requestPDU: confirmed_requestPDU_VALUES | None

		class confirmed_responsePDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_unrecognized_service = 1
			V_invalid_invokeID = 2
			V_invalid_result = 3
			V_max_recursion_exceeded = 5
			V_value_out_of_range = 6

		confirmed_responsePDU: confirmed_responsePDU_VALUES | None

		class confirmed_errorPDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_unrecognized_service = 1
			V_invalid_invokeID = 2
			V_invalid_serviceError = 3
			V_value_out_of_range = 4

		confirmed_errorPDU: confirmed_errorPDU_VALUES | None

		class unconfirmedPDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_unrecognized_service = 1
			V_invalid_argument = 2
			V_max_recursion_exceeded = 3
			V_value_out_of_range = 4

		unconfirmedPDU: unconfirmedPDU_VALUES | None

		class pdu_error_VALUES(EXT_IntEnum):
			V_unknown_pdu_type = 0
			V_invalid_pdu = 1
			V_illegal_acse_mapping = 2

		pdu_error: pdu_error_VALUES | None

		class cancel_requestPDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_invalid_invokeID = 1

		cancel_requestPDU: cancel_requestPDU_VALUES | None

		class cancel_responsePDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_invalid_invokeID = 1

		cancel_responsePDU: cancel_responsePDU_VALUES | None

		class cancel_errorPDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_invalid_invokeID = 1
			V_invalid_serviceError = 2
			V_value_out_of_range = 3

		cancel_errorPDU: cancel_errorPDU_VALUES | None

		class conclude_requestPDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_invalid_argument = 1

		conclude_requestPDU: conclude_requestPDU_VALUES | None

		class conclude_responsePDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_invalid_result = 1

		conclude_responsePDU: conclude_responsePDU_VALUES | None

		class conclude_errorPDU_VALUES(EXT_IntEnum):
			V_other = 0
			V_invalid_serviceError = 1
			V_value_out_of_range = 2

		conclude_errorPDU: conclude_errorPDU_VALUES | None
		def __init__(
			self, /, *,
			confirmed_requestPDU: confirmed_requestPDU_VALUES = ...,
			confirmed_responsePDU: confirmed_responsePDU_VALUES = ...,
			confirmed_errorPDU: confirmed_errorPDU_VALUES = ...,
			unconfirmedPDU: unconfirmedPDU_VALUES = ...,
			pdu_error: pdu_error_VALUES = ...,
			cancel_requestPDU: cancel_requestPDU_VALUES = ...,
			cancel_responsePDU: cancel_responsePDU_VALUES = ...,
			cancel_errorPDU: cancel_errorPDU_VALUES = ...,
			conclude_requestPDU: conclude_requestPDU_VALUES = ...,
			conclude_responsePDU: conclude_responsePDU_VALUES = ...,
			conclude_errorPDU: conclude_errorPDU_VALUES = ...,
		) -> None: ...

	rejectReason: rejectReason_TYPE
	@property
	def originalInvokeID(self) -> Unsigned32 | None: ...
	@originalInvokeID.setter
	def originalInvokeID(self, value: Unsigned32 | int | None) -> None: ...
	def __init__(
		self, /, *,
		originalInvokeID: Unsigned32 = ...,
		rejectReason: rejectReason_TYPE = ...,
	) -> None: ...

class DefineAccessControlList_Request(_Asn1Type): # SEQUENCE

	class accessControlListElements_TYPE(_Asn1Type): # SEQUENCE
		readAccessCondition: AccessCondition | None
		storeAccessCondition: AccessCondition | None
		writeAccessCondition: AccessCondition | None
		loadAccessCondition: AccessCondition | None
		executeAccessCondition: AccessCondition | None
		deleteAccessCondition: AccessCondition | None
		editAccessCondition: AccessCondition | None
		def __init__(
			self, /, *,
			readAccessCondition: AccessCondition = ...,
			storeAccessCondition: AccessCondition = ...,
			writeAccessCondition: AccessCondition = ...,
			loadAccessCondition: AccessCondition = ...,
			executeAccessCondition: AccessCondition = ...,
			deleteAccessCondition: AccessCondition = ...,
			editAccessCondition: AccessCondition = ...,
		) -> None: ...

	accessControlListElements: accessControlListElements_TYPE
	@property
	def accessControlListName(self) -> Identifier: ...
	@accessControlListName.setter
	def accessControlListName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		accessControlListName: Identifier = ...,
		accessControlListElements: accessControlListElements_TYPE = ...,
	) -> None: ...

class DefineAccessControlList_Response(_Asn1BasicType[None]):
	pass

class GetAccessControlListAttributes_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_accessControlListName = 1
		PR_vMD = 2
		PR_namedObject = 3

	@property
	def present(self) -> PRESENT: ...

	class namedObject_TYPE(_Asn1Type): # SEQUENCE
		objectClass: ObjectClass
		objectName: ObjectName
		def __init__(
			self, /, *,
			objectClass: ObjectClass = ...,
			objectName: ObjectName = ...,
		) -> None: ...

	namedObject: namedObject_TYPE
	@property
	def accessControlListName(self) -> Identifier | None: ...
	@accessControlListName.setter
	def accessControlListName(self, value: Identifier | str | None) -> None: ...
	vMD: None | None
	def __init__(
		self, /, *,
		accessControlListName: Identifier = ...,
		vMD: None = ...,
		namedObject: namedObject_TYPE = ...,
	) -> None: ...

class GetAccessControlListAttributes_Response(_Asn1Type): # SEQUENCE

	class accessControlListElements_TYPE(_Asn1Type): # SEQUENCE
		readAccessCondition: AccessCondition | None
		storeAccessCondition: AccessCondition | None
		writeAccessCondition: AccessCondition | None
		loadAccessCondition: AccessCondition | None
		executeAccessCondition: AccessCondition | None
		deleteAccessCondition: AccessCondition | None
		editAccessCondition: AccessCondition | None
		def __init__(
			self, /, *,
			readAccessCondition: AccessCondition = ...,
			storeAccessCondition: AccessCondition = ...,
			writeAccessCondition: AccessCondition = ...,
			loadAccessCondition: AccessCondition = ...,
			executeAccessCondition: AccessCondition = ...,
			deleteAccessCondition: AccessCondition = ...,
			editAccessCondition: AccessCondition = ...,
		) -> None: ...

	accessControlListElements: accessControlListElements_TYPE

	class references_TYPE(_Asn1Type):

		class Member_TYPE(_Asn1Type): # SEQUENCE
			objectClass: ObjectClass
			objectCount: int
			def __init__(
				self, /, *,
				objectClass: ObjectClass = ...,
				objectCount: int = ...,
			) -> None: ...

		def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Member_TYPE: ...
		def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
		def add(self, value: Member_TYPE) -> None: ...
		def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	references: references_TYPE
	@property
	def name(self) -> Identifier: ...
	@name.setter
	def name(self, value: Identifier | str) -> None: ...
	vMDuse: bool
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		name: Identifier = ...,
		accessControlListElements: accessControlListElements_TYPE = ...,
		vMDuse: bool = ...,
		references: references_TYPE = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class ReportAccessControlledObjects_Request(_Asn1Type): # SEQUENCE
	@property
	def accessControlList(self) -> Identifier: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str) -> None: ...
	objectClass: ObjectClass
	continueAfter: ObjectName | None
	def __init__(
		self, /, *,
		accessControlList: Identifier = ...,
		objectClass: ObjectClass = ...,
		continueAfter: ObjectName = ...,
	) -> None: ...

class ReportAccessControlledObjects_Response(_Asn1Type): # SEQUENCE

	class listOfNames_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfNames: listOfNames_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfNames: listOfNames_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class DeleteAccessControlList_Request(_Asn1BasicType[Identifier]):
	pass

class DeleteAccessControlList_Response(_Asn1BasicType[None]):
	pass

class ChangeAccessControl_Request(_Asn1Type): # SEQUENCE

	class scopeOfChange_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_vMDOnly = 1
			PR_listOfObjects = 2

		@property
		def present(self) -> PRESENT: ...

		class listOfObjects_TYPE(_Asn1Type): # SEQUENCE

			class objectScope_TYPE(_Asn1Type): # CHOICE
				class PRESENT(EXT_IntEnum):
					PR_NOTHING = 0
					PR_specific = 1
					PR_aa_specific = 2
					PR_domain = 3
					PR_vmd = 4

				@property
				def present(self) -> PRESENT: ...

				class specific_TYPE(_Asn1Type):
					def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
					def __getitem__(self, index: int) -> ObjectName: ...
					def __setitem__(self, index: int, value: ObjectName) -> None: ...
					def add(self, value: ObjectName) -> None: ...
					def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
					def clear(self) -> None: ...
					def __len__(self) -> int: ...
					def __delitem__(self, index: int) -> None: ...

				specific: specific_TYPE
				aa_specific: None | None
				@property
				def domain(self) -> Identifier | None: ...
				@domain.setter
				def domain(self, value: Identifier | str | None) -> None: ...
				vmd: None | None
				def __init__(
					self, /, *,
					specific: specific_TYPE = ...,
					aa_specific: None = ...,
					domain: Identifier = ...,
					vmd: None = ...,
				) -> None: ...

			objectScope: objectScope_TYPE
			objectClass: ObjectClass
			def __init__(
				self, /, *,
				objectClass: ObjectClass = ...,
				objectScope: objectScope_TYPE = ...,
			) -> None: ...

		listOfObjects: listOfObjects_TYPE
		vMDOnly: None | None
		def __init__(
			self, /, *,
			vMDOnly: None = ...,
			listOfObjects: listOfObjects_TYPE = ...,
		) -> None: ...

	scopeOfChange: scopeOfChange_TYPE
	@property
	def accessControlListName(self) -> Identifier: ...
	@accessControlListName.setter
	def accessControlListName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		scopeOfChange: scopeOfChange_TYPE = ...,
		accessControlListName: Identifier = ...,
	) -> None: ...

class ChangeAccessControl_Response(_Asn1Type): # SEQUENCE
	@property
	def numberMatched(self) -> Unsigned32: ...
	@numberMatched.setter
	def numberMatched(self, value: Unsigned32 | int) -> None: ...
	@property
	def numberChanged(self) -> Unsigned32: ...
	@numberChanged.setter
	def numberChanged(self, value: Unsigned32 | int) -> None: ...
	def __init__(
		self, /, *,
		numberMatched: Unsigned32 = ...,
		numberChanged: Unsigned32 = ...,
	) -> None: ...

class ChangeAccessControl_Error(_Asn1BasicType[Unsigned32]):
	pass

class StatusResponse(_Asn1Type): # SEQUENCE

	class vmdLogicalStatus_VALUES(EXT_IntEnum):
		V_state_changes_allowed = 0
		V_no_state_changes_allowed = 1
		V_limited_services_permitted = 2
		V_support_services_allowed = 3

	vmdLogicalStatus: vmdLogicalStatus_VALUES

	class vmdPhysicalStatus_VALUES(EXT_IntEnum):
		V_operational = 0
		V_partially_operational = 1
		V_inoperable = 2
		V_needs_commissioning = 3

	vmdPhysicalStatus: vmdPhysicalStatus_VALUES

	class localDetail_TYPE(_Asn1BitStrType):
		pass

	@property
	def localDetail(self) -> localDetail_TYPE | None: ...
	@localDetail.setter
	def localDetail(self, value: localDetail_TYPE | EXT_bitarray | bytes | None) -> None: ...
	def __init__(
		self, /, *,
		vmdLogicalStatus: vmdLogicalStatus_VALUES = ...,
		vmdPhysicalStatus: vmdPhysicalStatus_VALUES = ...,
		localDetail: localDetail_TYPE | EXT_bitarray | bytes = ...,
	) -> None: ...

class CS_Status_Response(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_fullResponse = 1
		PR_noExtraResponse = 2

	@property
	def present(self) -> PRESENT: ...

	class fullResponse_TYPE(_Asn1Type): # SEQUENCE

		class selectedProgramInvocation_TYPE(_Asn1Type): # CHOICE
			class PRESENT(EXT_IntEnum):
				PR_NOTHING = 0
				PR_programInvocation = 1
				PR_noneSelected = 2

			@property
			def present(self) -> PRESENT: ...
			@property
			def programInvocation(self) -> Identifier | None: ...
			@programInvocation.setter
			def programInvocation(self, value: Identifier | str | None) -> None: ...
			noneSelected: None | None
			def __init__(
				self, /, *,
				programInvocation: Identifier = ...,
				noneSelected: None = ...,
			) -> None: ...

		selectedProgramInvocation: selectedProgramInvocation_TYPE
		@property
		def operationState(self) -> OperationState: ...
		@operationState.setter
		def operationState(self, value: OperationState | int) -> None: ...
		@property
		def extendedStatus(self) -> ExtendedStatus: ...
		@extendedStatus.setter
		def extendedStatus(self, value: ExtendedStatus | EXT_bitarray | int | bytes) -> None: ...
		@property
		def extendedStatusMask(self) -> ExtendedStatus | None: ...
		@extendedStatusMask.setter
		def extendedStatusMask(self, value: ExtendedStatus | EXT_bitarray | int | bytes | None) -> None: ...
		def __init__(
			self, /, *,
			operationState: OperationState = ...,
			extendedStatus: ExtendedStatus = ...,
			extendedStatusMask: ExtendedStatus = ...,
			selectedProgramInvocation: selectedProgramInvocation_TYPE = ...,
		) -> None: ...

	fullResponse: fullResponse_TYPE
	noExtraResponse: None | None
	def __init__(
		self, /, *,
		fullResponse: fullResponse_TYPE = ...,
		noExtraResponse: None = ...,
	) -> None: ...

class OperationState(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_idle = 0
		V_loaded = 1
		V_ready = 2
		V_executing = 3
		V_motion_paused = 4
		V_manualInterventionRequired = 5

	@property
	def value(self) -> OperationState.VALUES: ...
	@value.setter
	def value(self, value: OperationState.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class ExtendedStatus(_Asn1BitStrType):
	V_safetyInterlocksViolated: bool # bit 0
	V_anyPhysicalResourcePowerOn: bool # bit 1
	V_allPhysicalResourcesCalibrated: bool # bit 2
	V_localControl: bool # bit 3


class Status_Request(_Asn1BasicType[bool]):
	pass

class Status_Response(_Asn1BasicType[StatusResponse]):
	pass

class UnsolicitedStatus(_Asn1BasicType[StatusResponse]):
	pass

class GetNameList_Request(_Asn1Type): # SEQUENCE

	class objectScope_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_vmdSpecific = 1
			PR_domainSpecific = 2
			PR_aaSpecific = 3

		@property
		def present(self) -> PRESENT: ...
		vmdSpecific: None | None
		@property
		def domainSpecific(self) -> Identifier | None: ...
		@domainSpecific.setter
		def domainSpecific(self, value: Identifier | str | None) -> None: ...
		aaSpecific: None | None
		def __init__(
			self, /, *,
			vmdSpecific: None = ...,
			domainSpecific: Identifier = ...,
			aaSpecific: None = ...,
		) -> None: ...

	objectScope: objectScope_TYPE
	objectClass: ObjectClass
	@property
	def continueAfter(self) -> Identifier | None: ...
	@continueAfter.setter
	def continueAfter(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		objectClass: ObjectClass = ...,
		objectScope: objectScope_TYPE = ...,
		continueAfter: Identifier = ...,
	) -> None: ...

class GetNameList_Response(_Asn1Type): # SEQUENCE

	class listOfIdentifier_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfIdentifier: listOfIdentifier_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfIdentifier: listOfIdentifier_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class Identify_Request(_Asn1BasicType[None]):
	pass

class Identify_Response(_Asn1Type): # SEQUENCE

	class listOfAbstractSyntaxes_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[str] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> str: ...
		def __setitem__(self, index: int, value: str) -> None: ...
		def add(self, value: str) -> None: ...
		def extend(self, values: EXT_Iterable[str]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfAbstractSyntaxes: listOfAbstractSyntaxes_TYPE | None
	@property
	def vendorName(self) -> MMSString: ...
	@vendorName.setter
	def vendorName(self, value: MMSString | str) -> None: ...
	@property
	def modelName(self) -> MMSString: ...
	@modelName.setter
	def modelName(self, value: MMSString | str) -> None: ...
	@property
	def revision(self) -> MMSString: ...
	@revision.setter
	def revision(self, value: MMSString | str) -> None: ...
	def __init__(
		self, /, *,
		vendorName: MMSString = ...,
		modelName: MMSString = ...,
		revision: MMSString = ...,
		listOfAbstractSyntaxes: listOfAbstractSyntaxes_TYPE = ...,
	) -> None: ...

class Rename_Request(_Asn1Type): # SEQUENCE
	objectClass: ObjectClass
	currentName: ObjectName
	@property
	def newIdentifier(self) -> Identifier: ...
	@newIdentifier.setter
	def newIdentifier(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		objectClass: ObjectClass = ...,
		currentName: ObjectName = ...,
		newIdentifier: Identifier = ...,
	) -> None: ...

class Rename_Response(_Asn1BasicType[None]):
	pass

class GetCapabilityList_Request(_Asn1Type): # SEQUENCE
	@property
	def continueAfter(self) -> MMSString | None: ...
	@continueAfter.setter
	def continueAfter(self, value: MMSString | str | None) -> None: ...
	def __init__(
		self, /, *,
		continueAfter: MMSString = ...,
	) -> None: ...

class GetCapabilityList_Response(_Asn1Type): # SEQUENCE

	class listOfCapabilities_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> MMSString: ...
		def __setitem__(self, index: int, value: MMSString) -> None: ...
		def add(self, value: MMSString) -> None: ...
		def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfCapabilities: listOfCapabilities_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfCapabilities: listOfCapabilities_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class VMDStop_Request(_Asn1BasicType[None]):
	pass

class VMDStop_Response(_Asn1BasicType[None]):
	pass

class VMDReset_Request(_Asn1BasicType[bool]):
	pass

class VMDReset_Response(_Asn1BasicType[StatusResponse]):
	pass

class InitiateDownloadSequence_Request(_Asn1Type): # SEQUENCE

	class listOfCapabilities_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> MMSString: ...
		def __setitem__(self, index: int, value: MMSString) -> None: ...
		def add(self, value: MMSString) -> None: ...
		def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfCapabilities: listOfCapabilities_TYPE
	@property
	def domainName(self) -> Identifier: ...
	@domainName.setter
	def domainName(self, value: Identifier | str) -> None: ...
	sharable: bool
	def __init__(
		self, /, *,
		domainName: Identifier = ...,
		listOfCapabilities: listOfCapabilities_TYPE = ...,
		sharable: bool = ...,
	) -> None: ...

class InitiateDownloadSequence_Response(_Asn1BasicType[None]):
	pass

class DownloadSegment_Request(_Asn1BasicType[Identifier]):
	pass

class DownloadSegment_Response(_Asn1Type): # SEQUENCE
	loadData: LoadData
	moreFollows: bool | None
	def __init__(
		self, /, *,
		loadData: LoadData = ...,
		moreFollows: bool = ...,
	) -> None: ...

class LoadData(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_non_coded = 1
		PR_coded = 2
		PR_embedded = 3

	@property
	def present(self) -> PRESENT: ...
	non_coded: bytes | None
	coded: EXTERNAL | None
	embedded: EMBEDDED_PDV | None
	def __init__(
		self, /, *,
		non_coded: bytes = ...,
		coded: EXTERNAL = ...,
		embedded: EMBEDDED_PDV = ...,
	) -> None: ...

class TerminateDownloadSequence_Request(_Asn1Type): # SEQUENCE
	@property
	def domainName(self) -> Identifier: ...
	@domainName.setter
	def domainName(self, value: Identifier | str) -> None: ...
	discard: ServiceError | None
	def __init__(
		self, /, *,
		domainName: Identifier = ...,
		discard: ServiceError = ...,
	) -> None: ...

class TerminateDownloadSequence_Response(_Asn1BasicType[None]):
	pass

class InitiateUploadSequence_Request(_Asn1BasicType[Identifier]):
	pass

class InitiateUploadSequence_Response(_Asn1Type): # SEQUENCE

	class listOfCapabilities_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> MMSString: ...
		def __setitem__(self, index: int, value: MMSString) -> None: ...
		def add(self, value: MMSString) -> None: ...
		def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfCapabilities: listOfCapabilities_TYPE
	@property
	def ulsmID(self) -> Integer32: ...
	@ulsmID.setter
	def ulsmID(self, value: Integer32 | int) -> None: ...
	def __init__(
		self, /, *,
		ulsmID: Integer32 = ...,
		listOfCapabilities: listOfCapabilities_TYPE = ...,
	) -> None: ...

class UploadSegment_Request(_Asn1BasicType[Integer32]):
	pass

class UploadSegment_Response(_Asn1Type): # SEQUENCE
	loadData: LoadData
	moreFollows: bool | None
	def __init__(
		self, /, *,
		loadData: LoadData = ...,
		moreFollows: bool = ...,
	) -> None: ...

class TerminateUploadSequence_Request(_Asn1BasicType[Integer32]):
	pass

class TerminateUploadSequence_Response(_Asn1BasicType[None]):
	pass

class RequestDomainDownload_Request(_Asn1Type): # SEQUENCE

	class listOfCapabilities_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> MMSString: ...
		def __setitem__(self, index: int, value: MMSString) -> None: ...
		def add(self, value: MMSString) -> None: ...
		def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfCapabilities: listOfCapabilities_TYPE | None
	@property
	def domainName(self) -> Identifier: ...
	@domainName.setter
	def domainName(self, value: Identifier | str) -> None: ...
	sharable: bool
	@property
	def fileName(self) -> FileName: ...
	@fileName.setter
	def fileName(self, value: FileName | list) -> None: ...
	def __init__(
		self, /, *,
		domainName: Identifier = ...,
		listOfCapabilities: listOfCapabilities_TYPE = ...,
		sharable: bool = ...,
		fileName: FileName = ...,
	) -> None: ...

class RequestDomainDownload_Response(_Asn1BasicType[None]):
	pass

class RequestDomainUpload_Request(_Asn1Type): # SEQUENCE
	@property
	def domainName(self) -> Identifier: ...
	@domainName.setter
	def domainName(self, value: Identifier | str) -> None: ...
	@property
	def fileName(self) -> FileName: ...
	@fileName.setter
	def fileName(self, value: FileName | list) -> None: ...
	def __init__(
		self, /, *,
		domainName: Identifier = ...,
		fileName: FileName = ...,
	) -> None: ...

class RequestDomainUpload_Response(_Asn1BasicType[None]):
	pass

class LoadDomainContent_Request(_Asn1Type): # SEQUENCE

	class listOfCapabilities_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> MMSString: ...
		def __setitem__(self, index: int, value: MMSString) -> None: ...
		def add(self, value: MMSString) -> None: ...
		def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfCapabilities: listOfCapabilities_TYPE | None
	@property
	def domainName(self) -> Identifier: ...
	@domainName.setter
	def domainName(self, value: Identifier | str) -> None: ...
	sharable: bool
	@property
	def fileName(self) -> FileName: ...
	@fileName.setter
	def fileName(self, value: FileName | list) -> None: ...
	thirdParty: ApplicationReference | None
	def __init__(
		self, /, *,
		domainName: Identifier = ...,
		listOfCapabilities: listOfCapabilities_TYPE = ...,
		sharable: bool = ...,
		fileName: FileName = ...,
		thirdParty: ApplicationReference = ...,
	) -> None: ...

class LoadDomainContent_Response(_Asn1BasicType[None]):
	pass

class StoreDomainContent_Request(_Asn1Type): # SEQUENCE
	@property
	def domainName(self) -> Identifier: ...
	@domainName.setter
	def domainName(self, value: Identifier | str) -> None: ...
	@property
	def fileName(self) -> FileName: ...
	@fileName.setter
	def fileName(self, value: FileName | list) -> None: ...
	thirdParty: ApplicationReference | None
	def __init__(
		self, /, *,
		domainName: Identifier = ...,
		fileName: FileName = ...,
		thirdParty: ApplicationReference = ...,
	) -> None: ...

class StoreDomainContent_Response(_Asn1BasicType[None]):
	pass

class DeleteDomain_Request(_Asn1BasicType[Identifier]):
	pass

class DeleteDomain_Response(_Asn1BasicType[None]):
	pass

class GetDomainAttributes_Request(_Asn1BasicType[Identifier]):
	pass

class GetDomainAttributes_Response(_Asn1Type): # SEQUENCE

	class listOfCapabilities_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> MMSString: ...
		def __setitem__(self, index: int, value: MMSString) -> None: ...
		def add(self, value: MMSString) -> None: ...
		def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfCapabilities: listOfCapabilities_TYPE

	class listOfProgramInvocations_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfProgramInvocations: listOfProgramInvocations_TYPE
	@property
	def state(self) -> DomainState: ...
	@state.setter
	def state(self, value: DomainState | int) -> None: ...
	mmsDeletable: bool
	sharable: bool
	@property
	def uploadInProgress(self) -> Integer8: ...
	@uploadInProgress.setter
	def uploadInProgress(self, value: Integer8 | int) -> None: ...
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		listOfCapabilities: listOfCapabilities_TYPE = ...,
		state: DomainState = ...,
		mmsDeletable: bool = ...,
		sharable: bool = ...,
		listOfProgramInvocations: listOfProgramInvocations_TYPE = ...,
		uploadInProgress: Integer8 = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class CreateProgramInvocation_Request(_Asn1Type): # SEQUENCE

	class listOfDomainNames_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfDomainNames: listOfDomainNames_TYPE
	@property
	def programInvocationName(self) -> Identifier: ...
	@programInvocationName.setter
	def programInvocationName(self, value: Identifier | str) -> None: ...
	reusable: bool | None
	monitorType: bool | None
	def __init__(
		self, /, *,
		programInvocationName: Identifier = ...,
		listOfDomainNames: listOfDomainNames_TYPE = ...,
		reusable: bool = ...,
		monitorType: bool = ...,
	) -> None: ...

class CreateProgramInvocation_Response(_Asn1BasicType[None]):
	pass

class CS_CreateProgramInvocation_Request(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_normal = 0
		V_controlling = 1
		V_controlled = 2

	@property
	def value(self) -> CS_CreateProgramInvocation_Request.VALUES: ...
	@value.setter
	def value(self, value: CS_CreateProgramInvocation_Request.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class DeleteProgramInvocation_Request(_Asn1BasicType[Identifier]):
	pass

class DeleteProgramInvocation_Response(_Asn1BasicType[None]):
	pass

class Start_Request(_Asn1Type): # SEQUENCE

	class executionArgument_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_simpleString = 1
			PR_encodedString = 2
			PR_embeddedString = 3

		@property
		def present(self) -> PRESENT: ...
		@property
		def simpleString(self) -> MMSString | None: ...
		@simpleString.setter
		def simpleString(self, value: MMSString | str | None) -> None: ...
		encodedString: EXTERNAL | None
		embeddedString: EMBEDDED_PDV | None
		def __init__(
			self, /, *,
			simpleString: MMSString = ...,
			encodedString: EXTERNAL = ...,
			embeddedString: EMBEDDED_PDV = ...,
		) -> None: ...

	executionArgument: executionArgument_TYPE | None
	@property
	def programInvocationName(self) -> Identifier: ...
	@programInvocationName.setter
	def programInvocationName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		programInvocationName: Identifier = ...,
		executionArgument: executionArgument_TYPE = ...,
	) -> None: ...

class Start_Response(_Asn1BasicType[None]):
	pass

class Start_Error(_Asn1BasicType[ProgramInvocationState]):
	pass

class CS_Start_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_normal = 1
		PR_controlling = 2

	@property
	def present(self) -> PRESENT: ...

	class controlling_TYPE(_Asn1Type): # SEQUENCE
		startLocation: str | None
		startCount: StartCount | None
		def __init__(
			self, /, *,
			startLocation: str = ...,
			startCount: StartCount = ...,
		) -> None: ...

	controlling: controlling_TYPE
	normal: None | None
	def __init__(
		self, /, *,
		normal: None = ...,
		controlling: controlling_TYPE = ...,
	) -> None: ...

class StartCount(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_noLimit = 1
		PR_cycleCount = 2
		PR_stepCount = 3

	@property
	def present(self) -> PRESENT: ...
	noLimit: None | None
	cycleCount: int | None
	stepCount: int | None
	def __init__(
		self, /, *,
		noLimit: None = ...,
		cycleCount: int = ...,
		stepCount: int = ...,
	) -> None: ...

class Stop_Request(_Asn1Type): # SEQUENCE
	@property
	def programInvocationName(self) -> Identifier: ...
	@programInvocationName.setter
	def programInvocationName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		programInvocationName: Identifier = ...,
	) -> None: ...

class Stop_Response(_Asn1BasicType[None]):
	pass

class Stop_Error(_Asn1BasicType[ProgramInvocationState]):
	pass

class Resume_Request(_Asn1Type): # SEQUENCE

	class executionArgument_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_simpleString = 1
			PR_encodedString = 2
			PR_enmbeddedString = 3

		@property
		def present(self) -> PRESENT: ...
		@property
		def simpleString(self) -> MMSString | None: ...
		@simpleString.setter
		def simpleString(self, value: MMSString | str | None) -> None: ...
		encodedString: EXTERNAL | None
		enmbeddedString: EMBEDDED_PDV | None
		def __init__(
			self, /, *,
			simpleString: MMSString = ...,
			encodedString: EXTERNAL = ...,
			enmbeddedString: EMBEDDED_PDV = ...,
		) -> None: ...

	executionArgument: executionArgument_TYPE | None
	@property
	def programInvocationName(self) -> Identifier: ...
	@programInvocationName.setter
	def programInvocationName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		programInvocationName: Identifier = ...,
		executionArgument: executionArgument_TYPE = ...,
	) -> None: ...

class Resume_Response(_Asn1BasicType[None]):
	pass

class Resume_Error(_Asn1BasicType[ProgramInvocationState]):
	pass

class CS_Resume_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_normal = 1
		PR_controlling = 2

	@property
	def present(self) -> PRESENT: ...

	class controlling_TYPE(_Asn1Type): # SEQUENCE

		class modeType_TYPE(_Asn1Type): # CHOICE
			class PRESENT(EXT_IntEnum):
				PR_NOTHING = 0
				PR_continueMode = 1
				PR_changeMode = 2

			@property
			def present(self) -> PRESENT: ...
			continueMode: None | None
			changeMode: StartCount | None
			def __init__(
				self, /, *,
				continueMode: None = ...,
				changeMode: StartCount = ...,
			) -> None: ...

		modeType: modeType_TYPE
		def __init__(
			self, /, *,
			modeType: modeType_TYPE = ...,
		) -> None: ...

	controlling: controlling_TYPE
	normal: None | None
	def __init__(
		self, /, *,
		normal: None = ...,
		controlling: controlling_TYPE = ...,
	) -> None: ...

class Reset_Request(_Asn1Type): # SEQUENCE
	@property
	def programInvocationName(self) -> Identifier: ...
	@programInvocationName.setter
	def programInvocationName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		programInvocationName: Identifier = ...,
	) -> None: ...

class Reset_Response(_Asn1BasicType[None]):
	pass

class Reset_Error(_Asn1BasicType[ProgramInvocationState]):
	pass

class Kill_Request(_Asn1Type): # SEQUENCE
	@property
	def programInvocationName(self) -> Identifier: ...
	@programInvocationName.setter
	def programInvocationName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		programInvocationName: Identifier = ...,
	) -> None: ...

class Kill_Response(_Asn1BasicType[None]):
	pass

class GetProgramInvocationAttributes_Request(_Asn1BasicType[Identifier]):
	pass

class GetProgramInvocationAttributes_Response(_Asn1Type): # SEQUENCE

	class listOfDomainNames_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfDomainNames: listOfDomainNames_TYPE

	class executionArgument_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_simpleString = 1
			PR_encodedString = 2
			PR_enmbeddedString = 3

		@property
		def present(self) -> PRESENT: ...
		@property
		def simpleString(self) -> MMSString | None: ...
		@simpleString.setter
		def simpleString(self, value: MMSString | str | None) -> None: ...
		encodedString: EXTERNAL | None
		enmbeddedString: EMBEDDED_PDV | None
		def __init__(
			self, /, *,
			simpleString: MMSString = ...,
			encodedString: EXTERNAL = ...,
			enmbeddedString: EMBEDDED_PDV = ...,
		) -> None: ...

	executionArgument: executionArgument_TYPE
	@property
	def state(self) -> ProgramInvocationState: ...
	@state.setter
	def state(self, value: ProgramInvocationState | int) -> None: ...
	mmsDeletable: bool
	reusable: bool
	monitor: bool
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		state: ProgramInvocationState = ...,
		listOfDomainNames: listOfDomainNames_TYPE = ...,
		mmsDeletable: bool = ...,
		reusable: bool = ...,
		monitor: bool = ...,
		executionArgument: executionArgument_TYPE = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class CS_GetProgramInvocationAttributes_Response(_Asn1Type): # SEQUENCE

	class control_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_controlling = 1
			PR_controlled = 2
			PR_normal = 3

		@property
		def present(self) -> PRESENT: ...

		class controlling_TYPE(_Asn1Type): # SEQUENCE

			class controlledPI_TYPE(_Asn1Type):
				def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
				def __getitem__(self, index: int) -> Identifier: ...
				def __setitem__(self, index: int, value: Identifier) -> None: ...
				def add(self, value: Identifier) -> None: ...
				def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
				def clear(self) -> None: ...
				def __len__(self) -> int: ...
				def __delitem__(self, index: int) -> None: ...

			controlledPI: controlledPI_TYPE

			class runningMode_TYPE(_Asn1Type): # CHOICE
				class PRESENT(EXT_IntEnum):
					PR_NOTHING = 0
					PR_freeRunning = 1
					PR_cycleLimited = 2
					PR_stepLimited = 3

				@property
				def present(self) -> PRESENT: ...
				freeRunning: None | None
				cycleLimited: int | None
				stepLimited: int | None
				def __init__(
					self, /, *,
					freeRunning: None = ...,
					cycleLimited: int = ...,
					stepLimited: int = ...,
				) -> None: ...

			runningMode: runningMode_TYPE
			programLocation: str | None
			def __init__(
				self, /, *,
				controlledPI: controlledPI_TYPE = ...,
				programLocation: str = ...,
				runningMode: runningMode_TYPE = ...,
			) -> None: ...

		controlling: controlling_TYPE

		class controlled_TYPE(_Asn1Type): # CHOICE
			class PRESENT(EXT_IntEnum):
				PR_NOTHING = 0
				PR_controllingPI = 1
				PR_none = 2

			@property
			def present(self) -> PRESENT: ...
			@property
			def controllingPI(self) -> Identifier | None: ...
			@controllingPI.setter
			def controllingPI(self, value: Identifier | str | None) -> None: ...
			none: None | None
			def __init__(
				self, /, *,
				controllingPI: Identifier = ...,
				none: None = ...,
			) -> None: ...

		controlled: controlled_TYPE
		normal: None | None
		def __init__(
			self, /, *,
			controlling: controlling_TYPE = ...,
			controlled: controlled_TYPE = ...,
			normal: None = ...,
		) -> None: ...

	control: control_TYPE
	errorCode: int
	def __init__(
		self, /, *,
		errorCode: int = ...,
		control: control_TYPE = ...,
	) -> None: ...

class Select_Request(_Asn1Type): # SEQUENCE

	class controlled_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	controlled: controlled_TYPE | None
	@property
	def controlling(self) -> Identifier | None: ...
	@controlling.setter
	def controlling(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		controlling: Identifier = ...,
		controlled: controlled_TYPE = ...,
	) -> None: ...

class Select_Response(_Asn1BasicType[None]):
	pass

class AlterProgramInvocationAttributes_Request(_Asn1Type): # SEQUENCE
	@property
	def programInvocation(self) -> Identifier: ...
	@programInvocation.setter
	def programInvocation(self, value: Identifier | str) -> None: ...
	startCount: StartCount | None
	def __init__(
		self, /, *,
		programInvocation: Identifier = ...,
		startCount: StartCount = ...,
	) -> None: ...

class AlterProgramInvocationAttributes_Response(_Asn1BasicType[None]):
	pass

class ControlElement(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_beginDomainDef = 1
		PR_continueDomainDef = 2
		PR_endDomainDef = 3
		PR_piDefinition = 4

	@property
	def present(self) -> PRESENT: ...

	class beginDomainDef_TYPE(_Asn1Type): # SEQUENCE

		class capabilities_TYPE(_Asn1Type):
			def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
			def __getitem__(self, index: int) -> MMSString: ...
			def __setitem__(self, index: int, value: MMSString) -> None: ...
			def add(self, value: MMSString) -> None: ...
			def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
			def clear(self) -> None: ...
			def __len__(self) -> int: ...
			def __delitem__(self, index: int) -> None: ...

		capabilities: capabilities_TYPE
		@property
		def domainName(self) -> Identifier: ...
		@domainName.setter
		def domainName(self, value: Identifier | str) -> None: ...
		sharable: bool
		loadData: LoadData | None
		def __init__(
			self, /, *,
			domainName: Identifier = ...,
			capabilities: capabilities_TYPE = ...,
			sharable: bool = ...,
			loadData: LoadData = ...,
		) -> None: ...

	beginDomainDef: beginDomainDef_TYPE

	class continueDomainDef_TYPE(_Asn1Type): # SEQUENCE
		@property
		def domainName(self) -> Identifier: ...
		@domainName.setter
		def domainName(self, value: Identifier | str) -> None: ...
		loadData: LoadData
		def __init__(
			self, /, *,
			domainName: Identifier = ...,
			loadData: LoadData = ...,
		) -> None: ...

	continueDomainDef: continueDomainDef_TYPE

	class piDefinition_TYPE(_Asn1Type): # SEQUENCE

		class listOfDomains_TYPE(_Asn1Type):
			def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
			def __getitem__(self, index: int) -> Identifier: ...
			def __setitem__(self, index: int, value: Identifier) -> None: ...
			def add(self, value: Identifier) -> None: ...
			def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
			def clear(self) -> None: ...
			def __len__(self) -> int: ...
			def __delitem__(self, index: int) -> None: ...

		listOfDomains: listOfDomains_TYPE
		@property
		def piName(self) -> Identifier: ...
		@piName.setter
		def piName(self, value: Identifier | str) -> None: ...
		reusable: bool | None
		monitorType: bool | None
		@property
		def pIState(self) -> ProgramInvocationState | None: ...
		@pIState.setter
		def pIState(self, value: ProgramInvocationState | int | None) -> None: ...
		def __init__(
			self, /, *,
			piName: Identifier = ...,
			listOfDomains: listOfDomains_TYPE = ...,
			reusable: bool = ...,
			monitorType: bool = ...,
			pIState: ProgramInvocationState = ...,
		) -> None: ...

	piDefinition: piDefinition_TYPE
	@property
	def endDomainDef(self) -> Identifier | None: ...
	@endDomainDef.setter
	def endDomainDef(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		beginDomainDef: beginDomainDef_TYPE = ...,
		continueDomainDef: continueDomainDef_TYPE = ...,
		endDomainDef: Identifier = ...,
		piDefinition: piDefinition_TYPE = ...,
	) -> None: ...

class InitiateUnitControlLoad_Request(_Asn1BasicType[Identifier]):
	pass

class InitiateUnitControlLoad_Response(_Asn1BasicType[None]):
	pass

class InitiateUnitControl_Error(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_domain = 1
		PR_programInvocation = 2

	@property
	def present(self) -> PRESENT: ...
	@property
	def domain(self) -> Identifier | None: ...
	@domain.setter
	def domain(self, value: Identifier | str | None) -> None: ...
	@property
	def programInvocation(self) -> Identifier | None: ...
	@programInvocation.setter
	def programInvocation(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		domain: Identifier = ...,
		programInvocation: Identifier = ...,
	) -> None: ...

class UnitControlLoadSegment_Request(_Asn1BasicType[Identifier]):
	pass

class UnitControlLoadSegment_Response(_Asn1Type): # SEQUENCE

	class controlElements_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ControlElement] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ControlElement: ...
		def __setitem__(self, index: int, value: ControlElement) -> None: ...
		def add(self, value: ControlElement) -> None: ...
		def extend(self, values: EXT_Iterable[ControlElement]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	controlElements: controlElements_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		controlElements: controlElements_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class UnitControlUpload_Request(_Asn1Type): # SEQUENCE

	class continueAfter_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_domain = 1
			PR_ulsmID = 2
			PR_programInvocation = 3

		@property
		def present(self) -> PRESENT: ...
		@property
		def domain(self) -> Identifier | None: ...
		@domain.setter
		def domain(self, value: Identifier | str | None) -> None: ...
		ulsmID: int | None
		@property
		def programInvocation(self) -> Identifier | None: ...
		@programInvocation.setter
		def programInvocation(self, value: Identifier | str | None) -> None: ...
		def __init__(
			self, /, *,
			domain: Identifier = ...,
			ulsmID: int = ...,
			programInvocation: Identifier = ...,
		) -> None: ...

	continueAfter: continueAfter_TYPE | None
	@property
	def unitControlName(self) -> Identifier: ...
	@unitControlName.setter
	def unitControlName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		unitControlName: Identifier = ...,
		continueAfter: continueAfter_TYPE = ...,
	) -> None: ...

class UnitControlUpload_Response(_Asn1Type): # SEQUENCE

	class controlElements_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ControlElement] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ControlElement: ...
		def __setitem__(self, index: int, value: ControlElement) -> None: ...
		def add(self, value: ControlElement) -> None: ...
		def extend(self, values: EXT_Iterable[ControlElement]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	controlElements: controlElements_TYPE

	class nextElement_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_domain = 1
			PR_ulsmID = 2
			PR_programInvocation = 3

		@property
		def present(self) -> PRESENT: ...
		@property
		def domain(self) -> Identifier | None: ...
		@domain.setter
		def domain(self, value: Identifier | str | None) -> None: ...
		ulsmID: int | None
		@property
		def programInvocation(self) -> Identifier | None: ...
		@programInvocation.setter
		def programInvocation(self, value: Identifier | str | None) -> None: ...
		def __init__(
			self, /, *,
			domain: Identifier = ...,
			ulsmID: int = ...,
			programInvocation: Identifier = ...,
		) -> None: ...

	nextElement: nextElement_TYPE | None
	def __init__(
		self, /, *,
		controlElements: controlElements_TYPE = ...,
		nextElement: nextElement_TYPE = ...,
	) -> None: ...

class StartUnitControl_Request(_Asn1Type): # SEQUENCE

	class executionArgument_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_simpleString = 1
			PR_encodedString = 2
			PR_enmbeddedString = 3

		@property
		def present(self) -> PRESENT: ...
		@property
		def simpleString(self) -> MMSString | None: ...
		@simpleString.setter
		def simpleString(self, value: MMSString | str | None) -> None: ...
		encodedString: EXTERNAL | None
		enmbeddedString: EMBEDDED_PDV | None
		def __init__(
			self, /, *,
			simpleString: MMSString = ...,
			encodedString: EXTERNAL = ...,
			enmbeddedString: EMBEDDED_PDV = ...,
		) -> None: ...

	executionArgument: executionArgument_TYPE | None
	@property
	def unitControlName(self) -> Identifier: ...
	@unitControlName.setter
	def unitControlName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		unitControlName: Identifier = ...,
		executionArgument: executionArgument_TYPE = ...,
	) -> None: ...

class StartUnitControl_Response(_Asn1BasicType[None]):
	pass

class StartUnitControl_Error(_Asn1Type): # SEQUENCE
	@property
	def programInvocationName(self) -> Identifier: ...
	@programInvocationName.setter
	def programInvocationName(self, value: Identifier | str) -> None: ...
	@property
	def programInvocationState(self) -> ProgramInvocationState: ...
	@programInvocationState.setter
	def programInvocationState(self, value: ProgramInvocationState | int) -> None: ...
	def __init__(
		self, /, *,
		programInvocationName: Identifier = ...,
		programInvocationState: ProgramInvocationState = ...,
	) -> None: ...

class StopUnitControl_Request(_Asn1BasicType[Identifier]):
	pass

class StopUnitControl_Response(_Asn1BasicType[None]):
	pass

class StopUnitControl_Error(_Asn1Type): # SEQUENCE
	@property
	def programInvocationName(self) -> Identifier: ...
	@programInvocationName.setter
	def programInvocationName(self, value: Identifier | str) -> None: ...
	@property
	def programInvocationState(self) -> ProgramInvocationState: ...
	@programInvocationState.setter
	def programInvocationState(self, value: ProgramInvocationState | int) -> None: ...
	def __init__(
		self, /, *,
		programInvocationName: Identifier = ...,
		programInvocationState: ProgramInvocationState = ...,
	) -> None: ...

class CreateUnitControl_Request(_Asn1Type): # SEQUENCE

	class domains_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	domains: domains_TYPE

	class programInvocations_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	programInvocations: programInvocations_TYPE
	@property
	def unitControl(self) -> Identifier: ...
	@unitControl.setter
	def unitControl(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		unitControl: Identifier = ...,
		domains: domains_TYPE = ...,
		programInvocations: programInvocations_TYPE = ...,
	) -> None: ...

class CreateUnitControl_Response(_Asn1BasicType[None]):
	pass

class AddToUnitControl_Request(_Asn1Type): # SEQUENCE

	class domains_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	domains: domains_TYPE

	class programInvocations_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	programInvocations: programInvocations_TYPE
	@property
	def unitControl(self) -> Identifier: ...
	@unitControl.setter
	def unitControl(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		unitControl: Identifier = ...,
		domains: domains_TYPE = ...,
		programInvocations: programInvocations_TYPE = ...,
	) -> None: ...

class AddToUnitControl_Response(_Asn1BasicType[None]):
	pass

class RemoveFromUnitControl_Request(_Asn1Type): # SEQUENCE

	class domains_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	domains: domains_TYPE

	class programInvocations_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	programInvocations: programInvocations_TYPE
	@property
	def unitControl(self) -> Identifier: ...
	@unitControl.setter
	def unitControl(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		unitControl: Identifier = ...,
		domains: domains_TYPE = ...,
		programInvocations: programInvocations_TYPE = ...,
	) -> None: ...

class RemoveFromUnitControl_Response(_Asn1BasicType[None]):
	pass

class GetUnitControlAttributes_Request(_Asn1BasicType[Identifier]):
	pass

class GetUnitControlAttributes_Response(_Asn1Type): # SEQUENCE

	class domains_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	domains: domains_TYPE

	class programInvocations_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Identifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Identifier: ...
		def __setitem__(self, index: int, value: Identifier) -> None: ...
		def add(self, value: Identifier) -> None: ...
		def extend(self, values: EXT_Iterable[Identifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	programInvocations: programInvocations_TYPE
	def __init__(
		self, /, *,
		domains: domains_TYPE = ...,
		programInvocations: programInvocations_TYPE = ...,
	) -> None: ...

class LoadUnitControlFromFile_Request(_Asn1Type): # SEQUENCE
	@property
	def unitControlName(self) -> Identifier: ...
	@unitControlName.setter
	def unitControlName(self, value: Identifier | str) -> None: ...
	@property
	def fileName(self) -> FileName: ...
	@fileName.setter
	def fileName(self, value: FileName | list) -> None: ...
	thirdParty: ApplicationReference | None
	def __init__(
		self, /, *,
		unitControlName: Identifier = ...,
		fileName: FileName = ...,
		thirdParty: ApplicationReference = ...,
	) -> None: ...

class LoadUnitControlFromFile_Response(_Asn1BasicType[None]):
	pass

class LoadUnitControlFromFile_Error(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_none = 1
		PR_domain = 2
		PR_programInvocation = 3

	@property
	def present(self) -> PRESENT: ...
	none: None | None
	@property
	def domain(self) -> Identifier | None: ...
	@domain.setter
	def domain(self, value: Identifier | str | None) -> None: ...
	@property
	def programInvocation(self) -> Identifier | None: ...
	@programInvocation.setter
	def programInvocation(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		none: None = ...,
		domain: Identifier = ...,
		programInvocation: Identifier = ...,
	) -> None: ...

class StoreUnitControlToFile_Request(_Asn1Type): # SEQUENCE
	@property
	def unitControlName(self) -> Identifier: ...
	@unitControlName.setter
	def unitControlName(self, value: Identifier | str) -> None: ...
	@property
	def fileName(self) -> FileName: ...
	@fileName.setter
	def fileName(self, value: FileName | list) -> None: ...
	thirdParty: ApplicationReference | None
	def __init__(
		self, /, *,
		unitControlName: Identifier = ...,
		fileName: FileName = ...,
		thirdParty: ApplicationReference = ...,
	) -> None: ...

class StoreUnitControlToFile_Response(_Asn1BasicType[None]):
	pass

class DeleteUnitControl_Request(_Asn1BasicType[Identifier]):
	pass

class DeleteUnitControl_Response(_Asn1BasicType[None]):
	pass

class DeleteUnitControl_Error(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_domain = 1
		PR_programInvocation = 2

	@property
	def present(self) -> PRESENT: ...
	@property
	def domain(self) -> Identifier | None: ...
	@domain.setter
	def domain(self, value: Identifier | str | None) -> None: ...
	@property
	def programInvocation(self) -> Identifier | None: ...
	@programInvocation.setter
	def programInvocation(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		domain: Identifier = ...,
		programInvocation: Identifier = ...,
	) -> None: ...

class TypeSpecification(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_typeName = 1
		PR_typeDescription = 2

	@property
	def present(self) -> PRESENT: ...
	typeName: ObjectName | None
	typeDescription: TypeDescription | None
	def __init__(
		self, /, *,
		typeName: ObjectName = ...,
		typeDescription: TypeDescription = ...,
	) -> None: ...

class AlternateAccess(_Asn1Type):

	class Member_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_unnamed = 1
			PR_named = 2

		@property
		def present(self) -> PRESENT: ...

		class named_TYPE(_Asn1Type): # SEQUENCE
			@property
			def componentName(self) -> Identifier: ...
			@componentName.setter
			def componentName(self, value: Identifier | str) -> None: ...
			access: AlternateAccessSelection | None
			def __init__(
				self, /, *,
				componentName: Identifier = ...,
				access: AlternateAccessSelection = ...,
			) -> None: ...

		named: named_TYPE
		unnamed: AlternateAccessSelection | None
		def __init__(
			self, /, *,
			unnamed: AlternateAccessSelection = ...,
			named: named_TYPE = ...,
		) -> None: ...

	def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Member_TYPE: ...
	def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
	def add(self, value: Member_TYPE) -> None: ...
	def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class AlternateAccessSelection(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_selectAlternateAccess = 1
		PR_selectAccess = 2

	@property
	def present(self) -> PRESENT: ...

	class selectAlternateAccess_TYPE(_Asn1Type): # SEQUENCE

		class accessSelection_TYPE(_Asn1Type): # CHOICE
			class PRESENT(EXT_IntEnum):
				PR_NOTHING = 0
				PR_component = 1
				PR_index = 2
				PR_indexRange = 3
				PR_allElements = 4

			@property
			def present(self) -> PRESENT: ...

			class indexRange_TYPE(_Asn1Type): # SEQUENCE
				@property
				def lowIndex(self) -> Unsigned32: ...
				@lowIndex.setter
				def lowIndex(self, value: Unsigned32 | int) -> None: ...
				@property
				def numberOfElements(self) -> Unsigned32: ...
				@numberOfElements.setter
				def numberOfElements(self, value: Unsigned32 | int) -> None: ...
				def __init__(
					self, /, *,
					lowIndex: Unsigned32 = ...,
					numberOfElements: Unsigned32 = ...,
				) -> None: ...

			indexRange: indexRange_TYPE
			@property
			def component(self) -> Identifier | None: ...
			@component.setter
			def component(self, value: Identifier | str | None) -> None: ...
			@property
			def index(self) -> Unsigned32 | None: ...
			@index.setter
			def index(self, value: Unsigned32 | int | None) -> None: ...
			allElements: None | None
			def __init__(
				self, /, *,
				component: Identifier = ...,
				index: Unsigned32 = ...,
				indexRange: indexRange_TYPE = ...,
				allElements: None = ...,
			) -> None: ...

		accessSelection: accessSelection_TYPE
		@property
		def alternateAccess(self) -> AlternateAccess | None: ...
		@alternateAccess.setter
		def alternateAccess(self, value: AlternateAccess | list | None) -> None: ...
		def __init__(
			self, /, *,
			accessSelection: accessSelection_TYPE = ...,
			alternateAccess: AlternateAccess = ...,
		) -> None: ...

	selectAlternateAccess: selectAlternateAccess_TYPE

	class selectAccess_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_component = 1
			PR_index = 2
			PR_indexRange = 3
			PR_allElements = 4

		@property
		def present(self) -> PRESENT: ...

		class indexRange_TYPE(_Asn1Type): # SEQUENCE
			@property
			def lowIndex(self) -> Unsigned32: ...
			@lowIndex.setter
			def lowIndex(self, value: Unsigned32 | int) -> None: ...
			@property
			def numberOfElements(self) -> Unsigned32: ...
			@numberOfElements.setter
			def numberOfElements(self, value: Unsigned32 | int) -> None: ...
			def __init__(
				self, /, *,
				lowIndex: Unsigned32 = ...,
				numberOfElements: Unsigned32 = ...,
			) -> None: ...

		indexRange: indexRange_TYPE
		@property
		def component(self) -> Identifier | None: ...
		@component.setter
		def component(self, value: Identifier | str | None) -> None: ...
		@property
		def index(self) -> Unsigned32 | None: ...
		@index.setter
		def index(self, value: Unsigned32 | int | None) -> None: ...
		allElements: None | None
		def __init__(
			self, /, *,
			component: Identifier = ...,
			index: Unsigned32 = ...,
			indexRange: indexRange_TYPE = ...,
			allElements: None = ...,
		) -> None: ...

	selectAccess: selectAccess_TYPE
	def __init__(
		self, /, *,
		selectAlternateAccess: selectAlternateAccess_TYPE = ...,
		selectAccess: selectAccess_TYPE = ...,
	) -> None: ...

class AccessResult(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_failure = 1
		PR_success = 2

	@property
	def present(self) -> PRESENT: ...
	@property
	def failure(self) -> DataAccessError | None: ...
	@failure.setter
	def failure(self, value: DataAccessError | int | None) -> None: ...
	success: Data | None
	def __init__(
		self, /, *,
		failure: DataAccessError = ...,
		success: Data = ...,
	) -> None: ...

class Data(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_array = 1
		PR_structure = 2
		PR_boolean = 3
		PR_bit_string = 4
		PR_integer = 5
		PR_Unsigned = 6
		PR_floating_point = 7
		PR_octet_string = 8
		PR_visible_string = 9
		PR_generalized_time = 10
		PR_binary_time = 11
		PR_bcd = 12
		PR_booleanArray = 13
		PR_objId = 14
		PR_mMSString = 15
		PR_utc_time = 16

	@property
	def present(self) -> PRESENT: ...

	class array_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Data] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Data: ...
		def __setitem__(self, index: int, value: Data) -> None: ...
		def add(self, value: Data) -> None: ...
		def extend(self, values: EXT_Iterable[Data]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	array: array_TYPE

	class structure_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Data] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Data: ...
		def __setitem__(self, index: int, value: Data) -> None: ...
		def add(self, value: Data) -> None: ...
		def extend(self, values: EXT_Iterable[Data]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	structure: structure_TYPE
	boolean: bool | None

	class bit_string_TYPE(_Asn1BitStrType):
		pass

	@property
	def bit_string(self) -> bit_string_TYPE | None: ...
	@bit_string.setter
	def bit_string(self, value: bit_string_TYPE | EXT_bitarray | bytes | None) -> None: ...
	integer: int | None
	unsigned: int | None
	@property
	def floating_point(self) -> FloatingPoint | None: ...
	@floating_point.setter
	def floating_point(self, value: FloatingPoint | bytes | None) -> None: ...
	octet_string: bytes | None
	visible_string: str | None
	generalized_time: bytes | None
	@property
	def binary_time(self) -> TimeOfDay | None: ...
	@binary_time.setter
	def binary_time(self, value: TimeOfDay | bytes | None) -> None: ...
	bcd: int | None

	class booleanArray_TYPE(_Asn1BitStrType):
		pass

	@property
	def booleanArray(self) -> booleanArray_TYPE | None: ...
	@booleanArray.setter
	def booleanArray(self, value: booleanArray_TYPE | EXT_bitarray | bytes | None) -> None: ...
	objId: str | None
	@property
	def mMSString(self) -> MMSString | None: ...
	@mMSString.setter
	def mMSString(self, value: MMSString | str | None) -> None: ...
	@property
	def utc_time(self) -> UtcTime | None: ...
	@utc_time.setter
	def utc_time(self, value: UtcTime | bytes | None) -> None: ...
	def __init__(
		self, /, *,
		array: array_TYPE = ...,
		structure: structure_TYPE = ...,
		boolean: bool = ...,
		bit_string: bit_string_TYPE | EXT_bitarray | bytes = ...,
		integer: int = ...,
		unsigned: int = ...,
		floating_point: FloatingPoint = ...,
		octet_string: bytes = ...,
		visible_string: str = ...,
		generalized_time: bytes = ...,
		binary_time: TimeOfDay = ...,
		bcd: int = ...,
		booleanArray: booleanArray_TYPE | EXT_bitarray | bytes = ...,
		objId: str = ...,
		mMSString: MMSString = ...,
		utc_time: UtcTime = ...,
	) -> None: ...

class UtcTime(_Asn1BasicType[bytes]):
	pass

class FloatingPoint(_Asn1BasicType[bytes]):
	pass

class DataAccessError(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_object_invalidated = 0
		V_hardware_fault = 1
		V_temporarily_unavailable = 2
		V_object_access_denied = 3
		V_object_undefined = 4
		V_invalid_address = 5
		V_type_unsupported = 6
		V_type_inconsistent = 7
		V_object_attribute_inconsistent = 8
		V_object_access_unsupported = 9
		V_object_non_existent = 10
		V_object_value_invalid = 11

	@property
	def value(self) -> DataAccessError.VALUES: ...
	@value.setter
	def value(self, value: DataAccessError.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class VariableAccessSpecification(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_listOfVariable = 1
		PR_variableListName = 2

	@property
	def present(self) -> PRESENT: ...

	class listOfVariable_TYPE(_Asn1Type):

		class Member_TYPE(_Asn1Type): # SEQUENCE
			variableSpecification: VariableSpecification
			@property
			def alternateAccess(self) -> AlternateAccess | None: ...
			@alternateAccess.setter
			def alternateAccess(self, value: AlternateAccess | list | None) -> None: ...
			def __init__(
				self, /, *,
				variableSpecification: VariableSpecification = ...,
				alternateAccess: AlternateAccess = ...,
			) -> None: ...

		def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Member_TYPE: ...
		def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
		def add(self, value: Member_TYPE) -> None: ...
		def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfVariable: listOfVariable_TYPE
	variableListName: ObjectName | None
	def __init__(
		self, /, *,
		listOfVariable: listOfVariable_TYPE = ...,
		variableListName: ObjectName = ...,
	) -> None: ...

class VariableSpecification(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_name = 1
		PR_address = 2
		PR_variableDescription = 3
		PR_scatteredAccessDescription = 4
		PR_invalidated = 5

	@property
	def present(self) -> PRESENT: ...

	class variableDescription_TYPE(_Asn1Type): # SEQUENCE
		address: Address
		typeSpecification: TypeSpecification
		def __init__(
			self, /, *,
			address: Address = ...,
			typeSpecification: TypeSpecification = ...,
		) -> None: ...

	variableDescription: variableDescription_TYPE
	name: ObjectName | None
	address: Address | None
	@property
	def scatteredAccessDescription(self) -> ScatteredAccessDescription | None: ...
	@scatteredAccessDescription.setter
	def scatteredAccessDescription(self, value: ScatteredAccessDescription | list | None) -> None: ...
	invalidated: None | None
	def __init__(
		self, /, *,
		name: ObjectName = ...,
		address: Address = ...,
		variableDescription: variableDescription_TYPE = ...,
		scatteredAccessDescription: ScatteredAccessDescription = ...,
		invalidated: None = ...,
	) -> None: ...

class Read_Request(_Asn1Type): # SEQUENCE
	specificationWithResult: bool | None
	variableAccessSpecification: VariableAccessSpecification
	def __init__(
		self, /, *,
		specificationWithResult: bool = ...,
		variableAccessSpecification: VariableAccessSpecification = ...,
	) -> None: ...

class Read_Response(_Asn1Type): # SEQUENCE

	class listOfAccessResult_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[AccessResult] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> AccessResult: ...
		def __setitem__(self, index: int, value: AccessResult) -> None: ...
		def add(self, value: AccessResult) -> None: ...
		def extend(self, values: EXT_Iterable[AccessResult]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfAccessResult: listOfAccessResult_TYPE
	variableAccessSpecification: VariableAccessSpecification | None
	def __init__(
		self, /, *,
		variableAccessSpecification: VariableAccessSpecification = ...,
		listOfAccessResult: listOfAccessResult_TYPE = ...,
	) -> None: ...

class Write_Response(_Asn1Type):

	class Member_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_failure = 1
			PR_success = 2

		@property
		def present(self) -> PRESENT: ...
		@property
		def failure(self) -> DataAccessError | None: ...
		@failure.setter
		def failure(self, value: DataAccessError | int | None) -> None: ...
		success: None | None
		def __init__(
			self, /, *,
			failure: DataAccessError = ...,
			success: None = ...,
		) -> None: ...

	def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Member_TYPE: ...
	def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
	def add(self, value: Member_TYPE) -> None: ...
	def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class Write_Request(_Asn1Type): # SEQUENCE

	class listOfData_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Data] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Data: ...
		def __setitem__(self, index: int, value: Data) -> None: ...
		def add(self, value: Data) -> None: ...
		def extend(self, values: EXT_Iterable[Data]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfData: listOfData_TYPE
	variableAccessSpecification: VariableAccessSpecification
	def __init__(
		self, /, *,
		variableAccessSpecification: VariableAccessSpecification = ...,
		listOfData: listOfData_TYPE = ...,
	) -> None: ...

class InformationReport(_Asn1Type): # SEQUENCE

	class listOfAccessResult_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[AccessResult] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> AccessResult: ...
		def __setitem__(self, index: int, value: AccessResult) -> None: ...
		def add(self, value: AccessResult) -> None: ...
		def extend(self, values: EXT_Iterable[AccessResult]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfAccessResult: listOfAccessResult_TYPE
	variableAccessSpecification: VariableAccessSpecification
	def __init__(
		self, /, *,
		variableAccessSpecification: VariableAccessSpecification = ...,
		listOfAccessResult: listOfAccessResult_TYPE = ...,
	) -> None: ...

class GetVariableAccessAttributes_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_name = 1
		PR_address = 2

	@property
	def present(self) -> PRESENT: ...
	name: ObjectName | None
	address: Address | None
	def __init__(
		self, /, *,
		name: ObjectName = ...,
		address: Address = ...,
	) -> None: ...

class GetVariableAccessAttributes_Response(_Asn1Type): # SEQUENCE
	mmsDeletable: bool
	address: Address | None
	typeDescription: TypeDescription
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	meaning: str | None
	def __init__(
		self, /, *,
		mmsDeletable: bool = ...,
		address: Address = ...,
		typeDescription: TypeDescription = ...,
		accessControlList: Identifier = ...,
		meaning: str = ...,
	) -> None: ...

class DefineNamedVariable_Request(_Asn1Type): # SEQUENCE
	variableName: ObjectName
	address: Address
	typeSpecification: TypeSpecification | None
	def __init__(
		self, /, *,
		variableName: ObjectName = ...,
		address: Address = ...,
		typeSpecification: TypeSpecification = ...,
	) -> None: ...

class DefineNamedVariable_Response(_Asn1BasicType[None]):
	pass

class DeleteVariableAccess_Request(_Asn1Type): # SEQUENCE

	class listOfName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfName: listOfName_TYPE | None

	class scopeOfDelete_VALUES(EXT_IntEnum):
		V_specific = 0
		V_aa_specific = 1
		V_domain = 2
		V_vmd = 3

	scopeOfDelete: scopeOfDelete_VALUES | None
	@property
	def domainName(self) -> Identifier | None: ...
	@domainName.setter
	def domainName(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		scopeOfDelete: scopeOfDelete_VALUES = ...,
		listOfName: listOfName_TYPE = ...,
		domainName: Identifier = ...,
	) -> None: ...

class DeleteVariableAccess_Response(_Asn1Type): # SEQUENCE
	@property
	def numberMatched(self) -> Unsigned32: ...
	@numberMatched.setter
	def numberMatched(self, value: Unsigned32 | int) -> None: ...
	@property
	def numberDeleted(self) -> Unsigned32: ...
	@numberDeleted.setter
	def numberDeleted(self, value: Unsigned32 | int) -> None: ...
	def __init__(
		self, /, *,
		numberMatched: Unsigned32 = ...,
		numberDeleted: Unsigned32 = ...,
	) -> None: ...

class DeleteVariableAccess_Error(_Asn1BasicType[Unsigned32]):
	pass

class DefineNamedVariableList_Request(_Asn1Type): # SEQUENCE

	class listOfVariable_TYPE(_Asn1Type):

		class Member_TYPE(_Asn1Type): # SEQUENCE
			variableSpecification: VariableSpecification
			@property
			def alternateAccess(self) -> AlternateAccess | None: ...
			@alternateAccess.setter
			def alternateAccess(self, value: AlternateAccess | list | None) -> None: ...
			def __init__(
				self, /, *,
				variableSpecification: VariableSpecification = ...,
				alternateAccess: AlternateAccess = ...,
			) -> None: ...

		def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Member_TYPE: ...
		def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
		def add(self, value: Member_TYPE) -> None: ...
		def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfVariable: listOfVariable_TYPE
	variableListName: ObjectName
	def __init__(
		self, /, *,
		variableListName: ObjectName = ...,
		listOfVariable: listOfVariable_TYPE = ...,
	) -> None: ...

class DefineNamedVariableList_Response(_Asn1BasicType[None]):
	pass

class GetNamedVariableListAttributes_Request(_Asn1BasicType[ObjectName]):
	pass

class GetNamedVariableListAttributes_Response(_Asn1Type): # SEQUENCE

	class listOfVariable_TYPE(_Asn1Type):

		class Member_TYPE(_Asn1Type): # SEQUENCE
			variableSpecification: VariableSpecification
			@property
			def alternateAccess(self) -> AlternateAccess | None: ...
			@alternateAccess.setter
			def alternateAccess(self, value: AlternateAccess | list | None) -> None: ...
			def __init__(
				self, /, *,
				variableSpecification: VariableSpecification = ...,
				alternateAccess: AlternateAccess = ...,
			) -> None: ...

		def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Member_TYPE: ...
		def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
		def add(self, value: Member_TYPE) -> None: ...
		def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfVariable: listOfVariable_TYPE
	mmsDeletable: bool
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		mmsDeletable: bool = ...,
		listOfVariable: listOfVariable_TYPE = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class DeleteNamedVariableList_Response(_Asn1Type): # SEQUENCE
	@property
	def numberMatched(self) -> Unsigned32: ...
	@numberMatched.setter
	def numberMatched(self, value: Unsigned32 | int) -> None: ...
	@property
	def numberDeleted(self) -> Unsigned32: ...
	@numberDeleted.setter
	def numberDeleted(self, value: Unsigned32 | int) -> None: ...
	def __init__(
		self, /, *,
		numberMatched: Unsigned32 = ...,
		numberDeleted: Unsigned32 = ...,
	) -> None: ...

class DeleteNamedVariableList_Request(_Asn1Type): # SEQUENCE

	class listOfVariableListName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfVariableListName: listOfVariableListName_TYPE | None

	class scopeOfDelete_VALUES(EXT_IntEnum):
		V_specific = 0
		V_aa_specific = 1
		V_domain = 2
		V_vmd = 3

	scopeOfDelete: scopeOfDelete_VALUES | None
	@property
	def domainName(self) -> Identifier | None: ...
	@domainName.setter
	def domainName(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		scopeOfDelete: scopeOfDelete_VALUES = ...,
		listOfVariableListName: listOfVariableListName_TYPE = ...,
		domainName: Identifier = ...,
	) -> None: ...

class DeleteNamedVariableList_Error(_Asn1BasicType[Unsigned32]):
	pass

class DefineNamedType_Request(_Asn1Type): # SEQUENCE
	typeName: ObjectName
	typeSpecification: TypeSpecification
	def __init__(
		self, /, *,
		typeName: ObjectName = ...,
		typeSpecification: TypeSpecification = ...,
	) -> None: ...

class DefineNamedType_Response(_Asn1BasicType[None]):
	pass

class GetNamedTypeAttributes_Request(_Asn1BasicType[ObjectName]):
	pass

class GetNamedTypeAttributes_Response(_Asn1Type): # SEQUENCE
	mmsDeletable: bool
	typeSpecification: TypeSpecification
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	meaning: str | None
	def __init__(
		self, /, *,
		mmsDeletable: bool = ...,
		typeSpecification: TypeSpecification = ...,
		accessControlList: Identifier = ...,
		meaning: str = ...,
	) -> None: ...

class DeleteNamedType_Request(_Asn1Type): # SEQUENCE

	class listOfTypeName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfTypeName: listOfTypeName_TYPE | None

	class scopeOfDelete_VALUES(EXT_IntEnum):
		V_specific = 0
		V_aa_specific = 1
		V_domain = 2
		V_vmd = 3

	scopeOfDelete: scopeOfDelete_VALUES | None
	@property
	def domainName(self) -> Identifier | None: ...
	@domainName.setter
	def domainName(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		scopeOfDelete: scopeOfDelete_VALUES = ...,
		listOfTypeName: listOfTypeName_TYPE = ...,
		domainName: Identifier = ...,
	) -> None: ...

class DeleteNamedType_Response(_Asn1Type): # SEQUENCE
	@property
	def numberMatched(self) -> Unsigned32: ...
	@numberMatched.setter
	def numberMatched(self, value: Unsigned32 | int) -> None: ...
	@property
	def numberDeleted(self) -> Unsigned32: ...
	@numberDeleted.setter
	def numberDeleted(self, value: Unsigned32 | int) -> None: ...
	def __init__(
		self, /, *,
		numberMatched: Unsigned32 = ...,
		numberDeleted: Unsigned32 = ...,
	) -> None: ...

class DeleteNamedType_Error(_Asn1BasicType[Unsigned32]):
	pass

class ExchangeData_Request(_Asn1Type): # SEQUENCE

	class listOfRequestData_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Data] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Data: ...
		def __setitem__(self, index: int, value: Data) -> None: ...
		def add(self, value: Data) -> None: ...
		def extend(self, values: EXT_Iterable[Data]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfRequestData: listOfRequestData_TYPE
	dataExchangeName: ObjectName
	def __init__(
		self, /, *,
		dataExchangeName: ObjectName = ...,
		listOfRequestData: listOfRequestData_TYPE = ...,
	) -> None: ...

class ExchangeData_Response(_Asn1Type): # SEQUENCE

	class listOfResponseData_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Data] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Data: ...
		def __setitem__(self, index: int, value: Data) -> None: ...
		def add(self, value: Data) -> None: ...
		def extend(self, values: EXT_Iterable[Data]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfResponseData: listOfResponseData_TYPE
	def __init__(
		self, /, *,
		listOfResponseData: listOfResponseData_TYPE = ...,
	) -> None: ...

class GetDataExchangeAttributes_Request(_Asn1BasicType[ObjectName]):
	pass

class GetDataExchangeAttributes_Response(_Asn1Type): # SEQUENCE

	class listOfRequestTypeDescriptions_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[TypeDescription] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> TypeDescription: ...
		def __setitem__(self, index: int, value: TypeDescription) -> None: ...
		def add(self, value: TypeDescription) -> None: ...
		def extend(self, values: EXT_Iterable[TypeDescription]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfRequestTypeDescriptions: listOfRequestTypeDescriptions_TYPE

	class listOfResponseTypeDescriptions_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[TypeDescription] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> TypeDescription: ...
		def __setitem__(self, index: int, value: TypeDescription) -> None: ...
		def add(self, value: TypeDescription) -> None: ...
		def extend(self, values: EXT_Iterable[TypeDescription]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfResponseTypeDescriptions: listOfResponseTypeDescriptions_TYPE
	inUse: bool
	@property
	def programInvocation(self) -> Identifier | None: ...
	@programInvocation.setter
	def programInvocation(self, value: Identifier | str | None) -> None: ...
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		inUse: bool = ...,
		listOfRequestTypeDescriptions: listOfRequestTypeDescriptions_TYPE = ...,
		listOfResponseTypeDescriptions: listOfResponseTypeDescriptions_TYPE = ...,
		programInvocation: Identifier = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class TakeControl_Request(_Asn1Type): # SEQUENCE
	semaphoreName: ObjectName
	@property
	def namedToken(self) -> Identifier | None: ...
	@namedToken.setter
	def namedToken(self, value: Identifier | str | None) -> None: ...
	@property
	def priority(self) -> Priority | None: ...
	@priority.setter
	def priority(self, value: Priority | int | None) -> None: ...
	@property
	def acceptableDelay(self) -> Unsigned32 | None: ...
	@acceptableDelay.setter
	def acceptableDelay(self, value: Unsigned32 | int | None) -> None: ...
	@property
	def controlTimeOut(self) -> Unsigned32 | None: ...
	@controlTimeOut.setter
	def controlTimeOut(self, value: Unsigned32 | int | None) -> None: ...
	abortOnTimeOut: bool | None
	relinquishIfConnectionLost: bool | None
	applicationToPreempt: ApplicationReference | None
	def __init__(
		self, /, *,
		semaphoreName: ObjectName = ...,
		namedToken: Identifier = ...,
		priority: Priority = ...,
		acceptableDelay: Unsigned32 = ...,
		controlTimeOut: Unsigned32 = ...,
		abortOnTimeOut: bool = ...,
		relinquishIfConnectionLost: bool = ...,
		applicationToPreempt: ApplicationReference = ...,
	) -> None: ...

class TakeControl_Response(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_noResult = 1
		PR_namedToken = 2

	@property
	def present(self) -> PRESENT: ...
	noResult: None | None
	@property
	def namedToken(self) -> Identifier | None: ...
	@namedToken.setter
	def namedToken(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		noResult: None = ...,
		namedToken: Identifier = ...,
	) -> None: ...

class RelinquishControl_Request(_Asn1Type): # SEQUENCE
	semaphoreName: ObjectName
	@property
	def namedToken(self) -> Identifier | None: ...
	@namedToken.setter
	def namedToken(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		semaphoreName: ObjectName = ...,
		namedToken: Identifier = ...,
	) -> None: ...

class RelinquishControl_Response(_Asn1BasicType[None]):
	pass

class DefineSemaphore_Request(_Asn1Type): # SEQUENCE
	semaphoreName: ObjectName
	@property
	def numberOfTokens(self) -> Unsigned16: ...
	@numberOfTokens.setter
	def numberOfTokens(self, value: Unsigned16 | int) -> None: ...
	def __init__(
		self, /, *,
		semaphoreName: ObjectName = ...,
		numberOfTokens: Unsigned16 = ...,
	) -> None: ...

class DefineSemaphore_Response(_Asn1BasicType[None]):
	pass

class DeleteSemaphore_Request(_Asn1BasicType[ObjectName]):
	pass

class DeleteSemaphore_Response(_Asn1BasicType[None]):
	pass

class ReportSemaphoreStatus_Request(_Asn1BasicType[ObjectName]):
	pass

class ReportSemaphoreStatus_Response(_Asn1Type): # SEQUENCE
	mmsDeletable: bool

	class class__VALUES(EXT_IntEnum):
		V_token = 0
		V_pool = 1

	class_: class__VALUES
	@property
	def numberOfTokens(self) -> Unsigned16: ...
	@numberOfTokens.setter
	def numberOfTokens(self, value: Unsigned16 | int) -> None: ...
	@property
	def numberOfOwnedTokens(self) -> Unsigned16: ...
	@numberOfOwnedTokens.setter
	def numberOfOwnedTokens(self, value: Unsigned16 | int) -> None: ...
	@property
	def numberOfHungTokens(self) -> Unsigned16: ...
	@numberOfHungTokens.setter
	def numberOfHungTokens(self, value: Unsigned16 | int) -> None: ...
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		mmsDeletable: bool = ...,
		class_: class__VALUES = ...,
		numberOfTokens: Unsigned16 = ...,
		numberOfOwnedTokens: Unsigned16 = ...,
		numberOfHungTokens: Unsigned16 = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class ReportPoolSemaphoreStatus_Request(_Asn1Type): # SEQUENCE
	semaphoreName: ObjectName
	@property
	def nameToStartAfter(self) -> Identifier | None: ...
	@nameToStartAfter.setter
	def nameToStartAfter(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		semaphoreName: ObjectName = ...,
		nameToStartAfter: Identifier = ...,
	) -> None: ...

class ReportPoolSemaphoreStatus_Response(_Asn1Type): # SEQUENCE

	class listOfNamedTokens_TYPE(_Asn1Type):

		class Member_TYPE(_Asn1Type): # CHOICE
			class PRESENT(EXT_IntEnum):
				PR_NOTHING = 0
				PR_freeNamedToken = 1
				PR_ownedNamedToken = 2
				PR_hungNamedToken = 3

			@property
			def present(self) -> PRESENT: ...
			@property
			def freeNamedToken(self) -> Identifier | None: ...
			@freeNamedToken.setter
			def freeNamedToken(self, value: Identifier | str | None) -> None: ...
			@property
			def ownedNamedToken(self) -> Identifier | None: ...
			@ownedNamedToken.setter
			def ownedNamedToken(self, value: Identifier | str | None) -> None: ...
			@property
			def hungNamedToken(self) -> Identifier | None: ...
			@hungNamedToken.setter
			def hungNamedToken(self, value: Identifier | str | None) -> None: ...
			def __init__(
				self, /, *,
				freeNamedToken: Identifier = ...,
				ownedNamedToken: Identifier = ...,
				hungNamedToken: Identifier = ...,
			) -> None: ...

		def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Member_TYPE: ...
		def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
		def add(self, value: Member_TYPE) -> None: ...
		def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfNamedTokens: listOfNamedTokens_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfNamedTokens: listOfNamedTokens_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class ReportSemaphoreEntryStatus_Request(_Asn1Type): # SEQUENCE
	semaphoreName: ObjectName

	class state_VALUES(EXT_IntEnum):
		V_queued = 0
		V_owner = 1
		V_hung = 2

	state: state_VALUES
	entryIDToStartAfter: bytes | None
	def __init__(
		self, /, *,
		semaphoreName: ObjectName = ...,
		state: state_VALUES = ...,
		entryIDToStartAfter: bytes = ...,
	) -> None: ...

class ReportSemaphoreEntryStatus_Response(_Asn1Type): # SEQUENCE

	class listOfSemaphoreEntry_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[SemaphoreEntry] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> SemaphoreEntry: ...
		def __setitem__(self, index: int, value: SemaphoreEntry) -> None: ...
		def add(self, value: SemaphoreEntry) -> None: ...
		def extend(self, values: EXT_Iterable[SemaphoreEntry]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfSemaphoreEntry: listOfSemaphoreEntry_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfSemaphoreEntry: listOfSemaphoreEntry_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class SemaphoreEntry(_Asn1Type): # SEQUENCE
	entryID: bytes

	class entryClass_VALUES(EXT_IntEnum):
		V_simple = 0
		V_modifier = 1

	entryClass: entryClass_VALUES
	applicationReference: ApplicationReference
	@property
	def namedToken(self) -> Identifier | None: ...
	@namedToken.setter
	def namedToken(self, value: Identifier | str | None) -> None: ...
	@property
	def priority(self) -> Priority | None: ...
	@priority.setter
	def priority(self, value: Priority | int | None) -> None: ...
	@property
	def remainingTimeOut(self) -> Unsigned32 | None: ...
	@remainingTimeOut.setter
	def remainingTimeOut(self, value: Unsigned32 | int | None) -> None: ...
	abortOnTimeOut: bool | None
	relinquishIfConnectionLost: bool | None
	def __init__(
		self, /, *,
		entryID: bytes = ...,
		entryClass: entryClass_VALUES = ...,
		applicationReference: ApplicationReference = ...,
		namedToken: Identifier = ...,
		priority: Priority = ...,
		remainingTimeOut: Unsigned32 = ...,
		abortOnTimeOut: bool = ...,
		relinquishIfConnectionLost: bool = ...,
	) -> None: ...

class AttachToSemaphore(_Asn1Type): # SEQUENCE
	semaphoreName: ObjectName
	@property
	def namedToken(self) -> Identifier | None: ...
	@namedToken.setter
	def namedToken(self, value: Identifier | str | None) -> None: ...
	@property
	def priority(self) -> Priority | None: ...
	@priority.setter
	def priority(self, value: Priority | int | None) -> None: ...
	@property
	def acceptableDelay(self) -> Unsigned32 | None: ...
	@acceptableDelay.setter
	def acceptableDelay(self, value: Unsigned32 | int | None) -> None: ...
	@property
	def controlTimeOut(self) -> Unsigned32 | None: ...
	@controlTimeOut.setter
	def controlTimeOut(self, value: Unsigned32 | int | None) -> None: ...
	abortOnTimeOut: bool | None
	relinquishIfConnectionLost: bool | None
	def __init__(
		self, /, *,
		semaphoreName: ObjectName = ...,
		namedToken: Identifier = ...,
		priority: Priority = ...,
		acceptableDelay: Unsigned32 = ...,
		controlTimeOut: Unsigned32 = ...,
		abortOnTimeOut: bool = ...,
		relinquishIfConnectionLost: bool = ...,
	) -> None: ...

class Input_Request(_Asn1Type): # SEQUENCE

	class listOfPromptData_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> MMSString: ...
		def __setitem__(self, index: int, value: MMSString) -> None: ...
		def add(self, value: MMSString) -> None: ...
		def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfPromptData: listOfPromptData_TYPE | None
	@property
	def operatorStationName(self) -> Identifier: ...
	@operatorStationName.setter
	def operatorStationName(self, value: Identifier | str) -> None: ...
	echo: bool | None
	@property
	def inputTimeOut(self) -> Unsigned32 | None: ...
	@inputTimeOut.setter
	def inputTimeOut(self, value: Unsigned32 | int | None) -> None: ...
	def __init__(
		self, /, *,
		operatorStationName: Identifier = ...,
		echo: bool = ...,
		listOfPromptData: listOfPromptData_TYPE = ...,
		inputTimeOut: Unsigned32 = ...,
	) -> None: ...

class Input_Response(_Asn1BasicType[MMSString]):
	pass

class Output_Request(_Asn1Type): # SEQUENCE

	class listOfOutputData_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[MMSString] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> MMSString: ...
		def __setitem__(self, index: int, value: MMSString) -> None: ...
		def add(self, value: MMSString) -> None: ...
		def extend(self, values: EXT_Iterable[MMSString]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfOutputData: listOfOutputData_TYPE
	@property
	def operatorStationName(self) -> Identifier: ...
	@operatorStationName.setter
	def operatorStationName(self, value: Identifier | str) -> None: ...
	def __init__(
		self, /, *,
		operatorStationName: Identifier = ...,
		listOfOutputData: listOfOutputData_TYPE = ...,
	) -> None: ...

class Output_Response(_Asn1BasicType[None]):
	pass

class TriggerEvent_Request(_Asn1Type): # SEQUENCE
	eventConditionName: ObjectName
	@property
	def priority(self) -> Priority | None: ...
	@priority.setter
	def priority(self, value: Priority | int | None) -> None: ...
	def __init__(
		self, /, *,
		eventConditionName: ObjectName = ...,
		priority: Priority = ...,
	) -> None: ...

class TriggerEvent_Response(_Asn1BasicType[None]):
	pass

class EventNotification(_Asn1Type): # SEQUENCE

	class actionResult_TYPE(_Asn1Type): # SEQUENCE

		class successOrFailure_TYPE(_Asn1Type): # CHOICE
			class PRESENT(EXT_IntEnum):
				PR_NOTHING = 0
				PR_success = 1
				PR_failure = 2

			@property
			def present(self) -> PRESENT: ...

			class success_TYPE(_Asn1Type): # SEQUENCE
				confirmedServiceResponse: ConfirmedServiceResponse
				cs_Response_Detail: Response_Detail | None
				def __init__(
					self, /, *,
					confirmedServiceResponse: ConfirmedServiceResponse = ...,
					cs_Response_Detail: Response_Detail = ...,
				) -> None: ...

			success: success_TYPE

			class failure_TYPE(_Asn1Type): # SEQUENCE
				@property
				def modifierPosition(self) -> Unsigned32 | None: ...
				@modifierPosition.setter
				def modifierPosition(self, value: Unsigned32 | int | None) -> None: ...
				serviceError: ServiceError
				def __init__(
					self, /, *,
					modifierPosition: Unsigned32 = ...,
					serviceError: ServiceError = ...,
				) -> None: ...

			failure: failure_TYPE
			def __init__(
				self, /, *,
				success: success_TYPE = ...,
				failure: failure_TYPE = ...,
			) -> None: ...

		successOrFailure: successOrFailure_TYPE
		eventActionName: ObjectName
		def __init__(
			self, /, *,
			eventActionName: ObjectName = ...,
			successOrFailure: successOrFailure_TYPE = ...,
		) -> None: ...

	actionResult: actionResult_TYPE | None
	eventEnrollmentName: ObjectName
	eventConditionName: ObjectName
	@property
	def severity(self) -> Severity: ...
	@severity.setter
	def severity(self, value: Severity | int) -> None: ...
	@property
	def currentState(self) -> EC_State | None: ...
	@currentState.setter
	def currentState(self, value: EC_State | int | None) -> None: ...
	transitionTime: EventTime
	notificationLost: bool | None
	@property
	def alarmAcknowledgmentRule(self) -> AlarmAckRule | None: ...
	@alarmAcknowledgmentRule.setter
	def alarmAcknowledgmentRule(self, value: AlarmAckRule | int | None) -> None: ...
	def __init__(
		self, /, *,
		eventEnrollmentName: ObjectName = ...,
		eventConditionName: ObjectName = ...,
		severity: Severity = ...,
		currentState: EC_State = ...,
		transitionTime: EventTime = ...,
		notificationLost: bool = ...,
		alarmAcknowledgmentRule: AlarmAckRule = ...,
		actionResult: actionResult_TYPE = ...,
	) -> None: ...

class CS_EventNotification(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_string = 1
		PR_index = 2
		PR_noEnhancement = 3

	@property
	def present(self) -> PRESENT: ...
	string: str | None
	index: int | None
	noEnhancement: None | None
	def __init__(
		self, /, *,
		string: str = ...,
		index: int = ...,
		noEnhancement: None = ...,
	) -> None: ...

class AcknowledgeEventNotification_Request(_Asn1Type): # SEQUENCE
	eventEnrollmentName: ObjectName
	@property
	def acknowledgedState(self) -> EC_State: ...
	@acknowledgedState.setter
	def acknowledgedState(self, value: EC_State | int) -> None: ...
	timeOfAcknowledgedTransition: EventTime
	def __init__(
		self, /, *,
		eventEnrollmentName: ObjectName = ...,
		acknowledgedState: EC_State = ...,
		timeOfAcknowledgedTransition: EventTime = ...,
	) -> None: ...

class AcknowledgeEventNotification_Response(_Asn1BasicType[None]):
	pass

class GetAlarmSummary_Request(_Asn1Type): # SEQUENCE

	class severityFilter_TYPE(_Asn1Type): # SEQUENCE
		@property
		def mostSevere(self) -> Unsigned8: ...
		@mostSevere.setter
		def mostSevere(self, value: Unsigned8 | int) -> None: ...
		@property
		def leastSevere(self) -> Unsigned8: ...
		@leastSevere.setter
		def leastSevere(self, value: Unsigned8 | int) -> None: ...
		def __init__(
			self, /, *,
			mostSevere: Unsigned8 = ...,
			leastSevere: Unsigned8 = ...,
		) -> None: ...

	severityFilter: severityFilter_TYPE | None
	enrollmentsOnly: bool | None
	activeAlarmsOnly: bool | None

	class acknowledgementFilter_VALUES(EXT_IntEnum):
		V_not_acked = 0
		V_acked = 1
		V_all = 2

	acknowledgementFilter: acknowledgementFilter_VALUES | None
	continueAfter: ObjectName | None
	def __init__(
		self, /, *,
		enrollmentsOnly: bool = ...,
		activeAlarmsOnly: bool = ...,
		acknowledgementFilter: acknowledgementFilter_VALUES = ...,
		severityFilter: severityFilter_TYPE = ...,
		continueAfter: ObjectName = ...,
	) -> None: ...

class GetAlarmSummary_Response(_Asn1Type): # SEQUENCE

	class listOfAlarmSummary_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[AlarmSummary] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> AlarmSummary: ...
		def __setitem__(self, index: int, value: AlarmSummary) -> None: ...
		def add(self, value: AlarmSummary) -> None: ...
		def extend(self, values: EXT_Iterable[AlarmSummary]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfAlarmSummary: listOfAlarmSummary_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfAlarmSummary: listOfAlarmSummary_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class AlarmSummary(_Asn1Type): # SEQUENCE
	eventConditionName: ObjectName
	@property
	def severity(self) -> Unsigned8: ...
	@severity.setter
	def severity(self, value: Unsigned8 | int) -> None: ...
	@property
	def currentState(self) -> EC_State: ...
	@currentState.setter
	def currentState(self, value: EC_State | int) -> None: ...

	class unacknowledgedState_VALUES(EXT_IntEnum):
		V_none = 0
		V_active = 1
		V_idle = 2
		V_both = 3

	unacknowledgedState: unacknowledgedState_VALUES
	displayEnhancement: EN_Additional_Detail | None
	timeOfLastTransitionToActive: EventTime | None
	timeOfLastTransitionToIdle: EventTime | None
	def __init__(
		self, /, *,
		eventConditionName: ObjectName = ...,
		severity: Unsigned8 = ...,
		currentState: EC_State = ...,
		unacknowledgedState: unacknowledgedState_VALUES = ...,
		displayEnhancement: EN_Additional_Detail = ...,
		timeOfLastTransitionToActive: EventTime = ...,
		timeOfLastTransitionToIdle: EventTime = ...,
	) -> None: ...

class EN_Additional_Detail(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_string = 1
		PR_index = 2
		PR_noEnhancement = 3

	@property
	def present(self) -> PRESENT: ...
	string: str | None
	index: int | None
	noEnhancement: None | None
	def __init__(
		self, /, *,
		string: str = ...,
		index: int = ...,
		noEnhancement: None = ...,
	) -> None: ...

class GetAlarmEnrollmentSummary_Request(_Asn1Type): # SEQUENCE

	class severityFilter_TYPE(_Asn1Type): # SEQUENCE
		@property
		def mostSevere(self) -> Unsigned8: ...
		@mostSevere.setter
		def mostSevere(self, value: Unsigned8 | int) -> None: ...
		@property
		def leastSevere(self) -> Unsigned8: ...
		@leastSevere.setter
		def leastSevere(self, value: Unsigned8 | int) -> None: ...
		def __init__(
			self, /, *,
			mostSevere: Unsigned8 = ...,
			leastSevere: Unsigned8 = ...,
		) -> None: ...

	severityFilter: severityFilter_TYPE | None
	enrollmentsOnly: bool | None
	activeAlarmsOnly: bool | None

	class acknowledgementFilter_VALUES(EXT_IntEnum):
		V_not_acked = 0
		V_acked = 1
		V_all = 2

	acknowledgementFilter: acknowledgementFilter_VALUES | None
	continueAfter: ObjectName | None
	def __init__(
		self, /, *,
		enrollmentsOnly: bool = ...,
		activeAlarmsOnly: bool = ...,
		acknowledgementFilter: acknowledgementFilter_VALUES = ...,
		severityFilter: severityFilter_TYPE = ...,
		continueAfter: ObjectName = ...,
	) -> None: ...

class GetAlarmEnrollmentSummary_Response(_Asn1Type): # SEQUENCE

	class listOfAlarmEnrollmentSummary_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[AlarmEnrollmentSummary] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> AlarmEnrollmentSummary: ...
		def __setitem__(self, index: int, value: AlarmEnrollmentSummary) -> None: ...
		def add(self, value: AlarmEnrollmentSummary) -> None: ...
		def extend(self, values: EXT_Iterable[AlarmEnrollmentSummary]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfAlarmEnrollmentSummary: listOfAlarmEnrollmentSummary_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfAlarmEnrollmentSummary: listOfAlarmEnrollmentSummary_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class AlarmEnrollmentSummary(_Asn1Type): # SEQUENCE
	eventEnrollmentName: ObjectName
	clientApplication: ApplicationReference | None
	@property
	def severity(self) -> Unsigned8: ...
	@severity.setter
	def severity(self, value: Unsigned8 | int) -> None: ...
	@property
	def currentState(self) -> EC_State: ...
	@currentState.setter
	def currentState(self, value: EC_State | int) -> None: ...
	displayEnhancement: EN_Additional_Detail | None
	notificationLost: bool | None
	@property
	def alarmAcknowledgmentRule(self) -> AlarmAckRule: ...
	@alarmAcknowledgmentRule.setter
	def alarmAcknowledgmentRule(self, value: AlarmAckRule | int) -> None: ...
	@property
	def enrollmentState(self) -> EE_State | None: ...
	@enrollmentState.setter
	def enrollmentState(self, value: EE_State | int | None) -> None: ...
	timeOfLastTransitionToActive: EventTime | None
	timeActiveAcknowledged: EventTime | None
	timeOfLastTransitionToIdle: EventTime | None
	timeIdleAcknowledged: EventTime | None
	def __init__(
		self, /, *,
		eventEnrollmentName: ObjectName = ...,
		clientApplication: ApplicationReference = ...,
		severity: Unsigned8 = ...,
		currentState: EC_State = ...,
		displayEnhancement: EN_Additional_Detail = ...,
		notificationLost: bool = ...,
		alarmAcknowledgmentRule: AlarmAckRule = ...,
		enrollmentState: EE_State = ...,
		timeOfLastTransitionToActive: EventTime = ...,
		timeActiveAcknowledged: EventTime = ...,
		timeOfLastTransitionToIdle: EventTime = ...,
		timeIdleAcknowledged: EventTime = ...,
	) -> None: ...

class AttachToEventCondition(_Asn1Type): # SEQUENCE
	eventEnrollmentName: ObjectName
	eventConditionName: ObjectName
	@property
	def causingTransitions(self) -> Transitions: ...
	@causingTransitions.setter
	def causingTransitions(self, value: Transitions | EXT_bitarray | int | bytes) -> None: ...
	@property
	def acceptableDelay(self) -> Unsigned32 | None: ...
	@acceptableDelay.setter
	def acceptableDelay(self, value: Unsigned32 | int | None) -> None: ...
	def __init__(
		self, /, *,
		eventEnrollmentName: ObjectName = ...,
		eventConditionName: ObjectName = ...,
		causingTransitions: Transitions = ...,
		acceptableDelay: Unsigned32 = ...,
	) -> None: ...

class DefineEventCondition_Request(_Asn1Type): # SEQUENCE
	eventConditionName: ObjectName
	@property
	def class_(self) -> EC_Class: ...
	@class_.setter
	def class_(self, value: EC_Class | int) -> None: ...
	@property
	def priority(self) -> Priority | None: ...
	@priority.setter
	def priority(self, value: Priority | int | None) -> None: ...
	@property
	def severity(self) -> Unsigned8 | None: ...
	@severity.setter
	def severity(self, value: Unsigned8 | int | None) -> None: ...
	alarmSummaryReports: bool | None
	monitoredVariable: VariableSpecification | None
	@property
	def evaluationInterval(self) -> Unsigned32 | None: ...
	@evaluationInterval.setter
	def evaluationInterval(self, value: Unsigned32 | int | None) -> None: ...
	def __init__(
		self, /, *,
		eventConditionName: ObjectName = ...,
		class_: EC_Class = ...,
		priority: Priority = ...,
		severity: Unsigned8 = ...,
		alarmSummaryReports: bool = ...,
		monitoredVariable: VariableSpecification = ...,
		evaluationInterval: Unsigned32 = ...,
	) -> None: ...

class DefineEventCondition_Response(_Asn1BasicType[None]):
	pass

class CS_DefineEventCondition_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_string = 1
		PR_index = 2
		PR_noEnhancement = 3

	@property
	def present(self) -> PRESENT: ...
	string: str | None
	index: int | None
	noEnhancement: None | None
	def __init__(
		self, /, *,
		string: str = ...,
		index: int = ...,
		noEnhancement: None = ...,
	) -> None: ...

class DeleteEventCondition_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_specific = 1
		PR_aa_specific = 2
		PR_domain = 3
		PR_vmd = 4

	@property
	def present(self) -> PRESENT: ...

	class specific_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	specific: specific_TYPE
	aa_specific: None | None
	@property
	def domain(self) -> Identifier | None: ...
	@domain.setter
	def domain(self, value: Identifier | str | None) -> None: ...
	vmd: None | None
	def __init__(
		self, /, *,
		specific: specific_TYPE = ...,
		aa_specific: None = ...,
		domain: Identifier = ...,
		vmd: None = ...,
	) -> None: ...

class DeleteEventCondition_Response(_Asn1BasicType[Unsigned32]):
	pass

class GetEventConditionAttributes_Request(_Asn1BasicType[ObjectName]):
	pass

class GetEventConditionAttributes_Response(_Asn1Type): # SEQUENCE

	class monitoredVariable_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_variableReference = 1
			PR_undefined = 2

		@property
		def present(self) -> PRESENT: ...
		variableReference: VariableSpecification | None
		undefined: None | None
		def __init__(
			self, /, *,
			variableReference: VariableSpecification = ...,
			undefined: None = ...,
		) -> None: ...

	monitoredVariable: monitoredVariable_TYPE | None
	mmsDeletable: bool | None
	@property
	def class_(self) -> EC_Class: ...
	@class_.setter
	def class_(self, value: EC_Class | int) -> None: ...
	@property
	def priority(self) -> Priority | None: ...
	@priority.setter
	def priority(self, value: Priority | int | None) -> None: ...
	@property
	def severity(self) -> Unsigned8 | None: ...
	@severity.setter
	def severity(self, value: Unsigned8 | int | None) -> None: ...
	alarmSummaryReports: bool | None
	@property
	def evaluationInterval(self) -> Unsigned32 | None: ...
	@evaluationInterval.setter
	def evaluationInterval(self, value: Unsigned32 | int | None) -> None: ...
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		mmsDeletable: bool = ...,
		class_: EC_Class = ...,
		priority: Priority = ...,
		severity: Unsigned8 = ...,
		alarmSummaryReports: bool = ...,
		monitoredVariable: monitoredVariable_TYPE = ...,
		evaluationInterval: Unsigned32 = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class CS_GetEventConditionAttributes_Response(_Asn1Type): # SEQUENCE

	class groupPriorityOverride_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_priority = 1
			PR_undefined = 2

		@property
		def present(self) -> PRESENT: ...
		@property
		def priority(self) -> Priority | None: ...
		@priority.setter
		def priority(self, value: Priority | int | None) -> None: ...
		undefined: None | None
		def __init__(
			self, /, *,
			priority: Priority = ...,
			undefined: None = ...,
		) -> None: ...

	groupPriorityOverride: groupPriorityOverride_TYPE | None

	class listOfReferencingECL_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfReferencingECL: listOfReferencingECL_TYPE | None

	class displayEnhancement_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_string = 1
			PR_index = 2
			PR_noEnhancement = 3

		@property
		def present(self) -> PRESENT: ...
		string: str | None
		index: int | None
		noEnhancement: None | None
		def __init__(
			self, /, *,
			string: str = ...,
			index: int = ...,
			noEnhancement: None = ...,
		) -> None: ...

	displayEnhancement: displayEnhancement_TYPE
	def __init__(
		self, /, *,
		groupPriorityOverride: groupPriorityOverride_TYPE = ...,
		listOfReferencingECL: listOfReferencingECL_TYPE = ...,
		displayEnhancement: displayEnhancement_TYPE = ...,
	) -> None: ...

class ReportEventConditionStatus_Request(_Asn1BasicType[ObjectName]):
	pass

class ReportEventConditionStatus_Response(_Asn1Type): # SEQUENCE
	@property
	def currentState(self) -> EC_State: ...
	@currentState.setter
	def currentState(self, value: EC_State | int) -> None: ...
	@property
	def numberOfEventEnrollments(self) -> Unsigned32: ...
	@numberOfEventEnrollments.setter
	def numberOfEventEnrollments(self, value: Unsigned32 | int) -> None: ...
	enabled: bool | None
	timeOfLastTransitionToActive: EventTime | None
	timeOfLastTransitionToIdle: EventTime | None
	def __init__(
		self, /, *,
		currentState: EC_State = ...,
		numberOfEventEnrollments: Unsigned32 = ...,
		enabled: bool = ...,
		timeOfLastTransitionToActive: EventTime = ...,
		timeOfLastTransitionToIdle: EventTime = ...,
	) -> None: ...

class AlterEventConditionMonitoring_Request(_Asn1Type): # SEQUENCE
	eventConditionName: ObjectName
	enabled: bool | None
	@property
	def priority(self) -> Priority | None: ...
	@priority.setter
	def priority(self, value: Priority | int | None) -> None: ...
	alarmSummaryReports: bool | None
	@property
	def evaluationInterval(self) -> Unsigned32 | None: ...
	@evaluationInterval.setter
	def evaluationInterval(self, value: Unsigned32 | int | None) -> None: ...
	def __init__(
		self, /, *,
		eventConditionName: ObjectName = ...,
		enabled: bool = ...,
		priority: Priority = ...,
		alarmSummaryReports: bool = ...,
		evaluationInterval: Unsigned32 = ...,
	) -> None: ...

class AlterEventConditionMonitoring_Response(_Asn1BasicType[None]):
	pass

class CS_AlterEventConditionMonitoring_Request(_Asn1Type): # SEQUENCE

	class changeDisplay_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_string = 1
			PR_index = 2
			PR_noEnhancement = 3

		@property
		def present(self) -> PRESENT: ...
		string: str | None
		index: int | None
		noEnhancement: None | None
		def __init__(
			self, /, *,
			string: str = ...,
			index: int = ...,
			noEnhancement: None = ...,
		) -> None: ...

	changeDisplay: changeDisplay_TYPE | None
	def __init__(
		self, /, *,
		changeDisplay: changeDisplay_TYPE = ...,
	) -> None: ...

class DefineEventAction_Request(_Asn1Type): # SEQUENCE

	class listOfModifier_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Modifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Modifier: ...
		def __setitem__(self, index: int, value: Modifier) -> None: ...
		def add(self, value: Modifier) -> None: ...
		def extend(self, values: EXT_Iterable[Modifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfModifier: listOfModifier_TYPE | None
	eventActionName: ObjectName
	confirmedServiceRequest: ConfirmedServiceRequest | None
	cs_extension: Request_Detail | None
	def __init__(
		self, /, *,
		eventActionName: ObjectName = ...,
		listOfModifier: listOfModifier_TYPE = ...,
		confirmedServiceRequest: ConfirmedServiceRequest = ...,
		cs_extension: Request_Detail = ...,
	) -> None: ...

class DefineEventAction_Response(_Asn1BasicType[None]):
	pass

class DeleteEventAction_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_specific = 1
		PR_aa_specific = 2
		PR_domain = 3
		PR_vmd = 4

	@property
	def present(self) -> PRESENT: ...

	class specific_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	specific: specific_TYPE
	aa_specific: None | None
	@property
	def domain(self) -> Identifier | None: ...
	@domain.setter
	def domain(self, value: Identifier | str | None) -> None: ...
	vmd: None | None
	def __init__(
		self, /, *,
		specific: specific_TYPE = ...,
		aa_specific: None = ...,
		domain: Identifier = ...,
		vmd: None = ...,
	) -> None: ...

class DeleteEventAction_Response(_Asn1BasicType[Unsigned32]):
	pass

class GetEventActionAttributes_Request(_Asn1BasicType[ObjectName]):
	pass

class GetEventActionAttributes_Response(_Asn1Type): # SEQUENCE

	class listOfModifier_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Modifier] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Modifier: ...
		def __setitem__(self, index: int, value: Modifier) -> None: ...
		def add(self, value: Modifier) -> None: ...
		def extend(self, values: EXT_Iterable[Modifier]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfModifier: listOfModifier_TYPE
	mmsDeletable: bool | None
	confirmedServiceRequest: ConfirmedServiceRequest
	cs_extension: Request_Detail | None
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		mmsDeletable: bool = ...,
		listOfModifier: listOfModifier_TYPE = ...,
		confirmedServiceRequest: ConfirmedServiceRequest = ...,
		cs_extension: Request_Detail = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class ReportEventActionStatus_Request(_Asn1BasicType[ObjectName]):
	pass

class ReportEventActionStatus_Response(_Asn1BasicType[Unsigned32]):
	pass

class DefineEventEnrollment_Request(_Asn1Type): # SEQUENCE
	eventEnrollmentName: ObjectName
	eventConditionName: ObjectName
	@property
	def eventConditionTransitions(self) -> Transitions: ...
	@eventConditionTransitions.setter
	def eventConditionTransitions(self, value: Transitions | EXT_bitarray | int | bytes) -> None: ...
	@property
	def alarmAcknowledgmentRule(self) -> AlarmAckRule: ...
	@alarmAcknowledgmentRule.setter
	def alarmAcknowledgmentRule(self, value: AlarmAckRule | int) -> None: ...
	eventActionName: ObjectName | None
	clientApplication: ApplicationReference | None
	def __init__(
		self, /, *,
		eventEnrollmentName: ObjectName = ...,
		eventConditionName: ObjectName = ...,
		eventConditionTransitions: Transitions = ...,
		alarmAcknowledgmentRule: AlarmAckRule = ...,
		eventActionName: ObjectName = ...,
		clientApplication: ApplicationReference = ...,
	) -> None: ...

class DefineEventEnrollment_Response(_Asn1BasicType[None]):
	pass

class DefineEventEnrollment_Error(_Asn1BasicType[ObjectName]):
	pass

class CS_DefineEventEnrollment_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_string = 1
		PR_index = 2
		PR_noEnhancement = 3

	@property
	def present(self) -> PRESENT: ...
	string: str | None
	index: int | None
	noEnhancement: None | None
	def __init__(
		self, /, *,
		string: str = ...,
		index: int = ...,
		noEnhancement: None = ...,
	) -> None: ...

class DeleteEventEnrollment_Request(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_specific = 1
		PR_ec = 2
		PR_ea = 3

	@property
	def present(self) -> PRESENT: ...

	class specific_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	specific: specific_TYPE
	ec: ObjectName | None
	ea: ObjectName | None
	def __init__(
		self, /, *,
		specific: specific_TYPE = ...,
		ec: ObjectName = ...,
		ea: ObjectName = ...,
	) -> None: ...

class DeleteEventEnrollment_Response(_Asn1BasicType[Unsigned32]):
	pass

class GetEventEnrollmentAttributes_Request(_Asn1Type): # SEQUENCE

	class eventEnrollmentNames_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	eventEnrollmentNames: eventEnrollmentNames_TYPE | None

	class scopeOfRequest_VALUES(EXT_IntEnum):
		V_specific = 0
		V_client = 1
		V_ec = 2
		V_ea = 3

	scopeOfRequest: scopeOfRequest_VALUES | None
	clientApplication: ApplicationReference | None
	eventConditionName: ObjectName | None
	eventActionName: ObjectName | None
	continueAfter: ObjectName | None
	def __init__(
		self, /, *,
		scopeOfRequest: scopeOfRequest_VALUES = ...,
		eventEnrollmentNames: eventEnrollmentNames_TYPE = ...,
		clientApplication: ApplicationReference = ...,
		eventConditionName: ObjectName = ...,
		eventActionName: ObjectName = ...,
		continueAfter: ObjectName = ...,
	) -> None: ...

class GetEventEnrollmentAttributes_Response(_Asn1Type): # SEQUENCE

	class listOfEEAttributes_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[EEAttributes] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> EEAttributes: ...
		def __setitem__(self, index: int, value: EEAttributes) -> None: ...
		def add(self, value: EEAttributes) -> None: ...
		def extend(self, values: EXT_Iterable[EEAttributes]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEEAttributes: listOfEEAttributes_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfEEAttributes: listOfEEAttributes_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class EEAttributes(_Asn1Type): # SEQUENCE

	class eventConditionName_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_eventCondition = 1
			PR_undefined = 2

		@property
		def present(self) -> PRESENT: ...
		eventCondition: ObjectName | None
		undefined: None | None
		def __init__(
			self, /, *,
			eventCondition: ObjectName = ...,
			undefined: None = ...,
		) -> None: ...

	eventConditionName: eventConditionName_TYPE

	class eventActionName_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_eventAction = 1
			PR_undefined = 2

		@property
		def present(self) -> PRESENT: ...
		eventAction: ObjectName | None
		undefined: None | None
		def __init__(
			self, /, *,
			eventAction: ObjectName = ...,
			undefined: None = ...,
		) -> None: ...

	eventActionName: eventActionName_TYPE | None

	class displayEnhancement_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_string = 1
			PR_index = 2
			PR_noEnhancement = 3

		@property
		def present(self) -> PRESENT: ...
		string: str | None
		index: int | None
		noEnhancement: None | None
		def __init__(
			self, /, *,
			string: str = ...,
			index: int = ...,
			noEnhancement: None = ...,
		) -> None: ...

	displayEnhancement: displayEnhancement_TYPE
	eventEnrollmentName: ObjectName
	clientApplication: ApplicationReference | None
	mmsDeletable: bool | None
	@property
	def enrollmentClass(self) -> EE_Class: ...
	@enrollmentClass.setter
	def enrollmentClass(self, value: EE_Class | int) -> None: ...
	@property
	def duration(self) -> EE_Duration | None: ...
	@duration.setter
	def duration(self, value: EE_Duration | int | None) -> None: ...
	@property
	def invokeID(self) -> Unsigned32 | None: ...
	@invokeID.setter
	def invokeID(self, value: Unsigned32 | int | None) -> None: ...
	@property
	def remainingAcceptableDelay(self) -> Unsigned32 | None: ...
	@remainingAcceptableDelay.setter
	def remainingAcceptableDelay(self, value: Unsigned32 | int | None) -> None: ...
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		eventEnrollmentName: ObjectName = ...,
		eventConditionName: eventConditionName_TYPE = ...,
		eventActionName: eventActionName_TYPE = ...,
		clientApplication: ApplicationReference = ...,
		mmsDeletable: bool = ...,
		enrollmentClass: EE_Class = ...,
		duration: EE_Duration = ...,
		invokeID: Unsigned32 = ...,
		remainingAcceptableDelay: Unsigned32 = ...,
		displayEnhancement: displayEnhancement_TYPE = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class ReportEventEnrollmentStatus_Request(_Asn1BasicType[ObjectName]):
	pass

class ReportEventEnrollmentStatus_Response(_Asn1Type): # SEQUENCE
	@property
	def eventConditionTransitions(self) -> Transitions: ...
	@eventConditionTransitions.setter
	def eventConditionTransitions(self, value: Transitions | EXT_bitarray | int | bytes) -> None: ...
	notificationLost: bool | None
	@property
	def duration(self) -> EE_Duration: ...
	@duration.setter
	def duration(self, value: EE_Duration | int) -> None: ...
	@property
	def alarmAcknowledgmentRule(self) -> AlarmAckRule | None: ...
	@alarmAcknowledgmentRule.setter
	def alarmAcknowledgmentRule(self, value: AlarmAckRule | int | None) -> None: ...
	@property
	def currentState(self) -> EE_State: ...
	@currentState.setter
	def currentState(self, value: EE_State | int) -> None: ...
	def __init__(
		self, /, *,
		eventConditionTransitions: Transitions = ...,
		notificationLost: bool = ...,
		duration: EE_Duration = ...,
		alarmAcknowledgmentRule: AlarmAckRule = ...,
		currentState: EE_State = ...,
	) -> None: ...

class AlterEventEnrollment_Request(_Asn1Type): # SEQUENCE
	eventEnrollmentName: ObjectName
	@property
	def eventConditionTransitions(self) -> Transitions | None: ...
	@eventConditionTransitions.setter
	def eventConditionTransitions(self, value: Transitions | EXT_bitarray | int | bytes | None) -> None: ...
	@property
	def alarmAcknowledgmentRule(self) -> AlarmAckRule | None: ...
	@alarmAcknowledgmentRule.setter
	def alarmAcknowledgmentRule(self, value: AlarmAckRule | int | None) -> None: ...
	def __init__(
		self, /, *,
		eventEnrollmentName: ObjectName = ...,
		eventConditionTransitions: Transitions = ...,
		alarmAcknowledgmentRule: AlarmAckRule = ...,
	) -> None: ...

class AlterEventEnrollment_Response(_Asn1Type): # SEQUENCE

	class currentState_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_state = 1
			PR_undefined = 2

		@property
		def present(self) -> PRESENT: ...
		@property
		def state(self) -> EE_State | None: ...
		@state.setter
		def state(self, value: EE_State | int | None) -> None: ...
		undefined: None | None
		def __init__(
			self, /, *,
			state: EE_State = ...,
			undefined: None = ...,
		) -> None: ...

	currentState: currentState_TYPE
	transitionTime: EventTime
	def __init__(
		self, /, *,
		currentState: currentState_TYPE = ...,
		transitionTime: EventTime = ...,
	) -> None: ...

class CS_AlterEventEnrollment_Request(_Asn1Type): # SEQUENCE

	class changeDisplay_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_string = 1
			PR_index = 2
			PR_noEnhancement = 3

		@property
		def present(self) -> PRESENT: ...
		string: str | None
		index: int | None
		noEnhancement: None | None
		def __init__(
			self, /, *,
			string: str = ...,
			index: int = ...,
			noEnhancement: None = ...,
		) -> None: ...

	changeDisplay: changeDisplay_TYPE | None
	def __init__(
		self, /, *,
		changeDisplay: changeDisplay_TYPE = ...,
	) -> None: ...

class EE_State(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_disabled = 0
		V_idle = 1
		V_active = 2
		V_activeNoAckA = 3
		V_idleNoAckI = 4
		V_idleNoAckA = 5
		V_idleAcked = 6
		V_activeAcked = 7
		V_undefined = 8

	@property
	def value(self) -> EE_State.VALUES: ...
	@value.setter
	def value(self, value: EE_State.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class DefineEventConditionList_Request(_Asn1Type): # SEQUENCE

	class listOfEventConditionName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionName: listOfEventConditionName_TYPE

	class listOfEventConditionListName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionListName: listOfEventConditionListName_TYPE | None
	eventConditionListName: ObjectName
	def __init__(
		self, /, *,
		eventConditionListName: ObjectName = ...,
		listOfEventConditionName: listOfEventConditionName_TYPE = ...,
		listOfEventConditionListName: listOfEventConditionListName_TYPE = ...,
	) -> None: ...

class DefineEventConditionList_Response(_Asn1BasicType[None]):
	pass

class DefineEventConditionList_Error(_Asn1BasicType[ObjectName]):
	pass

class DeleteEventConditionList_Request(_Asn1BasicType[ObjectName]):
	pass

class DeleteEventConditionList_Response(_Asn1BasicType[None]):
	pass

class AddEventConditionListReference_Request(_Asn1Type): # SEQUENCE

	class listOfEventConditionName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionName: listOfEventConditionName_TYPE

	class listOfEventConditionListName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionListName: listOfEventConditionListName_TYPE | None
	eventConditionListName: ObjectName
	def __init__(
		self, /, *,
		eventConditionListName: ObjectName = ...,
		listOfEventConditionName: listOfEventConditionName_TYPE = ...,
		listOfEventConditionListName: listOfEventConditionListName_TYPE = ...,
	) -> None: ...

class AddEventConditionListReference_Response(_Asn1BasicType[None]):
	pass

class AddEventConditionListReference_Error(_Asn1BasicType[ObjectName]):
	pass

class RemoveEventConditionListReference_Request(_Asn1Type): # SEQUENCE

	class listOfEventConditionName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionName: listOfEventConditionName_TYPE

	class listOfEventConditionListName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionListName: listOfEventConditionListName_TYPE
	eventConditionListName: ObjectName
	def __init__(
		self, /, *,
		eventConditionListName: ObjectName = ...,
		listOfEventConditionName: listOfEventConditionName_TYPE = ...,
		listOfEventConditionListName: listOfEventConditionListName_TYPE = ...,
	) -> None: ...

class RemoveEventConditionListReference_Response(_Asn1BasicType[None]):
	pass

class RemoveEventConditionListReference_Error(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_eventCondition = 1
		PR_eventConditionList = 2

	@property
	def present(self) -> PRESENT: ...
	eventCondition: ObjectName | None
	eventConditionList: ObjectName | None
	def __init__(
		self, /, *,
		eventCondition: ObjectName = ...,
		eventConditionList: ObjectName = ...,
	) -> None: ...

class GetEventConditionListAttributes_Request(_Asn1BasicType[ObjectName]):
	pass

class GetEventConditionListAttributes_Response(_Asn1Type): # SEQUENCE

	class listOfEventConditionName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionName: listOfEventConditionName_TYPE

	class listOfEventConditionListName_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[ObjectName] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> ObjectName: ...
		def __setitem__(self, index: int, value: ObjectName) -> None: ...
		def add(self, value: ObjectName) -> None: ...
		def extend(self, values: EXT_Iterable[ObjectName]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionListName: listOfEventConditionListName_TYPE | None
	def __init__(
		self, /, *,
		listOfEventConditionName: listOfEventConditionName_TYPE = ...,
		listOfEventConditionListName: listOfEventConditionListName_TYPE = ...,
	) -> None: ...

class ReportEventConditionListStatus_Request(_Asn1Type): # SEQUENCE
	eventConditionListName: ObjectName
	@property
	def continueAfter(self) -> Identifier | None: ...
	@continueAfter.setter
	def continueAfter(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		eventConditionListName: ObjectName = ...,
		continueAfter: Identifier = ...,
	) -> None: ...

class ReportEventConditionListStatus_Response(_Asn1Type): # SEQUENCE

	class listOfEventConditionStatus_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[EventConditionStatus] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> EventConditionStatus: ...
		def __setitem__(self, index: int, value: EventConditionStatus) -> None: ...
		def add(self, value: EventConditionStatus) -> None: ...
		def extend(self, values: EXT_Iterable[EventConditionStatus]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfEventConditionStatus: listOfEventConditionStatus_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfEventConditionStatus: listOfEventConditionStatus_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class EventConditionStatus(_Asn1Type): # SEQUENCE
	eventConditionName: ObjectName
	@property
	def currentState(self) -> EC_State: ...
	@currentState.setter
	def currentState(self, value: EC_State | int) -> None: ...
	@property
	def numberOfEventEnrollments(self) -> Unsigned32: ...
	@numberOfEventEnrollments.setter
	def numberOfEventEnrollments(self, value: Unsigned32 | int) -> None: ...
	enabled: bool | None
	timeOfLastTransitionToActive: EventTime | None
	timeOfLastTransitionToIdle: EventTime | None
	def __init__(
		self, /, *,
		eventConditionName: ObjectName = ...,
		currentState: EC_State = ...,
		numberOfEventEnrollments: Unsigned32 = ...,
		enabled: bool = ...,
		timeOfLastTransitionToActive: EventTime = ...,
		timeOfLastTransitionToIdle: EventTime = ...,
	) -> None: ...

class AlterEventConditionListMonitoring_Request(_Asn1Type): # SEQUENCE

	class priorityChange_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_priorityValue = 1
			PR_priorityReset = 2

		@property
		def present(self) -> PRESENT: ...
		priorityValue: int | None
		priorityReset: None | None
		def __init__(
			self, /, *,
			priorityValue: int = ...,
			priorityReset: None = ...,
		) -> None: ...

	priorityChange: priorityChange_TYPE | None
	eventConditionListName: ObjectName
	enabled: bool
	def __init__(
		self, /, *,
		eventConditionListName: ObjectName = ...,
		enabled: bool = ...,
		priorityChange: priorityChange_TYPE = ...,
	) -> None: ...

class AlterEventConditionListMonitoring_Response(_Asn1BasicType[None]):
	pass

class ReadJournal_Request(_Asn1Type): # SEQUENCE

	class rangeStartSpecification_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_startingTime = 1
			PR_startingEntry = 2

		@property
		def present(self) -> PRESENT: ...
		@property
		def startingTime(self) -> TimeOfDay | None: ...
		@startingTime.setter
		def startingTime(self, value: TimeOfDay | bytes | None) -> None: ...
		startingEntry: bytes | None
		def __init__(
			self, /, *,
			startingTime: TimeOfDay = ...,
			startingEntry: bytes = ...,
		) -> None: ...

	rangeStartSpecification: rangeStartSpecification_TYPE | None

	class rangeStopSpecification_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_endingTime = 1
			PR_numberOfEntries = 2

		@property
		def present(self) -> PRESENT: ...
		@property
		def endingTime(self) -> TimeOfDay | None: ...
		@endingTime.setter
		def endingTime(self, value: TimeOfDay | bytes | None) -> None: ...
		@property
		def numberOfEntries(self) -> Integer32 | None: ...
		@numberOfEntries.setter
		def numberOfEntries(self, value: Integer32 | int | None) -> None: ...
		def __init__(
			self, /, *,
			endingTime: TimeOfDay = ...,
			numberOfEntries: Integer32 = ...,
		) -> None: ...

	rangeStopSpecification: rangeStopSpecification_TYPE | None

	class listOfVariables_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[str] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> str: ...
		def __setitem__(self, index: int, value: str) -> None: ...
		def add(self, value: str) -> None: ...
		def extend(self, values: EXT_Iterable[str]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfVariables: listOfVariables_TYPE | None

	class entryToStartAfter_TYPE(_Asn1Type): # SEQUENCE
		@property
		def timeSpecification(self) -> TimeOfDay: ...
		@timeSpecification.setter
		def timeSpecification(self, value: TimeOfDay | bytes) -> None: ...
		entrySpecification: bytes
		def __init__(
			self, /, *,
			timeSpecification: TimeOfDay = ...,
			entrySpecification: bytes = ...,
		) -> None: ...

	entryToStartAfter: entryToStartAfter_TYPE | None
	journalName: ObjectName
	def __init__(
		self, /, *,
		journalName: ObjectName = ...,
		rangeStartSpecification: rangeStartSpecification_TYPE = ...,
		rangeStopSpecification: rangeStopSpecification_TYPE = ...,
		listOfVariables: listOfVariables_TYPE = ...,
		entryToStartAfter: entryToStartAfter_TYPE = ...,
	) -> None: ...

class ReadJournal_Response(_Asn1Type): # SEQUENCE

	class listOfJournalEntry_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[JournalEntry] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> JournalEntry: ...
		def __setitem__(self, index: int, value: JournalEntry) -> None: ...
		def add(self, value: JournalEntry) -> None: ...
		def extend(self, values: EXT_Iterable[JournalEntry]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfJournalEntry: listOfJournalEntry_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfJournalEntry: listOfJournalEntry_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class JournalEntry(_Asn1Type): # SEQUENCE
	entryIdentifier: bytes
	originatingApplication: ApplicationReference
	entryContent: EntryContent
	def __init__(
		self, /, *,
		entryIdentifier: bytes = ...,
		originatingApplication: ApplicationReference = ...,
		entryContent: EntryContent = ...,
	) -> None: ...

class WriteJournal_Request(_Asn1Type): # SEQUENCE

	class listOfJournalEntry_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[EntryContent] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> EntryContent: ...
		def __setitem__(self, index: int, value: EntryContent) -> None: ...
		def add(self, value: EntryContent) -> None: ...
		def extend(self, values: EXT_Iterable[EntryContent]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfJournalEntry: listOfJournalEntry_TYPE
	journalName: ObjectName
	def __init__(
		self, /, *,
		journalName: ObjectName = ...,
		listOfJournalEntry: listOfJournalEntry_TYPE = ...,
	) -> None: ...

class WriteJournal_Response(_Asn1BasicType[None]):
	pass

class InitializeJournal_Request(_Asn1Type): # SEQUENCE

	class limitSpecification_TYPE(_Asn1Type): # SEQUENCE
		@property
		def limitingTime(self) -> TimeOfDay: ...
		@limitingTime.setter
		def limitingTime(self, value: TimeOfDay | bytes) -> None: ...
		limitingEntry: bytes | None
		def __init__(
			self, /, *,
			limitingTime: TimeOfDay = ...,
			limitingEntry: bytes = ...,
		) -> None: ...

	limitSpecification: limitSpecification_TYPE | None
	journalName: ObjectName
	def __init__(
		self, /, *,
		journalName: ObjectName = ...,
		limitSpecification: limitSpecification_TYPE = ...,
	) -> None: ...

class InitializeJournal_Response(_Asn1BasicType[Unsigned32]):
	pass

class ReportJournalStatus_Request(_Asn1BasicType[ObjectName]):
	pass

class ReportJournalStatus_Response(_Asn1Type): # SEQUENCE
	@property
	def currentEntries(self) -> Unsigned32: ...
	@currentEntries.setter
	def currentEntries(self, value: Unsigned32 | int) -> None: ...
	mmsDeletable: bool
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		currentEntries: Unsigned32 = ...,
		mmsDeletable: bool = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class CreateJournal_Request(_Asn1Type): # SEQUENCE
	journalName: ObjectName
	def __init__(
		self, /, *,
		journalName: ObjectName = ...,
	) -> None: ...

class CreateJournal_Response(_Asn1BasicType[None]):
	pass

class DeleteJournal_Request(_Asn1Type): # SEQUENCE
	journalName: ObjectName
	def __init__(
		self, /, *,
		journalName: ObjectName = ...,
	) -> None: ...

class DeleteJournal_Response(_Asn1BasicType[None]):
	pass

class EntryContent(_Asn1Type): # SEQUENCE

	class entryForm_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_data = 1
			PR_annotation = 2

		@property
		def present(self) -> PRESENT: ...

		class data_TYPE(_Asn1Type): # SEQUENCE

			class event_TYPE(_Asn1Type): # SEQUENCE
				eventConditionName: ObjectName
				@property
				def currentState(self) -> EC_State: ...
				@currentState.setter
				def currentState(self, value: EC_State | int) -> None: ...
				def __init__(
					self, /, *,
					eventConditionName: ObjectName = ...,
					currentState: EC_State = ...,
				) -> None: ...

			event: event_TYPE | None

			class listOfVariables_TYPE(_Asn1Type):
				def __init__(self, values: EXT_Iterable[Journal_Variable] | None = ...) -> None: ...
				def __getitem__(self, index: int) -> Journal_Variable: ...
				def __setitem__(self, index: int, value: Journal_Variable) -> None: ...
				def add(self, value: Journal_Variable) -> None: ...
				def extend(self, values: EXT_Iterable[Journal_Variable]) -> None: ...
				def clear(self) -> None: ...
				def __len__(self) -> int: ...
				def __delitem__(self, index: int) -> None: ...

			listOfVariables: listOfVariables_TYPE | None
			def __init__(
				self, /, *,
				event: event_TYPE = ...,
				listOfVariables: listOfVariables_TYPE = ...,
			) -> None: ...

		data: data_TYPE
		@property
		def annotation(self) -> MMSString | None: ...
		@annotation.setter
		def annotation(self, value: MMSString | str | None) -> None: ...
		def __init__(
			self, /, *,
			data: data_TYPE = ...,
			annotation: MMSString = ...,
		) -> None: ...

	entryForm: entryForm_TYPE
	@property
	def occurrenceTime(self) -> TimeOfDay: ...
	@occurrenceTime.setter
	def occurrenceTime(self, value: TimeOfDay | bytes) -> None: ...
	def __init__(
		self, /, *,
		occurrenceTime: TimeOfDay = ...,
		entryForm: entryForm_TYPE = ...,
	) -> None: ...

class ApplicationReference(_Asn1Type): # SEQUENCE
	ap_title: AP_title | None
	@property
	def ap_invocation_id(self) -> AP_invocation_identifier | None: ...
	@ap_invocation_id.setter
	def ap_invocation_id(self, value: AP_invocation_identifier | int | None) -> None: ...
	ae_qualifier: AE_qualifier | None
	@property
	def ae_invocation_id(self) -> AE_invocation_identifier | None: ...
	@ae_invocation_id.setter
	def ae_invocation_id(self, value: AE_invocation_identifier | int | None) -> None: ...
	def __init__(
		self, /, *,
		ap_title: AP_title = ...,
		ap_invocation_id: AP_invocation_identifier = ...,
		ae_qualifier: AE_qualifier = ...,
		ae_invocation_id: AE_invocation_identifier = ...,
	) -> None: ...

class ObtainFile_Request(_Asn1Type): # SEQUENCE
	sourceFileServer: ApplicationReference | None
	@property
	def sourceFile(self) -> FileName: ...
	@sourceFile.setter
	def sourceFile(self, value: FileName | list) -> None: ...
	@property
	def destinationFile(self) -> FileName: ...
	@destinationFile.setter
	def destinationFile(self, value: FileName | list) -> None: ...
	def __init__(
		self, /, *,
		sourceFileServer: ApplicationReference = ...,
		sourceFile: FileName = ...,
		destinationFile: FileName = ...,
	) -> None: ...

class ObtainFile_Response(_Asn1BasicType[None]):
	pass

class ObtainFile_Error(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_source_file = 0
		V_destination_file = 1

	@property
	def value(self) -> ObtainFile_Error.VALUES: ...
	@value.setter
	def value(self, value: ObtainFile_Error.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class FileOpen_Request(_Asn1Type): # SEQUENCE
	@property
	def fileName(self) -> FileName: ...
	@fileName.setter
	def fileName(self, value: FileName | list) -> None: ...
	@property
	def initialPosition(self) -> Unsigned32: ...
	@initialPosition.setter
	def initialPosition(self, value: Unsigned32 | int) -> None: ...
	def __init__(
		self, /, *,
		fileName: FileName = ...,
		initialPosition: Unsigned32 = ...,
	) -> None: ...

class FileOpen_Response(_Asn1Type): # SEQUENCE
	@property
	def frsmID(self) -> Integer32: ...
	@frsmID.setter
	def frsmID(self, value: Integer32 | int) -> None: ...
	fileAttributes: FileAttributes
	def __init__(
		self, /, *,
		frsmID: Integer32 = ...,
		fileAttributes: FileAttributes = ...,
	) -> None: ...

class FileRead_Request(_Asn1BasicType[Integer32]):
	pass

class FileRead_Response(_Asn1Type): # SEQUENCE
	fileData: bytes
	moreFollows: bool | None
	def __init__(
		self, /, *,
		fileData: bytes = ...,
		moreFollows: bool = ...,
	) -> None: ...

class FileRename_Request(_Asn1Type): # SEQUENCE
	@property
	def currentFileName(self) -> FileName: ...
	@currentFileName.setter
	def currentFileName(self, value: FileName | list) -> None: ...
	@property
	def newFileName(self) -> FileName: ...
	@newFileName.setter
	def newFileName(self, value: FileName | list) -> None: ...
	def __init__(
		self, /, *,
		currentFileName: FileName = ...,
		newFileName: FileName = ...,
	) -> None: ...

class FileRename_Response(_Asn1BasicType[None]):
	pass

class FileRename_Error(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_source_file = 0
		V_destination_file = 1

	@property
	def value(self) -> FileRename_Error.VALUES: ...
	@value.setter
	def value(self, value: FileRename_Error.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class FileDelete_Request(_Asn1BasicType[FileName]):
	pass

class FileDelete_Response(_Asn1BasicType[None]):
	pass

class FileClose_Request(_Asn1BasicType[Integer32]):
	pass

class FileClose_Response(_Asn1BasicType[None]):
	pass

class FileDirectory_Request(_Asn1Type): # SEQUENCE
	@property
	def fileSpecification(self) -> FileName | None: ...
	@fileSpecification.setter
	def fileSpecification(self, value: FileName | list | None) -> None: ...
	@property
	def continueAfter(self) -> FileName | None: ...
	@continueAfter.setter
	def continueAfter(self, value: FileName | list | None) -> None: ...
	def __init__(
		self, /, *,
		fileSpecification: FileName = ...,
		continueAfter: FileName = ...,
	) -> None: ...

class FileDirectory_Response(_Asn1Type): # SEQUENCE

	class listOfDirectoryEntry_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[DirectoryEntry] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> DirectoryEntry: ...
		def __setitem__(self, index: int, value: DirectoryEntry) -> None: ...
		def add(self, value: DirectoryEntry) -> None: ...
		def extend(self, values: EXT_Iterable[DirectoryEntry]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	listOfDirectoryEntry: listOfDirectoryEntry_TYPE
	moreFollows: bool | None
	def __init__(
		self, /, *,
		listOfDirectoryEntry: listOfDirectoryEntry_TYPE = ...,
		moreFollows: bool = ...,
	) -> None: ...

class DirectoryEntry(_Asn1Type): # SEQUENCE
	@property
	def fileName(self) -> FileName: ...
	@fileName.setter
	def fileName(self, value: FileName | list) -> None: ...
	fileAttributes: FileAttributes
	def __init__(
		self, /, *,
		fileName: FileName = ...,
		fileAttributes: FileAttributes = ...,
	) -> None: ...

class FileAttributes(_Asn1Type): # SEQUENCE
	@property
	def sizeOfFile(self) -> Unsigned32: ...
	@sizeOfFile.setter
	def sizeOfFile(self, value: Unsigned32 | int) -> None: ...
	lastModified: bytes | None
	def __init__(
		self, /, *,
		sizeOfFile: Unsigned32 = ...,
		lastModified: bytes = ...,
	) -> None: ...

class ScatteredAccessDescription(_Asn1Type):

	class Member_TYPE(_Asn1Type): # SEQUENCE
		@property
		def componentName(self) -> Identifier | None: ...
		@componentName.setter
		def componentName(self, value: Identifier | str | None) -> None: ...
		variableSpecification: VariableSpecification | None
		@property
		def alternateAccess(self) -> AlternateAccess | None: ...
		@alternateAccess.setter
		def alternateAccess(self, value: AlternateAccess | list | None) -> None: ...
		def __init__(
			self, /, *,
			componentName: Identifier = ...,
			variableSpecification: VariableSpecification = ...,
			alternateAccess: AlternateAccess = ...,
		) -> None: ...

	def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Member_TYPE: ...
	def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
	def add(self, value: Member_TYPE) -> None: ...
	def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class DefineScatteredAccess_Request(_Asn1Type): # SEQUENCE
	scatteredAccessName: ObjectName
	@property
	def scatteredAccessDescription(self) -> ScatteredAccessDescription: ...
	@scatteredAccessDescription.setter
	def scatteredAccessDescription(self, value: ScatteredAccessDescription | list) -> None: ...
	def __init__(
		self, /, *,
		scatteredAccessName: ObjectName = ...,
		scatteredAccessDescription: ScatteredAccessDescription = ...,
	) -> None: ...

class DefineScatteredAccess_Response(_Asn1BasicType[None]):
	pass

class GetScatteredAccessAttributes_Request(_Asn1BasicType[ObjectName]):
	pass

class GetScatteredAccessAttributes_Response(_Asn1Type): # SEQUENCE
	mmsDeletable: bool
	@property
	def scatteredAccessDescription(self) -> ScatteredAccessDescription: ...
	@scatteredAccessDescription.setter
	def scatteredAccessDescription(self, value: ScatteredAccessDescription | list) -> None: ...
	@property
	def accessControlList(self) -> Identifier | None: ...
	@accessControlList.setter
	def accessControlList(self, value: Identifier | str | None) -> None: ...
	def __init__(
		self, /, *,
		mmsDeletable: bool = ...,
		scatteredAccessDescription: ScatteredAccessDescription = ...,
		accessControlList: Identifier = ...,
	) -> None: ...

class Modifier(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_eventModifier = 1
		PR_semaphoreModifier = 2

	@property
	def present(self) -> PRESENT: ...
	eventModifier: AttachToEventCondition | None
	semaphoreModifier: AttachToSemaphore | None
	def __init__(
		self, /, *,
		eventModifier: AttachToEventCondition = ...,
		semaphoreModifier: AttachToSemaphore = ...,
	) -> None: ...

class ModifierStep(_Asn1Type): # SEQUENCE
	modifierID: int
	modifier: Modifier
	def __init__(
		self, /, *,
		modifierID: int = ...,
		modifier: Modifier = ...,
	) -> None: ...

class ServiceSupportOptions(_Asn1BitStrType):
	V_status: bool # bit 0
	V_getNameList: bool # bit 1
	V_identify: bool # bit 2
	V_rename: bool # bit 3
	V_read: bool # bit 4
	V_write: bool # bit 5
	V_getVariableAccessAttributes: bool # bit 6
	V_defineNamedVariable: bool # bit 7
	V_defineScatteredAccess: bool # bit 8
	V_getScatteredAccessAttributes: bool # bit 9
	V_deleteVariableAccess: bool # bit 10
	V_defineNamedVariableList: bool # bit 11
	V_getNamedVariableListAttributes: bool # bit 12
	V_deleteNamedVariableList: bool # bit 13
	V_defineNamedType: bool # bit 14
	V_getNamedTypeAttributes: bool # bit 15
	V_deleteNamedType: bool # bit 16
	V_input: bool # bit 17
	V_output: bool # bit 18
	V_takeControl: bool # bit 19
	V_relinquishControl: bool # bit 20
	V_defineSemaphore: bool # bit 21
	V_deleteSemaphore: bool # bit 22
	V_reportSemaphoreStatus: bool # bit 23
	V_reportPoolSemaphoreStatus: bool # bit 24
	V_reportSemaphoreEntryStatus: bool # bit 25
	V_initiateDownloadSequence: bool # bit 26
	V_downloadSegment: bool # bit 27
	V_terminateDownloadSequence: bool # bit 28
	V_initiateUploadSequence: bool # bit 29
	V_uploadSegment: bool # bit 30
	V_terminateUploadSequence: bool # bit 31
	V_requestDomainDownload: bool # bit 32
	V_requestDomainUpload: bool # bit 33
	V_loadDomainContent: bool # bit 34
	V_storeDomainContent: bool # bit 35
	V_deleteDomain: bool # bit 36
	V_getDomainAttributes: bool # bit 37
	V_createProgramInvocation: bool # bit 38
	V_deleteProgramInvocation: bool # bit 39
	V_start: bool # bit 40
	V_stop: bool # bit 41
	V_resume: bool # bit 42
	V_reset: bool # bit 43
	V_kill: bool # bit 44
	V_getProgramInvocationAttributes: bool # bit 45
	V_obtainFile: bool # bit 46
	V_defineEventCondition: bool # bit 47
	V_deleteEventCondition: bool # bit 48
	V_getEventConditionAttributes: bool # bit 49
	V_reportEventConditionStatus: bool # bit 50
	V_alterEventConditionMonitoring: bool # bit 51
	V_triggerEvent: bool # bit 52
	V_defineEventAction: bool # bit 53
	V_deleteEventAction: bool # bit 54
	V_getEventActionAttributes: bool # bit 55
	V_reportEventActionStatus: bool # bit 56
	V_defineEventEnrollment: bool # bit 57
	V_deleteEventEnrollment: bool # bit 58
	V_alterEventEnrollment: bool # bit 59
	V_reportEventEnrollmentStatus: bool # bit 60
	V_getEventEnrollmentAttributes: bool # bit 61
	V_acknowledgeEventNotification: bool # bit 62
	V_getAlarmSummary: bool # bit 63
	V_getAlarmEnrollmentSummary: bool # bit 64
	V_readJournal: bool # bit 65
	V_writeJournal: bool # bit 66
	V_initializeJournal: bool # bit 67
	V_reportJournalStatus: bool # bit 68
	V_createJournal: bool # bit 69
	V_deleteJournal: bool # bit 70
	V_getCapabilityList: bool # bit 71
	V_fileOpen: bool # bit 72
	V_fileRead: bool # bit 73
	V_fileClose: bool # bit 74
	V_fileRename: bool # bit 75
	V_fileDelete: bool # bit 76
	V_fileDirectory: bool # bit 77
	V_unsolicitedStatus: bool # bit 78
	V_informationReport: bool # bit 79
	V_eventNotification: bool # bit 80
	V_attachToEventCondition: bool # bit 81
	V_attachToSemaphore: bool # bit 82
	V_conclude: bool # bit 83
	V_cancel: bool # bit 84
	V_getDataExchangeAttributes: bool # bit 85
	V_exchangeData: bool # bit 86
	V_defineAccessControlList: bool # bit 87
	V_getAccessControlListAttributes: bool # bit 88
	V_reportAccessControlledObjects: bool # bit 89
	V_deleteAccessControlList: bool # bit 90
	V_alterAccessControl: bool # bit 91
	V_reconfigureProgramInvocation: bool # bit 92


class ParameterSupportOptions(_Asn1BitStrType):
	V_str1: bool # bit 0
	V_str2: bool # bit 1
	V_vnam: bool # bit 2
	V_valt: bool # bit 3
	V_vadr: bool # bit 4
	V_vsca: bool # bit 5
	V_tpy: bool # bit 6
	V_vlis: bool # bit 7
	V_cei: bool # bit 10
	V_aco: bool # bit 11
	V_sem: bool # bit 12
	V_csr: bool # bit 13
	V_csnc: bool # bit 14
	V_csplc: bool # bit 15
	V_cspi: bool # bit 16
	V_Char: bool # bit 17


class AdditionalSupportOptions(_Asn1BitStrType):
	V_vMDStop: bool # bit 0
	V_vMDReset: bool # bit 1
	V_select: bool # bit 2
	V_alterProgramInvocationAttributes: bool # bit 3
	V_initiateUnitControlLoad: bool # bit 4
	V_unitControlLoadSegment: bool # bit 5
	V_unitControlUpload: bool # bit 6
	V_startUnitControl: bool # bit 7
	V_stopUnitControl: bool # bit 8
	V_createUnitControl: bool # bit 9
	V_addToUnitControl: bool # bit 10
	V_removeFromUnitControl: bool # bit 11
	V_getUnitControlAttributes: bool # bit 12
	V_loadUnitControlFromFile: bool # bit 13
	V_storeUnitControlToFile: bool # bit 14
	V_deleteUnitControl: bool # bit 15
	V_defineEventConditionList: bool # bit 16
	V_deleteEventConditionList: bool # bit 17
	V_addEventConditionListReference: bool # bit 18
	V_removeEventConditionListReference: bool # bit 19
	V_getEventConditionListAttributes: bool # bit 20
	V_reportEventConditionListStatus: bool # bit 21
	V_alterEventConditionListMonitoring: bool # bit 22


class AdditionalCBBOptions(_Asn1BitStrType):
	V_des: bool # bit 0
	V_dei: bool # bit 1
	V_recl: bool # bit 2


class AccessCondition(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_never = 1
		PR_semaphore = 2
		PR_user = 3
		PR_password = 4
		PR_joint = 5
		PR_alternate = 6

	@property
	def present(self) -> PRESENT: ...

	class user_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_association = 1
			PR_none = 2

		@property
		def present(self) -> PRESENT: ...
		association: ApplicationReference | None
		none: None | None
		def __init__(
			self, /, *,
			association: ApplicationReference = ...,
			none: None = ...,
		) -> None: ...

	user: user_TYPE

	class joint_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[AccessCondition] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> AccessCondition: ...
		def __setitem__(self, index: int, value: AccessCondition) -> None: ...
		def add(self, value: AccessCondition) -> None: ...
		def extend(self, values: EXT_Iterable[AccessCondition]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	joint: joint_TYPE

	class alternate_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[AccessCondition] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> AccessCondition: ...
		def __setitem__(self, index: int, value: AccessCondition) -> None: ...
		def add(self, value: AccessCondition) -> None: ...
		def extend(self, values: EXT_Iterable[AccessCondition]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	alternate: alternate_TYPE
	never: None | None
	@property
	def semaphore(self) -> Identifier | None: ...
	@semaphore.setter
	def semaphore(self, value: Identifier | str | None) -> None: ...
	password: Authentication_value | None
	def __init__(
		self, /, *,
		never: None = ...,
		semaphore: Identifier = ...,
		user: user_TYPE = ...,
		password: Authentication_value = ...,
		joint: joint_TYPE = ...,
		alternate: alternate_TYPE = ...,
	) -> None: ...

class DomainState(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_non_existent = 0
		V_loading = 1
		V_ready = 2
		V_in_use = 3
		V_complete = 4
		V_incomplete = 5
		V_d1 = 7
		V_d2 = 8
		V_d3 = 9
		V_d4 = 10
		V_d5 = 11
		V_d6 = 12
		V_d7 = 13
		V_d8 = 14
		V_d9 = 15

	@property
	def value(self) -> DomainState.VALUES: ...
	@value.setter
	def value(self, value: DomainState.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class ProgramInvocationState(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_non_existent = 0
		V_unrunnable = 1
		V_idle = 2
		V_running = 3
		V_stopped = 4
		V_starting = 5
		V_stopping = 6
		V_resuming = 7
		V_resetting = 8

	@property
	def value(self) -> ProgramInvocationState.VALUES: ...
	@value.setter
	def value(self, value: ProgramInvocationState.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class TypeDescription(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_array = 1
		PR_structure = 2
		PR_boolean = 3
		PR_bit_string = 4
		PR_integer = 5
		PR_Unsigned = 6
		PR_floating_point = 7
		PR_octet_string = 8
		PR_visible_string = 9
		PR_generalized_time = 10
		PR_binary_time = 11
		PR_bcd = 12
		PR_objId = 13
		PR_mMSString = 14

	@property
	def present(self) -> PRESENT: ...

	class array_TYPE(_Asn1Type): # SEQUENCE
		packed: bool | None
		@property
		def numberOfElements(self) -> Unsigned32: ...
		@numberOfElements.setter
		def numberOfElements(self, value: Unsigned32 | int) -> None: ...
		elementType: TypeSpecification | None
		def __init__(
			self, /, *,
			packed: bool = ...,
			numberOfElements: Unsigned32 = ...,
			elementType: TypeSpecification = ...,
		) -> None: ...

	array: array_TYPE

	class structure_TYPE(_Asn1Type): # SEQUENCE

		class components_TYPE(_Asn1Type):

			class Member_TYPE(_Asn1Type): # SEQUENCE
				@property
				def componentName(self) -> Identifier | None: ...
				@componentName.setter
				def componentName(self, value: Identifier | str | None) -> None: ...
				componentType: TypeSpecification | None
				def __init__(
					self, /, *,
					componentName: Identifier = ...,
					componentType: TypeSpecification = ...,
				) -> None: ...

			def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
			def __getitem__(self, index: int) -> Member_TYPE: ...
			def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
			def add(self, value: Member_TYPE) -> None: ...
			def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
			def clear(self) -> None: ...
			def __len__(self) -> int: ...
			def __delitem__(self, index: int) -> None: ...

		components: components_TYPE
		packed: bool | None
		def __init__(
			self, /, *,
			packed: bool = ...,
			components: components_TYPE = ...,
		) -> None: ...

	structure: structure_TYPE

	class floating_point_TYPE(_Asn1Type): # SEQUENCE
		@property
		def format_width(self) -> Unsigned8: ...
		@format_width.setter
		def format_width(self, value: Unsigned8 | int) -> None: ...
		@property
		def exponent_width(self) -> Unsigned8: ...
		@exponent_width.setter
		def exponent_width(self, value: Unsigned8 | int) -> None: ...
		def __init__(
			self, /, *,
			format_width: Unsigned8 = ...,
			exponent_width: Unsigned8 = ...,
		) -> None: ...

	floating_point: floating_point_TYPE
	boolean: None | None
	@property
	def bit_string(self) -> Integer32 | None: ...
	@bit_string.setter
	def bit_string(self, value: Integer32 | int | None) -> None: ...
	@property
	def integer(self) -> Unsigned8 | None: ...
	@integer.setter
	def integer(self, value: Unsigned8 | int | None) -> None: ...
	@property
	def unsigned(self) -> Unsigned8 | None: ...
	@unsigned.setter
	def unsigned(self, value: Unsigned8 | int | None) -> None: ...
	@property
	def octet_string(self) -> Integer32 | None: ...
	@octet_string.setter
	def octet_string(self, value: Integer32 | int | None) -> None: ...
	@property
	def visible_string(self) -> Integer32 | None: ...
	@visible_string.setter
	def visible_string(self, value: Integer32 | int | None) -> None: ...
	generalized_time: None | None
	binary_time: bool | None
	@property
	def bcd(self) -> Unsigned8 | None: ...
	@bcd.setter
	def bcd(self, value: Unsigned8 | int | None) -> None: ...
	objId: None | None
	@property
	def mMSString(self) -> Integer32 | None: ...
	@mMSString.setter
	def mMSString(self, value: Integer32 | int | None) -> None: ...
	def __init__(
		self, /, *,
		array: array_TYPE = ...,
		structure: structure_TYPE = ...,
		boolean: None = ...,
		bit_string: Integer32 = ...,
		integer: Unsigned8 = ...,
		unsigned: Unsigned8 = ...,
		floating_point: floating_point_TYPE = ...,
		octet_string: Integer32 = ...,
		visible_string: Integer32 = ...,
		generalized_time: None = ...,
		binary_time: bool = ...,
		bcd: Unsigned8 = ...,
		objId: None = ...,
		mMSString: Integer32 = ...,
	) -> None: ...

class Address(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_numericAddress = 1
		PR_symbolicAddress = 2
		PR_unconstrainedAddress = 3

	@property
	def present(self) -> PRESENT: ...
	@property
	def numericAddress(self) -> Unsigned32 | None: ...
	@numericAddress.setter
	def numericAddress(self, value: Unsigned32 | int | None) -> None: ...
	@property
	def symbolicAddress(self) -> MMSString | None: ...
	@symbolicAddress.setter
	def symbolicAddress(self, value: MMSString | str | None) -> None: ...
	unconstrainedAddress: bytes | None
	def __init__(
		self, /, *,
		numericAddress: Unsigned32 = ...,
		symbolicAddress: MMSString = ...,
		unconstrainedAddress: bytes = ...,
	) -> None: ...

class Priority(_Asn1BasicType[int]):
	pass

class Severity(_Asn1BasicType[int]):
	pass

class EventTime(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_timeOfDay = 1
		PR_timeSequenceIdentifier = 2
		PR_undefined = 3

	@property
	def present(self) -> PRESENT: ...
	@property
	def timeOfDay(self) -> TimeOfDay | None: ...
	@timeOfDay.setter
	def timeOfDay(self, value: TimeOfDay | bytes | None) -> None: ...
	@property
	def timeSequenceIdentifier(self) -> Unsigned32 | None: ...
	@timeSequenceIdentifier.setter
	def timeSequenceIdentifier(self, value: Unsigned32 | int | None) -> None: ...
	undefined: None | None
	def __init__(
		self, /, *,
		timeOfDay: TimeOfDay = ...,
		timeSequenceIdentifier: Unsigned32 = ...,
		undefined: None = ...,
	) -> None: ...

class EC_State(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_disabled = 0
		V_idle = 1
		V_active = 2

	@property
	def value(self) -> EC_State.VALUES: ...
	@value.setter
	def value(self, value: EC_State.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class AlarmAckRule(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_none = 0
		V_simple = 1
		V_ack_active = 2
		V_ack_all = 3

	@property
	def value(self) -> AlarmAckRule.VALUES: ...
	@value.setter
	def value(self, value: AlarmAckRule.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class Transitions(_Asn1BitStrType):
	V_idle_to_disabled: bool # bit 0
	V_active_to_disabled: bool # bit 1
	V_disabled_to_idle: bool # bit 2
	V_active_to_idle: bool # bit 3
	V_disabled_to_active: bool # bit 4
	V_idle_to_active: bool # bit 5
	V_any_to_deleted: bool # bit 6


class EC_Class(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_network_triggered = 0
		V_monitored = 1

	@property
	def value(self) -> EC_Class.VALUES: ...
	@value.setter
	def value(self, value: EC_Class.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class EE_Class(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_modifier = 0
		V_notification = 1

	@property
	def value(self) -> EE_Class.VALUES: ...
	@value.setter
	def value(self, value: EE_Class.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class EE_Duration(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_current = 0
		V_permanent = 1

	@property
	def value(self) -> EE_Duration.VALUES: ...
	@value.setter
	def value(self, value: EE_Duration.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class Journal_Variable(_Asn1Type): # SEQUENCE
	@property
	def variableTag(self) -> MMS255String: ...
	@variableTag.setter
	def variableTag(self, value: MMS255String | str) -> None: ...
	valueSpecification: Data
	def __init__(
		self, /, *,
		variableTag: MMS255String = ...,
		valueSpecification: Data = ...,
	) -> None: ...

class Name(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_rdnSequence = 1

	@property
	def present(self) -> PRESENT: ...
	@property
	def rdnSequence(self) -> RDNSequence | None: ...
	@rdnSequence.setter
	def rdnSequence(self, value: RDNSequence | list | None) -> None: ...
	def __init__(
		self, /, *,
		rdnSequence: RDNSequence = ...,
	) -> None: ...

class DomainName(_Asn1BasicType[str]):
	pass

class RDNSequence(_Asn1Type):
	def __init__(self, values: EXT_Iterable[RelativeDistinguishedName] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> RelativeDistinguishedName: ...
	def __setitem__(self, index: int, value: RelativeDistinguishedName) -> None: ...
	def add(self, value: RelativeDistinguishedName) -> None: ...
	def extend(self, values: EXT_Iterable[RelativeDistinguishedName]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class RelativeDistinguishedName(_Asn1Type):
	def __init__(self, values: EXT_Iterable[AttributeTypeAndValue] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> AttributeTypeAndValue: ...
	def __setitem__(self, index: int, value: AttributeTypeAndValue) -> None: ...
	def add(self, value: AttributeTypeAndValue) -> None: ...
	def extend(self, values: EXT_Iterable[AttributeTypeAndValue]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class AttributeTypeAndValue(_Asn1Type): # SEQUENCE
	type: str
	value: bytes
	def __init__(
		self, /, *,
		type: str = ...,
		value: bytes = ...,
	) -> None: ...

class ACSE_apdu(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_aarq = 1
		PR_aare = 2
		PR_rlrq = 3
		PR_rlre = 4
		PR_abrt = 5

	@property
	def present(self) -> PRESENT: ...
	aarq: AARQ_apdu | None
	aare: AARE_apdu | None
	rlrq: RLRQ_apdu | None
	rlre: RLRE_apdu | None
	abrt: ABRT_apdu | None
	def __init__(
		self, /, *,
		aarq: AARQ_apdu = ...,
		aare: AARE_apdu = ...,
		rlrq: RLRQ_apdu = ...,
		rlre: RLRE_apdu = ...,
		abrt: ABRT_apdu = ...,
	) -> None: ...

class AARQ_apdu(_Asn1Type): # SEQUENCE

	class protocol_version_TYPE(_Asn1BitStrType):
		V_version1: bool # bit 0

	@property
	def protocol_version(self) -> protocol_version_TYPE | None: ...
	@protocol_version.setter
	def protocol_version(self, value: protocol_version_TYPE | EXT_bitarray | bytes | None) -> None: ...
	@property
	def application_context_name(self) -> Application_context_name: ...
	@application_context_name.setter
	def application_context_name(self, value: Application_context_name | str) -> None: ...
	called_AP_title: AP_title | None
	called_AE_qualifier: AE_qualifier | None
	@property
	def called_AP_invocation_identifier(self) -> AP_invocation_identifier | None: ...
	@called_AP_invocation_identifier.setter
	def called_AP_invocation_identifier(self, value: AP_invocation_identifier | int | None) -> None: ...
	@property
	def called_AE_invocation_identifier(self) -> AE_invocation_identifier | None: ...
	@called_AE_invocation_identifier.setter
	def called_AE_invocation_identifier(self, value: AE_invocation_identifier | int | None) -> None: ...
	calling_AP_title: AP_title | None
	calling_AE_qualifier: AE_qualifier | None
	@property
	def calling_AP_invocation_identifier(self) -> AP_invocation_identifier | None: ...
	@calling_AP_invocation_identifier.setter
	def calling_AP_invocation_identifier(self, value: AP_invocation_identifier | int | None) -> None: ...
	@property
	def calling_AE_invocation_identifier(self) -> AE_invocation_identifier | None: ...
	@calling_AE_invocation_identifier.setter
	def calling_AE_invocation_identifier(self, value: AE_invocation_identifier | int | None) -> None: ...
	@property
	def sender_acse_requirements(self) -> ACSE_requirements | None: ...
	@sender_acse_requirements.setter
	def sender_acse_requirements(self, value: ACSE_requirements | EXT_bitarray | int | bytes | None) -> None: ...
	@property
	def mechanism_name(self) -> Mechanism_name | None: ...
	@mechanism_name.setter
	def mechanism_name(self, value: Mechanism_name | str | None) -> None: ...
	calling_authentication_value: Authentication_value | None
	@property
	def application_context_name_list(self) -> Application_context_name_list | None: ...
	@application_context_name_list.setter
	def application_context_name_list(self, value: Application_context_name_list | list | None) -> None: ...
	@property
	def implementation_information(self) -> Implementation_data | None: ...
	@implementation_information.setter
	def implementation_information(self, value: Implementation_data | str | None) -> None: ...
	@property
	def user_information(self) -> Association_information | None: ...
	@user_information.setter
	def user_information(self, value: Association_information | list | None) -> None: ...
	def __init__(
		self, /, *,
		protocol_version: protocol_version_TYPE | EXT_bitarray | bytes = ...,
		application_context_name: Application_context_name = ...,
		called_AP_title: AP_title = ...,
		called_AE_qualifier: AE_qualifier = ...,
		called_AP_invocation_identifier: AP_invocation_identifier = ...,
		called_AE_invocation_identifier: AE_invocation_identifier = ...,
		calling_AP_title: AP_title = ...,
		calling_AE_qualifier: AE_qualifier = ...,
		calling_AP_invocation_identifier: AP_invocation_identifier = ...,
		calling_AE_invocation_identifier: AE_invocation_identifier = ...,
		sender_acse_requirements: ACSE_requirements = ...,
		mechanism_name: Mechanism_name = ...,
		calling_authentication_value: Authentication_value = ...,
		application_context_name_list: Application_context_name_list = ...,
		implementation_information: Implementation_data = ...,
		user_information: Association_information = ...,
	) -> None: ...

class AARE_apdu(_Asn1Type): # SEQUENCE

	class protocol_version_TYPE(_Asn1BitStrType):
		V_version1: bool # bit 0

	@property
	def protocol_version(self) -> protocol_version_TYPE | None: ...
	@protocol_version.setter
	def protocol_version(self, value: protocol_version_TYPE | EXT_bitarray | bytes | None) -> None: ...
	@property
	def application_context_name(self) -> Application_context_name: ...
	@application_context_name.setter
	def application_context_name(self, value: Application_context_name | str) -> None: ...
	@property
	def result(self) -> Associate_result: ...
	@result.setter
	def result(self, value: Associate_result | int) -> None: ...
	result_source_diagnostic: Associate_source_diagnostic
	responding_AP_title: AP_title | None
	responding_AE_qualifier: AE_qualifier | None
	@property
	def responding_AP_invocation_identifier(self) -> AP_invocation_identifier | None: ...
	@responding_AP_invocation_identifier.setter
	def responding_AP_invocation_identifier(self, value: AP_invocation_identifier | int | None) -> None: ...
	@property
	def responding_AE_invocation_identifier(self) -> AE_invocation_identifier | None: ...
	@responding_AE_invocation_identifier.setter
	def responding_AE_invocation_identifier(self, value: AE_invocation_identifier | int | None) -> None: ...
	@property
	def responder_acse_requirements(self) -> ACSE_requirements | None: ...
	@responder_acse_requirements.setter
	def responder_acse_requirements(self, value: ACSE_requirements | EXT_bitarray | int | bytes | None) -> None: ...
	@property
	def mechanism_name(self) -> Mechanism_name | None: ...
	@mechanism_name.setter
	def mechanism_name(self, value: Mechanism_name | str | None) -> None: ...
	responding_authentication_value: Authentication_value | None
	@property
	def application_context_name_list(self) -> Application_context_name_list | None: ...
	@application_context_name_list.setter
	def application_context_name_list(self, value: Application_context_name_list | list | None) -> None: ...
	@property
	def implementation_information(self) -> Implementation_data | None: ...
	@implementation_information.setter
	def implementation_information(self, value: Implementation_data | str | None) -> None: ...
	@property
	def user_information(self) -> Association_information | None: ...
	@user_information.setter
	def user_information(self, value: Association_information | list | None) -> None: ...
	def __init__(
		self, /, *,
		protocol_version: protocol_version_TYPE | EXT_bitarray | bytes = ...,
		application_context_name: Application_context_name = ...,
		result: Associate_result = ...,
		result_source_diagnostic: Associate_source_diagnostic = ...,
		responding_AP_title: AP_title = ...,
		responding_AE_qualifier: AE_qualifier = ...,
		responding_AP_invocation_identifier: AP_invocation_identifier = ...,
		responding_AE_invocation_identifier: AE_invocation_identifier = ...,
		responder_acse_requirements: ACSE_requirements = ...,
		mechanism_name: Mechanism_name = ...,
		responding_authentication_value: Authentication_value = ...,
		application_context_name_list: Application_context_name_list = ...,
		implementation_information: Implementation_data = ...,
		user_information: Association_information = ...,
	) -> None: ...

class RLRQ_apdu(_Asn1Type): # SEQUENCE
	@property
	def reason(self) -> Release_request_reason | None: ...
	@reason.setter
	def reason(self, value: Release_request_reason | int | None) -> None: ...
	@property
	def user_information(self) -> Association_information | None: ...
	@user_information.setter
	def user_information(self, value: Association_information | list | None) -> None: ...
	def __init__(
		self, /, *,
		reason: Release_request_reason = ...,
		user_information: Association_information = ...,
	) -> None: ...

class RLRE_apdu(_Asn1Type): # SEQUENCE
	@property
	def reason(self) -> Release_response_reason | None: ...
	@reason.setter
	def reason(self, value: Release_response_reason | int | None) -> None: ...
	@property
	def user_information(self) -> Association_information | None: ...
	@user_information.setter
	def user_information(self, value: Association_information | list | None) -> None: ...
	def __init__(
		self, /, *,
		reason: Release_response_reason = ...,
		user_information: Association_information = ...,
	) -> None: ...

class ABRT_apdu(_Asn1Type): # SEQUENCE
	@property
	def abort_source(self) -> ABRT_source: ...
	@abort_source.setter
	def abort_source(self, value: ABRT_source | int) -> None: ...
	abort_diagnostic: ABRT_diagnostic | None
	@property
	def user_information(self) -> Association_information | None: ...
	@user_information.setter
	def user_information(self, value: Association_information | list | None) -> None: ...
	def __init__(
		self, /, *,
		abort_source: ABRT_source = ...,
		abort_diagnostic: ABRT_diagnostic = ...,
		user_information: Association_information = ...,
	) -> None: ...

class ABRT_diagnostic(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_no_reason_given = 1
		V_protocol_error = 2
		V_authentication_mechanism_name_not_recognized = 3
		V_authentication_mechanism_name_required = 4
		V_authentication_failure = 5
		V_authentication_required = 6

	@property
	def value(self) -> ABRT_diagnostic.VALUES: ...
	@value.setter
	def value(self, value: ABRT_diagnostic.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class ABRT_source(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_acse_service_user = 0
		V_acse_service_provider = 1

	@property
	def value(self) -> ABRT_source.VALUES: ...
	@value.setter
	def value(self, value: ABRT_source.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class ACSE_requirements(_Asn1BitStrType):
	V_authentication: bool # bit 0
	V_application_context_negotiation: bool # bit 1


class Application_context_name_list(_Asn1Type):
	def __init__(self, values: EXT_Iterable[Application_context_name] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Application_context_name: ...
	def __setitem__(self, index: int, value: Application_context_name) -> None: ...
	def add(self, value: Application_context_name) -> None: ...
	def extend(self, values: EXT_Iterable[Application_context_name]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class Application_context_name(_Asn1BasicType[str]):
	pass

class AP_title(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_ap_title_form1 = 1
		PR_ap_title_form2 = 2

	@property
	def present(self) -> PRESENT: ...
	ap_title_form1: AP_title_form1 | None
	@property
	def ap_title_form2(self) -> AP_title_form2 | None: ...
	@ap_title_form2.setter
	def ap_title_form2(self, value: AP_title_form2 | str | None) -> None: ...
	def __init__(
		self, /, *,
		ap_title_form1: AP_title_form1 = ...,
		ap_title_form2: AP_title_form2 = ...,
	) -> None: ...

class AE_qualifier(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_ae_qualifier_form1 = 1
		PR_ae_qualifier_form2 = 2

	@property
	def present(self) -> PRESENT: ...
	ae_qualifier_form1: AE_qualifier_form1 | None
	@property
	def ae_qualifier_form2(self) -> AE_qualifier_form2 | None: ...
	@ae_qualifier_form2.setter
	def ae_qualifier_form2(self, value: AE_qualifier_form2 | int | None) -> None: ...
	def __init__(
		self, /, *,
		ae_qualifier_form1: AE_qualifier_form1 = ...,
		ae_qualifier_form2: AE_qualifier_form2 = ...,
	) -> None: ...

class AP_title_form1(_Asn1BasicType[Name]):
	pass

class AE_qualifier_form1(_Asn1BasicType[RelativeDistinguishedName]):
	pass

class AP_title_form2(_Asn1BasicType[str]):
	pass

class AE_qualifier_form2(_Asn1BasicType[int]):
	pass

class AE_title(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_ae_title_form1 = 1
		PR_ae_title_form2 = 2

	@property
	def present(self) -> PRESENT: ...
	ae_title_form1: AE_title_form1 | None
	@property
	def ae_title_form2(self) -> AE_title_form2 | None: ...
	@ae_title_form2.setter
	def ae_title_form2(self, value: AE_title_form2 | str | None) -> None: ...
	def __init__(
		self, /, *,
		ae_title_form1: AE_title_form1 = ...,
		ae_title_form2: AE_title_form2 = ...,
	) -> None: ...

class AE_title_form1(_Asn1BasicType[Name]):
	pass

class AE_title_form2(_Asn1BasicType[str]):
	pass

class AE_invocation_identifier(_Asn1BasicType[int]):
	pass

class AP_invocation_identifier(_Asn1BasicType[int]):
	pass

class Associate_result(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_accepted = 0
		V_rejected_permanent = 1
		V_rejected_transient = 2

	@property
	def value(self) -> Associate_result.VALUES: ...
	@value.setter
	def value(self, value: Associate_result.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class Associate_source_diagnostic(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_acse_service_user = 1
		PR_acse_service_provider = 2

	@property
	def present(self) -> PRESENT: ...

	class acse_service_user_VALUES(EXT_IntEnum):
		V_null = 0
		V_no_reason_given = 1
		V_application_context_name_not_supported = 2
		V_calling_AP_title_not_recognized = 3
		V_calling_AP_invocation_identifier_not_recognized = 4
		V_calling_AE_qualifier_not_recognized = 5
		V_calling_AE_invocation_identifier_not_recognized = 6
		V_called_AP_title_not_recognized = 7
		V_called_AP_invocation_identifier_not_recognized = 8
		V_called_AE_qualifier_not_recognized = 9
		V_called_AE_invocation_identifier_not_recognized = 10
		V_authentication_mechanism_name_not_recognized = 11
		V_authentication_mechanism_name_required = 12
		V_authentication_failure = 13
		V_authentication_required = 14

	acse_service_user: acse_service_user_VALUES | None

	class acse_service_provider_VALUES(EXT_IntEnum):
		V_null = 0
		V_no_reason_given = 1
		V_no_common_acse_version = 2

	acse_service_provider: acse_service_provider_VALUES | None
	def __init__(
		self, /, *,
		acse_service_user: acse_service_user_VALUES = ...,
		acse_service_provider: acse_service_provider_VALUES = ...,
	) -> None: ...

class Association_information(_Asn1Type):
	def __init__(self, values: EXT_Iterable[EXTERNAL] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> EXTERNAL: ...
	def __setitem__(self, index: int, value: EXTERNAL) -> None: ...
	def add(self, value: EXTERNAL) -> None: ...
	def extend(self, values: EXT_Iterable[EXTERNAL]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class Authentication_value(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_charstring = 1
		PR_bitstring = 2
		PR_external = 3
		PR_other = 4

	@property
	def present(self) -> PRESENT: ...

	class other_TYPE(_Asn1Type): # SEQUENCE
		@property
		def other_mechanism_name(self) -> Mechanism_name: ...
		@other_mechanism_name.setter
		def other_mechanism_name(self, value: Mechanism_name | str) -> None: ...
		other_mechanism_value: bytes
		def __init__(
			self, /, *,
			other_mechanism_name: Mechanism_name = ...,
			other_mechanism_value: bytes = ...,
		) -> None: ...

	other: other_TYPE
	charstring: str | None

	class bitstring_TYPE(_Asn1BitStrType):
		pass

	@property
	def bitstring(self) -> bitstring_TYPE | None: ...
	@bitstring.setter
	def bitstring(self, value: bitstring_TYPE | EXT_bitarray | bytes | None) -> None: ...
	external: EXTERNAL | None
	def __init__(
		self, /, *,
		charstring: str = ...,
		bitstring: bitstring_TYPE | EXT_bitarray | bytes = ...,
		external: EXTERNAL = ...,
		other: other_TYPE = ...,
	) -> None: ...

class Implementation_data(_Asn1BasicType[str]):
	pass

class Mechanism_name(_Asn1BasicType[str]):
	pass

class Release_request_reason(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_normal = 0
		V_urgent = 1
		V_user_defined = 30

	@property
	def value(self) -> Release_request_reason.VALUES: ...
	@value.setter
	def value(self, value: Release_request_reason.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class Release_response_reason(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_normal = 0
		V_not_finished = 1
		V_user_defined = 30

	@property
	def value(self) -> Release_response_reason.VALUES: ...
	@value.setter
	def value(self, value: Release_response_reason.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class EXTERNAL(_Asn1Type): # SEQUENCE

	class encoding_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_single_ASN1_type = 1
			PR_octet_aligned = 2
			PR_arbitrary = 3

		@property
		def present(self) -> PRESENT: ...
		single_ASN1_type: bytes | None
		octet_aligned: bytes | None

		class arbitrary_TYPE(_Asn1BitStrType):
			pass

		@property
		def arbitrary(self) -> arbitrary_TYPE | None: ...
		@arbitrary.setter
		def arbitrary(self, value: arbitrary_TYPE | EXT_bitarray | bytes | None) -> None: ...
		def __init__(
			self, /, *,
			single_ASN1_type: bytes = ...,
			octet_aligned: bytes = ...,
			arbitrary: arbitrary_TYPE | EXT_bitarray | bytes = ...,
		) -> None: ...

	encoding: encoding_TYPE
	direct_reference: str | None
	indirect_reference: int | None
	data_value_descriptor: str | None
	def __init__(
		self, /, *,
		direct_reference: str = ...,
		indirect_reference: int = ...,
		data_value_descriptor: str = ...,
		encoding: encoding_TYPE = ...,
	) -> None: ...

### END GENERATED CODE ###
