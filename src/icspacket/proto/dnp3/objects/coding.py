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
"""
This module implements parsing and serialization of **DNP3 Application Layer
objects** according to section *4.2.2.7 Object Headers* of the DNP3
Specification.

Object headers carry information that a bare application header cannot
express. This library models each header as four pieces:

- **Group**: which data category is being carried (binary inputs, analog
  outputs, etc.).
- **Variation**: which on-the-wire layout was chosen for that data (packed,
  16-bit, 32-bit, etc.).
- **Qualifier fields**: how many objects to expect next, and which
  range/prefixing scheme locates them.
- **Objects**: the decoded values themselves.

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

from caterpillar.py import Pass, uint8, EnumFactory, pack_into, bitfield, f, unpack
from caterpillar.types import uint8_t

from icspacket.proto.dnp3.const import (
    APDU_PREFIX_TYPES,
    APDU_RANGE_TYPES,
    ObjectPrefixCode,
    RangeSpecifierCode,
)
from icspacket.proto.dnp3.objects.variations import get_variation


# /4.2.2.7 Object headers
# This bitfield is the fixed-size preamble that tags a batch of DNP3 objects
# with the addressing/type information the application header can't carry
# by itself.
@bitfield
class ObjectHeader:
    """Represents a **DNP3 Object Header**.

    Each instance pins down the group and variation that the following
    objects belong to, along with the qualifier fields describing how many
    objects to expect and how they are addressed or prefixed.
    """

    # fmt: off
    #: /4.2.2.7.1 Object group
    #: Identifies the data category the following objects belong to, whether
    #: this header is part of a master request or an outstation response.
    group: uint8_t

    #: /4.2.2.7.2 Object variation
    #: Selects the on-the-wire layout for objects in this group. This
    #: library uses the (group, variation) pair to look up the matching
    #: struct definition and decode the data accordingly.
    variation: uint8_t

    # 4.2.2.7.3 Qualifier and range fields
    reserved: f[int, 1] = 0
    #: /4.2.2.7.3.2 Object prefix code
    #: Selects whether each following object is preceded by a small value
    #: (an index or a size) and, if so, which kind.
    obj_prefix: f[ObjectPrefixCode | int, (3, EnumFactory(ObjectPrefixCode))] = ObjectPrefixCode.NONE

    #: /4.2.2.7.3.3 Range specifier codes
    range_spec: f[RangeSpecifierCode | int, (4, EnumFactory(RangeSpecifierCode))] = RangeSpecifierCode.NONE
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

    range_type: RangeSpecifierCode | int | None
    """
    Indicates the range encoding used for this variation (count or start/end).
    """

    range: tuple[int, int] | int | None
    """
    The decoded range value. May be a tuple ``(start, stop)`` for index ranges,
    an integer count, or ``None`` if not specified.
    """

    prefix_type: ObjectPrefixCode | int | None
    """
    Prefix encoding used for the objects (e.g., none, 1-byte, 2-byte index).
    """

    def __init__(self) -> None:
        super().__init__()
        self.range_type = None
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

        if self.range_type is None or self.range_type == RangeSpecifierCode.NONE:
            return None

        if int(self.range_type) >= 7:
            return len(self)

        if len(self) == 0:
            return None

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
    ) -> DNP3ObjectVariations:
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
        # Keep decoding (header, objects) pairs back-to-back until the
        # buffer runs out; a single fragment may carry any number of them.
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
        # Resolve the per-object prefix type so each object below can be
        # preceded by its index/size value while it is read from the stream.
        prefix_ty = APDU_PREFIX_TYPES.get(header.obj_prefix, Pass)
        target_variant = get_variation(header.group, header.variation)
        if not target_variant:
            raise ValueError(
                f"Unknown object variation {header.variation} for group {header.group}"
            )

        variation_instance = objects.get_variation(header.group, header.variation)
        variation_instance.range_type = header.range_spec
        variation_instance.range = (
            target_range  # pyright: ignore[reportAttributeAccessIssue]
        )
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
                    num_objects = len(instances)

                selected_range_type = (
                    instances.range_type
                    if instances.range_type is not None
                    else range_type
                )
                if selected_range_type is None:
                    if num_objects == 0:
                        selected_range_type = RangeSpecifierCode.NONE
                    elif num_objects <= 0xFF:
                        selected_range_type = RangeSpecifierCode.COUNT_8
                    elif num_objects <= 0xFFFF:
                        selected_range_type = RangeSpecifierCode.COUNT_16
                    else:
                        selected_range_type = RangeSpecifierCode.COUNT_32

                selected_prefix_type = (
                    instances.prefix_type
                    if instances.prefix_type is not None
                    else prefix_type
                )

                if instances.range is not None:
                    selected_range = instances.range
                elif selected_range_type == RangeSpecifierCode.NONE:
                    selected_range = None
                elif int(selected_range_type) >= 7:
                    selected_range = num_objects
                elif num_objects > 0:
                    selected_range = (instances[0].index, instances[-1].index)
                else:
                    selected_range = None

                header = ObjectHeader(
                    group=group_id,
                    variation=variation_id,
                    obj_prefix=selected_prefix_type,
                    range_spec=selected_range_type,
                )

                pack_into(header, stream)
                pack_into(  # pyright: ignore[reportCallIssue]
                    selected_range,
                    stream,
                    APDU_RANGE_TYPES.get(selected_range_type, Pass),
                )
                for object in instances if isinstance(instances, list) else [instances]:
                    pack_into(  # pyright: ignore[reportCallIssue]
                        object.prefix,
                        stream,
                        APDU_PREFIX_TYPES.get(selected_prefix_type, Pass),
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
