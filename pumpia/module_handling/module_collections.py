"""
Classes:
 * BaseCollection
 * OutputFrame
 * WindowGroup
"""

from abc import ABC
import tkinter as tk
from tkinter import ttk
from typing import overload, Literal, Self, Any
from collections.abc import Callable
from copy import copy
from pumpia.utilities.typing import DirectionType
from pumpia.utilities.tkinter_utils import tk_copy
from pumpia.image_handling.image_structures import ArrayImage
from pumpia.widgets.typing import ScreenUnits, Cursor, Padding, Relief, TakeFocusValue
from pumpia.widgets.context_managers import (BaseContextManager,
                                             BaseContextManagerGenerator,
                                             SimpleContextManagerGenerator)
from pumpia.widgets.scrolled_window import ScrolledWindow
from pumpia.widgets.viewers import BaseViewer
from pumpia.module_handling.in_outs.simple import BaseIO
from pumpia.module_handling.in_outs.viewer_ios import BaseViewerIO
from pumpia.module_handling.modules import BaseModule
from pumpia.module_handling.manager import Manager
from pumpia.module_handling.context import BaseContext


class OutputFrame(ttk.Labelframe):
    """
    A frame for displaying output values.

    Parameters
    ----------
    parent : tk.Misc or None, optional
        The parent widget (default is None).
    verbose_name : str or None, optional
        The verbose name of the frame (default is None).
    direction : DirectionType, optional
        The direction of the child widgets in the frame (default is vertical).
    **kw : dict
        Additional keyword arguments as defined by ttk Labelframe.

    Attributes
    ----------
    verbose_name : str or None
        The verbose name of the frame.
    parent : tk.Misc or None
        The parent widget.
    is_setup : bool
    var_values : list
    var_strings : list[str]
    horizontal_str : str
    vertical_str : str

    Methods
    -------
    set_parent(parent: tk.Misc)
        Sets the parent widget.
    setup(parent: tk.Misc | None = None, verbose_name: str | None = None)
        Sets up the frame.
    copy_horizontal() -> None
        Copies the horizontal string representation of the variable values to the clipboard.
    copy_vertical() -> None
        Copies the vertical string representation of the variable values to the clipboard.
    register_output(output: BaseIO, verbose_name: str | None = None) -> None
        Registers an output variable in the frame.
    """

    @overload
    def __init__(
        self,
        parent: tk.Misc | None = None,
        *,
        verbose_name: str | None = None,
        direction: DirectionType = "V",
        border: ScreenUnits = ...,
        borderwidth: ScreenUnits = ...,  # undocumented
        class_: str = "",
        cursor: Cursor = "",
        height: ScreenUnits = 0,
        labelanchor: Literal["nw", "n", "ne",
                             "en", "e", "es",
                             "se", "s", "sw",
                             "ws", "w", "wn"] = ...,
        labelwidget: tk.Misc = ...,
        padding: Padding = ...,
        relief: Relief = ...,  # undocumented
        style: str = "",
        takefocus: TakeFocusValue = "",
        underline: int = -1,
        width: ScreenUnits = 0,
    ) -> None: ...

    @overload
    def __init__(
        self,
        parent: tk.Misc | None = None,
        *,
        verbose_name: str | None = None,
        direction: DirectionType = "V",
        **kw) -> None: ...

    # pylint: disable-next=super-init-not-called
    def __init__(
            self,
            parent: tk.Misc | None = None,
            *,
            verbose_name: str | None = None,
            direction: DirectionType = "V",
            **kw):
        self.verbose_name = verbose_name
        self.parent = parent
        self._kw = kw
        self._vars: list[tk.Variable] = []
        self._labels: list[ttk.Label] = []
        self._out_labs: list[ttk.Label] = []
        self._is_setup: bool = False

        if direction[0].lower() == "h":
            self.direction: Literal["horizontal", "vertical"] = "horizontal"
        else:
            self.direction: Literal["horizontal", "vertical"] = "vertical"

        if self.parent is not None:
            self.setup()

    @property
    def is_setup(self) -> bool:
        """
        Whether the frame is set up.
        """
        return self._is_setup

    def set_parent(self, parent: tk.Misc):
        """
        Sets the parent widget.
        """
        self.parent = parent

    def setup(self, *, parent: tk.Misc | None = None, verbose_name: str | None = None):
        """
        Sets up the frame.
        Parent and verbose_name must be set before calling this method or provided as arguments.
        If they are provided then they override the values set before calling this method.

        Parameters
        ----------
        parent : tk.Misc or None, optional
            The parent widget (default is None).
        verbose_name : str or None, optional
            The verbose name of the frame (default is None).
        """
        if not self._is_setup:
            if parent is not None:
                self.parent = parent
            if verbose_name is not None:
                self.verbose_name = verbose_name
            if self.parent is None:
                raise ValueError("parent needs to be set using set_parent or provided")
            if self.verbose_name is None:
                raise ValueError("name needs to be provided or set as string")
            super().__init__(self.parent, text=self.verbose_name, **self._kw)

            self.output_frame = ttk.Frame(self)
            self.output_frame.grid(column=0, row=0, sticky="nsew")

            self.button_frame = ttk.Frame(self)
            self.button_frame.grid(column=0, row=1, sticky="nsew")

            self.h_button = ttk.Button(self.button_frame,
                                       text="Copy Horizontal",
                                       command=self.copy_horizontal)
            self.v_button = ttk.Button(self.button_frame,
                                       text="Copy Vertical",
                                       command=self.copy_vertical)
            self.h_button.grid(column=0, row=0, sticky="nsew")
            self.v_button.grid(column=0, row=1, sticky="nsew")

            self._is_setup = True

    @property
    def var_values(self) -> list:
        """
        The values of the variables in the frame.
        """
        return [var.get() for var in self._vars]

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

    def register_output(self, output: BaseIO, verbose_name: str | None = None) -> None:
        """
        Registers an output variable in the frame.
        """
        if output.verbose_name is not None:
            if verbose_name is not None:
                self._labels.append(ttk.Label(self.output_frame, text=verbose_name))
            else:
                self._labels.append(ttk.Label(self.output_frame, textvariable=output.label_var))

            self._vars.append(output.value_var)
            self._out_labs.append(ttk.Label(self.output_frame, textvariable=output.value_var))

            if self.direction == "horizontal":
                self._labels[-1].grid(column=2 * (len(self._vars) - 1),
                                      row=0,
                                      sticky="nsew")
                self._out_labs[-1].grid(column=2 * (len(self._vars) - 1) + 1,
                                        row=0,
                                        sticky="nsew")
            else:
                self._labels[-1].grid(column=0,
                                      row=len(self._vars) - 1,
                                      sticky="nsew")
                self._out_labs[-1].grid(column=1,
                                        row=len(self._vars) - 1,
                                        sticky="nsew")


class WindowGroup(ttk.Panedwindow):
    """
    A window for showing multiple modules.

    Parameters
    ----------
    modules : list of BaseModule
        The list of modules to display.
    verbose_name : str or None, optional
        The verbose name of the group (default is None).
    direction : DirectionType, optional
        The direction of the modules in the group (default is vertical).
    **kw : dict
        Additional keyword arguments as defined by ttk Panedwindow.

    Attributes
    ----------
    modules : list[BaseModule]
        The list of modules to display.
    verbose_name : str or None
        The verbose name of the group.
    direction : str
        The direction of the modules in the group.

    Methods
    -------
    setup(parent: tk.Misc, verbose_name: str | None = None)
        Sets up the window group.
    on_tab_select()
        Called when the tab containing this window is selected.
    """

    @overload
    def __init__(
        self,
        modules: list[BaseModule],
        verbose_name: str | None = None,
        *,
        direction: DirectionType = "V",
        border: ScreenUnits = ...,
        borderwidth: ScreenUnits = ...,
        class_: str = "",
        cursor: Cursor = "",
        height: ScreenUnits = 0,
        padding: Padding = ...,
        relief: Relief = ...,
        style: str = "",
        takefocus: TakeFocusValue = "",
        width: ScreenUnits = 0,
    ) -> None: ...

    @overload
    def __init__(
        self,
        modules: list[BaseModule],
        verbose_name: str | None = None,
        *,
        direction: DirectionType = "V",
        **kwargs) -> None: ...

    # pylint: disable-next=super-init-not-called
    def __init__(self,
                 modules: list[BaseModule],
                 verbose_name: str | None = None,
                 *,
                 direction: DirectionType = "V",
                 **kw) -> None:
        self.modules = modules
        self.verbose_name = verbose_name
        if direction[0].lower() == "h":
            self.direction = "horizontal"
        else:
            self.direction = "vertical"
        self.kw = kw

    def setup(self, parent: tk.Misc, verbose_name: str | None = None):
        """
        Sets up the window group.
        verbose_name must be set before calling this method or provided as arguments.
        If it is provided then it overrides the value set before calling this method.

        Parameters
        ----------
        parent : tk.Misc
            The parent widget.
        verbose_name : str or None, optional
            The verbose name of the group (default is None).
        """
        if verbose_name is not None:
            self.verbose_name = verbose_name

        if self.verbose_name is None:
            raise ValueError("name needs to be provided or set as string")

        super().__init__(parent, **self.kw)

    def on_tab_select(self):
        """
        Called when the tab containing this window is selected.
        Defaults to calling on_tab_select for each module in the group.
        """
        for module in self.modules:
            module.on_tab_select()


class BaseCollection(ABC, ttk.Frame):
    """
    A base class for collections of modules and viewers.

    Parameters
    ----------
    parent : tk.Misc
        The parent widget.
    manager : Manager
        The manager object for this collection.
    direction : DirectionType, optional
        The direction of the child widgets in this collection (default is "Horizontal").
    **kwargs : dict
        Additional keyword arguments as defined in ttk Frame.

    Attributes
    ----------
    manager : Manager
        The manager object for this collection.
    direction : str
        The direction of the child widgets in this collection.
    main_viewer : BaseViewer | None
        The main viewer in the collection.
    viewers : list[BaseViewer]
        The list of viewers in the collection.
    viewer_count : int
        The number of viewers in the collection.
    modules : list[BaseModule]
        The list of modules in the collection.
    output_frame_count : int
        The number of output frames in the collection.

    Methods
    -------
    load_outputs()
        User should override this method to load outputs into the OutputFrame objects in collection
        and link input and output variables in IOGroup objects.
    load_commands()
        User can override this method to register command buttons for the collection.
    register_command(text: str, command: Callable[[], Any])
        Register a command so that it shows as a button in the main tab.
    on_image_load(viewer: BaseViewer) -> None
        User should override this method to handle image load events.
    on_main_tab_select()
        Handles the event when the main tab is selected.
    create_rois() -> None
        Calls the create_rois method for each module.
    run_analysis() -> None
        Calls the run_analysis method for each module.
    create_and_run() -> None
        Calls the `create_rois` and `run_analysis` methods.
    run(cls: type[Self], direction: DirectionType = "Horizontal")
        Runs the application.
    """

    context_manager_generator: BaseContextManagerGenerator = SimpleContextManagerGenerator()

    @overload
    def __init__(
        self,
        parent: tk.Misc,
        manager: Manager,
        *,
        direction: DirectionType = "Horizontal",
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
        manager: Manager,
        *,
        direction: DirectionType = "Horizontal",
        **kwargs) -> None: ...

    def __init__(
            self,
            parent: tk.Misc,
            manager: Manager,
            *,
            direction: DirectionType = "Horizontal",
            **kwargs):
        super().__init__(parent, **kwargs)
        self.manager: Manager = manager
        if direction[0].lower() == "h":
            self.direction: Literal["horizontal", "vertical"] = "horizontal"
        else:
            self.direction = "vertical"

        self.main_viewer: BaseViewer | None = None
        self.viewers: list[BaseViewer] = []
        self.viewer_count: int = 0
        self._module_groups: dict[WindowGroup, list[BaseModule]] = {}
        self.modules: list[BaseModule] = []
        self.output_frame_count: int = 0
        self.command_buttons_count: int = 0

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._tab_change_calls: dict[str, Callable[[], None]] = {}

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(column=0, row=0, sticky="nsew")

        self.main_frame = ttk.Panedwindow(self.notebook, orient=self.direction)
        self.notebook.add(self.main_frame, text="Main")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self._tab_change_calls[self.notebook.tabs()[-1]] = self.on_main_tab_select

        self.viewer_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.viewer_frame, weight=1)
        self.main_window = ttk.Notebook(self.main_frame)
        self.main_frame.add(self.main_window)

        self.output_frame = ScrolledWindow(self.main_window)
        self.main_window.add(self.output_frame.outer_frame, text="Outputs")

        self.button_frame = ttk.Labelframe(self.output_frame, text="Commands")
        self.command_buttons: list[ttk.Button] = []
        if self.direction == "horizontal":
            self.button_frame.grid(column=0, row=self.output_frame_count, sticky="nsew")
        else:
            self.button_frame.grid(column=self.output_frame_count, row=0, sticky="nsew")
        self.output_frame_count += 1

        self.context_frame = ScrolledWindow(self.main_window)
        self.context_manager: BaseContextManager = self.context_manager_generator(
            self.context_frame,
            self.manager)
        self.context_manager.grid(column=0, row=0, sticky="nsew")
        self.main_window.add(self.context_frame.outer_frame, text="Context")

        for k, v in self.__class__.__dict__.items():
            if k[:2] != "__" or k[-2:] != "__":
                if isinstance(v, OutputFrame):
                    attr = copy(v)
                    setattr(self, k, attr)
                    if attr.verbose_name is None:
                        attr.verbose_name = k.replace("_", " ").title()
                    attr.setup(parent=self.output_frame)
                    if self.direction == "horizontal":
                        attr.grid(column=0, row=self.output_frame_count, sticky="nsew")
                    else:
                        attr.grid(column=self.output_frame_count, row=0, sticky="nsew")
                    self.output_frame_count += 1

                elif isinstance(v, WindowGroup):
                    attr = copy(v)
                    setattr(self, k, attr)
                    if attr.verbose_name is None:
                        attr.verbose_name = k.replace("_", " ").title()
                    attr.setup(parent=self.notebook)
                    self.notebook.add(attr, text=attr.verbose_name)
                    self._tab_change_calls[self.notebook.tabs()[-1]] = attr.on_tab_select
                    self._module_groups[attr] = attr.modules

                elif isinstance(v, BaseViewerIO):
                    attr = v.viewer_type(self.viewer_frame,
                                         manager=self.manager,
                                         allow_drag_drop=v.allow_drag_drop,
                                         allow_drawing_rois=v.allow_drawing_rois,
                                         validation_command=v.validation_command)
                    attr.grid(column=v.column,
                              row=v.row,
                              sticky="nsew")
                    self.viewer_frame.columnconfigure(v.column, weight=1)
                    self.viewer_frame.rowconfigure(v.row, weight=1)
                    setattr(self, k, attr)
                    attr.add_load_trace(self._on_image_load_partial(attr))
                    self.viewers.append(attr)
                    if self.viewer_count == 0 or v.main:
                        self.main_viewer = attr
                    self.viewer_count += 1

        self.rois_button = ttk.Button(self.button_frame,
                                      text="Draw ROIs",
                                      command=self.create_rois)
        self.analyse_button = ttk.Button(self.button_frame,
                                         text="Analyse",
                                         command=self.run_analysis)
        self.create_and_run_button = ttk.Button(self.button_frame,
                                                text="Create and Run",
                                                command=self.create_and_run)

        if self.direction == "horizontal":
            self.rois_button.grid(column=0, row=self.command_buttons_count, sticky="nsew")
            self.analyse_button.grid(column=1, row=self.command_buttons_count, sticky="nsew")
            self.command_buttons_count += 1
            self.create_and_run_button.grid(column=0,
                                            row=self.command_buttons_count,
                                            columnspan=2,
                                            sticky="nsew")
            self.command_buttons_count += 1

        else:
            self.rois_button.grid(column=self.command_buttons_count, row=0, sticky="nsew")
            self.analyse_button.grid(column=self.command_buttons_count, row=1, sticky="nsew")
            self.command_buttons_count += 1
            self.create_and_run_button.grid(column=self.command_buttons_count,
                                            row=0,
                                            rowspan=2,
                                            sticky="nsew")
            self.command_buttons_count += 1

        for k, v in self.__class__.__dict__.items():
            if k[:2] != "__" or k[-2:] != "__":
                if isinstance(v, BaseModule):
                    attr = copy(v)
                    setattr(self, k, attr)
                    self.modules.append(attr)
                    if attr.verbose_name is None:
                        attr.verbose_name = k.replace("_", " ").title()
                    found = False
                    for window, modules in self._module_groups.items():
                        if v in modules:
                            window.modules[window.modules.index(v)] = attr
                            lf = ttk.Labelframe(window, text=attr.verbose_name, labelanchor="nw")
                            lf.columnconfigure(0, weight=1)
                            lf.rowconfigure(0, weight=1)
                            attr.setup(parent=lf,
                                       manager=self.manager,
                                       context_manager=self.context_manager)
                            attr.grid(column=0, row=0, sticky="nsew")
                            window.add(lf, weight=1)
                            found = True
                            break
                    if not found:
                        attr.setup(parent=self.notebook,
                                   manager=self.manager,
                                   context_manager=self.context_manager)
                        self.notebook.add(attr, text=attr.verbose_name)
                        self._tab_change_calls[self.notebook.tabs()[-1]] = attr.on_tab_select

        self.load_outputs()
        self.load_commands()

    def _on_image_load_partial(self, viewer: BaseViewer) -> Callable[[], None]:
        """
        Returns a partial function for handling image load events.

        Parameters
        ----------
        viewer : BaseViewer
            The viewer object loading the image.

        Returns
        -------
        Callable[[], None]
            The partial function for handling image load events.
        """
        def partial():
            self.on_image_load(viewer)

        return partial

    def load_outputs(self):
        """
        User can override this method to load outputs into the OutputFrame objects in collection
        and link input and output variables in IOGroup objects.

        Examples
        --------
        The following would load outputs into the output frames::

            self.output_frame.register_output(self.module.output, verbose_name="Output Name")

        The following would link different modules inputs and outputs::

            IOGroup([self.module1.input, self.module2.input, self.module3.output])
        """

    def load_commands(self):
        """
        User can override this method to register command buttons for the collection.

        Examples
        --------
        The following would register a method called "print_outputs"::

            self.register_command("Print Outputs", self.print_outputs)
        """

    def register_command(self, text: str, command: Callable[[], Any]):
        """
        Register a command so that it shows as a button in the main tab.

        Parameters
        ----------
        text : str
            The text to show on the button
        command : Callable[[], Any]
            the command called when the button is pressed
        """
        button = ttk.Button(self.button_frame, text=text, command=command)
        self.command_buttons.append(button)
        if self.direction == "horizontal":
            button.grid(column=0,
                        row=self.command_buttons_count,
                        columnspan=2,
                        sticky="nsew")
            self.command_buttons_count += 1

        else:
            button.grid(column=self.command_buttons_count,
                        row=0,
                        rowspan=2,
                        sticky="nsew")
            self.command_buttons_count += 1

    def on_image_load(self, viewer: BaseViewer) -> None:
        """
        User should override this method to handle image load events
        for viewers in the main tab of the module.

        Parameters
        ----------
        viewer : BaseViewer
            The viewer object that has had an image loaded.

        Examples
        --------
        The following would load an image loaded into a main tab viewer into a module viewer::

            if viewer is self.viewer:
                if self.viewer.image is not None:
                    self.module.viewer.load_image(image)

        """

    def on_main_tab_select(self):
        """
        Handles the event when the main tab is selected.
        Default is to show all ROIs in the main tabs viewers.
        """
        for viewer in self.viewers:
            if viewer.image is not None and isinstance(viewer.image, ArrayImage):
                for roi in viewer.image.rois:
                    roi.hidden = False
                viewer.update()

    def _on_tab_change(self, event: tk.Event):
        """
        Handles the event when a tab is changed.
        """
        self._tab_change_calls[event.widget.select()]()

    def get_context(self) -> BaseContext | None:
        """
        Returns the context for the collection.
        """
        context = None
        if self.main_viewer is not None and self.main_viewer.image is not None:
            context = self.context_manager.get_context(self.main_viewer.image)
        return context

    def create_rois(self) -> None:
        """
        By default this gets the context then
        calls the `create_rois` method for each module.
        """
        context = self.get_context()
        for module in self.modules:
            module.create_rois(context, batch=True)

    def run_analysis(self) -> None:
        """
        By default this calls the `run_analysis` method for each module.
        """
        for module in self.modules:
            module.run_analysis(batch=True)

    def create_and_run(self) -> None:
        """
        Calls the `create_rois` and `run_analysis` methods.
        """
        self.create_rois()
        self.run_analysis()

    @classmethod
    def run(cls: type[Self],
            direction: DirectionType = "Horizontal"):
        """
        Runs the application.

        Parameters
        ----------
        direction : DirectionType, optional
            The direction of the collection (default is "Horizontal").
        """
        app = tk.Tk()
        app.columnconfigure(0, weight=1)
        app.columnconfigure(1, weight=1)
        app.rowconfigure(1, weight=1)
        app.resizable(True, True)

        man = Manager()

        load_butt = ttk.Button(app, text="Load Folder",
                               command=lambda: man.load_folder(False, app, 0, 2))
        load_butt.grid(column=0, row=0, sticky="nsew")

        load_butt = ttk.Button(app, text="Add Folder",
                               command=lambda: man.load_folder(True, app, 0, 2))
        load_butt.grid(column=1, row=0, sticky="nsew")

        frame = ttk.Panedwindow(app, orient="vertical")
        frame.grid(column=0, row=1, columnspan=2, sticky="nsew")

        tree_frame = man.get_tree_frame(frame)
        frame.add(tree_frame)

        options_frame = ttk.Frame(frame)
        frame.add(options_frame)

        options_combo = man.get_mouse_options_combobox(options_frame)
        options_combo.grid(column=0, row=0, sticky="nsew")

        roi_options = man.get_roi_options_frame(options_frame, "h")
        roi_options.grid(column=2, row=0, sticky="nsew")

        collection = cls(frame, man, direction=direction)
        frame.add(collection, weight=1)

        app.mainloop()
