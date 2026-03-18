"""
Contains groupings of inputs/outputs.
"""
from typing import overload, Self
import tkinter as tk
from tkinter import ttk
from pumpia.utilities.tkinter_utils import tk_copy
from pumpia.module_handling.fields.fields import BaseField
from pumpia.module_handling.modules import BaseModule
from pumpia.module_handling.module_collections import BaseCollection


class _FieldWindows:
    def __init__(self, obj: BaseCollection | BaseModule) -> None:
        self.obj: BaseCollection | BaseModule = obj
        self.windows_dict: dict[str, FieldWindow] = {}

    def __iter__(self):
        for window in self.windows_dict.values():
            yield window


class _FieldWindowsMeta:
    def __init__(self) -> None:
        self.windows: dict[str, FieldWindow] = {}
        self.name: str = ""
        self.private_name: str = "_"

    @property
    def window_names(self) -> list[str]:
        return list(self.windows.keys())

    def __set_name__(self, owner: type[BaseCollection | BaseModule], name: str):
        self.name = name
        self.private_name = "_" + name

    @overload
    def __get__(self, obj: BaseCollection | BaseModule, owner=None) -> _FieldWindows: ...
    @overload
    def __get__(self, obj: None, owner=None) -> Self: ...

    def __get__(self, obj: BaseCollection | BaseModule | None, owner=None) -> _FieldWindows | Self:
        if obj is None:
            return self

        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            windows = _FieldWindows(obj)
            setattr(obj, self.private_name, windows)
            return windows


class FieldWindow:
    """
    Represents a group of linked input / output objects.
    IOs should only be a member of one group.

    Parameters
    ----------
    linked_ios: list[BaseIO]
        The list of linked input / output objects.

    Attributes
    ----------
    linked_ios: list[BaseIO]
    """

    def __init__(self, *fields: BaseField,
                 verbose_name: str | None = None,
                 show_copy_buttons: bool = True):
        self.verbose_name: str | None = verbose_name
        self.show_copy_buttons: bool = show_copy_buttons
        self.module_field_names: list[tuple[str | None, str]] = [(field.module.name, field.name)
                                                                 if field.module is not None
                                                                 else (None, field.name)
                                                                 for field in fields]
        self.fields: list[BaseField] = []
        self.name: str = ""

    def __set_name__(self, owner: type[BaseCollection | BaseModule], name: str):
        self.name = name
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()
        owner.field_windows.windows[name] = self

    def __get__(self, obj: BaseCollection | BaseModule | None, owner=None) -> Self:
        if obj is None:
            return self

        try:
            return obj.field_windows.windows_dict[self.name]  # pyright: ignore[reportReturnType]
        except KeyError:
            fields: list[BaseField] = []
            if isinstance(obj, BaseCollection):
                for module_name, field_name in self.module_field_names:
                    if module_name is not None:
                        fields.append(getattr(getattr(obj, module_name), field_name))
            else:
                for _, field_name in self.module_field_names:
                    fields.append(getattr(obj, field_name))

            window = type(self)(*[], verbose_name=self.verbose_name)
            window.module_field_names = self.module_field_names
            window.fields = fields
            obj.field_windows.windows_dict[self.name] = window
            return window

    def get_frame(self, parent: tk.Misc, show_copy_buttons: bool | None = None) -> ttk.Labelframe:
        if len(self.fields) == 0:
            raise ValueError("Window group has no fields.")
        if self.verbose_name is None:
            frame = ttk.Labelframe(parent, text=self.name)
        else:
            frame = ttk.Labelframe(parent, text=self.verbose_name)
        final_row: int = -1
        for row, field in enumerate(self.fields):
            field.parent = frame
            label = field.new_label(frame)
            label.grid(column=0, row=row, sticky=tk.NSEW)
            entry = field.new_entry(frame)
            entry.grid(column=1, row=row, sticky=tk.NSEW)
            final_row = row

        if show_copy_buttons or ((show_copy_buttons is None)
                                 and self.show_copy_buttons):
            h_button = ttk.Button(frame,
                                  text="Copy Horizontal",
                                  command=self.copy_horizontal)
            v_button = ttk.Button(frame,
                                  text="Copy Vertical",
                                  command=self.copy_vertical)
            h_button.grid(column=0, row=final_row + 1, columnspan=2, sticky=tk.NSEW)
            v_button.grid(column=0, row=final_row + 2, columnspan=2, sticky=tk.NSEW)

        return frame

    @property
    def var_values(self) -> list:
        """
        The values of the variables in the frame.
        """
        return [field.value for field in self.fields]

    @property
    def var_strings(self) -> list[str]:
        """
        The string representations of the variable values.
        """
        return [str(val) for val in self.var_values]

    @property
    def horizontal_str(self) -> str:
        """
        The string representation of the variable values tab seperated.
        """
        return "\t".join(self.var_strings)

    @property
    def vertical_str(self) -> str:
        """
        The string representation of the variable values newline seperated.
        """
        return "\n".join(self.var_strings)

    def copy_horizontal(self) -> None:
        """
        Copies the horizontal string representation of the variable values to the clipboard.
        """
        tk_copy(self.horizontal_str)

    def copy_vertical(self) -> None:
        """
        Copies the vertical string representation of the variable values to the clipboard.
        """
        tk_copy(self.vertical_str)
