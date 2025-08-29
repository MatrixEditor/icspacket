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
# pyright: reportUnusedCallResult=false
import logging

from rich.logging import RichHandler
from rich.markup import escape

SAFE = object()
"""
Sentinel object used to mark log messages that should be escaped to prevent
Rich markup injection.
"""

TRACE = 5
"""
Custom logging level for trace messages, numerically below ``DEBUG`` (value =
5). These messages will appear when using ``-vvv`` verbosity.
"""

TRACE_PACKETS = 4
"""
Custom logging level to trace packets, numerically below ``TRACE`` (value =
4). These messages will appear when using ``-vvvv`` verbosity.

.. versionadded:: 0.2.0
"""


class PrefixFormatter(logging.Formatter):
    """
    Custom log formatter that injects colored prefixes and safely handles
    message escaping.
    """

    def __init__(self):
        logging.Formatter.__init__(self, "%(prefix)s %(message)s")

    def format(self, record):
        """Format a log record by injecting a prefix and optionally escaping the message."""
        match record.levelno:
            case logging.INFO:
                record.prefix = "[[cyan]I[/]]"
            case logging.DEBUG:
                record.prefix = "[[green]D[/]]"
            case logging.WARNING:
                record.prefix = "[[yellow]W[/]]"
            case logging.ERROR:
                record.prefix = "[[red]E[/]]"
            case logging.CRITICAL:
                record.prefix = "[[white on red]C[/]]"
            case 5 | 4:
                record.prefix = "[[dark_green]T[/]]"
            case _:
                record.prefix = "[[bright_black]-[/]]"

        if SAFE in (record.args or ()):
            index = record.args.index(SAFE)
            record.msg = escape(record.msg)
            # REVISIT: this does not work properly
            record.args = list(record.args[:index]) + list(record.args[index + 1 :])

        if record.name != "root":
            record.msg = f"([i]{record.name}[/]) {record.msg}"

        return logging.Formatter.format(self, record)


def init(ts=False, level: int = logging.INFO):
    """Initialize the global logging system with Rich-based formatting.

    Can optionally show timestamps.

    :param ts: Whether to include timestamps in log messages.
    :type ts: bool
    :param level: Logging level to configure for the root logger.
    :type level: int
    """
    handler = RichHandler(
        level=level,
        show_level=False,
        show_path=level <= logging.DEBUG,
        show_time=ts,
        rich_tracebacks=False,
        markup=True,
        keywords=[],
        omit_repeated_times=False,
    )
    # we don't want to use any highlighter
    handler.highlighter = None

    logger = logging.getLogger()
    logger.setLevel(level)
    handler.setFormatter(PrefixFormatter())
    logger.addHandler(handler)


def init_from_args(verbosity: int, quiet: bool, ts: bool):
    """Initialize logging from CLI-like verbosity/quiet flags.

    This helper interprets CLI verbosity levels into logging levels:

    * ``verbosity = 0`` -> ``INFO``
    * ``verbosity = 1`` -> ``DEBUG``
    * ``verbosity = 2`` -> ``TRACE``
    * ``verbosity >= 3`` -> ``TRACE_PACKETS``
    * ``quiet = True`` -> force ``ERROR`` regardless of verbosity

    :param verbosity: CLI verbosity count (``-v`` flags).
    :type verbosity: int
    :param quiet: Whether quiet mode is enabled (suppresses most logs).
    :type quiet: bool
    :param ts: Whether to show timestamps in log output.
    :type ts: bool
    """
    level = logging.INFO
    if verbosity == 1:
        level = logging.DEBUG
    elif verbosity == 2:
        level = TRACE
    elif verbosity >= 3:
        level = TRACE_PACKETS
    if quiet:
        level = logging.ERROR

    init(ts, level)
