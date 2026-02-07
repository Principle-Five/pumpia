from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, overload, Self
from datetime import date

from pumpia.module_handling.fields.simple import (BaseIO,
                                                  OptionIO,
                                                  BoolIO,
                                                  StringIO,
                                                  IntIO,
                                                  PercIO,
                                                  FloatIO,
                                                  DateIO)

if TYPE_CHECKING:
    from pumpia.module_handling.modules import BaseModule


class Fields:
    def __init__(self, obj: BaseModule) -> None:
        self.fields_dict: dict[str, BaseIO] = {}
        self.obj: BaseModule = obj


class _FieldsMeta:
    def __init__(self) -> None:
        self.field_types: dict[str, BaseField] = {}

    @property
    def field_names(self) -> list[str]:
        return list(self.field_types.keys())

    @overload
    def __get__(self, obj: BaseModule, owner=None) -> Fields: ...
    @overload
    def __get__(self, obj: None, owner=None) -> Self: ...

    def __get__(self, obj: BaseModule | None, owner=None) -> Fields | Self:
        if obj is None:
            return self

        try:
            return getattr(obj, "fields")
        except AttributeError:
            fields = Fields(obj)
            for name, field in self.field_types:
                setattr(fields, name, field)
            setattr(obj, "fields", fields)
            return fields


class BaseField[ValT, IOType:BaseIO](ABC):
    """
    Base class for input/output handling in modules.

    Parameters
    ----------
    initial_value : ValT or Callable[[], ValT]
        The initial value or a callable that returns the initial value.
    verbose_name : str, optional
        The verbose name of the input/output (default is None).
    label_style : str, optional
        The style of the label (default is None).
    hidden : bool, optional
        Whether the input/output is hidden (default is False).

    Attributes
    ----------
    verbose_name : str | None
    value : ValT
    label : ttk.Label
    label_var : tk.StringVar
    value_var : TkVarT
    hidden : bool

    Methods
    -------
    set_parent(parent: tk.Misc)
        Sets the parent of the input/output.
    """

    def __init__(self,
                 initial_value: ValT | Callable[[], ValT],
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False):
        self.initial_value: ValT | Callable[[], ValT] = initial_value
        self.verbose_name: str | None = verbose_name
        self.label_style: str | None = label_style
        self.entry_style: str | None = entry_style
        self.hidden: bool = hidden
        self.read_only: bool = read_only
        self.name: str = ""

    @property
    @abstractmethod
    def IO_base(self) -> type[IOType]:
        pass

    def __set_name__(self, owner: type[BaseModule], name: str):
        self.name = name
        owner.fields.field_types[name] = self

    @overload
    def __get__(self, obj: BaseModule, owner=None) -> ValT: ...
    @overload
    def __get__(self, obj: Fields, owner=None) -> IOType: ...

    def __get__(self, obj: BaseModule | Fields, owner=None) -> ValT | IOType:
        if isinstance(obj, Fields):
            try:
                field: IOType = obj.fields_dict[self.name]  # pyright: ignore[reportAssignmentType]

            except KeyError:
                field = self.IO_base(initial_value=self.initial_value,
                                     parent=obj.obj,
                                     verbose_name=self.verbose_name,
                                     label_style=self.label_style,
                                     entry_style=self.entry_style,
                                     hidden=self.hidden,
                                     read_only=self.read_only)
                obj.fields_dict[self.name] = field

            return field

        else:
            try:
                field: IOType = obj.fields.fields_dict[self.name]  # pyright: ignore[reportAssignmentType]

            except KeyError:
                field = self.IO_base(initial_value=self.initial_value,
                                     parent=obj,
                                     verbose_name=self.verbose_name,
                                     label_style=self.label_style,
                                     entry_style=self.entry_style,
                                     hidden=self.hidden,
                                     read_only=self.read_only)
                obj.fields.fields_dict[self.name] = field

            return field.value

    def __set__(self, obj: BaseModule, value: ValT):
        try:
            field: IOType = obj.fields.fields_dict[self.name]  # pyright: ignore[reportAssignmentType]

        except AttributeError:
            field = self.IO_base(initial_value=self.initial_value,
                                 parent=obj,
                                 verbose_name=self.verbose_name,
                                 label_style=self.label_style,
                                 entry_style=self.entry_style,
                                 hidden=self.hidden,
                                 read_only=self.read_only)
            obj.fields.fields_dict[self.name] = field

        field.value = value


class OptionField[DictValT](BaseField[str, OptionIO[DictValT]]):
    """
    Represents an option input.
    Has the same attributes and methods as BaseInput unless stated below.

    Parameters
    ----------
    options_map : dict[str, DictValT]
        A dictionary mapping the options in the dropdown to an object.
    initial : str or Callable[[], str]
        The initial dropdown value or a callable that returns the initial value.
    allow_inv_mapping : bool, optional
        Whether to allow inverse mapping from an object to the option (default is False).
    """

    def __init__(self,
                 options_map: dict[str, DictValT],
                 initial: str | Callable[[], str],
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 allow_inv_mapping: bool = False,
                 hidden: bool = False,
                 read_only: bool = False):
        super().__init__(initial,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only)
        self.options_map = options_map
        self.allow_inv_mapping = allow_inv_mapping

    @property
    def IO_base(self) -> type[OptionIO[DictValT]]:
        return OptionIO

    @overload
    def __get__(self, obj: BaseModule, owner=None) -> DictValT: ...
    @overload
    def __get__(self, obj: Fields, owner=None) -> OptionIO: ...

    def __get__(self, obj: BaseModule | Fields, owner=None) -> DictValT | OptionIO:
        if isinstance(obj, Fields):
            try:
                field: OptionIO[DictValT] = obj.fields_dict[self.name]  # pyright: ignore[reportAssignmentType]

            except KeyError:

                field = self.IO_base(initial=self.initial_value,
                                     options_map=self.options_map,
                                     parent=obj.obj,
                                     verbose_name=self.verbose_name,
                                     label_style=self.label_style,
                                     entry_style=self.entry_style,
                                     allow_inv_mapping=self.allow_inv_mapping,
                                     hidden=self.hidden,
                                     read_only=self.read_only)
                obj.fields_dict[self.name] = field

            return field
        else:
            try:
                field: OptionIO[DictValT] = obj.fields.fields_dict[self.name]  # pyright: ignore[reportAssignmentType]

            except KeyError:
                field = self.IO_base(initial=self.initial_value,
                                     options_map=self.options_map,
                                     parent=obj,
                                     verbose_name=self.verbose_name,
                                     label_style=self.label_style,
                                     entry_style=self.entry_style,
                                     allow_inv_mapping=self.allow_inv_mapping,
                                     hidden=self.hidden,
                                     read_only=self.read_only)
                obj.fields.fields_dict[self.name] = field

            return field.value

    def __set__(self, obj: BaseModule, value: DictValT | str):
        try:
            field: OptionIO[DictValT] = obj.fields.fields_dict[self.name]  # pyright: ignore[reportAssignmentType]

        except KeyError:
            field = self.IO_base(initial=self.initial_value,
                                 options_map=self.options_map,
                                 parent=obj,
                                 verbose_name=self.verbose_name,
                                 label_style=self.label_style,
                                 entry_style=self.entry_style,
                                 allow_inv_mapping=self.allow_inv_mapping,
                                 hidden=self.hidden,
                                 read_only=self.read_only)
            obj.fields.fields_dict[self.name] = field

        field.value = value


class BoolField(BaseField[bool, BoolIO]):
    """
    Represents a boolean input.
    Has the same attributes and methods as BaseInput unless stated below.
    """
    @property
    def IO_base(self) -> type[BoolIO]:
        return BoolIO


class StringField(BaseField[str, StringIO]):
    """
    Represents a string input.
    Has the same attributes and methods as BaseInput unless stated below.
    """
    @property
    def IO_base(self) -> type[StringIO]:
        return StringIO


class IntField(BaseField[int, IntIO]):
    """
    Represents an integer input.
    Has the same attributes and methods as BaseInput unless stated below.
    """
    @property
    def IO_base(self) -> type[IntIO]:
        return IntIO


class PercField(BaseField[float, PercIO]):
    """
    Represents a percentage input.
    Has the same attributes and methods as BaseInput unless stated below.
    """
    @property
    def IO_base(self) -> type[PercIO]:
        return PercIO


class FloatField(BaseField[float, FloatIO]):
    """
    Represents a float input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    @property
    def IO_base(self) -> type[FloatIO]:
        return FloatIO


class DateField(BaseField[date, DateIO]):
    """
    Represents a date input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    @property
    def IO_base(self) -> type[DateIO]:
        return DateIO
