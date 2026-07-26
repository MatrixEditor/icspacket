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

"""[ODVA CIP Vol 2] Wrapper for the CIP TCP/IP Interface Object (class 0xF5).

Instance attributes and the Get_Attributes_All reply layout are defined
according to §5-4.3.2 and §5-4.4.2 (Tables 5-4.8 and 5-4.13).
"""

from dataclasses import dataclass
from typing import ClassVar

from caterpillar.fields import uint32
from caterpillar.model import StructDefMixin
from caterpillar.shortcuts import LittleEndian, f, struct
from caterpillar.types import uint32_t

from ..const import ClassCode
from ..epath import EPATH
from ._base import (
    CIP_PREFIXED_EPATH,
    CIP_STRING,
    CIPAttribute,
    CIPAttributeReader,
    CIPObject,
)


@struct(order=LittleEndian)
class InterfaceConfiguration(StructDefMixin):
    """TCP/IP Interface Object Attribute 5, Interface Configuration.

    (See CIP Vol 2, §5-4.3.2.5, Table 5-4.8)
    """

    ip_address: uint32_t
    """This device's own IPv4 address."""

    network_mask: uint32_t
    """This device's IPv4 network mask."""

    gateway: uint32_t
    """Address of this device's default gateway -- the router it hands off
    traffic to for destinations outside the local subnet."""

    name_server: uint32_t
    """Address of the primary name server this device is configured to
    query."""

    name_server_2: uint32_t
    """Address of the secondary name server this device is configured to
    query."""

    domain_name: f[str, CIP_STRING]
    """Default domain name configured on this device."""


@dataclass
class TCPIPAttributes:
    """Instance-level Get_Attributes_All reply (See CIP Vol 2, §5-4.4.2, Table
    5-4.13).

    Trailing attributes beyond ``host_name`` (Safety Network Number,
    TTL, Mcast Config, ACD status, QuickConnect, Encapsulation
    Inactivity Timeout) are vendor/implementation dependent and are
    exposed verbatim via ``extra`` rather than individually decoded.
    """

    status: int
    configuration_capability: int
    configuration_control: int
    physical_link_object: EPATH
    interface_configuration: InterfaceConfiguration | None
    host_name: str
    extra: bytes = b""


class TCPIPInterfaceObject(CIPObject):
    """Typed access to TCP/IP Interface attributes (See CIP Vol 2, §5-4.3.2,
    Table 5-4.3)."""

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.TCP_IP_INTERFACE

    status: CIPAttribute[int] = CIPAttribute(1, uint32)
    """Interface status (attribute 1)."""

    configuration_capability: CIPAttribute[int] = CIPAttribute(2, uint32)
    """Configuration capability flags (attribute 2)."""

    configuration_control: CIPAttribute[int] = CIPAttribute(3, uint32)
    """Configuration control flags (attribute 3)."""

    physical_link_object: CIPAttribute[EPATH] = CIPAttribute(4, CIP_PREFIXED_EPATH)
    """Physical Link Object path (attribute 4)."""

    interface_configuration: CIPAttribute[InterfaceConfiguration] = CIPAttribute(
        5, InterfaceConfiguration
    )
    """Interface Configuration structure (attribute 5)."""

    host_name: CIPAttribute[str] = CIPAttribute(6, CIP_STRING)
    """Host Name string (attribute 6)."""

    def _decode_all(self, data: bytes) -> TCPIPAttributes:
        reader = CIPAttributeReader(data)
        values = reader.read_attributes(self.attribute_definitions, [1, 2, 3, 4])
        interface_configuration = None
        if reader.remaining >= 20:
            ip_address = reader.read_field(uint32)
            network_mask = reader.read_field(uint32)
            gateway = reader.read_field(uint32)
            name_server = reader.read_field(uint32)
            name_server_2 = reader.read_field(uint32)
            domain_name = reader.read_field(CIP_STRING)
            interface_configuration = InterfaceConfiguration(
                ip_address,
                network_mask,
                gateway,
                name_server,
                name_server_2,
                domain_name,
            )
        host_name = reader.read_field(CIP_STRING)
        return TCPIPAttributes(
            values.get(1, 0),  # pyright: ignore[reportArgumentType]
            values.get(2, 0),  # pyright: ignore[reportArgumentType]
            values.get(3, 0),  # pyright: ignore[reportArgumentType]
            values.get(4, EPATH()),  # pyright: ignore[reportArgumentType]
            interface_configuration,
            host_name,
            reader.read_remaining(),
        )

    def get_attributes(self) -> TCPIPAttributes:
        """Read and decode Get_Attributes_All for TCP/IP Interface."""
        return self._decode_all(self.all())


__all__ = ["InterfaceConfiguration", "TCPIPAttributes", "TCPIPInterfaceObject"]
