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
"""
APCI - Application Protocol Control Information (IEC 60870-5-104 framing).

(See IEC 60870-5-104, clause 5 - APCI structure)

Every message exchanged over an IEC 60870-5-104 TCP connection is wrapped in
an APCI frame: a fixed start byte, an automatically-computed length octet,
and a 4-octet control field whose own low bits pick one of three formats -

- **I-format** (Information transfer): carries an ASDU and both a send and
  a receive sequence number.
- **S-format** (Numbered supervisory function): a bare acknowledgment,
  carrying only a receive sequence number.
- **U-format** (Unnumbered control function): the ``STARTDT``/``STOPDT``/
  ``TESTFR`` connection handshake.
"""

from dataclasses import field

from caterpillar.py import (
    Bytes,
    ConstBytes,
    Invisible,
    Prefixed,
    StructDefMixin,
    f,
    struct,
    uint8,
)
from caterpillar.types import uint8_t

from icspacket.proto.iec104.const import (
    APCI_FORMAT_MASK,
    APCI_START,
    APCIFormat,
    UFormatFunction,
)

APCI_MAX_ASDU_LENGTH = 249
"""Largest ASDU payload (in octets) an I-format APCI frame should carry.

The length octet is a single byte (max 255), of which 4 octets are always
spent on the control field; 249 is the conservative, commonly used ceiling
for the 104 profile, leaving a small safety margin below the theoretical
``255 - 4 = 251``."""


@struct(kw_only=True)
class ControlField(StructDefMixin):
    """
    Raw 4-octet APCI control field.

    (See IEC 60870-5-104, clause 5.2)
    """

    octet1: uint8_t = 0
    octet2: uint8_t = 0
    octet3: uint8_t = 0
    octet4: uint8_t = 0

    @property
    def format(self) -> APCIFormat:
        """Which of the three APCI formats this control field follows."""
        if self.octet1 & 0b01 == 0:
            return APCIFormat.I_FORMAT
        is_u = (self.octet1 & APCI_FORMAT_MASK) == APCIFormat.U_FORMAT
        return APCIFormat.U_FORMAT if is_u else APCIFormat.S_FORMAT

    # -- I-format: N(S) / N(R) -------------------------------------------- #

    @property
    def send_seq(self) -> int:
        """``N(S)``: this frame's send sequence number (I-format only), a
        counter modulo 2**15."""
        return (self.octet1 >> 1) | (self.octet2 << 7)

    @send_seq.setter
    def send_seq(self, value: int) -> None:
        value &= 0x7FFF
        self.octet1 = (value & 0x7F) << 1
        self.octet2 = value >> 7

    @property
    def recv_seq(self) -> int:
        """``N(R)``: the last send sequence number acknowledged by the
        sender of this frame (I-format and S-format), a counter modulo
        2**15."""
        return (self.octet3 >> 1) | (self.octet4 << 7)

    @recv_seq.setter
    def recv_seq(self, value: int) -> None:
        value &= 0x7FFF
        self.octet3 = (value & 0x7F) << 1
        self.octet4 = value >> 7

    # -- U-format: handshake function flags ------------------------------- #

    @property
    def function(self) -> UFormatFunction:
        """U-format handshake function flags (``STARTDT``/``STOPDT``/
        ``TESTFR``, U-format only)."""
        return UFormatFunction(self.octet1 & ~APCI_FORMAT_MASK & 0xFF)

    @function.setter
    def function(self, value: UFormatFunction) -> None:
        self.octet1 = APCIFormat.U_FORMAT | int(value)
        self.octet2 = 0
        self.octet3 = 0
        self.octet4 = 0

    # -- constructors ------------------------------------------------------ #

    @staticmethod
    def new_i(send_seq: int, recv_seq: int) -> "ControlField":
        """Builds an I-format control field with the given sequence numbers."""
        control = ControlField()
        control.send_seq = send_seq
        control.recv_seq = recv_seq
        return control

    @staticmethod
    def new_s(recv_seq: int) -> "ControlField":
        """Builds an S-format control field acknowledging ``recv_seq``."""
        control = ControlField(octet1=int(APCIFormat.S_FORMAT))
        control.recv_seq = recv_seq
        return control

    @staticmethod
    def new_u(function: UFormatFunction) -> "ControlField":
        """Builds a U-format control field carrying ``function``."""
        control = ControlField()
        control.function = function
        return control


@struct(kw_only=True)
class APDU_Frame(StructDefMixin):
    """
    The variable-length part of an APCI frame: the control field plus,
    for I-format frames only, the raw encoded ASDU payload.

    This struct only exists to be wrapped by :class:`APCI`'s
    :class:`~caterpillar.fields.Prefixed` length field - use :class:`APCI`
    directly instead of this class.
    """

    control: ControlField = field(default_factory=ControlField)
    """The 4-octet control field, see :class:`ControlField`."""

    asdu: f[bytes, Bytes(...)] = b""
    """Raw encoded ASDU bytes. Only meaningful when ``control.format`` is
    :attr:`~icspacket.proto.iec104.const.APCIFormat.I_FORMAT`; empty for
    S-format and U-format frames."""


@struct(kw_only=True)
class APCI(StructDefMixin):
    """
    Application Protocol Control Information - the top-level TCP frame
    every IEC 60870-5-104 message is wrapped in.

    (See IEC 60870-5-104, clause 5.1)

    Because this class inherits :class:`~caterpillar.py.StructDefMixin`,
    it can be read straight off a socket with :meth:`from_bytes`, and an
    outgoing frame just needs :meth:`to_bytes` - the length octet is
    always computed automatically, there is no ``build()`` step.

    Examples
    --------
    >>> APCI.startdt_act().to_bytes()
    b'h\\x04\\x07\\x00\\x00\\x00'
    >>> APCI.i_format(send_seq=0, recv_seq=0, asdu=b"...").to_bytes()
    """

    start: f[bytes, ConstBytes(bytes([APCI_START]))] = Invisible()
    """Fixed start byte (``0x68``); not part of the constructor/repr since
    its value never varies."""

    frame: f[APDU_Frame, Prefixed(uint8, APDU_Frame)] = field(
        default_factory=APDU_Frame
    )
    """The control field and (I-format only) ASDU payload, automatically
    length-prefixed. See :class:`APDU_Frame`."""

    # -- ergonomic pass-through accessors ----------------------------------- #

    @property
    def control(self) -> ControlField:
        """Shortcut for ``self.frame.control``."""
        return self.frame.control

    @property
    def format(self) -> APCIFormat:
        """Shortcut for ``self.frame.control.format``."""
        return self.frame.control.format

    @property
    def asdu(self) -> bytes:
        """Shortcut for ``self.frame.asdu``."""
        return self.frame.asdu

    @asdu.setter
    def asdu(self, value: bytes) -> None:
        self.frame.asdu = value

    # -- constructors -------------------------------------------------------- #

    @staticmethod
    def i_format(send_seq: int, recv_seq: int, asdu: bytes) -> "APCI":
        """Builds an I-format APCI frame carrying ``asdu``."""
        return APCI(
            frame=APDU_Frame(control=ControlField.new_i(send_seq, recv_seq), asdu=asdu)
        )

    @staticmethod
    def s_format(recv_seq: int) -> "APCI":
        """Builds an S-format (bare acknowledgment) APCI frame."""
        return APCI(frame=APDU_Frame(control=ControlField.new_s(recv_seq)))

    @staticmethod
    def u_format(function: UFormatFunction) -> "APCI":
        """Builds a U-format (handshake) APCI frame carrying ``function``."""
        return APCI(frame=APDU_Frame(control=ControlField.new_u(function)))

    @staticmethod
    def startdt_act() -> "APCI":
        """Builds a ``STARTDT`` activation frame (client to server)."""
        return APCI.u_format(UFormatFunction.STARTDT_ACT)

    @staticmethod
    def startdt_con() -> "APCI":
        """Builds a ``STARTDT`` confirmation frame (server to client)."""
        return APCI.u_format(UFormatFunction.STARTDT_CON)

    @staticmethod
    def stopdt_act() -> "APCI":
        """Builds a ``STOPDT`` activation frame (client to server)."""
        return APCI.u_format(UFormatFunction.STOPDT_ACT)

    @staticmethod
    def stopdt_con() -> "APCI":
        """Builds a ``STOPDT`` confirmation frame (server to client)."""
        return APCI.u_format(UFormatFunction.STOPDT_CON)

    @staticmethod
    def testfr_act() -> "APCI":
        """Builds a ``TESTFR`` activation frame (either direction)."""
        return APCI.u_format(UFormatFunction.TESTFR_ACT)

    @staticmethod
    def testfr_con() -> "APCI":
        """Builds a ``TESTFR`` confirmation frame (either direction)."""
        return APCI.u_format(UFormatFunction.TESTFR_CON)
