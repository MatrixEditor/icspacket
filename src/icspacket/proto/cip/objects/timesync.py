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

"""[ODVA CIP Vol 1] Wrapper for the Time Sync Object (class 0x43, §5-47).

Provides a CIP interface to the IEEE 1588 (PTP) clock of a CIP Sync
capable device: clock synchronization status, offsets, and
Grandmaster/Parent/Local clock property structs.
"""

from collections.abc import Collection
from typing import ClassVar

from caterpillar.fields import Bytes, int8, int16, int64, uint8
from caterpillar.model import StructDefMixin
from caterpillar.shortcuts import LittleEndian, f, struct
from caterpillar.types import int16_t, int32_t

from ..const import ClassCode
from ._base import CIPAttribute, CIPObject

__all__ = ["ClockInfo", "ParentClockInfo", "TimeSyncObject"]


@struct(order=LittleEndian)
class ClockInfo(StructDefMixin):
    """Grandmaster/Local Clock Info payload shape (attributes 8 and 10, See
    §5-47.13.1.8/.10)."""

    identifier: f[bytes, Bytes(4)]
    """4-character clock identifier (e.g. ``b"DFLT"``)."""

    stratum: int16_t
    variance: int16_t
    communication_technology: int16_t
    """Clock communication technology specifier (See Table 5-47.5)."""

    port_id: int16_t
    uuid: f[bytes, Bytes(6)]
    """CommunicationTechnology + UUID + PortID make up the clock's UUID (See
    Table 5-47.6)."""


@struct(order=LittleEndian)
class ParentClockInfo(StructDefMixin):
    """Parent Clock Info payload shape (attribute 9, See §5-47.13.1.9)."""

    reserved: int32_t
    observed_drift: int32_t
    observed_variance: int16_t
    variance: int16_t
    communication_technology: int16_t
    port_id: int16_t
    uuid: f[bytes, Bytes(6)]


class TimeSyncObject(CIPObject):
    """Provides a CIP interface to an IEEE 1588 (PTP) clock (See CIP Vol 1,
    §5-47).

    Any CIP Sync capable device provides a single instance (instance 1) of
    this object. ``port_state``/``port_enable``/``port_burst_enable`` are
    INT-count-prefixed SINT arrays sized by :attr:`number_of_ports`, which
    caterpillar decodes directly (the count prefix lives inside the same
    attribute payload, unlike the cross-attribute-dependent fields seen in
    other objects).
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.TIME_SYNC

    enable_ptp: CIPAttribute[int] = CIPAttribute(1, uint8)
    """Enables (1) or disables (0) the Precision Time Protocol on this device
    (attribute 1)."""

    is_synchronized: CIPAttribute[int] = CIPAttribute(2, uint8)
    """1 if the local clock is synchronized with the reference clock (attribute
    2)."""

    current_time_microseconds: CIPAttribute[int] = CIPAttribute(3, int64)
    """Current local_time in microseconds since 1970-01-01 00:00 UTC (attribute
    3)."""

    current_time_nanoseconds: CIPAttribute[int] = CIPAttribute(4, int64)
    """Current local_time in nanoseconds since 1970-01-01 00:00 UTC (attribute
    4)."""

    offset_to_master: CIPAttribute[int] = CIPAttribute(5, int64)
    """Deviation between the local clock and the reference clock, in
    nanoseconds (attribute 5)."""

    max_offset_to_master: CIPAttribute[int] = CIPAttribute(6, int64)
    """Maximum offset_to_master seen since last reinitialized; settable to
    reset it (attribute 6)."""

    delay_to_master: CIPAttribute[int] = CIPAttribute(7, int64)
    """Path delay between the local clock and master clock, in nanoseconds
    (attribute 7)."""

    grandmaster_clock_info: CIPAttribute[ClockInfo] = CIPAttribute(8, ClockInfo)
    """Property info of the Grandmaster PTP clock (attribute 8)."""

    parent_clock_info: CIPAttribute[ParentClockInfo] = CIPAttribute(9, ParentClockInfo)
    """Property info of the Parent PTP clock (attribute 9)."""

    local_clock_info: CIPAttribute[ClockInfo] = CIPAttribute(10, ClockInfo)
    """Property info of the Local PTP clock (attribute 10)."""

    number_of_ports: CIPAttribute[int] = CIPAttribute(11, int8)
    """Number of PTP ports implemented by this clock (attribute 11)."""

    port_state: CIPAttribute[Collection[int]] = CIPAttribute(12, int8[int16::])
    """Per-port PTP state, one entry per :attr:`number_of_ports` (attribute
    12)."""

    port_enable: CIPAttribute[Collection[int]] = CIPAttribute(13, int8[int16::])
    """Per-port enable status, one entry per :attr:`number_of_ports` (attribute
    13)."""

    port_burst_enable: CIPAttribute[Collection[int]] = CIPAttribute(14, int8[int16::])
    """Per-port burst-enable status, one entry per :attr:`number_of_ports`
    (attribute 14)."""

    sync_interval: CIPAttribute[int] = CIPAttribute(15, int8)
    """PTP Sync message interval (attribute 15)."""

    preferred_master: CIPAttribute[int] = CIPAttribute(16, uint8)
    """Designates this clock as a preferred PTP master when non-zero (attribute
    16)."""

    subdomain: CIPAttribute[bytes] = CIPAttribute(17, Bytes(16))
    """Fixed 16-byte PTP clock subdomain name (attribute 17)."""

    clock_mode: CIPAttribute[int] = CIPAttribute(18, int8)
    """0=Slave Only/Ordinary, 1=Master Capable/Ordinary, 2=Master
    Capable/Boundary (attribute 18)."""

    steps_removed: CIPAttribute[int] = CIPAttribute(19, int16)
    """Number of communication paths between the local clock and the
    grandmaster clock (attribute 19, optional)."""

    system_time_offset: CIPAttribute[int] = CIPAttribute(20, int64)
    """Offset applied to the local clock under the CIP Sync offset clock model
    (attribute 20, optional)."""

    def initialize(self) -> bytes:
        """Invoke Initialize (service 0x4B), resetting the PTP clock to its
        power-up state and re-synchronizing."""
        return self._expect_empty(self.message(0x4B))

    def management_message(self, request_data: bytes) -> bytes:
        """Invoke ManagementMessage (service 0x4A) with a caller-built native
        PTP management message payload.

        The full set of PTP management commands (See Table 5-47.11, e.g.
        ``ObtainIdentity``, ``SetSyncInterval``, ``EnablePort``) is
        defined by the IEEE 1588 standard rather than this library, so
        the request/response payload is passed through unmodified.
        """
        return self.message(0x4A, request_data)
