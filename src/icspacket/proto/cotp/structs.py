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
# pyright: reportInvalidTypeForm=false, reportGeneralTypeIssues=false, reportAssignmentType=false


# [ITU X.224] - Open Systems Interconnection – Connection-mode protocol
# specifications

from collections.abc import Iterable
import enum

from caterpillar.context import CTX_OBJECT
from caterpillar.model import bitfield, EnumFactory, struct
from caterpillar.options import S_ADD_BYTES
from caterpillar.shared import Action
from caterpillar.shortcuts import F, BigEndian, opt, pack, this, unpack
from caterpillar.fields import (
    DEFAULT_OPTION,
    Bytes,
    Enum,
    Prefixed,
    uint32,
    uint8,
    uint16,
    ENUM_STRICT,
)


def checksum(tpdu_data: Iterable[int], checksum_off: int):
    """
    Compute the checksum for a TPDU according to Annex D.3 of X.224.

    The algorithm iterates through each octet, maintaining two
    accumulators ``C0`` and ``C1``. After processing, the two checksum
    octets ``X`` and ``Y`` are computed based on the position of the
    checksum parameter and the total TPDU length.

    **Algorithm (Annex D.3):**
      1. Initialize ``C0 = 0`` and ``C1 = 0``.
      2. For each octet in the TPDU, add its value to ``C0`` and then
         add the new ``C0`` to ``C1``.
      3. Compute the checksum values:
         - ``X = (-C1 + (L - n) * C0) mod 256``
         - ``Y = (C1 - (L - n + 1) * C0) mod 256``

    :param tpdu_data: Sequence of TPDU octets.
    :type tpdu_data: Iterable[int]
    :param checksum_off: Offset where the two checksum octets reside.
    :type checksum_off: int
    :return: Two-byte checksum value (X, Y).
    :rtype: bytes
    """

    # is the length of the complete TPDU;
    octets = list(tpdu_data)
    L = len(octets)
    n = checksum_off

    # D.3.2 Initialize C0 and C1 to zero.
    c0 = c1 = 0
    # D.3.3 Process each octet sequentially from i = 1 to L by:
    for byte in tpdu_data:
        # a) adding the value of the octet to C0; then
        c0 = (c0 + byte) & 0xFF
        # b) adding the value of C0 to C1.
        c1 = (c0 + c1) & 0xFF

    # Calculate X and Y
    x = (-c1 + (L - n) * c0) & 0xFF
    y = (c1 - (L - n + 1) * c0) & 0xFF
    return bytes([x, y])


def verify_checksum(tpdu_data: bytes, checksum_off: int) -> bool:
    """
    Verify the checksum of a TPDU.

    The function temporarily zeroes out the checksum field and recomputes
    it using :func:`checksum`. If the recomputed checksum matches the
    original octets at the checksum offset, the TPDU is considered valid.

    :param tpdu_data: The TPDU octets containing a checksum field.
    :type tpdu_data: bytes
    :param checksum_off: Offset to the start of the checksum field.
    :type checksum_off: int
    :return: ``True`` if checksum matches, ``False`` otherwise.
    :rtype: bool
    """
    data = bytearray(tpdu_data)
    data[checksum_off] = 0
    data[checksum_off + 1] = 0
    return checksum(data, checksum_off) == tpdu_data[checksum_off : checksum_off + 2]


class TPDU_Code(enum.IntEnum):
    """13.2.2.2 TPDU code"""

    ED = 0x01  # Expected Data
    EA = 0x02  # Expedited data acknowledgement
    RJ = 0x03  # Reject
    AK = 0x06  # Data acknowledgement
    ER = 0x07  # Error
    DR = 0x08  # Disconnect request
    DC = 0x0C  # Disconnect confirmation
    CC = 0x0D  # Connection confirmation
    CR = 0x0E  # Connection request
    DT = 0x0F  # Data


class TPDU_Class(enum.IntEnum):
    """7. Protocol classes"""

    CLASS0 = 0
    """8. Simple class (Class 0)

    Class 0 provides only the functions needed for connection establishment with
    negotiation, data transfer with segmenting and protocol error reporting.
    """

    CLASS1 = 1
    """9. Basic error recovery class (Class 1)

    Class 1 provides transport connections with flow control based on the
    network service provided flow control, error recovery, expedited data
    transfer, disconnection, and also the ability to support consecutive
    transport connections on a network connection.
    """

    CLASS2 = 2
    """10. Multiplexing class (Class 2)

    Class 2 provides transport connections with or without individual flow
    control; no error detection or error recovery is provided.
    """

    CLASS3 = 3
    """11. Error recovery and multiplexing class

    Class 3 provides the functionality of class 2 (with use of explicit flow
    control) plus the ability to recover after a failure signalled by the
    Network Layer without involving the TS-user.
    """

    CLASS4 = 4
    """12. Error detection and recovery class (Class 4)

    Class 4 provides the functionality of class 3, plus the ability to detect
    and recover from lost, duplicated, or out of sequence TPDUs without
    involving the TS-user.
    """


class TPDU_DisconnectReason(enum.IntEnum):
    """Defines the reason for disconnecting the transport connection."""

    __struct__ = uint8

    NORMAL = 128 + 0
    """Normal disconnect initiated by session entity."""

    REMOTE_CONGEST = 128 + 1
    """Remote transport entity congestion at connect request time."""

    NEGO_FAILED = 128 + 2
    """Connection negotiation failed [i.e. proposed class(es) not supported]."""

    DUPLICATE_SOURCE = 128 + 3
    """Duplicate source reference detected for the same pair of NSAPs."""

    MISMATCHED_REFERENCES = 128 + 4
    """Mismatched references."""

    PROTOCOL_ERROR = 128 + 5
    """Protocol error."""

    REF_OVERFLOW = 128 + 7
    """Reference overflow."""

    CONN_REFUSED = 128 + 8
    """Connection request refused on this network connection."""

    INVALID_LENGTH = 128 + 10
    """Header or parameter length invalid."""

    # available for all classes
    UNSPECIFIED = 0
    """Reason not specified."""

    TSAP_CONGESTION = 1
    """Congestion at TSAP."""

    ENTITIY_NOT_ATTACHED = 2
    """Session entity not attached to TSAP."""

    UNKNOWN_ADDRESS = 3
    """Address unknown."""


class TPDU_Size(enum.IntEnum):
    """
    Defines the proposed maximum TPDU size (in octets including the header) to
    be used over the requested transport connection
    """

    # fmt: off
    SIZE_8192 = 0b00001101  # 8192 octets (not allowed in class 0)
    SIZE_4096 = 0b00001100  # 4096 octets
    SIZE_2048 = 0b00001011  # 2048 octets
    SIZE_1024 = 0b00001010  # 1024 octets
    SIZE_512  = 0b00001001  # 512 octets
    SIZE_256  = 0b00001000  # 256 octets
    SIZE_128  = 0b00000111  # 128 octets
    # fmt: on


class TPDU_RejectCause(enum.IntEnum):
    """Cause of rejection of a connection request"""

    __struct__ = uint8

    UNSPECIFIED = 0
    """Cause not specified"""

    INVALID_PARAMETER_CODE = 1
    """Invalid parameter code"""

    INVALID_PDU_TYPE = 2
    """Invalid PDU type"""

    INVALID_PARAMETER_VALUE = 3
    """Invalid parameter value"""


@bitfield(options=[opt.S_ADD_BYTES])
class TPDU_AdditionalOptions:
    """Additional option selection (not used if class 0 is the preferred
    class)"""

    # fmt: off
    unused                 : 1 = False
    non_blocking           : 1 = False
    """Use of non-blocking expedited data in class 4"""

    use_request_ack        : 1 = False
    """Use of request acknowledgement in class 1, 3, 4"""

    use_selective_ack      : 1 = False
    """Use of selective acknowledgement in class 4"""

    speed_up               : 1 = False
    """Use of network expedited in class 1"""

    use_receipt_info       : 1 = False
    """
    - True: Use of receipt confirmation in class 1
    - False: Use of explicit AK variant in class 1
    """

    use_checksum_16bit     : 1 = False
    """16-bit checksum defined in 6.17 shall be used in class 4"""

    use_transport_speed_up : 1 = True
    """Use of transport expedited data transfer service"""
    # fmt: on


@struct(order=BigEndian, options=[S_ADD_BYTES])
class TPDU_TransitDelay:
    """Transit delay (not used if class 0 is the preferred class)"""

    # fmt: off
    calling_target_value        : uint16    = 0
    """target value, calling-called user direction;"""

    calling_maximum_acceptable  : uint16    = 0
    """maximum acceptable, calling-called user direction;"""

    called_target_value         : uint16    = 0
    """target value, called-calling user direction;"""

    called_maximum_acceptable   : uint16    = 0
    """maximum acceptable, called-calling user direction;"""
    # fmt: on


@struct(options=[S_ADD_BYTES])
class TPDU_ResidualErrorRate:
    """Residual error rate (not used if class 0 is the preferred class)"""

    # fmt: off
    target_value          : uint8   = 0
    """target value, power of 10;"""

    minimum_acceptable    : uint8   = 0
    """minimum acceptable, power of 10;"""

    tsdu_size_of_interest : uint8   = 0
    """TSDU size of interest, expressed as a power of 2."""
    # fmt: on


TPDU_Checksum = Bytes(2)


class Parameter_Code(enum.IntEnum):
    """Defines different parameter types used accross TPDUs"""

    __struct__ = uint8

    # fmt: off
    CALLED_T_SELECTOR   = 0b11000001  # Transport-Selector (T-selector) called or Invalid TPDU
    CALLING_T_SELECTOR  = 0b11000010  # Transport-Selector (T-selector) calling
    TPDU_SIZE           = 0b11000000  # TPDU size
    MAX_TPDU_SIZE       = 0b11110000  # Preferred maximum TPDU size
    VERSION             = 0b11000100  # Version number
    PROTECTION          = 0b11000101  # Protection parameters
    CHECKSUM            = 0b11000011  # Checksum
    ADDITIONAL_OPTS     = 0b11000110  # Additional option selection
    ALTERNATIVE_CLASSES = 0b11000111  # Alternative protocol classes
    ACK_TIME            = 0b10000101  # Acknowledgement time
    THROUGHPUT          = 0b10001001  # Throughput indication
    ERROR_RATE          = 0b10000110  # Residual error rate
    PRIORITY            = 0b10000111  # Priority
    TRANSIT_DELAY       = 0b10001000  # Transit delay
    REASSIGNMENT_TIME   = 0b10001011  # Reassignment time
    INACTIVITY          = 0b11110010  # Inactivity timer
    ADDTITIONAL_INFO    = 0b11100000  # DR additional information
    SUBSEQUENCE_NUM     = 0b10001010  # Subsequence number
    FLOW_CONTROL_INFO   = 0b10001100  # Flow control information
    ACK_PARAMS          = 0b10001111  # Selective acknowledgement parameters
    # fmt: on


# fmt: off
TPDU_PARAM_TYPES = {
    Parameter_Code.TPDU_SIZE           : Enum(TPDU_Size, uint8),
    Parameter_Code.VERSION             : uint8,
    Parameter_Code.CHECKSUM            : uint16,
    Parameter_Code.ADDITIONAL_OPTS     : TPDU_AdditionalOptions,
    Parameter_Code.ALTERNATIVE_CLASSES : uint8[...],
    Parameter_Code.ACK_TIME            : uint16,
    Parameter_Code.ERROR_RATE          : TPDU_ResidualErrorRate,
    Parameter_Code.PRIORITY            : uint16,
    Parameter_Code.TRANSIT_DELAY       : TPDU_TransitDelay,
    Parameter_Code.REASSIGNMENT_TIME   : uint16,
    Parameter_Code.INACTIVITY          : uint32,
    Parameter_Code.SUBSEQUENCE_NUM     : uint16,
    Parameter_Code.CHECKSUM            : TPDU_Checksum,
    # Parameter_Code.CALLED_T_SELECTOR   : uint16,
    # Parameter_Code.CALLING_T_SELECTOR  : uint16,

    # all other options will use raw bytes
    DEFAULT_OPTION                     : Bytes(...),
}
# fmt: on


@struct(options=[S_ADD_BYTES])
class Parameter:
    """13.2.3 Variable part

    The variable part is used to define less frequently used parameters. If the
    variable part is present, it shall contain one or more parameters.
    """

    # fmt: off
    type_id : Enum(Parameter_Code, uint8) | ENUM_STRICT                           = 0
    """The parameter code"""

    # Simple TLV structure with dynamic parsing behabior
    value   : Prefixed(uint8, F(this.type_id) >> TPDU_PARAM_TYPES) = b""
    """
    The parameter length indication indicates the length, in octets, of the
    parameter value field.

    The parameter value field contains the value of the parameter identified in
    the parameter code field.
    """

    # --- Verification
    @staticmethod
    def _verify_parameter(context) -> None:
        # Since we're using a greedy length by default on the value, we can't be
        # sure if the parameter is valid or not. This action resolbes that
        # issue.
        parameter = context[CTX_OBJECT]
        if parameter.type_id == 0 and not parameter.value:
            raise ValueError("Invalid parameter")

    _verify: Action(unpack=_verify_parameter)
    # fmt: on


@struct
class TPDU:
    """Transport Protocol Data Units (TPDUs)"""

    # fmt: off

    li   : uint8     = 0
    """13.2.1 Length indicator field

    The length indicated shall be the header length in octets including
    parameters, but excluding the length indicator field and user data, if any.
    The value 255 (1111 1111) is reserved for possible extensions.
    """

    code : uint8     = 0
    """13.2.2.2 TPDU code

    This field contains the TPDU code. It is used to define the structure of the
    remaining header.
    """
    # fmt: on

    @property
    def tpdu_code(self) -> TPDU_Code:
        """Qualified TPDU code"""
        return TPDU_Code(self.code >> 4)

    @tpdu_code.setter
    def tpdu_code(self, value: TPDU_Code):
        self.code = (self.code & 0x0F) | (value.value << 4)

    @property
    def code_arg(self) -> int:
        """Argument bits of the TPDU code"""
        return self.code & 0x0F

    @code_arg.setter
    def code_arg(self, value: int):
        self.code = (self.code & 0xF0) | value

    def has_parameters(self) -> bool:
        """Whether the TPDU has parameters"""
        return bool(hasattr(self, "parameters"))

    def get_parameters(self) -> list[Parameter]:
        """Returns the parameters of the TPDU if present"""
        return getattr(self, "parameters", [])

    def has_checksum(self) -> bool:
        """Checks whether the TPDU has a checksum parameter"""
        return any(
            (map(lambda p: p.type_id == Parameter_Code.CHECKSUM, self.get_parameters()))
        )

    @property
    def fixed_size(self) -> int:
        """
        Returns the number of octets that make up the fixed (header) part
        of this TPDU, excluding the variable part and user data.

        This value is normally defined per TPDU type in X.224 and stored
        as the class attribute ``TPDU_FIXED_SIZE``. If the subclass does
        not define it, a default of 1 octet is returned.

        The fixed size is used when computing the length indicator (LI),
        and also when locating parameter offsets, such as the position
        of the checksum parameter.
        """
        return getattr(self, "TPDU_FIXED_SIZE", 1)

    @property
    def first_checksum_octet(self) -> int:
        """
        Returns the zero-based index (offset) of the first checksum octet
        within the serialized TPDU, or -1 if no parameters are present.

        For ease of computation, the checksum parameter MUST appear in
        the *first position* of the variable part when present. This means:

        - Offset starts at ``fixed_size`` (end of fixed header)
        - Add 1 byte for the Length Indicator (LI)
        - Add 2 bytes for the TLV header (parameter code and length)
        """
        if not self.has_parameters():
            return -1

        # checksum MUST be in the first position of the parameters.
        # Add one for the length indicator
        # Add two for the TLV header (type_id, length)
        return self.fixed_size + 1 + 2

    def get_checksum(self) -> bytes:
        """
        Returns the current 2-byte checksum value from the variable part,
        if a checksum parameter is present. If no checksum parameter is
        found, returns an empty byte string.

        The checksum parameter is identified by its type code
        ``Parameter_Code.CHECKSUM`` and should be the first parameter.
        """
        parameters = self.get_parameters()
        for p in parameters:
            if p.type_id == Parameter_Code.CHECKSUM:
                return p.value
        return b""

    def set_checksum(self, value: bytes):
        """
        Sets the checksum parameter value in the TPDU.

        If a checksum parameter already exists, its value is replaced.
        If it does not exist, it is inserted into the first position
        of the parameter list. This ensures the checksum field is correctly
        located for both building and verification.
        """
        parameters = self.get_parameters()
        parameter = next(
            filter(lambda p: p.type_id == Parameter_Code.CHECKSUM, parameters), None
        )
        if parameter:
            parameter.value = value
        else:
            # always first position
            parameters.insert(0, Parameter(Parameter_Code.CHECKSUM, value))

    def is_valid(self) -> bool:
        """
        Verifies the TPDU checksum if present.

        - If no checksum parameter is found, returns True (valid by default).
        - If present, recomputes the checksum over the TPDU using the
          Annex D.3 algorithm, comparing the calculated value to the
          stored one.

        This method does not rebuild the TPDU using ``build()`` to avoid
        unintentional mutations; it uses the raw packed representation
        for verification.
        """
        if not self.has_checksum():
            return True
        return verify_checksum(pack(self), self.first_checksum_octet)

    def build(self, add_checksum: bool = False) -> bytes:
        """
        Serializes the TPDU into its octet representation.

        This method constructs a valid TPDU by encoding its fixed and
        variable parts, and optionally adds a checksum parameter.

        Behavior depends on ``add_checksum``:

        - **False (default)**: The TPDU is serialized normally without
          any checksum.
        - **True**:
            1. A placeholder checksum parameter (two zero bytes) is
               inserted.
            2. The TPDU is packed into octets.
            3. The checksum is recomputed across the entire TPDU (with
               zeros in the checksum field).
            4. The placeholder checksum is replaced with the computed
               value and the TPDU is repacked.

        Example:

        >>> pdu = TPDU_ConnectionRequest()
        >>> pdu.build(add_checksum=True)
        b'\\n\\xe0\\x00\\x00\\x00\\x00\\x00\\xc3\\x02|\\xd5'
        >>> parsed = TPDU_ConnectionRequest.from_octets(_)
        TPDU_ConnectionRequest(li=10, code=224,...parameters=[Parameter(type_id=<Parameter_Code.CHECKSUM: 195>, value=b'|\\xd5')])

        :param add_checksum: Whether to generate and insert a checksum
                             parameter during the build process.
        :return: Byte string representing the complete TPDU.
        """
        fixed_size = self.fixed_size
        # D.3.1 Set up the complete TPDU with the value of the checksum
        # parameter field set to zero.
        if add_checksum:
            self.set_checksum(bytes(2))

        parameters = self.get_parameters()
        variable_part = pack(parameters, TPDU_VariablePart) if len(parameters) else b""
        self.li = len(variable_part) + fixed_size
        tpdu_data = pack(self)
        if add_checksum:
            self.set_checksum(checksum(tpdu_data, self.first_checksum_octet))
            return pack(self)

        return tpdu_data

    @classmethod
    def from_octets(cls, octets: bytes):
        """
        Deserialize raw octets into a TPDU (or subclass) instance.

        This method unpacks the raw TPDU structure into the corresponding
        class representation.

        :param octets: Encoded TPDU octets.
        :type octets: bytes
        :return: TPDU instance populated from octets.
        :rtype: TPDU
        """
        return unpack(cls, octets)


@bitfield(options=[S_ADD_BYTES])
class TPDU_ClassOption:
    """CLASS OPTION

    Defines the preferred transport protocol class to be operated over the
    requested transport connection.
    """

    # fmt: off
    class_id              : (4, EnumFactory(TPDU_Class)) = TPDU_Class.CLASS0
    reserved              :  2                           = 0
    extended_formats      :  1                           = False
    explicit_flow_control :  1                           = False
    # fmt: on


TPDU_VariablePart = Parameter[...]
"""13.2.3 Variable part

The variable part is used to define less frequently used parameters. If the
variable part is present, it shall contain one or more parameters.
"""

TPDU_UserData = Bytes(...)
"""13.2.4 Data field

This field contains transparent user data
"""


@struct(order=BigEndian)
class TPDU_ConnectionRequest(TPDU):
    """13.3 Connection Request (CR) TPDU"""

    TPDU_FIXED_SIZE = 6

    # fmt: off
    dst_ref: uint16 = 0
    """c) DST-REF - Set to zero."""

    src_ref: uint16 = 0
    """d) SRC-REF

    Reference selected by the transport entity initiating the CR-TPDU to
    identify the requested transport connection.
    """

    class_opt: TPDU_ClassOption = None
    """e) CLASS OPTION

    Bits 8 to 5 of octet 7 define the preferred transport protocol class to be
    operated over the requested transport connection. The CR-TPDU contains the
    first choice of class in the fixed part. Second and subsequent choices are
    listed in the variable part if required.
    """

    parameters: Bytes(this.li - 6) & TPDU_VariablePart = None
    """13.3.4 Variable part

    The following parameters are permitted in the variable part:

    - a) Transport-Selector (T-selector)
    - b) TPDU size
    - c) Preferred maximum TPDU size
    - d) Version number (not used if class 0 is the preferred class)
    - e) Protection parameters (not used is class 0 is the preferred class)
    - f) Checksum (used only if class 4 is the preferred class)
    - h) Alternative protocol class(es) (not used if class 0 is the preferred
         class or when operating over CLNS) Parameter code:
    - i) Acknowledgement time (used only if class 4 is the preferred class)
    - j) Throughput (not used if class 0 is the preferred class)
    - k) Residual error rate (not used if class 0 is the preferred class)
    - l) Priority (not used if class 0 is the preferred class)
    - m) Transit delay (not used if class 0 is the preferred class)
    - n) Reassignment time (not used if class 0 or 2 is the preferred class; if
         class 4 is preferred and class 3 is an alternate, it may be used)
    - o) Inactivity timer (used only if class 4 is the preferred or selected
         class)
    """

    user_data: TPDU_UserData = None
    """
    No user data are permitted in class 0, and are optional in other classes.
    """
    # fmt: on

    def __post_init__(self) -> None:
        self.tpdu_code = TPDU_Code.CR
        self.class_opt = self.class_opt or TPDU_ClassOption()
        self.parameters = self.parameters or []
        self.user_data = self.user_data or b""


@struct(order=BigEndian)
class TPDU_ConnectionConfirm(TPDU):
    """13.4Connection Confirm (CC) TPDU"""

    TPDU_FIXED_SIZE = 6

    # fmt: off
    dst_ref    : uint16                                 = 0
    """c) DST-REF

    Reference identifying the requested transport connection at the remote
    transport entity.
    """

    src_ref    : uint16                                 = 0
    """d) SRC-REF

    Reference selected by the transport entity initiating the CC-TPDU to
    identify the confirmed transport connection.
    """

    class_opt  : TPDU_ClassOption                       = None
    """e) CLASS OPTION

    Defines the selected transport protocol class and option to be operated over
    the accepted transport connection.
    """

    parameters : Bytes(this.li - 6) & TPDU_VariablePart = None
    """Same as in :class:`TPDU_ConnectionRequest`"""

    user_data  : TPDU_UserData                          = b""
    """13.4.5 User Data

    No user data are permitted in class 0, and are optional in the other classes.
    """
    # fmt: on

    def __post_init__(self):
        self.tpdu_code = TPDU_Code.CC
        self.class_opt = self.class_opt or TPDU_ClassOption()
        self.parameters = self.parameters or []
        self.user_data = self.user_data or b""


@struct(order=BigEndian)
class TPDU_DisconnectRequest(TPDU):
    """13.5 Disconnect Request (DR) TPDU

    The DR-TPDU is used to terminate a transport connection. It may carry
    parameters and optional user data.
    """

    TPDU_FIXED_SIZE = 6

    # fmt: off
    dst_ref: uint16 = 0
    """Destination reference — identifies the transport connection to be
    released."""

    src_ref: uint16 = 0
    """Source reference — identifies the transport connection from the sender's
    perspective."""

    reason: TPDU_DisconnectReason = 0
    """Reason code for disconnection (X.224 §13.5.4)."""

    parameters: Bytes(this.li - 6) & TPDU_VariablePart = None
    """Optional parameters (variable part)

    Allowed parameters:

    - a) Additional information
    - b) Checksum
    """

    user_data: TPDU_UserData = None
    """Optional user data — must not exceed 64 octets."""
    # fmt: on

    def __post_init__(self):
        self.parameters = self.parameters or []
        self.user_data = self.user_data or b""
        self.tpdu_code = TPDU_Code.DR


@struct(order=BigEndian)
class TPDU_DisconnectConfirm(TPDU):
    """3.6 Disconnect Confirm (DC) TPDU

    The DC-TPDU is sent in response to a DR-TPDU to confirm the disconnection
    of a transport connection.
    """

    TPDU_FIXED_SIZE = 5

    # fmt: off
    dst_ref: uint16 = 0
    """Destination reference — identifies the transport connection being
    confirmed as disconnected."""

    src_ref: uint16 = 0
    """Source reference — identifies the transport connection from the sender's
    perspective."""

    parameters: Bytes(this.li - 5) & TPDU_VariablePart = None
    """Only checksum is allowed as a parameter"""
    # fmt: on

    def __post_init__(self):
        self.parameters = self.parameters or []
        self.tpdu_code = TPDU_Code.DC


@bitfield
class TPDU_Number:
    eot: 1 = False
    """d) EOT

    When set to ONE, it indicates that the current DT-TPDU is the last data unit
    of a complete DT-TPDU sequence (end of TSDU).
    """

    value: 7 = 0
    """e) TPDU-NR

    TPDU send sequence number (zero in class 0). May take any value in class 2
    without explicit flow control. TPDU-NR is bits 7 to 1 of octet 3 for
    classes 0 and 1, bits 7 to 1 of octet 5 for classes 2, 3 and 4.
    """


@struct(order=BigEndian)
class TPDU_Data(TPDU):
    """13.7 Data (DT) TPDU

    The DA-TPDU is used to transfer data over a transport connection. It may
    carry parameters and optional user data.
    """

    TPDU_FIXED_SIZE = 2

    # fmt: off
    nr: TPDU_Number = None
    """e) TPDU-NR"""

    user_data: TPDU_UserData = b""
    """This field contains data of the TSDU being transmitted."""
    # fmt: on

    def __post_init__(self):
        if not isinstance(self.nr, TPDU_Number):
            self.nr = TPDU_Number()
        self.user_data = self.user_data or b""
        self.tpdu_code = TPDU_Code.DT

    @property
    def tpdu_nr(self) -> int:
        return self.nr.value

    @property
    def is_last(self) -> bool:
        return self.nr.eot


@struct(order=BigEndian)
class TPDU_ExpeditedData(TPDU):
    """13.8 Expedited Data (ED) TPDU

    The ED-TPDU is used to send expedited (urgent) data across the transport
    connection.
    """

    TPDU_FIXED_SIZE = 4

    dst_ref: uint16 = 0
    """Destination reference — identifies the transport connection to which the
    expedited data belongs."""

    ed_nr: TPDU_Number = None
    """Sequence number for expedited data (X.224 §13.8.4)."""

    parameters: Bytes(this.li - 4) & TPDU_VariablePart = None
    """Only checksum is allowed as a parameter"""

    user_data: TPDU_UserData = None
    """The expedited data payload — must not exceed the maximum allowed for
    expedited service."""

    def __post_init__(self):
        self.user_data = self.user_data or b""
        if not isinstance(self.ed_nr, TPDU_Number):
            self.ed_nr = TPDU_Number()
        self.parameters = self.parameters or []
        self.tpdu_code = TPDU_Code.ED


@struct(order=BigEndian)
class TPDU_DataAcknowledgement(TPDU):
    """13.9 Data Acknowledgement (AK) TPDU

    The AK-TPDU acknowledges receipt of data and communicates flow control
    information.
    """

    TPDU_FIXED_SIZE = 6

    dst_ref: uint16 = 0
    """Destination reference — identifies the transport connection."""

    next_nr: TPDU_Number = None
    """Next expected TPDU sequence number."""

    credit: uint16 = 0
    """Flow control credit — number of TPDUs the sender is prepared to receive."""

    parameters: Bytes(this.li - 6) & TPDU_VariablePart = None
    """Optional parameters allowed in AK-TPDU:

    - a) Checksum
    - b) Subsequence number when optionally used under the conditions defined in
         class 4.
    - c) Flow control confirmation when optionally used under the conditions
         defined in class 4.
    - d) Selective acknowledgement parameters when optionally used, under
         conditions defined in class 4.
    """
    # fmt: on

    def __post_init__(self):
        self.parameters = self.parameters or []
        self.tpdu_code = TPDU_Code.AK
        if not isinstance(self.next_nr, TPDU_Number):
            self.next_nr = TPDU_Number()


@struct(order=BigEndian)
class TPDU_ExpeditedDataAcknowledgement(TPDU):
    """13.10 Expedited Data Acknowledgement (EA) TPDU

    The EA-TPDU is used to acknowledge receipt of expedited data (ED TPDUs).
    """

    TPDU_FIXED_SIZE = 4

    # fmt: off
    dst_ref: uint16 = 0
    """Destination reference — identifies the transport connection."""

    ed_nr: TPDU_Number = None
    """Expedited data sequence number being acknowledged."""

    parameters: Bytes(this.li - 4) & TPDU_VariablePart = None
    """Only checksum is allowed as a parameter"""
    # fmt: on

    def __post_init__(self):
        self.tpdu_code = TPDU_Code.EA
        self.parameters = self.parameters or []
        if not isinstance(self.ed_nr, TPDU_Number):
            self.ed_nr = TPDU_Number()


@struct(order=BigEndian)
class TPDU_Reject(TPDU):
    """13.11 Reject (RJ) TPDU

    The RJ-TPDU requests retransmission of certain TPDUs due to detected errors.
    """

    TPDU_FIXED_SIZE = 5

    dst_ref: uint16 = 0
    """Destination reference — identifies the transport connection."""

    y_nr: uint16 = 0
    """Next expected TPDU sequence number (Y(R))."""

    def __post_init__(self):
        self.tpdu_code = TPDU_Code.RJ


# Reject cause codes for ER (X.224 §13.12.3)
class ER_RejectCause(enum.IntEnum):
    __struct__ = uint8
    REASON_NOT_SPECIFIED = 0x00
    INVALID_PARAMETER_CODE = 0x01
    INVALID_TPDU_TYPE = 0x02
    INVALID_PARAMETER_VALUE = 0x03


@struct(order=BigEndian)
class TPDU_Error(TPDU):
    """13.12 TPDU error (ER) TPDU

    No user data.
    """

    TPDU_FIXED_SIZE = 4

    # fmt: off
    dst_ref: uint16 = 0
    """Destination reference (see §13.4.3)."""

    reject_cause: ER_RejectCause = ER_RejectCause.REASON_NOT_SPECIFIED
    """Reject cause (§13.12.3)."""

    parameters: Bytes(this.li - 4) & TPDU_VariablePart = None
    """Optional parameters:

    - a) Invalid TPDU
    - b) Checksum
    """
    # fmt: on

    def __post_init__(self):
        self.tpdu_code = TPDU_Code.ER
        self.parameters = self.parameters or []


TPDU_TYPES = {
    TPDU_Code.AK: TPDU_DataAcknowledgement,
    TPDU_Code.CC: TPDU_ConnectionConfirm,
    TPDU_Code.CR: TPDU_ConnectionRequest,
    TPDU_Code.DC: TPDU_DisconnectConfirm,
    TPDU_Code.DR: TPDU_DisconnectRequest,
    TPDU_Code.DT: TPDU_Data,
    TPDU_Code.EA: TPDU_ExpeditedDataAcknowledgement,
    TPDU_Code.ED: TPDU_ExpeditedData,
    TPDU_Code.ER: TPDU_Error,
    TPDU_Code.RJ: TPDU_Reject,
}

# just for typing purposes here
_TPDULike = (
    TPDU
    | TPDU_ConnectionConfirm
    | TPDU_ConnectionRequest
    | TPDU_Data
    | TPDU_DataAcknowledgement
    | TPDU_DisconnectConfirm
    | TPDU_DisconnectRequest
    | TPDU_Error
    | TPDU_ExpeditedData
    | TPDU_ExpeditedDataAcknowledgement
    | TPDU_Reject
)


def parse_tpdu(octets: bytes) -> _TPDULike:
    """
    Parse a TPDU (Transport Protocol Data Unit) from raw octets.

    First decodes a generic :class:`TPDU` to extract the TPDU code and uses this
    to dispatch to the corresponding TPDU subclass implementation defined in
    :data:`TPDU_TYPES`.

    Example:

    >>> tpdu = parse_tpdu(...)
    >>> isinstance(tpdu, TPDU_Data)
    True
    >>> data: bytes = tpdu.user_data

    :param octets: Raw TPDU octets to parse.
    :type octets: bytes
    :raises ValueError: If the octet buffer is shorter than two bytes.
    :return: A parsed TPDU instance corresponding to the TPDU code
             (e.g., :class:`TPDU_ConnectionRequest`).
    :rtype: _TPDULike
    """
    if len(octets) < 2:
        raise ValueError("TPDU must have at least 2 octets")

    tpdu_base = TPDU.from_octets(octets)
    tpdu_type = TPDU_TYPES.get(tpdu_base.tpdu_code, TPDU)
    return tpdu_type.from_octets(octets)
