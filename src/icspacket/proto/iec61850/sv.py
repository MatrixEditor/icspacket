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
from typing import Callable

from scapy.layers.l2 import Ether

from icspacket.proto.iec61850._iec61850 import *  # noqa
from icspacket.proto.iec61850.goose import PDU, GOOSE_Client

#: Type alias for the IEC 61850-9-2 Sampled Values ASN.1 protocol
#: representation. This alias provides semantic clarity when working
#: with decoded SV application PDUs.
SampledValues = IEC61850_9_2_Specific_Protocol

#: EtherType used for IEC 61850-9-2 Sampled Values (SV) traffic.
#: According to the IEC 61850 standard, SV frames are identified
#: at the Ethernet layer with EtherType ``0x88BA``.
SV_ETHER_TYPE = 0x88BA


class SV_Client(GOOSE_Client):
    """
    Observer and Publisher for IEC 61850-9-2 Sampled Values (SV) traffic.

    This class is a protocol-specific specialization of
    :class:`GOOSE_Client` that automatically binds to the EtherType
    ``0x88BA`` used by **Sampled Values (SV)** frames. It reuses the
    same underlying packet capture, filtering, and publishing
    mechanisms provided by :class:`GOOSE_Client`, but targets SV
    instead of GOOSE.

    Core functionality:

    - **Observation:** Capture and decode SV PDUs from one or more
      interfaces, optionally with an application-provided callback.
    - **Publishing:** Transmit SV PDUs on a given interface or across
      multiple interfaces, with optional VLAN tagging support.
    - **Compatibility:** Since SV reuses the same PDU decoding layer,
      both online capture and offline PCAP file analysis are supported.

    .. code-block:: python
        :caption: Example

        # Capture Sampled Values on eth1
        with SV_Client(interfaces=["eth1"]) as sv_client:
            sv_pdu = sv_client.recv_next()
            print("Received SV:", sv_pdu)

        # Publish a new Sampled Value PDU
        sv_client = SV_Client(["eth1"])
        sv_client.publish("01:0c:cd:01:00:01", my_sv_apdu)

    .. versionadded:: 0.2.3

    :param interfaces:
        List of interface names (e.g., ``["eth0", "eth1"]``) to capture
        and/or publish Sampled Values on. If ``None``, the default system
        capture interface is used.
    :type interfaces: list[str] | None
    :param callback:
        Optional callback invoked for each received SV frame. The callback
        receives the raw :class:`Ether` frame and the decoded :class:`PDU`.
    :type callback: Callable[[Ether, PDU], None] | None
    :param inputs:
        Optional list of offline PCAP files to process instead of
        live capture.
    :type inputs: list[str] | None
    """

    def __init__(
        self,
        interfaces: list[str] | str | None = None,
        callback: Callable[[Ether, PDU], None] | None = None,
        inputs: list[str] | None = None,
    ) -> None:
        super().__init__(interfaces, callback, SV_ETHER_TYPE, inputs)


__all__ = [  # noqa
    "SampledValues",
    "IEC61850_9_2_Specific_Protocol",
    "SavPdu",
    "ASDU",
    "SV_ETHER_TYPE",
    "SV_Client",
]
