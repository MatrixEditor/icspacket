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
from collections import defaultdict
from typing_extensions import override
from caterpillar.abc import _StructLike
from caterpillar.fields import Transformer, Pass
from caterpillar.shared import getstruct
from caterpillar.shortcuts import bitfield, struct, this, G, LittleEndian
from icspacket.proto.dnp3.objects.primitive import (
    UINT8,
    UINT16,
    UINT32,
    INT16,
    INT32,
    DNP3TIME,
    FLT32,
    FLT64,
    BSTRn,
    DBSTRn,
    UINT24,
    VSTR,
    OSTR,
    BCD,
)


class DNP3ObjectVariation(Transformer):
    """
    Represents a single **DNP3 object variation** definition.

    Variations define the exact encoding of values within a group.
    For example, Group 30 (Analog Input) may have multiple variations
    for 16-bit, 32-bit, or packed representations.

    :param int group: DNP3 object group number.
    :param int variation: Variation number within the group.
    :param type | _StructLike struct_ty: The Python type or struct-like
        definition used to encode/decode the variation.
    :param bool packed: Whether this variation encodes multiple values
        into a single object (e.g., packed binary inputs).
    """

    def __init__(
        self,
        group: int,
        variation: int,
        struct_ty: type | _StructLike,
        packed: bool = False,
    ) -> None:
        super().__init__(getstruct(struct_ty, struct_ty))
        self.__packed = packed
        self.group = group
        self.variation = variation

    @property
    def is_packed(self) -> bool:
        """
        Whether this variation encodes multiple values into a single object.

        :return: ``True`` if the variation uses packed encoding, ``False`` otherwise.
        :rtype: bool
        """
        return self.__packed

    @override
    def __repr__(self) -> str:
        """
        Return a concise string representation of this variation.

        :return: Representation in the form ``<GroupXVarY>``.
        :rtype: str
        """
        return f"<Group{self.group}Var{self.variation}>"

#: Registry of DNP3 object variations by group and variation.
#: Maps ``group -> variation -> DNP3ObjectVariation``.
__groups__: dict[int, dict[int, DNP3ObjectVariation]] = defaultdict(dict)

#: Registry of human-readable descriptions for groups and variations.
#: - If value is a ``str``, it describes the group / all variations.
#: - If value is a ``dict``, it maps ``variation -> description string``.
__variation_desc__: dict[int, dict[int, str] | str] = defaultdict(dict)

def get_variation(group: int, variation: int) -> DNP3ObjectVariation | None:
    """
    Look up a registered variation by group and variation number.

    :param int group: DNP3 object group number.
    :param int variation: Variation number within the group.
    :return: The registered variation definition, or ``None`` if not found.
    :rtype: DNP3ObjectVariation | None
    """
    group_spec = __groups__.get(group)
    if group_spec:
        return group_spec.get(variation)

def get_variation_desc(group: int, variation: int) -> str | None:
    """
    Retrieve a human-readable description of a variation.

    :param int group: DNP3 object group number.
    :param int variation: Variation number within the group.
    :return: The description string, or ``None`` if not available.
    :rtype: str | None
    """
    group_spec = __variation_desc__.get(group)
    if group_spec:
        return group_spec.get(variation) if not isinstance(group_spec , str) else group_spec

def get_group_name(group: int) -> str | None:
    """
    Retrieve the human-readable name of a group.

    Uses the first variation description if necessary.

    :param int group: DNP3 object group number.
    :return: The group name, or ``None`` if not found.
    :rtype: str | None
    """
    group_spec = __variation_desc__.get(group)
    if isinstance(group_spec, str):
        return group_spec

    first = list(group_spec.values())[0]
    return first.split(" - ")[0]

def register_variation(
    group: int,
    variation: int,
    struct_ty: type | _StructLike,
    desc: str,
    packed: bool = False,
) -> DNP3ObjectVariation:
    """
    Register a new DNP3 object variation in the registry.

    :param int group: DNP3 object group number.
    :param int variation: Variation number within the group.
    :param type | _StructLike struct_ty: Type or struct-like used to encode/decode.
    :param str desc: Human-readable description of the variation
        (e.g., ``"Analog Input - 32-bit with flag"``).
    :param bool packed: Whether this variation encodes multiple values
        into a single object (default: ``False``).
    :return: The created variation instance.
    :rtype: DNP3ObjectVariation
    """
    variation_obj = DNP3ObjectVariation(group, variation, struct_ty, packed=packed)
    __groups__[group][variation] = variation_obj
    __variation_desc__[group][variation] = desc
    return variation_obj

# fmt: off

### BEGIN GENERATED CONTENT ###
DNP3ObjectG1V1 = BSTRn()
__groups__[1][1] = DNP3ObjectVariation(1, 1, DNP3ObjectG1V1, packed=True)

@bitfield(order=LittleEndian)
class DNP3ObjectG1V2:
    state: 1 = False
    reserved: 1 = False
    chatter_filter: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False

__groups__[1][2] = DNP3ObjectVariation(1, 2, DNP3ObjectG1V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG2V1:
    state: UINT8

__groups__[2][1] = DNP3ObjectVariation(2, 1, DNP3ObjectG2V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG2V2:
    state: 1 = False
    reserved: 1 = False
    chatter_filter: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    timestamp: DNP3TIME

__groups__[2][2] = DNP3ObjectVariation(2, 2, DNP3ObjectG2V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG2V3:
    state: 1 = False
    reserved: 1 = False
    chatter_filter: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    timestamp: UINT16

__groups__[2][3] = DNP3ObjectVariation(2, 3, DNP3ObjectG2V3, packed=False)

DNP3ObjectG3V1 = DBSTRn()
__groups__[3][1] = DNP3ObjectVariation(3, 1, DNP3ObjectG3V1, packed=True)

@bitfield(order=LittleEndian)
class DNP3ObjectG3V2:
    state: 2 = 0
    chatter_filter: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False

__groups__[3][2] = DNP3ObjectVariation(3, 2, DNP3ObjectG3V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG4V1:
    state: 2 = 0
    chatter_filter: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False

__groups__[4][1] = DNP3ObjectVariation(4, 1, DNP3ObjectG4V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG4V2:
    state: 2 = 0
    chatter_filter: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    timestamp: DNP3TIME

__groups__[4][2] = DNP3ObjectVariation(4, 2, DNP3ObjectG4V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG4V3:
    state: 2 = 0
    chatter_filter: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    relative_time_ms: UINT16

__groups__[4][3] = DNP3ObjectVariation(4, 3, DNP3ObjectG4V3, packed=False)

DNP3ObjectG10V1 = BSTRn()
__groups__[10][1] = DNP3ObjectVariation(10, 1, DNP3ObjectG10V1, packed=True)

@bitfield(order=LittleEndian)
class DNP3ObjectG10V2:
    state: 1 = False
    reserved1: 1 = False
    reserved0: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False

__groups__[10][2] = DNP3ObjectVariation(10, 2, DNP3ObjectG10V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG11V1:
    state: 1 = False
    reserved1: 1 = False
    reserved0: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False

__groups__[11][1] = DNP3ObjectVariation(11, 1, DNP3ObjectG11V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG11V2:
    state: 1 = False
    reserved1: 1 = False
    reserved0: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    timestamp: DNP3TIME

__groups__[11][2] = DNP3ObjectVariation(11, 2, DNP3ObjectG11V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG12V1:
    tcc: 2 = 0
    cr: 1 = False
    qu: 1 = False
    op_type: 4 = 0
    count: UINT8
    ontime: UINT32
    offtime: UINT32
    reserved: 1 = False
    status_code: 7 = 0

__groups__[12][1] = DNP3ObjectVariation(12, 1, DNP3ObjectG12V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG12V2:
    tcc: 2 = 0
    cr: 1 = False
    qu: 1 = False
    op_type: 4 = 0
    count: UINT8
    ontime: UINT32
    offtime: UINT32
    reserved: 1 = False
    status_code: 7 = 0

__groups__[12][2] = DNP3ObjectVariation(12, 2, DNP3ObjectG12V2, packed=False)

DNP3ObjectG12V3 = BSTRn()
__groups__[12][3] = DNP3ObjectVariation(12, 3, DNP3ObjectG12V3, packed=True)

@bitfield(order=LittleEndian)
class DNP3ObjectG13V1:
    commanded_state: 1 = False
    status_code: 7 = 0

__groups__[13][1] = DNP3ObjectVariation(13, 1, DNP3ObjectG13V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG13V2:
    commanded_state: 1 = False
    status_code: 7 = 0
    timestamp: DNP3TIME

__groups__[13][2] = DNP3ObjectVariation(13, 2, DNP3ObjectG13V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG20V1:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32

__groups__[20][1] = DNP3ObjectVariation(20, 1, DNP3ObjectG20V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG20V2:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16

__groups__[20][2] = DNP3ObjectVariation(20, 2, DNP3ObjectG20V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG20V3:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32

__groups__[20][3] = DNP3ObjectVariation(20, 3, DNP3ObjectG20V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG20V4:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16

__groups__[20][4] = DNP3ObjectVariation(20, 4, DNP3ObjectG20V4, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG20V5:
    count: UINT32

__groups__[20][5] = DNP3ObjectVariation(20, 5, DNP3ObjectG20V5, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG20V6:
    count: UINT16

__groups__[20][6] = DNP3ObjectVariation(20, 6, DNP3ObjectG20V6, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG20V7:
    count: UINT32

__groups__[20][7] = DNP3ObjectVariation(20, 7, DNP3ObjectG20V7, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG20V8:
    count: UINT16

__groups__[20][8] = DNP3ObjectVariation(20, 8, DNP3ObjectG20V8, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG21V1:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32

__groups__[21][1] = DNP3ObjectVariation(21, 1, DNP3ObjectG21V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG21V2:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16

__groups__[21][2] = DNP3ObjectVariation(21, 2, DNP3ObjectG21V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG21V3:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32

__groups__[21][3] = DNP3ObjectVariation(21, 3, DNP3ObjectG21V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG21V4:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16

__groups__[21][4] = DNP3ObjectVariation(21, 4, DNP3ObjectG21V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG21V5:
    reserved1: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32
    timestamp: DNP3TIME

__groups__[21][5] = DNP3ObjectVariation(21, 5, DNP3ObjectG21V5, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG21V6:
    reserved1: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16
    timestamp: DNP3TIME

__groups__[21][6] = DNP3ObjectVariation(21, 6, DNP3ObjectG21V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG21V7:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32
    timestamp: DNP3TIME

__groups__[21][7] = DNP3ObjectVariation(21, 7, DNP3ObjectG21V7, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG21V8:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16
    timestamp: DNP3TIME

__groups__[21][8] = DNP3ObjectVariation(21, 8, DNP3ObjectG21V8, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG21V9:
    count: UINT32

__groups__[21][9] = DNP3ObjectVariation(21, 9, DNP3ObjectG21V9, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG21V10:
    count: UINT16

__groups__[21][10] = DNP3ObjectVariation(21, 10, DNP3ObjectG21V10, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG21V11:
    count: UINT32

__groups__[21][11] = DNP3ObjectVariation(21, 11, DNP3ObjectG21V11, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG21V12:
    count: UINT16

__groups__[21][12] = DNP3ObjectVariation(21, 12, DNP3ObjectG21V12, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG22V1:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32

__groups__[22][1] = DNP3ObjectVariation(22, 1, DNP3ObjectG22V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG22V2:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16

__groups__[22][2] = DNP3ObjectVariation(22, 2, DNP3ObjectG22V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG22V3:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32

__groups__[22][3] = DNP3ObjectVariation(22, 3, DNP3ObjectG22V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG22V4:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16

__groups__[22][4] = DNP3ObjectVariation(22, 4, DNP3ObjectG22V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG22V5:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32
    timestamp: DNP3TIME

__groups__[22][5] = DNP3ObjectVariation(22, 5, DNP3ObjectG22V5, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG22V6:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16
    timestamp: DNP3TIME

__groups__[22][6] = DNP3ObjectVariation(22, 6, DNP3ObjectG22V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG22V7:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32
    timestamp: DNP3TIME

__groups__[22][7] = DNP3ObjectVariation(22, 7, DNP3ObjectG22V7, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG22V8:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16
    timestamp: DNP3TIME

__groups__[22][8] = DNP3ObjectVariation(22, 8, DNP3ObjectG22V8, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG23V1:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32

__groups__[23][1] = DNP3ObjectVariation(23, 1, DNP3ObjectG23V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG23V2:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16

__groups__[23][2] = DNP3ObjectVariation(23, 2, DNP3ObjectG23V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG23V3:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32

__groups__[23][3] = DNP3ObjectVariation(23, 3, DNP3ObjectG23V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG23V4:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16

__groups__[23][4] = DNP3ObjectVariation(23, 4, DNP3ObjectG23V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG23V5:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32
    timestamp: DNP3TIME

__groups__[23][5] = DNP3ObjectVariation(23, 5, DNP3ObjectG23V5, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG23V6:
    reserved0: 1 = False
    discontinuity: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16
    timestamp: DNP3TIME

__groups__[23][6] = DNP3ObjectVariation(23, 6, DNP3ObjectG23V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG23V7:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT32
    timestamp: DNP3TIME

__groups__[23][7] = DNP3ObjectVariation(23, 7, DNP3ObjectG23V7, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG23V8:
    reserved1: 1 = False
    reserved0: 1 = False
    rollover: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    count: UINT16
    timestamp: DNP3TIME

__groups__[23][8] = DNP3ObjectVariation(23, 8, DNP3ObjectG23V8, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG30V1:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32

__groups__[30][1] = DNP3ObjectVariation(30, 1, DNP3ObjectG30V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG30V2:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16

__groups__[30][2] = DNP3ObjectVariation(30, 2, DNP3ObjectG30V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG30V3:
    value: INT32

__groups__[30][3] = DNP3ObjectVariation(30, 3, DNP3ObjectG30V3, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG30V4:
    value: INT16

__groups__[30][4] = DNP3ObjectVariation(30, 4, DNP3ObjectG30V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG30V5:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32

__groups__[30][5] = DNP3ObjectVariation(30, 5, DNP3ObjectG30V5, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG30V6:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64

__groups__[30][6] = DNP3ObjectVariation(30, 6, DNP3ObjectG30V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG31V1:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32

__groups__[31][1] = DNP3ObjectVariation(31, 1, DNP3ObjectG31V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG31V2:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16

__groups__[31][2] = DNP3ObjectVariation(31, 2, DNP3ObjectG31V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG31V3:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32
    timestamp: DNP3TIME

__groups__[31][3] = DNP3ObjectVariation(31, 3, DNP3ObjectG31V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG31V4:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16
    timestamp: DNP3TIME

__groups__[31][4] = DNP3ObjectVariation(31, 4, DNP3ObjectG31V4, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG31V5:
    value: INT32

__groups__[31][5] = DNP3ObjectVariation(31, 5, DNP3ObjectG31V5, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG31V6:
    value: INT16

__groups__[31][6] = DNP3ObjectVariation(31, 6, DNP3ObjectG31V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG31V7:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32

__groups__[31][7] = DNP3ObjectVariation(31, 7, DNP3ObjectG31V7, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG31V8:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64

__groups__[31][8] = DNP3ObjectVariation(31, 8, DNP3ObjectG31V8, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG32V1:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32

__groups__[32][1] = DNP3ObjectVariation(32, 1, DNP3ObjectG32V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG32V2:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16

__groups__[32][2] = DNP3ObjectVariation(32, 2, DNP3ObjectG32V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG32V3:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32
    timestamp: DNP3TIME

__groups__[32][3] = DNP3ObjectVariation(32, 3, DNP3ObjectG32V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG32V4:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16
    timestamp: DNP3TIME

__groups__[32][4] = DNP3ObjectVariation(32, 4, DNP3ObjectG32V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG32V5:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32

__groups__[32][5] = DNP3ObjectVariation(32, 5, DNP3ObjectG32V5, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG32V6:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64

__groups__[32][6] = DNP3ObjectVariation(32, 6, DNP3ObjectG32V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG32V7:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32
    timestamp: DNP3TIME

__groups__[32][7] = DNP3ObjectVariation(32, 7, DNP3ObjectG32V7, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG32V8:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64
    timestamp: DNP3TIME

__groups__[32][8] = DNP3ObjectVariation(32, 8, DNP3ObjectG32V8, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG33V1:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32

__groups__[33][1] = DNP3ObjectVariation(33, 1, DNP3ObjectG33V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG33V2:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16

__groups__[33][2] = DNP3ObjectVariation(33, 2, DNP3ObjectG33V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG33V3:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32
    timestamp: DNP3TIME

__groups__[33][3] = DNP3ObjectVariation(33, 3, DNP3ObjectG33V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG33V4:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16
    timestamp: DNP3TIME

__groups__[33][4] = DNP3ObjectVariation(33, 4, DNP3ObjectG33V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG33V5:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32

__groups__[33][5] = DNP3ObjectVariation(33, 5, DNP3ObjectG33V5, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG33V6:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64

__groups__[33][6] = DNP3ObjectVariation(33, 6, DNP3ObjectG33V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG33V7:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32
    timestamp: DNP3TIME

__groups__[33][7] = DNP3ObjectVariation(33, 7, DNP3ObjectG33V7, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG33V8:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64
    timestamp: DNP3TIME

__groups__[33][8] = DNP3ObjectVariation(33, 8, DNP3ObjectG33V8, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG34V1:
    deadband_value: UINT16

__groups__[34][1] = DNP3ObjectVariation(34, 1, DNP3ObjectG34V1, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG34V2:
    deadband_value: UINT32

__groups__[34][2] = DNP3ObjectVariation(34, 2, DNP3ObjectG34V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG34V3:
    deadband_value: FLT32

__groups__[34][3] = DNP3ObjectVariation(34, 3, DNP3ObjectG34V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG40V1:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32

__groups__[40][1] = DNP3ObjectVariation(40, 1, DNP3ObjectG40V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG40V2:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16

__groups__[40][2] = DNP3ObjectVariation(40, 2, DNP3ObjectG40V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG40V3:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32

__groups__[40][3] = DNP3ObjectVariation(40, 3, DNP3ObjectG40V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG40V4:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64

__groups__[40][4] = DNP3ObjectVariation(40, 4, DNP3ObjectG40V4, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG41V1:
    value: INT32
    control_status: UINT8

__groups__[41][1] = DNP3ObjectVariation(41, 1, DNP3ObjectG41V1, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG41V2:
    value: INT16
    control_status: UINT8

__groups__[41][2] = DNP3ObjectVariation(41, 2, DNP3ObjectG41V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG41V3:
    value: FLT32
    control_status: UINT8

__groups__[41][3] = DNP3ObjectVariation(41, 3, DNP3ObjectG41V3, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG41V4:
    value: FLT64
    control_status: UINT8

__groups__[41][4] = DNP3ObjectVariation(41, 4, DNP3ObjectG41V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG42V1:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32

__groups__[42][1] = DNP3ObjectVariation(42, 1, DNP3ObjectG42V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG42V2:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16

__groups__[42][2] = DNP3ObjectVariation(42, 2, DNP3ObjectG42V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG42V3:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT32
    timestamp: DNP3TIME

__groups__[42][3] = DNP3ObjectVariation(42, 3, DNP3ObjectG42V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG42V4:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: INT16
    timestamp: DNP3TIME

__groups__[42][4] = DNP3ObjectVariation(42, 4, DNP3ObjectG42V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG42V5:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32

__groups__[42][5] = DNP3ObjectVariation(42, 5, DNP3ObjectG42V5, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG42V6:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64

__groups__[42][6] = DNP3ObjectVariation(42, 6, DNP3ObjectG42V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG42V7:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT32
    timestamp: DNP3TIME

__groups__[42][7] = DNP3ObjectVariation(42, 7, DNP3ObjectG42V7, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG42V8:
    reserved0: 1 = False
    reference_err: 1 = False
    over_range: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    value: FLT64
    timestamp: DNP3TIME

__groups__[42][8] = DNP3ObjectVariation(42, 8, DNP3ObjectG42V8, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG43V1:
    reserved0: 1 = False
    status_code: 7 = 0
    commanded_value: INT32

__groups__[43][1] = DNP3ObjectVariation(43, 1, DNP3ObjectG43V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG43V2:
    reserved0: 1 = False
    status_code: 7 = 0
    commanded_value: INT16

__groups__[43][2] = DNP3ObjectVariation(43, 2, DNP3ObjectG43V2, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG43V3:
    reserved0: 1 = False
    status_code: 7 = 0
    commanded_value: INT32
    timestamp: DNP3TIME

__groups__[43][3] = DNP3ObjectVariation(43, 3, DNP3ObjectG43V3, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG43V4:
    reserved0: 1 = False
    status_code: 7 = 0
    commanded_value: INT16
    timestamp: DNP3TIME

__groups__[43][4] = DNP3ObjectVariation(43, 4, DNP3ObjectG43V4, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG43V5:
    reserved0: 1 = False
    status_code: 7 = 0
    commanded_value: FLT32

__groups__[43][5] = DNP3ObjectVariation(43, 5, DNP3ObjectG43V5, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG43V6:
    reserved0: 1 = False
    status_code: 7 = 0
    commanded_value: FLT64

__groups__[43][6] = DNP3ObjectVariation(43, 6, DNP3ObjectG43V6, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG43V7:
    reserved0: 1 = False
    status_code: 7 = 0
    commanded_value: FLT32
    timestamp: DNP3TIME

__groups__[43][7] = DNP3ObjectVariation(43, 7, DNP3ObjectG43V7, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG43V8:
    reserved0: 1 = False
    status_code: 7 = 0
    commanded_value: FLT64
    timestamp: DNP3TIME

__groups__[43][8] = DNP3ObjectVariation(43, 8, DNP3ObjectG43V8, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG50V1:
    timestamp: DNP3TIME

__groups__[50][1] = DNP3ObjectVariation(50, 1, DNP3ObjectG50V1, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG50V2:
    timestamp: DNP3TIME
    interval: UINT32

__groups__[50][2] = DNP3ObjectVariation(50, 2, DNP3ObjectG50V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG50V3:
    timestamp: DNP3TIME

__groups__[50][3] = DNP3ObjectVariation(50, 3, DNP3ObjectG50V3, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG50V4:
    timestamp: DNP3TIME
    interval_count: UINT32
    interval_units: UINT8

__groups__[50][4] = DNP3ObjectVariation(50, 4, DNP3ObjectG50V4, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG51V1:
    timestamp: DNP3TIME

__groups__[51][1] = DNP3ObjectVariation(51, 1, DNP3ObjectG51V1, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG51V2:
    timestamp: DNP3TIME

__groups__[51][2] = DNP3ObjectVariation(51, 2, DNP3ObjectG51V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG52V1:
    delay_secs: UINT16

__groups__[52][1] = DNP3ObjectVariation(52, 1, DNP3ObjectG52V1, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG52V2:
    delay_ms: UINT16

__groups__[52][2] = DNP3ObjectVariation(52, 2, DNP3ObjectG52V2, packed=False)

__groups__[60][1] = DNP3ObjectVariation(60, 1, Pass, packed=True)
__groups__[60][2] = DNP3ObjectVariation(60, 2, Pass, packed=True)
__groups__[60][3] = DNP3ObjectVariation(60, 3, Pass, packed=True)
__groups__[60][4] = DNP3ObjectVariation(60, 4, Pass, packed=True)
@struct(order=LittleEndian)
class DNP3ObjectG70V1:
    filename_size: UINT16
    filetype_code: UINT8
    attribute_code: UINT8
    start_record: UINT16
    end_record: UINT16
    file_size: UINT32
    created_timestamp: DNP3TIME
    permission: UINT16
    file_id: UINT32
    owner_id: UINT32
    group_id: UINT32
    file_function_code: UINT8
    status_code: UINT8
    filename: VSTR(this.filename_size)
    data_size: UINT16
    data: VSTR(this.data_size)

__groups__[70][1] = DNP3ObjectVariation(70, 1, DNP3ObjectG70V1, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG70V2:
    username_offset: UINT16
    username_size: UINT16
    password_offset: UINT16
    password_size: UINT16
    authentication_key: UINT32
    username: VSTR(this.username_size)
    password: VSTR(this.password_size)

__groups__[70][2] = DNP3ObjectVariation(70, 2, DNP3ObjectG70V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG70V3:
    filename_offset: UINT16
    filename_size: UINT16
    created: DNP3TIME
    permissions: UINT16
    authentication_key: UINT32
    file_size: UINT32
    operational_mode: UINT16
    maximum_block_size: UINT16
    request_id: UINT16
    filename: VSTR(this.filename_size)

__groups__[70][3] = DNP3ObjectVariation(70, 3, DNP3ObjectG70V3, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG70V4:
    file_handle: UINT32
    file_size: UINT32
    maximum_block_size: UINT16
    request_id: UINT16
    status_code: UINT8
    optional_text: VSTR(G.prefix)

__groups__[70][4] = DNP3ObjectVariation(70, 4, DNP3ObjectG70V4, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG70V5:
    file_handle: UINT32
    block_number: UINT32
    file_data: VSTR(G.prefix)

__groups__[70][5] = DNP3ObjectVariation(70, 5, DNP3ObjectG70V5, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG70V6:
    file_handle: UINT32
    block_number: UINT32
    status_code: UINT8
    optional_text: VSTR(G.prefix)

__groups__[70][6] = DNP3ObjectVariation(70, 6, DNP3ObjectG70V6, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG70V7:
    filename_offset: UINT16
    filename_size: UINT16
    file_type: UINT16
    file_size: UINT32
    created_timestamp: DNP3TIME
    permissions: UINT16
    request_id: UINT16
    filename: VSTR(this.filename_size)

__groups__[70][7] = DNP3ObjectVariation(70, 7, DNP3ObjectG70V7, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG70V8:
    file_specification: VSTR(G.prefix)

__groups__[70][8] = DNP3ObjectVariation(70, 8, DNP3ObjectG70V8, packed=False)

DNP3ObjectG80V1 = BSTRn()
__groups__[80][1] = DNP3ObjectVariation(80, 1, DNP3ObjectG80V1, packed=True)

@bitfield(order=LittleEndian)
class DNP3ObjectG81V1:
    overflow_state: 1 = False
    fill_percentage: 7 = 0
    group: UINT8
    variation: UINT8

__groups__[81][1] = DNP3ObjectVariation(81, 1, DNP3ObjectG81V1, packed=False)

# DNP3ObjectG82V1 NOT IMPLEMENTED
@struct(order=LittleEndian)
class DNP3ObjectG83V1:
    vendor_code: VSTR(4)
    object_id: UINT16
    length: UINT16
    data_objects: OSTR(this.length)

__groups__[83][1] = DNP3ObjectVariation(83, 1, DNP3ObjectG83V1, packed=False)

# DNP3ObjectG83V2 NOT IMPLEMENTED
# DNP3ObjectG85V1 NOT IMPLEMENTED
# DNP3ObjectG86V1 NOT IMPLEMENTED
@bitfield(order=LittleEndian)
class DNP3ObjectG86V2:
    padding2: 1 = False
    padding1: 1 = False
    padding0: 1 = False
    df: 1 = False
    ev: 1 = False
    st: 1 = False
    wr: 1 = False
    rd: 1 = False

__groups__[86][2] = DNP3ObjectVariation(86, 2, DNP3ObjectG86V2, packed=False)

# DNP3ObjectG86V3 NOT IMPLEMENTED
# DNP3ObjectG87V1 NOT IMPLEMENTED
# DNP3ObjectG88V1 NOT IMPLEMENTED
# DNP3ObjectG90V1 NOT IMPLEMENTED
# DNP3ObjectG91V1 NOT IMPLEMENTED
# DNP3ObjectG100V* NOT IMPLEMENTED
@struct(order=LittleEndian)
class DNP3ObjectG101V1:
    value: BCD(4)

__groups__[101][1] = DNP3ObjectVariation(101, 1, DNP3ObjectG101V1, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG101V2:
    value: BCD(8)

__groups__[101][2] = DNP3ObjectVariation(101, 2, DNP3ObjectG101V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG101V3:
    value: BCD(16)

__groups__[101][3] = DNP3ObjectVariation(101, 3, DNP3ObjectG101V3, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG102V1:
    value: UINT8

__groups__[102][1] = DNP3ObjectVariation(102, 1, DNP3ObjectG102V1, packed=False)

for i in range(1, 256):
    __groups__[110][i] = DNP3ObjectVariation(110, i, OSTR(i))

for i in range(1, 256):
    __groups__[111][i] = DNP3ObjectVariation(111, i, OSTR(i))

for i in range(1, 256):
    __groups__[112][i] = DNP3ObjectVariation(112, i, OSTR(i))

for i in range(1, 256):
    __groups__[113][i] = DNP3ObjectVariation(113, i, OSTR(i))

@struct(order=LittleEndian)
class DNP3ObjectG120V1:
    csq: UINT32
    usr: UINT16
    mal: UINT8
    reason: UINT8
    challenge_data: OSTR(G.prefix)

__groups__[120][1] = DNP3ObjectVariation(120, 1, DNP3ObjectG120V1, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V2:
    csq: UINT32
    usr: UINT16
    mac_value: OSTR(G.prefix)

__groups__[120][2] = DNP3ObjectVariation(120, 2, DNP3ObjectG120V2, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V3:
    csq: UINT32
    user_number: UINT16

__groups__[120][3] = DNP3ObjectVariation(120, 3, DNP3ObjectG120V3, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V4:
    user_number: UINT16

__groups__[120][4] = DNP3ObjectVariation(120, 4, DNP3ObjectG120V4, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V5:
    ksq: UINT32
    user_number: UINT16
    key_wrap_alg: UINT8
    key_status: UINT8
    mal: UINT8
    challenge_data_len: UINT16
    challenge_data: OSTR(this.challenge_data_len)
    mac_value: OSTR(G.prefix)

__groups__[120][5] = DNP3ObjectVariation(120, 5, DNP3ObjectG120V5, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V6:
    ksq: UINT24
    usr: UINT16
    wrapped_key_data: OSTR(G.prefix)

__groups__[120][6] = DNP3ObjectVariation(120, 6, DNP3ObjectG120V6, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V7:
    sequence_number: UINT32
    usr: UINT16
    association_id: UINT16
    error_code: UINT8
    time_of_error: DNP3TIME
    error_text: VSTR(G.prefix)

__groups__[120][7] = DNP3ObjectVariation(120, 7, DNP3ObjectG120V7, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V8:
    key_change_method: UINT8
    certificate_type: UINT8
    certificate: OSTR(G.prefix - 1)

__groups__[120][8] = DNP3ObjectVariation(120, 8, DNP3ObjectG120V8, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V9:
    mac_value: OSTR(G.prefix)

__groups__[120][9] = DNP3ObjectVariation(120, 9, DNP3ObjectG120V9, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V10:
    key_change_method: UINT8
    operation: UINT8
    scs: UINT32
    user_role: UINT16
    user_role_expiry_interval: UINT16
    username_len: UINT16
    user_public_key_len: UINT16
    certification_data_len: UINT16
    username: VSTR(this.username_len)
    user_public_key: OSTR(this.user_public_key_len)
    certification_data: OSTR(this.certification_data_len)

__groups__[120][10] = DNP3ObjectVariation(120, 10, DNP3ObjectG120V10, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V11:
    key_change_method: UINT8
    username_len: UINT16
    master_challenge_data_len: UINT16
    username: VSTR(this.username_len)
    master_challenge_data: OSTR(this.master_challenge_data_len)

__groups__[120][11] = DNP3ObjectVariation(120, 11, DNP3ObjectG120V11, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V12:
    ksq: UINT32
    user_number: UINT16
    challenge_data_len: UINT16
    challenge_data: OSTR(this.challenge_data_len)

__groups__[120][12] = DNP3ObjectVariation(120, 12, DNP3ObjectG120V12, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V13:
    ksq: UINT32
    user_number: UINT16
    encrypted_update_key_len: UINT16
    encrypted_update_key_data: OSTR(this.encrypted_update_key_len)

__groups__[120][13] = DNP3ObjectVariation(120, 13, DNP3ObjectG120V13, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V14:
    digital_signature: OSTR(G.prefix)

__groups__[120][14] = DNP3ObjectVariation(120, 14, DNP3ObjectG120V14, packed=False)

@struct(order=LittleEndian)
class DNP3ObjectG120V15:
    mac: OSTR(G.prefix)

__groups__[120][15] = DNP3ObjectVariation(120, 15, DNP3ObjectG120V15, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG121V1:
    reserved1: 1 = False
    discontinuity: 1 = False
    reserved0: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    association_id: UINT16
    count_value: UINT32

__groups__[121][1] = DNP3ObjectVariation(121, 1, DNP3ObjectG121V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG122V1:
    reserved1: 1 = False
    discontinuity: 1 = False
    reserved0: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    association_id: UINT16
    count_value: UINT32

__groups__[122][1] = DNP3ObjectVariation(122, 1, DNP3ObjectG122V1, packed=False)

@bitfield(order=LittleEndian)
class DNP3ObjectG122V2:
    reserved1: 1 = False
    discontinuity: 1 = False
    reserved0: 1 = False
    local_forced: 1 = False
    remote_forced: 1 = False
    comm_lost: 1 = False
    restart: 1 = False
    online: 1 = False
    association_id: UINT16
    count_value: UINT32
    timestamp: DNP3TIME

__groups__[122][2] = DNP3ObjectVariation(122, 2, DNP3ObjectG122V2, packed=False)

__variation_desc__[0][209] = "Device attributes - secure authentication version"
__variation_desc__[0][210] = "Device attributes - number of security statistics per association"
__variation_desc__[0][211] = "Device attributes - identification of support for user-specific attributes"
__variation_desc__[0][212] = "Device attributes - number of master-defined data set prototypes"
__variation_desc__[0][213] = "Device attributes - number of outstation-defined data set prototypes"
__variation_desc__[0][214] = "Device attributes - number of master-defined data sets"
__variation_desc__[0][215] = "Device attributes - number of outstation-defined data sets"
__variation_desc__[0][216] = "Device attributes - maximum number of binary output objects per"
__variation_desc__[0][217] = "Device attributes - local timing accura cy"
__variation_desc__[0][218] = "Device attributes - duration of time accuracy"
__variation_desc__[0][219] = "Device attributes - support for analog output events"
__variation_desc__[0][220] = "Device attributes - maximum analog o utput index"
__variation_desc__[0][221] = "Device attributes - number of analog outputs"
__variation_desc__[0][222] = "Device attributes - support for binary output events"
__variation_desc__[0][223] = "Device attributes - maximum binary output index"
__variation_desc__[0][224] = "Device attributes - number of binary o utputs"
__variation_desc__[0][225] = "Device attributes - support for frozen counter events"
__variation_desc__[0][226] = "Device attributes - support for frozen counters"
__variation_desc__[0][227] = "Device attributes - support for counter events"
__variation_desc__[0][228] = "Device attributes - maximum counter index"
__variation_desc__[0][229] = "Device attributes - number of counter points"
__variation_desc__[0][230] = "Device attributes - support for frozen analog inputs"
__variation_desc__[0][231] = "Device attributes - support for analog input events"
__variation_desc__[0][232] = "Device attributes - maximum analog input index"
__variation_desc__[0][233] = "Device attributes - number of analog input points"
__variation_desc__[0][234] = "Device attributes - support for double-bit binary input events"
__variation_desc__[0][235] = "Device attributes - maximum double-bit binary index"
__variation_desc__[0][236] = "Device attributes - number of double-bit binary input points"
__variation_desc__[0][237] = "Device attributes - support for binary input events"
__variation_desc__[0][238] = "Device attributes - maximum binary input index"
__variation_desc__[0][239] = "Device attributes - number of binary input points"
__variation_desc__[0][240] = "Device attributes - maximum transmit fragment size"
__variation_desc__[0][241] = "Device attributes - maximum receive fragment size"
__variation_desc__[0][242] = "Device attributes - device manufacturer's software version"
__variation_desc__[0][243] = "Device attributes - device manufacturer's hardware version"
__variation_desc__[0][245] = "Device attributes - user-assigned location name"
__variation_desc__[0][246] = "Device attributes - user-assigned ID code/number"
__variation_desc__[0][247] = "Device attributes - user-assigned devi ce name"
__variation_desc__[0][248] = "Device attributes - device serial number"
__variation_desc__[0][249] = "Device attributes - DNP3 subset and c onformance"
__variation_desc__[0][250] = "Device attributes - device manufacturer's product name and model"
__variation_desc__[0][252] = "Device attributes - device manufacturer's name"
__variation_desc__[0][254] = "Device attributes - non-specific all attributes request"
__variation_desc__[0][255] = "Device attributes - list of attribute variations"
__variation_desc__[1][1] = "Binary input - packed format"
__variation_desc__[1][2] = "Binary input - with flags"
__variation_desc__[2][1] = "Binary input event - without time"
__variation_desc__[2][2] = "Binary input event - with absolute time"
__variation_desc__[2][3] = "Binary input event - with relative time"
__variation_desc__[3][1] = "Double-bit binary input - packed format"
__variation_desc__[3][2] = "Double-bit binary input - with flags"
__variation_desc__[4][1] = "Double-bit binary input event - without time"
__variation_desc__[4][2] = "Double-bit binary input event - with absolute time"
__variation_desc__[4][3] = "Double-bit binary input event - with relative time"
__variation_desc__[10][1] = "Binary output - packed format"
__variation_desc__[10][2] = "Binary output - output status with flags"
__variation_desc__[11][1] = "Binary output event - status without time"
__variation_desc__[11][2] = "Binary output event - status with time"
__variation_desc__[12][1] = "Binary output command - control relay output block - also known as"
__variation_desc__[12][2] = "Binary output command - pattern control block - also known as PCB"
__variation_desc__[12][3] = "Binary output command - pattern mask"
__variation_desc__[13][1] = "Binary output command event - command status without time"
__variation_desc__[13][2] = "Binary output command event - command status with time"
__variation_desc__[20][1] = "Counter - 32-bit with flag"
__variation_desc__[20][2] = "Counter - 16-bit with flag"
__variation_desc__[20][3] = "Counter - 32-bit with flag, delta"
__variation_desc__[20][4] = "Counter - 16-bit with flag, delta"
__variation_desc__[20][5] = "Counter - 32-bit without flag"
__variation_desc__[20][6] = "Counter - 16-bit without flag"
__variation_desc__[20][7] = "Counter - 32-bit without flag, delta"
__variation_desc__[20][8] = "Counter - 16-bit without flag, delta"
__variation_desc__[21][1] = "Frozen counter - 32-bit with flag"
__variation_desc__[21][2] = "Frozen counter - 16-bit with flag"
__variation_desc__[21][3] = "Frozen counter - 32-bit with flag, delta"
__variation_desc__[21][4] = "Frozen counter - 16-bit with flag, delta"
__variation_desc__[21][5] = "Frozen counter - 32-bit with flag and time"
__variation_desc__[21][6] = "Frozen counter - 16-bit with flag and time"
__variation_desc__[21][7] = "Frozen counter - 32-bit with flag and time, delta"
__variation_desc__[21][8] = "Frozen counter - 16-bit with flag and time, delta"
__variation_desc__[21][9] = "Frozen counter - 32-bit without flag"
__variation_desc__[21][10] = "Frozen counter - 16-bit without flag"
__variation_desc__[21][11] = "Frozen counter - 32-bit without flag, delta"
__variation_desc__[21][12] = "Frozen counter - 16-bit without flag, delta"
__variation_desc__[22][1] = "Counter event - 32-bit with flag"
__variation_desc__[22][2] = "Counter event - 16-bit with flag"
__variation_desc__[22][3] = "Counter event - 32-bit with flag, delta"
__variation_desc__[22][4] = "Counter event - 16-bit with flag, delta"
__variation_desc__[22][5] = "Counter event - 32-bit with flag and time"
__variation_desc__[22][6] = "Counter event - 16-bit with flag and time"
__variation_desc__[22][7] = "Counter event - 32-bit with flag and time, delta"
__variation_desc__[22][8] = "Counter event - 16-bit with flag and time, delta"
__variation_desc__[23][1] = "Frozen counter event - 32-bit with flag"
__variation_desc__[23][2] = "Frozen counter event - 16-bit with flag"
__variation_desc__[23][3] = "Frozen counter event - 32-bit with flag , delta"
__variation_desc__[23][4] = "Frozen counter event - 16-bit with flag , delta"
__variation_desc__[23][5] = "Frozen counter event - 32-bit with flag and time"
__variation_desc__[23][6] = "Frozen counter event - 16-bit with flag and time"
__variation_desc__[23][7] = "Frozen counter event - 32-bit with flag and time, delta"
__variation_desc__[23][8] = "Frozen counter event - 16-bit with flag and time, delta"
__variation_desc__[30][1] = "Analog input - 32-bit with flag"
__variation_desc__[30][2] = "Analog input - 16-bit with flag"
__variation_desc__[30][3] = "Analog input - 32-bit without flag"
__variation_desc__[30][4] = "Analog input - 16-bit without flag"
__variation_desc__[30][5] = "Analog input - single-precision, floating-point with flag"
__variation_desc__[30][6] = "Analog input - double-precision, floati ng-point with flag"
__variation_desc__[31][1] = "Frozen analog input - 32-bit with flag"
__variation_desc__[31][2] = "Frozen analog input - 16-bit with flag"
__variation_desc__[31][3] = "Frozen analog input - 32-bit with time- of-freeze"
__variation_desc__[31][4] = "Frozen analog input - 16-bit with time- of-freeze"
__variation_desc__[31][5] = "Frozen analog input - 32-bit without flag"
__variation_desc__[31][6] = "Frozen analog input - 16-bit without flag"
__variation_desc__[31][7] = "Frozen analog input - single-precision, floating-point with flag"
__variation_desc__[31][8] = "Frozen analog input - double-precision, floating-point with flag"
__variation_desc__[32][1] = "Analog input event - 32-bit without time"
__variation_desc__[32][2] = "Analog input event - 16-bit without time"
__variation_desc__[32][3] = "Analog input event - 32-bit with time"
__variation_desc__[32][4] = "Analog input event - 16-bit with time"
__variation_desc__[32][5] = "Analog input event - single-precision, floating-point without time"
__variation_desc__[32][6] = "Analog input event - double-precision, floating-point without time"
__variation_desc__[32][7] = "Analog input event - single-precision, floating-point with time"
__variation_desc__[32][8] = "Analog input event - double-precision, floating-point with time"
__variation_desc__[33][1] = "Frozen analog input event - 32-bit without time"
__variation_desc__[33][2] = "Frozen analog input event - 16-bit without time"
__variation_desc__[33][3] = "Frozen analog input event - 32-bit with time"
__variation_desc__[33][4] = "Frozen analog input event - 16-bit with time"
__variation_desc__[33][5] = "Frozen analog input event - single-precision, floating-point without"
__variation_desc__[33][6] = "Frozen analog input event - double-precision, floating-point without"
__variation_desc__[33][7] = "Frozen analog input event - single-precision, floating-point with time"
__variation_desc__[33][8] = "Frozen analog input event - double-precision, floating-point with time"
__variation_desc__[34][1] = "Analog input reporting deadband - 16-bit"
__variation_desc__[34][2] = "Analog input reporting deadband - 32-bit"
__variation_desc__[34][3] = "Analog input reporting deadband - single-precision, floating-point"
__variation_desc__[40][1] = "Analog output status - 32-bit with flag"
__variation_desc__[40][2] = "Analog output status - 16-bit with flag"
__variation_desc__[40][3] = "Analog output status - single-precision, floating-point with flag"
__variation_desc__[40][4] = "Analog output status - double-precision, floating-point with flag"
__variation_desc__[41][1] = "Analog output - 32-bit"
__variation_desc__[41][2] = "Analog output - 16-bit"
__variation_desc__[41][3] = "Analog output - single-precision, floating-point"
__variation_desc__[41][4] = "Analog output - double-precision, floating-point"
__variation_desc__[42][1] = "Analog output event - 32-bit without time"
__variation_desc__[42][2] = "Analog output event - 16-bit without time"
__variation_desc__[42][3] = "Analog output event - 32-bit with time"
__variation_desc__[42][4] = "Analog output event - 16-bit with time"
__variation_desc__[42][5] = "Analog output event - single-precision, floating-point without time"
__variation_desc__[42][6] = "Analog output event - double-precisio n, floating-point without time"
__variation_desc__[42][7] = "Analog output event - single-precision, floating-point with time"
__variation_desc__[42][8] = "Analog output event - double-precisio n, floating-point with time"
__variation_desc__[43][1] = "Analog output command event - 32-bit without time"
__variation_desc__[43][2] = "Analog output command event - 16-bit without time"
__variation_desc__[43][3] = "Analog output command event - 32-bit with time"
__variation_desc__[43][4] = "Analog output command event - 16-bit with time"
__variation_desc__[43][5] = "Analog output command event - single-precision, floating-point"
__variation_desc__[43][6] = "Analog output command event - doub le-precision, floating-point"
__variation_desc__[43][7] = "Analog output command event - single-precision, floating-point with"
__variation_desc__[43][8] = "Analog output command event - doub le-precision, floating-point with"
__variation_desc__[50][1] = "Time and date - absolute time"
__variation_desc__[50][2] = "Time and date - absolute time and interval"
__variation_desc__[50][3] = "Time and date - absolute time at last recorded time"
__variation_desc__[50][4] = "Time and date - indexed absolute time and long interval"
__variation_desc__[51][1] = "Time and date common time-of-occurrence - absolute time,"
__variation_desc__[51][2] = "Time and date common time-of-occurrence - absolute time,"
__variation_desc__[52][1] = "Time delay - coarse"
__variation_desc__[52][2] = "Time delay - fine"
__variation_desc__[60][1] = "Class objects - Class 0 data"
__variation_desc__[60][2] = "Class objects - Class 1 data"
__variation_desc__[60][3] = "Class objects - Class 2 data"
__variation_desc__[60][4] = "Class objects - Class 3 data"
__variation_desc__[70][1] = "File-control - file identifier - superseded"
__variation_desc__[70][2] = "File-control - authentication"
__variation_desc__[70][3] = "File-control - file command"
__variation_desc__[70][4] = "File-control - file command status"
__variation_desc__[70][5] = "File-control - file transport"
__variation_desc__[70][6] = "File-control - file transport status"
__variation_desc__[70][7] = "File-control - file descriptor"
__variation_desc__[70][8] = "File-control - file specification string"
__variation_desc__[80][1] = "Internal indications - packed format"
__variation_desc__[81][1] = "Device storage - buffer fill status"
__variation_desc__[82][1] = "Device Profile - functions and indexes"
__variation_desc__[83][1] = "Data set - private registration object"
__variation_desc__[83][2] = "Data set - private registration object descriptor"
__variation_desc__[85][1] = "Data set prototype - with UUID"
__variation_desc__[86][1] = "Data set descriptor - data set contents"
__variation_desc__[86][2] = "Data set descriptor - characteristics"
__variation_desc__[86][3] = "Data set descriptor - point index attributes"
__variation_desc__[87][1] = "Data set - present value"
__variation_desc__[88][1] = "Data set event - snapshot"
__variation_desc__[90][1] = "Application - identifier"
__variation_desc__[91][1] = "Status of requested operation - active configuration"
__variation_desc__[100] = "Floating-point"
__variation_desc__[101][1] = "Binary-coded decimal integer - small"
__variation_desc__[101][2] = "Binary-coded decimal integer - medium"
__variation_desc__[101][3] = "Binary-coded decimal integer - large"
__variation_desc__[102][1] = "Unsigned integer - 8-bit"
__variation_desc__[110] = "Octet string"
__variation_desc__[111] = "Octet string event"
__variation_desc__[112] = "Virtual terminal output block"
__variation_desc__[113] = "Virtual terminal event data"
__variation_desc__[120][1] = "Authentication - challenge"
__variation_desc__[120][2] = "Authentication - reply"
__variation_desc__[120][3] = "Authentication - Aggressive Mode req uest"
__variation_desc__[120][4] = "Authentication - session key status re quest"
__variation_desc__[120][5] = "Authentication - session key status"
__variation_desc__[120][6] = "Authentication - session key change"
__variation_desc__[120][7] = "Authentication - error"
__variation_desc__[120][8] = "Authentication - user certificate"
__variation_desc__[120][9] = "Authentication - message authentication code (MAC)"
__variation_desc__[120][10] = "Authentication - user status change"
__variation_desc__[120][11] = "Authentication - update key change request"
__variation_desc__[120][12] = "Authentication - update key change reply"
__variation_desc__[120][13] = "Authentication - update key change"
__variation_desc__[120][14] = "Authentication - update key change si gnature"
__variation_desc__[120][15] = "Authentication - update key change confirmation"
__variation_desc__[121][1] = "Security statistic - 32-bit with flag"
__variation_desc__[122][1] = "Security statistic event - 32-bit with flag"
__variation_desc__[122][2] = "Security statistic event - 32-bit with flag and time"
### END GENERATED CONTENT ###
# fmt: on

