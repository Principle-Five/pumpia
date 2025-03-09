"""
Classes:
 * AddCombo
 * DateEntry
 * FloatEntry
 * IntEntry
 * PercEntry
"""
import tkinter as tk
from tkinter import ttk
from typing import Literal, overload
from collections.abc import Callable

from pumpia.utilities.string_validators import check_date, check_signed_float, check_signed_int, check_perc
from pumpia.widgets.typing import Cursor, TakeFocusValue, FontDescription, EntryValidateCommand, EntryValidateOptions, XYScrollCommand
from pumpia.widgets.variables import DateVar


class DateEntry(ttk.Entry):
    """
    Entry widget for date input.

    Parameters
    ----------
    parent : tk.Misc
        The parent widget.
    textvariable : DateVar
        The variable to store the date.
    widget : str or None, optional
        The widget name (default is None).
    background : str, optional
        The background color (default is undocumented).
    class_ : str, optional
        The class name (default is "").
    cursor : Cursor, optional
        The cursor type (default is "").
    exportselection : bool, optional
        Whether to export selection (default is True).
    font : FontDescription, optional
        The font description (default is "TkTextFont").
    foreground : str, optional
        The foreground color (default is "").
    invalidcommand : EntryValidateCommand, optional
        The command to run when validation fails (default is "").
    justify : Literal["left", "center", "right"], optional
        The justification of the text (default is "left").
    name : str, optional
        The name of the widget (default is None).
    show : str, optional
        The character to display instead of the actual text (default is "").
    state : str, optional
        The state of the widget (default is "normal").
    style : str, optional
        The style of the widget (default is "").
    takefocus : TakeFocusValue, optional
        Whether the widget can take focus (default is None).
    validate : EntryValidateOptions, optional
        The validation option (default is 'focusout').
    validatecommand : EntryValidateCommand, optional
        The command to run when validation is triggered (default is "").
    width : int, optional
        The width of the widget (default is 20).
    xscrollcommand : XYScrollCommand, optional
        The command to run when the widget is scrolled (default is "").
    """

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        textvariable: DateVar,
        widget: str | None = None,
        *,
        background: str = ...,  # undocumented
        class_: str = "",
        cursor: Cursor = ...,
        exportselection: bool = True,
        font: FontDescription = "TkTextFont",
        foreground: str = "",
        invalidcommand: EntryValidateCommand = "",
        justify: Literal["left", "center", "right"] = "left",
        name: str = ...,
        show: str = "",
        state: str = "normal",
        style: str = "",
        takefocus: TakeFocusValue = ...,
        validate: EntryValidateOptions = 'focusout',
        validatecommand: EntryValidateCommand = "",
        width: int = 20,
        xscrollcommand: XYScrollCommand = "",
    ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 textvariable: DateVar,
                 widget: str | None = None,
                 *,
                 validate: EntryValidateOptions = 'focusout',
                 **kw) -> None: ...

    def __init__(self,
                 parent: tk.Misc,
                 textvariable: DateVar,
                 widget: str | None = None,
                 *,
                 validate: EntryValidateOptions = 'focusout',
                 **kw) -> None:
        self.vcmd = parent.register(check_date)
        self.ivcmd = parent.register(self.focus_set)

        super().__init__(parent,
                         widget,
                         textvariable=textvariable,
                         invalidcommand=self.ivcmd,
                         validate=validate,
                         validatecommand=(self.vcmd, '%P'),
                         **kw)


class IntEntry(ttk.Entry):
    """
    Entry widget for integer input.

    Parameters
    ----------
    parent : tk.Misc
        The parent widget.
    widget : str or None, optional
        The widget name (default is None).
    background : str, optional
        The background color (default is undocumented).
    class_ : str, optional
        The class name (default is "").
    cursor : Cursor, optional
        The cursor type (default is "").
    exportselection : bool, optional
        Whether to export selection (default is True).
    font : FontDescription, optional
        The font description (default is "TkTextFont").
    foreground : str, optional
        The foreground color (default is "").
    invalidcommand : EntryValidateCommand, optional
        The command to run when validation fails (default is "").
    justify : Literal["left", "center", "right"], optional
        The justification of the text (default is "left").
    name : str, optional
        The name of the widget (default is None).
    show : str, optional
        The character to display instead of the actual text (default is "").
    state : str, optional
        The state of the widget (default is "normal").
    style : str, optional
        The style of the widget (default is "").
    takefocus : TakeFocusValue, optional
        Whether the widget can take focus (default is None).
    textvariable : tk.IntVar, optional
        The variable to store the integer value (default is None).
    validate : EntryValidateOptions, optional
        The validation option (default is 'all').
    validatecommand : EntryValidateCommand, optional
        The command to run when validation is triggered (default is "").
    width : int, optional
        The width of the widget (default is 20).
    xscrollcommand : XYScrollCommand, optional
        The command to run when the widget is scrolled (default is "").
    """

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        widget: str | None = None,
        *,
        background: str = ...,  # undocumented
        class_: str = "",
        cursor: Cursor = ...,
        exportselection: bool = True,
        font: FontDescription = "TkTextFont",
        foreground: str = "",
        invalidcommand: EntryValidateCommand = "",
        justify: Literal["left", "center", "right"] = "left",
        name: str = ...,
        show: str = "",
        state: str = "normal",
        style: str = "",
        takefocus: TakeFocusValue = ...,
        textvariable: tk.IntVar = ...,
        validate: EntryValidateOptions = 'all',
        validatecommand: EntryValidateCommand = "",
        width: int = 20,
        xscrollcommand: XYScrollCommand = "",
    ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 widget: str | None = None,
                 *,
                 validate: EntryValidateOptions = 'all',
                 **kw) -> None: ...

    def __init__(self,
                 parent: tk.Misc,
                 widget: str | None = None,
                 *,
                 validate: EntryValidateOptions = 'all',
                 **kw) -> None:
        self.vcmd = parent.register(check_signed_int)
        self.ivcmd = parent.register(self.focus_set)

        super().__init__(parent,
                         widget,
                         invalidcommand=self.ivcmd,
                         validate=validate,
                         validatecommand=(self.vcmd, '%P'),
                         **kw)


class FloatEntry(ttk.Entry):
    """
    Entry widget for float input.

    Parameters
    ----------
    parent : tk.Misc
        The parent widget.
    widget : str or None, optional
        The widget name (default is None).
    background : str, optional
        The background color (default is undocumented).
    class_ : str, optional
        The class name (default is "").
    cursor : Cursor, optional
        The cursor type (default is "").
    exportselection : bool, optional
        Whether to export selection (default is True).
    font : FontDescription, optional
        The font description (default is "TkTextFont").
    foreground : str, optional
        The foreground color (default is "").
    invalidcommand : EntryValidateCommand, optional
        The command to run when validation fails (default is "").
    justify : Literal["left", "center", "right"], optional
        The justification of the text (default is "left").
    name : str, optional
        The name of the widget (default is None).
    show : str, optional
        The character to display instead of the actual text (default is "").
    state : str, optional
        The state of the widget (default is "normal").
    style : str, optional
        The style of the widget (default is "").
    takefocus : TakeFocusValue, optional
        Whether the widget can take focus (default is None).
    textvariable : tk.DoubleVar, optional
        The variable to store the float value (default is None).
    validate : EntryValidateOptions, optional
        The validation option (default is 'all').
    validatecommand : EntryValidateCommand, optional
        The command to run when validation is triggered (default is "").
    width : int, optional
        The width of the widget (default is 20).
    xscrollcommand : XYScrollCommand, optional
        The command to run when the widget is scrolled (default is "").
    """

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        widget: str | None = None,
        *,
        background: str = ...,  # undocumented
        class_: str = "",
        cursor: Cursor = ...,
        exportselection: bool = True,
        font: FontDescription = "TkTextFont",
        foreground: str = "",
        invalidcommand: EntryValidateCommand = "",
        justify: Literal["left", "center", "right"] = "left",
        name: str = ...,
        show: str = "",
        state: str = "normal",
        style: str = "",
        takefocus: TakeFocusValue = ...,
        textvariable: tk.DoubleVar = ...,
        validate: EntryValidateOptions = 'all',
        validatecommand: EntryValidateCommand = "",
        width: int = 20,
        xscrollcommand: XYScrollCommand = "",
    ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 widget: str | None = None,
                 *,
                 validate: EntryValidateOptions = 'all',
                 **kw) -> None: ...

    def __init__(self,
                 parent: tk.Misc,
                 widget: str | None = None,
                 *,
                 validate: EntryValidateOptions = 'all',
                 **kw) -> None:
        self.vcmd = parent.register(check_signed_float)
        self.ivcmd = parent.register(self.focus_set)

        super().__init__(parent,
                         widget,
                         invalidcommand=self.ivcmd,
                         validate=validate,
                         validatecommand=(self.vcmd, '%P'),
                         **kw)


class PercEntry(ttk.Entry):
    """
    Entry widget for percentage input.

    Parameters
    ----------
    parent : tk.Misc
        The parent widget.
    widget : str or None, optional
        The widget name (default is None).
    background : str, optional
        The background color (default is undocumented).
    class_ : str, optional
        The class name (default is "").
    cursor : Cursor, optional
        The cursor type (default is "").
    exportselection : bool, optional
        Whether to export selection (default is True).
    font : FontDescription, optional
        The font description (default is "TkTextFont").
    foreground : str, optional
        The foreground color (default is "").
    invalidcommand : EntryValidateCommand, optional
        The command to run when validation fails (default is "").
    justify : Literal["left", "center", "right"], optional
        The justification of the text (default is "left").
    name : str, optional
        The name of the widget (default is None).
    show : str, optional
        The character to display instead of the actual text (default is "").
    state : str, optional
        The state of the widget (default is "normal").
    style : str, optional
        The style of the widget (default is "").
    takefocus : TakeFocusValue, optional
        Whether the widget can take focus (default is None).
    textvariable : tk.DoubleVar, optional
        The variable to store the percentage value (default is None).
    validate : EntryValidateOptions, optional
        The validation option (default is 'all').
    validatecommand : EntryValidateCommand, optional
        The command to run when validation is triggered (default is "").
    width : int, optional
        The width of the widget (default is 20).
    xscrollcommand : XYScrollCommand, optional
        The command to run when the widget is scrolled (default is "").
    """

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        widget: str | None = None,
        *,
        background: str = ...,  # undocumented
        class_: str = "",
        cursor: Cursor = ...,
        exportselection: bool = True,
        font: FontDescription = "TkTextFont",
        foreground: str = "",
        invalidcommand: EntryValidateCommand = "",
        justify: Literal["left", "center", "right"] = "left",
        name: str = ...,
        show: str = "",
        state: str = "normal",
        style: str = "",
        takefocus: TakeFocusValue = ...,
        textvariable: tk.DoubleVar = ...,
        validate: EntryValidateOptions = 'all',
        validatecommand: EntryValidateCommand = "",
        width: int = 20,
        xscrollcommand: XYScrollCommand = "",
    ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 widget: str | None = None,
                 *,
                 validate: EntryValidateOptions = 'all',
                 **kw) -> None: ...

    def __init__(self,
                 parent: tk.Misc,
                 widget: str | None = None,
                 *,
                 validate: EntryValidateOptions = 'all',
                 **kw) -> None:
        self.vcmd = parent.register(check_perc)
        self.ivcmd = parent.register(self.focus_set)

        super().__init__(parent,
                         widget,
                         invalidcommand=self.ivcmd,
                         validate=validate,
                         validatecommand=(self.vcmd, '%P'),
                         **kw)


class AddCombo(ttk.Combobox):
    """
    Combobox widget with additional functionality to change values.

    Parameters
    ----------
    parent : tk.Misc
        The parent widget.
    values : list[str]
        The list of values for the combobox.
    textvariable : tk.StringVar
        The variable to store the selected value.
    new_vals_command : Callable
        The command to generate new values for the combobox.
    background : str, optional
        The background color (default is undocumented).
    class_ : str, optional
        The class name (default is "").
    cursor : Cursor, optional
        The cursor type (default is "").
    exportselection : bool, optional
        Whether to export selection (default is True).
    font : FontDescription, optional
        The font description (default is undocumented).
    foreground : str, optional
        The foreground color (default is undocumented).
    height : int, optional
        The height of the combobox (default is 10).
    invalidcommand : EntryValidateCommand, optional
        The command to run when validation fails (default is undocumented).
    justify : Literal["left", "center", "right"], optional
        The justification of the text (default is "left").
    name : str, optional
        The name of the widget (default is None).
    postcommand : Callable[[], object] | str, optional
        The command to run when the combobox is posted (default is "").
    show : str, optional
        The character to display instead of the actual text (default is undocumented).
    state : Literal['normal', 'readonly', 'disabled'], optional
        The state of the widget (default is "normal").
    style : str, optional
        The style of the widget (default is "").
    takefocus : TakeFocusValue, optional
        Whether the widget can take focus (default is None).
    validate : EntryValidateOptions, optional
        The validation option (default is 'focusout').
    validatecommand : Callable | None, optional
        The command to run when validation is triggered (default is None).
    width : int, optional
        The width of the widget (default is 20).
    xscrollcommand : XYScrollCommand, optional
        The command to run when the widget is scrolled (default is undocumented).
    """

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        values: list[str],
        textvariable: tk.StringVar,
        new_vals_command: Callable,
        *,
        background: str = ...,  # undocumented
        class_: str = "",
        cursor: Cursor = "",
        exportselection: bool = True,
        font: FontDescription = ...,  # undocumented
        foreground: str = ...,  # undocumented
        height: int = 10,
        invalidcommand: EntryValidateCommand = ...,  # undocumented
        justify: Literal["left", "center", "right"] = "left",
        name: str = ...,
        postcommand: Callable[[], object] | str = "",
        show=...,  # undocumented
        state: Literal['normal', 'readonly', 'disabled'] = "normal",
        style: str = "",
        takefocus: TakeFocusValue = ...,
        validate: EntryValidateOptions = 'focusout',  # undocumented
        validatecommand: Callable | None = None,  # undocumented
        width: int = 20,
        xscrollcommand: XYScrollCommand = ...,  # undocumented
    ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 values: list[str],
                 textvariable: tk.StringVar,
                 new_vals_command: Callable,
                 *,
                 state: Literal['normal', 'readonly', 'disabled'] = 'normal',
                 validatecommand: Callable | None = None,
                 validate: EntryValidateOptions = 'focusout',
                 **kw): ...

    def __init__(self,
                 parent: tk.Misc,
                 values: list[str],
                 textvariable: tk.StringVar,
                 new_vals_command: Callable[[], list[str]],
                 *,
                 state: Literal['normal', 'readonly', 'disabled'] = 'normal',
                 validatecommand: Callable | None = None,
                 validate: EntryValidateOptions = 'focusout',
                 **kw):
        self.ivcmd = parent.register(self.focus_set)
        self.pcmd = parent.register(self.change_vals)
        self.new_vals = new_vals_command

        if validatecommand is not None:
            self.vcmd = parent.register(validatecommand)
            super().__init__(parent,
                             values=values,
                             textvariable=textvariable,
                             state=state,
                             invalidcommand=self.ivcmd,
                             validate=validate,
                             validatecommand=(self.vcmd, '%P'),
                             postcommand=self.pcmd,
                             **kw)

        else:
            super().__init__(parent,
                             values=values,
                             textvariable=textvariable,
                             state=state,
                             invalidcommand=self.ivcmd,
                             validate=validate,
                             postcommand=self.pcmd,
                             **kw)

    def change_vals(self):
        """
        Change the values of the combobox.
        """
        self.config(values=self.new_vals())
