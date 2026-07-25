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
"""
ASDU - Application Service Data Unit (IEC 60870-5-104 application layer).

(See IEC 60870-5-101, clause 7.2 - Application Service Data Unit)
"""

from dataclasses import field

from caterpillar.py import (
    Bytes,
    Enum,
    LittleEndian,
    StructDefMixin,
    bitfield,
    f,
    struct,
    uint8,
)
from caterpillar.types import uint8_t, uint16_t

from icspacket.proto.iec104.const import TypeID
from icspacket.proto.iec104.objects.coding import (
    InformationObject,
    pack_information_objects,
    unpack_information_objects,
)

__all__ = [
    "ASDU",
    "ASDU_Header",
    "CauseOfTransmissionField",
    "InformationObject",
    "VariableStructureQualifier",
]


# /7.2.1.1 Variable structure qualifier
@bitfield
class VariableStructureQualifier:
    """
    Variable Structure Qualifier (VSQ).

    Tells a decoder how many information objects follow the ASDU header
    and whether they share one implicit, incrementing address or each
    carry their own.
    (See IEC 60870-5-101, clause 7.2.2)
    """

    sq: f[bool, 1] = False
    """``SQ`` bit. When ``True``, only the first information object
    carries an explicit Information Object Address; the rest are
    implicitly addressed ``ioa + 1``, ``ioa + 2``, etc. ("sequence" of
    same-kind objects, e.g. a contiguous block of measured values). When
    ``False``, every object carries its own address."""

    number: f[int, 7] = 0
    """Number of information objects (or, when ``sq`` is set, elements
    within the single addressed sequence) following the header."""


# /7.2.1.2 Cause of transmission
@bitfield
class CauseOfTransmissionField:
    """
    Cause Of Transmission (COT) octet.

    Wraps a :class:`~icspacket.proto.iec104.const.CauseOfTransmission`
    value together with the test and negative-confirmation flags.
    (See IEC 60870-5-101, clause 7.2.3)
    """

    test: f[bool, 1] = False
    """Marks the ASDU as a test frame - the outstation processes it
    normally but the master should not act on the result."""

    negative: f[bool, 1] = False
    """``P/N``: ``True`` marks a negative confirmation (the requested
    activation/command could not be performed)."""

    cause: f[int, 6] = 0
    """The reason this ASDU was sent; interpret with
    :class:`~icspacket.proto.iec104.const.CauseOfTransmission`."""


@struct(order=LittleEndian, kw_only=True)
class ASDU_Header(StructDefMixin):
    """
    Fixed 6-octet ASDU header.

    (See IEC 60870-5-101, clause 7.2 and clause 7.2.4 - Common address of
    ASDU)

    The 104 profile always uses the 2-octet forms of both the Cause Of
    Transmission's originator address and the Common Address of ASDU
    (unlike 101, where 1-octet forms are also legal) - this struct only
    implements the 104 forms, matching this module's TCP-only scope.
    """

    type_id: f[TypeID | int, Enum(TypeID, uint8)] = TypeID.M_SP_NA_1
    """Identifies the structure and semantics of the objects that follow,
    see :class:`~icspacket.proto.iec104.const.TypeID`."""

    vsq: VariableStructureQualifier = field(default_factory=VariableStructureQualifier)
    """Variable Structure Qualifier, see :class:`VariableStructureQualifier`."""

    cot: CauseOfTransmissionField = field(default_factory=CauseOfTransmissionField)
    """Cause Of Transmission, see :class:`CauseOfTransmissionField`."""

    originator_address: uint8_t = 0
    """Identifies the originating controlling station in multi-master
    setups; ``0`` when only one master is used."""

    common_address: uint16_t = 0
    """Station (sector) address this ASDU concerns; ``0xFFFF`` addresses
    all stations (global/broadcast, only valid for select ASDU types)."""

    def __post_init__(self):
        self.vsq = self.vsq or VariableStructureQualifier()
        self.cot = self.cot or CauseOfTransmissionField()


@struct(order=LittleEndian, kw_only=True)
class ASDU(StructDefMixin):
    """
    Application Service Data Unit (ASDU).

    (See IEC 60870-5-101, clause 7.2)

    Carries a :class:`ASDU_Header` plus the raw, not-yet-decoded
    information-object bytes; use :meth:`build`/:meth:`decode_objects` to
    go from/to a :class:`~icspacket.proto.iec104.objects.coding.InformationObject`
    list.
    """

    header: ASDU_Header = field(default_factory=ASDU_Header)
    """The fixed 6-octet header, see :class:`ASDU_Header`."""

    objects: f[bytes, Bytes(...)] = b""
    """Raw, undecoded information-object bytes. Populated/consumed via
    :meth:`build`/:meth:`decode_objects`."""

    def __post_init__(self):
        self.header = self.header or ASDU_Header()

    def build(self, objects: list[InformationObject], sq: bool = False) -> bytes:
        """
        Encode ``objects`` and serialize the whole ASDU.

        Keeps :attr:`ASDU_Header.vsq`'s ``number``/``sq`` fields in sync
        with ``objects``/``sq`` before packing, recomputing these derived
        header fields immediately before packing.

        :param objects: The information objects to encode, in wire order.
        :param sq: Whether to use the sequential-address form: see
            :attr:`VariableStructureQualifier.sq`.
        :raises ValueError: If ``len(objects)`` does not fit in the VSQ's
            7-bit ``number`` field (i.e. more than 127 objects).
        :return: The fully encoded ASDU bytes.
        """
        if len(objects) > 0x7F:
            raise ValueError(
                f"Too many information objects ({len(objects)}); "
                + "VSQ.number is only 7 bits wide (max 127)"
            )

        self.header.vsq.number = len(objects)
        self.header.vsq.sq = sq
        self.objects = pack_information_objects(self.header.type_id, objects, sq=sq)
        return self.to_bytes()

    def decode_objects(self) -> list[InformationObject]:
        """
        Decode :attr:`objects` according to the header's Type-ID/VSQ.

        :raises ValueError: If the header's Type-ID has no registered
            information-element struct (see
            :func:`~icspacket.proto.iec104.objects.coding.asdu_type`).
        :return: The decoded information objects.
        """
        return unpack_information_objects(
            self.header.type_id,
            self.header.vsq.sq,
            self.header.vsq.number,
            self.objects,
        )
