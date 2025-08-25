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
import enum

from collections.abc import Generator, Iterator
from typing import Any
from typing_extensions import Self

from caterpillar.context import CTX_STREAM
from caterpillar.exception import DynamicSizeError
from caterpillar.fields import FieldMixin, Prefixed, uint8, uint16
from caterpillar.options import S_ADD_BYTES
from caterpillar.shared import getstruct
from caterpillar.shortcuts import F, BigEndian, struct, this, unpack

from icspacket.proto.iso_ses import values

# [ITU X.225] – Connection-oriented session protocol
# This protocol is a mess!


# 8.2.5 Length indicator field
class LI(FieldMixin):
    """8.2.5 Length indicator field

    Encodes/decodes the length, in octets, of the associated parameter field.
    The LI value does **not** include the LI octets themselves nor any subsequent
    *user information* octets.

    Encoding forms:

    - **Short form (1 octet)**: values in range 0..254 are encoded in one octet.
      A value of **0** indicates that the associated parameter field is absent.
    - **Extended form (3 octets)**: values in range 255..65535 are encoded as:
      0xFF | <length: uint16 big-endian> i.e., first octet 1111 1111 (255),
      followed by two octets carrying the length.

    """

    EXTENDED_INDICATOR = b"\xff"
    """Indicates an extended length indicator."""

    def __init__(self, extended: bool = True) -> None:
        self.extended = extended
        # Backing field to read the extended 2-byte big-endian length (after 0xFF).
        self.__field = BigEndian + uint16

    def __size__(self, context) -> int:
        # The LI can be either 1 or 3 octets depending on the value; callers must
        # compute size from the actual value using LI.octet_size().
        raise DynamicSizeError("LI size is either 1 or 3 depending on its value")

    def __type__(self) -> type[int]:
        return int

    def __unpack__(self, context) -> int:
        stream = context[CTX_STREAM]
        first_octet = stream.read(1)
        # LI fields indicating lengths within the range 0-254 shall comprise one
        # octet.
        if first_octet != LI.EXTENDED_INDICATOR:
            return first_octet[0]

        # LI fields indicating lengths within the range 255-65 535 shall comprise
        # three octets. The first octet shall be coded 1111 1111 and the second
        # and third octets shall contain the length of the associated parameter
        # field with the high order bits in the first of these two octets.
        return self.__field.__unpack__(context)

    def __pack__(self, obj: int, context) -> None:
        stream = context[CTX_STREAM]
        if not self.extended or 0 <= obj <= 254:
            return stream.write(bytes([obj & 255]))

        stream.write(LI.EXTENDED_INDICATOR)
        # NOTE: Per spec, LI does NOT include its own octets nor any following
        # user information octets. We simply encode the numeric value here
        self.__field.__pack__(obj, context)

    @staticmethod
    def octet_size(value: int) -> int:
        """Return the number of octets required to encode `value` as an LI."""
        return 1 if 0 <= value <= 254 else 3


LI_Extended = LI()
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
    EXCEPTION_REPORT_SPDU = 0         # (ER)
    DATA_TRANSFER_SPDU = 1            # (DT)
    GIVE_TOKENS_SPDU = 1              # (GT)  — shares code with DT in some contexts
    PLEASE_TOKENS_SPDU = 2            # (PT)
    EXPEDITED_SPDU = 5                # (EX)
    PREPARE_SPDU = 7                  # (PR)
    NOT_FINISHED_SPDU = 8             # (NF)
    FINISH_SPDU = 9                   # (FN)
    DISCONNECT_SPDU = 10              # (DN)
    REFUSE_SPDU = 12                  # (RF)
    CONNECT_SPDU = 13                 # (CN)
    ACCEPT_SPDU = 14                  # (AC)
    CONNECT_DATA_OVERFLOW_SPDU = 15   # (CDO)
    OVERFLOW_ACCEPT_SPDU = 16         # (OA)
    GIVE_TOKENS_CONFIRM_SPDU = 21     # (GTC)
    GIVE_TOKENS_ACK_SPDU = 22         # (GTA)
    ABORT_SPDU = 25                   # (AB)
    ACTIVITY_INTERRUPT_SPDU = 25      # (AI) — code reuse
    ABORT_ACCEPT_SPDU = 26            # (AA)
    ACTIVITY_INTERRUPT_ACK_SPDU = 26  # (AIA) — code reuse
    ACTIVITY_RESUME_SPDU = 29         # (AR)
    TYPED_DATA_SPDU = 33              # (TD)
    RESYNCHRONIZE_ACK_SPDU = 34       # (RA)
    ACTIVITY_END_SPDU = 41            # (AE)
    MAJOR_SYNC_POINT_SPDU = 41        # (MAP) — code reuse
    MAJOR_SYNC_ACK_SPDU = 42          # (MAA)
    ACTIVITY_START_SPDU = 45          # (AS)
    EXCEPTION_DATA_SPDU = 48          # (ED)
    MINOR_SYNC_POINT_SPDU = 49        # (MIP)
    MINOR_SYNC_ACK_SPDU = 50          # (MIA)
    RESYNCHRONIZE_SPDU = 53           # (RS)
    ACTIVITY_DISCARD_SPDU = 57        # (AD)
    ACTIVITY_DISCARD_ACK_SPDU = 58    # (ADA)
    CAPABILITY_DATA_SPDU = 61         # (CD)
    CAPABILITY_DATA_ACK_SPDU = 62     # (CDA)
    CLSES_UNIT_DATA = 64              # Connectionless Session (CL-mode) U-Data
    # fmt: on

    @staticmethod
    def has_user_info(code: int) -> bool:
        """Return True if **User Information Field** is defined for this SI code.

        Per X.225, only a subset of SPDUs carry user data directly. In the
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
def _pi_from_context(pi: int, context):
    pv_struct = values.PV_TYPES.get(pi)
    if pv_struct:
        return Prefixed(LI_Extended, getstruct(pv_struct, pv_struct))

    # revert to raw bytes instead
    return Prefixed(LI_Extended)


@struct(options=[S_ADD_BYTES])
class PI_Unit_Raw:
    """PI Unit (Parameter) — X.225 §8.2.3

    .. code-block:: text
        :caption: Wire format

        +--------+--------+-----------------...
        |  PI    |   LI   | parameter value (LI octets)
        +--------+--------+-----------------...


    - PI: 1 octet identifier for the parameter.
    - LI: Length Indicator (1 or 3 octets) for the parameter value.
    - value_raw: Bytes of the parameter value (no nested parsing here).
    """

    pi: uint8
    """PI field that identifies the parameter."""

    value: F(this.pi) >> _pi_from_context
    """Parameter value as raw bytes, length-prefixed by an LI, if not
    implemented in icspacket.iso_cosp.values.
    """


PI_Units_Raw = Prefixed(LI_Extended, PI_Unit_Raw[...])
"""Defines a list of PI Units (length-prefixed aggregate)."""


@struct(options=[S_ADD_BYTES])
class PGI_Unit_Raw:  # unused
    """PGI Unit (Parameter Group) — X.225 §8.2.2

    .. code-block:: text
        :caption: Wire format

        +--------+--------+-----------------...
        |  PGI   |   LI   |   parameter field
        +--------+--------+-----------------...


    The parameter field of a PGI may be:

    -  1) a **single parameter value**, or
    -  2) one or more **PI units** (each PI is again LI-prefixed).

    This raw representation keeps the inner sequence as a list of PI_Unit_Raw.
    """

    pgi: PGI_Code
    """PGI field identifying the parameter group."""

    value: PI_Units_Raw
    """Parameter field for the group: either a single value or multiple PI units."""


def _px_from_context(pi: int, context):
    """Dynamic selector for the value format of a parameter-like unit."""
    if pi in list(PGI_Code):
        if pi not in (PGI_Code.USER_DATA, PGI_Code.EXTENDED_USER_DATA):
            return PI_Units_Raw

    return _pi_from_context(pi, context)


@struct
class Px_Unit:
    """Unified view over either a **PI** or a **PGI**."""

    pi: uint8
    """
    The 1-octet identifier. For PGIs this holds the PGI code; for PIs it is the
    PI.
    """

    value: F(this.pi) >> _px_from_context
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
@struct(options=[S_ADD_BYTES])
class SPDU_Raw:
    """SPDU (raw representation) — X.225 §8.2

    .. code-block:: text
        :caption: Wire format

        +--------+--------+-----------------...
        |  SI    |   LI   | parameter field (LI octets)
        +--------+--------+-----------------...


    - `si` (1 octet): SPDU Identifier (SI) — code that identifies the SPDU type
      (e.g., CN/AC/DT/etc.).
    - `parameters_raw` (LI-prefixed): a mixed sequence of **PGI units** and/or
      **PI units** as defined for that SPDU type.

    .. important::

        The **User Information Field** (if any) is *not part* of this
        raw struct. It is handled by the higher-level `SPDU` wrapper because the
        presence rules depend on the SI code and items like the **Enclosure Item**.
    """

    si: uint8
    """The SI field that identifies the type of SPDU."""

    parameters_raw: Px_Units
    """The parameter field: a prefixed block of PGI units and/or PI units."""

    @staticmethod
    def from_octets(octets: bytes):
        """Deserialize a raw SPDU from octets (SI + LI + parameter field)."""
        return unpack(SPDU_Raw, octets)


# ---------------------------------------------------------------------------
# Concatenation categories (mapping to TSDU usage) — X.225 §6.3.7
# ---------------------------------------------------------------------------
class SPDU_Category(enum.IntEnum):
    """SPDU categories for transport concatenation behavior — 6.3.7."""

    CATEGORY_0 = 0
    """
    a) Category 0 SPDUs which may be mapped one-to-one onto a TSDU or may be
       concatenated with one or more category 2 SPDUs;
    """

    CATEGORY_1 = 1
    """
    b) Category 1 SPDUs which are always mapped one-to-one onto a TSDU;
    """

    CATEGORY_2 = 2
    """
    c) Category 2 SPDUs which are never mapped one-to-one onto a TSDU.
    """


# ---------------------------------------------------------------------------
# High-level SPDU wrapper (adds user-info detection and helpers)
# ---------------------------------------------------------------------------


class SPDU:
    """Convenience wrapper over :class:`SPDU_Raw` with user-info detection.

    **Structure (logical) — X.225 8.2**

    SPDUs shall contain, in order:

    - a) SI — identifies the SPDU type (1 octet).
    - b) LI — length (in octets) of the **parameter field** (1 or 3 octets).
    - c) Parameter field — zero or more **PGI**/**PI** units (the block whose
    -    length is provided by the LI).
    - d) **User Information Field** — if defined for the SPDU type and present.

    :class:`SPDU_Raw` models (a)-(c). Whether (d) exists cannot be decided by
    just looking at the LI, because for some SPDU types (e.g., DT) the presence
    of user information depends on control items like the **Enclosure Item** and
    sequence rules (§7.11.2 and §8.3.*.4). This wrapper inspects parameters to
    decide if trailing octets belong to the User Information Field.
    """

    code: int
    """The SI code (a.k.a. SPDU type)."""

    category: SPDU_Category
    """Concatenation category (6.3.7)."""

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
        self.__parameters = []
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

    def __repr__(self) -> str:
        fields = []
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
             (§8.3.11/13.4, §7.11.2). If Enclosure indicates “more follows”
             (bit 1 == 0), user information must be present on all but the last.

        :return: True if we should treat remaining octets as the User
            Information Field; False otherwise.
        :rtype: bool
        """
        # d) the user information field, if defined for the SPDU and if present.
        # User Information Field is defined for the following SPDUs:
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
                # 8.3.{11,13}.4
                # The User Information Field, if present, shall contain user
                # data supplied by the SS-user. The User Information Field shall
                # be present if the Enclosure Item is not present, or has bit 2
                # = 0.
                if not isinstance(param.value, values.PV_EnclosureItem):
                    raise TypeError(f"Expected EnclosureItem, got {type(param.value)}")

                if param.value.end:
                    # 7.11.2 Sending the DATA TRANSFER SPDU
                    # All DATA TRANSFER SPDUs, except the last DATA TRANSFER
                    # SPDU in a sequence greater than one, must have user
                    # information.
                    #
                    # That means the flags should indicate that this is not the
                    # last SPDU.
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
    41: "ACTIVITY END (AE) SPDU",
    41: "MAJOR SYNC POINT (MAP) SPDU",
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
