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
"""Wrapper and service helpers for the CIP Connection Manager Object (0x06)."""

from collections.abc import Iterable
from typing import Any, ClassVar

from icspacket.proto.cip.connmgr import (
    ForwardCloseRequest,
    ForwardCloseResponse,
    ForwardOpenRequest,
    ForwardOpenResponse,
    LargeForwardOpenRequest,
)
from icspacket.proto.cip.const import ClassCode, CommonService
from icspacket.proto.cip.epath import EPATH
from icspacket.proto.cip.msgrouter import MessageRouterRequest, MessageRouterResponse

from ._base import CIPObject


class ConnectionManagerObject(CIPObject):
    """Access Connection Manager class and instance attributes.

    Forward_Open, Forward_Close, and Unconnected_Send wire handling
    remains in :class:`CIP_Connection`; these methods only delegate to
    that implementation.
    """

    CLASS_CODE: ClassVar[ClassCode] = ClassCode.CONNECTION_MANAGER

    def get_class_attribute(self, attribute: int) -> bytes:
        """Read a Connection Manager class attribute from instance 0."""
        return self.get_attr(attribute, instance=0)

    def get_instance_attribute(self, attribute: int) -> bytes:
        """Read a Connection Manager instance attribute."""
        return self.get_attr(attribute)

    def set_instance_attribute(self, attribute: int, value: bytes) -> bytes:
        """Write a Connection Manager instance attribute."""
        return self.set_empty(attribute, value)

    def get_connection_data(self, request_data: bytes = b"") -> bytes:
        """Invoke Get_Connection_Data with caller-provided request bytes."""
        return self.message(CommonService.GET_CONNECTION_DATA, request_data)

    def forward_open(
        self,
        request: ForwardOpenRequest | LargeForwardOpenRequest | None = None,
        **kwargs: Any,
    ) -> ForwardOpenResponse:
        """Delegate Forward_Open to the underlying connection."""
        if request is None:
            return self.connection.forward_open(**kwargs)
        if kwargs:
            raise TypeError(
                "specify a Forward_Open request or keyword fields, not both"
            )
        return self.connection.forward_open(request)

    def large_forward_open(
        self, request: LargeForwardOpenRequest | None = None, **kwargs: Any
    ) -> ForwardOpenResponse:
        """Delegate Large_Forward_Open to the underlying connection."""
        if request is None:
            return self.connection.large_forward_open(**kwargs)
        if kwargs:
            raise TypeError(
                "specify a Large_Forward_Open request or keyword fields, not both"
            )
        return self.connection.large_forward_open(request)

    def forward_close(
        self, request: ForwardCloseRequest | None = None, **kwargs: Any
    ) -> ForwardCloseResponse:
        """Delegate Forward_Close to the underlying connection."""
        if request is None:
            return self.connection.forward_close(**kwargs)
        if kwargs:
            raise TypeError(
                "specify a Forward_Close request or keyword fields, not both"
            )
        return self.connection.forward_close(request)

    def unconnected_send(
        self,
        message: MessageRouterRequest | bytes | None = None,
        route_path: EPATH | bytes | Iterable[Any] | None = None,
        **kwargs: Any,
    ) -> MessageRouterResponse:
        """Delegate Unconnected_Send to the underlying connection."""
        if route_path is None:
            return self.connection.unconnected_send(message, **kwargs)
        return self.connection.unconnected_send(message, route_path, **kwargs)


__all__ = ["ConnectionManagerObject"]
