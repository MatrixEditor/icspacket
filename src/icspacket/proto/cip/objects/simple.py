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
"""[ODVA CIP Vol 1] Wrappers for small, single-purpose CIP objects:

- DeviceNet (class 0x03, §5-4),
- Register (class 0x07, §5-8),
- Presence Sensing (class 0x0E, §5-13), and
- Selection (class 0x2E, §5-34).
"""

from collections.abc import Collection
from typing import ClassVar

from caterpillar.fields import uint8, uint16

from ..const import ClassCode, CommonService
from ._base import CIPAttribute, CIPObject


class DeviceNetObject(CIPObject):
    """DeviceNet port configuration and status (See CIP Vol 1, §5-4).

    Volume 1 only reserves this class code; the attribute set itself is
    defined in CIP Volume 3, DeviceNet Adaptation of CIP, so no typed
    attributes are declared here. Use
    :meth:`~CIPObject.get`/:meth:`~CIPObject.set` with the attribute IDs
    from that volume.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.DEVICE_NET


class RegisterObject(CIPObject):
    """Addresses up to 64K bits of input/output register data (See CIP Vol 1,
    §5-8)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.REGISTER

    bad_flag: CIPAttribute[int] = CIPAttribute(1, uint8)
    """0 = good, 1 = bad (attribute 1)."""

    direction: CIPAttribute[int] = CIPAttribute(2, uint8)
    """Direction of data transfer: 0 = Input Register, 1 = Output Register (attribute 2)."""

    size: CIPAttribute[int] = CIPAttribute(3, uint16)
    """Size of the register data in bits (attribute 3)."""

    data: CIPAttribute[bytes] = CIPAttribute(4)
    """Register data, LSB-aligned bit array (attribute 4)."""


class PresenceSensingObject(CIPObject):
    """Senses the presence or absence of a real-world target (See CIP Vol 1,
    §5-13)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.PRESENCE_SENSING

    output: CIPAttribute[int] = CIPAttribute(1, uint8)
    """0 = switching element open, 1 = switching element closed (attribute 1)."""

    number_of_attributes: CIPAttribute[int] = CIPAttribute(2, uint8)
    """Number of attributes supported (attribute 2)."""

    attribute_list: CIPAttribute[bytes] = CIPAttribute(3)
    """List of supported attribute IDs, one USINT each (attribute 3)."""

    diagnostic: CIPAttribute[int] = CIPAttribute(4, uint8)
    """0 = good, 1 = fault (attribute 4)."""

    on_delay: CIPAttribute[int] = CIPAttribute(5, uint16)
    """On delay in milliseconds, 0-65535 (attribute 5)."""

    off_delay: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Off delay in milliseconds, 0-65535 (attribute 6)."""

    one_shot_delay: CIPAttribute[int] = CIPAttribute(7, uint16)
    """One-shot delay in milliseconds, 0-65535 (attribute 7)."""

    operate_mode: CIPAttribute[int] = CIPAttribute(8, uint8)
    """0 = output attribute as specified, 1 = inversion of output attribute (attribute 8)."""

    sensitivity: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Detection amplification, 0 (lowest) - 255 (highest) (attribute 9)."""

    target_margin: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Signal strength above the switching threshold, 1-255 (attribute 10)."""

    background_margin: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Signal strength below the switching threshold, 0-100 (attribute 11)."""

    min_detect_distance: CIPAttribute[int] = CIPAttribute(12, uint16)
    """Minimum detection distance in mm, 0-65535 (attribute 12)."""

    max_detect_distance: CIPAttribute[int] = CIPAttribute(13, uint16)
    """Maximum detection distance in mm; shall be >= min_detect_distance
    (attribute 13)."""

    detect_distance: CIPAttribute[int] = CIPAttribute(14, uint16)
    """Current detection distance in mm, 0-65535 (attribute 14)."""

class SelectionObject(CIPObject):
    """Manages the selection and distribution of data between objects (See CIP
    Vol 1, §5-34).

    ``destination_list``, ``source_list``, and ``object_source_list`` (and
    the algorithm-dependent ``input_data_value``/``output_data_value``) are
    exposed as raw bytes: they are lists of path-length-prefixed EPATHs (or,
    for ``input_data_value``/``output_data_value``, a type that depends on
    whichever source/destination is currently selected) rather than a fixed
    schema.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.SELECTION

    state: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Current state of this instance (attribute 1, See §5-34.4.1, Table
    5-34.5)."""

    max_destinations: CIPAttribute[int] = CIPAttribute(2, uint16)
    """Maximum number of destination indexes supported, 0 = none (attribute 2)."""

    number_of_destinations: CIPAttribute[int] = CIPAttribute(3, uint16)
    """Number of entries in ``destination_list`` (attribute 3)."""

    destination_list: CIPAttribute[bytes] = CIPAttribute(4)
    """List of ``{USINT path_length, EPATH}`` destination paths (attribute
    4)."""

    max_sources: CIPAttribute[int] = CIPAttribute(5, uint16)
    """Maximum number of source indexes supported, 0 = none (attribute 5)."""

    number_of_sources: CIPAttribute[int] = CIPAttribute(6, uint16)
    """Number of entries in ``source_list`` (attribute 6)."""

    source_list: CIPAttribute[Collection[int]] = CIPAttribute(7, uint16[...])
    """Consuming I/O Connection Instance IDs, one UINT per source (attribute
    7)."""

    source_used: CIPAttribute[int] = CIPAttribute(8, uint16)
    """Index into ``source_list`` of the source currently in use, 1-based
    (attribute 8)."""

    source_alarm: CIPAttribute[Collection[int]] = CIPAttribute(9, uint8[...])
    """Per-source availability, one BOOL each: 0 = available, 1 = not available (attribute 9)."""

    algorithm_type: CIPAttribute[int] = CIPAttribute(10, uint8)
    """Selection algorithm type; 0 if unsupported (attribute 10)."""

    detection_count: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Required when the algorithm type is supported, range 2-255 (attribute
    11)."""

    selection_period: CIPAttribute[int] = CIPAttribute(12, uint16)
    """Required when the algorithm type is supported, range 1-65535 ms
    (attribute 12)."""

    object_source_list: CIPAttribute[bytes] = CIPAttribute(13)
    """List of ``{USINT path_length, EPATH}`` source paths (attribute 13)."""

    destination_used: CIPAttribute[int] = CIPAttribute(14, uint16)
    """Index into ``destination_list`` currently in use, 1-based (attribute
    14)."""

    input_data_value: CIPAttribute[bytes] = CIPAttribute(15)
    """Copy of the currently selected source attribute's data (attribute
    15)."""

    output_data_value: CIPAttribute[bytes] = CIPAttribute(16)
    """Copy of the currently selected destination attribute's data (attribute
    16)."""

    def start(self) -> bytes:
        """Invoke the class-level Start service (See §5-34.2, Table 5-34.3)."""
        return self.message(CommonService.START, instance=0)

    def stop(self) -> bytes:
        """Invoke the class-level Stop service (See §5-34.2, Table 5-34.3)."""
        return self.message(CommonService.STOP, instance=0)

    def reset(self) -> bytes:
        """Invoke the class-level Reset service, clearing table entries (See
        §5-34.2, Table 5-34.3)."""
        return self.message(CommonService.RESET, instance=0)


__all__ = [
    "DeviceNetObject",
    "PresenceSensingObject",
    "RegisterObject",
    "SelectionObject",
]
