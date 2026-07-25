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
from caterpillar.model import BitfieldDefMixin
from caterpillar.py import Bytes, bitfield, f

from icspacket.proto.dnp3.application import APDU

# Maximum border number of a sequence number
TPDU_SEQUENCE_MAX = 64

TPDU_APPLICATION_MAX_LENGTH = 249


@bitfield
class TPDU(BitfieldDefMixin):
    """
    Transport Protocol Data Unit (TPDU) representation for DNP3.

    This class models the Transport Header defined in IEEE 1815 (DNP3
    Specification), Section 8.2.1, as a single-byte prefix that this
    library attaches to the front of every transport segment, ahead of
    the Application Layer data it carries.

    Its flag bits and sequence number are what let this layer keep
    segments in order and reassemble them into a complete Application
    Layer message.
    """

    # fmt: off
    final_segment: f[bool, 1] = False
    """True when this segment is the last one making up the message."""

    first_segment: f[bool, 1] = False
    """True when this segment is the first one making up the message."""

    sequence: f[int, 6] = 0
    """Six-bit counter identifying this segment's place in the sequence,
    used by the receiver to keep segments in order."""

    app_fragment: f[bytes, Bytes(...)] = b""
    """
    Chunk of Application Layer data carried inside this TPDU.

    .. versionchanged:: 0.2.0
        Changed type to ``bytes`` in order to support segmentation.
    """
    # fmt: on

    @property
    def real_sequence(self) -> int:
        """
        Return the transport sequence number normalized to the 0-63 range
        used on the wire, applying the rollover behavior required according to
        Section 8.2.1.3 of the DNP3 Specification.

        :return: Normalized sequence number (0-63).
        :rtype: int
        """
        return self.sequence % TPDU_SEQUENCE_MAX

    @property
    def apdu(self) -> APDU:
        """
        Parses the APDU contained in the TPDU.

        .. versionadded:: 0.2.0
        """
        return APDU.from_octets(self.app_fragment)
