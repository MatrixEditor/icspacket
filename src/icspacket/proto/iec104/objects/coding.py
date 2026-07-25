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
This module implements the registry that maps an ASDU
:class:`~icspacket.proto.iec104.const.TypeID` to the information-element
struct used to encode/decode its objects, together with the SQ-aware
(:attr:`~icspacket.proto.iec104.asdu.VariableStructureQualifier.sq`)
packing/unpacking of a whole information-object list.

Every IEC 60870-5-101/104 ASDU Type-ID has exactly one on-the-wire
information-element layout, so the registry is keyed by a single
``type_id`` value.
"""

import io
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from caterpillar.abc import _StructLike
from caterpillar.py import pack_into, uint24, unpack
from caterpillar.shared import getstruct
from typing_extensions import TypeVar, overload, override

from icspacket.proto.iec104.const import TypeID

IOA_STRUCT = uint24
"""Wire format of an Information Object Address: an unsigned 24-bit
little-endian integer.
(See IEC 60870-5-101, clause 7.2.5)
"""


@dataclass
class InformationObject:
    """
    A single decoded information object: its address plus payload.

    :attr:`element` holds whatever struct instance is registered for the
    owning ASDU's Type-ID (e.g. an :class:`~icspacket.proto.iec104.objects.elements.SIQ`
    for :data:`~icspacket.proto.iec104.const.TypeID.M_SP_NA_1`).
    """

    ioa: int
    """Information Object Address (0 - 16777215)."""

    element: Any
    """The decoded information element, or ``None``/opaque bytes for
    unregistered Type-IDs."""


class ASDUType:
    """
    A single registered Type-ID -> information-element struct mapping.

    :param type_id: The ASDU Type-ID this entry describes.
    :param struct_ty: The struct type/instance used to encode/decode a
        single information element for this Type-ID.
    :param desc: Human-readable description (e.g. ``"Single-point
        information"``).
    """

    def __init__(
        self, type_id: TypeID, struct_ty: type | _StructLike, desc: str
    ) -> None:
        self.type_id: TypeID = type_id
        self.struct = getstruct(struct_ty, struct_ty)
        self.desc: str = desc

    @override
    def __repr__(self) -> str:
        return f"<ASDUType {self.type_id.name}>"


#: Registry of information-element structs by ASDU Type-ID.
__asdu_types__: dict[TypeID, ASDUType] = {}

#: Registry of human-readable Type-ID descriptions.
__asdu_type_desc__: dict[TypeID, str] = {}


def get_asdu_type(type_id: TypeID) -> ASDUType | None:
    """
    Look up a registered information-element struct by Type-ID.

    :param type_id: The ASDU Type-ID to look up.
    :return: The registered entry, or ``None`` if ``type_id`` is not
        (yet) implemented.
    """
    return __asdu_types__.get(type_id)


def get_asdu_type_desc(type_id: TypeID | int) -> str | None:
    """Retrieve the human-readable description of a Type-ID, if registered."""
    return __asdu_type_desc__.get(type_id)  # pyright: ignore[reportArgumentType]


def register_asdu_type(
    type_id: TypeID, struct_ty: type | _StructLike, desc: str
) -> ASDUType:
    """
    Register the information-element struct used for a given Type-ID.

    Most callers should use the :func:`asdu_type` decorator instead, which
    derives ``desc`` automatically and calls this function under the hood;
    this is exposed directly for cases where a struct is registered without
    also being decorated (e.g. reusing one struct for several Type-IDs).

    :param type_id: The ASDU Type-ID this entry describes.
    :param struct_ty: The struct type/instance used to encode/decode a
        single information element for this Type-ID.
    :param desc: Human-readable description.
    :return: The created registry entry.
    """
    entry = ASDUType(type_id, struct_ty, desc)
    __asdu_types__[type_id] = entry
    __asdu_type_desc__[type_id] = desc
    return entry


_T = TypeVar("_T")


@overload
def asdu_type(cls: type[_T]) -> type[_T]: ...
@overload
def asdu_type(cls: None = None) -> Callable[[type[_T]], type[_T]]: ...
def asdu_type(cls: type[_T] | None = None) -> type[_T] | Callable[[type[_T]], type[_T]]:
    """
    Decorator to register an information-object struct for its Type-ID.

    Reads the Type-ID from the decorated class' ``TYPE_ID`` attribute and
    the registry description from the first sentence of its docstring, then
    registers both via :func:`register_asdu_type`.
    """

    def decorator(struct_cls: type[_T]) -> type[_T]:
        type_id = getattr(struct_cls, "TYPE_ID", None)
        if not isinstance(type_id, TypeID):
            raise TypeError(
                f"ASDU information object class {struct_cls.__name__} must define TYPE_ID"
            )

        doc = " ".join(
            line.strip() for line in (struct_cls.__doc__ or "").strip().split("\n")
        )
        desc, _, _ = doc.partition(". ")
        _ = register_asdu_type(type_id, struct_cls, desc.rstrip("."))
        return struct_cls

    if cls is None:
        return decorator
    return decorator(cls)


def unpack_information_objects(
    type_id: TypeID, sq: bool, number: int, data: bytes
) -> list[InformationObject]:
    """
    Decode the information-object list carried by an ASDU.

    (See IEC 60870-5-101, clause 7.2.1 - structure of ASDU, for the SQ bit's
    effect on Information Object Address repetition.)

    :param type_id: The owning ASDU's Type-ID, selects which registered
        struct decodes each element.
    :param sq: The owning ASDU's VSQ ``sq`` bit. When ``False``, every
        object carries its own 3-octet IOA; when ``True``, only the first
        object does and subsequent objects use ``ioa + 1``, ``ioa + 2``, ...
    :param number: The owning ASDU's VSQ ``number`` field - how many
        objects to decode.
    :param data: Raw object bytes (an ASDU's payload after its 6-octet
        header).
    :raises ValueError: If ``type_id`` has no registered information
        element struct.
    :return: The decoded objects, always as a flat list regardless of the
        wire-level ``sq`` grouping.
    """
    entry = get_asdu_type(type_id)
    if entry is None:
        raise ValueError(f"No information object registered for {type_id!r}")

    stream = io.BytesIO(data)
    objects: list[InformationObject] = []
    ioa = 0
    for index in range(number):
        if index == 0 or not sq:
            ioa = unpack(IOA_STRUCT, stream, as_field=True)
        else:
            ioa += 1
        element = unpack(entry.struct, stream)
        objects.append(InformationObject(ioa=ioa, element=element))
    return objects


def pack_information_objects(
    type_id: TypeID, objects: list[InformationObject], sq: bool = False
) -> bytes:
    """
    Encode an information-object list the way an ASDU carries it.

    This is the inverse of :func:`unpack_information_objects`; callers are
    responsible for keeping the owning ASDU's ``vsq.number``/``vsq.sq``
    fields in sync with ``objects``/``sq`` (see
    :meth:`~icspacket.proto.iec104.asdu.ASDU.build`, which does this
    automatically).

    :param type_id: The owning ASDU's Type-ID, selects which registered
        struct encodes each element.
    :param objects: The objects to encode, in wire order.
    :param sq: Whether to use the sequential-address form (``True``: only
        the first object's IOA is written; every other object must have
        ``ioa == objects[0].ioa + index``) or the individually-addressed
        form (``False``: every object writes its own IOA).
    :raises ValueError: If ``type_id`` has no registered information
        element struct, or (when ``sq`` is ``True``) if ``objects``' IOAs
        are not contiguous.
    :return: The encoded raw object bytes.
    """
    entry = get_asdu_type(type_id)
    if entry is None:
        raise ValueError(f"No information object registered for {type_id!r}")

    stream = io.BytesIO()
    for index, obj in enumerate(objects):
        if index == 0 or not sq:
            pack_into(obj.ioa, stream, IOA_STRUCT, as_field=True)
        elif obj.ioa != objects[0].ioa + index:
            raise ValueError(
                "Non-contiguous IOA "
                + f"{obj.ioa} at index {index} (expected "
                + f"{objects[0].ioa + index}) while sq=True"
            )
        pack_into(obj.element, stream, entry.struct)
    return stream.getvalue()
