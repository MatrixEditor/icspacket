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
TSDU (Transport Service Data Unit) Handling
-------------------------------------------

This module implements parsing and building logic for **TSDUs** as defined in
§8.1 of the X.225 specification.

A TSDU is the *unit of data* exchanged between the session layer and the
transport layer. It may contain:

- One SPDU mapped directly to a TSDU (Category 1)
- Multiple SPDUs concatenated (Category 0 + Category 2, or multiple Category 2s)
- In special cases, only a Category 0 SPDU

Concatenation rules are defined in §6.3.7:

- **Category 0** SPDUs may be mapped one-to-one onto a TSDU *or*
    concatenated with one or more Category 2 SPDUs.
- **Category 1** SPDUs are always mapped one-to-one to a TSDU (no
    concatenation).
- **Category 2** SPDUs are never mapped one-to-one — they appear only after
    a Category 0 SPDU in the same TSDU.

.. seealso::

    - §6.3.7 Concatenation rules
    - §8.1 TSDU structure
    - §8.2 SPDU structure
"""

from collections.abc import Iterator
from caterpillar.model import unpack

from icspacket.proto.iso_ses.spdu import LI, SPDU, SPDU_Category, SPDU_Codes, LI_Extended


class TSDU:
    """TSDU container for one or more concatenated SPDUs — X.225 §8.1

    Usage:

    >>> tsdu = TSDU.from_octets(data)   # Parse a raw TSDU from bytes
    >>> tsdu.build()                    # Encode back to raw bytes
    """

    def __init__(self) -> None:
        self.__spdus = []

    def __repr__(self) -> str:
        return f"TSDU(spdus={self.spdus})"

    def __len__(self) -> int:
        return len(self.spdus)

    def __iter__(self) -> Iterator[SPDU]:
        return iter(self.spdus)

    def add_spdu(self, code: int, category: SPDU_Category | None = None) -> SPDU:
        """Create a new SPDU and append it to this TSDU.

        :param code: The SPDU code (see `SPDU_Codes`).
        :type code: int
        :param category: The SPDU category, defaults to False
        :type category: SPDU_Category, optional
        :return: The newly created SPDU object.
        :rtype: SPDU
        """
        spdu = SPDU(code, category)
        self.spdus.append(spdu)
        return spdu

    @property
    def spdus(self) -> list[SPDU]:
        """List of SPDUs contained in this TSDU.

        This property returns a direct reference to the internal list, so it can be
        iterated over or modified directly.
        """
        return self.__spdus

    @staticmethod
    def from_octets(octets: bytes):
        """Decode a raw TSDU from its octet representation.

        :param octets: The raw TSDU data as received from the transport layer.
        :type octets: bytes
        :raises ValueError: If a Category 0 SPDU has a non-zero length, or or if
            any SPDU length is invalid (extends beyond buffer).
        :return: A fully parsed TSDU object containing one or more SPDUs.
        :rtype: TSDU
        """
        # fmt: off
        tsdu = TSDU()

        # --- Step 1: Detect Category 0 SPDU ---
        si = octets[0]  # SPDU Identifier
        offset = 0           # Current parsing position in TSDU buffer
        index = 0            # SPDU sequence index within TSDU

        # Special case: Category 0 types (PLEASE_TOKENS, GIVE_TOKENS)
        if si in (SPDU_Codes.PLEASE_TOKENS_SPDU, SPDU_Codes.GIVE_TOKENS_SPDU):
            tsdu.spdus.append(SPDU(si, category=SPDU_Category.CATEGORY_0))
            if octets[1] != 0:  # length MUST be null
                raise ValueError("Invalid length of Category 0 SPDU")

            offset = 2      # Skip SI + LI
            index = 1

        # --- Step 2: Parse remaining SPDUs ---
        while offset < len(octets):
            # Read LI for this SPDU (octets[offset+1:] = LI + rest)
            li = unpack(LI_Extended, octets[offset + 1 :])
            if li > len(octets) or 2 + li > len(octets):
                raise ValueError(
                    f"Invalid length of SPDU [{index}] at offset {offset}+1"
                )

            # Parse SPDU without immediately decoding user information
            spdu = SPDU.from_octets(octets[offset:])
            category = SPDU_Category.CATEGORY_1
            if len(tsdu.spdus) and tsdu.spdus[0].category == SPDU_Category.CATEGORY_0:
                category = SPDU_Category.CATEGORY_2

            spdu.category = category
            # Advance offset:
            #   LI length (LI.octet_size) + LI value + SI (1 byte)
            #   + any trailing user information bytes
            offset += li + 1 + LI.octet_size(li) + len(spdu.user_information)
            tsdu.spdus.append(spdu)

        # fmt: on
        return tsdu

    def build(self) -> bytes:
        """Assemble the TSDU into its raw octet representation.

        :return: The encoded TSDU, produced by concatenating each SPDU's octet
            representation.
        :rtype: bytes
        """
        return b"".join([spdu.build() for spdu in self.spdus])
