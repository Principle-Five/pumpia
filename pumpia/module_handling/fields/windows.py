"""
Contains groupings of inputs/outputs.
"""
from typing import overload, Self, TYPE_CHECKING
import tkinter as tk
from tkinter import ttk
from pumpia.utilities.tkinter_utils import tk_copy
from pumpia.module_handling.fields.fields import BaseField


if TYPE_CHECKING:
    from pumpia.module_handling.modules import BaseModule
    from pumpia.module_handling.collections import BaseCollection


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
        self.base_owner: type[BaseCollection | BaseModule] | None = None

    @property
    def window_names(self) -> list[str]:
        return list(self.windows.keys())

    def __set_name__(self, owner: type[BaseCollection | BaseModule], name: str):
        self.name = name
        self.private_name = "_" + name
        self.base_owner = owner

    @overload
    def __get__(self, obj: BaseCollection | BaseModule, owner: type[BaseCollection | BaseModule]) -> _FieldWindows: ...
    @overload
    def __get__(self, obj: None, owner: type[BaseCollection | BaseModule]) -> Self: ...

    def __get__(self, obj: BaseCollection | BaseModule | None, owner: type[BaseCollection | BaseModule]) -> _FieldWindows | Self:
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

    def __init__(self,
                 *fields: BaseField,
                 field_names: list[str | None] | None = None,
                 verbose_name: str | None = None,
                 show_copy_buttons: bool = True):
        if isinstance(field_names, list) and len(field_names) != len(fields):
            raise TypeError("field_names not the same length as fields")
        self.verbose_name: str | None = verbose_name
        self.show_copy_buttons: bool = show_copy_buttons
        self.fields: list[BaseField] = list(fields)
        self.field_names: list[str | None] | None = field_names
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
            module_field_names = [(field.module.name, field.name)
                                  if field.module is not None
                                  else (None, field.name)
                                  for field in self.fields]
            for module_name, field_name in module_field_names:
                if module_name is not None:
                    fields.append(getattr(getattr(obj, module_name).fields, field_name))
                else:
                    fields.append(getattr(obj.fields, field_name))  # pyright: ignore[reportAttributeAccessIssue]

            window = type(self)(*fields,
                                field_names=self.field_names,
                                verbose_name=self.verbose_name,
                                show_copy_buttons=self.show_copy_buttons)

            obj.field_windows.windows_dict[self.name] = window
            return window
        except AttributeError:
            return self

    def get_frame(self, parent: tk.Misc, show_copy_buttons: bool | None = None) -> ttk.Labelframe:
        if len(self.fields) == 0:
            raise ValueError("Window group has no fields.")
        if self.verbose_name is None:
            frame = ttk.Labelframe(parent, text=self.name)
        else:
            frame = ttk.Labelframe(parent, text=self.verbose_name)
        row: int = 0
        for field_num, field in enumerate(self.fields):
            if field.parent is None:
                field.parent = frame

            if not field.hidden:
                label = field.new_label(frame)
                if (self.field_names is not None
                        and self.field_names[field_num] is not None):
                    field.label_var.set(self.field_names[field_num])  # pyright: ignore[reportArgumentType]
                label.grid(column=0, row=row, sticky=tk.NSEW)
                entry = field.new_entry(frame)
                entry.grid(column=1, row=row, sticky=tk.NSEW)
                row += 1

        if show_copy_buttons or ((show_copy_buttons is None)
                                 and self.show_copy_buttons):
            h_button = ttk.Button(frame,
                                  text="Copy Horizontal",
                                  command=self.copy_horizontal)
            v_button = ttk.Button(frame,
                                  text="Copy Vertical",
                                  command=self.copy_vertical)
            h_button.grid(column=0, row=row, columnspan=2, sticky=tk.NSEW)
            v_button.grid(column=0, row=row + 1, columnspan=2, sticky=tk.NSEW)

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
