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

class MMSString(_Asn1BasicType[str]):
	pass

class FloatingPoint(_Asn1BasicType[bytes]):
	pass

class TimeOfDay(_Asn1BasicType[bytes]):
	pass

class IEC61850_Specific_Protocol(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_gseMngtPdu = 1
		PR_goosePdu = 2

	@property
	def present(self) -> PRESENT: ...
	gseMngtPdu: GSEMngtPdu | None
	goosePdu: IECGoosePdu | None
	def __init__(
		self, /, *,
		gseMngtPdu: GSEMngtPdu = ...,
		goosePdu: IECGoosePdu = ...,
	) -> None: ...

class GSEMngtPdu(_Asn1Type): # SEQUENCE
	stateID: int
	requestResp: GSERequestResponse
	def __init__(
		self, /, *,
		stateID: int = ...,
		requestResp: GSERequestResponse = ...,
	) -> None: ...

class GSERequestResponse(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_requests = 1
		PR_responses = 2

	@property
	def present(self) -> PRESENT: ...
	requests: GSEMngtRequests | None
	responses: GSEMngtResponses | None
	def __init__(
		self, /, *,
		requests: GSEMngtRequests = ...,
		responses: GSEMngtResponses = ...,
	) -> None: ...

class GSEMngtRequests(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_getGoReference = 1
		PR_getGOOSEElementNumber = 2
		PR_getGsReference = 3
		PR_getGSSEDataOffset = 4

	@property
	def present(self) -> PRESENT: ...
	getGoReference: GetReferenceRequestPdu | None
	getGOOSEElementNumber: GetElementRequestPdu | None
	getGsReference: GetReferenceRequestPdu | None
	getGSSEDataOffset: GetElementRequestPdu | None
	def __init__(
		self, /, *,
		getGoReference: GetReferenceRequestPdu = ...,
		getGOOSEElementNumber: GetElementRequestPdu = ...,
		getGsReference: GetReferenceRequestPdu = ...,
		getGSSEDataOffset: GetElementRequestPdu = ...,
	) -> None: ...

class GSEMngtResponses(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_gseMngtNotSupported = 1
		PR_getGoReference = 2
		PR_getGOOSEElementNumber = 3
		PR_getGsReference = 4
		PR_getGSSEDataOffset = 5

	@property
	def present(self) -> PRESENT: ...
	gseMngtNotSupported: None | None
	getGoReference: GSEMngtResponsePdu | None
	getGOOSEElementNumber: GSEMngtResponsePdu | None
	getGsReference: GSEMngtResponsePdu | None
	getGSSEDataOffset: GSEMngtResponsePdu | None
	def __init__(
		self, /, *,
		gseMngtNotSupported: None = ...,
		getGoReference: GSEMngtResponsePdu = ...,
		getGOOSEElementNumber: GSEMngtResponsePdu = ...,
		getGsReference: GSEMngtResponsePdu = ...,
		getGSSEDataOffset: GSEMngtResponsePdu = ...,
	) -> None: ...

class GetReferenceRequestPdu(_Asn1Type): # SEQUENCE

	class offset_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[int] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> int: ...
		def __setitem__(self, index: int, value: int) -> None: ...
		def add(self, value: int) -> None: ...
		def extend(self, values: EXT_Iterable[int]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	offset: offset_TYPE
	ident: str
	def __init__(
		self, /, *,
		ident: str = ...,
		offset: offset_TYPE = ...,
	) -> None: ...

class GetElementRequestPdu(_Asn1Type): # SEQUENCE

	class references_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[str] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> str: ...
		def __setitem__(self, index: int, value: str) -> None: ...
		def add(self, value: str) -> None: ...
		def extend(self, values: EXT_Iterable[str]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	references: references_TYPE
	ident: str
	def __init__(
		self, /, *,
		ident: str = ...,
		references: references_TYPE = ...,
	) -> None: ...

class GSEMngtResponsePdu(_Asn1Type): # SEQUENCE

	class positiveNegative_TYPE(_Asn1Type): # CHOICE
		class PRESENT(EXT_IntEnum):
			PR_NOTHING = 0
			PR_responsePositive = 1
			PR_responseNegative = 2

		@property
		def present(self) -> PRESENT: ...

		class responsePositive_TYPE(_Asn1Type): # SEQUENCE

			class result_TYPE(_Asn1Type):
				def __init__(self, values: EXT_Iterable[RequestResults] | None = ...) -> None: ...
				def __getitem__(self, index: int) -> RequestResults: ...
				def __setitem__(self, index: int, value: RequestResults) -> None: ...
				def add(self, value: RequestResults) -> None: ...
				def extend(self, values: EXT_Iterable[RequestResults]) -> None: ...
				def clear(self) -> None: ...
				def __len__(self) -> int: ...
				def __delitem__(self, index: int) -> None: ...

			result: result_TYPE
			datSet: str | None
			def __init__(
				self, /, *,
				datSet: str = ...,
				result: result_TYPE = ...,
			) -> None: ...

		responsePositive: responsePositive_TYPE
		@property
		def responseNegative(self) -> GlbErrors | None: ...
		@responseNegative.setter
		def responseNegative(self, value: GlbErrors | int | None) -> None: ...
		def __init__(
			self, /, *,
			responsePositive: responsePositive_TYPE = ...,
			responseNegative: GlbErrors = ...,
		) -> None: ...

	positiveNegative: positiveNegative_TYPE
	ident: str
	confRev: int | None
	def __init__(
		self, /, *,
		ident: str = ...,
		confRev: int = ...,
		positiveNegative: positiveNegative_TYPE = ...,
	) -> None: ...

class RequestResults(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_offset = 1
		PR_reference = 2
		PR_error = 3

	@property
	def present(self) -> PRESENT: ...
	offset: int | None
	reference: str | None
	@property
	def error(self) -> ErrorReason | None: ...
	@error.setter
	def error(self, value: ErrorReason | int | None) -> None: ...
	def __init__(
		self, /, *,
		offset: int = ...,
		reference: str = ...,
		error: ErrorReason = ...,
	) -> None: ...

class GlbErrors(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_other = 0
		V_unknownControlBlock = 1
		V_responseTooLarge = 2
		V_controlBlockConfigurationError = 3

	@property
	def value(self) -> GlbErrors.VALUES: ...
	@value.setter
	def value(self, value: GlbErrors.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class ErrorReason(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_other = 0
		V_notFound = 1

	@property
	def value(self) -> ErrorReason.VALUES: ...
	@value.setter
	def value(self, value: ErrorReason.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class IECGoosePdu(_Asn1Type): # SEQUENCE

	class allData_TYPE(_Asn1Type):
		def __init__(self, values: EXT_Iterable[Data] | None = ...) -> None: ...
		def __getitem__(self, index: int) -> Data: ...
		def __setitem__(self, index: int, value: Data) -> None: ...
		def add(self, value: Data) -> None: ...
		def extend(self, values: EXT_Iterable[Data]) -> None: ...
		def clear(self) -> None: ...
		def __len__(self) -> int: ...
		def __delitem__(self, index: int) -> None: ...

	allData: allData_TYPE
	gocbRef: str
	timeAllowedtoLive: int
	datSet: str
	goID: str | None
	time: bytes
	stNum: int
	sqNum: int
	simulation: bool | None
	confRev: int
	ndsCom: bool | None
	numDatSetEntries: int
	def __init__(
		self, /, *,
		gocbRef: str = ...,
		timeAllowedtoLive: int = ...,
		datSet: str = ...,
		goID: str = ...,
		time: bytes = ...,
		stNum: int = ...,
		sqNum: int = ...,
		simulation: bool = ...,
		confRev: int = ...,
		ndsCom: bool = ...,
		numDatSetEntries: int = ...,
		allData: allData_TYPE = ...,
	) -> None: ...

class UtcTime(_Asn1BasicType[bytes]):
	pass

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
