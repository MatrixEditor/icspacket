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
**ODVA CIP Networks Library Volume 1: Common Industrial Protocol, and
Volume 2: EtherNet/IP Adaptation of CIP**

This package provides a pure-Python implementation of the Common Industrial
Protocol (CIP): a network-independent, object-oriented application layer in
which every device exposes its data and behavior as class/instance/attribute
addressed objects (:mod:`icspacket.proto.cip.objects`), located through
EPATHs (:mod:`icspacket.proto.cip.epath`) and manipulated through Message
Router requests (:mod:`icspacket.proto.cip.msgrouter`).

EtherNet/IP (CIP Volume 2) is the TCP/UDP adaptation covered here: session
encapsulation (:mod:`icspacket.proto.cip.encap`) and the Common Packet
Format that carries addressing and data items alongside it
(:mod:`icspacket.proto.cip.cpf`). On top of that transport, the package
implements both CIP messaging types - explicit (unconnected and
Connection-Manager-brokered connected messaging,
:mod:`icspacket.proto.cip.connmgr`) and implicit (cyclic Class 0/1 I/O,
:mod:`icspacket.proto.cip.io`) - behind client connections
(:mod:`icspacket.proto.cip.connection`).

.. versionadded:: 0.3.0
"""
