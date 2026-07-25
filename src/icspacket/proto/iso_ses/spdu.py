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
import enum

from collections.abc import Generator, Iterator
from typing import Any
from caterpillar.py import Field, StructDefMixin
from typing_extensions import Final, Self, override

from caterpillar.context import CTX_STREAM
from caterpillar.exception import DynamicSizeError
from caterpillar.fields import Enum, FieldMixin, Prefixed, uint8, uint16
from caterpillar.shared import getstruct
from caterpillar.shortcuts import F, BigEndian, f, struct, this, unpack
from caterpillar.types import uint8_t
from caterpillar.abc import _ContextLike

from icspacket.proto.iso_ses import values

# See ITU X.225 – Connection-oriented session protocol
# This protocol is a mess!


# Length Indicator (LI) field: precedes every parameter and SPDU parameter block
class LI(FieldMixin):
    """Implements the Length Indicator (clause 8.2.5) that reports, in octets,
    how large the parameter field attached to it is.

    That count only covers the parameter bytes themselves - it never includes
    the LI's own octets, nor any user-information octets that might follow.

    This class switches between two on-the-wire shapes depending on how big
    the value being described is:

    - sizes from 0 to 254 fit in a single octet, and a value of **0** means
      there is no parameter field at all;
    - anything from 255 up to 65535 instead uses three octets: a marker octet
      of ``0xFF`` (255), followed by the size as a big-endian 16-bit integer.

    """

    EXTENDED_INDICATOR: bytes = b"\xff"
    """Indicates an extended length indicator."""

    def __init__(self, extended: bool = True) -> None:
        self.extended: bool = extended
        # Backing field to read the extended 2-byte big-endian length (after 0xFF).
        self.__field: Field[int, int] = BigEndian + uint16

    def __size__(self, context: _ContextLike) -> int:
        # The LI can be either 1 or 3 octets depending on the value; callers must
        # compute size from the actual value using LI.octet_size().
        raise DynamicSizeError("LI size is either 1 or 3 depending on its value")

    def __type__(self) -> type[int]:
        return int

    def __unpack__(self, context: _ContextLike) -> int:
        stream = context[CTX_STREAM]
        first_octet: bytes = stream.read(1)
        # A value of 0-254 always fits in this single octet, so we can return
        # it directly.
        if first_octet != LI.EXTENDED_INDICATOR:
            return first_octet[0]

        # Anything bigger switches to the 3-octet form: the 0xFF marker we
        # just consumed is followed by the real length as a big-endian
        # 16-bit integer.
        return self.__field.__unpack__(context)

    def __pack__(self, obj: int, context: _ContextLike) -> None:
        stream = context[CTX_STREAM]
        if not self.extended or 0 <= obj <= 254:
            stream.write(bytes([obj & 255]))
            return

        stream.write(LI.EXTENDED_INDICATOR)
        # obj is only ever the parameter length itself: it never needs to
        # account for the LI's own octets or for trailing user-information
        # octets, so we can encode it as-is.
        self.__field.__pack__(obj, context)

    @staticmethod
    def octet_size(value: int) -> int:
        """Return the number of octets required to encode `value` as an LI."""
        return 1 if 0 <= value <= 254 else 3


LI_Extended: Final[LI] = LI()
"""Convenience alias for LI that allows extended form"""


# ---------------------------------------------------------------------------
# SPDU Codes (SI values)
# ---------------------------------------------------------------------------
class SPDU_Codes:
    """Mapping of SPDU SI codes to mnemonic names.

    .. note::
        Some codes in X.225 are **contextual aliases** (e.g., code 1 is used for
        both DT and GT) depending on category/semantics. This class preserves the
        code values.
    """

    # fmt: off
    EXCEPTION_REPORT_SPDU: int = 0         # (ER)
    DATA_TRANSFER_SPDU: int = 1            # (DT)
    GIVE_TOKENS_SPDU: int = 1              # (GT)  - shares code with DT in some contexts
    PLEASE_TOKENS_SPDU: int = 2            # (PT)
    EXPEDITED_SPDU: int = 5                # (EX)
    PREPARE_SPDU: int = 7                  # (PR)
    NOT_FINISHED_SPDU: int = 8             # (NF)
    FINISH_SPDU: int = 9                   # (FN)
    DISCONNECT_SPDU: int = 10              # (DN)
    REFUSE_SPDU: int = 12                  # (RF)
    CONNECT_SPDU: int = 13                 # (CN)
    ACCEPT_SPDU: int = 14                  # (AC)
    CONNECT_DATA_OVERFLOW_SPDU: int = 15   # (CDO)
    OVERFLOW_ACCEPT_SPDU: int = 16         # (OA)
    GIVE_TOKENS_CONFIRM_SPDU: int = 21     # (GTC)
    GIVE_TOKENS_ACK_SPDU: int = 22         # (GTA)
    ABORT_SPDU: int = 25                   # (AB)
    ACTIVITY_INTERRUPT_SPDU: int = 25      # (AI) - code reuse
    ABORT_ACCEPT_SPDU: int = 26            # (AA)
    ACTIVITY_INTERRUPT_ACK_SPDU: int = 26  # (AIA) - code reuse
    ACTIVITY_RESUME_SPDU: int = 29         # (AR)
    TYPED_DATA_SPDU: int = 33              # (TD)
    RESYNCHRONIZE_ACK_SPDU: int = 34       # (RA)
    ACTIVITY_END_SPDU: int = 41            # (AE)
    MAJOR_SYNC_POINT_SPDU: int = 41        # (MAP) - code reuse
    MAJOR_SYNC_ACK_SPDU: int = 42          # (MAA)
    ACTIVITY_START_SPDU: int = 45          # (AS)
    EXCEPTION_DATA_SPDU: int = 48          # (ED)
    MINOR_SYNC_POINT_SPDU: int = 49        # (MIP)
    MINOR_SYNC_ACK_SPDU: int = 50          # (MIA)
    RESYNCHRONIZE_SPDU: int = 53           # (RS)
    ACTIVITY_DISCARD_SPDU: int = 57        # (AD)
    ACTIVITY_DISCARD_ACK_SPDU: int = 58    # (ADA)
    CAPABILITY_DATA_SPDU: int = 61         # (CD)
    CAPABILITY_DATA_ACK_SPDU: int = 62     # (CDA)
    CLSES_UNIT_DATA: int = 64              # Connectionless Session (CL-mode) U-Data
    # fmt: on

    @staticmethod
    def has_user_info(code: int) -> bool:
        """Return True if **User Information Field** is defined for this SI code.

        According to X.225, only a subset of SPDUs carry user data directly. In the
        connection-oriented subset, these are primarily:

        - DATA TRANSFER (DT)
        - EXPEDITED (EX)
        - TYPED DATA (TD)

        Final presence is further constrained by **Enclosure Item** semantics for DT.
        """
        # fmt: off
        return code in (
            SPDU_Codes.DATA_TRANSFER_SPDU,  # DATA TRANSFER (DT)
            SPDU_Codes.EXPEDITED_SPDU,      # EXPEDITED (EX)
            SPDU_Codes.TYPED_DATA_SPDU,     # TYPED DATA (TD)
        )
        # fmt: on


# ---------------------------------------------------------------------------
# PGI (Parameter Group) Codes
# ---------------------------------------------------------------------------
class PGI_Code(enum.IntEnum):
    """Parameter Group Identifier (PGI) codes"""

    # NOTE - PGIs and PIs reserved for use by Recommendation T.62 are not
    # defined here.
    __struct__ = uint8

    # Reserved for extension = 0
    CONNECTION_ID = 1
    # Non-basic session capabilities = 2
    ACCEPT_ITEM = 5
    # Reserved for extension = 32
    LINKING_INFORMATION = 33
    # Reserved for extension = 64
    # Non-baseic teletex terminal capabilities = 65
    USER_DATA = 193
    EXTENDED_USER_DATA = 194


# ---------------------------------------------------------------------------
# Raw PI / PGI units (length-prefixed)
# ---------------------------------------------------------------------------
def _pi_from_context(value: int, context: _ContextLike) -> Any:
    pv_struct = values.PV_TYPES.get(value)
    if pv_struct:
        return Prefixed(LI_Extended, getstruct(pv_struct, pv_struct))

    # revert to raw bytes instead
    return Prefixed(LI_Extended)


@struct
class PI_Unit_Raw(StructDefMixin):
    """PI Unit (Parameter). (See X.225, §8.2.3)

    .. code-block:: text
        :caption: Wire format

        +--------+--------+-----------------...
        |  PI    |   LI   | parameter value (LI octets)
        +--------+--------+-----------------...


    - PI: 1 octet identifier for the parameter.
    - LI: Length Indicator (1 or 3 octets) for the parameter value.
    - value_raw: Bytes of the parameter value (no nested parsing here).
    """

    pi: uint8_t
    """PI field that identifies the parameter."""

    value: f[Any, F(this.pi) >> _pi_from_context]
    """Parameter value as raw bytes, length-prefixed by an LI, if not
    implemented in icspacket.iso_cosp.values.
    """


PI_Units_Raw = Prefixed(LI_Extended, PI_Unit_Raw[...])
"""Defines a list of PI Units (length-prefixed aggregate)."""


@struct
class PGI_Unit_Raw(StructDefMixin):  # unused
    """PGI Unit (Parameter Group). (See X.225, §8.2.2)

    .. code-block:: text
        :caption: Wire format

        +--------+--------+-----------------...
        |  PGI   |   LI   |   parameter field
        +--------+--------+-----------------...


    The parameter field of a PGI holds either a single parameter value on its
    own, or a run of one or more **PI units** stacked back to back (each
    still carrying its own LI prefix).

    This raw representation keeps the inner sequence as a list of PI_Unit_Raw.
    """

    pgi: f[PGI_Code | int, Enum(PGI_Code, uint8)]
    """PGI field identifying the parameter group."""

    value: f[list[PI_Unit_Raw], PI_Units_Raw]
    """Parameter field for the group: either a single value or multiple PI units."""


def _px_from_context(value: int, context: _ContextLike):
    """Dynamic selector for the value format of a parameter-like unit."""
    if value in list(PGI_Code):
        if value not in (PGI_Code.USER_DATA, PGI_Code.EXTENDED_USER_DATA):
            return PI_Units_Raw

    return _pi_from_context(value, context)


@struct
class Px_Unit(StructDefMixin):
    """Unified view over either a **PI** or a **PGI**."""

    pi: uint8_t
    """
    The 1-octet identifier. For PGIs this holds the PGI code; for PIs it is the
    PI.
    """

    value: f[Any, F(this.pi) >> _px_from_context]
    """
    - PGI: list of PI_Unit_Raw (unless USER_DATA/EXTENDED_USER_DATA)
    - PI: raw value bytes (LI-prefixed)
    """

    @property
    def is_group(self) -> bool:
        """True if `pi` is a known PGI code."""
        return self.pi in list(PGI_Code)

    @property
    def is_user_data(self) -> bool:
        """True if `pi` is USER_DATA or EXTENDED_USER_DATA."""
        return self.pi in (PGI_Code.USER_DATA, PGI_Code.EXTENDED_USER_DATA)

    def add_parameter(self, pi: int, value: list["Px_Unit"] | bytes | Any) -> "Px_Unit":
        """Add a parameter (PGI or PI) to the SPDU."""
        if not isinstance(self.value, list):
            raise TypeError("This parameter is not a group!")

        param = Px_Unit(pi, value)
        self.value.append(param)
        return param


Px_Units = Prefixed(LI_Extended, Px_Unit[...])
"""Defines a prefixed list of PGI or PI units (mixed)."""


# ---------------------------------------------------------------------------
# Raw SPDU (SI + parameter field)
# ---------------------------------------------------------------------------
@struct
class SPDU_Raw(StructDefMixin):
    """SPDU (raw representation). (See X.225, §8.2)

    .. code-block:: text
        :caption: Wire format

        +--------+--------+-----------------...
        |  SI    |   LI   | parameter field (LI octets)
        +--------+--------+-----------------...


    - `si` (1 octet): SPDU Identifier (SI) - code that identifies the SPDU type
      (e.g., CN/AC/DT/etc.).
    - `parameters_raw` (LI-prefixed): a mixed sequence of **PGI units** and/or
      **PI units** as defined for that SPDU type.

    .. important::

        The **User Information Field** (if any) is *not part* of this
        raw struct. It is handled by the higher-level `SPDU` wrapper because the
        presence rules depend on the SI code and items like the **Enclosure Item**.
    """

    si: uint8_t
    """The SI field that identifies the type of SPDU."""

    parameters_raw: f[list[Px_Unit], Px_Units]
    """The parameter field: a prefixed block of PGI units and/or PI units."""

    @staticmethod
    def from_octets(octets: bytes):
        """Deserialize a raw SPDU from octets (SI + LI + parameter field)."""
        return unpack(SPDU_Raw, octets)


# ---------------------------------------------------------------------------
# Concatenation categories (mapping to TSDU usage). (See X.225, §6.3.7)
# ---------------------------------------------------------------------------
class SPDU_Category(enum.IntEnum):
    """Groups SPDU types by how they may be packed into a TSDU. (See 6.3.7)"""

    CATEGORY_0 = 0
    """
    SPDUs that can either stand alone as a whole TSDU or ride along with one
    or more Category 2 SPDUs bundled into the same TSDU.
    """

    CATEGORY_1 = 1
    """
    SPDUs that always fill an entire TSDU by themselves and are never
    combined with other SPDUs.
    """

    CATEGORY_2 = 2
    """
    SPDUs that can never appear alone in a TSDU and must always be bundled
    together with another SPDU.
    """


# ---------------------------------------------------------------------------
# High-level SPDU wrapper (adds user-info detection and helpers)
# ---------------------------------------------------------------------------


class SPDU:
    """Convenience wrapper over :class:`SPDU_Raw` with user-info detection.

    **Structure (logical). (See X.225, 8.2)**

    On the wire, an SPDU is built from up to four consecutive parts: a
    one-octet SI that identifies the SPDU type, an LI (one or three octets)
    giving the size of what follows, a parameter field holding zero or more
    **PGI**/**PI** units sized by that LI, and - only for some SPDU types - a
    trailing **User Information Field**.

    :class:`SPDU_Raw` only models the SI, the LI and the parameter field.
    Whether a User Information Field follows can't be told from the LI alone:
    for some SPDU types (e.g., DT) that depends on control items such as the
    **Enclosure Item**, plus sequencing rules (See §7.11.2 and §8.3.*.4). This
    wrapper inspects the decoded parameters to work out whether any trailing
    octets should be treated as that User Information Field.
    """

    code: int
    """The SI code (a.k.a. SPDU type)."""

    category: SPDU_Category
    """Concatenation category (See 6.3.7)."""

    def __init__(self, code: int = 0, category: SPDU_Category | None = None) -> None:
        # public (modifiable) members
        self.code = code
        if category is None:
            if code in CATEGORY_2_NAMES:
                self.category = SPDU_Category.CATEGORY_2
            elif code in CATEGORY_1_NAMES:
                self.category = SPDU_Category.CATEGORY_1
            else:
                self.category = SPDU_Category.CATEGORY_0
        else:
            self.category = category

        # private members
        self.__parameters: list[Px_Unit] = []
        self.__user_information = b""

    def __add__(self, other: Self | list["SPDU"]) -> list["SPDU"]:
        """Allow `spdu1 + spdu2` or `spdu + [spdu2, spdu3]` to build lists quickly."""
        match other:
            case list():
                other.insert(0, self)
                return other
            case _:
                return [self, other]

    def __radd__(self, other: Self | list["SPDU"]) -> list["SPDU"]:
        """Symmetric addition to support `[spdu1] + spdu2`."""
        match other:
            case list():
                other.append(self)
                return other
            case _:
                return [other, self]

    @override
    def __repr__(self) -> str:
        fields: list[str] = []
        if self.parameters:
            fields.append(f"parameters={self.__parameters}")
        if self.user_information:
            fields.append(f"user_information={self.__user_information}")

        return f"<{self.name} [{self.category.value}] {', '.join(fields)}>"

    def __iter__(self) -> Iterator[Px_Unit]:
        """Iterate over **flattened parameters** (recursing into PGI contents)."""
        return self.iter_parameters()

    def add_parameter(self, pi: int, value: list[Px_Unit] | bytes | Any) -> Px_Unit:
        """Add a parameter (PGI or PI) to the SPDU."""
        param = Px_Unit(pi, value)
        self.parameters.append(param)
        return param

    @property
    def parameters(self) -> list[Px_Unit]:
        """The top-level mixed list of PGI/PI units for this SPDU."""
        return self.__parameters

    def iter_parameters(self) -> Generator[Px_Unit, None, None]:
        """Yield parameters **flattened**: for PGIs, yield their inner PIs."""
        for param in self.parameters:
            if isinstance(param.value, list):
                yield from param.value
            else:
                yield param

    @property
    def name(self) -> str:
        """A human-readable name for this SPDU type."""
        return spdu_name(self.code, self.category)

    def parameter_by_id(self, pi: int) -> Px_Unit | None:
        """Get a parameter by its PI code.

        :param pi: The PI code
        :type pi: int
        :return: The parameter, or None if not found
        :rtype: Px_Unit | None
        """
        for param in self.iter_parameters():
            if param.pi == pi:
                return param

    @property
    def has_user_information(self) -> bool:
        """Infer whether a **User Information Field** is expected/present.

        Rules applied

        1. Only certain SI codes **define** user information (DT/EX/TD). See
           `SPDU_Codes.has_user_info()`. If not defined, return False.
        2. Category 0 SPDUs are excluded here (mapping rules may reserve bytes).
        3. For **DATA TRANSFER (DT)** in particular:

           - If the **Enclosure Item** is present, its **bit 2** semantics affect
             whether user information should appear in a multi-SPDU sequence
             (See §8.3.11/13.4, §7.11.2). If Enclosure indicates “more follows”
             (bit 1 == 0), user information must be present on all but the last.

        :return: True if we should treat remaining octets as the User
            Information Field; False otherwise.
        :rtype: bool
        """
        # An SPDU's optional fourth part - the User Information Field - only
        # exists for the SPDU types that define one, namely:
        # - DATA TRANSFER (DT) SPDU
        # - EXPEDITED (EX) SPDU
        # - TYPED DATA (TD) SPDU
        # NOTE: there are some extra cases handled in the from_octets() method
        if (
            not SPDU_Codes.has_user_info(self.code)
            or self.category == SPDU_Category.CATEGORY_0
        ):
            return False

        has_user_info = True
        for param in self.iter_parameters():
            if param.pi == 25:  # Enclosure Item
                # Clause 8.3.{11,13}.4: the field carries whatever data the
                # SS-user supplied, and is required whenever the Enclosure
                # Item is missing, or present with its bit 2 cleared.
                if not isinstance(param.value, values.PV_EnclosureItem):
                    raise TypeError(f"Expected EnclosureItem, got {type(param.value)}")

                if param.value.end:
                    # Clause 7.11.2 only excuses the very last DATA TRANSFER
                    # SPDU of a multi-SPDU sequence from carrying user
                    # information; every other one in that sequence needs it.
                    # We recognize that excused "last SPDU" case here whenever
                    # the Enclosure Item shows this SPDU is not also the
                    # sequence's first one.
                    if not param.value.start:
                        has_user_info = False

        return has_user_info

    @property
    def user_information(self) -> bytes:
        """Raw bytes of the **User Information Field** (may be empty)."""
        return self.__user_information

    @user_information.setter
    def user_information(self, value: bytes):
        self.__user_information = value

    @staticmethod
    def from_octets(octets: bytes, category: SPDU_Category | None = None):
        """
        Deserialize an SPDU from `octets` and extract user-info if applicable.

        :param octets: The full SPDU octet string (SI + LI + parameters [+ user
            info?]).
        :type octets: bytes
        :param category: The concatenation category to associate with this
            SPDU., defaults to SPDU_Category.CATEGORY_2
        :type category: SPDU_Category, optional
        :return: A high-level SPDU with parameters and (if detected) user info.
        :rtype: SPDU
        """
        # Parse parameters first; user-info detection needs parameter semantics.
        raw_spdu = SPDU_Raw.from_octets(octets)
        spdu_len = unpack(LI_Extended, octets[1:])

        spdu = SPDU(raw_spdu.si, category)
        spdu.parameters.extend(raw_spdu.parameters_raw)

        if spdu.has_user_information:
            # Compute the start of user information:
            #   SI(1) + LI(octets) + parameter_field_length
            offset = 1 + LI.octet_size(spdu_len) + spdu_len
            spdu.__user_information = octets[offset:]

        return spdu

    def build(self) -> bytes:
        """Serialize the SPDU to octets."""
        spdu_raw = SPDU_Raw(self.code, self.parameters)
        spdu_data = bytes(spdu_raw)
        return spdu_data + self.user_information


def spdu_name(code: int, category: SPDU_Category = SPDU_Category.CATEGORY_2) -> str:
    names = {}
    match category:
        case SPDU_Category.CATEGORY_0:
            names = CATEGORY_0_NAMES
        case SPDU_Category.CATEGORY_1:
            names = CATEGORY_1_NAMES
        case SPDU_Category.CATEGORY_2:
            names = CATEGORY_2_NAMES

    return names.get(code, f"Unknown ({code:02X}) SPDU")


CATEGORY_0_NAMES = {
    1: "GIVE TOKENS (GT)",
    2: "PLEASE TOKENS (PT)",
}

CATEGORY_1_NAMES = {
    7: "PREPARE (PR) SPDU",
    8: "NOT FINISHED (NF) SPDU",
    9: "FINISH (FN) SPDU",
    10: "DISCONNECT (DN) SPDU",
    12: "REFUSE (RF) SPDU",
    13: "CONNECT (CN) SPDU",
    14: "ACCEPT (AC) SPDU",
    15: "CONNECT DATA OVERFLOW (CDO) SPDU",
    16: "OVERFLOW ACCEPT (OA) SPDU",
    21: "GIVE TOKENS CONFIRM (GTC) SPDU",
    22: "GIVE TOKENS ACK (GTA) SPDU",
    25: "ABORT (AB) SPDU",
    26: "ABORT ACCEPT (AA) SPDU",
    33: "TYPED DATA (TD) SPDU",
}

CATEGORY_2_NAMES = {
    1: "DATA TRANSFER (DT) SPDU",
    5: "EXPEDITED (EX) SPDU",
    25: "ACTIVITY INTERRUPT (AI) SPDU",
    26: "ACTIVITY INTERRUPT ACK (AIA) SPDU",
    29: "ACTIVITY RESUME (AR) SPDU",
    34: "RESYNCHRONIZE ACK (RA) SPDU",
    41: "ACTIVITY END (AE) SPDU / MAJOR SYNC POINT (MAP) SPDU",
    42: "MAJOR SYNC ACK (MAA) SPDU",
    45: "ACTIVITY START (AS) SPDU",
    48: "EXCEPTION DATA (ED) SPDU",
    49: "MINOR SYNC POINT (MIP) SPDU",
    50: "MINOR SYNC ACK (MIA) SPDU",
    53: "RESYNCHRONIZE (RS) SPDU",
    57: "ACTIVITY DISCARD (AD) SPDU",
    58: "ACTIVITY DISCARD ACK (ADA) SPDU",
    61: "CAPABILITY DATA (CD) SPDU",
    62: "CAPABILITY DATA ACK (CDA) SPDU",
}
