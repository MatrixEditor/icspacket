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
This module implements parsing and serialization of **DNP3 Application Layer
objects** as defined in section *4.2.2.7 Object Headers* of the DNP3
specification.

In DNP3, object headers describe data structures that cannot be conveyed
through the application header alone. Each object header specifies:

- **Group**: The type of data (e.g., binary inputs, analog outputs).
- **Variation**: The representation of the data (e.g., packed, 16-bit, 32-bit).
- **Qualifier fields**: Indicate how many objects follow and what range or
  prefixing mechanism is applied.
- **Objects**: The actual data values.

Example: Class0123 Request
--------------------------

.. code-block:: python

    # no prefix and no range needed here
    objects = DNP3Objects()
    objects.add_emtpy(60, 1) # object 60, variation 1 (Class 0)
    objects.add_emtpy(60, 2) # object 60, variation 2 (Class 1)
    objects.add_emtpy(60, 3) # object 60, variation 3 (Class 2)
    objects.add_emtpy(60, 4) # object 60, variation 4 (Class 3)

    encoded = pack_objects(objects)

    # ...

"""

import io
import dataclasses
from typing import Any

from caterpillar.fields import Pass, uint8
from caterpillar.model import EnumFactory, pack_into
from caterpillar.shortcuts import bitfield, unpack

from icspacket.proto.dnp3.const import (
    APDU_PREFIX_TYPES,
    APDU_RANGE_TYPES,
    ObjectPrefixCode,
    RangeSpecifierCode,
)
from icspacket.proto.dnp3.objects.variations import get_variation


# /4.2.2.7 Object headers
# object headers and objects provide supplementary information as required when
# the application header alone cannot convey the complete message.
@bitfield
class ObjectHeader:
    """Represents a **DNP3 Object Header**.

    Object headers provide additional context about a set of objects
    transmitted in the Application Layer. They define the group, variation,
    and addressing/range information for associated data objects.
    """

    # fmt: off
    #: /4.2.2.7.1 Object group
    #: The object group specifies what data type or values are included in a
    #: master request or in an outstation response.
    group           : uint8

    #: /4.2.2.7.2 Object variation
    #: Specifies the data format of DNP3 objects. The object group and object variation
    #: together uniquely specify the structure of a DNP3 object and the type of data that
    #: it references.
    variation       : uint8

    # 4.2.2.7.3 Qualifier and range fields
    reserved        : (1, int)                             = 0
    #: /4.2.2.7.3.2 Object prefix code
    #: Specifies what, if any, prefix value appears before each of the DNP3
    #: objects that follow the object header. Prefixes are either an index number
    #: or an object size.
    obj_prefix      : (3, EnumFactory(ObjectPrefixCode))   = ObjectPrefixCode.NONE

    #: /4.2.2.7.3.3 Range specifier codes
    range_spec      : (4, EnumFactory(RangeSpecifierCode)) = RangeSpecifierCode.NONE
    # fmt: on


# Simple storage object that represents a transmitted DNP3 object
@dataclasses.dataclass
class DNP3Object:
    """
    Represents a single transmitted **DNP3 object instance**.

    A DNP3 object may optionally include a prefix (such as an index),
    followed by its data value.
    """

    prefix: int | None
    """Parsed prefix value (if present). This may represent an index or size."""
    index: int
    """Sequential index of this object within its variation."""
    instance: Any
    """The parsed data payload for this object (actual value)."""


class DNP3ObjectVariations(list[DNP3Object]):
    """
    Represents all **objects of a given variation** within a group.

    Extends ``list[DNP3Object]`` to hold multiple instances of the same
    group/variation. Additional metadata about range and prefixing is stored
    here for proper serialization.

    >>> v = DNP3ObjectVariations() # generic interface
    >>> v.add(DNP3ObjectG2V1(state=1))
    """

    range_type: RangeSpecifierCode
    """
    Indicates the range encoding used for this variation (count or start/end).
    """

    range: tuple[int, int] | int | None
    """
    The decoded range value. May be a tuple ``(start, stop)`` for index ranges,
    an integer count, or ``None`` if not specified.
    """

    prefix_type: ObjectPrefixCode | None
    """
    Prefix encoding used for the objects (e.g., none, 1-byte, 2-byte index).
    """

    def __init__(self) -> None:
        super().__init__()
        self.range_type = RangeSpecifierCode.NONE
        self.range = None
        self.prefix_type = None

    def get_range(self) -> tuple[int, int] | int | None:
        """
        Compute the effective range of objects for this variation.

        If an explicit range is already set, it is returned. Otherwise,
        derives the range based on the range type.

        :return: The start/end tuple, object count, or ``None``.
        :rtype: tuple[int, int] | int | None
        """
        if self.range is not None:
            return self.range

        if int(self.range_type) >= 7:
            return len(self)

        if self.range_type != RangeSpecifierCode.NONE:
            return (self[0].index, self[-1].index)

    def add(
        self, value: Any, /, prefix: int | None = None, index: int | None = None
    ) -> None:
        """
        Add a new object instance to this variation.

        :param Any value: The parsed object payload.
        :param int | None prefix: Optional prefix (e.g., index) associated
            with this object.
        :param int | None index: Explicit index. Defaults to sequential numbering.
        """
        if index is None:
            index = len(self)

        self.append(DNP3Object(prefix, index, value))


class DNP3Objects(dict[int, dict[int, DNP3ObjectVariations | None]]):
    """
    A container for all **DNP3 objects in a fragment**.

    Maps group numbers to variations, which then contain one or more
    object instances.

    Structure::

        DNP3Objects[group][variation] -> DNP3ObjectVariations
    """

    def __init__(self) -> None:
        super().__init__()

    def get_variation(
        self, group: int, variation: int, /
    ) -> DNP3ObjectVariations | None:
        """
        Retrieve or create a variation container for the given group/variation.

        :param int group: DNP3 object group number.
        :param int variation: DNP3 object variation number.
        :return: A variation container if known, otherwise ``None``.
        :rtype: DNP3ObjectVariations | None
        """
        group_instance = self.setdefault(group, {})
        return group_instance.setdefault(variation, DNP3ObjectVariations())

    def add_variation0(self, group: int, /) -> None:
        self.add_empty(group, 0)

    def add_empty(self, group: int, variation: int, /) -> None:
        _ = self.setdefault(group, {}).setdefault(variation, None)


def unpack_objects(object_data: bytes) -> DNP3Objects:
    """
    Parse raw DNP3 object data into structured representations.

    Reads one or more object headers and associated objects from
    a byte sequence. Automatically handles range specifiers, prefix
    codes, and object variations.

    :param bytes object_data: Encoded DNP3 object data.
    :return: A structured mapping of groups, variations, and parsed objects.
    :rtype: DNP3Objects
    :raises ValueError: If an unknown object variation is encountered.
    """
    stream = io.BytesIO(object_data)
    objects = DNP3Objects()
    # /4.2.2.1 General fragment structure
    while stream.tell() < len(object_data):
        # one or more sets of object headers and possibly DNP3 objects are
        # included after the application header
        header = unpack(ObjectHeader, stream)
        target_range = unpack(
            APDU_RANGE_TYPES.get(header.range_spec, Pass),
            stream,
            as_field=True,
        )
        # The number of objects will be specified by the range
        num_objects = 0
        start = stop = 0
        match target_range:
            case int():
                num_objects = target_range
                stop = num_objects
            case list():
                num_objects = (target_range[1] + 1) - target_range[0]
                start = target_range[0]
                stop = target_range[1] + 1
            case _:
                pass

        # /4.2.2.7.3.2 Object prefix code
        # It specifies what, if any, prefix value appears before each of the
        # DNP3 objects that follow the object header.
        prefix_ty = APDU_PREFIX_TYPES.get(header.obj_prefix, Pass)
        target_variant = get_variation(header.group, header.variation)
        if not target_variant:
            raise ValueError(
                f"Unknown object variation {header.variation} for group {header.group}"
            )

        variation_instance = objects.get_variation(header.group, header.variation)
        variation_instance.range_type = header.range_spec
        variation_instance.range = target_range
        variation_instance.prefix_type = header.obj_prefix
        for index in range(start, stop):
            prefix = unpack(prefix_ty, stream, as_field=True)
            value = unpack(
                target_variant,
                stream,
                range=target_range,
                range_count=num_objects,
                prefic=prefix,
            )
            if value:
                if target_variant.is_packed:
                    for real_value in value:
                        variation_instance.add(real_value, prefix)
                else:
                    variation_instance.add(value, prefix, index)
            if target_variant.is_packed:
                # all objects are packed within one value
                break

        if num_objects == 0:
            objects[header.group][header.variation] = None

    return objects


def pack_objects(
    objects: DNP3Objects,
    prefix_type: ObjectPrefixCode | None = None,
    range_type: RangeSpecifierCode | None = None,
) -> bytes:
    """
    Serialize structured DNP3 objects into raw bytes.

    Iterates over all object groups and variations in the provided
    container, generating object headers, range/prefix encodings,
    and packed values.

    :param DNP3Objects objects: Structured DNP3 objects to serialize.
    :param ObjectPrefixCode | None prefix_type: Default prefix type to
        apply when none is specified.
    :param RangeSpecifierCode | None range_type: Default range type to
        apply when none is specified.
    :return: Encoded object data suitable for transmission.
    :rtype: bytes
    :raises ValueError: If an unknown object variation is encountered.
    """
    if prefix_type is None:
        prefix_type = ObjectPrefixCode.NONE
    if range_type is None:
        range_type = RangeSpecifierCode.NONE

    stream = io.BytesIO()
    for group_id, variations in objects.items():
        for variation_id, instances in variations.items():
            num_objects = 0
            if instances is not None:
                variation = get_variation(group_id, variation_id)
                if not variation:
                    raise ValueError(
                        f"Unknown object variation {variation_id} for group {group_id}"
                    )

                if isinstance(instances, list):
                    num_objects = len(objects)

                if instances.range_type is None:
                    if range_type == RangeSpecifierCode.NONE and num_objects > 0:
                        # automatically use a simple range specifier
                        if num_objects > 255:
                            range_type = RangeSpecifierCode.COUNT_32
                        else:
                            range_type = RangeSpecifierCode.COUNT_8
                    instances.range_type = range_type

                if instances.prefix_type is None:
                    instances.prefix_type = prefix_type

                header = ObjectHeader(
                    group=group_id,
                    variation=variation_id,
                    obj_prefix=instances.prefix_type,
                    range_spec=instances.range_type,
                )

                pack_into(header, stream)
                pack_into(
                    instances.get_range(),
                    stream,
                    APDU_RANGE_TYPES.get(instances.range_type, Pass),
                )
                for object in instances if isinstance(instances, list) else [instances]:
                    pack_into(
                        object.prefix,
                        stream,
                        APDU_PREFIX_TYPES.get(instances.prefix_type, Pass),
                    )
                    if variation.is_packed:
                        value = [v.instance for v in instances]
                        pack_into(value, stream, variation)
                        break
                    pack_into(object.instance, stream, variation, prefix=object.prefix)
            else:
                header = ObjectHeader(group=group_id, variation=variation_id)
                pack_into(header, stream)

    return stream.getvalue()
