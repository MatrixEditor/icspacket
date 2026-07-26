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
High-level BACnet/IP connection wrapper built on top of :mod:`bacpypes3`.
"""

import asyncio
import concurrent.futures
import logging
import queue
import threading
from collections.abc import Coroutine, Sequence
from dataclasses import dataclass
from typing import Any

from bacpypes3.apdu import ErrorRejectAbortNack
from bacpypes3.app import Application
from bacpypes3.argparse import SimpleArgumentParser
from bacpypes3.comm import ApplicationServiceElement, bind
from bacpypes3.constructeddata import AnyAtomic
from bacpypes3.ipv4.bvll import (
    LPDU,
    ReadBroadcastDistributionTable,
    ReadBroadcastDistributionTableAck,
    ReadForeignDeviceTable,
    ReadForeignDeviceTableAck,
)
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import ObjectIdentifier, PropertyIdentifier
from typing_extensions import Self, override

from icspacket.core.connection import (
    ConnectionError,
    ConnectionNotEstablished,
    ConnectionStateError,
    connection,
)

logger = logging.getLogger(__name__)

__all__ = [
    "BACnetObject",
    "BACnetProtocolError",
    "BACnet_Connection",
    "BACnet_Subscription",
    "DiscoveredDevice",
    "DiscoveredObject",
]


class BACnetProtocolError(ConnectionError):
    """
    Raised when a BACnet service request fails at the application level.
    """


def _unwrap_value(value: Any) -> Any:
    """Unwrap a raw :class:`~bacpypes3.constructeddata.AnyAtomic` reading
    into its underlying Python value, passing any other value through
    unchanged."""
    if isinstance(value, AnyAtomic):
        return value.get_value()
    return value


@dataclass(frozen=True)
class DiscoveredDevice:
    """
    A device discovered via :meth:`BACnet_Connection.who_is`.

    :ivar device_identifier: The device's object identifier, e.g.
        ``("device", 1234)``.
    :vartype device_identifier: ObjectIdentifier
    :ivar address: The network address the I-Am response was received from.
    :vartype address: Address
    :ivar max_apdu_length_accepted: Maximum APDU length the device accepts.
    :vartype max_apdu_length_accepted: int | None
    :ivar segmentation_supported: The device's segmentation capability
        (e.g. ``"noSegmentation"``, ``"segmentedBoth"``).
    :vartype segmentation_supported: str | None
    :ivar vendor_id: The device's BACnet vendor identifier.
    :vartype vendor_id: int | None
    """

    device_identifier: ObjectIdentifier
    address: Address
    max_apdu_length_accepted: int | None = None
    segmentation_supported: str | None = None
    vendor_id: int | None = None

    @override
    def __str__(self) -> str:
        return f"{self.device_identifier} @ {self.address}"


@dataclass(frozen=True)
class DiscoveredObject:
    """
    An object discovered via :meth:`BACnet_Connection.who_has`.

    :ivar device_identifier: Object identifier of the device that holds
        the object.
    :vartype device_identifier: ObjectIdentifier
    :ivar object_identifier: The matched object's identifier.
    :vartype object_identifier: ObjectIdentifier
    :ivar object_name: The matched object's name, if reported.
    :vartype object_name: str | None
    """

    device_identifier: ObjectIdentifier
    object_identifier: ObjectIdentifier
    object_name: str | None = None

    @override
    def __str__(self) -> str:
        label = f" ({self.object_name})" if self.object_name else ""
        return f"{self.object_identifier}{label} on {self.device_identifier}"


@dataclass
class BACnetObject:
    """
    An object discovered while scanning a device's ``object-list``
    property, as returned by :meth:`BACnet_Connection.scan_objects`.

    :ivar object_identifier: The object's identifier.
    :vartype object_identifier: ObjectIdentifier
    :ivar object_name: The object's ``object-name`` property, if it could
        be read.
    :vartype object_name: str | None
    :ivar present_value: The object's ``present-value`` property, only
        populated when requested via ``values=True``.
    :vartype present_value: Any
    """

    object_identifier: ObjectIdentifier
    object_name: str | None = None
    present_value: Any = None

    @override
    def __str__(self) -> str:
        text = str(self.object_identifier)
        if self.object_name:
            text += f" ({self.object_name})"
        if self.present_value is not None:
            text += f" = {self.present_value!r}"
        return text


class _BVLLServiceElement(ApplicationServiceElement):
    """
    Private Application Service Element bound directly to the BVLL
    (BACnet Virtual Link Layer) service access point of the local
    network adapter.

    Reading a *remote* BBMD's Broadcast Distribution Table (BDT) or
    Foreign Device Table (FDT) has no high-level helper on
    :class:`~bacpypes3.app.Application` - it requires sending raw
    ``ReadBroadcastDistributionTable``/``ReadForeignDeviceTable`` LPDUs
    below the NPDU/APDU layer and matching the corresponding Ack LPDUs as
    they arrive, exactly as shown in BACpypes3's own
    ``samples/read-bbmd.py``.
    """

    def __init__(self) -> None:
        super().__init__()
        self._bdt_future: asyncio.Future[Any] | None = None
        self._fdt_future: asyncio.Future[Any] | None = None

    @override
    async def confirmation(self, pdu: LPDU) -> None:
        if isinstance(pdu, ReadBroadcastDistributionTableAck):
            if self._bdt_future is not None and not self._bdt_future.done():
                self._bdt_future.set_result(pdu.bvlciBDT)
            self._bdt_future = None
        elif isinstance(pdu, ReadForeignDeviceTableAck):
            if self._fdt_future is not None and not self._fdt_future.done():
                self._fdt_future.set_result(pdu.bvlciFDT)
            self._fdt_future = None

    def read_broadcast_distribution_table(
        self, address: Address
    ) -> asyncio.Future[Any]:
        self._bdt_future = asyncio.get_event_loop().create_future()
        asyncio.ensure_future(
            self.request(ReadBroadcastDistributionTable(destination=address))
        )
        return self._bdt_future

    def read_foreign_device_table(self, address: Address) -> asyncio.Future[Any]:
        self._fdt_future = asyncio.get_event_loop().create_future()
        asyncio.ensure_future(self.request(ReadForeignDeviceTable(destination=address)))
        return self._fdt_future


class BACnet_Connection(connection):
    """
    Synchronous BACnet/IP client connection built on :mod:`bacpypes3`.

    Unlike Modbus/OPC-UA, BACnet has no single remote "server" to connect
    to: a BACnet/IP client first binds its *own* local device/endpoint
    (with its own device object instance, name and vendor id), then
    addresses individual peers explicitly on every subsequent call
    (:meth:`read_property`, :meth:`who_is`, ...) via unicast or broadcast.
    :meth:`connect` therefore binds the *local* endpoint rather than a
    remote target.

    Example:

    .. code-block:: python

        conn = BACnet_Connection(instance=1001, name="icspacket-client")
        conn.connect("192.168.1.50/24")
        for device in conn.who_is():
            print(device)
        value = conn.read_property("192.168.1.60", "analog-input,1", "present-value")
        conn.close()

    :param name: Local device object name.
    :type name: str
    :param instance: Local device object instance number (device
        identifier). Must be unique on the BACnet network.
    :type instance: int
    :param network: Local BACnet network number, or ``0`` if unknown/not
        applicable.
    :type network: int
    :param vendor_identifier: BACnet vendor identifier to advertise for
        the local device.
    :type vendor_identifier: int
    :param foreign_bbmd: Address of a remote BBMD to register with as a
        foreign device, or ``None`` to disable foreign device
        registration. Mutually exclusive with ``bbmd_bdt``.
    :type foreign_bbmd: str | None
    :param foreign_ttl: Foreign device registration time-to-live in
        seconds, used only when ``foreign_bbmd`` is set.
    :type foreign_ttl: int
    :param bbmd_bdt: Broadcast Distribution Table entries to configure if
        this local device should itself act as a BBMD. Mutually exclusive
        with ``foreign_bbmd``.
    :type bbmd_bdt: Sequence[str] | None
    :param timeout: Default timeout in seconds applied to BACnet service
        calls that do not explicitly override it.
    :type timeout: float
    """

    def __init__(
        self,
        name: str = "icspacket",
        instance: int = 999,
        network: int = 0,
        vendor_identifier: int = 999,
        foreign_bbmd: str | None = None,
        foreign_ttl: int = 30,
        bbmd_bdt: Sequence[str] | None = None,
        timeout: float = 4.0,
    ) -> None:
        super().__init__()
        self.name: str = name
        self.instance: int = instance
        self.network: int = network
        self.vendor_identifier: int = vendor_identifier
        self.foreign_bbmd: str | None = foreign_bbmd
        self.foreign_ttl: int = foreign_ttl
        self.bbmd_bdt: list[str] | None = list(bbmd_bdt) if bbmd_bdt else None
        self.timeout: float = timeout

        self._app: Application | None = None
        self._bvll_ase: _BVLLServiceElement | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    @property
    def app(self) -> Application:
        """The underlying :class:`~bacpypes3.app.Application` instance."""
        if self._app is None:
            raise ConnectionNotEstablished
        return self._app

    def _build_argv(self, address: str | None) -> list[str]:
        argv = [
            "--name",
            self.name,
            "--instance",
            str(self.instance),
            "--vendoridentifier",
            str(self.vendor_identifier),
        ]
        if address:
            argv += ["--address", address]
        if self.network:
            argv += ["--network", str(self.network)]
        if self.foreign_bbmd:
            argv += ["--foreign", self.foreign_bbmd, "--ttl", str(self.foreign_ttl)]
        if self.bbmd_bdt:
            argv += ["--bbmd", *self.bbmd_bdt]
        return argv

    @staticmethod
    def _thread_main(
        ready: threading.Event, box: dict[str, Any], argv: list[str]
    ) -> None:
        """Entry point for the background event-loop thread: builds the
        BACnet application stack, then services it until ``close()``
        schedules a loop stop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def build() -> tuple[Application, _BVLLServiceElement]:
            args = SimpleArgumentParser().parse_args(argv)
            app = Application.from_args(args)
            # Application.from_args() schedules UDP transport creation as
            # background tasks rather than awaiting them; without this,
            # a request issued immediately after connect() returns can
            # race ahead of the socket actually being bound.
            await asyncio.sleep(0.2)

            bvll_ase = _BVLLServiceElement()
            sap = app.nsap.local_adapter.clientPeer
            bind(bvll_ase, sap)
            return app, bvll_ase

        try:
            app, bvll_ase = loop.run_until_complete(build())
        except BaseException as e:  # noqa: BLE001 - report any startup failure
            box["error"] = e
            ready.set()
            loop.close()
            return

        box["loop"] = loop
        box["app"] = app
        box["bvll_ase"] = bvll_ase
        ready.set()
        try:
            loop.run_forever()
        finally:
            loop.close()

    @override
    def connect(self, address: str | None = None) -> None:
        """
        Bind the local BACnet/IP endpoint and build the underlying
        BACnet application stack.

        :param address: Local network address to bind to, in
            ``host[/prefixlen]`` form (e.g. ``"192.168.1.50/24"``), or
            ``None`` to bind using BACpypes3's default address
            resolution (all interfaces / a foreign-device placeholder
            address when ``foreign_bbmd`` is set).
        :type address: str | None
        :raises ConnectionStateError: If this connection is already
            established.
        :raises ConnectionError: If building the local device/network
            stack fails (e.g. the UDP port is already in use, or the
            foreign device/BBMD configuration is invalid).
        """
        if self._loop is not None:
            raise ConnectionStateError("BACnet connection is already established")

        argv = self._build_argv(address)
        ready = threading.Event()
        box: dict[str, Any] = {}
        thread = threading.Thread(
            target=self._thread_main,
            args=(ready, box, argv),
            name="bacnet-connection",
            daemon=True,
        )
        thread.start()

        if not ready.wait(timeout=self.timeout + 5.0):
            raise ConnectionError("Timed out starting BACnet application stack")

        if "error" in box:
            thread.join(timeout=2.0)
            raise ConnectionError(
                f"Failed to build BACnet application stack: {box['error']}"
            ) from box["error"]

        self._thread = thread
        self._loop = box["loop"]
        self._app = box["app"]
        self._bvll_ase = box["bvll_ase"]
        self._connected: bool = True
        self._valid: bool = True

    @override
    def close(self) -> None:
        """
        Close the local BACnet device/network stack and stop the
        background event loop thread.

        Idempotent: calling this more than once, or before a connection
        was ever established, is a no-op.
        """
        if self._loop is None:
            return

        loop, self._loop = self._loop, None
        app, self._app = self._app, None
        self._bvll_ase = None
        thread, self._thread = self._thread, None
        self._connected = False
        self._valid = False

        if app is not None:

            async def _do_close() -> None:
                app.close()

            future = asyncio.run_coroutine_threadsafe(_do_close(), loop)
            try:
                future.result(timeout=5.0)
            except Exception:
                logger.debug(
                    "Cleanup during BACnet application close() raised", exc_info=True
                )
                future.cancel()

        # stop the loop and wait for the background thread to exit so it
        # doesn't leak/keep the process alive, mirroring the discipline
        # already applied to asyncua's background ThreadLoop in
        # OPCUA_Connection.close()/discover_endpoints().
        loop.call_soon_threadsafe(loop.stop)
        if thread is not None:
            thread.join(timeout=5.0)

    def _run_coro(
        self, coro: Coroutine[Any, Any, Any], *, timeout: float | None = None
    ) -> Any:
        """Schedule ``coro`` onto the background event loop and block for
        its result, translating BACnet/asyncio failures into
        :class:`BACnetProtocolError`."""
        self._assert_connected()
        assert self._loop is not None
        eff_timeout = timeout if timeout is not None else self.timeout

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=eff_timeout)
        except ErrorRejectAbortNack as e:
            raise BACnetProtocolError(f"BACnet request rejected: {e}") from e
        except (TimeoutError, concurrent.futures.TimeoutError) as e:
            future.cancel()
            raise BACnetProtocolError(
                f"BACnet request timed out after {eff_timeout}s"
            ) from e
        except Exception as e:  # noqa: BLE001 - normalize any bacpypes3 failure
            raise BACnetProtocolError(f"BACnet request failed: {e}") from e

    def who_is(
        self,
        low_limit: int | None = None,
        high_limit: int | None = None,
        address: str | Address | None = None,
        *,
        timeout: float | None = None,
    ) -> list[DiscoveredDevice]:
        """Discover devices on the network via a Who-Is/I-Am exchange.

        :param low_limit: Lower bound of the device instance range to
            query, or ``None`` for no lower bound. Must be given together
            with ``high_limit``.
        :type low_limit: int | None
        :param high_limit: Upper bound of the device instance range to
            query, or ``None`` for no upper bound.
        :type high_limit: int | None
        :param address: Address to direct the Who-Is to, or ``None`` to
            broadcast on the local network.
        :type address: str | Address | None
        :param timeout: How long to wait for I-Am responses, in seconds.
        :type timeout: float | None
        :returns: Devices that responded, in the order received.
        :rtype: list[DiscoveredDevice]
        :raises BACnetProtocolError: If the request itself fails (a lack
            of any responses is not an error - it yields an empty list).
        """
        self._assert_connected()
        target = Address(address) if isinstance(address, str) else address
        eff_timeout = timeout if timeout is not None else self.timeout

        async def _do() -> list[Any]:
            return await self.app.who_is(
                low_limit, high_limit, target, timeout=eff_timeout
            )

        i_ams = self._run_coro(_do(), timeout=eff_timeout + 2.0)
        return [
            DiscoveredDevice(
                device_identifier=i_am.iAmDeviceIdentifier,
                address=i_am.pduSource,
                max_apdu_length_accepted=i_am.maxAPDULengthAccepted,
                segmentation_supported=str(i_am.segmentationSupported),
                vendor_id=i_am.vendorID,
            )
            for i_am in i_ams
        ]

    def who_has(
        self,
        low_limit: int | None = None,
        high_limit: int | None = None,
        object_identifier: str | ObjectIdentifier | None = None,
        object_name: str | None = None,
        address: str | Address | None = None,
        *,
        timeout: float | None = None,
    ) -> list[DiscoveredObject]:
        """Discover which device(s) hold a given object via a
        Who-Has/I-Have exchange.

        Exactly one of ``object_identifier`` or ``object_name`` must be
        given, matching the underlying BACnet service definition.

        :param low_limit: Lower bound of the device instance range to
            query, or ``None`` for no lower bound.
        :type low_limit: int | None
        :param high_limit: Upper bound of the device instance range to
            query, or ``None`` for no upper bound.
        :type high_limit: int | None
        :param object_identifier: Object identifier to search for.
        :type object_identifier: str | ObjectIdentifier | None
        :param object_name: Object name to search for.
        :type object_name: str | None
        :param address: Address to direct the Who-Has to, or ``None`` to
            broadcast on the local network.
        :type address: str | Address | None
        :param timeout: How long to wait for I-Have responses, in
            seconds.
        :type timeout: float | None
        :returns: Devices/objects that matched, in the order received.
        :rtype: list[DiscoveredObject]
        :raises BACnetProtocolError: If the request itself fails.
        """
        self._assert_connected()
        target = Address(address) if isinstance(address, str) else address
        eff_timeout = timeout if timeout is not None else self.timeout

        async def _do() -> list[Any]:
            return await self.app.who_has(
                low_limit,
                high_limit,
                object_identifier,
                object_name,
                target,
                timeout=eff_timeout,
            )

        i_haves = self._run_coro(_do(), timeout=eff_timeout + 2.0)
        return [
            DiscoveredObject(
                device_identifier=i_have.deviceIdentifier,
                object_identifier=i_have.objectIdentifier,
                object_name=(
                    str(i_have.objectName) if i_have.objectName is not None else None
                ),
            )
            for i_have in i_haves
        ]

    def read_property(
        self,
        device_address: str | Address,
        object_identifier: str | ObjectIdentifier,
        property_identifier: str | PropertyIdentifier,
        array_index: int | None = None,
        *,
        timeout: float | None = None,
    ) -> Any:
        """Read a single property from an object on a remote device.

        :param device_address: Target device's network address.
        :type device_address: str | Address
        :param object_identifier: Target object, e.g. ``"analog-input,1"``.
        :type object_identifier: str | ObjectIdentifier
        :param property_identifier: Property to read, e.g.
            ``"present-value"``.
        :type property_identifier: str | PropertyIdentifier
        :param array_index: Optional array index, for array-valued
            properties.
        :type array_index: int | None
        :param timeout: Timeout in seconds for this call.
        :type timeout: float | None
        :returns: The decoded property value.
        :rtype: Any
        :raises BACnetProtocolError: If the read fails or times out.
        """
        self._assert_connected()

        async def _do() -> Any:
            return await self.app.read_property(
                device_address, object_identifier, property_identifier, array_index
            )

        return _unwrap_value(self._run_coro(_do(), timeout=timeout))

    def write_property(
        self,
        device_address: str | Address,
        object_identifier: str | ObjectIdentifier,
        property_identifier: str | PropertyIdentifier,
        value: Any,
        array_index: int | None = None,
        priority: int | None = None,
        *,
        timeout: float | None = None,
    ) -> None:
        """Write a single property on an object on a remote device.

        :param device_address: Target device's network address.
        :type device_address: str | Address
        :param object_identifier: Target object, e.g. ``"analog-value,1"``.
        :type object_identifier: str | ObjectIdentifier
        :param property_identifier: Property to write, e.g.
            ``"present-value"``.
        :type property_identifier: str | PropertyIdentifier
        :param value: New value. Plain Python/string values are cast to
            the property's declared datatype by :mod:`bacpypes3`; pass
            ``"null"``/``Null()`` to relinquish a commandable priority.
        :type value: Any
        :param array_index: Optional array index, for array-valued
            properties.
        :type array_index: int | None
        :param priority: Optional commandable priority (1-16).
        :type priority: int | None
        :param timeout: Timeout in seconds for this call.
        :type timeout: float | None
        :raises BACnetProtocolError: If the write fails or times out.
        """
        self._assert_connected()

        async def _do() -> Any:
            return await self.app.write_property(
                device_address,
                object_identifier,
                property_identifier,
                value,
                array_index,
                priority,
            )

        self._run_coro(_do(), timeout=timeout)

    def read_property_multiple(
        self,
        device_address: str | Address,
        parameter_list: Sequence[
            tuple[str | ObjectIdentifier, Sequence[str | PropertyIdentifier]]
        ],
        *,
        timeout: float | None = None,
    ) -> list[tuple[ObjectIdentifier, PropertyIdentifier, int | None, Any]]:
        """Read multiple properties (possibly across multiple objects) in
        a single ReadPropertyMultiple request.

        :param device_address: Target device's network address.
        :type device_address: str | Address
        :param parameter_list: A sequence of
            ``(object_identifier, [property_identifier, ...])`` pairs. Note
            that :mod:`bacpypes3` itself expects these flattened into an
            alternating ``[object_identifier, [property_identifier, ...],
            object_identifier, [...], ...]`` list (see
            :meth:`bacpypes3.app.Application.read_property_multiple`); this
            method performs that flattening so callers can use the more
            structured pair form.
        :type parameter_list: Sequence[tuple[str | ObjectIdentifier, Sequence[str | PropertyIdentifier]]]
        :param timeout: Timeout in seconds for this call.
        :type timeout: float | None
        :returns: One ``(object_identifier, property_identifier,
            array_index, value)`` tuple per requested property, in
            request order.
        :rtype: list[tuple[ObjectIdentifier, PropertyIdentifier, int | None, Any]]
        :raises BACnetProtocolError: If the request fails or times out.
        """
        self._assert_connected()
        flat_parameter_list: list[Any] = []
        for object_identifier, property_reference_list in parameter_list:
            flat_parameter_list.append(object_identifier)
            flat_parameter_list.append(list(property_reference_list))

        async def _do() -> Any:
            return await self.app.read_property_multiple(
                device_address, flat_parameter_list
            )

        result = self._run_coro(_do(), timeout=timeout)
        if isinstance(result, ErrorRejectAbortNack):
            raise BACnetProtocolError(f"ReadPropertyMultiple rejected: {result}")
        if result is None:
            raise BACnetProtocolError("ReadPropertyMultiple received no valid response")
        return [
            (obj_id, prop_id, arr_idx, _unwrap_value(value))
            for obj_id, prop_id, arr_idx, value in result
        ]

    def write_property_multiple(
        self,
        device_address: str | Address,
        values: Sequence[
            tuple[str | ObjectIdentifier, str | PropertyIdentifier, Any]
            | tuple[str | ObjectIdentifier, str | PropertyIdentifier, Any, int | None]
            | tuple[
                str | ObjectIdentifier,
                str | PropertyIdentifier,
                Any,
                int | None,
                int | None,
            ]
        ],
        *,
        timeout: float | None = None,
    ) -> list[BACnetProtocolError | None]:
        """Write multiple properties in a single call.

        .. note::
           Unlike :meth:`read_property_multiple`, the installed
           :mod:`bacpypes3` version does not expose a client-side helper
           for the WritePropertyMultiple *service* (only the server-side
           ``do_WritePropertyMultipleRequest`` handler exists, used when
           icspacket itself is on the receiving end). This method issues
           one WriteProperty request per item (via :meth:`write_property`)
           and aggregates the per-item results, rather than sending a
           single atomic WritePropertyMultiple APDU - all-or-nothing
           semantics across items are therefore **not** guaranteed.

        :param device_address: Target device's network address.
        :type device_address: str | Address
        :param values: A sequence of
            ``(object_identifier, property_identifier, value[,
            array_index[, priority]])`` tuples.
        :param timeout: Timeout in seconds applied to each individual
            write.
        :type timeout: float | None
        :returns: One entry per input item, in order: ``None`` on
            success, or the :class:`BACnetProtocolError` raised for that
            item.
        :rtype: list[BACnetProtocolError | None]
        """
        self._assert_connected()
        results: list[BACnetProtocolError | None] = []
        for item in values:
            object_identifier, property_identifier, value, *rest = item
            array_index = rest[0] if len(rest) > 0 else None
            priority = rest[1] if len(rest) > 1 else None
            try:
                self.write_property(
                    device_address,
                    object_identifier,
                    property_identifier,
                    value,
                    array_index=array_index,
                    priority=priority,
                    timeout=timeout,
                )
                results.append(None)
            except BACnetProtocolError as e:
                results.append(e)
        return results

    def scan_objects(
        self,
        device_address: str | Address,
        *,
        device_identifier: str | ObjectIdentifier | None = None,
        values: bool = False,
        timeout: float | None = None,
    ) -> list[BACnetObject]:
        """Enumerate the objects exposed by a remote device.

        When ``device_identifier`` is not supplied, it is resolved by sending
        a unicast :meth:`who_is` to ``device_address`` first.

        :param device_address: Target device's network address.
        :type device_address: str | Address
        :param device_identifier: The target device's object identifier
            (e.g. ``"device,1234"``), if already known. When omitted, it
            is resolved automatically via :meth:`who_is`.
        :type device_identifier: str | ObjectIdentifier | None
        :param values: Also read each object's ``present-value``
            property (best-effort: failures for individual objects, e.g.
            objects with no ``present-value``, are ignored).
        :type values: bool
        :param timeout: Timeout in seconds applied to each individual
            property read (and to the ``who_is`` resolution step, if
            needed).
        :type timeout: float | None
        :returns: One entry per object in the device's object list.
        :rtype: list[BACnetObject]
        :raises BACnetProtocolError: If the device identifier cannot be
            resolved, or the object list itself cannot be read.
        """
        self._assert_connected()
        if device_identifier is None:
            devices = self.who_is(address=device_address, timeout=timeout)
            if not devices:
                raise BACnetProtocolError(
                    f"Could not resolve device identifier for {device_address}: "
                    + "no I-Am response received"
                )
            device_identifier = devices[0].device_identifier

        object_list = self.read_property(
            device_address, device_identifier, "object-list", timeout=timeout
        )

        results: list[BACnetObject] = []
        for object_identifier in object_list:
            entry = BACnetObject(object_identifier=object_identifier)
            try:
                name = self.read_property(
                    device_address, object_identifier, "object-name", timeout=timeout
                )
                entry.object_name = str(name)
            except BACnetProtocolError:
                logger.debug(
                    "Failed to read object-name of %s", object_identifier, exc_info=True
                )

            if values:
                try:
                    entry.present_value = self.read_property(
                        device_address,
                        object_identifier,
                        "present-value",
                        timeout=timeout,
                    )
                except BACnetProtocolError:
                    logger.debug(
                        "Failed to read present-value of %s",
                        object_identifier,
                        exc_info=True,
                    )
            results.append(entry)
        return results

    def subscribe_cov(
        self,
        device_address: str | Address,
        object_identifier: str | ObjectIdentifier,
        *,
        confirmed: bool = False,
        lifetime: int | None = None,
        process_identifier: int | None = None,
        timeout: float | None = None,
    ) -> BACnet_Subscription:
        """Subscribe to Change-of-Value (COV) notifications for an object.

        :param device_address: Target device's network address.
        :type device_address: str | Address
        :param object_identifier: Object to monitor.
        :type object_identifier: str | ObjectIdentifier
        :param confirmed: Request confirmed (vs. unconfirmed)
            notifications.
        :type confirmed: bool
        :param lifetime: Subscription lifetime in seconds, or ``None``
            for BACpypes3's default (or an indefinite/self-refreshing
            subscription, per its own subscription refresh logic).
        :type lifetime: int | None
        :param process_identifier: Subscriber process identifier, or
            ``None`` to let BACpypes3 allocate one automatically.
        :type process_identifier: int | None
        :param timeout: Timeout in seconds for the initial subscription
            request.
        :type timeout: float | None
        :returns: A handle yielding COV notifications as they arrive.
        :rtype: BACnet_Subscription
        :raises BACnetProtocolError: If the subscription request fails.
        """
        self._assert_connected()
        target = (
            Address(device_address)
            if isinstance(device_address, str)
            else device_address
        )
        monitored = (
            ObjectIdentifier(object_identifier)
            if isinstance(object_identifier, str)
            else object_identifier
        )

        async def _do() -> tuple[Any, asyncio.Task, queue.Queue]:
            scm = self.app.change_of_value(
                target, monitored, process_identifier, confirmed, lifetime
            )
            await scm.__aenter__()

            notifications: queue.Queue[
                tuple[PropertyIdentifier, Any] | BaseException
            ] = queue.Queue()

            async def _pump() -> None:
                try:
                    while True:
                        item = await scm.get_value()
                        notifications.put(item)
                except asyncio.CancelledError:
                    raise
                except BaseException as e:  # noqa: BLE001 - forward to consumer
                    notifications.put(e)

            pump_task = asyncio.get_event_loop().create_task(_pump())
            return scm, pump_task, notifications

        scm, pump_task, notifications = self._run_coro(_do(), timeout=timeout)
        assert self._loop is not None
        return BACnet_Subscription(self._loop, scm, pump_task, notifications)

    def read_broadcast_distribution_table(
        self, bbmd_address: str | Address, *, timeout: float | None = None
    ) -> list[Any]:
        """Read a remote BBMD's Broadcast Distribution Table (BDT).

        This is the lowest-level, most bespoke operation exposed by this
        connection: it sends a raw BVLL ``Read-Broadcast-Distribution-
        Table`` message (below the NPDU/APDU layer BACpypes3's
        higher-level services operate at) via a dedicated Application
        Service Element bound at :meth:`connect` time, mirroring
        BACpypes3's own ``samples/read-bbmd.py``.

        :param bbmd_address: The BBMD's network address.
        :type bbmd_address: str | Address
        :param timeout: Timeout in seconds for this call.
        :type timeout: float | None
        :returns: The BDT entries reported by the BBMD.
        :rtype: list[Any]
        :raises BACnetProtocolError: If no response is received in time.
        """
        self._assert_connected()
        target = (
            Address(bbmd_address) if isinstance(bbmd_address, str) else bbmd_address
        )

        async def _do() -> Any:
            assert self._bvll_ase is not None
            future = self._bvll_ase.read_broadcast_distribution_table(target)
            return await future

        return list(self._run_coro(_do(), timeout=timeout))

    def read_foreign_device_table(
        self, bbmd_address: str | Address, *, timeout: float | None = None
    ) -> list[Any]:
        """Read a remote BBMD's Foreign Device Table (FDT).

        See :meth:`read_broadcast_distribution_table` for the underlying
        mechanism; this issues a ``Read-Foreign-Device-Table`` BVLL
        message instead.

        :param bbmd_address: The BBMD's network address.
        :type bbmd_address: str | Address
        :param timeout: Timeout in seconds for this call.
        :type timeout: float | None
        :returns: The FDT entries reported by the BBMD.
        :rtype: list[Any]
        :raises BACnetProtocolError: If no response is received in time.
        """
        self._assert_connected()
        target = (
            Address(bbmd_address) if isinstance(bbmd_address, str) else bbmd_address
        )

        async def _do() -> Any:
            assert self._bvll_ase is not None
            future = self._bvll_ase.read_foreign_device_table(target)
            return await future

        return list(self._run_coro(_do(), timeout=timeout))


class BACnet_Subscription:
    """
    Handle for an active BACnet Change-of-Value (COV) subscription.

    Returned by :meth:`BACnet_Connection.subscribe_cov`. Mirrors
    :class:`~icspacket.proto.opcua.connection.OPCUA_Subscription`'s shape:
    unlike :mod:`asyncua`, BACpypes3 provides no ready-made synchronous
    subscription buffer, so this class runs a background task on the
    connection's event-loop thread that pumps notifications
    (``await scm.get_value()``) into a thread-safe :class:`queue.Queue`,
    exposed here as a blocking, iterable API.

    Example:

    .. code-block:: python

        sub = conn.subscribe_cov("192.168.1.60", "analog-input,1")
        for property_identifier, value in sub:
            print(property_identifier, value)
        sub.close()

    Also usable as a context manager, which calls :meth:`close` on exit:

    .. code-block:: python

        with conn.subscribe_cov("192.168.1.60", "analog-input,1") as sub:
            event = sub.next_value(timeout=5.0)
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        scm: Any,
        pump_task: asyncio.Task,
        notifications: queue.Queue,
    ) -> None:
        self._loop = loop
        self._scm = scm
        self._pump_task = pump_task
        self._queue = notifications
        self._closed = False

    def next_value(
        self, timeout: float | None = None
    ) -> tuple[PropertyIdentifier, Any] | None:
        """Wait for and return the next COV notification.

        :param timeout: Maximum time in seconds to wait, or ``None`` to
            block indefinitely.
        :type timeout: float | None
        :returns: A ``(property_identifier, value)`` tuple, or ``None``
            if ``timeout`` elapsed with no notification.
        :rtype: tuple[PropertyIdentifier, Any] | None
        :raises BACnetProtocolError: If the subscription's background
            pump task failed (e.g. the subscription was cancelled or
            expired on the server side).
        """
        try:
            item = self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
        if isinstance(item, BaseException):
            raise BACnetProtocolError(f"COV subscription failed: {item}") from item
        return item

    def __iter__(self):
        while not self._closed:
            item = self.next_value()
            if item is not None:
                yield item

    def close(self) -> None:
        """Cancel the subscription and release resources.

        Idempotent: safe to call more than once.
        """
        if self._closed:
            return
        self._closed = True

        async def _do_close() -> None:
            self._pump_task.cancel()
            try:
                await self._pump_task
            except (asyncio.CancelledError, BaseException):
                pass
            await self._scm.__aexit__(None, None, None)

        future = asyncio.run_coroutine_threadsafe(_do_close(), self._loop)
        try:
            future.result(timeout=5.0)
        except Exception:
            logger.debug(
                "Cleanup while closing BACnet COV subscription raised", exc_info=True
            )
            future.cancel()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
