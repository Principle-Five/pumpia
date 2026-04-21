import logging
import tkinter as tk
from tkinter import ttk
from typing import overload, Any
from collections.abc import Mapping

from pumpia.widgets.typing import ScreenUnits

LOG_LEVELS_MAP = logging.getLevelNamesMapping()
LOG_LEVELS_MAP.pop('WARN', 0)
LOG_LEVELS_MAP.pop('FATAL', 0)
LOG_LEVELS_MAP.pop('NOTSET', 0)
LOG_LEVELS = list(LOG_LEVELS_MAP.values())
LOG_LEVELS_STRINGS = ["ALL"] + list(LOG_LEVELS_MAP.keys())


class TextBoxHandler(logging.Handler):
    def __init__(self, parent: tk.Misc, level: int | str = 0, label_text: str = "Logger") -> None:
        super().__init__(level)
        self.setFormatter(logging.Formatter(fmt="{levelname: >8}: {message}", style="{"))

        self.records: list[logging.LogRecord] = []

        self.frame = ttk.Labelframe(parent, text=label_text)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        self.options_frame = ttk.Frame(self.frame)
        self.options_frame.grid(column=0, row=0, sticky=tk.NW)

        self.options_label = ttk.Label(self.options_frame, text="Logging Level: ")
        self.options_label.grid(column=0, row=0, sticky=tk.NE)

        self.options_var = tk.StringVar(self.options_frame, LOG_LEVELS_STRINGS[0])
        self.options_var.trace_add('write', self.switch_levels)
        self.options_box = ttk.Combobox(self.options_frame,
                                        values=LOG_LEVELS_STRINGS,
                                        state="readonly",
                                        textvariable=self.options_var)
        self.options_box.grid(column=1, row=0, sticky=tk.NW)

        self.lower_levels_label = ttk.Label(self.options_frame, text="Show Lower Levels: ")
        self.lower_levels_label.grid(column=0, row=1, sticky=tk.NE)

        self.lower_levels_var = tk.BooleanVar(self.options_frame, True)
        self.lower_levels_var.trace_add('write', self.switch_levels)
        self.lower_levels_entry = ttk.Checkbutton(self.options_frame,
                                                  variable=self.lower_levels_var)
        self.lower_levels_entry.grid(column=1, row=1, sticky=tk.NW)

        self.textbox_frame = ttk.Frame(self.frame)
        self.textbox_frame.grid(column=0, row=1, sticky=tk.NSEW)

        self.textbox_frame.columnconfigure(0, weight=1)
        self.textbox_frame.rowconfigure(0, weight=1)

        self.textbox = tk.Text(self.textbox_frame,
                               state=tk.DISABLED,
                               width=1,
                               height=1,
                               wrap="none")
        self.textbox.grid(column=0, row=0, sticky=tk.NSEW)

        self.xscrlbr = ttk.Scrollbar(self.textbox_frame,
                                     orient='horizontal',
                                     command=self.textbox.xview)
        self.xscrlbr.grid(column=0, row=1, sticky=tk.EW, columnspan=2)

        self.yscrlbr = ttk.Scrollbar(self.textbox_frame,
                                     command=self.textbox.yview)
        self.yscrlbr.grid(column=1, row=0, sticky=tk.NS)

        self.textbox.config(xscrollcommand=self.xscrlbr.set,
                            yscrollcommand=self.yscrlbr.set)

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        self.add_new_log(self.format(record))

    def add_new_log(self, text: str):
        self.textbox.configure(state=tk.NORMAL)
        self.textbox.insert(tk.END, text + "\n")
        self.textbox.configure(state=tk.DISABLED)

    def clear_log(self):
        self.textbox.configure(state=tk.NORMAL)
        self.textbox.delete(1.0, tk.END)
        self.textbox.configure(state=tk.DISABLED)

    def switch_levels(self, *_: str):
        self.clear_log()
        include_lower = self.lower_levels_var.get()
        level = LOG_LEVELS_MAP.get(self.options_var.get(), 0)
        text = ""
        for record in self.records:
            if (level == 0
                or record.levelno == level
                    or (include_lower and (record.levelno > level))):
                text = text + self.format(record) + "\n"
        self.add_new_log(text)

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
        self.frame.grid(*args, **kwargs)
