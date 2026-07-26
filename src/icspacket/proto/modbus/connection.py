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
"""\
High-level Modbus TCP/UDP connection wrapper built on top of :mod:`pymodbus`.

.. versionadded:: 0.3.0
"""
from dataclasses import dataclass
from typing import Literal

from pymodbus.client import ModbusTcpClient, ModbusUdpClient
from pymodbus.client.base import ModbusBaseSyncClient
from pymodbus.constants import ExcCodes
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import ExceptionResponse, ModbusPDU
from typing_extensions import override

from icspacket.core.connection import (
    ConnectionError,
    ConnectionNotEstablished,
    connection,
)

__all__ = [
    "AddressRange",
    "ModbusProtocolError",
    "Modbus_Connection",
]

ModbusTransport = Literal["tcp", "udp"]
"""Supported Modbus transport protocols."""

ModbusTable = Literal["coils", "discrete", "holding", "input"]
"""Supported Modbus data tables."""

# Read method name and protocol-defined maximum item count (Modbus
# Application Protocol V1.1b3, sections 6.1-6.4) for each data table.
_TABLE_READERS: dict[ModbusTable, tuple[str, int]] = {
    "coils": ("read_coils", 2000),
    "discrete": ("read_discrete_inputs", 2000),
    "holding": ("read_holding_registers", 125),
    "input": ("read_input_registers", 125),
}


@dataclass(frozen=True)
class AddressRange:
    """
    A contiguous range of Modbus data addresses confirmed present on a
    device, as returned by :meth:`Modbus_Connection.scan_table`.

    :ivar start: Zero-based starting address of the range.
    :vartype start: int
    :ivar count: Number of consecutive addresses in the range.
    :vartype count: int
    """

    start: int
    count: int

    @property
    def end(self) -> int:
        """Address immediately following the last address in this range (exclusive)."""
        return self.start + self.count

    @override
    def __str__(self) -> str:
        if self.count == 1:
            return str(self.start)
        return f"{self.start}-{self.end - 1} ({self.count})"


class ModbusProtocolError(ConnectionError):
    """
    Raised when a Modbus request fails at the application/protocol level.

    This covers both explicit Modbus exception responses (e.g. illegal
    data address/value, slave device failure) and cases where no
    response was received at all.

    :ivar response: The raw response PDU that caused this error, if any.
    :vartype response: ModbusPDU | None
    """

    def __init__(self, *args: object, response: ModbusPDU | None = None) -> None:
        super().__init__(*args)
        self.response: ModbusPDU | None = response


class Modbus_Connection(connection):
    """
    Synchronous Modbus TCP/UDP connection built on :mod:`pymodbus`.

    This class provides a thin, icspacket-style wrapper around
    :class:`pymodbus.client.ModbusTcpClient` and
    :class:`pymodbus.client.ModbusUdpClient`, exposing the most common
    read/write services (coils, discrete inputs, holding/input
    registers).

    All application-level failures (Modbus exception responses, missing
    responses) are normalized into :class:`ModbusProtocolError`.

    Example:

    .. code-block:: python

        conn = Modbus_Connection(unit_id=1)
        conn.connect(("192.168.1.50", 502))
        values = conn.read_holding_registers(0, count=4)
        conn.write_register(0, 1234)
        conn.close()

        # Modbus/UDP
        udp_conn = Modbus_Connection(unit_id=1, transport="udp")
        udp_conn.connect(("192.168.1.50", 502))

    :param unit_id: Default Modbus unit/slave identifier used for requests
        that do not explicitly override it.
    :type unit_id: int
    :param timeout: Socket-level timeout (in seconds) for the underlying
        connection.
    :type timeout: float
    :param transport: Transport protocol to use, either ``"tcp"`` (default)
        or ``"udp"``.
    :type transport: ModbusTransport
    """

    def __init__(
        self,
        unit_id: int = 1,
        timeout: float = 10.0,
        transport: ModbusTransport = "tcp",
    ) -> None:
        super().__init__()
        if transport not in ("tcp", "udp"):
            raise ValueError(f"Unsupported Modbus transport: {transport!r}")

        self.unit_id: int = unit_id
        self.timeout: float = timeout
        self.transport: ModbusTransport = transport
        self._client: ModbusBaseSyncClient | None = None

    @property
    def client(self) -> ModbusBaseSyncClient:
        """The underlying pymodbus sync client instance (TCP or UDP)."""
        if self._client is None:
            raise ConnectionNotEstablished
        return self._client

    @override
    def connect(self, address: tuple[str, int]) -> None:
        """Connect to a Modbus TCP or UDP server.

        :param address: Target ``(host, port)`` tuple (default Modbus
            port is 502).
        :type address: tuple[str, int]
        :raises ConnectionError: If the connection cannot be established.
        """
        host, port = address
        client_cls = ModbusUdpClient if self.transport == "udp" else ModbusTcpClient
        client = client_cls(host, port=port, timeout=self.timeout)
        if not client.connect():
            raise ConnectionError(
                f"Failed to connect to Modbus server at {host}:{port} "
                + f"({self.transport.upper()})"
            )

        self._client = client
        self._connected: bool = True
        self._valid: bool = True


    @override
    def close(self) -> None:
        """Close the underlying Modbus TCP/UDP connection."""
        if self._client is not None:
            self._client.close()

        self._connected = False
        self._valid = False

    def _unit(self, unit_id: int | None) -> int:
        if unit_id is None:
            return self.unit_id
        return unit_id

    def _raise_on_error(self, response: ModbusPDU | None, operation: str) -> ModbusPDU:
        if response is None:
            raise ModbusProtocolError(f"No response received for {operation}")

        if isinstance(response, ExceptionResponse) or response.isError():
            raise ModbusProtocolError(
                f"{operation} failed with exception response: {response}",
                response=response,
            )
        return response

    def read_coils(
        self, address: int, count: int = 1, unit_id: int | None = None
    ) -> list[bool]:
        """Read one or more coils (``0x`` addresses, function code 1).

        :param address: Zero-based starting coil address.
        :type address: int
        :param count: Number of coils to read.
        :type count: int
        :param unit_id: Override the default unit/slave identifier.
        :type unit_id: int | None
        :returns: List of coil states.
        :rtype: list[bool]
        :raises ModbusProtocolError: On an exception response or no response.
        """
        self._assert_connected()
        response = self.client.read_coils(
            address,
            count=count,
            device_id=self._unit(unit_id),
        )
        result = self._raise_on_error(response, "read_coils")
        return list(result.bits[:count])

    def read_discrete_inputs(
        self, address: int, count: int = 1, unit_id: int | None = None
    ) -> list[bool]:
        """Read one or more discrete inputs (``1x`` addresses, function code 2)."""
        self._assert_connected()
        response = self.client.read_discrete_inputs(
            address,
            count=count,
            device_id=self._unit(unit_id),
        )
        result = self._raise_on_error(response, "read_discrete_inputs")
        return list(result.bits[:count])

    def read_holding_registers(
        self, address: int, count: int = 1, unit_id: int | None = None
    ) -> list[int]:
        """Read one or more holding registers (``4x`` addresses, function code 3)."""
        self._assert_connected()
        response = self.client.read_holding_registers(
            address,
            count=count,
            device_id=self._unit(unit_id),
        )
        result = self._raise_on_error(response, "read_holding_registers")
        return list(result.registers)

    def read_input_registers(
        self, address: int, count: int = 1, unit_id: int | None = None
    ) -> list[int]:
        """Read one or more input registers (``3x`` addresses, function code 4)."""
        self._assert_connected()
        response = self.client.read_input_registers(
            address,
            count=count,
            device_id=self._unit(unit_id),
        )
        result = self._raise_on_error(response, "read_input_registers")
        return list(result.registers)

    def write_coil(
        self, address: int, value: bool, unit_id: int | None = None
    ) -> None:
        """Write a single coil (function code 5)."""
        self._assert_connected()
        response = self.client.write_coil(
            address,
            value,
            device_id=self._unit(unit_id),
        )
        _ = self._raise_on_error(response, "write_coil")

    def write_coils(
        self, address: int, values: list[bool], unit_id: int | None = None
    ) -> None:
        """Write multiple coils (function code 15).

        .. note::
           A copy of ``values`` is passed to the underlying pymodbus
           client, since it pads the bit list in place to a full byte
           boundary as a side effect of encoding the request - without
           the copy, the caller's list would be silently mutated.
        """
        self._assert_connected()
        response = self.client.write_coils(
            address,
            list(values),
            device_id=self._unit(unit_id),
        )
        _ = self._raise_on_error(response, "write_coils")

    def write_register(
        self, address: int, value: int, unit_id: int | None = None
    ) -> None:
        """Write a single holding register (function code 6)."""
        self._assert_connected()
        response = self.client.write_register(
            address,
            value,
            device_id=self._unit(unit_id),
        )
        _ = self._raise_on_error(response, "write_register")

    def write_registers(
        self, address: int, values: list[int], unit_id: int | None = None
    ) -> None:
        """Write multiple holding registers (function code 16)."""
        self._assert_connected()
        response = self.client.write_registers(
            address,
            values,
            device_id=self._unit(unit_id),
        )
        _ = self._raise_on_error(response, "write_registers")

    def read_device_information(
        self, unit_id: int | None = None
    ) -> dict[int, bytes]:
        """Read basic device identification objects (function code 43/14).

        :returns: Mapping of object id to raw identification value
            (e.g. vendor name, product code, revision).
        :rtype: dict[int, bytes]
        """
        self._assert_connected()
        response = self.client.read_device_information(
            device_id=self._unit(unit_id)
        )
        result = self._raise_on_error(response, "read_device_information")
        return dict(getattr(result, "information", {}))

    def get_unit_ids(self, start: int = 1, end: int = 248) -> list[int]:
        """Discover which unit/slave identifiers respond on this connection.

        Modbus has no service to enumerate connected slaves, so this
        probes every candidate id in ``[start, end)`` with a minimal
        ``read_coils(0, count=1)`` request. *Any* well-formed Modbus reply
        including exception responses such as illegal data address or
        slave device failure is treated as evidence that a device with
        that unit id is present and answering, since it means the request
        was received and processed. Only a timeout (no reply at all) is
        treated as absence.

        :param start: First unit id to probe, inclusive.
        :type start: int
        :param end: Last unit id to probe, exclusive. Defaults to ``248``
            (one past the highest valid Modbus unit id, 247).
        :type end: int
        :returns: Sorted list of responsive unit ids.
        :rtype: list[int]
        :raises ValueError: If ``start``/``end`` are out of bounds.
        """
        if not 0 <= start < end <= 248:
            raise ValueError("start/end must satisfy 0 <= start < end <= 248")

        self._assert_connected()
        responsive: list[int] = []
        for candidate in range(start, end):
            try:
                _ = self.read_coils(0, count=1, unit_id=candidate)
            except ModbusProtocolError:
                # A (possibly negative) reply still proves something is
                # alive and speaking Modbus on this unit id.
                responsive.append(candidate)
            except ModbusIOException:
                continue  # no reply within the timeout - nothing there
            else:
                responsive.append(candidate)
        return responsive

    def get_table(
        self,
        table: ModbusTable,
        start: int = 0,
        end: int = 0x10000,
        unit_id: int | None = None,
        block_size: int | None = None,
    ) -> list[AddressRange]:
        """Discover which addresses of a data table are implemented.

        .. warning::
           Because exact discovery requires probing until every boundary
           is resolved, the number of requests is bounded by ``end -
           start`` in the worst case (e.g. a table that is entirely
           absent across the whole scanned range). Keep the scanned range
           modest (the default ``end`` is deliberately *not* the full
           address space) unless you are prepared for a slow, thorough
           scan.

        Example:

        .. code-block:: python

            conn = Modbus_Connection(unit_id=1)
            conn.connect(("192.168.1.50", 502))
            for r in conn.scan_table("holding", end=1000):
                print(f"holding registers: {r}")

        :param table: Table to scan: ``"coils"``, ``"discrete"``,
            ``"holding"`` or ``"input"``.
        :type table: ModbusTable
        :param start: Zero-based starting address, inclusive.
        :type start: int
        :param end: Ending address, exclusive. Defaults to ``0x10000``
            (the full 16-bit Modbus address space) - narrow this for a
            faster scan.
        :type end: int
        :param unit_id: Override the default unit/slave identifier.
        :type unit_id: int | None
        :param block_size: Maximum number of addresses to probe per
            request. Defaults to (and is capped at) the table's protocol
            maximum; lower it if the target rejects maximum-size requests
            even within its valid range.
        :type block_size: int | None
        :returns: Coalesced list of address ranges that responded
            successfully, in ascending order.
        :rtype: list[AddressRange]
        :raises ValueError: If ``table`` is unknown, the address bounds
            are invalid, or ``block_size`` is less than 1.
        :raises ModbusProtocolError: If a probe fails for a reason other
            than an illegal-address exception (e.g. a device failure
            response), since that does not indicate an absent address.
        """
        if table not in _TABLE_READERS:
            raise ValueError(
                f"Unknown Modbus table {table!r}, expected one of "
                + f"{sorted(_TABLE_READERS)}"
            )
        if not 0 <= start < end <= 0x10000:
            raise ValueError("start/end must satisfy 0 <= start < end <= 65536")

        method_name, max_count = _TABLE_READERS[table]
        chunk = max_count if not block_size else min(block_size, max_count)
        if chunk < 1:
            raise ValueError("block_size must be >= 1")

        self._assert_connected()
        read = getattr(self, method_name)
        ranges: list[AddressRange] = []

        def _record(address: int, count: int) -> None:
            if ranges and ranges[-1].end == address:
                ranges[-1] = AddressRange(ranges[-1].start, ranges[-1].count + count)
            else:
                ranges.append(AddressRange(address, count))

        def _probe(address: int, count: int) -> None:
            # A span wider than one request can cover must be split
            # before it can be tested at all - this is "free" (no
            # request issued) and keeps large fully-valid spans cheap
            # (one request per `chunk`-sized piece, no bisection).
            if count > chunk:
                half = count // 2
                _probe(address, half)
                _probe(address + half, count - half)
                return

            try:
                read(address, count=count, unit_id=unit_id)
            except ModbusProtocolError as e:
                code = getattr(e.response, "exception_code", None)
                if code != ExcCodes.ILLEGAL_ADDRESS:
                    raise
                if count > 1:
                    # Ambiguous: could be a boundary inside this chunk or
                    # entirely absent - bisect to resolve exactly.
                    half = count // 2
                    _probe(address, half)
                    _probe(address + half, count - half)
                # count == 1: confirmed absent, nothing to record.
            else:
                _record(address, count)

        _probe(start, end - start)
        return ranges
