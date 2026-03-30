"""
Contains simple fields.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, overload, Self, Literal
from datetime import date
import tkinter as tk
from tkinter import ttk

from pumpia.module_handling.fields.values import (BaseValue,
                                                  BoolValue,
                                                  StringValue,
                                                  IntValue,
                                                  FloatValue,
                                                  DateValue)
from pumpia.widgets.entry_boxes import IntEntry, FloatEntry, DateEntry, PercEntry, DateVar

if TYPE_CHECKING:
    from pumpia.module_handling.modules import BaseModule


class _Fields:
    def __init__(self, module: BaseModule) -> None:
        self.fields_dict: dict[str, BaseField] = {}
        self.module: BaseModule = module

    def __iter__(self):
        for field in self.fields_dict.values():
            yield field

    def __getitem__(self, key: str):
        return self.fields_dict[key]

    @overload
    def __getattr__(self, name: Literal["module"]) -> BaseModule: ...
    @overload
    def __getattr__(self, name: Literal["fields_dict"]) -> dict[str, BaseField]: ...
    @overload
    def __getattr__(self, name: str) -> BaseField: ...

    def __getattr__(self, name: str) -> BaseModule | BaseField | dict[str, BaseField]:
        if name == "module":
            return self.module
        elif name == "fields_dict":
            return self.fields_dict
        else:
            return self.fields_dict[name]


class _FieldsMeta:
    def __init__(self) -> None:
        self.field_types: dict[str, BaseField] = {}
        self.name: str = ""
        self.private_name: str = "_"
        self.base_owner: type[BaseModule] | None = None

    @property
    def field_names(self) -> list[str]:
        """
        The names of the fields for the module.

        Returns
        -------
        list[str]
        """
        return list(self.field_types.keys())

    def __set_name__(self, owner: type[BaseModule], name: str):
        self.name = name
        self.private_name = "_" + name
        self.base_owner = owner

    @overload
    def __get__(self, obj: BaseModule, owner: type[BaseModule]) -> _Fields: ...
    @overload
    def __get__(self, obj: None, owner: type[BaseModule]) -> Self: ...

    def __get__(self, obj: BaseModule | None, owner: type[BaseModule]) -> _Fields | Self:
        if obj is None:
            if owner is self.base_owner:
                return self
            else:
                meta_obj = type(self)()
                meta_obj.name = self.name
                meta_obj.private_name = self.private_name
                meta_obj.base_owner = owner
                setattr(owner, self.name, meta_obj)
                return meta_obj

        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            fields = _Fields(obj)
            setattr(obj, self.private_name, fields)
            return fields


class BaseField[ValT, TkVarT:tk.Variable](ABC):
    """
    Base class for fields in modules.

    Parameters
    ----------
    initial_value : ValT or Callable[[], ValT]
        The initial value or a callable that returns the initial value.
    parent : tk.Misc, optional
        The parent widget (default is None).
    verbose_name : str, optional
        The verbose name of the field (default is None).
    label_style : str, optional
        The ttk style of the labels linked to this field (default is None).
    entry_style : str, optional
        The ttk style of the entries linked to this field (default is None).
    hidden : bool, optional
        Whether the field is hidden in the user interface (default is False).
    read_only : bool, optional
        Whether the field is read only in the user interface (default is False).
    reset_on_analysis : bool, optional
        Whether the field is set to the initial value prior to analysis for a module
        (default is False).

    Attributes
    ----------
    verbose_name : str | None
    value : ValT
    label : ttk.Label
    label_var : tk.StringVar
    value_var : TkVarT
    hidden : bool
    parent : tk.Misc | None
    """

    def __init__(self,
                 initial_value: ValT | Callable[[], ValT],
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False,
                 reset_on_analysis: bool = False):
        self._name: str | None = verbose_name
        self._label_style: str | None = label_style

        self._parent: tk.Misc | None = parent
        self._labels: list[ttk.Label] = []
        self._entries: list[ttk.Entry] = []
        self._label_var: tk.StringVar | None = None
        self.hidden: bool = hidden
        self._initial_value: ValT | Callable[[], ValT] = initial_value
        self._value: BaseValue[ValT, TkVarT] | None = None

        self.read_only: bool = read_only
        self._entry_style: str | None = entry_style

        self.reset_on_analysis: bool = reset_on_analysis

        self.name: str = ""
        self.module: BaseModule | None = None

    def __set_name__(self, owner: type[BaseModule], name: str):
        self.name = name
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()
        owner.fields.field_types[name] = self

    @overload
    def __get__(self, obj: BaseModule, owner=None) -> ValT: ...
    @overload
    def __get__(self, obj: None, owner=None) -> Self: ...

    def __get__(self, obj: BaseModule | None, owner=None) -> ValT | Self:
        if obj is None:
            return self

        try:
            return obj.fields.fields_dict[self.name].value

        except KeyError:
            field = type(self)(initial_value=self.initial_value,
                               parent=None,
                               verbose_name=self.verbose_name,
                               label_style=self._label_style,
                               entry_style=self._entry_style,
                               hidden=self.hidden,
                               read_only=self.read_only,
                               reset_on_analysis=self.reset_on_analysis)
            field.name = self.name
            field.module = obj
            obj.fields.fields_dict[self.name] = field
            return field.initial_value
        except AttributeError:
            return self

    def __set__(self, obj: BaseModule, value: ValT):
        try:
            field = obj.fields.fields_dict[self.name]

        except KeyError:
            field = type(self)(initial_value=self.initial_value,
                               parent=None,
                               verbose_name=self.verbose_name,
                               label_style=self._label_style,
                               entry_style=self._entry_style,
                               hidden=self.hidden,
                               read_only=self.read_only,
                               reset_on_analysis=self.reset_on_analysis)
            field.name = self.name
            field.module = obj
            obj.fields.fields_dict[self.name] = field

        field.value = value

    @property
    def widget(self) -> type[ttk.Entry]:
        """
        The tkinter widget used for entries.

        Returns
        -------
        type[ttk.Entry]
        """
        return ttk.Entry

    @property
    @abstractmethod
    def value_type(self) -> type[BaseValue[ValT, TkVarT]]:
        """
        The pumpia value type used for this field.

        Returns
        -------
        type[BaseValue[ValT, TkVarT]]
        """

    @property
    def verbose_name(self) -> str | None:
        """
        The verbose name of the field.
        """
        return self._name

    @verbose_name.setter
    def verbose_name(self, val: str):
        self._name = val
        if self._label_var is not None:
            self._label_var.set(val)

    @property
    def parent(self) -> tk.Misc | None:
        """
        The parent of the field.
        Can only be set once.
        """
        return self._parent

    @parent.setter
    def parent(self, value: tk.Misc):
        if self._parent is None:
            self._parent = value
        else:
            raise ValueError("Parent already set")

    @property
    def value_store(self) -> BaseValue[ValT, TkVarT]:
        """
        The pumpia value used to store the value for this field.
        Values can shared between fields
        by setting the value store for one field to be the value of another field.
        e.g. `field1.value = field2.value_store`

        Returns
        -------
        BaseValue[ValT, TkVarT]

        Raises
        ------
        ValueError
            If the field parent has not been set
        """
        if self._value is None:
            if self._parent is None:
                raise ValueError("Parent has not been set")
            self._value = self.value_type(self._parent, self.initial_value)
        return self._value

    @property
    def value_var(self) -> TkVarT:
        """
        The tkinter variable used for the entry widgets.
        """
        return self.value_store.var

    @property
    def value(self) -> ValT:
        """
        The value of the field.
        """
        if self.value_store.error:
            raise ValueError(f"Error in value of {self.verbose_name}")
        return self.value_store.value

    @value.setter
    def value(self, val: ValT | BaseValue[ValT, TkVarT]):
        if isinstance(val, BaseValue):
            self._value = val
            self._value_var_setter()
        else:
            self.value_store.value = val

    @property
    def initial_value(self) -> ValT:
        """
        The initial value of the IO.
        """
        if callable(self._initial_value):
            return self._initial_value()  # type: ignore
        else:
            return self._initial_value

    def new_label(self, parent: tk.Misc) -> ttk.Label:
        """
        Returns a label linked to this field, with text of `verbose_name`.
        This is placed in `parent`, this is not the fields parent.

        Parameters
        ----------
        parent : tk.Misc

        Returns
        -------
        ttk.Label
        """
        var = self.label_var
        if self._label_style is None:
            label = ttk.Label(parent, textvariable=var)
        else:
            label = ttk.Label(parent, style=self._label_style, textvariable=var)
        self._labels.append(label)
        return label

    @property
    def label_var(self) -> tk.StringVar:
        """
        The tkinter variable linked to labels for this field.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
        if self.verbose_name is None:
            raise ValueError("verbose_name has not been set")
        if self._label_var is None:
            self._label_var = tk.StringVar(self._parent, value=self.verbose_name)
        return self._label_var

    def reset_value(self):
        """
        Resets the field to the initial value.
        """
        self.value = self.initial_value

    def new_entry(self, parent: tk.Misc) -> ttk.Entry:
        """
        Returns an entry linked to this field.
        This is placed in `parent`, this is not the fields parent.

        Parameters
        ----------
        parent : tk.Misc

        Returns
        -------
        ttk.Entry
        """
        var = self.value_store.var
        if self.read_only:
            state = "readonly"
        else:
            state = "normal"
        if self._entry_style is None:
            entry = self.widget(parent, textvariable=var, state=state)
        else:
            entry = self.widget(parent, textvariable=var, state=state, style=self._entry_style)
        self._entries.append(entry)
        return entry

    def _value_var_setter(self):
        for entry in self._entries:
            entry.configure(textvariable=self.value_var)


class OptionField[DictValT](BaseField[str, tk.StringVar]):
    """
    Represents an option field.
    Has the same attributes and methods as BaseField unless stated below.

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
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 allow_inv_mapping: bool = False,
                 hidden: bool = False,
                 read_only: bool = False,
                 reset_on_analysis: bool = False):
        super().__init__(initial_value=initial,
                         parent=parent,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only,
                         reset_on_analysis=reset_on_analysis)

        self._entries: list[ttk.Combobox] = []

        self.allow_inv_mapping: bool = allow_inv_mapping
        self.options_map: dict[str, DictValT] = options_map

        if self.allow_inv_mapping:
            self._inv_map: dict[DictValT, str] = {v: k for k, v in self.options_map.items()}

        self.options = list(self.options_map.keys())
        if initial not in self.options:
            raise ValueError("initial not in options")

    @overload
    def __get__(self, obj: BaseModule, owner=None) -> DictValT: ...
    @overload
    def __get__(self, obj: None, owner=None) -> Self: ...

    def __get__(self, obj: BaseModule | None, owner=None) -> DictValT | Self:
        if obj is None:
            return self

        try:
            field = obj.fields.fields_dict[self.name]  # pyright: ignore[reportAssignmentType]
            return field.value
        except KeyError:
            field = type(self)(initial=self.initial_value,
                               options_map=self.options_map,
                               parent=None,
                               verbose_name=self.verbose_name,
                               label_style=self._label_style,
                               entry_style=self._entry_style,
                               allow_inv_mapping=self.allow_inv_mapping,
                               hidden=self.hidden,
                               read_only=self.read_only,
                               reset_on_analysis=self.reset_on_analysis)
            obj.fields.fields_dict[self.name] = field
            field.name = self.name
            field.module = obj
            return self.options_map[field.initial_value]
        except AttributeError:
            return self

    def __set__(self, obj: BaseModule, value: DictValT | str):
        try:
            field: Self = obj.fields.fields_dict[self.name]  # pyright: ignore[reportAssignmentType]

        except KeyError:
            field = type(self)(initial=self.initial_value,
                               options_map=self.options_map,
                               parent=None,
                               verbose_name=self.verbose_name,
                               label_style=self._label_style,
                               entry_style=self._entry_style,
                               allow_inv_mapping=self.allow_inv_mapping,
                               hidden=self.hidden,
                               read_only=self.read_only,
                               reset_on_analysis=self.reset_on_analysis)
            field.name = self.name
            field.module = obj
            obj.fields.fields_dict[self.name] = field

        field.value = value

    @property
    def widget(self) -> type[ttk.Combobox]:
        return ttk.Combobox

    @property
    def value_type(self) -> type[StringValue]:
        return StringValue

    @property
    def value(self) -> DictValT:
        """
        The object mapped to the option as given by `options_map`.
        Can be set by using the option string or, if `allow_inv_mapping` is True, the object.
        """
        value = super().value
        return self.options_map[value]

    @value.setter
    def value(self, val: DictValT | str | BaseValue[str, tk.StringVar]):
        if isinstance(val, BaseValue):
            self._value = val
            self._value_var_setter()
        elif val in self.options:
            super().value = val  # pyright: ignore[reportAttributeAccessIssue]
        elif self.allow_inv_mapping and val in self._inv_map:
            val = self._inv_map[val]  # pyright: ignore[reportArgumentType]
            super().value = val
        else:
            raise ValueError("Value not in options")

    def new_entry(self, parent: tk.Misc) -> ttk.Combobox:
        """
        Returns a combobox linked to this field.
        This is placed in `parent`, this is not the fields parent.

        Parameters
        ----------
        parent : tk.Misc

        Returns
        -------
        ttk.Combobox
        """
        var = self.value_var
        if self.read_only:
            state = "disabled"
        else:
            state = "readonly"
        if self._entry_style is None:
            entry = self.widget(parent,
                                textvariable=var,
                                values=self.options,
                                state=state)
        else:
            entry = self.widget(parent,
                                textvariable=var,
                                values=self.options,
                                style=self._entry_style,
                                state=state)
        self._entries.append(entry)
        return entry


class BoolField(BaseField[bool, tk.BooleanVar]):
    """
    Represents a boolean field.
    Has the same attributes and methods as BaseField unless stated below.
    """

    def __init__(self,
                 initial_value: bool | Callable[[], bool] = True,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False,
                 reset_on_analysis: bool = False):
        super().__init__(initial_value,
                         parent=parent,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only,
                         reset_on_analysis=reset_on_analysis)
        self._entries: list[ttk.Checkbutton] = []

    @property
    def widget(self) -> type[ttk.Checkbutton]:
        return ttk.Checkbutton

    @property
    def value_type(self) -> type[BoolValue]:
        return BoolValue

    def _value_var_setter(self):
        for entry in self._entries:
            entry.configure(variable=self.value_var)

    def new_entry(self, parent: tk.Misc) -> ttk.Checkbutton:
        """
        Returns a checkbutton linked to this field.
        This is placed in `parent`, this is not the fields parent.

        Parameters
        ----------
        parent : tk.Misc

        Returns
        -------
        ttk.Checkbutton
        """
        var = self.value_var
        if self.read_only:
            state = "disabled"
        else:
            state = "normal"
        if self._entry_style is None:
            entry = self.widget(self._parent, variable=var, state=state)
        else:
            entry = self.widget(self._parent, variable=var, state=state, style=self._entry_style)
        self._entries.append(entry)
        return entry


class StringField(BaseField[str, tk.StringVar]):
    """
    Represents a string field.
    Has the same attributes and methods as BaseField unless stated below.
    """

    def __init__(self,
                 initial_value: str | Callable[[], str] = "",
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False,
                 reset_on_analysis: bool = False):
        super().__init__(initial_value,
                         parent=parent,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only,
                         reset_on_analysis=reset_on_analysis)

    @property
    def value_type(self) -> type[StringValue]:
        return StringValue


class IntField(BaseField[int, tk.IntVar]):
    """
    Represents an integer field.
    Has the same attributes and methods as BaseField unless stated below.
    """

    def __init__(self,
                 initial_value: int | Callable[[], int] = 0,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False,
                 reset_on_analysis: bool = False):
        super().__init__(initial_value,
                         parent=parent,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only,
                         reset_on_analysis=reset_on_analysis)

    @property
    def widget(self) -> type[IntEntry]:
        return IntEntry

    @property
    def value_type(self) -> type[IntValue]:
        return IntValue


class PercField(BaseField[float, tk.IntVar]):
    """
    Represents a percentage field.
    Has the same attributes and methods as BaseField unless stated below.
    """

    def __init__(self,
                 initial_value: float | Callable[[], float] = 0,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False,
                 reset_on_analysis: bool = False):
        if isinstance(initial_value, float) and (initial_value > 100 or initial_value < 0):
            raise ValueError("Initial value must be less that 100")
        super().__init__(initial_value,
                         parent=parent,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only,
                         reset_on_analysis=reset_on_analysis)

    @property
    def widget(self) -> type[PercEntry]:
        return PercEntry

    @property
    def value_type(self) -> type[FloatValue]:
        return FloatValue


class FloatField(BaseField[float, tk.DoubleVar]):
    """
    Represents a float field.
    Has the same attributes and methods as BaseField unless stated below.
    """

    def __init__(self,
                 initial_value: float | Callable[[], float] = 0,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False,
                 reset_on_analysis: bool = False):
        super().__init__(initial_value,
                         parent=parent,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only,
                         reset_on_analysis=reset_on_analysis)

    @property
    def widget(self) -> type[FloatEntry]:
        return FloatEntry

    @property
    def value_type(self) -> type[FloatValue]:
        return FloatValue


class DateField(BaseField[date, DateVar]):
    """
    Represents a date field.
    Has the same attributes and methods as BaseField unless stated below.
    """

    def __init__(self,
                 initial_value: date | Callable[[], date] = date.today,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False,
                 reset_on_analysis: bool = False):
        super().__init__(initial_value,
                         parent=parent,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only,
                         reset_on_analysis=reset_on_analysis)

    @property
    def widget(self) -> type[DateEntry]:
        return DateEntry

    @property
    def value_type(self) -> type[DateValue]:
        return DateValue
