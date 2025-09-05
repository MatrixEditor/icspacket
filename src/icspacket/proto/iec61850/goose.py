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
# pyright: reportInvalidTypeForm=false, reportGeneralTypeIssues=false, reportAssignmentType=false
import logging

from queue import Queue
from threading import Event
from typing import Any, Callable, TypeVar

from caterpillar.fields import Bytes, uint16
from caterpillar.model import pack, unpack

from caterpillar.shortcuts import struct, BigEndian, this
from scapy.arch import get_if_hwaddr
from scapy.error import Scapy_Exception
from scapy.layers.l2 import Dot1Q, Ether
from scapy.packet import Raw
from scapy.sendrecv import AsyncSniffer, sendp, sendpfast

from icspacket.core.logger import TRACE, TRACE_PACKETS
from icspacket.core.hexdump import hexdump
from icspacket.proto.iec61850._iec61850 import *  # noqa

_T = TypeVar("_T")

GOOSE_ETHER_TYPE = 0x88B8
"""
EtherType value assigned to IEC 61850 GOOSE (Generic Object Oriented Substation
Event)
"""

# private
_DOT1Q_ETHER_TYPE = 0x8100


@struct(order=BigEndian)
class PDU:
    """
    Protocol Data Unit (PDU) representing the ISO/IEC 8802-3 frame structure
    used for GSE management and GOOSE communication.

    The PDU wraps the **Application Protocol Data Unit (APDU)** carried in an
    Ethernet frame. The frame contains reserved fields in addition to the
    application identifier and APDU payload.

    """

    app_id: uint16 = 0
    """
    Application identifier (AppID). This field uniquely identifies the
    application instance for which the message is intended.
    """

    length: uint16 = 0
    """
    Total length of the PDU in bytes, including the 8-byte header (AppID,
    Length, Reserved1, Reserved2).
    """

    reserved1: uint16 = 0
    reserved2: uint16 = 0

    raw_apdu: Bytes(this.length - 8) = b""
    """
    Encoded APDU (Application Protocol Data Unit). This may contain ASN.1
    BER-encoded payloads or raw bytes depending on context.
    """

    def build(self) -> bytes:
        """
        Construct a serialized representation of the PDU.

        If the ``raw_apdu`` field has a ``ber_encode()`` method, the APDU
        is encoded before serialization. The length field is automatically
        recalculated to include the header.

        :return: A serialized PDU ready for transmission over Ethernet.
        :rtype: bytes
        :raises TypeError:
            If ``raw_apdu`` is not a byte sequence after encoding.
        """
        if hasattr(self.raw_apdu, "ber_encode"):
            self.raw_apdu = self.raw_apdu.ber_encode()

        if not isinstance(self.raw_apdu, bytes):
            raise TypeError("apdu must be bytes")

        self.length = len(self.raw_apdu) + 8
        return pack(self)

    def apdu(self, asn1_cls: type[_T]) -> _T:
        """
        Decode the APDU portion of the PDU.

        :param asn1_cls:
            ASN.1 class type implementing a ``ber_decode()`` method.
        :type asn1_cls: type
        :return: Decoded APDU instance.
        :rtype: _T
        """
        return asn1_cls.ber_decode(self.raw_apdu)

    @staticmethod
    def from_octets(pctets: bytes) -> "PDU":
        """
        Parse a serialized byte sequence into a :class:`PDU`.

        :param bytes pctets:
            Raw PDU bytes extracted from an Ethernet frame.
        :return: A :class:`PDU` instance parsed from the octets.
        :rtype: PDU
        """
        return unpack(PDU, pctets)


class GOOSE_Client:
    """
    Observer **and Publisher** for IEC 61850 GOOSE (Generic Object Oriented
    Substation Event) messages.

    This class provides a dual role:

    1. **Observer** — It captures and filters incoming GOOSE PDUs
       using **Scapy**'s asynchronous sniffer. Incoming PDUs can be accessed
       through a queue or by registering a callback.
    2. **Publisher** — It constructs and transmits GOOSE PDUs over Ethernet,
       supporting both raw PDUs and higher-level APDUs. VLAN tagging is
       supported where required by the application environment.

    Clients can be used as context managers to ensure proper startup and
    teardown of the sniffer. For example:

    .. code-block:: python

        with GOOSE_Client(iface="eth0") as client:
            # Capture one incoming PDU
            incoming_pdu = client.recv_next()

            # Publish a new PDU (simple echo)
            client.publish_pdu("01:0c:cd:01:00:01", incoming_pdu)

    .. note::
        Publishing can be done **without** a sniffer running in the background,
        i.e. the with statement can be ignored.

    .. versionadded:: 0.2.3

    :param iface:
        Optional capture interface or list of interfaces to sniff on.
        If multiple interfaces are provided, publishing requires
        explicit configuration of ``iface`` or ``all_interfaces=True``.
    :type iface: str | list[str] | None
    :param callback:
        Optional callback invoked for each received GOOSE frame.
        The callback receives the raw :class:`Ether` frame and the decoded :class:`PDU`.
    :type callback: Callable[[Ether, PDU], None] | None
    :param ether_type:
        EtherType filter for GOOSE traffic. Defaults to :data:`GOOSE_ETHER_TYPE`.
    :type ether_type: int
    :param inputs:
        Optional list of input files (pcap) for offline analysis.
    :type inputs: list[str] | None
    :param app_id:
        Default application identifier (AppID) to use when publishing.
    :type app_id: int | None
    :param vlan_id:
        Default VLAN identifier to apply when publishing. If ``None``,
        packets are sent without VLAN tagging unless overridden in the
        publish call.
    :type vlan_id: int | None
    """

    def __init__(
        self,
        iface: list[str] | str | None = None,
        callback: Callable[[Ether, PDU], None] | None = None,
        ether_type: int = GOOSE_ETHER_TYPE,
        inputs: list[str] | None = None,
        app_id: int | None = None,
        vlan_id: int | None = None,
    ) -> None:
        args = {
            "prn": self._process_pkt,
            "store": 0,
            "lfilter": self._filter_pkt,
        }
        if iface:
            args["iface"] = iface
        if inputs:
            args["offline"] = inputs
        self.__sniffer = AsyncSniffer(**args)
        self.__stop = Event()
        self.__pkt_in = Queue()
        self.__ether_type = ether_type
        self.__iface = iface

        self.app_id = app_id or 0
        self.vlan_id = vlan_id
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    def __enter__(self) -> "GOOSE_Client":
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    @property
    def pkt_in(self) -> Queue[PDU]:
        """
        Queue of decoded PDUs captured by the observer.

        :return: A thread-safe queue containing :class:`PDU` objects.
        :rtype: Queue[PDU]
        """
        return self.__pkt_in

    def _filter_pkt(self, pkt: Ether) -> bool:
        """
        Filter function applied to captured packets.

        Matches packets carrying the configured EtherType, either directly
        in the Ethernet header or within an IEEE 802.1Q VLAN tag.

        :param Ether pkt:
            The captured packet.
        :return: ``True`` if the packet should be processed, ``False`` otherwise.
        :rtype: bool
        """
        vlan_pkt = pkt.getlayer(Dot1Q)
        if vlan_pkt is not None and vlan_pkt.type == self.__ether_type:
            return True

        if type(pkt) != Ether:
            return False

        return pkt.type == self.__ether_type

    def _process_pkt(self, pkt: Ether) -> None:
        """
        Process a packet that passed the filter.

        Decodes the payload into a :class:`PDU`, logs trace information,
        and invokes the configured callback (if any).

        :param Ether pkt:
            The captured Ethernet frame.
        """
        vlan_pkt = pkt.getlayer(Dot1Q)
        if vlan_pkt is not None:
            payload = vlan_pkt.payload.load
            self.logger.log(
                TRACE_PACKETS,
                "(VLAN %s) 802.1Q from %s\n%s",
                vlan_pkt.vlan,
                pkt.src,
                hexdump(payload),
            )
        else:
            payload = pkt.payload.load
            self.logger.log(
                TRACE_PACKETS,
                "Raw framge from %s\n%s",
                pkt.src,
                hexdump(payload),
            )

        try:
            pdu = PDU.from_octets(payload)
        except Exception as e:
            self.logger.log(TRACE, "Failed to parse IEC61850 PDU: %s", e)
            return

        if self.callback:
            try:
                self.callback(pkt, pdu)
            except Exception as e:
                self.logger.exception(e)
        self.__pkt_in.put(pdu)

    def start(self) -> None:
        """
        Start the observer and begin sniffing packets.

        This resets the incoming PDU queue and clears the stop event.
        """
        if self.__sniffer.running:
            return

        self.__stop.clear()
        self.__sniffer.start()
        del self.__pkt_in
        self.__pkt_in = Queue()

    def stop(self, join: bool = False):
        """Stop the observer and terminate packet sniffing.

        .. tip::
            Use the ``join`` parameter to read out all remaining packets from PCAP
            files if specified in the constructor.

        :param bool join:
            If ``True``, block until the sniffer thread terminates.
        """
        self.__stop.set()
        try:
            if self.__sniffer.running:
                if join:
                    self.__sniffer.join()
                _ = self.__sniffer.stop()
        except Scapy_Exception:
            # in case no packets were captured
            pass

    def listen_forever(self) -> None:
        """
        Continuously capture GOOSE packets until interrupted.

        This method blocks the calling thread until ``stop()`` is invoked
        or a keyboard interrupt is received.
        """
        # ensures the sniffer is not running and clears __stop
        self.start()
        try:
            while not self.__stop.is_set():
                self.__stop.wait(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def recv_next(self) -> PDU:
        """
        Retrieve the next decoded PDU from the capture queue.

        :return: The next available :class:`PDU`.
        :rtype: PDU
        :raises ConnectionError:
            If the sniffer is not currently running.
        """
        if not self.__sniffer.running:
            raise ConnectionError("Sniffer is not running")

        return self.pkt_in.get()

    def publish_pdu(
        self,
        addr: str,
        pdu: PDU,
        vlan_id: int | None = None,
        vlan_priority: int | None = None,
        iface: str | None = None,
        all_interfaces: bool = False,
    ) -> None:
        """
        Transmit a fully constructed :class:`PDU` to the given destination address.

        This is the low-level publishing method. It requires the caller
        to provide a complete :class:`PDU` object (including encoded APDU).
        VLAN tagging and priority handling are supported.

        :param str addr:
            Destination MAC address for the frame (typically a GOOSE
            multicast address).
        :param PDU pdu:
            The protocol data unit to serialize and publish.
        :param vlan_id:
            VLAN identifier to use for this transmission. If ``None``,
            the instance's default VLAN ID is used. If still ``None``,
            the frame is sent without VLAN tagging.
        :type vlan_id: int | None
        :param vlan_priority:
            Optional VLAN priority code point (PCP) to apply. Ignored if
            ``vlan_id`` is ``None``.
        :type vlan_priority: int | None
        :param iface:
            Explicit interface to publish on. If not provided, the default
            interface(s) configured in the client are used.
        :type iface: str | None
        :param bool all_interfaces:
            If multiple interfaces were configured and this flag is ``True``,
            the PDU is transmitted on all interfaces. If ``False`` and multiple
            interfaces exist, an explicit ``iface`` must be given.
        :raises ValueError:
            If multiple interfaces are configured but no target interface
            was specified and ``all_interfaces`` is ``False``.
        """
        vlan_id = vlan_id if vlan_id is not None else self.vlan_id
        if not iface:
            if isinstance(self.__iface, list):
                if not all_interfaces:
                    raise ValueError(
                        "iface must be specified if multiple interfaces are available"
                    )
                target = self.__iface
            else:
                target = [self.__iface]
        else:
            target = [iface]

        for iface in target:
            mac_addr = get_if_hwaddr(iface)
            pkt = Ether(
                type=_DOT1Q_ETHER_TYPE if vlan_id is not None else self.__ether_type,
                dst=addr,
                src=mac_addr,
            )
            if vlan_id is not None:
                pkt = pkt / Dot1Q(
                    vlan=vlan_id,
                    prio=vlan_priority if vlan_priority is not None else 0,
                    type=self.__ether_type,
                )

            pkt.add_payload(pdu.build())
            _ = sendp(pkt, iface=iface, verbose=False)

    def publish(
        self,
        addr: str,
        aodu: Any,
        app_id: int | None = None,
        vlan_id: int | None = None,
        vlan_priority: int | None = None,
        iface: str | None = None,
        all_interfaces: bool = False,
    ) -> None:
        """
        Publish an APDU (Application Protocol Data Unit) directly as a GOOSE PDU.

        This higher-level publishing method simplifies transmission by
        constructing the PDU automatically from the given APDU. The
        APDU may be a raw ASN.1 object (with a ``ber_encode()`` method)
        or already-encoded bytes.

        .. note::
            This method automatically wraps the APDU in a :class:`PDU`
            with the appropriate ``AppID``.

        :param str addr:
            Destination MAC address for the frame (typically a GOOSE
            multicast address).
        :param aodu:
            The APDU to embed in the outgoing PDU. Can be an ASN.1 object
            or raw bytes.
        :type aodu: Any
        :param app_id:
            Application identifier to use. If ``None``, the default
            ``app_id`` set on the client instance is applied.
        :type app_id: int | None
        :param vlan_id:
            VLAN identifier to use for this transmission. Overrides the
            instance default if provided.
        :type vlan_id: int | None
        :param vlan_priority:
            Optional VLAN priority code point (PCP) to apply. Ignored if
            ``vlan_id`` is ``None``.
        :type vlan_priority: int | None
        :param iface:
            Explicit interface to publish on. If not provided, the default
            interface(s) configured in the client are used.
        :type iface: str | None
        :param bool all_interfaces:
            If multiple interfaces were configured and this flag is ``True``,
            the PDU is transmitted on all interfaces. If ``False`` and multiple
            interfaces exist, an explicit ``iface`` must be given.
        """
        app_id = app_id if app_id is not None else self.app_id
        pdu = PDU(app_id=app_id, raw_apdu=aodu)
        self.publish_pdu(addr, pdu, vlan_id, vlan_priority, iface, all_interfaces)


__all__ = [  # noqa
    "GOOSE_ETHER_TYPE",
    "PDU",
    "GOOSE_Client",
    "Data",
    "MMSString",
    "FloatingPoint",
    "TimeOfDay",
    "IEC61850_Specific_Protocol",
    "GSEMngtPdu",
    "GSERequestResponse",
    "GSEMngtRequests",
    "GSEMngtResponses",
    "GetReferenceRequestPdu",
    "GetElementRequestPdu",
    "GSEMngtResponsePdu",
    "RequestResults",
    "GlbErrors",
    "ErrorReason",
    "IECGoosePdu",
    "UtcTime",
]
