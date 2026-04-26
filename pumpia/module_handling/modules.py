"""
Classes:
 * BaseModule
 * PhantomModule
"""

import logging
from abc import ABC
import tkinter as tk
from tkinter import ttk
from typing import overload, Self, Literal, Any, TYPE_CHECKING
from collections.abc import Callable

from pumpia.module_handling.context import BaseContext, SimpleContext
from pumpia.module_handling.manager import Manager
from pumpia.utilities.typing import DirectionType
from pumpia.image_handling.image_structures import ArrayImage
from pumpia.image_handling.roi_structures import BaseROI
from pumpia.widgets.scrolled_window import ScrolledWindow
from pumpia.widgets.viewers import BaseViewer
from pumpia.widgets.context_managers import (BaseContextManager,
                                             PhantomContextManager,
                                             SimpleContextManager,
                                             ManualPhantomManager)
from pumpia.widgets.textbox_logger import TextBoxHandler
from pumpia.widgets.typing import ScreenUnits, Cursor, Padding, Relief, TakeFocusValue
from pumpia.module_handling.fields.simple import _FieldsMeta
from pumpia.module_handling.fields.windows import _FieldWindowsMeta, FieldWindow
from pumpia.module_handling.fields.viewer_fields import _ViewerFieldsMeta
from pumpia.module_handling.fields.roi_fields import _ROIFieldsMeta, BaseROIField

if TYPE_CHECKING:
    from pumpia.module_handling.collections import BaseCollection


class _Modules:
    def __init__(self, obj: BaseCollection) -> None:
        self.modules_dict: dict[str, BaseModule] = {}
        self.obj: BaseCollection = obj

    def __iter__(self):
        for module in self.modules_dict.values():
            yield module

    def __getitem__(self, key: str):
        return self.modules_dict[key]


class _ModulesMeta:
    def __init__(self) -> None:
        self.module_types: dict[str, BaseModule] = {}
        self.name: str = ""
        self.private_name: str = "_"
        self.base_owner: type[BaseCollection] | None = None

    @property
    def module_names(self) -> list[str]:
        """
        The names of the modules for the module.

        Returns
        -------
        list[str]
        """
        return list(self.module_types.keys())

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        self.private_name = "_" + name
        self.base_owner = owner

    @overload
    def __get__(self, obj: BaseCollection, owner: type[BaseCollection]) -> _Modules: ...
    @overload
    def __get__(self, obj: None, owner: type[BaseCollection]) -> Self: ...

    def __get__(self, obj: BaseCollection | None, owner: type[BaseCollection]) -> _Modules | Self:
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
            modules = _Modules(obj)
            setattr(obj, self.private_name, modules)
            return modules


class BaseModule(ABC, ttk.Frame):
    """
    Base class for modules.

    Parameters
    ----------
    parent : tk.Misc or None, optional
        The parent widget (default is None).
    manager : Manager or None, optional
        The manager object (default is None).
    context_manager : BaseContextManager or None, optional
        The context manager instance to be used (default is None).
    verbose_name : str or None, optional
        The verbose name of the module (default is None).
    direction : DirectionType, optional
        The direction of the child widgets in the frame (default is "Horizontal").
    **kw : dict
        Additional keyword arguments as defined by ttk Labelframe.

    Attributes
    ----------
    context_manager : BaseContextManager
        Set at class level.
        Determines which context manager to use
        if none is passed in at object initialisation.
        (default is SimpleContextManager)
    show_draw_rois_button : bool
        Set at class level.
        Determines if a button to draw ROIs is shown.
    show_analyse_button : bool
        Set at class level.
        Determines if a button to analyse the module is shown.
    show_copy_buttons : bool
        Set at class level.
        Determines if buttons to copy all field values is shown.
    title : str
        Set at class level.
        Title of the module tkinter window.
    fields
    field_windows
    viewers
    rois
        ROI Fields for the module
    manager : Manager | None
    parent : tk.Misc | None
    logger : logging.Logger
    verbose_name : str | None
    direction : Literal["horizontal", "vertical"]
    main_viewer : BaseViewer | None
        The main viewer for the module, used to get context etc.
        Defaults to first viewer defined if not provided in ViewerIOs.
        If multiple are set then defaults to the last defined ViewerIO.
    rois_loaded : bool
    analysed : bool
    input_count : int
    output_count : int
    viewer_count : int
    roi_count : int
    is_setup : bool

    Methods
    -------
    setup(parent : tk.Misc | None = None, manager : Manager | None = None, context_manager : BaseContextManager | None = None)
        Sets up the module.
    get_context() -> BaseContext
        Returns the context for the module.
    load_commands()
        User can override this method to register command buttons for the collection.
    register_command(text: str, command: Callable[[], Any])
        Register a command so that it shows as a button in the main tab.
    link_rois_viewers()
        Link ROIs and viewers for manual drawing.
    post_roi_register(roi_input : BaseInputROI)
        Command ran after an roi is registered with an input.
    manual_roi_draw(self)
        Does a full manual draw of all ROIs
    draw_rois(context : BaseContext) -> None
        User should override this method to handle drawing the required ROIs.
    analyse()
        User should override this method to handle analysing the ROIs.
    on_image_load(viewer : BaseViewer) -> None
        User can add to this method to handle image load events by calling it using super.
    on_tab_select()
        Handles the event when a tab containing the module is selected.
    create_rois(context : BaseContext | None = None) -> None
        Creates the ROIs for the module.
    run_analysis() -> None
        Runs the analysis for the module.
    create_and_run(context : BaseContext | None = None) -> None
        Creates the ROIs and runs the analysis.
    setup_window(app : tk.Tk, direction : DirectionType = "Horizontal")
        Sets up the application window when running the module independently.
    run(direction : DirectionType = "Horizontal")
        Class method which runs the module independently.
    """
    context_manager: BaseContextManager = SimpleContextManager()
    show_draw_rois_button: bool = False
    show_analyse_button: bool = False
    show_copy_buttons: bool = False
    title: str = "PumpIA Module"
    fields = _FieldsMeta()
    field_windows = _FieldWindowsMeta()
    viewers = _ViewerFieldsMeta()
    rois = _ROIFieldsMeta()

    @overload
    def __init__(
        self,
        parent: tk.Misc | None = None,
        manager: Manager | None = None,
        context_manager: BaseContextManager | None = None,
        *,
        verbose_name: str | None = None,
        direction: DirectionType = "Horizontal",
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
    def __init__(self,
                 parent: tk.Misc | None = None,
                 manager: Manager | None = None,
                 context_manager: BaseContextManager | None = None,
                 *,
                 verbose_name: str | None = None,
                 direction: DirectionType = "Horizontal",
                 **kw): ...

    # pylint: disable-next=super-init-not-called
    def __init__(self,
                 parent: tk.Misc | None = None,
                 manager: Manager | None = None,
                 context_manager: BaseContextManager | None = None,
                 *,
                 verbose_name: str | None = None,
                 direction: DirectionType = "Horizontal",
                 **kw):
        self.parent: tk.Misc | None = parent
        self.manager: Manager | None = manager
        if context_manager is not None:
            self.context_manager = context_manager

        self._kw = kw
        self.verbose_name = verbose_name
        self.name: str = ""

        self._is_setup: bool = False

        if direction[0].lower() == "h":
            self.direction: Literal["horizontal", "vertical"] = "horizontal"
        else:
            self.direction = "vertical"

        self.main_viewer: BaseViewer | None = None

        self.analysed: bool = False

        self.input_count: int = 0
        self.output_count: int = 0
        self.viewer_count: int = 0
        self.roi_count: int = 0
        self.command_buttons_count: int = 0
        self._start_manual_draw: bool = False

        for field_name in type(self).fields.field_names:
            getattr(self, field_name)

        if self.manager is not None and self.parent is not None:
            self.setup()

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()
        owner.modules.module_types[name] = self

    def __get__(self, obj: BaseCollection | None, owner=None) -> Self:
        if obj is None:
            return self

        try:
            return obj.modules.modules_dict[self.name]  # pyright: ignore[reportReturnType]
        except KeyError:
            module = type(self)(parent=self.parent,
                                manager=self.manager,
                                context_manager=self.context_manager,
                                verbose_name=self.verbose_name,
                                direction=self.direction,
                                **self._kw)
            module.name = self.name
            obj.modules.modules_dict[self.name] = module
            return module
        except AttributeError:
            return self

    @property
    def is_setup(self) -> bool:
        """
        Whether the module is set up.
        """
        return self._is_setup

    def setup(self,
              *,
              parent: tk.Misc | None = None,
              manager: Manager | None = None,
              context_manager: BaseContextManager | None = None,
              parent_logger: logging.Logger | None = None):
        """
        Sets up the module.
        Parent and manager must be set before calling this method or provided as arguments.
        If parent, manager, or context manager are provided
        then they override the values set before calling this method.

        Parameters
        ----------
        parent : tk.Misc or None, optional
            The parent widget (default is None).
        manager : Manager or None, optional
            The manager object (default is None).
        context_manager : BaseContextManager or None, optional
            The context manager (default is None).
        """
        if not self._is_setup:
            if parent is not None:
                self.parent = parent
            if manager is not None:
                self.manager = manager
            if context_manager is not None:
                self.context_manager = context_manager

            if self.parent is None:
                raise ValueError("parent needs to be set using set_parent or provided")
            if self.manager is None:
                raise ValueError("manager needs to be set using set_manager or provided")

            if self.verbose_name is None:
                super().__init__(self.parent, **self._kw)
            else:
                super().__init__(self.parent, name=self.verbose_name.lower(), **self._kw)

            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=1)

            self.paned_window = ttk.Panedwindow(self, orient=self.direction)
            self.paned_window.grid(column=0, row=0, sticky=tk.NSEW)

            self.viewer_frame = ttk.Frame(self.paned_window)
            self.paned_window.add(self.viewer_frame, weight=1)

            self.main_window = ttk.Notebook(self.paned_window)
            self.paned_window.add(self.main_window)
            self.io_frame = ScrolledWindow(self.main_window)
            self.main_window.add(self.io_frame.outer_frame, text="Main")

            if context_manager is None:
                self.context_frame = ScrolledWindow(self.main_window)

                self.context_buttons_frame = ttk.Frame(self.context_frame)
                self.context_buttons_frame.grid(column=0, row=0, sticky=tk.NSEW)

                self.get_context_button = ttk.Button(self.context_buttons_frame,
                                                     text="Get Context",
                                                     command=self.get_context)
                self.get_context_button.grid(column=0, row=0, sticky=tk.NSEW)

                if self.direction == "horizontal":
                    self.context_manager.direction = "V"
                    self.context_manager(parent=self.context_frame,
                                         manager=self.manager)
                else:
                    self.context_manager.direction = "H"
                    self.context_manager(parent=self.context_frame,
                                         manager=self.manager)
                self.context_manager.grid(column=0, row=1, sticky=tk.NSEW)  # type: ignore

                self.main_window.add(self.context_frame.outer_frame, text="Context")
                add_context_buttons = True
            else:
                add_context_buttons = False

            self.log_handler = TextBoxHandler(self.main_window)
            self.main_window.add(self.log_handler.frame, text="Log")
            self.stream_handler = logging.StreamHandler()
            self.stream_handler.setLevel(logging.WARNING)

            if parent_logger is not None:
                self.logger = logging.getLogger(parent_logger.name + "." + self.name)
            else:
                self.logger = logging.getLogger(self.name)
                self.logger.addHandler(self.stream_handler)

            self.logger.propagate = True
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(self.log_handler)

            self.fields_frame = ttk.Labelframe(self.io_frame, text="Fields")
            self.roi_frame = ttk.Labelframe(self.io_frame, text="ROIs")
            self.button_frame = ttk.Labelframe(self.io_frame, text="Commands")
            self.command_buttons: list[ttk.Button] = []

            if self.direction == "horizontal":
                self.fields_frame.grid(column=0, row=0, sticky=tk.NSEW)
                self.roi_frame.grid(column=0, row=1, sticky=tk.NSEW)
                self.button_frame.grid(column=0, row=2, sticky=tk.NSEW)
            else:
                self.fields_frame.grid(column=0, row=0, sticky=tk.NSEW)
                self.roi_frame.grid(column=1, row=0, sticky=tk.NSEW)
                self.button_frame.grid(column=2, row=0, sticky=tk.NSEW)

            self.rois_button = ttk.Button(self.button_frame,
                                          command=self.create_rois,
                                          text="Create ROIs")

            self.analyse_button = ttk.Button(self.button_frame,
                                             command=self.run_analysis,
                                             text="Analyse")

            self.create_and_run_button = ttk.Button(self.button_frame,
                                                    text="Create and Run",
                                                    command=self.create_and_run)
            if self.direction == "horizontal":
                if self.show_draw_rois_button:
                    if self.show_analyse_button:
                        self.rois_button.grid(column=0,
                                              row=self.command_buttons_count,
                                              sticky=tk.NSEW)
                        self.analyse_button.grid(column=1,
                                                 row=self.command_buttons_count,
                                                 sticky=tk.NSEW)
                    else:
                        self.rois_button.grid(column=0,
                                              row=self.command_buttons_count,
                                              columnspan=2,
                                              sticky=tk.NSEW)
                    self.command_buttons_count += 1
                elif self.show_analyse_button:
                    self.analyse_button.grid(column=0,
                                             row=self.command_buttons_count,
                                             columnspan=2,
                                             sticky=tk.NSEW)
                    self.command_buttons_count += 1

                if self.show_analyse_button and self.show_draw_rois_button:
                    self.create_and_run_button.grid(column=0,
                                                    row=self.command_buttons_count,
                                                    columnspan=2,
                                                    sticky=tk.NSEW)
                    self.command_buttons_count += 1

            else:
                if self.show_draw_rois_button:
                    if self.show_analyse_button:
                        self.rois_button.grid(column=self.command_buttons_count,
                                              row=0,
                                              sticky=tk.NSEW)
                        self.analyse_button.grid(column=self.command_buttons_count,
                                                 row=1,
                                                 sticky=tk.NSEW)
                    else:
                        self.rois_button.grid(column=self.command_buttons_count,
                                              row=0,
                                              rowspan=2,
                                              sticky=tk.NSEW)
                    self.command_buttons_count += 1
                elif self.show_analyse_button:
                    self.analyse_button.grid(column=self.command_buttons_count,
                                             row=0,
                                             rowspan=2,
                                             sticky=tk.NSEW)
                    self.command_buttons_count += 1

                if self.show_analyse_button and self.show_draw_rois_button:
                    self.create_and_run_button.grid(column=self.command_buttons_count,
                                                    row=0,
                                                    rowspan=2,
                                                    sticky=tk.NSEW)
                    self.command_buttons_count += 1

            field_count = 0

            frames = []
            for window_name in type(self).field_windows.window_names:
                window: FieldWindow = getattr(self, window_name)
                frames.append(window.get_frame(self.fields_frame))

            for field in self.fields:
                if field.parent is None:
                    field.parent = self.fields_frame
                    if not field.hidden:
                        label = field.new_label(self.fields_frame)
                        entry = field.new_entry(self.fields_frame)
                        if self.direction == "horizontal":
                            label.grid(column=0,
                                       row=field_count,
                                       sticky=tk.NSEW)
                            entry.grid(column=1,
                                       row=field_count,
                                       sticky=tk.NSEW)
                        else:
                            label.grid(column=2 * field_count,
                                       row=0,
                                       sticky=tk.NSEW)
                            entry.grid(column=2 * field_count + 1,
                                       row=0,
                                       sticky=tk.NSEW)
                        field_count += 1

            for frame in frames:
                if self.direction == "horizontal":
                    frame.grid(column=0,
                               row=field_count,
                               columnspan=2,
                               sticky=tk.NSEW)
                else:
                    frame.grid(column=2 * field_count,
                               row=0,
                               columnspan=2,
                               sticky=tk.NSEW)
                field_count += 1

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

            for roi_name in type(self).rois.roi_names:
                roi_field: BaseROIField = getattr(self, roi_name)
                if self.direction == "horizontal":
                    roi_field.select_button.grid(column=0,
                                                 row=self.roi_count,
                                                 sticky=tk.NSEW)
                    if roi_field.allow_manual_draw:
                        roi_field.draw_button.grid(column=1,
                                                   row=self.roi_count,
                                                   sticky=tk.NSEW)

                else:
                    roi_field.select_button.grid(column=2 * self.roi_count,
                                                 row=0,
                                                 sticky=tk.NSEW)
                    if roi_field.allow_manual_draw:
                        roi_field.draw_button.grid(column=2 * self.roi_count + 1,
                                                   row=0,
                                                   sticky=tk.NSEW)
                    self.roi_count += 1

            if add_context_buttons:
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

            self.link_rois_viewers()
            self.load_commands()
            self._is_setup = True

    @classmethod
    def setup_window(cls: type[Self],
                     app: tk.Tk,
                     direction: DirectionType = "Horizontal"):
        """
        Sets up the application window when running the module independantly.

        Parameters
        ----------
        app : tk.Tk
            The application window.
        direction : DirectionType, optional
            The direction of the child widgets in the module (default is "Horizontal").
        """
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

        module = cls(frame, man, direction=direction)
        frame.add(module, weight=1)

    @classmethod
    def run(cls: type[Self],
            direction: DirectionType = "Horizontal"):
        """
        Runs the module independently.

        Parameters
        ----------
        direction : DirectionType, optional
            The direction child widgets in the module (default is "Horizontal").
        """
        app = tk.Tk()
        app.title(cls.title)
        cls.setup_window(app, direction)
        app.mainloop()

    @property
    def rois_loaded(self) -> bool:
        """
        If the ROIs have been loaded returns `True`.
        """
        rois_loaded = True
        for roi in self.rois:
            rois_loaded = rois_loaded and (roi.roi is not None)
        return rois_loaded

    def _on_image_load_partial(self, viewer: BaseViewer) -> Callable[[], None]:
        """
        Returns a partial function for handling image load events.
        """
        def partial():
            self.on_image_load(viewer)

        return partial

    def get_context(self) -> BaseContext:
        """
        Returns the context for the module.

        By default, it returns the context from `context_manager`,
        using the image in `main_viewer`.

        If `context_manager` is None then it returns `SimpleContext` for the `main_viewer`.

        If `main_viewer` is None or `main_viewer` has no image loaded,
        it raises an error.
        """
        if (self.main_viewer is not None
                and self.main_viewer.image is not None):
            if self.context_manager is not None:
                return self.context_manager.get_context(self.main_viewer.image)
            elif isinstance(self.main_viewer.image, ArrayImage):
                return SimpleContext(self.main_viewer.image.shape[2] / 2,
                                     self.main_viewer.image.shape[1] / 2,
                                     self.main_viewer.image.shape[2],
                                     self.main_viewer.image.shape[1])
        raise ValueError("Viewer has unsuitable image loaded")

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

    def link_rois_viewers(self):
        """
        Link ROIs and viewers for manual drawing.

        Do `self.roi.viewer = self.viewer`.

        By defualt links the ROIs to `main_viewer`,
        this is suitable where the module contains only 1 viewer.
        """
        if self.main_viewer is not None:
            for roi in self.rois:
                roi.viewer = self.main_viewer

    def update_viewers(self):
        """
        Updates the viewers in the module.
        """
        for viewer in self.viewers:
            viewer.update()

    def _post_roi_register_manual_wrapper(self,
                                          roi_input: BaseROIField,
                                          update_viewers: bool = False):
        self.post_roi_register(roi_input)
        if (update_viewers
            and self.manager is not None
                and roi_input.roi is not None):
            self.manager.update_viewers(roi_input.roi.image)

    def post_roi_register(self, roi_input: BaseROIField):
        """
        Command ran after an roi is registered with an input.

        Parameters
        ----------
        roi_input : BaseROIField
            the roi input that has been registered
        """

    def manual_roi_draw(self):
        """
        Does a full manual draw of all ROIs
        """
        for roi in self.rois:
            roi.register_roi(None)
        self._start_manual_draw = True
        self._manually_draw_rois()

    def _manually_draw_rois(self, new_roi: BaseROI | None = None) -> None:
        """
        Manually draw ROIs in the module.
        """
        if new_roi is not None or self._start_manual_draw:
            self._start_manual_draw = False
            for roi in self.rois:
                if roi.allow_manual_draw and roi.roi is None and roi.viewer is not None:
                    roi.manual_draw(self._manually_draw_rois)
                    break

    # pylint: disable-next=unused-argument
    def draw_rois(self, context: BaseContext, batch: bool = False) -> None:
        """
        User should override this method to handle drawing the required ROIs.

        This should not be called directly, use `create_rois` which will get the context.

        By default this calls `manual_roi_draw` if not in ran by a collection
        (i.e. with `batch=True`).

        Parameters
        ----------
        context : BaseContext
            The context for the module as given by `get_context`.
        batch : bool
            If this is being ran as part of a batch, e.g. in a collection (default is False)
        """
        if not batch:
            self.manual_roi_draw()

    def analyse(self, batch: bool = False):
        """
        User should override this method to handle analysing the ROIs.

        This should not be called directly,
        use `run_analysis` which will check the ROIs exist first.

        Parameters
        ----------
        batch : bool
            If this is being ran as part of a batch, e.g. in a collection (default is False)
        """

    def on_image_load(self, viewer: BaseViewer) -> None:
        """
        Users can add to this method to handle image load events.

        By default it checks if the modules ROIs have already been created for the image
        and sets `analysed` to `False`.

        Parameters
        ----------
        viewer : BaseViewer
            The viewer object that has had an image loaded.
        """
        image_rois: list[BaseROI] = []
        viewer_rois: dict[BaseViewer, set[BaseROI]] = {}
        for viewer in self.viewers:
            if viewer.image is not None:
                if isinstance(viewer.image, ArrayImage):
                    image_rois.extend(viewer.image.rois)
                    viewer_rois[viewer] = viewer.image.rois

        for input_roi in self.rois:
            input_roi.roi = None
            if input_roi.viewer is None:
                for image_roi in image_rois:
                    if input_roi.name == image_roi.name:
                        input_roi.roi = image_roi
            else:
                try:
                    for image_roi in viewer_rois[input_roi.viewer]:
                        if input_roi.name == image_roi.name:
                            input_roi.roi = image_roi
                except KeyError:
                    pass

        self.analysed = False

    def on_tab_select(self):
        """
        Handles the event when a tab containing the module is selected.
        """
        roi_names = [roi.name for roi in self.rois if roi.roi is not None]
        for viewer in self.viewers:
            if viewer.image is not None and isinstance(viewer.image, ArrayImage):
                for roi in viewer.image.rois:
                    if not roi.name in roi_names:
                        roi.hidden = True
                    else:
                        roi.hidden = False
                viewer.update()

    def create_rois(self, context: BaseContext | None = None, batch: bool = False) -> None:
        """
        Creates the ROIs for the module.
        Context is obtained from `get_context` if not provided.

        Parameters
        ----------
        context : BaseContext or None, optional
            The context for the module (default is None).
        batch : bool
            If this is being ran as part of a batch, e.g. in a collection (default is False)
        """
        try:
            for roi in self.rois:
                roi.register_roi(None)
            if context is None:
                context = self.get_context()
            self.draw_rois(context, batch)
            if batch is False:
                self.update_viewers()
            self.logger.info("ROIs Created")
        # pylint: disable-next=broad-exception-caught
        except Exception:
            self.logger.warning("module had an error drawing ROIs.",
                                exc_info=True)

    def run_analysis(self, batch: bool = False) -> None:
        """
        Runs the analysis for the module.
        This will not create or re-create the ROIs.

        Parameters
        ----------
        batch : bool
            If this is being ran as part of a batch, e.g. in a collection (default is False)
        """
        try:
            if self.rois_loaded:
                for field in self.fields:
                    if field.reset_on_analysis:
                        field.reset_value()
                        field.reset_entry_style()
                        field.reset_label_style()
                self.analyse(batch)
                self.analysed = True
                if batch is False:
                    self.update_viewers()
                self.logger.info("Analysis Completed")
        # pylint: disable-next=broad-exception-caught
        except Exception:
            self.logger.warning("module had an error on analysis.",
                                exc_info=True)

    def create_and_run(self, context: BaseContext | None = None) -> None:
        """
        Creates the ROIs and runs the analysis.
        Context is obtained from `get_context` if not provided.

        Parameters
        ----------
        context : BaseContext or None, optional
            The context for the module (default is None).
        """
        self.create_rois(context)
        self.run_analysis()


class PhantomModule(BaseModule):
    """
    Module for handling phantom images.
    Has the same attributes and methods as `BaseModule` unless stated below.

    Uses `ManualPhantomManager` as the default `context_manager`.
    """
    context_manager: PhantomContextManager = ManualPhantomManager()
