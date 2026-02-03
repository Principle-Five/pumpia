"""
Contains simple inputs and outputs.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
import tkinter as tk
from tkinter import ttk
from datetime import date
from pumpia.widgets.entry_boxes import IntEntry, FloatEntry, DateEntry, PercEntry, DateVar


class BaseValue[ValT, TkVarT:tk.Variable](ABC):

    def __init__(self, parent: tk.Misc, initial_value: ValT) -> None:
        self._value: ValT = initial_value
        self.var: TkVarT = self.var_type(parent)
        self._var_trace = self.var.trace_add("write", self._var_to_val)

    @property
    @abstractmethod
    def var_type(self) -> type[TkVarT]:
        pass

    @property
    def value(self) -> ValT:
        """
        The value of the input/output.
        """
        return self._value

    @value.setter
    def value(self, val: ValT):
        self._value = val
        self.var.set(val)

    def _var_to_val(self, *_):
        self._value = self.var.get()


class StringValue(BaseValue[str, tk.StringVar]):
    """
    Represents a string input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self, parent: tk.Misc, initial_value: str = "") -> None:
        super().__init__(parent=parent,
                         initial_value=initial_value)

    @property
    def var_type(self) -> type[tk.StringVar]:
        return tk.StringVar


class BoolValue(BaseValue[bool, tk.BooleanVar]):
    """
    Represents an integer input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self, parent: tk.Misc, initial_value: bool = True) -> None:
        super().__init__(parent=parent,
                         initial_value=initial_value)

    @property
    def var_type(self) -> type[tk.BooleanVar]:
        return tk.BooleanVar


class IntValue(BaseValue[int, tk.IntVar]):
    """
    Represents an integer input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self, parent: tk.Misc, initial_value: int = 0) -> None:
        super().__init__(parent=parent,
                         initial_value=initial_value)

    @property
    def var_type(self) -> type[tk.IntVar]:
        return tk.IntVar


class FloatValue(BaseValue[float, tk.DoubleVar]):
    """
    Represents a float input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self, parent: tk.Misc, initial_value: float = 0) -> None:
        super().__init__(parent=parent,
                         initial_value=initial_value)

    @property
    def var_type(self) -> type[tk.DoubleVar]:
        return tk.DoubleVar


class DateValue(BaseValue[date, DateVar]):
    """
    Represents a date input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self, parent: tk.Misc, initial_value: date | Callable[[], date] = date.today) -> None:
        if callable(initial_value):
            initial_value = initial_value()
        super().__init__(parent=parent,
                         initial_value=initial_value)

    @property
    def var_type(self) -> type[DateVar]:
        return DateVar


class BaseIO[ValT, TkVarT:tk.Variable](ABC):
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
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False):
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

    @property
    @abstractmethod
    def widget(self) -> type[ttk.Entry]:
        pass

    @property
    @abstractmethod
    def value_type(self) -> type[BaseValue[ValT, TkVarT]]:
        pass

    @property
    def verbose_name(self) -> str | None:
        """
        The verbose name of the input/output.
        """
        return self._name

    @verbose_name.setter
    def verbose_name(self, val: str):
        self._name = val
        if self._label_var is not None:
            self._label_var.set(val)

    @property
    def value_store(self) -> BaseValue[ValT, TkVarT]:
        if self._value is None:
            if self._parent is None:
                raise ValueError("Parent has not been set")
            self._value = self.value_type(self._parent, self.initial_value)
        return self._value

    @property
    def value_var(self) -> TkVarT:
        return self.value_store.var

    @property
    def value(self) -> ValT:
        """
        The value of the input/output.
        """
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
        The label with the name of the input/output.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
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
        The tkinter variable related to `label`.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
        if self.verbose_name is None:
            raise ValueError("Name has not been set")
        if self._label_var is None:
            self._label_var = tk.StringVar(self._parent, value=self.verbose_name)
        return self._label_var

    def set_parent(self, parent: tk.Misc):
        """
        Sets the parent of the input/output.

        Parameters
        ----------
        parent : tk.Misc
            The parent of the input/output.
        """
        if self._parent is None:
            self._parent = parent
        else:
            raise ValueError("Parent already set")

    def reset_value(self):
        """
        Resets the IO to the initial value.
        """
        self.value = self.initial_value

    def new_entry(self, parent: tk.Misc) -> ttk.Entry:
        """
        The entry widget of the input.
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


class OptionIO[DictValT](BaseIO[str, tk.StringVar]):
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
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 allow_inv_mapping: bool = False,
                 hidden: bool = False,
                 read_only: bool = False):
        super().__init__(initial,
                         parent=parent,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only)
        self._entries: list[ttk.Combobox] = []

        self.allow_inv_mapping: bool = allow_inv_mapping
        self.options_map: dict[str, DictValT] = options_map

        if self.allow_inv_mapping:
            self._inv_map: dict[DictValT, str] = {v: k for k, v in self.options_map.items()}

        self.options = list(self.options_map.keys())
        if initial not in self.options:
            raise ValueError("initial not in options")

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
    def value(self, val: DictValT | str):
        if val in self.options:
            super().value = val  # pyright: ignore[reportAttributeAccessIssue]
        elif self.allow_inv_mapping and val in self._inv_map:
            val = self._inv_map[val]  # pyright: ignore[reportArgumentType]
            super().value = val
        else:
            raise ValueError("Value not in options")

    @property
    def entry(self) -> ttk.Combobox:
        """
        The Combobox widget of the input.
        """
        var = self.value_var
        if self.read_only:
            state = "disabled"
        else:
            state = "readonly"
        if self._entry_style is None:
            entry = self.widget(self._parent,
                                textvariable=var,
                                values=self.options,
                                state=state)
        else:
            entry = self.widget(self._parent,
                                textvariable=var,
                                values=self.options,
                                style=self._entry_style,
                                state=state)
        self._entries.append(entry)
        return entry


class BoolIO(BaseIO[bool, tk.BooleanVar]):
    """
    Represents a boolean input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self,
                 initial_value: bool | Callable[[], bool] = True,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only)
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
        The Checkbutton widget of the input.
        """
        var = self.value_var
        if self.read_only:
            state = "readonly"
        else:
            state = "normal"
        if self._entry_style is None:
            entry = self.widget(self._parent, variable=var, state=state)
        else:
            entry = self.widget(self._parent, variable=var, state=state, style=self._entry_style)
        self._entries.append(entry)
        return entry


class StringIO(BaseIO[str, tk.StringVar]):
    """
    Represents a string input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self,
                 initial_value: str | Callable[[], str] = "",
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only)

    @property
    def widget(self) -> type[ttk.Entry]:
        return ttk.Entry

    @property
    def value_type(self) -> type[StringValue]:
        return StringValue


class IntIO(BaseIO[int, tk.IntVar]):
    """
    Represents an integer input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self,
                 initial_value: int | Callable[[], int] = 0,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only)

    @property
    def widget(self) -> type[IntEntry]:
        return IntEntry

    @property
    def value_type(self) -> type[IntValue]:
        return IntValue


class PercIO(BaseIO[float, tk.IntVar]):
    """
    Represents a percentage input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self,
                 initial_value: float | Callable[[], float] = 0,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False):
        if isinstance(initial_value, float) and initial_value > 100:
            raise ValueError("Initial value must be less that 100")
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only)

    @property
    def widget(self) -> type[PercEntry]:
        return PercEntry

    @property
    def value_type(self) -> type[FloatValue]:
        return FloatValue


class FloatIO(BaseIO[float, tk.DoubleVar]):
    """
    Represents a float input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self,
                 initial_value: float | Callable[[], float] = 0,
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only)

    @property
    def widget(self) -> type[FloatEntry]:
        return FloatEntry

    @property
    def value_type(self) -> type[FloatValue]:
        return FloatValue


class DateIO(BaseIO[date, DateVar]):
    """
    Represents a date input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    def __init__(self,
                 initial_value=date.today(),
                 parent: tk.Misc | None = None,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False,
                 read_only: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden,
                         read_only=read_only)

    @property
    def widget(self) -> type[DateEntry]:
        return DateEntry

    @property
    def value_type(self) -> type[DateValue]:
        return DateValue
