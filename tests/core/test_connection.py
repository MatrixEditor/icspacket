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
import pytest

from icspacket.core.connection import (
    ConnectionClosedError,
    ConnectionError,
    ConnectionNotEstablished,
    ConnectionStateError,
    connection,
)


def test_initial_state():
    conn = connection()
    assert conn.is_connected() is False
    assert conn.is_valid() is False


def test_connected():
    conn = connection()
    conn._connected = True
    assert conn.is_connected() is True
    conn._assert_connected()  # must not raise


def test_assert_not_connected():
    conn = connection()
    with pytest.raises(ConnectionNotEstablished):
        conn._assert_connected()


@pytest.mark.parametrize(
    "connected,valid",
    [
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test_is_valid(connected, valid):
    conn = connection()
    conn._connected = connected
    conn._valid = valid
    assert conn.is_connected() is connected
    assert conn.is_valid() is valid


@pytest.mark.parametrize(
    "method,args",
    [
        ("connect", (("host", 102),)),
        ("close", ()),
        ("send_data", (b"data",)),
        ("recv_data", ()),
    ],
)
def test_not_implemented(method, args):
    conn = connection()
    with pytest.raises(NotImplementedError):
        getattr(conn, method)(*args)


@pytest.mark.parametrize(
    "exc_type",
    [ConnectionClosedError, ConnectionNotEstablished, ConnectionStateError],
)
def test_error_hierarchy(exc_type):
    assert issubclass(exc_type, ConnectionError)
    assert issubclass(ConnectionError, Exception)
