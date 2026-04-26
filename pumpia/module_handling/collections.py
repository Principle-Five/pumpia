"""
Classes:
 * BaseCollection
 * OutputFrame
 * WindowGroup
"""

from abc import ABC
import logging
import tkinter as tk
from tkinter import ttk
from typing import overload, Literal, Self, Any
from collections.abc import Callable
from pumpia.utilities.typing import DirectionType
from pumpia.image_handling.image_structures import ArrayImage
from pumpia.widgets.typing import ScreenUnits, Cursor, Padding, Relief, TakeFocusValue
from pumpia.widgets.context_managers import (BaseContextManager,
                                             SimpleContextManager,
                                             PhantomContextManager)
from pumpia.widgets.scrolled_window import ScrolledWindow
from pumpia.widgets.viewers import BaseViewer
from pumpia.widgets.textbox_logger import TextBoxHandler
from pumpia.module_handling.fields.groups import _FieldGroupsMeta
from pumpia.module_handling.fields.windows import _FieldWindowsMeta, FieldWindow
from pumpia.module_handling.fields.viewer_fields import _ViewerFieldsMeta
from pumpia.module_handling.modules import BaseModule, _ModulesMeta
from pumpia.module_handling.manager import Manager
from pumpia.module_handling.context import BaseContext


class ModuleFormatter(logging.Formatter):
    """
    A logging formatter that preppends the module name
    (pulled from the initial logger name) to the formatted string.
    """

    def format(self, record: logging.LogRecord) -> str:
        formatted_record = super().format(record)
        try:
            module_logger = ".".join(record.name.split(".")[1:])
        except IndexError:
            module_logger = record.name
        return f"{module_logger}: {formatted_record}"


class _ModuleGroups:
    def __init__(self, obj: BaseCollection) -> None:
        self.obj: BaseCollection = obj
        self.groups_dict: dict[str, ModuleGroup] = {}

    def __iter__(self):
        for group in self.groups_dict.values():
            yield group


class _ModuleGroupsMeta:
    def __init__(self) -> None:
        self.groups: dict[str, ModuleGroup] = {}
        self.name: str = ""
        self.private_name: str = "_"
        self.base_owner: type[BaseCollection] | None = None

    @property
    def group_names(self) -> list[str]:
        """
        The names of the module groups for the linked collection.
        """
        return list(self.groups.keys())

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        self.private_name = "_" + name
        self.base_owner = owner

    @overload
    def __get__(self, obj: BaseCollection, owner: type[BaseCollection]) -> _ModuleGroups: ...
    @overload
    def __get__(self, obj: None, owner: type[BaseCollection]) -> Self: ...

    def __get__(self,
                obj: BaseCollection | None,
                owner: type[BaseCollection]
                ) -> _ModuleGroups | Self:
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
            groups = _ModuleGroups(obj)
            setattr(obj, self.private_name, groups)
            return groups


class ModuleGroup(ttk.Panedwindow):
    """
    Groups multiple modules into the same tab in the collection.

    Parameters
    ----------
    *modules : BaseModule
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
        *modules: BaseModule,
        verbose_name: str | None = None,
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
        *modules: BaseModule,
        verbose_name: str | None = None,
        direction: DirectionType = "V",
        **kwargs) -> None: ...

    # pylint: disable-next=super-init-not-called
    def __init__(self,
                 *modules: BaseModule,
                 verbose_name: str | None = None,
                 direction: DirectionType = "V",
                 **kw) -> None:
        self.module_names: list[str] = []
        self.modules: list[BaseModule] = list(modules)
        self.verbose_name: str | None = verbose_name
        self.name: str = ""

        if direction[0].lower() == "h":
            self.direction: DirectionType = "horizontal"
        else:
            self.direction: DirectionType = "vertical"
        self.kw = kw
        self.kw["orient"] = self.direction

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()
        owner.module_groups.groups[name] = self
        self.module_names = [module.name for module in self.modules]

    def __get__(self, obj: BaseCollection | None, owner=None) -> Self:
        if obj is None:
            return self

        try:
            return obj.module_groups.groups_dict[self.name]  # pyright: ignore[reportReturnType]
        except KeyError:
            group = type(self)(*[],
                               verbose_name=self.verbose_name,
                               direction=self.direction,
                               **self.kw)
            group.setup(parent=obj.notebook)

            modules: list[BaseModule] = []
            for module_name in self.module_names:
                module: BaseModule = getattr(obj, module_name)
                if module.verbose_name is None:
                    name = module.name
                else:
                    name = module.verbose_name
                lf = ttk.Labelframe(group, text=name, labelanchor="nw")
                lf.columnconfigure(0, weight=1)
                lf.rowconfigure(0, weight=1)
                module.setup(parent=lf,
                             manager=obj.manager,
                             context_manager=obj.context_manager,
                             parent_logger=obj.logger)
                module.grid(column=0, row=0, sticky=tk.NSEW)
                group.add(lf, weight=1)
                modules.append(getattr(obj, module_name))

            group.module_names = self.module_names
            group.modules = modules
            obj.module_groups.groups_dict[self.name] = group
            return group

    def setup(self, parent: tk.Misc):
        """
        Sets up the module group.

        Parameters
        ----------
        parent : tk.Misc
            The parent widget.
        """

        super().__init__(parent, **self.kw)

    def on_tab_select(self):
        """
        Called when the tab containing this group is selected.
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
    context_manager : BaseContextManager
        Set at class level.
        Determines which context manager to use
        if none is passed in at object initialisation.
        (default is SimpleContextManager)
    title : str
        Set at class level.
        Title of the module tkinter window.
    manager : Manager
        The manager object for this collection.
    direction : str
        The direction of the child widgets in this collection.
    modules
    field_groups
    field_windows
    viewers
    module_groups
    main_viewer : BaseViewer | None
        The main viewer in the collection.
    viewer_count : int
        The number of viewers in the collection.
    output_frame_count : int
        The number of output frames in the collection.

    Methods
    -------
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

    context_manager: BaseContextManager = SimpleContextManager()
    title: str = "Pumpia Collection"
    modules = _ModulesMeta()
    field_groups = _FieldGroupsMeta()
    field_windows = _FieldWindowsMeta()
    viewers = _ViewerFieldsMeta()
    module_groups = _ModuleGroupsMeta()

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
        self.viewer_count: int = 0
        self.output_frame_count: int = 0
        self.command_buttons_count: int = 0

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._tab_change_calls: dict[str, Callable[[], None]] = {}

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(column=0, row=0, sticky=tk.NSEW)

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
            self.button_frame.grid(column=0, row=self.output_frame_count, sticky=tk.NSEW)
        else:
            self.button_frame.grid(column=self.output_frame_count, row=0, sticky=tk.NSEW)
        self.output_frame_count += 1

        self.context_frame = ScrolledWindow(self.main_window)
        self.context_buttons_frame = ttk.Frame(self.context_frame)
        self.context_buttons_frame.grid(column=0, row=0, sticky=tk.NSEW)
        self.context_manager(parent=self.context_frame, manager=self.manager)
        self.context_manager.grid(column=0, row=1, sticky=tk.NSEW)
        self.main_window.add(self.context_frame.outer_frame, text="Context")

        self.get_context_button = ttk.Button(self.context_buttons_frame,
                                             text="Get Context",
                                             command=self.get_context)
        self.get_context_button.grid(column=0, row=0, sticky=tk.NSEW)

        self.log_handler = TextBoxHandler(self.main_window,
                                          formatter=ModuleFormatter(fmt="{levelname}: {message}",
                                                                    style="{"))
        self.main_window.add(self.log_handler.frame, text="Log")
        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setLevel(logging.WARNING)
        self.stream_handler.setFormatter(ModuleFormatter(fmt="{levelname}: {message}",
                                                         style="{"))

        self.logger = logging.getLogger(self.title.replace(" ", "_").lower())
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.log_handler)
        self.logger.addHandler(self.stream_handler)

        show_draw_rois_button: bool = False
        show_analyse_button: bool = False

        for group_name in type(self).module_groups.group_names:
            group: ModuleGroup = getattr(self, group_name)
            if group.verbose_name is None:
                name = group.name
            else:
                name = group.verbose_name
            self.notebook.add(group, text=name)
            self._tab_change_calls[self.notebook.tabs()[-1]] = group.on_tab_select

        for module_name in type(self).modules.module_names:
            module: BaseModule = getattr(self, module_name)
            show_draw_rois_button = show_draw_rois_button or module.show_draw_rois_button
            show_analyse_button = show_analyse_button or module.show_analyse_button
            if module.parent is None:
                module.setup(parent=self.notebook,
                             manager=self.manager,
                             context_manager=self.context_manager,
                             parent_logger=self.logger)
                if module.verbose_name is None:
                    name = module.name
                else:
                    name = module.verbose_name
                self.notebook.add(module, text=name)
                self._tab_change_calls[self.notebook.tabs()[-1]] = module.on_tab_select

        for window_name in type(self).field_windows.window_names:
            window: FieldWindow = getattr(self, window_name)
            frame = window.get_frame(self.output_frame)
            if self.direction == "horizontal":
                frame.grid(column=0,
                           row=self.output_frame_count,
                           columnspan=2,
                           sticky=tk.NSEW)
            else:
                frame.grid(column=2 * self.output_frame_count,
                           row=0,
                           columnspan=2,
                           sticky=tk.NSEW)
            self.output_frame_count += 1

        for group_name in type(self).field_groups.group_names:
            getattr(self, group_name)

        for viewer_name, viewer_field in type(self).viewers.viewer_fields.items():
            viewer: BaseViewer = getattr(self, viewer_name)
            viewer.grid(column=viewer_field.column,
                        row=viewer_field.row,
                        sticky=tk.NSEW)
            self.viewer_frame.columnconfigure(viewer_field.column, weight=1)
            self.viewer_frame.rowconfigure(viewer_field.row, weight=1)
            viewer.add_load_trace(self._on_image_load_partial(viewer))
            if self.viewer_count == 0 or viewer_field.main:
                self.main_viewer = viewer
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
            if show_draw_rois_button:
                if show_analyse_button:
                    self.rois_button.grid(column=0,
                                          row=self.command_buttons_count,
                                          sticky=tk.NSEW)
                else:
                    self.rois_button.grid(column=0,
                                          row=self.command_buttons_count,
                                          columnspan=2,
                                          sticky=tk.NSEW)

            if show_analyse_button:
                if show_draw_rois_button:
                    self.analyse_button.grid(column=1,
                                             row=self.command_buttons_count,
                                             sticky=tk.NSEW)
                else:
                    self.analyse_button.grid(column=0,
                                             row=self.command_buttons_count,
                                             columnspan=2,
                                             sticky=tk.NSEW)

            if show_analyse_button or show_draw_rois_button:
                self.command_buttons_count += 1

            if show_analyse_button and show_draw_rois_button:
                self.create_and_run_button.grid(column=0,
                                                row=self.command_buttons_count,
                                                columnspan=2,
                                                sticky=tk.NSEW)
                self.command_buttons_count += 1

        else:
            if show_draw_rois_button:
                if show_analyse_button:
                    self.rois_button.grid(column=self.command_buttons_count,
                                          row=0,
                                          sticky=tk.NSEW)
                else:
                    self.rois_button.grid(column=self.command_buttons_count,
                                          row=0,
                                          rowspan=2,
                                          sticky=tk.NSEW)

            if show_analyse_button:
                if show_draw_rois_button:
                    self.analyse_button.grid(column=self.command_buttons_count,
                                             row=1,
                                             sticky=tk.NSEW)
                else:
                    self.analyse_button.grid(column=self.command_buttons_count,
                                             row=0,
                                             rowspan=2,
                                             sticky=tk.NSEW)

            if show_analyse_button or show_draw_rois_button:
                self.command_buttons_count += 1

            if show_analyse_button and show_draw_rois_button:
                self.create_and_run_button.grid(column=self.command_buttons_count,
                                                row=0,
                                                rowspan=2,
                                                sticky=tk.NSEW)
                self.command_buttons_count += 1

        if (self.main_viewer is not None
                and isinstance(self.context_manager, PhantomContextManager)):

            def bbox_command():
                if (self.main_viewer is not None
                    and isinstance(self.main_viewer.image, ArrayImage)
                        and isinstance(self.context_manager, PhantomContextManager)):
                    self.context_manager.get_bound_box_roi(self.main_viewer.image)

            bbox_button = ttk.Button(self.context_buttons_frame,
                                     command=bbox_command,
                                     text="Draw Phantom Boundbox")
            bbox_button.grid(column=0, row=1, sticky=tk.NSEW)

            def boundary_command():
                if (self.main_viewer is not None
                    and isinstance(self.main_viewer.image, ArrayImage)
                        and isinstance(self.context_manager, PhantomContextManager)):
                    self.context_manager.get_boundary_roi(self.main_viewer.image)

            boundary_button = ttk.Button(self.context_buttons_frame,
                                         command=boundary_command,
                                         text="Draw Phantom Boundary")
            boundary_button.grid(column=0, row=2, sticky=tk.NSEW)

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
                        sticky=tk.NSEW)
            self.command_buttons_count += 1

        else:
            button.grid(column=self.command_buttons_count,
                        row=0,
                        rowspan=2,
                        sticky=tk.NSEW)
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

    def update_viewers(self):
        """
        Updates the viewers in the collection.
        """
        for module in self.modules:
            module.update_viewers()
        for viewer in self.viewers:
            viewer.update()

    def _on_tab_change(self, event: tk.Event):
        """
        Handles the event when a tab is changed.
        """
        self._tab_change_calls[event.widget.select()]()  # type: ignore

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
        self.update_viewers()

    def run_analysis(self) -> None:
        """
        By default this calls the `run_analysis` method for each module.
        """
        for module in self.modules:
            module.run_analysis(batch=True)
        self.update_viewers()

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
        app.title(cls.title)
        app.columnconfigure(0, weight=1)
        app.columnconfigure(1, weight=1)
        app.rowconfigure(1, weight=1)
        app.resizable(True, True)

        man = Manager()

        load_butt = ttk.Button(app, text="Load Folder",
                               command=lambda: man.load_folder(False, app, 0, 2))
        load_butt.grid(column=0, row=0, sticky=tk.NSEW)

        load_butt = ttk.Button(app, text="Add Folder",
                               command=lambda: man.load_folder(True, app, 0, 2))
        load_butt.grid(column=1, row=0, sticky=tk.NSEW)

        frame = ttk.Panedwindow(app, orient="vertical")
        frame.grid(column=0, row=1, columnspan=2, sticky=tk.NSEW)

        tree_frame = man.get_tree_frame(frame)
        frame.add(tree_frame)

        options_frame = ttk.Frame(frame)
        frame.add(options_frame)

        options_combo = man.get_mouse_options_combobox(options_frame)
        options_combo.grid(column=0, row=0, sticky=tk.NSEW)

        roi_options = man.get_roi_options_frame(options_frame, "h")
        roi_options.grid(column=2, row=0, sticky=tk.NSEW)

        collection = cls(frame, man, direction=direction)
        frame.add(collection, weight=1)

        app.mainloop()
