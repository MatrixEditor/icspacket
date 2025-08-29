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
from caterpillar.fields import Bytes
from caterpillar.shortcuts import opt, bitfield

from icspacket.proto.dnp3.application import APDU

# Maximum border number of a sequence number
TPDU_SEQUENCE_MAX = 64

TPDU_APPLICATION_MAX_LENGTH = 249

@bitfield(options=[opt.S_ADD_BYTES])
class TPDU:
    """
    Transport Protocol Data Unit (TPDU) representation for DNP3.

    This class implements the Transport Header defined in IEEE 1815
    (DNP3 Specification), Section 8.2.1. The header is the first byte
    of every transport segment and precedes the Application Layer data.

    The transport header fields support proper sequencing, ordering,
    and fragment reassembly for Application Layer messages.
    """

    # fmt: off
    final_segment : 1 = False
    """Indicates whether this is the final (last) transport segment."""

    first_segment : 1 = False
    """Indicates whether this is the first transport segment."""

    sequence : 6 = 0
    """6-bit sequence number for ordering transport segments."""

    app_fragment : Bytes(...) = b""
    """
    Application Layer fragment associated with this TPDU.

    .. versionchanged:: 0.2.0
        Changed type to ``bytes`` in order to support segmentation.
    """
    # fmt: on

    @property
    def real_sequence(self) -> int:
        """
        Compute the normalized sequence number modulo 64.

        This property ensures compliance with the rollover rule in
        Section 8.2.1.3 of the DNP3 specification.

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