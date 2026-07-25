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
import datetime
import enum

from typing_extensions import Any, override

from icspacket.proto.iec61850.classes import ControlModel
from icspacket.proto.iec61850.path import ObjectReference
from icspacket.proto.mms._mms import Data, TypeDescription
from icspacket.proto.mms.data import Timestamp, from_dict


class ControlError(enum.IntEnum):
    """
    Outcome code the client decodes from the ``error`` field of a
    ``LastApplError`` diagnostic for an IEC 61850 control request.

    Together with a :class:`Cause`, this tells the caller in what way a
    control request or response failed.

    .. versionadded:: 0.2.4
    """

    NO_ERROR = 0
    """Indicates the control command completed without error."""
    UNKNOWN = 1
    """Indicates the failure reason could not be classified further."""
    TIMEOUT = 2
    """Indicates the control operation did not complete in time."""
    OPERATOR_TEST_FAIL = 3
    """Indicates the control operation failed while running as an operator test."""


class Cause(enum.IntEnum):
    """
    Fine-grained reason the client decodes from the ``cause`` field of a
    ``LastApplError`` diagnostic, alongside a :class:`ControlError`.

    .. versionadded:: 0.2.4
    """

    Unknown = 0
    Not_supported = 1
    Blocked_by_switching_hierarchy = 2
    Select_failed = 3
    Invalid_position = 4
    Position_reached = 5
    Parameter_change_in_execution = 6
    Step_limit = 7
    Blocked_by_Mode = 8
    Blocked_by_process = 9
    Blocked_by_interlocking = 10
    Blocked_by_synchrocheck = 11
    Command_already_in_execution = 12
    Blocked_by_health = 13
    One_of_n_control = 14
    Abortion_by_cancel = 15
    Time_limit_over = 16
    Abortion_by_trip = 17
    Object_not_selected = 18
    Object_already_selected = 19
    No_access_authority = 20
    Ended_with_overshoot = 21
    Abortion_due_to_deviation = 22
    Abortion_by_communication_loss = 23
    Blocked_by_command = 24
    NONE = 25
    Inconsistent_parameters = 26
    Locked_by_other_client = 27


class LastApplError(ConnectionError):
    """
    Exception representing the *LastApplError* diagnostic
    from IEC 61850 control services.

    Raised when a control service returns an error response
    containing both a control error and a cause.

    .. versionadded:: 0.2.4

    :param str ctrl_obj:
        The control object reference string.
    :param ControlError error:
        The control error category.
    :param int ctlnum:
        The control number associated with the request.
    :param Cause cause:
        Detailed cause of the error.
    """

    def __init__(
        self,
        ctrl_obj: str,
        error: ControlError,
        ctlnum: int,
        cause: Cause,
        *args: object,
    ) -> None:
        super().__init__(*args)
        self.ctrl_obj: str = ctrl_obj
        self.error: ControlError = error
        self.ctlnum: int = ctlnum
        self.cause: Cause = cause


class ControlObject:
    """
    Represents an IEC 61850 control object reference.

    Provides access to control object properties, origin parameters,
    and the ability to generate operate data structures for issuing
    control commands.

    Implements context manager protocol for safe usage in
    connection-based operations.

    .. versionadded:: 0.2.4

    :param ref: The object reference for the control point.
    :type ref: ObjectReference
    :param spec: ASN.1 type description of the control object.
    :type spec: TypeDescription
    :param model: Control model (e.g., ``DIRECT_NORMAL`` or ``SBO_ENHANCED``).
    :type model: ControlModel
    """

    origin_cat: int
    """Numeric code for the source category, sent to the server as part of
    the origin block."""
    origin_ident: bytes | None
    """Byte-string naming or identifying the initiating client/system, sent
    together with ``origin_cat``."""
    ctl_num: int
    """Running counter that tracks SBO and direct control operations;
    advanced automatically for direct-operate models."""

    test: bool
    """Marks whether the server should treat this command as a test rather
    than a normal operation."""
    interlock_check: bool
    """Controls whether the interlock check is applied when the command
    executes."""
    synchro_check: bool
    """Controls whether the synchrocheck condition is applied when the
    command executes."""

    def __init__(
        self, ref: ObjectReference, spec: TypeDescription, model: ControlModel
    ) -> None:
        # what we need is:
        # - CO_CtrlObjectRef
        #
        self.__ref = ref
        self.__model = model
        self.__type = spec

        self.__oper_tm = False
        self.__ctl_num = False
        self.__ctl_val_type = None

        oper = self._get_item(spec, "Oper")
        if oper is not None:
            oper_spec = oper.componentType.typeDescription
            self.__ctl_val_type = self._get_item(oper_spec, "ctlVal")
            self.__oper_tm = self._has_item(oper_spec, "operTm")
            self.__ctl_num = self._has_item(oper_spec, "ctlNum")

        self.origin_cat = 0
        self.origin_ident = bytes()
        self.ctl_num = 0
        self.test = False
        self.interlock_check = False
        self.synchro_check = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @override
    def __repr__(self) -> str:
        """Return a human-readable string for debugging."""
        type_name = self.__ctl_val_type.componentType.typeDescription.present.name[3:]
        return f"<ControlObject model={self.__model.name} ref={self.__ref!r} ctlVal_Type={type_name}>"

    @property
    def ctrl_object_ref(self) -> ObjectReference:
        """Reference to the underlying control object node."""
        return self.__ref

    @property
    def has_time_activated_oper(self) -> bool:
        """Whether this control object supports time-activated operate requests."""
        return self.__oper_tm

    @property
    def has_ctl_num(self) -> bool:
        """Whether this control object includes a control number field."""
        return self.__ctl_num

    @property
    def model(self) -> ControlModel:
        """Return the configured control model for this object."""
        return self.__model

    @property
    def ctl_val_type(self) -> str | None:
        """
        Return the ASN.1 *Data* CHOICE alternative name expected for
        ``ctlVal`` (e.g. ``"boolean"``, ``"integer"``, ``"visible_string"``),
        or ``None`` if the control object has no ``Oper.ctlVal`` attribute.
        """
        if self.__ctl_val_type is None:
            return None
        return self.__ctl_val_type.componentType.typeDescription.present.name[3:]

    def origin(self) -> list[dict[str, int | bytes]]:
        """
        Build the *origin* structure according to IEC 61850-7-2, used by
        :meth:`get_operate_data` when assembling a control request.

        :return: Origin information consisting of category and identifier.
        :rtype: list[dict[str, int | bytes]]
        """
        return [
            {"integer": self.origin_cat},
            {"octet_string": self.origin_ident or bytes()},
        ]

    def get_operate_data(
        self, ctl_val: Any, oper_time: Timestamp | None = None, check=True
    ) -> Data:
        """
        Assemble the MMS ``Data`` payload written to a control object's
        ``Oper`` attribute to carry out an operate request.

        The value supplied in ``ctl_val`` is combined with a fresh ``T``
        timestamp and the ``origin`` block; depending on this control
        object's capabilities and the ``check`` flag, ``operTm``, ``ctlNum``,
        ``Test``, and/or ``Check`` are folded in as well.

        :param ctl_val: The control value to apply.
        :type ctl_val: Any
        :param oper_time: Optional timestamp for time-activated control.
        :type oper_time: Timestamp | None
        :param check: Whether to include interlock and synchrocheck parameters.
        :type check: bool
        :return: ASN.1 encoded :class:`Data` structure for the operate request.
        :rtype: Data
        """
        items = [
            {
                # ctlVal = <CO_CtrlObjectRef>$Oper$ctlVal
                self.__ctl_val_type.componentType.typeDescription.present.name[
                    3:
                ]: ctl_val,
            }
        ]
        if self.has_time_activated_oper:
            ts = oper_time or bytes(8)
            # operTm = <CO_CtrlObjectRef>$Oper$operTm
            items.append({"utc_time": bytes(ts)})

        # origin = <CO_CtrlObjectRef>$Oper$origin
        items.append({"structure": self.origin()})

        if self.model not in (ControlModel.SBO_NORMAL, ControlModel.SBO_ENHANCED):
            self.ctl_num += 1

        # ctlNum = <CO_CtrlObjectRef>$Oper$ctlNum
        if self.has_ctl_num:
            items.append({"unsigned": self.ctl_num})

        # T = <CO_CtrlObjectRef>$Oper$T
        ts = Timestamp.from_datetime(datetime.datetime.now())
        items.append({"utc_time": bytes(ts)})
        # Test = <CO_CtrlObjectRef>$Oper$Test
        items.append({"boolean": self.test})

        if check:
            check = Data.bit_string_TYPE(1)
            check.set(0, self.interlock_check)
            check.set(1, self.synchro_check)
            # Check = <CO_CtrlObjectRef>$Oper$Check
            items.append({"bit_string": check})
        return from_dict({"structure": items})

    @property
    def T(self) -> Timestamp:
        """
        Return the current control timestamp (*T*).

        :return: Timestamp of the control request.
        :rtype: Timestamp
        """
        return Timestamp.from_datetime(datetime.datetime.now())

    # --- private ---
    def _has_item(self, spec: TypeDescription, name: str) -> bool:
        if spec.present == TypeDescription.PRESENT.PR_structure:
            fields = list(spec.structure.components)
            for field in fields:
                if field.componentName.value == name:
                    return True
        return False

    def _get_item(
        self, spec: TypeDescription, name: str
    ) -> TypeDescription.structure_TYPE.components_TYPE.Member_TYPE | None:
        if spec.present == TypeDescription.PRESENT.PR_structure:
            fields = list(spec.structure.components)
            for field in fields:
                if field.componentName.value == name:
                    return field
