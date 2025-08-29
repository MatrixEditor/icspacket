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
from argparse import ArgumentParser
import getpass
import logging
import pathlib
import shlex

from icspacket.core.logger import SAFE
from icspacket.proto.cotp.connection import COTP_Connection
from icspacket.proto.cotp.structs import TPDU_Size
from icspacket.proto.mms.asn1types import ObjectName
from icspacket.proto.mms.acse import ACSEConnectionError, PasswordAuth
from icspacket.proto.mms.connection import MMS_Connection
from icspacket.proto.mms.util import domain_object_name
from icspacket.proto.tpkt import tpktsock


def parse_auth(auth_spec: str | None, from_stdin: bool) -> PasswordAuth | None:
    """
    Parse an MMS password authentication specification.

    The authentication string is expected to follow the format::

        <qualifier>@<title>:<password>

    - ``qualifier`` (int): An integer ACSE authentication qualifier.
    - ``title`` (str): A user identity or role string. represented as an OID
    - ``password`` (str): The associated password.

    If ``auth_spec`` is ``None`` and ``from_stdin`` is ``True``,
    the user will be prompted interactively (without echo) to
    enter the specification in the same format.

    :param auth_spec: Authentication string in
        ``<qualifier>@<title>:<password>`` form, or ``None``.
    :type auth_spec: str | None
    :param from_stdin: If ``True`` and ``auth_spec`` is not provided,
        request interactive input via :mod:`getpass`.
    :type from_stdin: bool

    :returns: A :class:`PasswordAuth` object on success, or ``None`` if parsing failed.
    :rtype: PasswordAuth | None

    :raises ValueError: If ``auth_spec`` is malformed.

    Example:

    >>> parse_auth("123@1.2.3:secret", from_stdin=False)
    PasswordAuth(password='secret', title='1.2.3', qualifier=123)
    """
    if not auth_spec:
        if not from_stdin:
            return None

        auth_spec = getpass.getpass("<qualifier>@<title>:<password> : ")

    if "@" not in auth_spec:
        logging.error("Invalid authentication specification: missing qualifier")
        return None

    qualifier, principal = shlex.split(auth_spec)[0].split("@", 1)
    if ":" not in principal:
        logging.error("Invalid authentication specification: missing title or password")
        return None

    title, password = principal.split(":", 1)
    return PasswordAuth(password, title, int(qualifier))


def parse_variable_target(
    target_spec: list[str], global_domain: str | None
) -> list[ObjectName] | None:
    """
    Normalize and resolve variable target specifications for MMS services.

    A target specification may take one of the following forms:

    - ``<domain>/<variable>``
      Fully-qualified domain and variable name.
      Example: ``PROCESS/Valve.State`` → ``PROCESS/Valve$State``

    - ``<variable>`` (with global domain)
      Shorthand form where the domain is supplied via ``--domain`` or
      the ``global_domain`` argument.
      Example: ``Temperature`` with ``--domain PLANT`` → ``PLANT/Temperature``

    - ``vmd:<variable>``
      Variable defined at the **Virtual Manufacturing Device** scope.
      Example: ``vmd:Uptime``

    - ``aa:<variable>``
      Variable tied to the **Application Association** scope.
      Example: ``aa:SessionCounter``

    - ``<file>``
      Path to a text file containing one target specification per line.
      File contents may mix any of the above formats. Empty lines are ignored.
      Example file ``targets.txt``:

      .. code-block::

         PROCESS/Valve.State
         aa:SessionCounter
         vmd:Uptime

    .. note::
       MMS identifiers cannot contain dots (``.``).
       To ensure compatibility, dots in variable names are automatically
       replaced with ``$`` during normalization.

    :param target_spec: List of raw target strings (domain/variable, shorthand variable,
                        vmd:/aa: form, or filename).
    :type target_spec: list[str]
    :param global_domain: Default domain to apply if only a variable name is given.
    :type global_domain: str | None

    :returns: A list of normalized ``ObjectName`` instances ready for MMS service requests,
              or ``None`` if parsing fails.
    :rtype: list[ObjectName] | None

    :raises ValueError: If a variable without domain is given and no ``global_domain`` is set.

    Example usage:

    >>> parse_variable_target(["PLANT/Temp.Sensor"], None)
    [ObjectName(domain_specific=('PLANT', 'Temp$Sensor'))]

    >>> parse_variable_target(["Temp1"], global_domain="SYS")
    [ObjectName(domain_specific=('SYS', 'Temp1'))]

    >>> parse_variable_target(["vmd:Uptime"], None)
    [ObjectName(vmd_specific='Uptime')]

    >>> parse_variable_target(["aa:Counter"], None)
    [ObjectName(aa_specific='Counter')]

    >>> parse_variable_target(["targets.txt"], global_domain="PLANT")
    [ObjectName(domain_specific=('PLANT', 'Var1')),
     ObjectName(aa_specific='SessionCounter'),
     ObjectName(vmd_specific='Uptime')]
    """
    collected_targets = []
    for target in target_spec:
        target_path = pathlib.Path(target)
        if target_path.is_file():
            for line in target_path.read_text().splitlines():
                if line:
                    collected_targets.append(line)
        else:
            collected_targets.append(target)

    cleaned_targets = list()
    for target in collected_targets:
        if "/" in target:
            domain, name = target.split("/", 1)
            cleaned_targets.append(domain_object_name(domain, name.replace(".", "$")))
        elif target.startswith("vmd:"):
            name = target[4:]
            cleaned_targets.append(ObjectName(vmd_specific=name))

        elif target.startswith("aa:"):
            name = target[3:]
            cleaned_targets.append(ObjectName(aa_specific=name))
        else:
            # domain MUST be set
            if not global_domain:
                logging.error("No domain specified and no global domain set")
                return None

            cleaned_targets.append(
                domain_object_name(global_domain, target.replace(".", "$"))
            )
    return cleaned_targets


def init_mms_connection(
    host: str,
    port: int,
    auth_spec: str,
    auth_stdin: bool = False,
    timeout: float | None = None,
    tpdu_size: TPDU_Size | None = None,
) -> MMS_Connection | None:
    """
    Initialize and associate an MMS connection to a remote peer.

    This helper combines parsing of authentication credentials,
    establishing a COTP transport connection, and performing the
    MMS association handshake.

    :param host: Target host (IP address or hostname).
    :type host: str
    :param port: Target TCP port number.
    :type port: int
    :param auth_spec: Authentication string in the form
        ``<qualifier>@<title>:<password>``.
    :type auth_spec: str
    :param auth_stdin: If ``True``, prompt for authentication via stdin
        if ``auth_spec`` is empty.
    :type auth_stdin: bool, optional
    :param timeout: Connection timeout in seconds, or ``None`` for default.
    :type timeout: float | None, optional
    :param tpdu_size: TPDU size to negotiate, defaults to 1024 octets if not provided.
    :type tpdu_size: TPDU_Size | None, optional

    :returns: An established :class:`MMS_Connection` instance on success,
        or ``None`` if the association failed.
    :rtype: MMS_Connection | None

    :raises ACSEConnectionError: If association fails due to authentication.
    :raises ConnectionRefusedError: If the TCP connection is refused.
    :raises ConnectionError: For other transport or protocol-level errors.

    Example:
    >>> conn = init_mms_connection(
    ...     host="192.168.1.100",
    ...     port=102,
    ...     auth_spec="100@1.2.3:secret"
    ... )
    >>> if conn:
    ...     print("Connected to MMS peer!")
    """
    auth = parse_auth(auth_spec, auth_stdin)
    cotp = COTP_Connection(
        sock_cls=tpktsock,
        timeout=timeout,
        max_tpdu_size=TPDU_Size(tpdu_size) if tpdu_size else TPDU_Size.SIZE_1024,
    )
    conn = MMS_Connection(auth=auth, cotp_conn=cotp)
    logging.info(f"Associating MMS environment with peer {host}:{port}...", SAFE)
    if auth is not None:
        logging.info(
            f"Using password authentication as {auth.title} ({auth.qualifier})", SAFE
        )

    try:
        conn.associate((host, port))
    except ACSEConnectionError as e:
        if auth is None:
            logging.error("Could not associate, please provide authentication options!")
        else:
            logging.exception("Could not associate", e)
    except ConnectionRefusedError:
        logging.error(
            f"Failed to connect to {host} with port {port} (connection refused)"
        )
    except ConnectionError as e:
        logging.exception("Encountered an error while connecting to target", e)
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user")
    else:
        logging.debug(f"Entered MMS environment with peer at {host}:{port}")
        return conn


def add_mms_connection_options(parser: ArgumentParser) -> None:
    # fmt: off
    parser.add_argument("-i", "--interactive", action="store_true", help="Continue in interactive mode acter executing the first command (only if given)", default=False)
    # ------------------------------------------------------------------------
    # Authentication options
    # ------------------------------------------------------------------------
    auth_group = parser.add_argument_group("Authentication Options", "ACSE/Password authentication for MMS association")
    auth_group.add_argument("--auth", type=str, metavar="<qualifier>@<title>:<password>", help="Password-based authentication specification, e.g., '100@operator:secret'", default=None)
    auth_group.add_argument("--auth-stdin", action="store_true", help="Read authentication specification from stdin (interactive prompt)", default=False)

    # ------------------------------------------------------------------------
    # Connection options
    # ------------------------------------------------------------------------
    conn_group = parser.add_argument_group("Connection Options","Specify transport layer settings and target host information")
    conn_group.add_argument("-p", "--port", type=int, help="TCP port of the target MMS server (default: 102)", default=102)
    conn_group.add_argument("--max-tpdu-size", type=int, metavar="SIZE", help="Maximum TPDU size to negotiate during COTP connection", default=TPDU_Size.SIZE_1024)
    conn_group.add_argument("--timeout", type=float, metavar="SEC", help="Timeout in seconds for transport-level operations (default: None)", default=None)
    conn_group.add_argument("host", type=str, help="Target host (IP address or hostname) to establish MMS connection")
    # fmt: on
