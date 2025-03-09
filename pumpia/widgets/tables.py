"""
Classes:
 * SimpleTable
 """

import tkinter as tk
from tkinter import ttk
import math
from typing import overload

from pumpia.widgets.typing import ScreenUnits, Cursor, Padding, Relief, TakeFocusValue


class SimpleTable(ttk.Frame):
    """
    Table widget for use with tkinter

    Attributes
    ----------
    parent: tk.Frame like
        the parent widget

    x_scroll: boolean
        tag for if the x scroll bar is shown, cannot be changed after creation

    y_scroll: boolean
        tag for if the y scroll bar is shown, cannot be changed after creation

    titles: list[string]
        a list of the column titles

    entries: list[list[string]]
        a 2 dimensional array of the cell values

    title_labels: list[tk.Label]
        a list of the column title tkinter labels, accessed [row][column]

    entry_labels: list[list[tk.Label]]
        a 2 dimensional array of the cell value tkinter labels, accessed [row][column]


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
        titles: list[str],
        y_scroll: bool = True,
        x_scroll: bool = True,
        *,
        border: ScreenUnits = ...,
        borderwidth: ScreenUnits = ...,
        class_: str = "",
        cursor: Cursor = "",
        height: ScreenUnits = 0,
        name: str = ...,
        padding: Padding = ...,
        relief: Relief = ...,
        style: str = "",
        takefocus: TakeFocusValue = "",
        width: ScreenUnits = 0,
    ) -> None: ...

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        titles: list[str],
        y_scroll: bool = True,
        x_scroll: bool = True,
        **kw): ...

    def __init__(self,
                 parent: tk.Misc,
                 titles: list[str],
                 y_scroll: bool = True,
                 x_scroll: bool = True,
                 **kw):
        """
        Initialises the SimpleTable widget

        Parameters
        ----------
        parent : frame like
            parent widget of table
        titles : list[str]
            column titles
        y_scroll : bool, optional
            boolean to show y scroll bar, by default True
        x_scroll : bool, optional
            boolean to show x scroll bar, by default True

        *args and **kw get passed to super tkinter frame class
        """

        super().__init__(parent, **kw)
        self.parent = parent
        self.x_scroll = x_scroll
        self.y_scroll = y_scroll
        self.titles = titles
        self.entries: list[list[str]] = []
        self.title_labels: list[tk.Label] = []
        self.entry_labels: list[list[tk.Label]] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.xscrlbr = ttk.Scrollbar(self, orient='horizontal')
        if x_scroll:
            self.xscrlbr.grid(column=0, row=2, columnspan=2, sticky='ew')
        self.yscrlbr = ttk.Scrollbar(self)
        if y_scroll:
            self.yscrlbr.grid(column=1, row=0, sticky='ns')

        self.out_canv = tk.Canvas(self)
        self.out_canv.config(relief='flat',
                             width=10,
                             height=10, bd=0)
        self.out_canv.grid(column=0, row=0, sticky='nsew')
        self.out_frame = ttk.Frame(self)
        self.out_canv.create_window(0, 0, window=self.out_frame, anchor='nw')
        self.out_canv.config(xscrollcommand=self.xscrlbr.set,
                             scrollregion=(0, 0, 100, 100))

        self.tab_canv = tk.Canvas(self.out_frame)
        self.tab_canv.config(relief='flat',
                             width=10,
                             height=10, bd=-2)  # -2 needed as canvas has default border of 2
        self.tab_canv.grid(column=0, row=1, columnspan=len(titles) + 1, sticky='nsew')
        self.tab_frame = ttk.Frame(self.out_frame)
        self.tab_canv.create_window(0, 0, window=self.tab_frame, anchor='nw')
        self.tab_canv.config(yscrollcommand=self.yscrlbr.set,
                             scrollregion=(0, 0, 100, 100))

        self.xscrlbr.lift(self.out_frame)
        self.yscrlbr.lift(self.tab_frame)
        self.bind('<Configure>', self._configure_window)
        self.tab_frame.bind('<Configure>', self._configure_window)
        self.tab_frame.bind('<Enter>', self._bound_to_mousewheel)
        self.tab_frame.bind('<Leave>', self._unbound_to_mousewheel)

        self.xscrlbr.config(command=self.out_canv.xview)
        self.yscrlbr.config(command=self.tab_canv.yview)
        ####
        for t in range(len(self.titles)):
            self.title_labels.append(tk.Label(self.out_frame,
                                              text=titles[t],
                                              borderwidth=0.5,
                                              relief="solid"))
            self.title_labels[-1].grid(row=0, column=t, sticky='nsew')
            self.out_frame.grid_columnconfigure(t, weight=1)
            self.tab_frame.grid_columnconfigure(t, weight=1)

        self.out_frame.grid_rowconfigure(1, weight=1)

    def add_row(self, entry: list[str], new: bool = True):
        """
        add a row to the end of the table

        Parameters
        ----------
        entry : list[str]
            a list containing each column entry for the row

        new : boolean
            True if the entry is a new row. False if it is not, e.g. if it is part of a redrawing

        Raises
        ------
        RowLengthError
            error if entry does does not have the correct amount of columns
        """
        if len(entry) != len(self.titles):
            raise ValueError("Incorrect number of columns in Row")

        row = len(self.entry_labels)
        self.tab_frame.grid_rowconfigure(row, weight=1)
        new_row = []
        for e, _ in enumerate(entry):
            new_row.append(tk.Label(self.tab_frame, text=entry[e], borderwidth=0.5, relief="solid"))
            new_row[-1].grid(row=row, column=e, sticky='nsew')
        if new:
            self.entries.append(entry)
        self.entry_labels.append(new_row)

    def redraw(self):
        """
        redraw the table
        """
        for row in self.entry_labels:
            for column in row:
                column.grid_forget()

        self.entry_labels = []
        for row in self.entries:
            self.add_row(row, False)

    def delete_row(self, index: int):
        """
        deletes row 'index' from the table. First row is at index=0

        Parameters
        ----------
        index : int
            the index of the row to be deleted
        """
        del self.entries[index]
        self.redraw()

    def change_title(self, new_title: str, index: int):
        """
        Change the title of column 'index'

        Parameters
        ----------
        new_title : str
            new column name
        index : int
            index of column. First column is index=0
        Raises
        ------
        IndexError
            if index given is too big
        """
        if index >= len(self.titles) or index < 0:
            raise IndexError

        self.titles[index] = new_title
        self.title_labels[index].config(text=new_title)

    def _configure_window(self, _):

        # function changes tab_frame size so need to unbind to avoid infinite loop
        self.tab_frame.unbind_all('<Configure>')

        # make title columns same size as table columns
        if len(self.entry_labels) > 0:
            for c in range(len(self.titles)):
                self.entry_labels[0][c].update_idletasks()
                self.title_labels[c].update_idletasks()
                if self.entry_labels[0][c].winfo_width() > self.title_labels[c].winfo_reqwidth():
                    pad = (self.entry_labels[0][c].winfo_width()
                           - self.title_labels[c].winfo_reqwidth()) / 2
                    self.title_labels[c].grid_configure(ipadx=math.floor(pad))
                elif self.entry_labels[0][c].winfo_width() < self.title_labels[c].winfo_reqwidth():
                    pad = (self.title_labels[c].winfo_reqwidth()
                           - self.entry_labels[0][c].winfo_width()) / 2
                    self.entry_labels[0][c].grid_configure(ipadx=math.ceil(pad))
                    # ceil here prevents loops due to width vs reqwidth being used

        # update the scrollbars to match the size of the inner frame
        tab_size = (self.tab_frame.winfo_reqwidth(), self.tab_frame.winfo_reqheight())
        self.tab_canv.config(scrollregion=(0, 0, tab_size[0], tab_size[1]))
        if self.tab_frame.winfo_reqwidth() != self.tab_canv.winfo_width():
            # update the canvas's width to fit the inner frame
            self.tab_canv.config(width=tab_size[0])

        if self.tab_frame.winfo_reqheight() != self.tab_canv.winfo_height():
            # update the canvas's height to fit the inner frame
            self.tab_canv.config(height=tab_size[1])

        # update the scrollbars to match the size of the inner frame
        out_size = (self.out_frame.winfo_reqwidth(), self.out_frame.winfo_reqheight())
        self.out_canv.config(scrollregion=(0, 0, out_size[0], out_size[1]))
        if self.out_frame.winfo_reqwidth() != self.out_canv.winfo_width():
            # update the canvas's width to fit the inner frame
            self.out_canv.config(width=out_size[0])

        if self.out_frame.winfo_reqheight() != self.out_canv.winfo_height():
            # update the canvas's height to fit the inner frame
            self.out_canv.config(height=out_size[1])

        self.tab_canv.config(height=self.out_canv.winfo_height()
                             - self.title_labels[0].winfo_height())

        # need to rebind
        self.tab_frame.bind('<Configure>', self._configure_window)

    def _bound_to_mousewheel(self, _):
        self.tab_canv.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, _):
        self.tab_canv.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if self.tab_canv.winfo_height() < self.tab_frame.winfo_reqheight():
            direction = 0
            if event.num == 5 or event.delta == -120:
                direction = 1
            elif event.num == 4 or event.delta == 120:
                direction = -1
            self.tab_canv.yview_scroll(direction, "units")
