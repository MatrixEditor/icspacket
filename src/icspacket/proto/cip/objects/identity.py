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

"""[ODVA CIP Vol 1] Wrapper for the CIP Identity Object (class 0x01).

Instance attributes are defined according to §5-2.2, Table 5-2.2.
"""

from collections.abc import Collection
from typing import ClassVar, cast

from caterpillar.fields import uint8, uint16, uint32
from caterpillar.model import StructDefMixin
from caterpillar.shortcuts import LittleEndian, f, struct
from caterpillar.types import uint8_t, uint16_t, uint32_t

from ..const import ClassCode, CommonService
from ._base import CIP_SHORT_STRING, CIPAttribute, CIPAttributeReader, CIPObject


@struct(order=LittleEndian)
class IdentityAttributes(StructDefMixin):
    """Identity Object instance attributes 1-8 (See CIP Vol 1, §5-2.2, Table
    5-2.2)."""

    vendor_id: uint16_t
    """Numeric code identifying which vendor manufactured the device."""

    device_type: uint16_t
    """Numeric code indicating the device's general product category."""

    product_code: uint16_t
    """Vendor-specific numeric code that pins down the exact product model
    within that vendor's own lineup."""

    revision_major: uint8_t
    """Major component of the Identity Object's revision number."""

    revision_minor: uint8_t
    """Minor component of the Identity Object's revision number, reported
    alongside revision_major."""

    status: uint16_t
    """16-bit value that summarizes the device's current status."""

    serial_number: uint32_t
    """32-bit value holding the device's serial number."""

    product_name: f[str, CIP_SHORT_STRING]
    """Human-readable product name, decoded as a CIP short string."""

    state: uint8_t
    """Single-byte code reporting the device's current state."""

    @property
    def revision(self) -> tuple[int, int]:
        """Major/minor revision tuple."""
        return self.revision_major, self.revision_minor


class IdentityObject(CIPObject):
    """Typed access to Identity Object instance attributes (See CIP Vol 1,
    §5-2.2, Table 5-2.2)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.IDENTITY

    vendor_id: CIPAttribute[int] = CIPAttribute(1, uint16)
    """Vendor ID (attribute 1)."""

    device_type: CIPAttribute[int] = CIPAttribute(2, uint16)
    """Device type (attribute 2)."""

    product_code: CIPAttribute[int] = CIPAttribute(3, uint16)
    """Product code (attribute 3)."""

    revision: CIPAttribute[Collection[int]] = CIPAttribute(4, uint8[2])
    """Major/minor revision (attribute 4)."""

    status: CIPAttribute[int] = CIPAttribute(5, uint16)
    """Identity status word (attribute 5)."""

    serial_number: CIPAttribute[int] = CIPAttribute(6, uint32)
    """Serial number (attribute 6)."""

    product_name: CIPAttribute[str] = CIPAttribute(7, CIP_SHORT_STRING)
    """Product name (attribute 7)."""

    state: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Present state (attribute 8)."""

    def _decode_all(self, data: bytes) -> IdentityAttributes:
        reader = CIPAttributeReader(data)
        values = reader.read_attributes(
            self.attribute_definitions,
            [1, 2, 3, 4, 5, 6, 7],
            missing_ok=False,
        )
        # Some adapters omit the later Identity attributes from Get_Attributes_All,
        # while others append implementation-specific attributes.  Attribute 8 is
        # the first byte after the product name when it is present.
        values.update(reader.read_attributes(self.attribute_definitions, [8]))
        revision = cast(list[int], values[4])
        return IdentityAttributes(
            cast(int, values[1]),
            cast(int, values[2]),
            cast(int, values[3]),
            revision[0],
            revision[1],
            cast(int, values[5]),
            cast(int, values[6]),
            cast(str, values[7]),
            cast(int, values.get(8, 0)),
        )

    def get_attributes(self) -> IdentityAttributes:
        """Read and decode Get_Attributes_All for Identity."""
        return self._decode_all(self.all())

    def reset(self, reset_type: int = 0) -> bytes:
        """Invoke the Identity Reset service."""
        request_data = uint8.to_bytes(int(reset_type), order=LittleEndian)
        return self._expect_empty(
            self.message(CommonService.RESET, bytes(request_data))
        )


__all__ = ["IdentityAttributes", "IdentityObject"]
