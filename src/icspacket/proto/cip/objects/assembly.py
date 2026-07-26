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
"""Wrapper for the CIP Assembly Object (class 0x04)."""

from typing import ClassVar

from ..const import ClassCode
from ._base import CIPAttribute, CIPObject


class AssemblyObject(CIPObject):
    """Raw access to Assembly instance Data (attribute 3)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.ASSEMBLY

    data: CIPAttribute[bytes] = CIPAttribute(3)
    """Assembly Data (attribute 3)."""

__all__ = ["AssemblyObject"]
