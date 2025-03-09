"""
Classes:
 * ScrolledWindow
"""

import tkinter as tk
from tkinter import ttk
from typing import overload, Any
from collections.abc import Mapping

from pumpia.widgets.typing import ScreenUnits, Cursor, Padding, Relief, TakeFocusValue


class ScrolledWindow(ttk.Frame):
    """
    A frame with scrollbars that automatically adjust to the size of the content.

    Parameters
    ----------
    parent : tk.Misc
        The parent widget.
    y_scroll : bool, optional
        Whether to enable vertical scrolling (default is True).
    x_scroll : bool, optional
        Whether to enable horizontal scrolling (default is True).
    border : ScreenUnits, optional
        The border size (default is None).
    borderwidth : ScreenUnits, optional
        The border width (default is None).
    class_ : str, optional
        The class name (default is "").
    cursor : Cursor, optional
        The cursor type (default is "").
    height : ScreenUnits, optional
        The height of the frame (default is 0).
    name : str, optional
        The name of the frame (default is None).
    padding : Padding, optional
        The padding of the frame (default is None).
    relief : Relief, optional
        The relief style (default is None).
    style : str, optional
        The style of the frame (default is "").
    takefocus : TakeFocusValue, optional
        The take focus value (default is "").
    underline : int, optional
        The underline position (default is -1).
    width : ScreenUnits, optional
        The width of the frame (default is 0).

    Notes
    -----
    For parent widgets such as paned window where it is managed through .add
    use `ScrolledWindow.outer_frame` as the child argument
    """

    @overload
    def __init__(self,
                 parent: tk.Misc,
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
    def __init__(self, parent: tk.Misc, y_scroll: bool = True, x_scroll: bool = True, **kw): ...

    def __init__(self, parent: tk.Misc, y_scroll: bool = True, x_scroll: bool = True, **kw):
        self.outer_frame = ttk.Frame(parent, **kw)
        self.parent = parent
        self.x_scroll = x_scroll
        self.y_scroll = y_scroll

        self.outer_frame.columnconfigure(0, weight=1)
        self.outer_frame.rowconfigure(0, weight=1)
        # creating a scrollbars
        self.xscrlbr = ttk.Scrollbar(self.outer_frame, orient='horizontal')
        if x_scroll:
            self.xscrlbr.grid(column=0, row=1, sticky='ew', columnspan=2)
        self.yscrlbr = ttk.Scrollbar(self.outer_frame)
        if y_scroll:
            self.yscrlbr.grid(column=1, row=0, sticky='ns')
        # creating a canvas
        self.canv = tk.Canvas(self.outer_frame)
        self.canv.config(relief='flat',
                         width=10,
                         height=10, bd=2)
        # placing a canvas into frame
        self.canv.grid(column=0, row=0, sticky='nsew')
        # associating scrollbar commands to canvas scrolling
        self.xscrlbr.config(command=self.canv.xview)
        self.yscrlbr.config(command=self.canv.yview)

        # when super call is put at top then widgets within scrolled window are not visible
        super().__init__(self.outer_frame, **kw)  # ordering of widget creation matters?

        self.canv.create_window(0, 0, window=self, anchor='nw')

        self.canv.config(xscrollcommand=self.xscrlbr.set,
                         yscrollcommand=self.yscrlbr.set,
                         scrollregion=(0, 0, 100, 100))

        self.yscrlbr.lift(self)
        self.xscrlbr.lift(self)
        self.bind('<Configure>', self._configure_window)
        self.bind('<Enter>', self._bound_to_mousewheel)
        self.bind('<Leave>', self._unbound_to_mousewheel)

    def _bound_to_mousewheel(self, _: tk.Event):
        """
        Binds the mouse wheel to the canvas for scrolling.

        Parameters
        ----------
        _ : tk.Event
            The event object.
        """
        self.canv.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, _: tk.Event):
        """
        Unbinds the mouse wheel from the canvas.

        Parameters
        ----------
        _ : tk.Event
            The event object.
        """
        self.canv.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event: tk.Event):
        """
        Handles mouse wheel events for scrolling.

        Parameters
        ----------
        event : tk.Event
            The event object.
        """
        if self.outer_frame.winfo_height() < self.winfo_reqheight():
            direction = 0
            if event.num == 5 or event.delta == -120:
                direction = 1
            elif event.num == 4 or event.delta == 120:
                direction = -1
            self.canv.yview_scroll(direction, "units")

    def _configure_window(self, _: tk.Event):
        """
        Configures the window to update the scroll region.

        Parameters
        ----------
        _ : tk.Event
            The event object.
        """
        # update the scrollbars to match the size of the inner frame
        self.canv.config(scrollregion=(0,
                                       0,
                                       self.winfo_reqwidth(),
                                       self.winfo_reqheight()))
        if self.winfo_reqwidth() != self.canv.winfo_width():
            # update the canvas's width to fit the inner frame
            self.canv.config(width=self.winfo_reqwidth())

        if self.winfo_reqheight() != self.canv.winfo_height():
            # update the canvas's height to fit the inner frame
            self.canv.config(height=self.winfo_reqheight())

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

        Parameters
        ----------
        *args : tuple
            Positional arguments for the grid method.
        **kwargs : dict
            Keyword arguments for the grid method.
        """
        self.outer_frame.grid(*args, **kwargs)
