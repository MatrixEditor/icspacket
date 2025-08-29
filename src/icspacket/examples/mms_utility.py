#!/usr/bin/env python
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
#
# Very basic approach to retrieve information from a remote MMS peer. Currently,
# it supports the following operations:
#
#   - Variables: read, write, query info
#   - Domain: list, and list variables
#   - identify
import pathlib
import shlex
import sys
import logging
import textwrap

from rich.markup import escape
from rich.table import Table
from rich import box, pretty

from icspacket.core.connection import ConnectionClosedError
from icspacket.examples.util import add_logging_options
from icspacket.proto.mms._mms import DataAccessError, TypeDescription
from icspacket.proto.mms.asn1types import (
    Data,
    ObjectClass,
    ServiceError,
)
from icspacket.proto.mms.connection import MMS_Connection
from icspacket.proto.mms.exceptions import MMSConnectionError
from icspacket.proto.mms.data import (
    get_floating_point_value,
    create_floating_point_value,
)
from icspacket.proto.mms.util import (
    ObjectScope,
    VariableAccessItem,
    basic_object_class,
    object_name_to_string,
)

from icspacket.examples.util.mms import (
    add_mms_connection_options,
    init_mms_connection,
    parse_variable_target,
)


def data_to_str(data: Data) -> str | dict | list:
    match data.present:
        case Data.PRESENT.PR_floating_point:
            return str(get_floating_point_value(data.floating_point))
        case Data.PRESENT.PR_integer:
            return str(data.integer)
        case Data.PRESENT.PR_octet_string:
            return data.octet_string.hex(sep=" ") if data.octet_string else "<EMPTY>"
        case Data.PRESENT.PR_bit_string | Data.PRESENT.PR_booleanArray:
            return data.bit_string.value.to01(sep=" ") if data.bit_string else "<EMPTY>"
        case Data.PRESENT.PR_boolean:
            return "[green]TRUE[/]" if data.boolean else "FALSE"
        case Data.PRESENT.PR_array:
            return [data_to_str(item) for item in data.array]
        case Data.PRESENT.PR_structure:
            return {
                item.present.name[3:].lower(): data_to_str(item)
                for item in data.structure
            }
        case Data.PRESENT.PR_visible_string:
            return escape(data.visible_string or "")
        case _:
            return escape(data.to_text().decode().strip())


def str_to_data(value: str) -> Data | None:
    # Format specification:
    # The argument can take various forms, including nested structures defined
    # by JSON documents. The format is as follows:
    #
    #   - <type> ':' <value>
    #
    # Whereby the type is one of the following:
    #   - str       <-> VisibleString
    #   - int       <-> Integer
    #   - float     <-> FloatingPoint
    #   - uint      <-> Unsigned
    #   - bool      <-> BOOLEAN
    #   - bits      <-> BIT STRING
    #   - oid       <-> ObjectIdentifier
    #   - mms-str   <-> MMSString
    #   - bytes     <-> OCTET STRING
    #
    # TODO: array and structure types are represented through JSON structures.
    if ":" not in value:
        logging.error(f"Invalid value format: {value!r} - expected <type>:<value>")
        return None

    type_, value = shlex.split(value)[0].split(":", 1)
    path = pathlib.Path(value)
    match type_:
        case "str":
            return Data(visible_string=value)
        case "int":
            return Data(integer=int(value))
        case "float":
            return Data(floating_point=create_floating_point_value(float(value)))
        case "uint":
            return Data(unsigned=int(value))
        case "bool":
            return Data(boolean=bool(value))
        case "bits":
            if path.is_file():
                return Data(bit_string=path.read_bytes())

            return Data(bit_string=bytes.fromhex(value))
        case "oid":
            return Data(objId=value)
        case "mms-str":
            return Data(mMSString=value)
        case "bytes":
            if path.is_file():
                return Data(octet_string=path.read_bytes())

            return Data(octet_string=bytes.fromhex(value))
        case _:
            logging.error(f"Invalid value type: {type_!r}")
            return None


def do_identify(args, conn: MMS_Connection) -> None:
    logging.info("Requesting identity information...")
    name, model, revision = conn.identify()
    print(f"Vendor: {name}")
    print(f"Model: {model}")
    print(f"Revision: {revision}")


def do_domain(args, conn: MMS_Connection) -> None:
    target_domain = args.list
    if target_domain is None:
        # just request all available domains
        logging.info("Requesting all domain names...")
        object_class = basic_object_class(ObjectClass.basicObjectClass_VALUES.V_domain)
        domains = conn.get_name_list(object_class)

        logging.info(f"Found {len(domains)} Domain(s):")
        return print(*domains, sep="\n")

    # request all variables of a domain
    scope = ObjectScope(domainSpecific=args.list)
    object_class = basic_object_class(
        ObjectClass.basicObjectClass_VALUES.V_namedVariable
    )
    variables = conn.get_name_list(object_class, scope)
    logging.info(f"Found {len(variables)} Variable(s):")
    print(*variables, sep="\n")


def do_variable(args, conn: MMS_Connection):
    if args.var_read:
        # try to read a variable
        if not args.var_target:
            return logging.error("No variable target specified")

        targets = parse_variable_target(args.var_target, args.domain)
        if not targets:
            sys.exit(1)

        logging.debug("Preparing to read  %d variable(s)...", len(targets))
        # 1. build access specification
        access_spec = []
        for object_name in targets:
            access = VariableAccessItem()
            access.variableSpecification.name = object_name
            access_spec.append(access)

        logging.info("Reading %d variable(s) from peer...", len(targets))
        with args.console.status("Awaiting access results..."):
            results = conn.read_variables(*access_spec)

        table = Table(safe_box=True, expand=False, box=box.ASCII_DOUBLE_HEAD)
        table.add_column("Variable", justify="left")
        table.add_column("Value", justify="left")
        for object_name, result in zip(targets, results):
            item = object_name_to_string(object_name).replace("$", ".")
            if result.failure:
                error_code = result.failure.value
                error_msg = f"[red]({error_code})[/]"
                if hasattr(error_code, "name"):
                    error_msg = f"[red bold]{error_code.name[2:]}[/] {error_msg}"
                else:
                    error_msg = f"[red]Error during read op[/] {error_msg}"
                table.add_row(item, error_msg)
            else:
                value = data_to_str(result.success)
                if not isinstance(value, str):
                    value = pretty.pretty_repr(value)

                table.add_row(item, value, end_section=True)

        args.console.print(table)

    elif args.var_write:
        if not args.var_target:
            return logging.error("No variable target specified")

        if not args.var_value:
            return logging.error("No variable value specified")

        targets = parse_variable_target(args.var_target, args.domain)
        if not targets:
            sys.exit(1)

        if len(targets) > 1:
            logging.warning("Only one variable can be written at a time")

        item_name_safe = object_name_to_string(targets[0])
        logging.debug("Preparing to write %s...", item_name_safe)
        access = VariableAccessItem()
        access.variableSpecification.name = targets[0]
        data = str_to_data(args.var_value)
        if data is None:
            sys.exit(1)

        write_result = conn.write_variable(access, data)
        if write_result is None:
            logging.info("Write operation succeeded")
        else:
            logging.error(
                "Failed to write variable %s: [bold red]%s[/] [red](%d)[/]",
                item_name_safe.replace("$", "."),
                DataAccessError.VALUES(write_result.value).name[2:],
                write_result.value,
            )

    elif args.var_query:
        if not args.var_target:
            return logging.error("No variable target specified")

        targets = parse_variable_target(args.var_target, args.domain)
        if not targets:
            sys.exit(1)

        if len(targets) > 1:
            logging.warning("Only one variable can be queried at a time")

        item_name_safe = object_name_to_string(targets[0]).replace("$", ".")
        logging.debug("Querying %s...", item_name_safe)
        result = conn.variable_attributes(name=targets[0])
        logging.info("Query result:")

        args.console.print(f"- [bold]Name:[/] {item_name_safe}")
        args.console.print(f"- [bold]Deletable:[/] {result.mmsDeletable}")
        if result.address:
            args.console.print(
                f"- [bold]Address:[/] {result.address.to_text().decode()}"
            )
        if result.accessControlList:
            args.console.print(f"- [bold]ACL:[/] {result.accessControlList.value!r}")
        if result.meaning:
            args.console.print(f"- [bold]Meaning:[/] {result.meaning}")

        type_descr = result.typeDescription
        if type_descr.present in (
            TypeDescription.PRESENT.PR_structure,
            TypeDescription.PRESENT.PR_array,
        ):
            args.console.print(f"- [bold]Type:[/] {type_descr.to_text().decode()}")
        else:
            args.console.print(f"- [bold]Type:[/] {type_descr.present.name[3:]}")


def cli_main():
    import argparse

    from rich.console import Console
    from icspacket import __version__
    from icspacket.core import logger

    EPILOG = """\
    Examples:
        mms_utility.py id <host>
        mms_utility.py domain --list <host>
        mms_utility.py domain --list <domain> <host>
        mms_utility.py var --read <domain>/<var> <host>
        mms_utility.py var --write <domain>/<var> --value <type>:<value> <host>
    """

    parser = argparse.ArgumentParser(
        description="MMS utility for ISO 9506/ACSE operations",
        epilog=textwrap.dedent(EPILOG),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # fmt: off
    # ------------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------------
    services = parser.add_subparsers(title="Services", description="Available MMS service operations", metavar="SERVICE")

    identify = services.add_parser("identify", aliases=["id"], help="Retrieve identifying information from the target MMS server")
    identify.set_defaults(func=do_identify)

    domain = services.add_parser("domain", aliases=["d"], help="List domain names or objects within a domain")
    domain.set_defaults(func=do_domain)
    domain.add_argument("--list", type=str, nargs="?", help="Specify the domain name or filter to list objects within")

    variable = services.add_parser("var", aliases=["v"], help="Perform operations on MMS variables (read, write, query)")
    variable.set_defaults(func=do_variable)
    variable.add_argument("-D", "--domain", type=str, required=False, help="Global domain to use if variable targets do not include a domain")

    op_group = variable.add_argument_group("Operations", "Specify exactly one operation")
    op_group_mutex = op_group.add_mutually_exclusive_group(required=True)
    op_group_mutex.add_argument("-r", "--read", action="store_true", dest="var_read", help="Read the specified variable(s) from the target MMS server")
    op_group_mutex.add_argument("-w", "--write", action="store_true", dest="var_write", help="Write a value to the specified variable(s)")
    op_group_mutex.add_argument("-q", "--query", action="store_true", dest="var_query", help="Query attributes or metadata of the specified variable(s)")

    value_group = variable.add_argument_group("Variable Value Options", "Specify values to write using the '<type>:<value>' format")
    value_group.add_argument("--value", type=str, metavar="<type>:<value>", dest="var_value", help="Value to write to variable(s). See epilog for type specifications")
    variable.add_argument("var_target", nargs="*", type=str, help="Target variable(s), either '<domain>/<variable>' or '<variable>' if using --domain for domain variables, "
        + "vmd:<variable for VMD specific and aa:<variable> for AA-specific variables; or just a path to a file")
    variable.formatter_class = argparse.RawDescriptionHelpFormatter
    variable.epilog = textwrap.dedent("""\
    Variable Value Format:

    Many operations allow setting or writing variable values. These values
    are specified in the form:

        <type>:<value>

    Where <type> indicates the MMS data type, and <value> is the corresponding
    value in string representation.

    Supported types:

    - str       -> VisibleString
    - int       -> Integer
    - float     -> FloatingPoint
    - uint      -> Unsigned integer
    - bool      -> BOOLEAN (True/False)
    - bits      -> BIT STRING (e.g., '1010')
    - oid       -> ObjectIdentifier (e.g., '1.3.6.1.4')
    - mms-str   -> MMSString
    - bytes     -> OCTET STRING (hex or raw bytes)

    !! Complex types (arrays, structures) are not supported yet !!

    Example value definitions:
        --value str:"Hello World"
        --value int:42
        --value bool:True
        --value bits:101011
        --value bytes:0A0B0C
        --value oid:1.3.6.1.4
    """)

    add_mms_connection_options(parser)
    add_logging_options(parser)

    args = parser.parse_args()
    args.console = Console()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

    func = getattr(args, "func", None)
    if func is None:
        logging.error("No service selected, quitting...")
        sys.exit(1)

    conn = init_mms_connection(
        args.host,
        args.port,
        args.auth,
        args.auth_stdin,
        args.timeout,
        args.max_tpdu_size,
    )
    if conn is None:
        sys.exit(1)

    try:
        func(args, conn)
    except MMSConnectionError as error:
        service_error = error.error
        match service_error.errorClass.present:
            case ServiceError.errorClass_TYPE.PRESENT.PR_access:
                logging.error(
                    "Access error while performing service request: [b]%s[/]",
                    service_error.errorClass.access.name[2:],
                )
            case _:
                logging.error("Failed to perform service request: %s", error)
    except KeyboardInterrupt:
        logging.error("Operation cancelled by user...")
    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)
        sys.exit(1)
    finally:
        try:
            logging.debug("Closing MMS connection...")
            conn.close()
        except ConnectionClosedError:
            logging.debug("Connection was already closed by remote peer")


if __name__ == "__main__":
    cli_main()
