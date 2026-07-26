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

"""[ODVA CIP Vol 1] Wrappers for the Parameter Object (class 0x0F, §5-14) and
Parameter Group Object (class 0x10, §5-15)."""

from typing import ClassVar

from caterpillar.fields import int16, uint8, uint16
from caterpillar.py import unpack
from caterpillar.shortcuts import LittleEndian

from ..const import ClassCode, CommonService
from ..epath import EPATH
from ._base import CIP_EPATH, CIP_SHORT_STRING, CIPAttribute, CIPObject


class ParameterObject(CIPObject):
    """Public, self-describing interface to one of a device's configuration
    parameters (See CIP Vol 1, §5-14).

    ``data_type`` is a CIP data-type-segment code (See Appendix C-6.1) and
    ``parameter_value``/``minimum_value``/``maximum_value``/``default_value``
    are shaped by it (and by ``data_size``), so all four are exposed as raw
    bytes rather than a fixed schema. Attributes 22-24 (International
    Parameter/Engineering Units/Help Name Strings, data type STRINGI) need
    the Get_Member service to decode and are not implemented.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.PARAMETER

    parameter_value: CIPAttribute[bytes] = CIPAttribute(1)
    """Actual parameter value; shape depends on data_type/data_size, set-only
    if descriptor bit 4 is clear (attribute 1)."""

    link_path_size: CIPAttribute[int] = CIPAttribute(2, uint8)
    """Size of link_path in bytes, 0 = no link (attribute 2)."""

    link_path: CIPAttribute[EPATH] = CIPAttribute(3, CIP_EPATH)
    """CIP path to the object attribute this parameter's value is linked to, up
    to 255 bytes (attribute 3)."""

    descriptor: CIPAttribute[int] = CIPAttribute(4, uint16)
    """Parameter behavior bit flags, e.g. bit 4 = read only (attribute 4, See §5-14.2.1.1, Table 5-14.9)."""

    data_type: CIPAttribute[bytes] = CIPAttribute(5)
    """CIP data-type-segment code selecting the type of the value attributes
    (attribute 5, See Appendix C-6.1)."""

    data_size: CIPAttribute[int] = CIPAttribute(6, uint8)
    """Number of bytes in parameter_value (attribute 6)."""

    parameter_name_string: CIPAttribute[str] = CIPAttribute(7, CIP_SHORT_STRING)
    """Human-readable parameter name, up to 16 characters, e.g. "Frequency #1"
    (attribute 7)."""

    units_string: CIPAttribute[str] = CIPAttribute(8, CIP_SHORT_STRING)
    """Engineering unit string, up to 4 characters (attribute 8)."""

    help_string: CIPAttribute[str] = CIPAttribute(9, CIP_SHORT_STRING)
    """Help string, up to 64 characters (attribute 9)."""

    minimum_value: CIPAttribute[bytes] = CIPAttribute(10)
    """Minimum settable value; shape depends on data_type (attribute 10, See
    §5-14.2.1.3)."""

    maximum_value: CIPAttribute[bytes] = CIPAttribute(11)
    """Maximum settable value; shape depends on data_type (attribute 11, See
    §5-14.2.1.3)."""

    default_value: CIPAttribute[bytes] = CIPAttribute(12)
    """Factory default value; shape depends on data_type (attribute 12)."""

    scaling_multiplier: CIPAttribute[int] = CIPAttribute(13, uint16)
    """Multiplier for the scaling formula (attribute 13, See Figure
    5-14.11)."""

    scaling_divisor: CIPAttribute[int] = CIPAttribute(14, uint16)
    """Divisor for the scaling formula (attribute 14)."""

    scaling_base: CIPAttribute[int] = CIPAttribute(15, uint16)
    """Base for the scaling formula (attribute 15)."""

    scaling_offset: CIPAttribute[int] = CIPAttribute(16, int16)
    """Offset for the scaling formula, may be negative (attribute 16)."""

    multiplier_link: CIPAttribute[int] = CIPAttribute(17, uint16)
    """Parameter instance sourcing the scaling multiplier, 0 = use scaling_multiplier (attribute 17)."""

    divisor_link: CIPAttribute[int] = CIPAttribute(18, uint16)
    """Parameter instance sourcing the scaling divisor, 0 = use scaling_divisor (attribute 18)."""

    base_link: CIPAttribute[int] = CIPAttribute(19, uint16)
    """Parameter instance sourcing the scaling base, 0 = use scaling_base (attribute 19)."""

    offset_link: CIPAttribute[int] = CIPAttribute(20, uint16)
    """Parameter instance sourcing the scaling offset, 0 = use scaling_offset (attribute 20)."""

    decimal_precision: CIPAttribute[int] = CIPAttribute(21, uint8)
    """Number of decimal places to show for the scaled engineering value
    (attribute 21)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Parameter class attribute from instance 0 (See §5-14.1, Table
        5-14.2)."""
        return self.get_attr(attribute, instance=0)

    def apply_attributes(self) -> bytes:
        """Invoke Apply_Attributes, committing parameter values whose use is
        pending."""
        return self.message(CommonService.APPLY_ATTRIBUTES)

    def reset(self) -> bytes:
        """Invoke the class-level Reset service, restoring all parameters to
        their factory default."""
        return self._expect_empty(self.message(CommonService.RESET, instance=0))

    def save(self) -> bytes:
        """Invoke Save, persisting this parameter instance's value to non-
        volatile storage."""
        return self._expect_empty(self.message(CommonService.SAVE))

    def restore(self) -> bytes:
        """Invoke Restore, reloading this parameter instance's value from non-
        volatile storage."""
        return self._expect_empty(self.message(CommonService.RESTORE))


class ParameterGroupObject(CIPObject):
    """Names and lists the parameter instances that belong to one configuration
    group (See CIP Vol 1, §5-15).

    The "Nth Parameter Number in Group" instance attributes are numbered
    dynamically - starting at attribute 3 for revision 1's abbreviated
    static set (§5-15.2), or attribute 16 for revision >1's extended static
    set (§5-15.3) - so :meth:`member` computes the attribute ID rather than
    declaring one :class:`CIPAttribute` per group slot.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.PARAMETER_GROUP

    group_name: CIPAttribute[str] = CIPAttribute(1, CIP_SHORT_STRING)
    """Human-readable group name, up to 16 characters, e.g. "Setup" (attribute
    1)."""

    number_of_members: CIPAttribute[int] = CIPAttribute(2, uint16)
    """Number of parameters in this group (attribute 2)."""

    def member(self, index: int, *, extended: bool = False) -> int:
        """Read the Nth (1-based) Parameter Object instance number bound to
        this group.

        :param index: 1-based member position within the group.
        :param extended: Use the extended static attribute set's
            numbering (1st member at attribute 16) instead of the
            abbreviated set's (1st member at attribute 3); the class-
            level Revision attribute selects which layout is active (See
            §5-15.1.1.1).
        """
        base = 15 if extended else 2
        return unpack(uint16, self.get(base + index), order=LittleEndian)

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Parameter Group class attribute from instance 0 (See §5-15.1,
        Table 5-15.1)."""
        return self.get_attr(attribute, instance=0)


__all__ = ["ParameterObject", "ParameterGroupObject"]
