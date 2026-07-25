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

"""Registry mapping a CIP object class code to its typed wrapper class.

Every core CIP object wrapper (:class:`~icspacket.proto.cip.objects.identity.IdentityObject`,
:class:`~icspacket.proto.cip.objects.connection.ConnectionObject`, ...) registers
itself automatically via :meth:`CIPObject.__init_subclass__
<icspacket.proto.cip.objects._base.CIPObject>`, so :func:`object_for` can
construct the right wrapper for a class code discovered at runtime (e.g. while
walking a device's object list).
"""

from ..connection import CIP_Connection
from ..const import ClassCode
from ._base import CIPObject, __cip_objects__


def object_for(connection: CIP_Connection, class_code: int | ClassCode, instance: int = 1) -> CIPObject:
    """Construct the registered wrapper for a standard CIP object class.

    :param connection: The session-bound connection the wrapper will
        issue requests over.
    :param class_code: The CIP object class code to look up.
    :param instance: The object instance the wrapper addresses (defaults
        to the first instance).
    :raises ValueError: if ``class_code`` has no registered wrapper.
    """
    try:
        object_type = __cip_objects__[int(class_code)]
    except KeyError as exc:
        raise ValueError(f"no core CIP object wrapper for class 0x{int(class_code):x}") from exc
    return object_type(connection, instance)
