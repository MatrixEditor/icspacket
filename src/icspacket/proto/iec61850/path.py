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
from typing_extensions import Self, override

from icspacket.proto.iec61850.classes import FC, LN_Class, LN_Group
from icspacket.proto.mms._mms import ObjectName
from icspacket.proto.mms.util import domain_object_name


class ObjectReference:
    """
    IEC 61850 ACSI ObjectReference (IEC 61850-7-2 §5.5.3.3).

    An ObjectReference uniquely identifies instances in the ACSI class hierarchy
    (logical devices, logical nodes, data objects, sub-data objects, and data
    attributes). It is constructed by concatenating all instance names in the
    hierarchy.

    **IEC 61850 Representation**

    Format: ``LDName/LNName.DoName.SubDoName.AttrName``

    - ``/`` separates the logical device name (LDName) from the logical node
      name (LNName).
    - ``.`` separates deeper hierarchical levels (data objects, sub-data
      objects, attributes).

    Example::

        LD1/MMXU1.A.phsA.mag.f

    *MMS Representation**

    In MMS, ObjectReferences are encoded as a variable-length VisibleString:

    - Maximum length: 129 octets
    - ``.`` (dot) separators are replaced with ``$`` (dollar).
    - Example: ``LD1/MMXU1.A.phsA`` → ``LD1/MMXU1$A$phsA``

    .. note::
        The MMS representation contains an extra *functional constraint* (FC)
        between a logical node and its data objects.

    ObjectReferences can be built directly:

    >>> ObjectReference("LD1")
    "LD1"

    >>> ObjectReference("LD1", "MMXU1", "CO", "phsA")
    "LD1/MMXU1.CO.phsA"

    Or parsed from existing references:

    - :meth:`from_string` → parses IEC 61850 notation with ``.`` separators.
    - :meth:`from_mmsref` → parses MMS VisibleString with ``$`` separators.
    """

    def __init__(
        self, logical_device: str, /, logical_node: str | None = None, *names: str
    ) -> None:
        self.__parts = [logical_device]
        if logical_node:
            self.__parts.append(logical_node)
        self.__parts.extend(names)

    @property
    def ldname(self) -> str:
        """
        Return the logical device name (LDName).

        >>> ref = ObjectReference("LD1", "MMXU1", "A")
        >>> ref.ldname
        'LD1'
        """
        return self.__parts[0]

    @property
    def lnname(self) -> str | None:
        """
        Return the logical node name (LNName), or ``None`` if not present.

        >>> ref = ObjectReference("LD1", "MMXU1", "A")
        >>> ref.lnname
        'MMXU1'
        >>> ObjectReference("LD1").lnname is None
        True
        """
        return self.__parts[1] if len(self.__parts) > 1 else None

    @property
    def lnclass(self) -> LN_Class | None:
        """
        Resolve the LN class from the LNName, if available.

        >>> ref = ObjectReference("LD1", "MMXU1")
        >>> ref.lnclass
        LN_Class.MMXU
        """
        lnname = self.lnname
        if lnname:
            return LN_Class.from_lname(lnname)

    @property
    def lngroup(self) -> LN_Group | None:
        """
        Resolve the LN group from the first character of the LNName.

        >>> ref = ObjectReference("LD1", "MMXU1")
        >>> ref.lngroup
        LN_Group.M
        """
        lnname = self.lnname
        if lnname:
            try:
                return LN_Group[lnname[0]]
            except KeyError:
                pass

    @property
    def parts(self) -> list[str]:
        """
        Return the hierarchical components of the reference as a list.

        >>> ref = ObjectReference("LD1", "MMXU1", "A", "phsA")
        >>> ref.parts
        ['LD1', 'MMXU1', 'A', 'phsA']
        """
        return self.__parts

    def name(self, index: int) -> str:
        """
        Return the name of the component at the given hierarchy index.

        >>> ref = ObjectReference("LD1", "MMXU1", "A", "phsA")
        >>> ref.name(2)
        'A'
        """
        return self.__parts[index]

    def __truediv__(self, other: str) -> Self:
        """
        Extend the ObjectReference with another hierarchical part using `/`.

        >>> ObjectReference("LD1", "MMXU1") / "A"
        'LD1/MMXU1.A'
        """
        return self.__class__(self.ldname, *self.parts[1:], other)

    @override
    def __str__(self) -> str:
        """
        Return the IEC 61850 style reference:

        - ``/`` separates LDName from LNName
        - ``.`` separates deeper hierarchy parts

        >>> str(ObjectReference("LD1", "MMXU1", "A", "phsA"))
        'LD1/MMXU1.A.phsA'
        """
        if not self.lnname:
            return self.ldname
        ln_ref = "/".join([self.ldname, self.lnname])
        return ".".join([ln_ref] + self.__parts[2:])

    @override
    def __repr__(self) -> str:
        return repr(self.__str__())

    @classmethod
    def from_mmsref(cls: type[Self], reference: str) -> Self:
        """
        Parse an ObjectReference from an MMS VisibleString reference.

        >>> ObjectReference.from_mmsref("LD1/MMXU1$A$phsA")
        'LD1/MMXU1.A.phsA'
        """
        if "/" not in reference:
            return cls(reference)

        ldname, parts = reference.replace("$", ".").split("/", 1)
        return cls(ldname, *parts.split("."))

    @classmethod
    def from_string(cls: type[Self], reference: str) -> Self:
        """
        Parse an ObjectReference from an IEC 61850 style string.

        >>> ObjectReference.from_string("LD1/MMXU1.A.phsA")
        'LD1/MMXU1.A.phsA'
        """
        if "/" not in reference:
            return cls(reference)

        ldname, parts = reference.split("/", 1)
        return cls(ldname, *parts.split("."))

    @property
    def mmsref(self) -> str:
        """
        Return the MMS VisibleString form (with ``$`` separators).

        >>> ref = ObjectReference("LD1", "MMXU1", "A", "phsA")
        >>> ref.mmsref
        'LD1/MMXU1$A$phsA'
        """
        return str(self).replace(".", "$")

    @property
    def mms_name(self) -> ObjectName:
        """
        Return the MMS ObjectName corresponding to this reference.

        >>> ref = ObjectReference("LD1", "MMXU1", "A")
        >>> ref.mms_name
        ObjectName(domain='LD1', item='MMXU1$A')
        """
        path = "$".join(self.parts[1:])
        return domain_object_name(self.ldname, path)

    @override
    def __hash__(self) -> int:
        return hash(self.mmsref)

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, ObjectReference) and self.mmsref == other.mmsref


class DataObjectReference(ObjectReference):
    """
    Specialized ObjectReference for data objects with Functional Constraints.

    Format:

    ``<LNVariableName>$<FC>$<LNDataObjectName>[$<SubDataObjectName>...]``

    Example (IEC 61850-7-2 §5.5.3.3):

    ``MMXU1$MX$A$phsA``

    This maps into an ObjectReference hierarchy:

    >>> DataObjectReference("LD1", "MMXU1", "MX", "A", "phsA")
    'LD1/MMXU1.MX.A.phsA'
    """

    def __init__(
        self, logical_device: str, /, logical_node: str, fc: str, *names: str
    ) -> None:
        super().__init__(logical_device, logical_node, fc, *names)

    @property
    def functional_constraint(self) -> FC:
        """
        Return the Functional Constraint (FC) of this DataObjectReference.

        >>> ref = DataObjectReference("LD1", "MMXU1", "MX", "A", "phsA")
        >>> ref.functional_constraint
        FC.MX
        """
        return FC[self.parts[2]]

    @property
    def datname(self) -> str:
        """
        Return the data object name.

        >>> ref = DataObjectReference("LD1", "MMXU1", "MX", "A", "phsA")
        >>> ref.datname
        'A'
        """
        return self.parts[3]
