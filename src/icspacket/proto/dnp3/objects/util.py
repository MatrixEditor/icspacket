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
from icspacket.proto.dnp3.objects.coding import DNP3Objects


def new_octet_string(
    data: bytes, /, group: int | None = None, prefix: int | None = None
) -> DNP3Objects:
    """Create a new DNP3 octet string object.

    This function constructs a :class:`DNP3Objects` container holding
    a single octet string object of the given length. By default,
    group 110 is used (standard octet strings), unless a specific
    group is provided.

    The function automatically selects the variation number based on
    the length of the input string.

    :param data: Octet string payload.
    :type data: bytes
    :param group: Optional group identifier. Defaults to 110 if not provided.
    :type group: int | None, optional
    :param prefix: Optional prefix used when adding the object instance.
    :type prefix: int | None, optional
    :return: A DNP3Objects container with the constructed octet string.
    :rtype: DNP3Objects
    :raises ValueError: If the octet string exceeds 255 bytes.
    """
    if len(data) > 255:
        raise ValueError("Octet string too long")

    group_id = group if group is not None else 110
    objects = DNP3Objects()
    variation = objects.get_variation(group_id, len(data))
    variation.add(data, prefix=prefix)
    return objects


def get_octet_string(objects: DNP3Objects, /, group_id: int | None = None) -> bytes:
    """Extract the first octet string instance from a DNP3Objects container.

    This function searches the given :class:`DNP3Objects` container
    for an octet string in the specified group (default: 110).
    If found, it returns the first octet string instance.

    *This function always succeeds.*

    :param objects: Container holding DNP3 objects.
    :type objects: DNP3Objects
    :param group_id: Optional group identifier. Defaults to 110 if not provided.
    :type group_id: int | None, optional
    :return: The extracted octet string, or an empty bytes object if not found.
    :rtype: bytes
    """
    group_id = group_id if group_id is not None else 110
    group = objects.get(group_id)
    if group is None:
        return b""

    values = group.values()
    if len(values) == 0:
        return b""

    variation = list(values)[0]
    if variation is None or len(variation) == 0:
        return b""

    return variation[0].instance


def as_variation0(*groups: int) -> DNP3Objects:
    """Construct variation 0 objects for the given groups.

    Variation 0 is a "request all variations" mechanism defined by
    the DNP3 specification. This utility builds a :class:`DNP3Objects`
    container where each requested group contains a variation 0 object.

    :param groups: One or more group identifiers.
    :type groups: int
    :return: A DNP3Objects container with variation 0 objects for the given groups.
    :rtype: DNP3Objects
    """
    objects = DNP3Objects()
    for group in groups:
        objects.add_variation0(group)
    return objects


def new_class_data_request(*classes: int) -> DNP3Objects:
    """Construct a DNP3 class data request.

    This function creates a :class:`DNP3Objects` container representing
    a request for event data belonging to the specified DNP3 classes
    (0-3). Each class corresponds to a variation within Group 60:

    - Class 0 :octicon:`arrow-right` Group 60 Variation 1
    - Class 1 :octicon:`arrow-right` Group 60 Variation 2
    - Class 2 :octicon:`arrow-right` Group 60 Variation 3
    - Class 3 :octicon:`arrow-right` Group 60 Variation 4

    :param classes: One or more class numbers (0-3).
    :type classes: int
    :return: A DNP3Objects container representing the class data request.
    :rtype: DNP3Objects
    """
    objects = DNP3Objects()
    for class_num in classes:
        if 0 <= class_num <= 3:
            objects.add_empty(60, class_num + 1)
    return objects
