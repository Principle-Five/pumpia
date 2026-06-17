"""
Some Treeview widgets with extra functionality.
Contains:
*SearchTreeview
*DiffTreeview
"""

import tkinter as tk
from tkinter import ttk
from typing import overload, Literal, Any
from collections.abc import Callable, Mapping

from pumpia.widgets.typing import ScreenUnits, Cursor, Padding


class SearchTreeview(ttk.Treeview):
    """
    Creates a frame with a treeview and linked search bar.

    WARNING: For parent widgets such as paned window where it is managed through `add`
    use `SearchTreeview.outer_frame` as the child argument.

    Attributes
    ----------
    parent: ttk.Frame like
        the parent widget

    x_scroll: boolean
        tag for if the x scroll bar is shown, cannot be changed after creation

    y_scroll: boolean
        tag for if the y scroll bar is shown, cannot be changed after creation


    treeview: ttk.Treeview
        The underlying treeview object


    Methods
    ----------
    add_row
        add a row to the end of the table

    redraw
        redraws the table

    delete_row
        delete a specified row from the table

    change_title
        change the title of a specified column
    """
    @overload
    def __init__(
        self,
        parent: tk.Misc,
        y_scroll: bool = True,
        x_scroll: bool = True,
        *,
        class_: str = "",
        columns: (str
                  | list[str]
                  | list[int]
                  | list[str | int]
                  | tuple[str | int, ...]) = "",
        cursor: Cursor = "",
        displaycolumns: (str
                         | int
                         | list[str]
                         | tuple[str, ...]
                         | list[int]
                         | tuple[int, ...]) = ("#all",),
        height: int = 10,
        name: str = ...,
        padding: Padding = ...,
        selectmode: Literal["extended", "browse", "none"] = "extended",
        show: (Literal["tree", "headings", "tree headings", ""]
               | list[str]
               | tuple[str, ...]) = ("tree", "headings"),
        style: str = "",
        takefocus: bool | Literal[0, 1, ""] | Callable[[str], bool | None] = ...,
        xscrollcommand: str | Callable[[float, float], object] = "",
        yscrollcommand: str | Callable[[float, float], object] = "",
    ) -> None: ...

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        y_scroll: bool = True,
        x_scroll: bool = True,
        **kw): ...

    def __init__(self,
                 parent: tk.Misc,
                 y_scroll: bool = True,
                 x_scroll: bool = True,
                 **kw):

        self.x_scroll = x_scroll
        self.y_scroll = y_scroll

        self.outer_frame = ttk.Frame(parent)
        self.outer_frame.columnconfigure(1, weight=1)
        self.outer_frame.rowconfigure(1, weight=1)

        super().__init__(self.outer_frame, **kw)
        super().grid(column=0, row=1, columnspan=2, sticky=tk.NSEW)

        self.search_label = ttk.Label(self.outer_frame, text="Search:", anchor=tk.E)
        self.search_label.grid(column=0, row=0, sticky=tk.EW)
        self.search_var = tk.StringVar(self.outer_frame)
        self.search_var.trace_add('write', self.filter_tree)
        self.search_entry = ttk.Entry(self.outer_frame, textvariable=self.search_var)
        self.search_entry.grid(column=1, row=0, sticky=tk.EW)

        self.yscrollbar = ttk.Scrollbar(
            self.outer_frame, orient=tk.VERTICAL, command=self.yview)
        if self.y_scroll:
            self.configure(yscrollcommand=self.yscrollbar.set)
            self.yscrollbar.grid(row=1, column=2, sticky=tk.NS)

        self.xscrollbar = ttk.Scrollbar(
            self.outer_frame, orient=tk.HORIZONTAL, command=self.xview)
        if self.x_scroll:
            self.configure(xscrollcommand=self.xscrollbar.set)
            self.xscrollbar.grid(row=2, column=0, columnspan=3, sticky=tk.EW)

        self.entries: dict[str, str] = {}
        self.parents: dict[str, list[str]] = {}

    @overload
    def insert(self,
               parent: str,
               index: int | Literal['end'],
               iid: str | int | None = None,
               *,
               # pylint: disable-next=redefined-builtin
               id: str | int = ...,
               text: str = ...,
               image: tk.Image | str = ...,
               values: list[Any] | tuple[Any, ...] = ...,
               # pylint: disable-next=redefined-builtin
               open: bool = ...,
               tags: str | list[str] | tuple[str, ...] = ...,
               **kw) -> str: ...

    @overload
    def insert(self,
               parent: str,
               index: int | Literal['end'],
               iid: str | int | None = None,
               **kw) -> str: ...

    def insert(self,
               parent: str,
               index: int | Literal['end'],
               iid: str | int | None = None,
               **kw) -> str:

        entry = super().insert(parent, index, iid, **kw)

        self.entries[entry] = parent
        if parent not in self.parents:
            self.parents[parent] = [entry]
        else:
            self.parents[parent].append(entry)

        return entry

    def add_parent_items(self, parent: str, *items: str):
        """
        Adds items to parent where both are str IDs of items in the treeview
        """
        for item in items:
            self.move(item, parent, 'end')
            self.item(item, open=False)
            if item in self.parents:
                self.add_parent_items(item, *self.parents[item])

    def filter_tree(self, *_):
        """
        Filters the tree based on the search
        """
        self.detach(*self.entries)
        text = self.search_var.get().lower()
        if text == "":
            self.add_parent_items("", *self.parents[""])
        else:
            for entry, parent in self.entries.items():
                item = self.item(entry)
                if (text in item["text"].lower()
                        or any([text in str(value).lower()  # value sometimes int (typehint is str)
                                for value in item["values"]])):
                    list_parents = [entry, parent]
                    while list_parents[-1] != "":
                        list_parents.append(self.entries[list_parents[-1]])

                    for index, included in enumerate(reversed(list_parents[0:-1])):
                        if self.bbox(included) == "":
                            self.see(included)  # makes visible if in tree
                            if self.bbox(included) == "":  # will only be "" here if not in tree
                                self.move(included, list_parents[-(index + 1)], 'end')

                        if included != entry:
                            self.item(included, open=True)
                        else:
                            self.item(included, open=False)
                            if entry in self.parents:
                                self.add_parent_items(entry, *self.parents[entry])

        if self.y_scroll:
            self.yview_moveto(0)

    @overload
    def grid(self,
             cnf: Mapping[str, Any] | None = None,
             *,
             column: int = ...,
             columnspan: int = ...,
             row: int = ...,
             rowspan: int = ...,
             ipadx: ScreenUnits = ...,
             ipady: ScreenUnits = ...,
             padx: ScreenUnits | tuple[ScreenUnits, ScreenUnits] = ...,
             pady: ScreenUnits | tuple[ScreenUnits, ScreenUnits] = ...,
             sticky: str = ...,  # consists of letters 'n', 's', 'w', 'e', may contain repeats or ""
             in_: tk.Misc = ...,
             **kw,  # allow keyword argument named 'in', see #4836
             ) -> None: ...

    @overload
    def grid(self,
             *args,
             **kwargs) -> None: ...

    def grid(self,
             *args,
             **kwargs) -> None:
        """
        Places the widget on the grid.
        """
        self.outer_frame.grid(*args, **kwargs)


class DiffTreeview(ttk.Treeview):
    """
    Creates a frame with a treeview and linked search bar and option to only show different values.

    WARNING: For parent widgets such as paned window where it is managed through `add`
    use `DiffTreeview.outer_frame` as the child argument.

    Attributes
    ----------
    parent: ttk.Frame like
        the parent widget

    x_scroll: boolean
        tag for if the x scroll bar is shown, cannot be changed after creation

    y_scroll: boolean
        tag for if the y scroll bar is shown, cannot be changed after creation


    treeview: ttk.Treeview
        The underlying treeview object


    Methods
    ----------
    add_row
        add a row to the end of the table

    redraw
        redraws the table

    delete_row
        delete a specified row from the table

    change_title
        change the title of a specified column
    """
    @overload
    def __init__(
        self,
        parent: tk.Misc,
        y_scroll: bool = True,
        x_scroll: bool = True,
        *,
        diff_checks: list[bool] | None = None,
        class_: str = "",
        columns: (str
                  | list[str]
                  | list[int]
                  | list[str | int]
                  | tuple[str | int, ...]) = "",
        cursor: Cursor = "",
        displaycolumns: (str
                         | int
                         | list[str]
                         | tuple[str, ...]
                         | list[int]
                         | tuple[int, ...]) = ("#all",),
        height: int = 10,
        name: str = ...,
        padding: Padding = ...,
        selectmode: Literal["extended", "browse", "none"] = "extended",
        show: (Literal["tree", "headings", "tree headings", ""]
               | list[str]
               | tuple[str, ...]) = ("tree", "headings"),
        style: str = "",
        takefocus: bool | Literal[0, 1, ""] | Callable[[str], bool | None] = ...,
        xscrollcommand: str | Callable[[float, float], object] = "",
        yscrollcommand: str | Callable[[float, float], object] = "",
    ) -> None: ...

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        y_scroll: bool = True,
        x_scroll: bool = True,
        *,
        diff_checks: list[bool] | None = None,
        **kw): ...

    def __init__(self,
                 parent: tk.Misc,
                 y_scroll: bool = True,
                 x_scroll: bool = True,
                 *,
                 diff_checks: list[bool] | None = None,
                 **kw):

        self.x_scroll = x_scroll
        self.y_scroll = y_scroll

        self.outer_frame = ttk.Frame(parent)
        self.outer_frame.columnconfigure(1, weight=1)
        self.outer_frame.rowconfigure(2, weight=1)

        super().__init__(self.outer_frame, **kw)
        super().grid(column=0, row=2, columnspan=2, sticky=tk.NSEW)

        if (diff_checks is not None
            and "columns" in kw
                and not isinstance(kw["columns"], str)):
            if len(diff_checks) != len(kw["columns"]):
                raise ValueError("diff_checks must be the same length as columns")
        elif (diff_checks is None
              and "columns" in kw
              and not isinstance(kw["columns"], str)):
            diff_checks = [True for _ in kw["columns"]]
        else:
            diff_checks = [True]

        self.diff_checks: list[bool] = diff_checks

        self.search_label = ttk.Label(self.outer_frame, text="Search:", anchor=tk.E)
        self.search_label.grid(column=0, row=0, sticky=tk.EW)
        self.search_var = tk.StringVar(self.outer_frame)
        self.search_var.trace_add('write', self.filter_tree)
        self.search_entry = ttk.Entry(self.outer_frame, textvariable=self.search_var)
        self.search_entry.grid(column=1, row=0, sticky=tk.EW)

        self.diff_label = ttk.Label(self.outer_frame, text="Show Same Values", anchor=tk.E)
        self.diff_label.grid(column=0, row=1, sticky=tk.EW)
        self.diff_var = tk.BooleanVar(self.outer_frame, True)
        self.diff_var.trace_add('write', self.filter_tree)
        self.diff_entry = ttk.Checkbutton(self.outer_frame, variable=self.diff_var)
        self.diff_entry.grid(column=1, row=1, sticky=tk.EW)

        self.yscrollbar = ttk.Scrollbar(
            self.outer_frame, orient=tk.VERTICAL, command=self.yview)
        if self.y_scroll:
            self.configure(yscrollcommand=self.yscrollbar.set)
            self.yscrollbar.grid(row=2, column=2, sticky=tk.NS)

        self.xscrollbar = ttk.Scrollbar(
            self.outer_frame, orient=tk.HORIZONTAL, command=self.xview)
        if self.x_scroll:
            self.configure(xscrollcommand=self.xscrollbar.set)
            self.xscrollbar.grid(row=3, column=0, columnspan=3, sticky=tk.EW)

        self.entries: dict[str, str] = {}
        self.parents: dict[str, list[str]] = {}

    @overload
    def insert(self,
               parent: str,
               index: int | Literal['end'],
               iid: str | int | None = None,
               *,
               # pylint: disable-next=redefined-builtin
               id: str | int = ...,
               text: str = ...,
               image: tk.Image | str = ...,
               values: list[Any] | tuple[Any, ...] = ...,
               # pylint: disable-next=redefined-builtin
               open: bool = ...,
               tags: str | list[str] | tuple[str, ...] = ...,
               **kw) -> str: ...

    @overload
    def insert(self,
               parent: str,
               index: int | Literal['end'],
               iid: str | int | None = None,
               **kw) -> str: ...

    def insert(self,
               parent: str,
               index: int | Literal['end'],
               iid: str | int | None = None,
               **kw) -> str:

        entry = super().insert(parent, index, iid, **kw)

        self.entries[entry] = parent
        if parent not in self.parents:
            self.parents[parent] = [entry]
        else:
            self.parents[parent].append(entry)

        return entry

    def add_parent_items(self, parent: str, *items: str):
        """
        Adds items to parent where both are str IDs of items in the treeview
        """
        for item in items:
            self.move(item, parent, 'end')
            self.item(item, open=False)
            if item in self.parents:
                self.add_parent_items(item, *self.parents[item])

    def filter_tree(self, *_):
        """
        Filters the tree based on the search and diff checkbox
        """
        self.detach(*self.entries)
        text = self.search_var.get().strip().lower()
        show_same = self.diff_var.get()
        if text == "" and show_same:
            self.add_parent_items("", *self.parents[""])
        else:
            for entry, parent in self.entries.items():
                show = True
                item = self.item(entry)
                if not show_same:
                    values = [value
                              for i, value in enumerate(item["values"])
                              if self.diff_checks[i]]
                    if len(values) > 1:
                        show = not all(value == values[0] for value in values[1:])
                    elif len(values) == 0:
                        show = False
                if show and (text in item["text"].lower()
                             or any(text in str(value).lower()  # typehint is str sometimes is not
                                    for value in item["values"])):
                    list_parents = [entry, parent]
                    while list_parents[-1] != "":
                        list_parents.append(self.entries[list_parents[-1]])

                    for index, included in enumerate(reversed(list_parents[0:-1])):
                        if self.bbox(included) == "":
                            self.see(included)  # makes visible if in tree
                            if self.bbox(included) == "":  # will only be "" here if not in tree
                                self.move(included, list_parents[-(index + 1)], 'end')

                        if included != entry:
                            self.item(included, open=True)
                        else:
                            self.item(included, open=False)
                            if entry in self.parents:
                                self.add_parent_items(entry, *self.parents[entry])

        if self.y_scroll:
            self.yview_moveto(0)

    @overload
    def grid(self,
             cnf: Mapping[str, Any] | None = None,
             *,
             column: int = ...,
             columnspan: int = ...,
             row: int = ...,
             rowspan: int = ...,
             ipadx: ScreenUnits = ...,
             ipady: ScreenUnits = ...,
             padx: ScreenUnits | tuple[ScreenUnits, ScreenUnits] = ...,
             pady: ScreenUnits | tuple[ScreenUnits, ScreenUnits] = ...,
             sticky: str = ...,  # consists of letters 'n', 's', 'w', 'e', may contain repeats or ""
             in_: tk.Misc = ...,
             **kw,  # allow keyword argument named 'in', see #4836
             ) -> None: ...

    @overload
    def grid(self,
             *args,
             **kwargs) -> None: ...

    def grid(self,
             *args,
             **kwargs) -> None:
        """
        Places the widget on the grid.
        """
        self.outer_frame.grid(*args, **kwargs)
