"""
Contains simple inputs and outputs.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
import tkinter as tk
from tkinter import ttk
from datetime import date
from pumpia.widgets.entry_boxes import IntEntry, FloatEntry, DateEntry, PercEntry, DateVar


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

    var_type: type[tk.Variable]

    def __init__(self,
                 # pylint: disable-next=undefined-variable
                 initial_value: ValT | Callable[[], ValT],
                 *,
                 verbose_name: str | None,
                 label_style: str | None = None,
                 hidden: bool = False):
        self._name: str | None = verbose_name
        self._label_style: str | None = label_style
        # pylint: disable-next=undefined-variable
        self._value: ValT | Callable[[], ValT] = initial_value
        self._parent: tk.Misc | None = None
        self._label: ttk.Label | None = None
        self._label_var: tk.StringVar | None = None
        # pylint: disable-next=undefined-variable
        self._var: TkVarT | None = None
        self._var_trace: str = ""
        self.hidden: bool = hidden

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
    def value(self
              # pylint: disable-next=undefined-variable
              ) -> ValT:
        """
        The value of the input/output.
        """
        if callable(self._value):
            value = self._value()
            self._value = value  # type: ignore
            return value  # type: ignore
        return self._value

    @value.setter
    def value(self,
              # pylint: disable-next=undefined-variable
              val: ValT):
        if self._var is None:
            self._value = val
        else:
            self._var.set(val)

    @property
    def label(self) -> ttk.Label:
        """
        The label with the name of the input/output.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
        if self._label is None:
            var = self.label_var
            if self._label_style is None:
                self._label = ttk.Label(self._parent, textvariable=var)
            else:
                self._label = ttk.Label(self._parent, style=self._label_style, textvariable=var)
        return self._label

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

    @property
    def value_var(self
                  # pylint: disable-next=undefined-variable
                  ) -> TkVarT:
        """
        The tkinter variable related to `value`.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
        if self._var is None:
            self._var = self.var_type(self._parent, value=self.value)  # type: ignore
            self._var_trace = self._var.trace_add("write", self._var_to_val)  # type: ignore
        return self._var  # type: ignore

    @value_var.setter
    def value_var(self,
                  # pylint: disable-next=undefined-variable
                  var: TkVarT):
        if self._parent is None:
            raise ValueError("Parent has not been set")
        if self._var is not None:
            self._var.trace_remove("write", self._var_trace)
        self._var = var
        self._var_trace = self._var.trace_add("write", self._var_to_val)
        self._var_to_val()
        self._value_var_setter()

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

    @abstractmethod
    def _value_var_setter(self):
        pass

    def _var_to_val(self, *_):
        try:
            self._value = self.value_var.get()
        except ValueError:
            pass
        except tk.TclError:
            pass


class BaseInput[ValT, TkVarT](
        # pylint: disable-next=undefined-variable
        BaseIO[ValT, TkVarT]):  # type: ignore
    """
    Base class for input handling for modules.
    Has the same attributes and methods as BaseIO unless stated below.

    Parameters
    ----------
    entry_style : str, optional
        The style of the entry widget (default is None).

    Attributes
    ----------
    entry : ttk.Entry
    """

    widget: type[ttk.Entry]

    def __init__(self,
                 # pylint: disable-next=undefined-variable
                 initial_value: ValT | Callable[[], ValT],
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False):
        BaseIO.__init__(self,
                        initial_value,
                        verbose_name=verbose_name,
                        label_style=label_style,
                        hidden=hidden)
        self._entry_style: str | None = entry_style
        self._entry: ttk.Entry | None = None

    @property
    def entry(self) -> ttk.Entry:
        """
        The entry widget of the input.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")

        if self._entry is None:
            var = self.value_var
            if self._entry_style is None:
                self._entry = self.widget(self._parent, textvariable=var)
            else:
                self._entry = self.widget(self._parent, textvariable=var, style=self._entry_style)
        return self._entry

    def _value_var_setter(self):
        if self._entry is not None:
            self._entry.configure(textvariable=self.value_var)


class BaseOutput[ValT, TkVarT](
        # pylint: disable-next=undefined-variable
        BaseIO[ValT, TkVarT]):  # type: ignore
    """
    Base class for output handling.
    Has the same attributes and methods as BaseIO unless stated below.

    Parameters
    ----------
    val_label_style : str, optional
        The style of the value label widget (default is None).

    Attributes
    ----------
    value_label : ttk.Label
    """

    def __init__(self,
                 # pylint: disable-next=undefined-variable
                 initial_value: ValT | Callable[[], ValT],
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 val_label_style: str | None = None,
                 hidden: bool = False):
        BaseIO.__init__(self,
                        initial_value,
                        verbose_name=verbose_name,
                        label_style=label_style,
                        hidden=hidden)
        self._val_label_style: str | None = val_label_style
        self._val_label: ttk.Label | None = None

    @property
    def value_label(self) -> ttk.Label:
        """
        The value label widget of the output.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")

        if self._val_label is None:
            var = self.value_var
            if self._val_label_style is None:
                self._val_label = ttk.Label(self._parent, textvariable=var)
            else:
                self._val_label = ttk.Label(self._parent,
                                            textvariable=var,
                                            style=self._val_label_style)
        return self._val_label

    def _value_var_setter(self):
        if self._val_label is not None:
            self._val_label.configure(textvariable=self.value_var)


class OptionInput[DictValT](BaseInput[str, tk.StringVar]):
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

    widget: type[ttk.Combobox] = ttk.Combobox
    var_type = tk.StringVar

    def __init__(self,
                 # pylint: disable-next=undefined-variable
                 options_map: dict[str, DictValT],
                 initial: str | Callable[[], str],
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 allow_inv_mapping: bool = False,
                 hidden: bool = False):
        if initial not in options_map:
            raise ValueError("initial must be option")
        super().__init__(initial,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden)
        self._entry: ttk.Combobox | None = None

        self.allow_inv_mapping: bool = allow_inv_mapping
        # pylint: disable-next=undefined-variable
        self.options_map: dict[str, DictValT] = options_map

        if self.allow_inv_mapping:
            # pylint: disable-next=undefined-variable
            self._inv_map: dict[DictValT, str] = {v: k for k, v in self.options_map.items()}

        self.options = list(self.options_map.keys())
        if initial not in self.options:
            raise ValueError("initial not in options")

    @property
    def value(self
              # pylint: disable-next=undefined-variable
              ) -> DictValT:
        """
        The object mapped to the option as given by `options_map`.
        Can be set by using the option string or, if `allow_inv_mapping` is True, the object.
        """
        if callable(self._value):
            value = self._value()
            return self.options_map[value]
        return self.options_map[self._value]

    @value.setter
    def value(self,
              # pylint: disable-next=undefined-variable
              val: DictValT | str):
        if val in self.options:
            if self._var is None:
                self._value = val  # type: ignore
            else:
                self._var.set(val)  # type: ignore
        elif self.allow_inv_mapping:
            val = self._inv_map[val]  # type: ignore
            if self._var is None:
                self._value = val
            else:
                self._var.set(val)
        else:
            raise ValueError("Value not in options")

    @property
    def entry(self) -> ttk.Combobox:
        """
        The Combobox widget of the input.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
        var = self.value_var
        if self._entry is None:
            if self._entry_style is None:
                self._entry = self.widget(self._parent,
                                          textvariable=var,
                                          values=self.options,
                                          state="readonly")
            else:
                self._entry = self.widget(self._parent,
                                          textvariable=var,
                                          values=self.options,
                                          style=self._entry_style,
                                          state="readonly")
        return self._entry


class BoolInput(BaseInput[bool, tk.BooleanVar]):
    """
    Represents a boolean input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    widget: type[ttk.Checkbutton] = ttk.Checkbutton
    var_type = tk.BooleanVar

    def __init__(self,
                 initial_value: bool | Callable[[], bool] = True,
                 *,
                 verbose_name: str | None = None,
                 label_style: str | None = None,
                 entry_style: str | None = None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden)
        self._entry: ttk.Checkbutton | None = None

    @property
    def entry(self) -> ttk.Checkbutton:
        """
        The Checkbutton widget of the input.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")

        if self._entry is None:
            var = self.value_var
            if self._entry_style is None:
                self._entry = self.widget(self._parent, variable=var)
            else:
                self._entry = self.widget(self._parent, variable=var, style=self._entry_style)
        return self._entry


class StringInput(BaseInput[str, tk.StringVar]):
    """
    Represents a string input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    widget = ttk.Entry
    var_type = tk.StringVar

    def __init__(self,
                 initial_value: str | Callable[[], str] = "",
                 *, verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden)


class IntInput(BaseInput[int, tk.IntVar]):
    """
    Represents an integer input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    widget = IntEntry
    var_type = tk.IntVar

    def __init__(self,
                 initial_value: int | Callable[[], int] = 0,
                 *, verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden)


class PercInput(BaseInput[float, tk.IntVar]):
    """
    Represents a percentage input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    widget = PercEntry
    var_type = tk.DoubleVar

    def __init__(self,
                 initial_value: float | Callable[[], float] = 0,
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 hidden: bool = False):
        if isinstance(initial_value, float) and initial_value > 100:
            raise ValueError("Initial value must be less that 100")
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden)


class FloatInput(BaseInput[float, tk.DoubleVar]):
    """
    Represents a float input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    widget = FloatEntry
    var_type = tk.DoubleVar

    def __init__(self,
                 initial_value: float | Callable[[], float] = 0,
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden)


class DateInput(BaseInput[date, DateVar]):
    """
    Represents a date input.
    Has the same attributes and methods as BaseInput unless stated below.
    """

    widget = DateEntry
    var_type = DateVar

    def __init__(self,
                 initial_value=date.today(),
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 entry_style=None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         entry_style=entry_style,
                         hidden=hidden)


class StringOutput(BaseOutput[str, tk.StringVar]):
    """
    Represents a string output.
    Has the same attributes and methods as BaseOutput unless stated below.
    """
    var_type = tk.StringVar

    def __init__(self,
                 initial_value: str | Callable[[], str] = "",
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 val_label_style=None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         val_label_style=val_label_style,
                         hidden=hidden)


class IntOutput(BaseOutput[int, tk.IntVar]):
    """
    Represents an integer output.
    Has the same attributes and methods as BaseOutput unless stated below.
    """
    var_type = tk.IntVar

    def __init__(self,
                 initial_value: int | Callable[[], int] = 0,
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 val_label_style=None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         val_label_style=val_label_style,
                         hidden=hidden)


class FloatOutput(BaseOutput[float, tk.DoubleVar]):
    """
    Represents a float output.
    Has the same attributes and methods as BaseOutput unless stated below.
    """
    var_type = tk.DoubleVar

    def __init__(self,
                 initial_value: float | Callable[[], float] = 0,
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 val_label_style=None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         val_label_style=val_label_style,
                         hidden=hidden)


class DateOutput(BaseOutput[date, DateVar]):
    """
    Represents a date output.
    Has the same attributes and methods as BaseOutput unless stated below.
    """
    var_type = DateVar

    def __init__(self,
                 initial_value=date.today(),
                 *,
                 verbose_name: str | None = None,
                 label_style=None,
                 val_label_style=None,
                 hidden: bool = False):
        super().__init__(initial_value,
                         verbose_name=verbose_name,
                         label_style=label_style,
                         val_label_style=val_label_style,
                         hidden=hidden)
