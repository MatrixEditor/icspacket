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
from dataclasses import field

from caterpillar.abc import _ContextLike
from caterpillar.context import CTX_OBJECT
from caterpillar.py import (
    S_ADD_BYTES,
    Bytes,
    EndGroup,
    Enum,
    StructDefMixin,
    bitfield,
    f,
    getstruct,
    struct,
    uint8,
)

from icspacket.proto.dnp3.const import (
    APDU_RESP_FUNC_MAX,
    APDU_RESP_FUNC_MIN,
    FunctionCode,
)

APDU_SEQ_MAX = 16
"""
Maximum border number of a sequence number within an APDU.

.. versionadded:: 0.2.0
"""


# /4.2.2.4 Application control octet
# Leading octet of every application fragment; its bits let the reassembler
# line up multi-fragment messages in order and tell the peer whether an
# application-layer confirmation needs to be sent back.
@bitfield
class ApplicationControl:
    """Represents the DNP3 Application Control octet (See DNP3 Specification, §4.2.2.4).

    This library models the octet as a bitfield so callers can read or set the
    fragmentation flags, the confirmation-request flag, and the rolling
    sequence number that accompany every application fragment exchanged
    between a master and an outstation.
    """

    # /4.2.2.4.1 FIR field
    first_fragment: f[bool, 1] = False
    """True when this fragment is the first piece of a multi-fragment message."""

    # /4.2.2.4.2 FIN field
    final_fragment: f[bool, 1] = False
    """True when this fragment is the last piece of a multi-fragment message."""

    # /4.2.2.4.3 CON field
    need_confirmation: f[bool, 1] = False
    """Requests that the peer's Application Layer send back an
    **Application Layer confirmation message** once the fragment is processed."""

    # /4.2.2.4.4 UNS field
    unsolicited_response: f[bool, 1] = False
    """True when the fragment is an **unsolicited response** (or the
    confirmation of one) rather than something the master asked for."""

    # /4.2.2.4.5 SEQ field
    sequence: f[int, 4] = 0
    """Rolling **sequence number** (wraps modulo 16) that this library uses to
    line up fragments belonging to the same message and to catch duplicates."""


def _apdu_is_response(context: _ContextLike) -> bool:
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
# Two-byte bitfield an outstation attaches to its responses to surface its
# own status and error flags back to the master.
@bitfield
class IIN:
    """Represents the DNP3 Internal Indications (IIN) bitfield (See DNP3 Specification, §4.2.2.6).

    This library exposes the two-byte IIN field as individual boolean flags so
    callers can inspect an outstation's status and error conditions - such as
    pending events, a recent restart, or an unsupported function code -
    without manually decoding the raw bits.
    """

    device_restart: f[bool, 1] = False
    """Set by the outstation after it has **restarted**, so the master can
    notice that a reset happened since the last exchange."""

    device_trouble: f[bool, 1] = False
    """Flags an abnormal condition on the outstation whose exact meaning is
    device-specific (vendor-defined)."""

    local_control: f[bool, 1] = False
    """Set when one or more of the outstation's points are currently being
    driven by **local control** rather than by the master."""

    need_time: f[bool, 1] = False
    """Set by the outstation to ask the master to perform **time
    synchronization**."""

    class_3_events: f[bool, 1] = False
    """Set while the outstation is holding **Class 3 events** that have not
    yet been reported."""

    class_2_events: f[bool, 1] = False
    """Set while the outstation is holding **Class 2 events** that have not
    yet been reported."""

    class_1_events: f[bool, 1] = False
    """Set while the outstation is holding **Class 1 events** that have not
    yet been reported."""

    broadcast: f[int, (1, EndGroup)] = 0
    """Set when the request that triggered this response was sent to the
    broadcast address."""

    # Second byte
    reserved: f[int, 2] = 0

    config_corrupt: f[bool, 1] = False
    """Set when the outstation finds its own **configuration data** to be
    corrupted; implementing this check is optional."""

    already_executing: f[bool, 1] = False
    """Set when the outstation is still carrying out a previously requested
    operation of the same kind; support for this flag is optional."""

    event_buffer_overflow: f[bool, 1] = False
    """Set when the outstation's **event buffer** filled up and it had to
    discard at least one unconfirmed event."""

    parameter_error: f[bool, 1] = False
    """Set when the outstation rejects the request because one of its
    **parameters** was invalid."""

    object_unknown: f[bool, 1] = False
    """Set when the outstation cannot recognize or does not implement one or
    more of the **objects** referenced by the request."""

    no_func_code_support: f[bool, 1] = False
    """Set when the outstation has no implementation for the **function
    code** carried by the request."""


# /4.2.2 Application Layer fragment structure
# Requests and responses share the same on-the-wire layout, so a single APDU
# struct below models both directions.
@struct(options=[S_ADD_BYTES])
class APDU(StructDefMixin):
    """Represents the **Application Protocol Data Unit (APDU)** in DNP3 (See DNP3 Specification, §4.2.2).

    This struct models one application-layer fragment, regardless of whether
    it was sent by a master or an outstation - both directions reuse the same
    on-the-wire layout of a control octet, a function code, an optional
    internal-indications field, and the encoded application objects that
    follow.

    .. versionchanged:: 0.2.0
        Added support for building an APDU using ``bytes(obj)``.
    """

    control: ApplicationControl = field(default_factory=ApplicationControl)
    """The fragment's control octet, modeled by :class:`ApplicationControl`,
    holding the fragmentation/confirmation flags and the sequence number.
    """

    function: f[FunctionCode | int, Enum(FunctionCode, uint8)] = FunctionCode.CONFIRM
    """Single-octet operation code carried by this fragment. Request codes
    fall in ``0-128``; response codes fall in ``129-255``.
    """

    iin: f[IIN, getstruct(IIN) // _apdu_is_response] = field(default_factory=IIN)
    """Outstation status/error flags, modeled by :class:`IIN`.

    Only response fragments carry this field, so it is left unset while
    decoding requests; parsing it is conditional on the function code
    indicating a response (≥ 129).
    """

    objects: f[bytes, Bytes(...)] = b""
    """Raw encoded application objects making up this fragment's payload.

    This library keeps the objects as opaque bytes here; use the
    object-header parsing helpers to decode individual entries.

    :meta: May include measurement data, control commands, or file operations.
    """

    @staticmethod
    def from_octets(octets: bytes):
        """Parse an APDU from a raw byte sequence."""
        return APDU.from_bytes(octets)
