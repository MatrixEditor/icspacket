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
"""This subpackage implements typed wrappers for the CIP objects defined in
ODVA CIP Volumes 1 and 2: Identity, Message Router, Assembly, Connection and
Connection Manager, TCP/IP Interface and Ethernet Link, Simple I/O, Group,
Parameter, Diagnostics (File, Event Log), Time Sync, Drive, Motion,
Semiconductor, and EtherNet/IP switch management (DLR, QoS, Base Switch,
SNMP, Power Management, RSTP, PRP), together with the class-code registry
that ties them together (:mod:`icspacket.proto.cip.objects.registry`).
"""

# Every wrapper module is imported below purely for its registration side
# effect.
from . import ( # noqa
    assembly as _assembly,
    connection as _connection,
    connmgr as _connmgr,
    diagnostics as _diagnostics,
    drive as _drive,
    ethlink as _ethlink,
    group as _group,
    identity as _identity,
    motion as _motion,
    msgrouter as _msgrouter,
    parameter as _parameter,
    point as _point,
    semiconductor as _semiconductor,
    simple as _simple,
    switch as _switch,
    tcpip as _tcpip,
    timesync as _timesync,
)
