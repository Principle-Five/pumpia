"""
Contains simple values.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
import tkinter as tk
from datetime import date

from pumpia.widgets.entry_boxes import DateVar


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
