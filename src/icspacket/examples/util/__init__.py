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
Support code for icspacket's examples
"""


def add_logging_options(parser):
    # fmt: off
    # ------------------------------------------------------------------------
    # Logging options
    # ------------------------------------------------------------------------
    log_group = parser.add_argument_group("Logging Options", "Control verbosity and formatting of log messages")
    log_group.add_argument("-v", action="count", help="Increase logging verbosity (can be specified multiple times)", dest="verbosity", default=0)
    log_group.add_argument("-q", "--quiet", action="store_true", help="Suppress informational logs (errors still printed)", default=False)
    log_group.add_argument("--ts", action="store_true", help="Add timestamps to log messages", default=False)
    # fmt: on
