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
# 1pyright: reportInvalidTypeForm=false, reportGeneralTypeIssues=false, reportAssignmentType=false


# See ITU X.224 - Open Systems Interconnection – Connection-mode protocol
# specifications
import enum

from typing import Any
from collections.abc import Iterable

from caterpillar.context import CTX_OBJECT
from caterpillar.model import Invisible, bitfield, EnumFactory, struct
from caterpillar.options import S_ADD_BYTES
from caterpillar.py import StructDefMixin
from caterpillar.shared import Action
from caterpillar.shortcuts import F, BigEndian, opt, pack, this, unpack, f
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
from caterpillar.types import uint8_t, uint16_t
from caterpillar.abc import _ContextLike


def checksum(tpdu_data: Iterable[int], checksum_off: int):
    """
    Compute the checksum for a TPDU according to Annex D.3 of X.224.

    Two running accumulators, ``C0`` and ``C1``, are folded over every
    octet of ``tpdu_data`` in order (each octet updates ``C0``, and the
    updated ``C0`` is then folded into ``C1``). Their final values are
    combined with the total octet count ``L`` and the checksum's offset
    ``n`` to derive the pair of result octets:

    - ``X = (-C1 + (L - n) * C0) mod 256``
    - ``Y = (C1 - (L - n + 1) * C0) mod 256``

    :param tpdu_data: Sequence of TPDU octets.
    :type tpdu_data: Iterable[int]
    :param checksum_off: Offset where the two checksum octets reside.
    :type checksum_off: int
    :return: Two-byte checksum value (X, Y).
    :rtype: bytes
    """

    # total octet count and offset of the checksum field within it
    octets = list(tpdu_data)
    L = len(octets)
    n = checksum_off

    c0 = c1 = 0
    # running sum: fold each octet into C0, then fold C0 into C1
    for byte in tpdu_data:
        c0 = (c0 + byte) & 0xFF
        c1 = (c0 + c1) & 0xFF

    # derive the two result octets from the final accumulator state
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
    """Per-type identifier occupying the upper nibble of a TPDU's
    :attr:`~TPDU.code` octet; selects which TPDU subclass and fixed
    header layout a decoder should use for the remaining bytes.
    """

    ED = 0x01  # Expected Data
    EA = 0x02  # Expedited data acknowledgement
    RJ = 0x05  # Reject
    AK = 0x06  # Data acknowledgement
    ER = 0x07  # Error
    DR = 0x08  # Disconnect request
    DC = 0x0C  # Disconnect confirmation
    CC = 0x0D  # Connection confirmation
    CR = 0x0E  # Connection request
    DT = 0x0F  # Data


class TPDU_Class(enum.IntEnum):
    """Transport protocol classes (clause 7 of X.224), assigned to the
    ``class_id`` of a :class:`TPDU_ClassOption` to pick which connection,
    flow-control, and recovery features a transport connection uses.
    """

    CLASS0 = 0
    """Class 0 - simple class.

    Covers connection establishment (with negotiation), segmented data
    transfer, and reporting of protocol errors.
    """

    CLASS1 = 1
    """Class 1 - basic error recovery class.

    Provides flow control tied to the underlying network connection's
    own flow control, together with error recovery, expedited data
    transfer, an explicit disconnect procedure, and the ability to run
    consecutive transport connections over a single network connection.
    """

    CLASS2 = 2
    """Class 2 - multiplexing class.

    Supports transport connections with flow control being optional
    (used or not, per connection); it offers neither error detection
    nor error recovery.
    """

    CLASS3 = 3
    """Class 3 - error recovery and multiplexing class.

    Everything class 2 offers, but always with explicit flow control,
    plus recovery from a failure reported by the Network Layer that is
    handled internally, without involving the TS-user.
    """

    CLASS4 = 4
    """Class 4 - error detection and recovery class.

    Everything class 3 offers, plus detection and recovery from lost,
    duplicated, or out-of-sequence TPDUs, again handled internally
    without involving the TS-user.
    """


class TPDU_DisconnectReason(enum.IntEnum):
    """Reason codes carried by a DR-TPDU to explain why the transport
    connection is being released."""

    __struct__ = uint8

    NORMAL = 128 + 0
    """The session entity requested this disconnect under normal
    conditions."""

    REMOTE_CONGEST = 128 + 1
    """The remote transport entity was congested at the time the
    connection was requested."""

    NEGO_FAILED = 128 + 2
    """Class negotiation failed, i.e. none of the proposed protocol
    class(es) could be supported."""

    DUPLICATE_SOURCE = 128 + 3
    """This source reference was already in use for the same pair of
    NSAPs."""

    MISMATCHED_REFERENCES = 128 + 4
    """The connection's reference values did not match."""

    PROTOCOL_ERROR = 128 + 5
    """A protocol error was detected."""

    REF_OVERFLOW = 128 + 7
    """The connection reference has overflowed."""

    CONN_REFUSED = 128 + 8
    """The connection request was refused over this network
    connection."""

    INVALID_LENGTH = 128 + 10
    """The header length, or a parameter's length, was invalid."""

    # available for all classes
    UNSPECIFIED = 0
    """No specific reason was given."""

    TSAP_CONGESTION = 1
    """The destination TSAP was congested."""

    ENTITIY_NOT_ATTACHED = 2
    """No session entity is attached to that TSAP."""

    UNKNOWN_ADDRESS = 3
    """The destination address was not recognized."""


class TPDU_Size(enum.IntEnum):
    """
    Maximum TPDU size (header included, in octets) proposed for use over
    the requested transport connection. Each value is the base-2
    logarithm of the octet count it represents, as carried in the
    TPDU-SIZE parameter.
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
    """Why a connection request was rejected."""

    __struct__ = uint8

    UNSPECIFIED = 0
    """No cause was given."""

    INVALID_PARAMETER_CODE = 1
    """A parameter code was not recognized."""

    INVALID_PDU_TYPE = 2
    """The PDU type was not recognized."""

    INVALID_PARAMETER_VALUE = 3
    """A parameter carried a value that is not valid."""


@bitfield(options=[opt.S_ADD_BYTES])
class TPDU_AdditionalOptions:
    """Bit flags for the ADDITIONAL OPTION SELECTION parameter; irrelevant
    whenever class 0 is the preferred class."""

    # fmt: off
    unused                 : f[bool, 1] = False
    non_blocking           : f[bool, 1] = False
    """When set, class 4 uses non-blocking expedited data."""

    use_request_ack        : f[bool, 1] = False
    """When set, classes 1, 3 and 4 use the request-acknowledgement
    option."""

    use_selective_ack      : f[bool, 1] = False
    """When set, class 4 uses selective acknowledgement."""

    speed_up               : f[bool, 1] = False
    """When set, class 1 makes use of the network service's expedited
    delivery."""

    use_receipt_info       : f[bool, 1] = False
    """
    Chooses, for class 1, between receipt confirmation (``True``) and
    the explicit AK variant (``False``).
    """

    use_checksum_16bit     : f[bool, 1] = False
    """When set, class 4 uses the 16-bit checksum defined in clause 6.17."""

    use_transport_speed_up : f[bool, 1] = True
    """When set, the transport-expedited data transfer service is used."""
    # fmt: on


@struct(order=BigEndian, options=[S_ADD_BYTES])
class TPDU_TransitDelay:
    """TRANSIT DELAY parameter values, one target/maximum pair per
    direction; unused whenever class 0 is the preferred class."""

    # fmt: off
    calling_target_value        : uint16_t    = 0
    """Target transit delay from the calling to the called user."""

    calling_maximum_acceptable  : uint16_t    = 0
    """Largest transit delay still acceptable from the calling to the
    called user."""

    called_target_value         : uint16_t    = 0
    """Target transit delay from the called to the calling user."""

    called_maximum_acceptable   : uint16_t    = 0
    """Largest transit delay still acceptable from the called to the
    calling user."""
    # fmt: on


@struct(options=[S_ADD_BYTES])
class TPDU_ResidualErrorRate:
    """RESIDUAL ERROR RATE parameter values; unused whenever class 0 is
    the preferred class."""

    # fmt: off
    target_value          : uint8_t   = 0
    """Target residual error rate, expressed as a power of 10."""

    minimum_acceptable    : uint8_t   = 0
    """Smallest residual error rate still acceptable, expressed as a
    power of 10."""

    tsdu_size_of_interest : uint8_t   = 0
    """TSDU size this error rate applies to, expressed as a power of 2."""
    # fmt: on


TPDU_Checksum = Bytes(2)


class Parameter_Code(enum.IntEnum):
    """Defines different parameter types used accross TPDUs"""

    __struct__ = uint8

    # fmt: off
    CALLING_T_SELECTOR  = 0b11000001  # Transport-Selector (T-selector) calling
    CALLED_T_SELECTOR   = 0b11000010  # Transport-Selector (T-selector) called/responding or Invalid TPDU
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
    # Parameter_Code.CALLED_T_SELECTOR   : uint16_t,
    # Parameter_Code.CALLING_T_SELECTOR  : uint16_t,

    # all other options will use raw bytes
    DEFAULT_OPTION                     : Bytes(...),
}
# fmt: on


@struct(options=[S_ADD_BYTES])
class Parameter(StructDefMixin):
    """A single TLV-encoded entry from a TPDU's variable part (X.224,
    §13.2.3).

    Each :class:`TPDU` subclass that defines a ``parameters`` field
    stores a list of these; the variable part only exists at all when
    at least one such parameter needs to be carried.
    """

    # fmt: off
    type_id : f[Parameter_Code, Enum(Parameter_Code, uint8) | ENUM_STRICT] = 0
    """The parameter code"""

    # Simple TLV structure with dynamic parsing behabior
    value   : f[Any, Prefixed(uint8, F(this.type_id) >> TPDU_PARAM_TYPES)] = b""
    """Parameter payload, length-prefixed by a single length octet.

    The concrete type stored here is looked up from
    :data:`TPDU_PARAM_TYPES` based on ``type_id``, so this field decodes
    to whatever representation is appropriate for that parameter code.
    """

    # --- Verification
    @staticmethod
    def _verify_parameter(context: _ContextLike) -> None:
        # Since we're using a greedy length by default on the value, we can't be
        # sure if the parameter is valid or not. This action resolbes that
        # issue.
        parameter = context[CTX_OBJECT]
        if parameter.type_id == 0 and not parameter.value:
            raise ValueError("Invalid parameter")

    _verify: f[None, Action(unpack=_verify_parameter)] = Invisible()
    # fmt: on


@struct
class TPDU:
    """Transport Protocol Data Units (TPDUs)"""

    # fmt: off

    li   : uint8_t     = 0
    """Header length indicator, in octets.

    Counts the fixed and variable parts of the header - i.e. everything
    after this field up to (but not including) the user data - which is
    the same quantity :meth:`build` derives from :attr:`fixed_size` plus
    the packed variable part's length. The value 255 (1111 1111) is set
    aside by the standard for a future length-indicator extension.
    """

    code : uint8_t     = 0
    """Raw TPDU code octet, combining :attr:`tpdu_code` (upper nibble)
    and :attr:`code_arg` (lower nibble); together they identify which
    kind of TPDU this is and how the rest of the header is laid out.
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
        TPDU_ConnectionRequest(li=10, code=224,...parameters=[Parameter(type_id=<Parameter_Code.CHECKSUM: int1_t95>, value=b'|\\xd5')])

        :param add_checksum: Whether to generate and insert a checksum
                             parameter during the build process.
        :return: Byte string representing the complete TPDU.
        """
        fixed_size = self.fixed_size
        # zero out the checksum parameter before computing over the whole TPDU
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
    """CLASS OPTION octet, as carried by CR/CC-TPDUs.

    Packs the preferred/selected transport protocol class (``class_id``)
    for this connection alongside the ``extended_formats`` and
    ``explicit_flow_control`` switches, with two reserved bits in
    between.
    """

    # fmt: off
    class_id              : f[TPDU_Class | int, (4, EnumFactory(TPDU_Class))] = TPDU_Class.CLASS0
    reserved              : f[int, 2]                                          = 0
    extended_formats      : f[bool, 1]                                         = False
    explicit_flow_control : f[bool, 1]                                         = False
    # fmt: on


TPDU_VariablePart = Parameter[...]
"""Packing helper for a TPDU's variable part (X.224, §13.2.3): an
open-ended sequence of zero or more :class:`Parameter` entries, back to
back until the bytes run out.
"""

TPDU_UserData = Bytes(...)
"""Packing helper for a TPDU's user-data field (X.224, §13.2.4): the
remaining bytes are copied through as-is, with no further structure
imposed.
"""


@struct(order=BigEndian)
class TPDU_ConnectionRequest(TPDU):
    """Connection Request (CR) TPDU (X.224, §13.3), sent to open a new
    transport connection and propose the parameters it should use.
    """

    TPDU_FIXED_SIZE = 6

    # fmt: off
    dst_ref: uint16_t = 0
    """Destination reference - always zero on a CR-TPDU."""

    src_ref: uint16_t = 0
    """Source reference chosen by this (initiating) transport entity to
    identify the connection being requested.
    """

    class_opt: TPDU_ClassOption = None
    """First-choice class option for this connection (bits 8-5 of octet
    7). Any further class choices the initiator wants to offer as
    alternatives go into the variable part instead.
    """

    parameters: f[list[Parameter], Bytes(this.li - 6) & TPDU_VariablePart] = None
    """Optional parameters that may accompany a CR-TPDU (X.224, §13.3.4).

    Transport-Selector, TPDU size, and preferred maximum TPDU size may be
    present regardless of class. Version number, protection parameters,
    and alternative protocol class(es) only matter once a class other
    than 0 is proposed - alternative classes are additionally never used
    when running over CLNS. Throughput, residual error rate, priority,
    and transit delay are likewise skipped whenever class 0 is
    preferred. Checksum and acknowledgement time only make sense when
    class 4 is the preferred class. Reassignment time is omitted when
    class 0 or 2 is preferred, but remains available when class 4 is
    preferred with class 3 offered as an alternate. The inactivity timer
    applies once class 4 is either preferred or selected.
    """

    user_data: f[bytes, TPDU_UserData] = None
    """User data accompanying the request; class 0 must leave this
    empty, while every other class may optionally include some.
    """
    # fmt: on

    def __post_init__(self) -> None:
        self.tpdu_code: TPDU_Code = TPDU_Code.CR
        self.class_opt = self.class_opt or TPDU_ClassOption()
        self.parameters = self.parameters or []
        self.user_data = self.user_data or b""


@struct(order=BigEndian)
class TPDU_ConnectionConfirm(TPDU):
    """Connection Confirm (CC) TPDU (X.224, §13.4), returned in reply to
    a CR-TPDU to accept the connection and settle on its final
    parameters.
    """

    TPDU_FIXED_SIZE = 6

    # fmt: off
    dst_ref    : uint16_t                                 = 0
    """Destination reference - identifies, from the remote transport
    entity's point of view, which requested connection this CC-TPDU
    confirms.
    """

    src_ref    : uint16_t                                 = 0
    """Source reference chosen by this (responding) transport entity to
    identify the now-confirmed connection.
    """

    class_opt  : TPDU_ClassOption                       = None
    """Class and option finally selected, from the CR-TPDU's offered
    choices, for this now-accepted connection.
    """

    parameters : f[list[Parameter], Bytes(this.li - 6) & TPDU_VariablePart] = None
    """Same as in :class:`TPDU_ConnectionRequest`"""

    user_data  : f[bytes, TPDU_UserData]                          = b""
    """User data returned with the confirmation (X.224, §13.4.5); empty
    for class 0, optional for every other class.
    """
    # fmt: on

    def __post_init__(self):
        self.tpdu_code: TPDU_Code = TPDU_Code.CC
        self.class_opt = self.class_opt or TPDU_ClassOption()
        self.parameters = self.parameters or []
        self.user_data = self.user_data or b""


@struct(order=BigEndian)
class TPDU_DisconnectRequest(TPDU):
    """Disconnect Request (DR) TPDU (X.224, §13.5): initiates release of
    a transport connection, optionally carrying parameters and user data
    explaining why.
    """

    TPDU_FIXED_SIZE = 6

    # fmt: off
    dst_ref: uint16_t = 0
    """Destination reference - identifies the transport connection to be
    released."""

    src_ref: uint16_t = 0
    """Source reference - identifies the transport connection from the sender's
    perspective."""

    reason: f[TPDU_DisconnectReason | int, Enum(TPDU_DisconnectReason, uint8)] = 0
    """Reason code for disconnection (See X.224, §13.5.4)."""

    parameters: f[list[Parameter], Bytes(this.li - 6) & TPDU_VariablePart] = None
    """Optional variable-part parameters; only additional information
    and checksum may appear here.
    """

    user_data: f[bytes, TPDU_UserData] = None
    """Optional explanatory user data, limited to 64 octets."""
    # fmt: on

    def __post_init__(self):
        self.parameters = self.parameters or []
        self.user_data = self.user_data or b""
        self.tpdu_code: TPDU_Code = TPDU_Code.DR


@struct(order=BigEndian)
class TPDU_DisconnectConfirm(TPDU):
    """Disconnect Confirm (DC) TPDU (X.224, §13.6): the reply to a
    DR-TPDU acknowledging that the connection has been released.
    """

    TPDU_FIXED_SIZE = 5

    # fmt: off
    dst_ref: uint16_t = 0
    """Destination reference - identifies the transport connection being
    confirmed as disconnected."""

    src_ref: uint16_t = 0
    """Source reference - identifies the transport connection from the sender's
    perspective."""

    parameters: f[list[Parameter], Bytes(this.li - 5) & TPDU_VariablePart] = None
    """Only checksum is allowed as a parameter"""
    # fmt: on

    def __post_init__(self):
        self.parameters = self.parameters or []
        self.tpdu_code: TPDU_Code = TPDU_Code.DC


@bitfield
class TPDU_Number:
    eot: f[bool, 1] = False
    """End-of-TSDU marker.

    Set to ``1`` on the final DT-TPDU of a segmented TSDU so the
    receiver knows the sequence is complete; ``0`` on every DT-TPDU
    before it.
    """

    value: f[int, 7] = 0
    """Send sequence number for this TPDU.

    Always zero in class 0, and unconstrained in class 2 when explicit
    flow control is not used. Packed into bits 7-1 of octet 3 for
    classes 0 and 1, or bits 7-1 of octet 5 for classes 2, 3 and 4.
    """


@struct(order=BigEndian)
class TPDU_Data(TPDU):
    """Data (DT) TPDU (X.224, §13.7): the workhorse PDU that carries
    application data across an established transport connection, plus
    any parameters needed alongside it.
    """

    TPDU_FIXED_SIZE = 2

    # fmt: off
    nr: TPDU_Number = None
    """Sequence number and end-of-TSDU marker for this DT-TPDU."""

    user_data: f[bytes, TPDU_UserData] = b""
    """The actual TSDU payload data being carried by this TPDU."""
    # fmt: on

    def __post_init__(self):
        if not isinstance(self.nr, TPDU_Number):
            self.nr = TPDU_Number()
        self.user_data = self.user_data or b""
        self.tpdu_code: TPDU_Code = TPDU_Code.DT

    @property
    def tpdu_nr(self) -> int:
        return self.nr.value

    @property
    def is_last(self) -> bool:
        return self.nr.eot


@struct(order=BigEndian)
class TPDU_ExpeditedData(TPDU):
    """Expedited Data (ED) TPDU (X.224, §13.8): carries urgent data that
    should bypass normal flow control on its way across the connection.
    """

    TPDU_FIXED_SIZE = 4

    dst_ref: uint16_t = 0
    """Destination reference - identifies the transport connection to which the
    expedited data belongs."""

    ed_nr: TPDU_Number = None
    """Sequence number for expedited data (See X.224, §13.8.4)."""

    parameters: f[list[Parameter], Bytes(this.li - 4) & TPDU_VariablePart] = None
    """Only checksum is allowed as a parameter"""

    user_data: f[bytes, TPDU_UserData] = None
    """Expedited payload data, bounded by whatever maximum size the
    expedited service allows.
    """

    def __post_init__(self):
        self.user_data = self.user_data or b""
        if not isinstance(self.ed_nr, TPDU_Number):
            self.ed_nr = TPDU_Number()
        self.parameters = self.parameters or []
        self.tpdu_code: TPDU_Code = TPDU_Code.ED


@struct(order=BigEndian)
class TPDU_DataAcknowledgement(TPDU):
    """Data Acknowledgement (AK) TPDU (X.224, §13.9): acknowledges data
    received so far and reports flow-control state back to the sender.
    """

    TPDU_FIXED_SIZE = 6

    dst_ref: uint16_t = 0
    """Destination reference - identifies the transport connection."""

    next_nr: TPDU_Number = None
    """Sequence number of the next DT-TPDU this side expects to
    receive."""

    credit: uint16_t = 0
    """Flow-control credit: how many further TPDUs the sender of this
    AK-TPDU is currently willing to accept."""

    parameters: f[list[Parameter], Bytes(this.li - 6) & TPDU_VariablePart] = None
    """Optional parameters an AK-TPDU may carry (X.224, §13.9): a
    checksum, and, only where class 4 permits it, a subsequence number,
    flow-control confirmation, and/or selective-acknowledgement
    parameters.
    """
    # fmt: on

    def __post_init__(self):
        self.parameters = self.parameters or []
        self.tpdu_code: TPDU_Code = TPDU_Code.AK
        if not isinstance(self.next_nr, TPDU_Number):
            self.next_nr = TPDU_Number()


@struct(order=BigEndian)
class TPDU_ExpeditedDataAcknowledgement(TPDU):
    """Expedited Data Acknowledgement (EA) TPDU (X.224, §13.10):
    acknowledges receipt of a specific ED-TPDU.
    """

    TPDU_FIXED_SIZE = 4

    # fmt: off
    dst_ref: uint16_t = 0
    """Destination reference - identifies the transport connection."""

    ed_nr: TPDU_Number = None
    """Sequence number of the ED-TPDU that this acknowledgement
    confirms."""

    parameters: f[list[Parameter], Bytes(this.li - 4) & TPDU_VariablePart] = None
    """Only checksum is allowed as a parameter"""
    # fmt: on

    def __post_init__(self):
        self.tpdu_code: TPDU_Code = TPDU_Code.EA
        self.parameters = self.parameters or []
        if not isinstance(self.ed_nr, TPDU_Number):
            self.ed_nr = TPDU_Number()


@struct(order=BigEndian)
class TPDU_Reject(TPDU):
    """Reject (RJ) TPDU (X.224, §13.11): tells the peer that TPDU(s) it
    sent were rejected and need to be retransmitted.
    """

    TPDU_FIXED_SIZE = 5

    dst_ref: uint16_t = 0
    """Destination reference - identifies the transport connection."""

    y_nr: uint16_t = 0
    """Sequence number of the next TPDU this side still expects, i.e.
    Y(R)."""

    def __post_init__(self):
        self.tpdu_code: TPDU_Code = TPDU_Code.RJ


# Reject cause codes for ER (See X.224, §13.12.3)
class ER_RejectCause(enum.IntEnum):
    __struct__ = uint8
    REASON_NOT_SPECIFIED = 0x00
    INVALID_PARAMETER_CODE = 0x01
    INVALID_TPDU_TYPE = 0x02
    INVALID_PARAMETER_VALUE = 0x03


@struct(order=BigEndian)
class TPDU_Error(TPDU):
    """TPDU Error (ER) TPDU (X.224, §13.12): reports a protocol error
    detected in a received TPDU; it never carries user data.
    """

    TPDU_FIXED_SIZE = 4

    # fmt: off
    dst_ref: uint16_t = 0
    """Destination reference (See §13.4.3)."""

    reject_cause: f[ER_RejectCause | int, Enum(ER_RejectCause, uint8)] = ER_RejectCause.REASON_NOT_SPECIFIED
    """Reject cause (See §13.12.3)."""

    parameters: f[list[Parameter], Bytes(this.li - 4) & TPDU_VariablePart] = None
    """Optional parameters: an "Invalid TPDU" entry and/or a checksum."""
    # fmt: on

    def __post_init__(self):
        self.tpdu_code: TPDU_Code = TPDU_Code.ER
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

    li = octets[0]
    if li == 0xFF:
        raise ValueError("Reserved TPDU length indicator")
    if li >= len(octets):
        raise ValueError(f"Invalid TPDU length indicator: li={li}, total={len(octets)}")

    tpdu_base = TPDU.from_octets(octets)
    tpdu_type = TPDU_TYPES.get(tpdu_base.tpdu_code, TPDU)
    fixed_size = getattr(tpdu_type, "TPDU_FIXED_SIZE", 1)
    if li < fixed_size:
        raise ValueError(
            "TPDU fixed part cannot be contained within header: "
            + f"li={li}, fixed_size={fixed_size}"
        )
    return tpdu_type.from_octets(octets)
