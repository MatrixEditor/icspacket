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

This package works with four nested layers of ACSI objects, from the
outside in:

- **Server** - the whole addressable device as seen by a client; every other
  layer below lives inside it.
- **Logical Device (LD)** - a container grouping the data produced and
  consumed by a related set of application functions, each represented by a
  Logical Node.
- **Logical Node (LN)** - the unit modeling one specific application
  function, such as overvoltage protection or circuit-breaker.
- **Data** - a typed piece of information owned by a Logical Node, e.g. a
  switch position together with its quality and timestamp.

In this implementation, every level - logical device, logical node, data,
and data attribute - is identified by its own :class:`ObjectName`.

-- IEC61850 7-2
"""