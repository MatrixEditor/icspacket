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
"""[ODVA CIP Vol 2] Wrapper for the CIP Ethernet Link Object (class 0xF6).

Instance attributes and counter block layouts are defined according to
§5-5.3.2 (Table 5-5.3) and §5-5.3.2.4/.5.
"""

from collections.abc import Collection
from dataclasses import dataclass
from typing import ClassVar, cast

from caterpillar.fields import Bytes, uint8, uint32

from ..const import ClassCode
from ._base import (
    CIP_SHORT_STRING,
    CIPAttribute,
    CIPAttributeReader,
    CIPObject,
)


@dataclass
class EthernetLinkAttributes:
    """Instance-level Get_Attributes_All reply (See CIP Vol 2, §5-5.3.2, Table
    5-5.3).

    Attributes 6-11 (Interface Control, Interface Type, Interface State,
    Admin State, Interface Label, Interface Capability) are optional/
    conditional and variably sized; they are exposed verbatim via
    ``extra`` rather than individually decoded.
    """

    interface_speed: int
    interface_flags: int
    physical_address: bytes
    interface_counters: "list[int] | None"
    media_counters: "list[int] | None"
    extra: bytes = b""


class EthernetLinkObject(CIPObject):
    """Typed access to Ethernet Link attributes (See CIP Vol 2, §5-5.3.2, Table
    5-5.3)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.ETHERNET_LINK
    # Fixed sizes according to CIP Vol 2, §5-5.3.2.4/.5: 11 and 12 UDINT fields.
    INTERFACE_COUNTERS_SIZE: ClassVar[int] = 44
    MEDIA_COUNTERS_SIZE: ClassVar[int] = 48

    interface_speed: CIPAttribute[int] = CIPAttribute(1, uint32)
    """Interface speed in Mbps (attribute 1)."""

    interface_flags: CIPAttribute[int] = CIPAttribute(2, uint32)
    """Interface flags (attribute 2)."""

    physical_address: CIPAttribute[bytes] = CIPAttribute(3, Bytes(6))
    """Physical MAC address (attribute 3)."""

    interface_counters: CIPAttribute[Collection[int]] = CIPAttribute(
        4, uint32[INTERFACE_COUNTERS_SIZE // 4], size=INTERFACE_COUNTERS_SIZE
    )
    """Interface counters block (attribute 4)."""

    media_counters: CIPAttribute[Collection[int]] = CIPAttribute(
        5, uint32[MEDIA_COUNTERS_SIZE // 4], size=MEDIA_COUNTERS_SIZE
    )
    """Media counters block (attribute 5)."""

    interface_control: CIPAttribute[bytes] = CIPAttribute(6)
    """Interface control bytes (attribute 6)."""

    interface_type: CIPAttribute[int] = CIPAttribute(7, uint8)
    """Interface type (attribute 7)."""

    interface_state: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Interface state (attribute 8)."""

    administrative_state: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Administrative state (attribute 9)."""

    interface_label: CIPAttribute[str] = CIPAttribute(10, CIP_SHORT_STRING)
    """Human-readable interface label (attribute 10)."""

    def _decode_all(self, data: bytes) -> EthernetLinkAttributes:
        reader = CIPAttributeReader(data)
        values = reader.read_attributes(self.attribute_definitions, [1, 2, 3, 4, 5])
        return EthernetLinkAttributes(
            cast(int, values.get(1, 0)),
            cast(int, values.get(2, 0)),
            cast(bytes, values.get(3, b"")),
            cast(list[int], values.get(4)),
            cast(list[int], values.get(5)),
            reader.read_remaining(),
        )

    def get_attributes(self) -> EthernetLinkAttributes:
        """Read and decode Get_Attributes_All for Ethernet Link."""
        return self._decode_all(self.all())


__all__ = ["EthernetLinkAttributes", "EthernetLinkObject"]
