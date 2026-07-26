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

"""[ODVA CIP Vol 1] Wrappers for the File Object (class 0x37, §5-42) and Event
Log Object (class 0x41, §5-45)."""

from collections.abc import Collection
from typing import ClassVar

from caterpillar.fields import int16, uint8, uint16, uint32
from caterpillar.model import StructDefMixin
from caterpillar.shortcuts import LittleEndian, struct
from caterpillar.types import uint8_t

from ..const import ClassCode, CommonService
from ._base import CIPAttribute, CIPObject

__all__ = ["EventLogObject", "FileObject", "FileRevision"]


@struct(order=LittleEndian)
class FileRevision(StructDefMixin):
    """File Object attribute 5 payload (See CIP Vol 1, §5-42.2, Table
    5-42.3)."""

    major_rev: uint8_t
    minor_rev: uint8_t


class FileObject(CIPObject):
    """Manages an uploadable/downloadable file, e.g. firmware or configuration
    data (See CIP Vol 1, §5-42).

    ``instance_name``/``file_name`` are STRINGI (international string)
    encoded (See Appendix I) and ``directory``/the file transfer
    services' request/response payloads have their own internal framing,
    so they are all exposed as raw bytes rather than a fixed schema.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.FILE

    state: CIPAttribute[int] = CIPAttribute(1, uint8)
    """0=Nonexistent, 1=File Empty, 2=File Loaded, 3-6=Transfer in progress,
    7=Storing (attribute 1)."""

    instance_name: CIPAttribute[bytes] = CIPAttribute(2)
    """STRINGI name assigned to this instance (attribute 2)."""

    instance_format_version: CIPAttribute[int] = CIPAttribute(3, uint16)
    """Format version of this instance (attribute 3)."""

    file_name: CIPAttribute[bytes] = CIPAttribute(4)
    """STRINGI name assigned to the file loaded in this instance (attribute
    4)."""

    file_revision: CIPAttribute[FileRevision] = CIPAttribute(5, FileRevision)
    """Major/minor revision of the loaded file (attribute 5)."""

    file_size: CIPAttribute[int] = CIPAttribute(6, uint32)
    """Size of the loaded file in bytes (attribute 6)."""

    file_checksum: CIPAttribute[int] = CIPAttribute(7, int16)
    """Checksum of the loaded file (attribute 7)."""

    invocation_method: CIPAttribute[int] = CIPAttribute(8, uint8)
    """0=none, 1=Reset Identity, 2=power cycle, 3=Start service required, ...

    (attribute 8).
    """

    file_save_parameters: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Bit flags describing the file's non-volatile storage (attribute 9)."""

    file_type: CIPAttribute[int] = CIPAttribute(10, uint8)
    """0 = Read/Write (default), 1 = Read Only (attribute 10)."""

    file_encoding_format: CIPAttribute[int] = CIPAttribute(11, uint8)
    """Encoding format of the file's data, if any (attribute 11, optional, See
    §5-42.8)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a File class attribute from instance 0 (See §5-42.1, Table
        5-42.2)."""
        return self.get_attr(attribute, instance=0)

    def create(self, instance_name: bytes = b"") -> bytes:
        """Invoke Create, allocating a new file transfer instance
        (``instance_name`` is a STRINGI payload)."""
        return self.message(CommonService.CREATE, instance_name, instance=0)

    def delete(self) -> bytes:
        """Invoke Delete, removing a file transfer instance previously
        allocated via :meth:`create`."""
        return self._expect_empty(self.message(CommonService.DELETE))

    def save(self) -> bytes:
        """Invoke Save, persisting the loaded file to non-volatile storage."""
        return self._expect_empty(self.message(CommonService.SAVE))

    def restore(self) -> bytes:
        """Invoke Restore, reloading the file from non-volatile storage."""
        return self._expect_empty(self.message(CommonService.RESTORE))

    def initiate_upload(self, maximum_transfer_size: int) -> bytes:
        """Invoke Initiate_Upload (service 0x4B), starting a file upload.

        :param maximum_transfer_size: Maximum number of bytes this
            client can accept in each Upload_Transfer response (USINT).
        """
        request_data = uint8.to_bytes(int(maximum_transfer_size), order=LittleEndian)
        return self.message(0x4B, request_data)

    def initiate_download(self, request_data: bytes) -> bytes:
        """Invoke Initiate_Download (service 0x4C) with a caller-built request
        payload, starting a file download."""
        return self.message(0x4C, request_data)

    def initiate_partial_read(self, request_data: bytes) -> bytes:
        """Invoke Initiate_Partial_Read (service 0x4D) with a caller-built
        request payload."""
        return self.message(0x4D, request_data)

    def initiate_partial_write(self, request_data: bytes) -> bytes:
        """Invoke Initiate_Partial_Write (service 0x4E) with a caller-built
        request payload."""
        return self.message(0x4E, request_data)

    def upload_transfer(self, request_data: bytes) -> bytes:
        """Invoke Upload_Transfer (service 0x4F) with a caller-built request
        payload."""
        return self.message(0x4F, request_data)

    def download_transfer(self, request_data: bytes) -> bytes:
        """Invoke Download_Transfer (service 0x50) with a caller-built request
        payload."""
        return self.message(0x50, request_data)

    def clear_file(self) -> bytes:
        """Invoke Clear_File (service 0x51), clearing the loaded file's
        contents and resetting its attributes."""
        return self._expect_empty(self.message(0x51))


class EventLogObject(CIPObject):
    """Provides event indication and/or a time-stamped event log on a CIP node
    (See CIP Vol 1, §5-45).

    ``instance_name`` is STRINGI-encoded, and the event/log list attributes
    (4, 14, 16, 18) are arrays of structures whose per-entry layout is
    selected by ``event_identifier_format``/the class-level Time Format
    attribute, so all of these are exposed as raw bytes rather than a fixed
    schema. ``event_enable``/``event_silenced``/``event_state`` are
    homogeneous byte arrays without that dependency, so they use a greedy
    array schema instead.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.EVENT_LOG

    instance_name: CIPAttribute[bytes] = CIPAttribute(1)
    """STRINGI name of this event instance (attribute 1)."""

    state: CIPAttribute[int] = CIPAttribute(2, uint8)
    """0=Nonexistent, 1=Stopped, 2=Empty, 3=Available, 4=Full/Overwrite,
    5=Full/Halted (attribute 2)."""

    event_list_size: CIPAttribute[int] = CIPAttribute(3, uint32)
    """Number of elements in event_list/event_enable/event_silenced/event_state
    (attribute 3)."""

    event_list: CIPAttribute[bytes] = CIPAttribute(4)
    """All event identifiers monitored by this instance; format set by
    event_identifier_format (attribute 4)."""

    event_enable: CIPAttribute[Collection[int]] = CIPAttribute(5, uint8[...])
    """Per-event enable flags: 0 = disabled, 1 = enabled (default), one BOOL each (attribute 5)."""

    event_silenced: CIPAttribute[Collection[int]] = CIPAttribute(6, uint8[...])
    """Per-event silence flags: 0 = not silenced (default), 1 = silenced, one BOOL each (attribute 6)."""

    event_state: CIPAttribute[Collection[int]] = CIPAttribute(7, uint8[...])
    """Per-event state bit flags: bit0=enabled, bit1=active, bit2=acked,
    bit3=logged, bit4=silenced (attribute 7)."""

    logged_states_configuration: CIPAttribute[int] = CIPAttribute(8, uint8)
    """Bit flags selecting which event state transitions are logged, default
    0x01 (attribute 8, See Table 5-45.4)."""

    logged_data_configuration: CIPAttribute[int] = CIPAttribute(9, uint8)
    """Bit flags selecting what data is stored in the event log, default 0
    (attribute 9, See Table 5-45.5)."""

    log_full_action: CIPAttribute[int] = CIPAttribute(10, uint8)
    """0 = Halt (default), 1 = Scroll, action to take when the log is full (attribute 10)."""

    duplicate_event_action: CIPAttribute[int] = CIPAttribute(11, uint8)
    """0 = Ignore (default), 1 = Add, 2 = Overwrite, action to take on a duplicate event (attribute 11)."""

    event_data_log_maximum_size: CIPAttribute[int] = CIPAttribute(12, uint32)
    """Maximum number of allowable entries in the Event/Data Log (attribute
    12)."""

    event_data_log_size: CIPAttribute[int] = CIPAttribute(13, uint32)
    """Present number of entries in the Event/Data Log (attribute 13)."""

    event_data_log: CIPAttribute[bytes] = CIPAttribute(14)
    """List of all logged events (attribute 14)."""

    active_event_data_list_size: CIPAttribute[int] = CIPAttribute(15, uint32)
    """Number of entries in active_event_data_list (attribute 15)."""

    active_event_data_list: CIPAttribute[bytes] = CIPAttribute(16)
    """List of event identifiers presently active (attribute 16)."""

    logged_event_data_list_size: CIPAttribute[int] = CIPAttribute(17, uint32)
    """Number of entries in logged_event_data_list (attribute 17)."""

    logged_event_data_list: CIPAttribute[bytes] = CIPAttribute(18)
    """List of event identifiers currently logged (attribute 18)."""

    log_full: CIPAttribute[int] = CIPAttribute(19, uint8)
    """0 = log not full, 1 = event_data_log_size == event_data_log_maximum_size (attribute 19)."""

    log_contains_entries: CIPAttribute[int] = CIPAttribute(20, uint8)
    """0 = log empty, 1 = log contains entries (attribute 20)."""

    log_overrun: CIPAttribute[int] = CIPAttribute(21, uint8)
    """0 = no overrun, 1 = the log has overrun (attribute 21)."""

    sequential_event_data_access: CIPAttribute[bytes] = CIPAttribute(22)
    """Simple mechanism to sequentially access Event/Data Log entries
    (attribute 22, See §5-45.4.22)."""

    startup_behavior: CIPAttribute[int] = CIPAttribute(23, uint8)
    """0 = Auto Active (default), 1 = Start Required, behavior after power-up/reset (attribute 23)."""

    event_identifier_format: CIPAttribute[int] = CIPAttribute(24, uint8)
    """Format of the Event Identifier used in log entries, default 0 (attribute
    24)."""

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read an Event Log class attribute from instance 0 (See §5-45.2,
        Table 5-45.2)."""
        return self.get_attr(attribute, instance=0)

    def reset(self, reset_type: int = 0) -> bytes:
        """Invoke Reset, restoring this instance to its power-up (0) or out-of-
        box (1) state."""
        request_data = uint8.to_bytes(int(reset_type), order=LittleEndian)
        return self._expect_empty(self.message(CommonService.RESET, request_data))

    def start(self) -> bytes:
        """Invoke Start, transitioning this instance from Configuring to Active
        so logging can commence."""
        return self._expect_empty(self.message(CommonService.START))

    def stop(self) -> bytes:
        """Invoke Stop, transitioning this instance back to Configuring and
        clearing its event list/status."""
        return self._expect_empty(self.message(CommonService.STOP))
