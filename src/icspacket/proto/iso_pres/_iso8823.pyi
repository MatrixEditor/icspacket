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
    def xer_decode(
        cls: type[_ASN_T], data: bytes, /, *, canonical: bool = ...
    ) -> _ASN_T: ...
    def jer_encode(self, /, *, minified: bool = ...) -> bytes: ...
    @classmethod
    def jer_decode(
        cls: type[_ASN_T], data: bytes, /, *, minified: bool = ...
    ) -> _ASN_T: ...
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

# fmt: off
### BEGIN GENERATED CODE ###
class CP_type(_Asn1Type): # SET

	class normal_mode_parameters_TYPE(_Asn1Type): # SEQUENCE
		@property
		def protocol_version(self) -> Protocol_version | None: ...
		@protocol_version.setter
		def protocol_version(self, value: Protocol_version | EXT_bitarray | int | bytes | None) -> None: ...
		calling_presentation_selector: Calling_presentation_selector | None
		called_presentation_selector: Called_presentation_selector | None
		presentation_context_definition_list: Presentation_context_definition_list | None
		default_context_name: Default_context_name | None
		@property
		def presentation_requirements(self) -> Presentation_requirements | None: ...
		@presentation_requirements.setter
		def presentation_requirements(self, value: Presentation_requirements | EXT_bitarray | int | bytes | None) -> None: ...
		@property
		def user_session_requirements(self) -> User_session_requirements | None: ...
		@user_session_requirements.setter
		def user_session_requirements(self, value: User_session_requirements | EXT_bitarray | int | bytes | None) -> None: ...
		@property
		def protocol_options(self) -> Protocol_options | None: ...
		@protocol_options.setter
		def protocol_options(self, value: Protocol_options | EXT_bitarray | int | bytes | None) -> None: ...
		@property
		def initiators_nominated_context(self) -> Presentation_context_identifier | None: ...
		@initiators_nominated_context.setter
		def initiators_nominated_context(self, value: Presentation_context_identifier | int | None) -> None: ...
		user_data: User_data | None
		def __init__(
			self, /, *,
			protocol_version: Protocol_version = ...,
			calling_presentation_selector: Calling_presentation_selector = ...,
			called_presentation_selector: Called_presentation_selector = ...,
			presentation_context_definition_list: Presentation_context_definition_list = ...,
			default_context_name: Default_context_name = ...,
			presentation_requirements: Presentation_requirements = ...,
			user_session_requirements: User_session_requirements = ...,
			protocol_options: Protocol_options = ...,
			initiators_nominated_context: Presentation_context_identifier = ...,
			user_data: User_data = ...,
		) -> None: ...

	normal_mode_parameters: normal_mode_parameters_TYPE | None
	mode_selector: Mode_selector
	def __init__(
		self, /, *,
		mode_selector: Mode_selector = ...,
		normal_mode_parameters: normal_mode_parameters_TYPE = ...,
	) -> None: ...

class CPC_type(_Asn1BasicType[User_data]):
	pass

class CPA_PPDU(_Asn1Type): # SET

	class normal_mode_parameters_TYPE(_Asn1Type): # SEQUENCE
		@property
		def protocol_version(self) -> Protocol_version | None: ...
		@protocol_version.setter
		def protocol_version(self, value: Protocol_version | EXT_bitarray | int | bytes | None) -> None: ...
		responding_presentation_selector: Responding_presentation_selector | None
		presentation_context_definition_result_list: Presentation_context_definition_result_list | None
		@property
		def presentation_requirements(self) -> Presentation_requirements | None: ...
		@presentation_requirements.setter
		def presentation_requirements(self, value: Presentation_requirements | EXT_bitarray | int | bytes | None) -> None: ...
		@property
		def user_session_requirements(self) -> User_session_requirements | None: ...
		@user_session_requirements.setter
		def user_session_requirements(self, value: User_session_requirements | EXT_bitarray | int | bytes | None) -> None: ...
		@property
		def protocol_options(self) -> Protocol_options | None: ...
		@protocol_options.setter
		def protocol_options(self, value: Protocol_options | EXT_bitarray | int | bytes | None) -> None: ...
		@property
		def responders_nominated_context(self) -> Presentation_context_identifier | None: ...
		@responders_nominated_context.setter
		def responders_nominated_context(self, value: Presentation_context_identifier | int | None) -> None: ...
		user_data: User_data | None
		def __init__(
			self, /, *,
			protocol_version: Protocol_version = ...,
			responding_presentation_selector: Responding_presentation_selector = ...,
			presentation_context_definition_result_list: Presentation_context_definition_result_list = ...,
			presentation_requirements: Presentation_requirements = ...,
			user_session_requirements: User_session_requirements = ...,
			protocol_options: Protocol_options = ...,
			responders_nominated_context: Presentation_context_identifier = ...,
			user_data: User_data = ...,
		) -> None: ...

	normal_mode_parameters: normal_mode_parameters_TYPE | None
	mode_selector: Mode_selector
	def __init__(
		self, /, *,
		mode_selector: Mode_selector = ...,
		normal_mode_parameters: normal_mode_parameters_TYPE = ...,
	) -> None: ...

class CPR_PPDU(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_normal_mode_parameters = 1

	@property
	def present(self) -> PRESENT: ...

	class normal_mode_parameters_TYPE(_Asn1Type): # SEQUENCE
		@property
		def protocol_version(self) -> Protocol_version | None: ...
		@protocol_version.setter
		def protocol_version(self, value: Protocol_version | EXT_bitarray | int | bytes | None) -> None: ...
		responding_presentation_selector: Responding_presentation_selector | None
		presentation_context_definition_result_list: Presentation_context_definition_result_list | None
		default_context_result: Default_context_result | None
		@property
		def provider_reason(self) -> Provider_reason | None: ...
		@provider_reason.setter
		def provider_reason(self, value: Provider_reason | int | None) -> None: ...
		user_data: User_data | None
		def __init__(
			self, /, *,
			protocol_version: Protocol_version = ...,
			responding_presentation_selector: Responding_presentation_selector = ...,
			presentation_context_definition_result_list: Presentation_context_definition_result_list = ...,
			default_context_result: Default_context_result = ...,
			provider_reason: Provider_reason = ...,
			user_data: User_data = ...,
		) -> None: ...

	normal_mode_parameters: normal_mode_parameters_TYPE
	def __init__(
		self, /, *,
		normal_mode_parameters: normal_mode_parameters_TYPE = ...,
	) -> None: ...

class Abort_type(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_aru_ppdu = 1
		PR_arp_ppdu = 2

	@property
	def present(self) -> PRESENT: ...
	aru_ppdu: ARU_PPDU | None
	arp_ppdu: ARP_PPDU | None
	def __init__(
		self, /, *,
		aru_ppdu: ARU_PPDU = ...,
		arp_ppdu: ARP_PPDU = ...,
	) -> None: ...

class ARU_PPDU(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_normal_mode_parameters = 1

	@property
	def present(self) -> PRESENT: ...

	class normal_mode_parameters_TYPE(_Asn1Type): # SEQUENCE
		@property
		def presentation_context_identifier_list(self) -> Presentation_context_identifier_list | None: ...
		@presentation_context_identifier_list.setter
		def presentation_context_identifier_list(self, value: Presentation_context_identifier_list | list | None) -> None: ...
		user_data: User_data | None
		def __init__(
			self, /, *,
			presentation_context_identifier_list: Presentation_context_identifier_list = ...,
			user_data: User_data = ...,
		) -> None: ...

	normal_mode_parameters: normal_mode_parameters_TYPE
	def __init__(
		self, /, *,
		normal_mode_parameters: normal_mode_parameters_TYPE = ...,
	) -> None: ...

class ARP_PPDU(_Asn1Type): # SEQUENCE
	@property
	def provider_reason(self) -> Abort_reason | None: ...
	@provider_reason.setter
	def provider_reason(self, value: Abort_reason | int | None) -> None: ...
	@property
	def event_identifier(self) -> Event_identifier | None: ...
	@event_identifier.setter
	def event_identifier(self, value: Event_identifier | int | None) -> None: ...
	def __init__(
		self, /, *,
		provider_reason: Abort_reason = ...,
		event_identifier: Event_identifier = ...,
	) -> None: ...

class Typed_data_type(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_acPPDU = 1
		PR_acaPPDU = 2
		PR_ttdPPDU = 3

	@property
	def present(self) -> PRESENT: ...
	acPPDU: AC_PPDU | None
	acaPPDU: ACA_PPDU | None
	ttdPPDU: User_data | None
	def __init__(
		self, /, *,
		acPPDU: AC_PPDU = ...,
		acaPPDU: ACA_PPDU = ...,
		ttdPPDU: User_data = ...,
	) -> None: ...

class AC_PPDU(_Asn1Type): # SEQUENCE
	presentation_context_addition_list: Presentation_context_addition_list | None
	@property
	def presentation_context_deletion_list(self) -> Presentation_context_deletion_list | None: ...
	@presentation_context_deletion_list.setter
	def presentation_context_deletion_list(self, value: Presentation_context_deletion_list | list | None) -> None: ...
	user_data: User_data | None
	def __init__(
		self, /, *,
		presentation_context_addition_list: Presentation_context_addition_list = ...,
		presentation_context_deletion_list: Presentation_context_deletion_list = ...,
		user_data: User_data = ...,
	) -> None: ...

class ACA_PPDU(_Asn1Type): # SEQUENCE
	presentation_context_addition_result_list: Presentation_context_addition_result_list | None
	@property
	def presentation_context_deletion_result_list(self) -> Presentation_context_deletion_result_list | None: ...
	@presentation_context_deletion_result_list.setter
	def presentation_context_deletion_result_list(self, value: Presentation_context_deletion_result_list | list | None) -> None: ...
	user_data: User_data | None
	def __init__(
		self, /, *,
		presentation_context_addition_result_list: Presentation_context_addition_result_list = ...,
		presentation_context_deletion_result_list: Presentation_context_deletion_result_list = ...,
		user_data: User_data = ...,
	) -> None: ...

class RS_PPDU(_Asn1Type): # SEQUENCE
	@property
	def presentation_context_identifier_list(self) -> Presentation_context_identifier_list | None: ...
	@presentation_context_identifier_list.setter
	def presentation_context_identifier_list(self, value: Presentation_context_identifier_list | list | None) -> None: ...
	user_data: User_data | None
	def __init__(
		self, /, *,
		presentation_context_identifier_list: Presentation_context_identifier_list = ...,
		user_data: User_data = ...,
	) -> None: ...

class RSA_PPDU(_Asn1Type): # SEQUENCE
	@property
	def presentation_context_identifier_list(self) -> Presentation_context_identifier_list | None: ...
	@presentation_context_identifier_list.setter
	def presentation_context_identifier_list(self, value: Presentation_context_identifier_list | list | None) -> None: ...
	user_data: User_data | None
	def __init__(
		self, /, *,
		presentation_context_identifier_list: Presentation_context_identifier_list = ...,
		user_data: User_data = ...,
	) -> None: ...

class Abort_reason(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_reason_not_specified = 0
		V_unrecognized_ppdu = 1
		V_unexpected_ppdu = 2
		V_unexpected_session_service_primitive = 3
		V_unrecognized_ppdu_parameter = 4
		V_unexpected_ppdu_parameter = 5
		V_invalid_ppdu_parameter_value = 6

	@property
	def value(self) -> Abort_reason.VALUES: ...
	@value.setter
	def value(self, value: Abort_reason.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class Abstract_syntax_name(_Asn1BasicType[str]):
	pass

class Called_presentation_selector(_Asn1BasicType[Presentation_selector]):
	pass

class Calling_presentation_selector(_Asn1BasicType[Presentation_selector]):
	pass

class Context_list(_Asn1Type):

	class Member_TYPE(_Asn1Type): # SEQUENCE

		class transfer_syntax_name_list_TYPE(_Asn1Type):
			def __init__(self, values: EXT_Iterable[Transfer_syntax_name] | None = ...) -> None: ...
			def __getitem__(self, index: int) -> Transfer_syntax_name: ...
			def __setitem__(self, index: int, value: Transfer_syntax_name) -> None: ...
			def add(self, value: Transfer_syntax_name) -> None: ...
			def extend(self, values: EXT_Iterable[Transfer_syntax_name]) -> None: ...
			def clear(self) -> None: ...
			def __len__(self) -> int: ...
			def __delitem__(self, index: int) -> None: ...

		transfer_syntax_name_list: transfer_syntax_name_list_TYPE
		@property
		def presentation_context_identifier(self) -> Presentation_context_identifier: ...
		@presentation_context_identifier.setter
		def presentation_context_identifier(self, value: Presentation_context_identifier | int) -> None: ...
		@property
		def abstract_syntax_name(self) -> Abstract_syntax_name: ...
		@abstract_syntax_name.setter
		def abstract_syntax_name(self, value: Abstract_syntax_name | str) -> None: ...
		def __init__(
			self, /, *,
			presentation_context_identifier: Presentation_context_identifier = ...,
			abstract_syntax_name: Abstract_syntax_name = ...,
			transfer_syntax_name_list: transfer_syntax_name_list_TYPE = ...,
		) -> None: ...

	def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Member_TYPE: ...
	def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
	def add(self, value: Member_TYPE) -> None: ...
	def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class Default_context_name(_Asn1Type): # SEQUENCE
	@property
	def abstract_syntax_name(self) -> Abstract_syntax_name: ...
	@abstract_syntax_name.setter
	def abstract_syntax_name(self, value: Abstract_syntax_name | str) -> None: ...
	@property
	def transfer_syntax_name(self) -> Transfer_syntax_name: ...
	@transfer_syntax_name.setter
	def transfer_syntax_name(self, value: Transfer_syntax_name | str) -> None: ...
	def __init__(
		self, /, *,
		abstract_syntax_name: Abstract_syntax_name = ...,
		transfer_syntax_name: Transfer_syntax_name = ...,
	) -> None: ...

class Default_context_result(_Asn1BasicType[Result]):
	pass

class Event_identifier(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_cp_PPDU = 0
		V_cpa_PPDU = 1
		V_cpr_PPDU = 2
		V_aru_PPDU = 3
		V_arp_PPDU = 4
		V_ac_PPDU = 5
		V_aca_PPDU = 6
		V_td_PPDU = 7
		V_ttd_PPDU = 8
		V_te_PPDU = 9
		V_tc_PPDU = 10
		V_tcc_PPDU = 11
		V_rs_PPDU = 12
		V_rsa_PPDU = 13
		V_s_release_indication = 14
		V_s_release_confirm = 15
		V_s_token_give_indication = 16
		V_s_token_please_indication = 17
		V_s_control_give_indication = 18
		V_s_sync_minor_indication = 19
		V_s_sync_minor_confirm = 20
		V_s_sync_major_indication = 21
		V_s_sync_major_confirm = 22
		V_s_p_exception_report_indication = 23
		V_s_u_exception_report_indication = 24
		V_s_activity_start_indication = 25
		V_s_activity_resume_indication = 26
		V_s_activity_interrupt_indication = 27
		V_s_activity_interrupt_confirm = 28
		V_s_activity_discard_indication = 29
		V_s_activity_discard_confirm = 30
		V_s_activity_end_indication = 31
		V_s_activity_end_confirm = 32

	@property
	def value(self) -> Event_identifier.VALUES: ...
	@value.setter
	def value(self, value: Event_identifier.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class Mode_selector(_Asn1Type): # SET

	class mode_value_VALUES(EXT_IntEnum):
		V_x410_1984_mode = 0
		V_normal_mode = 1

	mode_value: mode_value_VALUES
	def __init__(
		self, /, *,
		mode_value: mode_value_VALUES = ...,
	) -> None: ...

class Presentation_context_addition_list(_Asn1BasicType[Context_list]):
	pass

class Presentation_context_addition_result_list(_Asn1BasicType[Result_list]):
	pass

class Presentation_context_definition_list(_Asn1BasicType[Context_list]):
	pass

class Presentation_context_definition_result_list(_Asn1BasicType[Result_list]):
	pass

class Presentation_context_deletion_list(_Asn1Type):
	def __init__(self, values: EXT_Iterable[Presentation_context_identifier] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Presentation_context_identifier: ...
	def __setitem__(self, index: int, value: Presentation_context_identifier) -> None: ...
	def add(self, value: Presentation_context_identifier) -> None: ...
	def extend(self, values: EXT_Iterable[Presentation_context_identifier]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class Presentation_context_deletion_result_list(_Asn1Type):

	class Member_VALUES(EXT_IntEnum):
		V_acceptance = 0
		V_user_rejection = 1

	def __init__(self, values: EXT_Iterable[Member_VALUES] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Member_VALUES: ...
	def __setitem__(self, index: int, value: Member_VALUES) -> None: ...
	def add(self, value: Member_VALUES) -> None: ...
	def extend(self, values: EXT_Iterable[Member_VALUES]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class Presentation_context_identifier(_Asn1BasicType[int]):
	pass

class Presentation_context_identifier_list(_Asn1Type):

	class Member_TYPE(_Asn1Type): # SEQUENCE
		@property
		def presentation_context_identifier(self) -> Presentation_context_identifier: ...
		@presentation_context_identifier.setter
		def presentation_context_identifier(self, value: Presentation_context_identifier | int) -> None: ...
		@property
		def transfer_syntax_name(self) -> Transfer_syntax_name: ...
		@transfer_syntax_name.setter
		def transfer_syntax_name(self, value: Transfer_syntax_name | str) -> None: ...
		def __init__(
			self, /, *,
			presentation_context_identifier: Presentation_context_identifier = ...,
			transfer_syntax_name: Transfer_syntax_name = ...,
		) -> None: ...

	def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Member_TYPE: ...
	def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
	def add(self, value: Member_TYPE) -> None: ...
	def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class Presentation_requirements(_Asn1BitStrType):
	V_context_management: bool # bit 0
	V_restoration: bool # bit 1


class Presentation_selector(_Asn1BasicType[bytes]):
	pass

class Protocol_options(_Asn1BitStrType):
	V_nominated_context: bool # bit 0
	V_short_encoding: bool # bit 1
	V_packed_encoding_rules: bool # bit 2


class Protocol_version(_Asn1BitStrType):
	V_version_1: bool # bit 0


class Provider_reason(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_reason_not_specified = 0
		V_temporary_congestion = 1
		V_local_limit_exceeded = 2
		V_called_presentation_address_unknown = 3
		V_protocol_version_not_supported = 4
		V_default_context_not_supported = 5
		V_user_data_not_readable = 6
		V_no_PSAP_available = 7

	@property
	def value(self) -> Provider_reason.VALUES: ...
	@value.setter
	def value(self, value: Provider_reason.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class Responding_presentation_selector(_Asn1BasicType[Presentation_selector]):
	pass

class Result(_Asn1Type):
	class VALUES(EXT_IntEnum):
		V_acceptance = 0
		V_user_rejection = 1
		V_provider_rejection = 2

	@property
	def value(self) -> Result.VALUES: ...
	@value.setter
	def value(self, value: Result.VALUES | int) -> None: ...
	def __init__(self, value: VALUES = ...) -> None: ...

class Result_list(_Asn1Type):

	class Member_TYPE(_Asn1Type): # SEQUENCE
		@property
		def result(self) -> Result: ...
		@result.setter
		def result(self, value: Result | int) -> None: ...
		@property
		def transfer_syntax_name(self) -> Transfer_syntax_name | None: ...
		@transfer_syntax_name.setter
		def transfer_syntax_name(self, value: Transfer_syntax_name | str | None) -> None: ...

		class provider_reason_VALUES(EXT_IntEnum):
			V_reason_not_specified = 0
			V_abstract_syntax_not_supported = 1
			V_proposed_transfer_syntaxes_not_supported = 2
			V_local_limit_on_DCS_exceeded = 3

		provider_reason: provider_reason_VALUES | None
		def __init__(
			self, /, *,
			result: Result = ...,
			transfer_syntax_name: Transfer_syntax_name = ...,
			provider_reason: provider_reason_VALUES = ...,
		) -> None: ...

	def __init__(self, values: EXT_Iterable[Member_TYPE] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> Member_TYPE: ...
	def __setitem__(self, index: int, value: Member_TYPE) -> None: ...
	def add(self, value: Member_TYPE) -> None: ...
	def extend(self, values: EXT_Iterable[Member_TYPE]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class Transfer_syntax_name(_Asn1BasicType[str]):
	pass

class User_data(_Asn1Type): # CHOICE
	class PRESENT(EXT_IntEnum):
		PR_NOTHING = 0
		PR_simply_encoded_data = 1
		PR_fully_encoded_data = 2

	@property
	def present(self) -> PRESENT: ...
	@property
	def simply_encoded_data(self) -> Simply_encoded_data | None: ...
	@simply_encoded_data.setter
	def simply_encoded_data(self, value: Simply_encoded_data | bytes | None) -> None: ...
	@property
	def fully_encoded_data(self) -> Fully_encoded_data | None: ...
	@fully_encoded_data.setter
	def fully_encoded_data(self, value: Fully_encoded_data | list | None) -> None: ...
	def __init__(
		self, /, *,
		simply_encoded_data: Simply_encoded_data = ...,
		fully_encoded_data: Fully_encoded_data = ...,
	) -> None: ...

class Simply_encoded_data(_Asn1BasicType[bytes]):
	pass

class Fully_encoded_data(_Asn1Type):
	def __init__(self, values: EXT_Iterable[PDV_list] | None = ...) -> None: ...
	def __getitem__(self, index: int) -> PDV_list: ...
	def __setitem__(self, index: int, value: PDV_list) -> None: ...
	def add(self, value: PDV_list) -> None: ...
	def extend(self, values: EXT_Iterable[PDV_list]) -> None: ...
	def clear(self) -> None: ...
	def __len__(self) -> int: ...
	def __delitem__(self, index: int) -> None: ...

class PDV_list(_Asn1Type): # SEQUENCE

	class presentation_data_values_TYPE(_Asn1Type): # CHOICE
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

	presentation_data_values: presentation_data_values_TYPE
	@property
	def transfer_syntax_name(self) -> Transfer_syntax_name | None: ...
	@transfer_syntax_name.setter
	def transfer_syntax_name(self, value: Transfer_syntax_name | str | None) -> None: ...
	@property
	def presentation_context_identifier(self) -> Presentation_context_identifier: ...
	@presentation_context_identifier.setter
	def presentation_context_identifier(self, value: Presentation_context_identifier | int) -> None: ...
	def __init__(
		self, /, *,
		transfer_syntax_name: Transfer_syntax_name = ...,
		presentation_context_identifier: Presentation_context_identifier = ...,
		presentation_data_values: presentation_data_values_TYPE = ...,
	) -> None: ...

class User_session_requirements(_Asn1BitStrType):
	V_half_duplex: bool # bit 0
	V_duplex: bool # bit 1
	V_expedited_data: bool # bit 2
	V_minor_synchronize: bool # bit 3
	V_major_synchronize: bool # bit 4
	V_resynchronize: bool # bit 5
	V_activity_management: bool # bit 6
	V_negotiated_release: bool # bit 7
	V_capability_data: bool # bit 8
	V_exceptions: bool # bit 9
	V_typed_data: bool # bit 10
	V_symmetric_synchronize: bool # bit 11
	V_data_separation: bool # bit 12


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
# fmt: on
