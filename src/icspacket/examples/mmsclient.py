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
# pyright: reportUnusedCallResult=false, reportGeneralTypeIssues=false
import logging
import sys
import pathlib
import cmd2

from typing import Any
from rich.columns import Columns
from rich.console import Console
from typing_extensions import override

from rich import box
from rich.table import Table

from icspacket.core.connection import ConnectionClosedError
from icspacket.core import hexdump
from icspacket.proto.cotp.structs import TPDU_Size
from icspacket.proto.mms._mms import FileName, ServiceError
from icspacket.proto.mms.connection import MMS_Connection
from icspacket.proto.mms.exceptions import MMSConnectionError, MMSUnknownServiceError


from icspacket.examples.util.mms import add_mms_connection_options, init_mms_connection
from icspacket.examples.util import add_logging_options


class MMSClient(cmd2.Cmd):
    do_exit = cmd2.Cmd.do_quit

    def __init__(self, conn: MMS_Connection) -> None:
        """Interactive MMS client shell.

        This command-line shell allows interactive navigation and manipulation
        of remote MMS (Manufacturing Message Specification) file systems, as
        well as execution of basic MMS services. It is designed to mimic the
        behavior of familiar UNIX shell commands while operating against
        MMS-accessible resources.

        :param conn: Active MMS connection instance
        :type conn: MMS_Connection
        """
        super().__init__(
            allow_cli_args=False,
            allow_redirection=False,
        )
        self.__connection = conn
        self.local_dir = pathlib.Path(".").absolute()
        self.remote_dir = pathlib.Path("/")
        self.prompt = "mms> "
        # disable default commands
        del [
            cmd2.Cmd.do_alias,
            cmd2.Cmd.do_edit,
            cmd2.Cmd.do_macro,
            cmd2.Cmd.do_py,
            cmd2.Cmd.do_run_pyscript,
            cmd2.Cmd.do_run_script,
            cmd2.Cmd.do_set,
            cmd2.Cmd.do_shell,
            cmd2.Cmd.do_shortcuts,
        ]
        self.remove_settable("debug")

    @property
    def conn(self) -> MMS_Connection:
        """Return the underlying MMS connection object."""
        return self.__connection

    def do_id(self, _) -> None:
        """id

        Display the remote MMS server identity.

        This command sends an MMS Identify request and prints the
        response, including vendor, model, and revision information.
        """
        name, model, revision = self.conn.identify()
        self.poutput(f"Vendor: {name}")
        self.poutput(f"Model: {model}")
        self.poutput(f"Revision: {revision}")

    def do_ldir(self, arg) -> None:
        """ldir [newdir]

        List the currently used *local* directory or specify a new one
        """
        if arg:
            self.local_dir = pathlib.Path(arg).absolute().resolve()
        else:
            self.poutput(str(self.local_dir))

    def do_rdir(self, arg) -> None:
        """rdir [newdir]

        List the currently used *remote* directory or specify a new one
        """
        if arg:
            if arg.startswith("/"):
                self.remote_dir = pathlib.Path(arg).resolve()
            else:
                self.remote_dir = pathlib.Path(arg).absolute().resolve()
        else:
            self.poutput(str(self.remote_dir))

    def do_cd(self, arg) -> None:
        """cd newdir

        Change the current remote MMS working directory.

        This affects subsequent relative path operations, such as
        ls, get, rename, and del.
        """
        self.remote_dir = (self.remote_dir / arg).absolute().resolve()
        logging.info("Changed remote directory to '%s'", self.remote_dir)

    def _handle_file_service_error(
        self, exc: Exception, service_error: ServiceError, msg: str
    ):
        if (
            service_error.errorClass.present
            != ServiceError.errorClass_TYPE.PRESENT.PR_file
        ):
            logging.exception("Could not open file", exc)
        else:
            code = service_error.errorClass.file
            logging.error(
                "%s: [bold red]%s[/] [red](%s)[/]",
                msg,
                code.name[2:],
                code.value,
            )

    ls_parser = cmd2.Cmd2ArgumentParser()
    ls_parser.add_argument(
        "-l",
        action="store_true",
        dest="print_list",
        help="Print output as a list (table) instead of filenames only",
    )
    ls_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="List all files, including ones in subdirectories",
    )
    ls_parser.add_argument(
        "directory",
        type=str,
        nargs="?",
        help="Remote directory to list (defaults to current remote directory)",
    )

    @cmd2.with_argparser(ls_parser)
    def do_ls(self, args) -> None:
        """List the contents of a remote MMS directory."""
        directory = args.directory
        remote_dir = self.remote_dir
        if directory:
            remote_dir /= directory

        name = FileName([str(remote_dir)])
        try:
            if str(remote_dir) == "/":
                # show root dir
                name = None

            entries = self.conn.list_directory(name)

        except MMSConnectionError as error:
            service_error = error.error
            self._handle_file_service_error(
                error, service_error, f"Could not list directory {str(remote_dir)!r}"
            )
        else:
            console = Console()
            if args.print_list:
                table = Table(
                    title=f"Information of {remote_dir}",
                    safe_box=True,
                    expand=False,
                    box=box.ASCII_DOUBLE_HEAD,
                )
                table.add_column("Name", justify="left", style="bold")
                table.add_column("Size", justify="left")
                table.add_column("Last Modified", justify="right")
                for entry in entries:
                    raw_path = "".join(list(entry.fileName))
                    path = pathlib.Path(raw_path.removeprefix(str(remote_dir) + "/"))
                    # TODO: parse time
                    table.add_row(
                        str(path), str(entry.fileAttributes.sizeOfFile), "N/A"
                    )
                console.print(table)
            else:
                files = []
                for entry in entries:
                    raw_path = "".join(list(entry.fileName))
                    path = pathlib.Path(raw_path.removeprefix(str(remote_dir) + "/"))
                    if len(path.parts) == 1:
                        # simple file
                        files.append(str(path))
                    else:
                        # make sure we should display the file
                        if args.all:
                            files.append(f"[bold]{path.parent}[/]/{path.name}")
                        else:
                            files.append(f"[bold]{path.parts[0]}[/]")
                columns = Columns(files, column_first=True, equal=True, padding=(0, 4))
                console.print(columns)

    # fmt: off
    get_parser = cmd2.Cmd2ArgumentParser(add_help=True)
    get_parser.add_argument("remote_name", type=str, help="Remote file name")
    get_parser.add_argument("local_name", type=str, nargs="?", help="Optional local file name to store the file under; defaults to the remote file name")
    get_parser.add_argument("--stdout", action="store_true", help="Write file contents to stdout (hex) instead of saving locally")
    get_parser.add_argument("--unsafe", action="store_true", help="Write file contents as text to stdout",)
    # fmt: on

    @cmd2.with_argparser(get_parser)
    def do_get(self, args) -> None:
        """Retrieve a file from the remote MMS server.

        Supports saving to a local file or streaming to standard output.
        """
        console = Console()
        remote_file_path = self.remote_dir / args.remote_name
        remote_file_name = FileName([str(remote_file_path)])
        if not args.local_name:
            local_file_path = self.local_dir / remote_file_path.name
        else:
            local_file_path = pathlib.Path(args.local_name)

        logging.debug("Saving to '%s'", local_file_path)
        try:
            logging.debug("Opening '%s'", remote_file_path)
            handle = self.conn.file_open(remote_file_name)
            logging.info(
                "Downloading %s (%d bytes)...",
                remote_file_path.name,
                handle.attributes.sizeOfFile.value,
            )
            with console.status("Retrieving file..."):
                data = self.conn.file_read(handle)
                self.conn.file_close(handle)

            if args.stdout:
                if args.unsafe:
                    self.poutput(data.decode(errors="replace"))
                else:
                    self.poutput(hexdump.hexdump(data))
            else:
                with local_file_path.open("wb") as local_fp:
                    local_fp.write(data)

        except MMSConnectionError as error:
            service_error = error.error
            self._handle_file_service_error(
                error, service_error, f"Could not get file {str(remote_file_path)!r}"
            )

    rename_parser = cmd2.Cmd2ArgumentParser()
    rename_parser.add_argument("old_name", type=str, help="Remote old file name")
    rename_parser.add_argument("new_name", type=str, help="Remote new file name")

    @cmd2.with_argparser(rename_parser)
    def do_rename(self, args) -> None:
        """Rename a file in the remote MMS server."""
        remote_file_path = self.remote_dir / args.old_name
        remote_file_name = FileName([str(remote_file_path)])
        new_remote_file_path = self.remote_dir / args.new_name
        new_remote_file_name = FileName([str(new_remote_file_path)])
        logging.info("Renaming '%s' to '%s'", remote_file_path, new_remote_file_path)
        try:
            self.conn.file_rename(remote_file_name, new_remote_file_name)
        except MMSConnectionError as error:
            service_error = error.error
            self._handle_file_service_error(
                error, service_error, f"Could not rename file {str(remote_file_path)!r}"
            )

    del_parser = cmd2.Cmd2ArgumentParser()
    del_parser.add_argument("remote_name", type=str, help="Remote file name to delete")

    @cmd2.with_argparser(del_parser)
    def do_del(self, args) -> None:
        """Delete a file from the remote MMS server."""
        remote_file_path = self.remote_dir / args.remote_name
        remote_file_name = FileName([str(remote_file_path)])
        logging.info("Deleting '%s'", remote_file_path)
        try:
            self.conn.file_delete(remote_file_name)
        except MMSConnectionError as error:
            service_error = error.error
            self._handle_file_service_error(
                error, service_error, f"Could not delete file {str(remote_file_path)!r}"
            )

    @override
    def pexcept(self, msg: Any, *, end: str = "\n", apply_style: bool = True) -> None:
        match msg:
            case MMSUnknownServiceError():
                return logging.error(str(msg))
            case ConnectionClosedError():
                return logging.warning(str(msg))

        return super().pexcept(msg, end=end, apply_style=apply_style)


def cli_main():
    import argparse

    from rich.console import Console
    from icspacket import __version__
    from icspacket.core import logger

    parser = argparse.ArgumentParser(
        usage="%(prog)s [options] host [command [args...]]",
    )
    add_mms_connection_options(parser)
    add_logging_options(parser)

    args, remaining = parser.parse_known_args()
    args.console = Console()

    logger.init_from_args(args.verbosity, args.quiet, args.ts)
    if args.verbosity > 0:
        print(f"icspacket v{__version__}\n")

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

    client = MMSClient(conn)
    try:
        if remaining:
            client.onecmd_plus_hooks(" ".join(remaining))

        if not remaining or args.interactive:
            client.cmdloop()
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
