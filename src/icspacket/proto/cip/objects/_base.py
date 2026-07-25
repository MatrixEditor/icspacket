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
from io import BytesIO
from typing import Any, ClassVar, Generic

from caterpillar.abc import _ContextLike, _EndianLike, _StructLike
from caterpillar.exception import DynamicSizeError
from caterpillar.fields import Prefixed, Transformer, uint8, uint16
from caterpillar.py import FieldStruct, pack, unpack
from caterpillar.shortcuts import LittleEndian, sizeof
from typing_extensions import TypeVar, override

from ..connection import CIP_Connection
from ..const import ClassCode, CommonService
from ..epath import EPATH

_IT = TypeVar("_IT", default=bytes)


class CIPString(Transformer[str | bytes, bytes, str, bytes]):
    """Length-prefixed CIP string (SHORT_STRING or STRING).

    ``padded`` follows the CIP STRING type's word-alignment rule: a
    payload with an odd byte length is followed by one pad byte so the
    field always ends on a 16-bit boundary. SHORT_STRING
    (:data:`CIP_SHORT_STRING`) never pads; STRING (:data:`CIP_STRING`)
    does.
    """

    def __init__(self, prefix: _StructLike[int, int], padded: bool = False) -> None:
        super().__init__(Prefixed(prefix))
        self.padded: bool = padded

    @override
    def encode(self, obj: str | bytes, context: _ContextLike) -> bytes:
        return obj.encode("utf-8") if isinstance(obj, str) else bytes(obj)

    @override
    def decode(self, parsed: bytes, context: _ContextLike) -> str:
        if self.padded and len(parsed) & 1:
            context._io.read(1)
        return bytes(parsed).decode("utf-8")

    @override
    def pack_single(self, obj: str | bytes, context: _ContextLike) -> None:
        value = self.encode(obj, context)
        self.struct.__pack__(value, context)
        if self.padded and len(value) & 1:
            context._io.write(b"\x00")

    @property
    def minimum_size(self) -> int:
        """Bytes needed before the length prefix itself can be read."""
        return sizeof(self.struct.prefix)


#: SHORT_STRING: ``USINT`` length prefix, unpadded.
CIP_SHORT_STRING = CIPString(uint8)
#: STRING: ``UINT`` length prefix, word-padded.
CIP_STRING = CIPString(uint16, padded=True)


class CIPPrefixedEPATH(FieldStruct[EPATH, EPATH]):
    """CIP attribute shaped as ``UINT path_size`` (16-bit words) + EPATH bytes.

    Unlike :class:`CIPString`, the prefix here counts *words*, not
    bytes, so it cannot be expressed as a plain ``Prefixed`` wrapper;
    the word/byte conversion is done directly against the shared stream
    instead.
    """

    def __type__(self) -> type[EPATH]:
        return EPATH

    def __size__(self, context: _ContextLike):
        raise DynamicSizeError("Prefixed EPATH's size is dynamic", context)

    @override
    def unpack_single(self, context: _ContextLike) -> EPATH:
        words = uint16.__unpack__(context)
        payload: bytes = context._io.read(words * 2)
        if len(payload) != words * 2:
            raise ValueError("truncated CIP EPATH")

        return EPATH.from_bytes(payload) if payload else EPATH()

    @override
    def pack_single(self, obj: EPATH, context: _ContextLike) -> None:
        payload = obj.to_bytes()
        uint16.__pack__(len(payload) // 2, context)
        context._io.write(payload)


#: TCP/IP Interface Object attribute 4 (Physical Link Object): the one core
#: CIP attribute shaped as a word-counted EPATH rather than a raw one.
CIP_PREFIXED_EPATH = CIPPrefixedEPATH()


class CIPEPATH(FieldStruct[EPATH, EPATH]):
    """Bare CIP EPATH occupying an entire attribute payload.

    Unlike :class:`CIPPrefixedEPATH`, this has no length prefix of its own - it reads to
    the end of the current stream, so it is only valid as a whole-payload attribute
    schema and cannot be sequenced before other fields in a :class:`CIPAttributeReader`
    multi-attribute decode.
    """

    def __type__(self) -> type[EPATH]:
        return EPATH

    def __size__(self, context: _ContextLike):
        raise DynamicSizeError("EPATH size is dynamic", context)

    @override
    def unpack_single(self, context: _ContextLike) -> EPATH:
        payload: bytes = context._io.read()
        return EPATH.from_bytes(payload) if payload else EPATH()

    @override
    def pack_single(self, obj: EPATH, context: _ContextLike) -> None:
        context._io.write(obj.to_bytes())


#: Connection Object attributes 14/16 (Produced/Consumed Connection Path).
CIP_EPATH = CIPEPATH()


class CIPAttribute(Generic[_IT]):
    """Descriptor for one CIP object attribute's wire schema.

    Assign as a class attribute on a :class:`CIPObject` subclass;
    reading it issues Get_Attribute_Single and decodes the reply via
    ``schema``, writing it encodes the value and issues
    Set_Attribute_Single requiring an empty response. ``schema`` is any
    caterpillar field/struct or ``None`` for raw, undecoded bytes.
    """

    def __init__(
        self,
        id: int,
        schema: _StructLike[_IT, _IT] | type[_IT] | None = None,
        *,
        size: int | None = None,
        order: _EndianLike = LittleEndian,
    ) -> None:
        self.id: int = id
        self.schema: _StructLike[_IT, _IT] | type[_IT] | None = schema
        self.size: int | None = size
        self.attr_name: str = f"attribute {id}"
        self.order: _EndianLike = order

    def __set_name__(self, owner: type, name: str) -> None:
        self.attr_name = name
        # Each subclass gets its own dict - otherwise a subclass that never
        # declares one of its own would silently share (and pollute)
        # whichever base class's dict its MRO happens to resolve to.
        if "attribute_definitions" not in owner.__dict__:
            owner.attribute_definitions = {}
        owner.attribute_definitions[self.id] = self

    def __get__(self, obj: "CIPObject | None", objtype: type | None = None) -> _IT:
        if obj is None:
            return self  # pyright: ignore[reportReturnType]

        return self.from_bytes(obj.get(self.id))

    def __set__(self, obj: "CIPObject", value: _IT) -> None:
        _ = obj.set_empty(self.id, self.to_bytes(value))

    def from_bytes(self, data: bytes) -> _IT:
        """Decode a Get_Attribute_Single reply for this attribute."""
        if self.size is not None and len(data) != self.size:
            raise ValueError(f"{self.attr_name} must contain exactly {self.size} bytes")

        if self.schema is None:
            return data  # pyright: ignore[reportReturnType]

        return unpack(self.schema, data, order=self.order)

    def to_bytes(self, value: _IT) -> bytes:
        """Encode a value for Set_Attribute_Single."""
        if self.schema is None:
            return bytes(value)  # pyright: ignore[reportArgumentType]

        return pack(value, self.schema, order=self.order)

    @property
    def minimum_size(self) -> int | None:
        """Minimum bytes needed before this attribute might be stream-
        decodable.

        ``None`` means it cannot be decoded from a sequential stream at
        all; ``0`` means any amount (including none) is acceptable.
        """
        if self.size is not None:
            return self.size
        if self.schema is None:
            return 0
        own_minimum = getattr(self.schema, "minimum_size", None)
        if own_minimum is not None:
            return own_minimum
        try:
            return sizeof(self.schema)
        except DynamicSizeError:
            return 0 if hasattr(self.schema, "from_bytes") else None

    @property
    def stream_decodable(self) -> bool:
        """Whether this attribute can be decoded from the middle of a
        shared, multi-attribute stream (e.g. a ``Get_Attributes_All``
        reply) without over-consuming bytes that belong to a later
        attribute.

        True for any fixed-size schema (including an explicit :attr:`size`
        override) and for the self-delimiting :class:`CIPString`/
        :class:`CIPPrefixedEPATH` wrappers, each of which reads its own
        explicit length prefix and then stops. False for a schema with no
        fixed size that is *not* self-delimiting - e.g. a bare
        :class:`CIPEPATH` or a greedy ``schema[...]`` array sized by
        another attribute - since those read to the end of the stream
        regardless of where the next attribute's bytes begin.
        """
        if self.size is not None:
            return True
        if self.schema is None:
            return False
        if isinstance(self.schema, (CIPString, CIPPrefixedEPATH)):
            return True
        try:
            _ = sizeof(self.schema)
            return True
        except DynamicSizeError:
            return False


class CIPAttributeReader:
    """Sequential reader for variable CIP attribute payloads.

    Use this for ``Get_Attributes_All`` replies where fields are
    optional or followed by vendor-specific trailing data.  Fixed
    single-attribute getters should normally use a :class:`CIPAttribute`
    descriptor instead.
    """

    def __init__(self, data: bytes) -> None:
        self._data: bytes = bytes(data)
        self._stream: BytesIO = BytesIO(self._data)

    @property
    def remaining(self) -> int:
        """Number of unread bytes."""
        return len(self._data) - self._stream.tell()

    def read_field(self, schema: _StructLike[_IT, _IT]) -> _IT:
        """Decode one field from the shared stream using ``schema``."""
        return unpack(schema, self._stream, order=LittleEndian)

    def read_attributes(
        self,
        definitions: dict[int, CIPAttribute[Any]],
        attributes: tuple[int, ...] | list[int] | None = None,
        *,
        missing_ok: bool = True,
    ) -> dict[int, object]:
        """Decode sequential attributes using declarative definitions.

        The method stops before the first missing optional attribute or
        the first definition that cannot be safely decoded from a
        stream.
        """
        values: dict[int, object] = {}
        for attribute in attributes or sorted(definitions):
            definition = definitions[attribute]
            if not definition.stream_decodable:
                break
            minimum_size = definition.minimum_size
            if (
                missing_ok
                and minimum_size is not None
                and self.remaining < minimum_size
            ):
                break
            if missing_ok and minimum_size == 0 and self.remaining == 0:
                break

            value = None
            if definition.size is not None:
                data = self._stream.read(definition.size)
                value = definition.from_bytes(data)
            elif definition.schema is not None:
                value = unpack(definition.schema, self._stream, order=definition.order)

            values[attribute] = value
        return values

    def read_remaining(self) -> bytes:
        """Return all unread bytes."""
        return self._stream.read()


#: Registry of CIP object wrapper classes by class code, populated
#: automatically by :meth:`CIPObject.__init_subclass__`.
__cip_objects__: dict[int, type["CIPObject"]] = {}


class CIPObject:
    """Small typed facade over a :class:`~icspacket.proto.cip.CIP_Connection`.

    Subclasses that assign :attr:`CLASS_CODE` directly in their own body are
    registered automatically under that class code, for
    :func:`~icspacket.proto.cip.objects.registry.object_for`.
    """

    CLASS_CODE: ClassVar[ClassCode]
    attribute_definitions: ClassVar[dict[int, CIPAttribute[Any]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register ``cls`` under its own ``CLASS_CODE``, if it defines one."""
        super().__init_subclass__(**kwargs)
        class_code = cls.__dict__.get("CLASS_CODE")
        if isinstance(class_code, ClassCode):
            __cip_objects__[int(class_code)] = cls

    def __init__(self, connection: CIP_Connection, instance: int = 1) -> None:
        self.connection: CIP_Connection = connection
        self.instance: int = instance

    def _resolve_instance(self, instance: int | None) -> int:
        """Return ``instance`` if given, otherwise this object's own
        instance."""
        return self.instance if instance is None else instance

    def path(
        self, attribute: int | None = None, *, instance: int | None = None
    ) -> EPATH:
        """Build the EPATH addressing this object, optionally down to one
        attribute.

        :param attribute: Narrows the path to one specific attribute, if
            given.
        :param instance: Overrides this object's own instance, if given.
        """
        return self.connection.object_path(
            self.CLASS_CODE, self._resolve_instance(instance), attribute
        )

    def get(self, attribute: int, *, instance: int | None = None) -> bytes:
        """Read one attribute's raw bytes via Get_Attribute_Single.

        :param attribute: The attribute ID to read.
        :param instance: Overrides this object's own instance, if given.
        """
        return bytes(
            self.connection.get_attribute_single(
                self.CLASS_CODE, self._resolve_instance(instance), attribute
            )
        )

    def set(
        self, attribute: int, value: bytes, *, instance: int | None = None
    ) -> bytes:
        """Write one attribute's raw bytes via Set_Attribute_Single.

        :param attribute: The attribute ID to write.
        :param value: The encoded attribute value.
        :param instance: Overrides this object's own instance, if given.
        """
        return bytes(
            self.connection.set_attribute_single(
                self.CLASS_CODE,
                self._resolve_instance(instance),
                attribute,
                bytes(value),
            )
        )

    def all(self, *, instance: int | None = None) -> bytes:
        """Read every attribute's raw bytes via Get_Attributes_All.

        :param instance: Overrides this object's own instance, if given.
        """
        return bytes(
            self.connection.get_attributes_all(
                self.CLASS_CODE, self._resolve_instance(instance)
            )
        )

    def message(
        self,
        service: int | CommonService,
        request_data: bytes = b"",
        *,
        connected: bool = False,
        instance: int | None = None,
    ) -> bytes:
        """Issue a generic (non-Get/Set_Attribute) service request to this
        object.

        :param service: The CIP service code to invoke.
        :param request_data: The service-specific request payload.
        :param connected: Send over the connected (Class 3) session if
            ``True``.
        :param instance: Overrides this object's own instance, if given.
        """
        return bytes(
            self.connection.generic_message(
                service,
                self.path(instance=instance),
                bytes(request_data),
                connected=connected,
            )
        )

    @staticmethod
    def _expect_empty(data: bytes) -> bytes:
        """Return ``data`` unchanged, or raise ``ValueError`` if it's non-
        empty."""
        if data:
            raise ValueError(f"expected an empty response, got {len(data)} bytes")
        return data

    def get_attr(self, attribute: int, *, instance: int | None = None) -> _IT | bytes:
        """Read and decode one attribute using :attr:`attribute_definitions`.

        Falls back to raw bytes if ``attribute`` has no registered
        :class:`CIPAttribute` definition.

        :param attribute: The attribute ID to read.
        :param instance: Overrides this object's own instance, if given.
        """
        definition = self.attribute_definitions.get(attribute)
        data = self.get(attribute, instance=instance)
        return data if definition is None else definition.from_bytes(data)

    def set_empty(
        self,
        attribute: int,
        value: bytes,
        *,
        instance: int | None = None,
    ) -> bytes:
        """Write an attribute and require an empty service response.

        :param attribute: The attribute ID to write.
        :param value: The encoded attribute value.
        :param instance: Overrides this object's own instance, if given.
        """
        return self._expect_empty(self.set(attribute, value, instance=instance))
