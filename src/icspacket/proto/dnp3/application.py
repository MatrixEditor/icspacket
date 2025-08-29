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
# pyright: reportGeneralTypeIssues=false, reportUninitializedInstanceVariable=false, reportInvalidTypeForm=false
from caterpillar.options import S_ADD_BYTES
from caterpillar.shared import getstruct
from caterpillar.shortcuts import struct, bitfield
from caterpillar.fields import Bytes
from caterpillar.context import CTX_OBJECT
from caterpillar.model import unpack, EndGroup

from icspacket.proto.dnp3.const import (
    FunctionCode,
    APDU_RESP_FUNC_MAX,
    APDU_RESP_FUNC_MIN,
)

APDU_SEQ_MAX = 16
"""
Maximum border number of a sequence number within an APDU.

.. versionadded:: 0.2.0
"""

# /4.2.2.4 Application control octet
# Provides information needed to construct and reassemble multiple fragment
# messages and to indicate whether the receiver's Application Layer shall return
# an Application Layer confirmation message.
@bitfield
class ApplicationControl:
    """Represents the DNP3 Application Control octet (see DNP3 standard §4.2.2.4).

    This octet carries control information required for managing multi-fragment
    Application Layer messages, including message boundaries, sequencing, and
    whether acknowledgments are required.
    """

    # /4.2.2.4.1 FIR field
    first_fragment: 1 = False
    """Indicates whether this is the **first fragment** of a multi-fragment message."""

    # /4.2.2.4.2 FIN field
    final_fragment: 1 = False
    """Indicates whether this is the **final fragment** of a multi-fragment message."""

    # /4.2.2.4.3 CON field
    need_confirmation: 1 = False
    """Specifies whether the receiver's Application Layer shall return an
    **Application Layer confirmation message**."""

    # /4.2.2.4.4 UNS field
    unsolicited_response: 1 = False
    """Marks the fragment as containing an **unsolicited response** or a
    confirmation of an unsolicited response."""

    # /4.2.2.4.5 SEQ field
    sequence: 4 = 0
    """Message **sequence number** used to verify fragment ordering and detect
    duplicate fragments. Values increment modulo 16."""


def _apdu_is_response(context) -> bool:
    """Determine if the current APDU context corresponds to a **response message**.

    In DNP3, responses from outstations use function codes in the range
    ``129-255``.

    :param context: Parsing or decoding context that includes an APDU object.
    :type context: dict
    :return: ``True`` if the APDU is a response, ``False`` otherwise.
    :rtype: bool
    """
    obj = context[CTX_OBJECT]
    return APDU_RESP_FUNC_MIN <= obj.function <= APDU_RESP_FUNC_MAX


# /4.2.2.6 Internal indications
# The two bytes of the internal indication contain certain states and error
# conditions within the outstation.
@bitfield
class IIN:
    """Represents the DNP3 Internal Indications (IIN) bitfield (§4.2.2.6).

    This 2-byte structure communicates the outstation's internal states and
    error conditions, such as pending events, device restarts, or unsupported
    function codes.
    """

    device_restart: 1 = False
    """Indicates that the outstation has **restarted**."""

    device_trouble: 1 = False
    """An abnormal, device-specific condition exists in the outstation."""

    local_control: 1 = False
    """Indicates one or more of the outstation's points are in **local control
    mode**."""

    need_time: 1 = False
    """Indicates that the outstation requires **time synchronization**."""

    class_3_events: 1 = False
    """Indicates unreported **Class 3 events** are pending at the outstation."""

    class_2_events: 1 = False
    """Indicates unreported **Class 2 events** are pending at the outstation."""

    class_1_events: 1 = False
    """Indicates unreported **Class 1 events** are pending at the outstation."""

    broadcast: (1, EndGroup) = 0
    """A broadcast message was received."""

    # Second byte
    reserved: 2 = 0

    config_corrupt: 1 = False
    """The outstation detected **corrupt configuration data**. Support is optional."""

    already_executing: 1 = False
    """The requested operation is already executing. Support for this field is
    optional."""

    event_buffer_overflow: 1 = False
    """An **event buffer overflow** occurred, and at least one unconfirmed
    event was lost."""

    parameter_error: 1 = False
    """A **parameter error** was detected in the request."""

    object_unknown: 1 = False
    """The outstation does not support the requested **object(s)** in the request."""

    no_func_code_support: 1 = False
    """The outstation does not support the requested **function code**."""


# /4.2.2 Application Layer fragment structure
# Request and response fragments are similar and can be represented by a single APDU structure.
@struct(options=[S_ADD_BYTES])
class APDU:
    """Represents the **Application Protocol Data Unit (APDU)** in DNP3 (§4.2.2).

    APDUs encapsulate Application Layer fragments exchanged between masters and
    outstations. Both request and response fragments share the same structural
    format, consisting of an application control octet, a function code, internal
    indications, and object headers.

    .. versionchanged:: 0.2.0
        Added support for building an APDU using ``bytes(obj)``.
    """

    control: ApplicationControl = None
    """Application control octet providing fragment sequencing and acknowledgment
    control.
    """

    function: FunctionCode = FunctionCode.CONFIRM
    """Function code octet indicating the operation requested or responded to.
    Values range from ``0-128`` for requests and ``129-255`` for responses.
    """

    iin: getstruct(IIN) // _apdu_is_response = None
    """Internal indications (IIN) structure, included only in **response APDUs**.
    Encodes device states and error conditions.

    Parsing is conditional on the APDU being a response (function code ≥ 129).
    """

    objects: Bytes(...) = b""
    """Application objects included in the fragment. These represent the payload
    of the APDU and are parsed separately according to object headers.

    :meta: May include measurement data, control commands, or file operations.
    """

    def __post_init__(self):
        self.control = self.control or ApplicationControl()
        self.function = self.function or FunctionCode.CONFIRM
        self.iin = self.iin or IIN()

    @staticmethod
    def from_octets(octets: bytes):
        """Parse an APDU from a raw byte sequence."""
        return unpack(APDU, octets)
