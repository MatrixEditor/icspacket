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
from icspacket.proto.mms.asn1types import ServiceError


class MMSConnectionError(ConnectionError):
    """
    Raised when an MMS association or connection-related error occurs.

    This exception indicates that the remote MMS peer responded with
    an error at the connection-management level, such as during
    association setup (`M-ASSOCIATE`), release (`M-RELEASE`),
    abort (`M-U-ABORT`), or conclude (`M-CONCLUDE`).

    The contained :class:`ServiceError` provides detailed information
    about the nature of the failure as returned by the MMS peer.

    Example:
        .. code-block:: python

            try:
                mms_conn.associate(("192.168.1.100", 102))
            except MMSConnectionError as e:
                print(f"Association failed: {e.error}")

    :param error: MMS service error value returned by the peer.
    :type error: ServiceError
    :param args: Additional positional arguments passed to the base
        :class:`ConnectionError`.
    :type args: Any
    :ivar error: The MMS service error instance associated with this exception.
    :vartype error: ServiceError
    """

    error: ServiceError
    """The causing MMS service error"""

    def __init__(self, error: ServiceError, *args) -> None:
        super().__init__(error, *args)
        self.error = error


class MMSServiceError(ConnectionError):
    """
    Base class for all MMS service-related errors.

    This exception serves as a parent class for errors arising from
    incorrect or unsupported MMS service invocations, outside of
    connection setup/teardown.

    Subclasses provide more specific context, such as unknown service
    requests or invalid operations.

    Typically raised when an MMS primitive is received that cannot be
    handled by the local MMS-user.
    """


class MMSUnknownServiceError(MMSServiceError):
    """
    Raised when an unsupported or unknown MMS service is invoked.

    This exception is typically used to signal that the peer attempted
    to call an MMS service primitive that the local implementation
    does not support, or that is not defined in ISO 9506.

    Example:
        .. code-block:: python

            try:
                response = mms_conn.recv_mms_data()
            except MMSUnknownServiceError:
                print("Peer requested an unsupported MMS service.")
    """
