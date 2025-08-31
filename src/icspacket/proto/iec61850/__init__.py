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
IEC61850
========

Basic Information Models
------------------------

a) SERVER - represents the external visible behaviour of a device. All other
   ACSI models are part of the server.

b) LOGICAL-DEVICE (LD) - contains the information produced and consumed by a
   group of domain-specific application functions; functions are defined as
   LOGICAL-NODEs.

c) LOGICAL-NODE (LN) - contains the information produced and consumed by a
   domain-specific application function, for example, overvoltage protection or
   circuit-breaker.

d) DATA - provide means to specify typed information, for example, position of a
   switch with quality information and timestamp, contained in LOGICAL-NODEs


Example: In an implementation the logical device, logical node, data, and data
attribute have each an object name (:class:`ObjectName`).

-- IEC61850 7-2
"""