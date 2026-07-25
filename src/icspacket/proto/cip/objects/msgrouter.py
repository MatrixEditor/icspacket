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

"""Wrapper for the CIP Message Router Object (class 0x02)."""

from collections.abc import Collection
from typing import ClassVar

from caterpillar.fields import uint16

from ..const import ClassCode
from ._base import CIPAttribute, CIPObject


class MessageRouterObject(CIPObject):
    """Access instance-level Message Router attributes (See CIP Vol 1, Table
    5-3.2)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.MESSAGE_ROUTER

    object_list: CIPAttribute[Collection[int]] = CIPAttribute(1, uint16[uint16::])
    """Object class codes advertised by the device.

    On the wire, attribute 1 (instance 1) leads with a 2-byte count
    followed by that many UINT class codes; the count is stripped here
    and only the class codes are returned.
    """

    connection_count: CIPAttribute[int] = CIPAttribute(2, uint16)
    """Message Router connection count (attribute 2)."""

__all__ = ["MessageRouterObject"]
