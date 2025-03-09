"""
Classes:
 * BaseModule
 * PhantomModule
"""

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
from copy import copy
from typing import overload, Self, Literal, Any
from collections.abc import Callable

from pumpia.utilities.typing import DirectionType
from pumpia.image_handling.image_structures import ArrayImage
from pumpia.image_handling.roi_structures import BaseROI
from pumpia.widgets.scrolled_window import ScrolledWindow
from pumpia.widgets.viewers import BaseViewer
from pumpia.widgets.context_managers import (BaseContextManager,
                                             PhantomContextManager,
                                             BaseContextManagerGenerator,
                                             PhantomContextManagerGenerator,
                                             SimpleContextManagerGenerator,
                                             ManualPhantomManagerGenerator)
from pumpia.widgets.typing import ScreenUnits, Cursor, Padding, Relief, TakeFocusValue
from pumpia.module_handling.in_outs.simple import BaseInput, BaseOutput
from pumpia.module_handling.in_outs.viewer_ios import BaseViewerIO
from pumpia.module_handling.in_outs.roi_ios import BaseInputROI
from pumpia.module_handling.manager import Manager
from pumpia.module_handling.context import BaseContext, SimpleContext


class BaseModule(ABC, ttk.Frame):
    """
    Base class for modules.

    Class attribute `context_manager_generator` is used when running the module as stand alone,
    set to `SimpleContextManagerGenerator` by default.

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
    context_manager : BaseContextManager | None
    manager : Manager | None
    parent : tk.Misc | None
    verbose_name : str | None
    direction : Literal["horizontal", "vertical"]
    main_viewer : BaseViewer | None
        The main viewer for the module, used to get context etc.
        Defaults to first viewer defined if not provided in ViewerIOs.
        If multiple are set then defaults to the last defined ViewerIO.
    viewers : list[BaseViewer]
    rois : list[BaseInputROI]
    rois_loaded : bool
    analysed : bool
    input_count : int
    output_count : int
    viewer_count : int
    roi_count : int
    is_setup : bool

    Methods
    -------
    set_parent(parent: tk.Misc)
        Sets the parent widget.
    set_manager(manager: Manager)
        Sets the manager.
    setup(parent: tk.Misc | None = None, manager: Manager | None = None, context_manager: BaseContextManager | None = None)
        Sets up the module.
    get_context() -> BaseContext
        Returns the context for the module.
    load_commands()
        User can override this method to register command buttons for the collection.
    register_command(text: str, command: Callable[[], Any])
        Register a command so that it shows as a button in the main tab.
    link_rois_viewers():
        Link ROIs and viewers for manual drawing.
    post_roi_register(roi_input: BaseInputROI):
        Command ran after an roi is registered with an input.
    manual_roi_draw(self):
        Does a full manual draw of all ROIs
    draw_rois(context: BaseContext) -> None
        User should override this method to handle drawing the required ROIs.
    analyse()
        User should override this method to handle analysing the ROIs.
    on_image_load(viewer: BaseViewer) -> None
        User can add to this method to handle image load events by calling it using super.
    on_tab_select()
        Handles the event when a tab containing the module is selected.
    create_rois(context: BaseContext | None = None) -> None
        Creates the ROIs for the module.
    run_analysis() -> None
        Runs the analysis for the module.
    create_and_run(context: BaseContext | None = None) -> None
        Creates the ROIs and runs the analysis.
    setup_window(app: tk.Tk, direction: DirectionType = "Horizontal")
        Sets up the application window when running the module independently.
    run(direction: DirectionType = "Horizontal")
        Class method which runs the module independently.
    """
    context_manager_generator: BaseContextManagerGenerator = SimpleContextManagerGenerator()

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
        self.context_manager: BaseContextManager | None = context_manager
        self.manager: Manager | None = manager
        self.parent: tk.Misc | None = parent
        self._kw = kw
        self.verbose_name = verbose_name

        self._is_setup: bool = False

        if direction[0].lower() == "h":
            self.direction: Literal["horizontal", "vertical"] = "horizontal"
        else:
            self.direction = "vertical"

        self.main_viewer: BaseViewer | None = None
        self.viewers: list[BaseViewer] = []

        self.rois: list[BaseInputROI] = []
        self.analysed: bool = False

        self.input_count: int = 0
        self.output_count: int = 0
        self.viewer_count: int = 0
        self.roi_count: int = 0
        self.command_buttons_count: int = 0
        self._start_manual_draw: bool = False

        if self.manager is not None and self.parent is not None:
            self.setup()

    @property
    def is_setup(self) -> bool:
        """
        Whether the module is set up.
        """
        return self._is_setup

    def set_parent(self, parent: tk.Misc):
        """
        Sets the parent widget.
        """
        self.parent = parent

    def set_manager(self, manager: Manager):
        """
        Sets the manager.
        """
        self.manager = manager

    def setup(self,
              *,
              parent: tk.Misc | None = None,
              manager: Manager | None = None,
              context_manager: BaseContextManager | None = None):
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
                super().__init__(self.parent, name=self.verbose_name.lower(), ** self._kw)

            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=1)

            self.paned_window = ttk.Panedwindow(self, orient=self.direction)
            self.paned_window.grid(column=0, row=0, sticky="nsew")

            self.viewer_frame = ttk.Frame(self.paned_window)
            self.paned_window.add(self.viewer_frame, weight=1)
            self.io_frame = ScrolledWindow(self.paned_window)
            self.paned_window.add(self.io_frame.outer_frame)

            self.input_frame = ttk.Labelframe(self.io_frame, text="Inputs")
            self.output_frame = ttk.Labelframe(self.io_frame, text="Outputs")
            self.roi_frame = ttk.Labelframe(self.io_frame, text="ROIs")
            self.button_frame = ttk.Labelframe(self.io_frame, text="Commands")
            self.command_buttons: list[ttk.Button] = []

            if self.direction == "horizontal":
                self.input_frame.grid(column=0, row=0, sticky="nsew")
                self.output_frame.grid(column=0, row=1, sticky="nsew")
                self.roi_frame.grid(column=0, row=2, sticky="nsew")
                self.button_frame.grid(column=0, row=3, sticky="nsew")
            else:
                self.input_frame.grid(column=0, row=0, sticky="nsew")
                self.output_frame.grid(column=1, row=0, sticky="nsew")
                self.roi_frame.grid(column=2, row=0, sticky="nsew")
                self.button_frame.grid(column=3, row=0, sticky="nsew")

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
                    if isinstance(v, (BaseInput, BaseOutput)):
                        attr = copy(v)
                        setattr(self, k, attr)
                        if attr.verbose_name is None:
                            attr.verbose_name = k.replace("_", " ").title()
                        if isinstance(attr, BaseInput):
                            attr.set_parent(self.input_frame)
                            if not attr.hidden:
                                if self.direction == "horizontal":
                                    attr.label.grid(column=0,
                                                    row=self.input_count,
                                                    sticky="nsew")
                                    attr.entry.grid(column=1,
                                                    row=self.input_count,
                                                    sticky="nsew")
                                else:
                                    attr.label.grid(column=2 * self.input_count,
                                                    row=0,
                                                    sticky="nsew")
                                    attr.entry.grid(column=2 * self.input_count + 1,
                                                    row=0,
                                                    sticky="nsew")
                            self.input_count += 1
                        elif isinstance(attr, BaseOutput):
                            attr.set_parent(self.output_frame)
                            if not attr.hidden:
                                if self.direction == "horizontal":
                                    attr.label.grid(column=0,
                                                    row=self.output_count,
                                                    sticky="nsew")
                                    attr.value_label.grid(column=1,
                                                          row=self.output_count,
                                                          sticky="nsew")
                                else:
                                    attr.label.grid(column=2 * self.output_count,
                                                    row=0,
                                                    sticky="nsew")
                                    attr.value_label.grid(column=2 * self.output_count + 1,
                                                          row=0,
                                                          sticky="nsew")
                            self.output_count += 1
                    elif isinstance(v, BaseViewerIO):
                        attr = v.viewer_type(self.viewer_frame,
                                             manager=self.manager,
                                             allow_drag_drop=v.allow_drag_drop,
                                             allow_drawing_rois=v.allow_drawing_rois,
                                             allow_changing_rois=v.allow_changing_rois,
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

                    elif isinstance(v, BaseInputROI):
                        attr = copy(v)
                        setattr(self, k, attr)
                        if attr.name is None:
                            attr.name = k.replace("_", " ").title()
                        self.rois.append(attr)
                        attr.set_manager(self.manager)
                        attr.set_parent(self.roi_frame)
                        attr.post_register_command = self.post_roi_register

                        if self.direction == "horizontal":
                            attr.select_button.grid(column=0,
                                                    row=self.roi_count,
                                                    sticky="nsew")
                            if attr.allow_manual_draw:
                                attr.draw_button.grid(column=1,
                                                      row=self.roi_count,
                                                      sticky="nsew")

                        else:
                            attr.select_button.grid(column=2 * self.roi_count,
                                                    row=0,
                                                    sticky="nsew")
                            if attr.allow_manual_draw:
                                attr.draw_button.grid(column=2 * self.roi_count + 1,
                                                      row=0,
                                                      sticky="nsew")
                        self.roi_count += 1
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

        context_frame = ScrolledWindow(frame)
        context_options = cls.context_manager_generator(context_frame, man, direction="H")
        context_options.grid(column=0, row=0, sticky="nsew")
        frame.add(context_frame.outer_frame)

        module = cls(frame, man, context_manager=context_options, direction=direction)
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
                        sticky="nsew")
            self.command_buttons_count += 1

        else:
            button.grid(column=self.command_buttons_count,
                        row=0,
                        rowspan=2,
                        sticky="nsew")
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

    def post_roi_register(self, roi_input: BaseInputROI):
        """
        Command ran after an roi is registered with an input.

        Parameters
        ----------
        roi_input : BaseInputROI
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

    @abstractmethod
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
        if context is None:
            context = self.get_context()
        self.draw_rois(context, batch)

    def run_analysis(self, batch: bool = False) -> None:
        """
        Runs the analysis for the module.
        This will not create or re-create the ROIs.

        Parameters
        ----------
        batch : bool
            If this is being ran as part of a batch, e.g. in a collection (default is False)
        """
        if self.rois_loaded:
            self.analyse(batch)
            self.analysed = True

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

    Uses `ManualPhantomManagerGenerator` as the default `context_manager_generator`.

    Adds two buttons for showing the phantom boundary and boundbox compared with `BaseModule`.
    """
    context_manager_generator: PhantomContextManagerGenerator = ManualPhantomManagerGenerator()

    @overload
    def __init__(
        self,
        parent: tk.Misc | None = None,
        manager: Manager | None = None,
        context_manager: PhantomContextManager | None = None,
        *,
        verbose_name: str | None = None,
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
    def __init__(self,
                 parent: tk.Misc | None = None,
                 manager: Manager | None = None,
                 context_manager: PhantomContextManager | None = None,
                 *,
                 verbose_name: str | None = None,
                 direction: DirectionType = "Horizontal",
                 **kw): ...

    # pylint: disable-next=super-init-not-called
    def __init__(self,
                 parent: tk.Misc | None = None,
                 manager: Manager | None = None,
                 # _init__ overwrite is to change type here
                 context_manager: PhantomContextManager | None = None,
                 *,
                 verbose_name: str | None = None,
                 direction: DirectionType = "Horizontal",
                 **kw):
        super().__init__(parent,
                         manager,
                         context_manager,
                         verbose_name=verbose_name,
                         direction=direction, ** kw)

    @classmethod
    def setup_window(cls,
                     app: tk.Tk,
                     direction: DirectionType = "Horizontal"):
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

        context_frame = ScrolledWindow(frame)
        context_options = cls.context_manager_generator(context_frame,
                                                        man,
                                                        direction="H")
        context_options.grid(column=0, row=0, sticky="nsew")
        frame.add(context_frame.outer_frame)

        module = cls(frame, man, context_manager=context_options, direction=direction)
        frame.add(module, weight=1)

        if module.main_viewer is not None:

            def bbox_command():
                if module.main_viewer is not None:
                    if isinstance(module.main_viewer.image, ArrayImage):
                        context_options.get_bound_box_roi(module.main_viewer.image)

            bbox_button = ttk.Button(context_frame,
                                     command=bbox_command,
                                     text="Draw Phantom Boundbox")
            bbox_button.grid(column=1, row=0, sticky="nsew")

            def boundary_command():
                if module.main_viewer is not None:
                    if isinstance(module.main_viewer.image, ArrayImage):
                        context_options.get_boundary_roi(module.main_viewer.image)

            boundary_button = ttk.Button(context_frame,
                                         command=boundary_command,
                                         text="Draw Phantom Boundary")
            boundary_button.grid(column=2, row=0, sticky="nsew")

    @classmethod
    def run(cls: type[Self],
            direction: DirectionType = "Horizontal"):
        app = tk.Tk()
        cls.setup_window(app, direction)
        app.mainloop()
