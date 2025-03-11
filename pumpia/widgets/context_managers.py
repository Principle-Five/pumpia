"""
Classes:
 * AutoPhantomManager
 * AutoPhantomManagerGenerator
 * BaseContextManager
 * BaseContextManagerGenerator
 * ManualPhantomManager
 * ManualPhantomManagerGenerator
 * PhantomContextManager
 * PhantomContextManagerGenerator
 * SimpleContextManager
 * SimpleContextManagerGenerator
 """

import tkinter as tk
from tkinter import ttk
from typing import overload, Literal
from abc import ABC, abstractmethod

from pumpia.widgets.typing import ScreenUnits, Cursor, Padding, Relief, TakeFocusValue
from pumpia.widgets.entry_boxes import IntEntry, PercEntry, FloatEntry
from pumpia.utilities.typing import DirectionType, SideType
from pumpia.utilities.feature_utils import (phantom_boundbox_manual,
                                            phantom_boundary_automatic)
from pumpia.image_handling.roi_structures import BaseROI, RectangleROI, EllipseROI
from pumpia.image_handling.image_structures import ArrayImage
from pumpia.module_handling.manager import Manager
from pumpia.module_handling.context import (BaseContext,
                                            PhantomContext,
                                            BoundBoxContext,
                                            SimpleContext,
                                            PhantomShape,
                                            PhantomShapes)

side_map: dict[str, SideType] = {"Top": "top",
                                 "Bottom": "bottom",
                                 "Left": "left",
                                 "Right": "right"}
inv_side_map: dict[SideType, str] = {v: k for k, v in side_map.items()}
side_opts = list(side_map.keys())


class BaseContextManager(ABC, ttk.Labelframe):
    """
    Base class for context managers.

    Parameters
    ----------
    parent : tk.Misc
        The parent widget.
    manager : Manager
        The manager object.
    direction : DirectionType, optional
        The direction of the child widgets in the frame (default is "Vertical").
    text : float or str, optional
        The text for the labelframe (default is "Bound Box Options").
    **kw : dict
        Additional keyword arguments as defined by ttk Labelframe.
    """

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Context Manager",
                 *,
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
                 name: str = ...,
                 padding: Padding = ...,
                 relief: Relief = ...,  # undocumented
                 style: str = "",
                 takefocus: TakeFocusValue = "",
                 underline: int = -1,
                 width: ScreenUnits = 0,
                 ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 **kw) -> None: ...

    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 **kw) -> None:
        super().__init__(parent, text=text, **kw)
        self.direction: DirectionType = direction
        self.manager: Manager = manager

    @abstractmethod
    def get_context(self, image: ArrayImage) -> BaseContext:
        """
        Users should override this method to return the context for the given image.
        """


class SimpleContextManager(BaseContextManager):
    """
    Simple context manager that returns the center context of the image.
    Has the same parameters as BaseContextManager.
    """

    def get_context(self, image: ArrayImage) -> SimpleContext:
        """
        Gets the center context for the given image.
        """
        return SimpleContext(image.array.shape[2] / 2,
                             image.array.shape[1] / 2,
                             image.array.shape[2],
                             image.array.shape[1])


class PhantomContextManager(BaseContextManager):
    """
    Context manager for phantom images.
    Has the same parameters as BaseContextManager.
    """
    shape_map: dict[str, None | PhantomShape] = {"Any": None,
                                                 "Ellipse": "ellipse",
                                                 "Rectangle": "rectangle"}
    inv_shape_map: dict[None | PhantomShape, str] = {v: k for k, v in shape_map.items()}
    shape_opts = list(shape_map.keys())

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 *,
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
                 name: str = ...,
                 padding: Padding = ...,
                 relief: Relief = ...,  # undocumented
                 style: str = "",
                 takefocus: TakeFocusValue = "",
                 underline: int = -1,
                 width: ScreenUnits = 0,
                 ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 **kw) -> None: ...

    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 **kw) -> None:
        super().__init__(parent, manager=manager, direction=direction, text=text, **kw)
        self.shape: PhantomShapes = shape

    def _show_rectangles(self,
                         bounds: BoundBoxContext | PhantomContext,
                         image: ArrayImage,
                         secondary_images: None | list[ArrayImage] = None,
                         name: str = "Phantom Bound Box") -> RectangleROI:
        """
        Shows the boundbox or rectangle boundary for the phantom as an ROI on the image.

        Parameters
        ----------
        bounds : BoundBoxContext or PhantomContext
            The bounds for the rectangles.
        image : ArrayImage
            The image to show the rectangles on.
        secondary_images : list of ArrayImage or None, optional
            The secondary images to show the rectangles on (default is None).
        name : str, optional
            The name of the rectangles (default is "Phantom Bound Box").
        """
        roi = RectangleROI(image,
                           bounds.xmin,
                           bounds.ymin,
                           bounds.xmax,
                           bounds.ymax,
                           slice_num=image.current_slice,
                           name=name,
                           replace=True)
        self.manager.add_roi(roi)
        if secondary_images is not None:
            for s_image in secondary_images:
                if s_image != image:
                    copied_roi = roi.copy_to_image(s_image, s_image.current_slice, name, True)
                    self.manager.add_roi(copied_roi)
        return roi

    def _show_ellipses(self,
                       bounds: BoundBoxContext | PhantomContext,
                       image: ArrayImage,
                       secondary_images: None | list[ArrayImage] = None,
                       name: str = "Phantom Boundary") -> EllipseROI:
        """
        Shows the boundary ellipse as an ROI on the image.

        Parameters
        ----------
        bounds : BoundBoxContext or PhantomContext
            The bounds for the ellipses.
        image : ArrayImage
            The image to show the ellipses on.
        secondary_images : list of ArrayImage or None, optional
            The secondary images to show the ellipses on (default is None).
        name : str, optional
            The name of the ellipses (default is "Phantom Boundary").
        """
        xc = round((bounds.xmax + bounds.xmin) / 2)
        a = round((bounds.xmax - bounds.xmin) / 2)
        yc = round((bounds.ymax + bounds.ymin) / 2)
        b = round((bounds.ymax - bounds.ymin) / 2)
        roi = EllipseROI(image,
                         xc,
                         yc,
                         a,
                         b,
                         slice_num=image.current_slice,
                         name=name,
                         replace=True)

        self.manager.add_roi(roi)
        if secondary_images is not None:
            for s_image in secondary_images:
                if s_image != image:
                    copied_roi = roi.copy_to_image(s_image,
                                                   s_image.current_slice,
                                                   name,
                                                   True)
                    self.manager.add_roi(copied_roi)
        return roi

    def get_bound_box_roi(self,
                          image: ArrayImage,
                          secondary_images: None | list[ArrayImage] = None,
                          ) -> RectangleROI:
        """
        Gets the bound box ROI for the given image.

        Parameters
        ----------
        image : ArrayImage
            The image to get the bound box ROI for.
        secondary_images : list of ArrayImage or None, optional
            The secondary images to get the bound box ROI for (default is None).
        """
        bounds = self.get_context(image)
        roi = self._show_rectangles(bounds, image, secondary_images, "Phantom Bound Box")

        return roi

    def get_boundary_roi(self,
                         image: ArrayImage,
                         secondary_images: None | list[ArrayImage] = None,
                         ) -> BaseROI:
        """
        Gets the boundary ROI for the given image.

        Parameters
        ----------
        image : ArrayImage
            The image to show the ROI on.
        secondary_images : list of ArrayImage or None, optional
            The secondary images to copy the ROI to (default is None).
        """
        bounds = self.get_context(image)
        if bounds.shape == "rectangle":
            roi = self._show_rectangles(bounds, image, secondary_images, "Phantom Boundary")
        else:
            roi = self._show_ellipses(bounds, image, secondary_images, "Phantom Boundary")
        return roi

    @abstractmethod
    def get_context(self, image: ArrayImage) -> PhantomContext:
        pass


class ManualPhantomManager(PhantomContextManager):
    """
    Context manager for phantom images, user inputs shape and boundbox manually.
    Has the same parameters as BaseContextManager unless stated below.

    Parameters
    ----------
    shape : PhantomShapes, optional
        The shape of the phantom (default is None).
    """

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 *,
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
                 name: str = ...,
                 padding: Padding = ...,
                 relief: Relief = ...,  # undocumented
                 style: str = "",
                 takefocus: TakeFocusValue = "",
                 underline: int = -1,
                 width: ScreenUnits = 0,
                 ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 **kw) -> None: ...

    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 **kw) -> None:
        super().__init__(parent, manager=manager, shape=shape, direction=direction, text=text, **kw)

        self.shape_frame = ttk.Labelframe(self, text="Shape")
        self.boundary_frame = ttk.Labelframe(self, text="Boundary (pixels)")

        self.shape_radios: list[ttk.Radiobutton] = []
        self.shape_var = tk.StringVar(self)
        if shape is None:
            self.shape_var.set(self.shape_opts[1])
        elif isinstance(shape, list):
            self.shape_var.set(self.inv_shape_map[shape[0]])
        else:
            self.shape_var.set(self.inv_shape_map[shape])

        for opt in self.shape_opts:
            if opt != self.inv_shape_map[None]:
                button = ttk.Radiobutton(self.shape_frame,
                                         value=opt,
                                         text=opt,
                                         variable=self.shape_var)
                self.shape_radios.append(button)

        self.xmin_var = tk.IntVar(self, value=0)
        self.xmax_var = tk.IntVar(self, value=1)
        self.ymin_var = tk.IntVar(self, value=0)
        self.ymax_var = tk.IntVar(self, value=1)

        self.xmin_label = ttk.Label(self.boundary_frame, text="xmin:")
        self.xmax_label = ttk.Label(self.boundary_frame, text="xmax:")
        self.ymin_label = ttk.Label(self.boundary_frame, text="ymin:")
        self.ymax_label = ttk.Label(self.boundary_frame, text="ymax:")

        self.xmin_entry = IntEntry(self.boundary_frame, textvariable=self.xmin_var)
        self.xmax_entry = IntEntry(self.boundary_frame, textvariable=self.xmax_var)
        self.ymin_entry = IntEntry(self.boundary_frame, textvariable=self.ymin_var)
        self.ymax_entry = IntEntry(self.boundary_frame, textvariable=self.ymax_var)

        if self.direction[0].lower() == "h":
            self.boundary_frame.grid(column=0, row=0, sticky="nsew")
            self.xmin_label.grid(column=0, row=0, sticky="nsew")
            self.xmin_entry.grid(column=1, row=0, sticky="nsew")
            self.xmax_label.grid(column=2, row=0, sticky="nsew")
            self.xmax_entry.grid(column=3, row=0, sticky="nsew")
            self.ymin_label.grid(column=4, row=0, sticky="nsew")
            self.ymin_entry.grid(column=5, row=0, sticky="nsew")
            self.ymax_label.grid(column=6, row=0, sticky="nsew")
            self.ymax_entry.grid(column=7, row=0, sticky="nsew")

            self.shape_frame.grid(column=1, row=0, sticky="nsew")

            for c, radio in enumerate(self.shape_radios):
                radio.grid(column=c, row=0, sticky="nsew")

        else:
            self.boundary_frame.grid(column=0, row=0, sticky="nsew")
            self.xmin_label.grid(column=0, row=0, sticky="nsew")
            self.xmin_entry.grid(column=1, row=0, sticky="nsew")
            self.xmax_label.grid(column=0, row=1, sticky="nsew")
            self.xmax_entry.grid(column=1, row=1, sticky="nsew")
            self.ymin_label.grid(column=0, row=2, sticky="nsew")
            self.ymin_entry.grid(column=1, row=2, sticky="nsew")
            self.ymax_label.grid(column=0, row=3, sticky="nsew")
            self.ymax_entry.grid(column=1, row=3, sticky="nsew")

            self.shape_frame.grid(column=0, row=1, sticky="nsew")

            for r, radio in enumerate(self.shape_radios):
                radio.grid(column=0, row=r, sticky="nsew")

    def get_context(self, image: ArrayImage) -> PhantomContext:
        """
        Gets the context based on the user inputs
        """
        phantom_shape: None | PhantomShape = self.shape_map[self.shape_var.get()]
        if phantom_shape is None:
            phantom_shape = "ellipse"
        xmin = min(self.xmin_var.get(), self.xmax_var.get())
        xmax = max(self.xmin_var.get(), self.xmax_var.get())
        ymin = min(self.ymin_var.get(), self.ymax_var.get())
        ymax = max(self.ymin_var.get(), self.ymax_var.get())
        return PhantomContext(xmin,
                              xmax,
                              ymin,
                              ymax,
                              phantom_shape)


class AutoPhantomManager(PhantomContextManager):
    """
    Context manager for phantom images, using the `phantom_boundbox_manual`
    or `phantom_boundary_automatic` functions.
    Has the same parameters as BaseContextManager unless stated below.

    Parameters
    ----------
    mode : Literal["auto", "manual"], optional
        The initial mode of the manager (default is "auto").
    sensitivity : int, optional
        The initial sensitivity for boundary detection (default is 3).
    top_perc : int, optional
        The initial maximum percentage for boundary detection (default is 95).
    iterations : int, optional
        The initial number of iterations for boundary detection (default is 2).
    cull_perc : int, optional
        The initial cull percentage for boundary detection (default is 80).
    bubble_offset : int, optional
        The initial bubble offset for boundary detection (default is 0).
    bubble_side : SideType, optional
        The initial side of the bubble for boundary detection (default is "top").
    shape : PhantomShapes, optional
        The initial shape of the phantom (default is None).
    """

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 mode: Literal["auto", "manual"] = "auto",
                 sensitivity: int = 3,
                 top_perc: int = 95,
                 iterations: int = 2,
                 cull_perc: int = 80,
                 bubble_offset: int = 0,
                 bubble_side: SideType = "top",
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 *,
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
                 name: str = ...,
                 padding: Padding = ...,
                 relief: Relief = ...,  # undocumented
                 style: str = "",
                 takefocus: TakeFocusValue = "",
                 underline: int = -1,
                 width: ScreenUnits = 0,
                 ) -> None: ...

    @overload
    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 mode: Literal["auto", "manual"] = "auto",
                 sensitivity: int = 3,
                 top_perc: int = 95,
                 iterations: int = 2,
                 cull_perc: int = 80,
                 bubble_offset: int = 0,
                 bubble_side: SideType = "top",
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 **kw) -> None: ...

    def __init__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 mode: Literal["auto", "manual"] = "auto",
                 sensitivity: int = 3,
                 top_perc: int = 95,
                 iterations: int = 2,
                 cull_perc: int = 80,
                 bubble_offset: int = 0,
                 bubble_side: SideType = "top",
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
                 **kw) -> None:
        super().__init__(parent, manager=manager, shape=shape, direction=direction, text=text, **kw)

        self.general_frame = ttk.Labelframe(self, text="General")
        self.manual_frame = ttk.Labelframe(self, text="Manual")
        self.automatic_frame = ttk.Labelframe(self, text="Automatic")
        self.mode_frame = ttk.Labelframe(self.general_frame, text="Mode")
        self.auto_shape_frame = ttk.Labelframe(self.automatic_frame, text="Shapes")
        self.manual_shape_frame = ttk.Labelframe(self.manual_frame, text="Shape")
        self.fine_tune_frame = ManualPhantomManager(self, manager, shape, direction, "Fine Tune")

        self.sensitivity_var = tk.DoubleVar(self, value=sensitivity)
        self.sensitivity_label = ttk.Label(self.general_frame, text="Sensitivity:")
        self.sensitivity_entry = FloatEntry(self.general_frame, textvariable=self.sensitivity_var)

        self.top_perc_var = tk.DoubleVar(self, value=top_perc)
        self.top_perc_label = ttk.Label(self.general_frame, text="Maximum Percentage:")
        self.top_perc_entry = PercEntry(self.general_frame, textvariable=self.top_perc_var)

        self.shape_checks: list[ttk.Checkbutton] = []
        self.shape_vars: list[tk.StringVar] = []
        for opt in self.shape_opts:
            if (opt != self.inv_shape_map[None]
                and ((isinstance(shape, list) and self.shape_map[opt] in shape)
                     or self.shape_map[opt] == shape
                     or shape is None)):
                var = tk.StringVar(self, value=opt)
                self.shape_vars.append(var)
                if isinstance(shape, list) or shape is None:
                    button = ttk.Checkbutton(self.auto_shape_frame,
                                             offvalue="",
                                             onvalue=opt,
                                             text=opt,
                                             variable=var)
                    self.shape_checks.append(button)

        self.shape_radios: list[ttk.Radiobutton] = []
        self.man_shape_var = tk.StringVar(self)
        if shape is None:
            self.man_shape_var.set(self.shape_opts[1])
        elif isinstance(shape, list):
            self.man_shape_var.set(self.inv_shape_map[shape[0]])
        else:
            self.man_shape_var.set(self.inv_shape_map[shape])

        for opt in self.shape_opts:
            if (opt != self.inv_shape_map[None]
                and ((isinstance(shape, list) and self.shape_map[opt] in shape)
                     or self.shape_map[opt] == shape
                     or shape is None)):
                button = ttk.Radiobutton(self.manual_shape_frame,
                                         value=opt,
                                         text=opt,
                                         variable=self.man_shape_var)
                self.shape_radios.append(button)

        self.mode_var = tk.StringVar(self, value=mode)
        self.auto_radio = ttk.Radiobutton(self.mode_frame,
                                          text="Auto Fitting",
                                          variable=self.mode_var,
                                          value="auto",
                                          command=self._update_mode)
        self.manual_radio = ttk.Radiobutton(self.mode_frame,
                                            text="Manual Boundary Control",
                                            variable=self.mode_var,
                                            value="manual",
                                            command=self._update_mode)
        self.fine_tune_radio = ttk.Radiobutton(self.mode_frame,
                                               text="Full Manual Control",
                                               variable=self.mode_var,
                                               value="fine tune",
                                               command=self._update_mode)
        self.on_image_radio = ttk.Radiobutton(self.mode_frame,
                                              text="On Image",
                                              variable=self.mode_var,
                                              value="on image",
                                              command=self._update_mode)

        self.bubble_offset_var = tk.IntVar(self, value=bubble_offset)
        self.bubble_offset_label = ttk.Label(self.manual_frame, text="Bubble Offset (Px):")
        self.bubble_offset_entry = IntEntry(self.manual_frame, textvariable=self.bubble_offset_var)

        self.bubble_side_var = tk.StringVar(self, inv_side_map[bubble_side])
        self.bubble_side_label = ttk.Label(self.manual_frame, text="Bubble Side:")
        self.bubble_side_combo = ttk.Combobox(self.manual_frame,
                                              textvariable=self.bubble_side_var,
                                              values=list(side_opts),
                                              height=4,
                                              state="readonly")

        self.iterations_var = tk.IntVar(self, value=iterations)
        self.iterations_label = ttk.Label(self.automatic_frame, text="Iterations:")
        self.iterations_entry = IntEntry(self.automatic_frame, textvariable=self.iterations_var)

        self.cull_perc_var = tk.DoubleVar(self, value=cull_perc)
        self.cull_perc_label = ttk.Label(self.automatic_frame, text="Cull Percentage:")
        self.cull_perc_entry = PercEntry(self.automatic_frame, textvariable=self.cull_perc_var)

        if self.direction[0].lower() == "h":
            self.general_frame.grid(column=0, row=0, sticky="nsew")

            self.sensitivity_label.grid(column=0, row=0, sticky="nsew")
            self.sensitivity_entry.grid(column=1, row=0, sticky="ew")
            self.top_perc_label.grid(column=2, row=0, sticky="nsew")
            self.top_perc_entry.grid(column=3, row=0, sticky="ew")
            self.mode_frame.grid(column=4, row=0, sticky="nsew")
            self.auto_radio.grid(column=0, row=0, sticky="nsew")
            self.manual_radio.grid(column=0, row=1, sticky="nsew")

            # manual frame
            self.bubble_offset_label.grid(column=0, row=0, sticky="nsew")
            self.bubble_offset_entry.grid(column=1, row=0, sticky="nsew")
            self.bubble_side_label.grid(column=2, row=0, sticky="nsew")
            self.bubble_side_combo.grid(column=3, row=0, sticky="nsew")
            self.manual_shape_frame.grid(column=4, row=0, sticky="nsew")

            for c, radio in enumerate(self.shape_radios):
                radio.grid(column=c, row=0, sticky="nsew")

            # automatic frame
            self.iterations_label.grid(column=2, row=0, sticky="nsew")
            self.iterations_entry.grid(column=3, row=0, sticky="nsew")
            self.cull_perc_label.grid(column=4, row=0, sticky="nsew")
            self.cull_perc_entry.grid(column=5, row=0, sticky="nsew")
            self.auto_shape_frame.grid(column=6, row=0, sticky="nsew")

            for c, check in enumerate(self.shape_checks):
                check.grid(column=c, row=0, sticky="nsew")

        else:
            self.general_frame.grid(column=0, row=0, sticky="nsew")

            self.sensitivity_label.grid(column=0, row=0, sticky="nsew")
            self.sensitivity_entry.grid(column=1, row=0, sticky="nsew")
            self.top_perc_label.grid(column=0, row=1, sticky="nsew")
            self.top_perc_entry.grid(column=1, row=1, sticky="nsew")
            self.mode_frame.grid(column=0, row=2, columnspan=2, sticky="nsew")
            self.auto_radio.grid(column=0, row=0, sticky="nsew")
            self.manual_radio.grid(column=0, row=1, sticky="nsew")

            # manual frame
            self.bubble_offset_label.grid(column=0, row=0, sticky="nsew")
            self.bubble_offset_entry.grid(column=1, row=0, sticky="nsew")
            self.bubble_side_label.grid(column=0, row=1, sticky="nsew")
            self.bubble_side_combo.grid(column=1, row=1, sticky="nsew")
            self.manual_shape_frame.grid(column=0, row=2, columnspan=2, sticky="nsew")

            for r, radio in enumerate(self.shape_radios):
                radio.grid(column=0, row=r, sticky="nsew")

            # automatic frame
            self.iterations_label.grid(column=0, row=1, sticky="nsew")
            self.iterations_entry.grid(column=1, row=1, sticky="nsew")
            self.cull_perc_label.grid(column=0, row=2, sticky="nsew")
            self.cull_perc_entry.grid(column=1, row=2, sticky="nsew")
            self.auto_shape_frame.grid(column=0, row=3, columnspan=2, sticky="nsew")

            for r, check in enumerate(self.shape_checks):
                check.grid(column=0, row=r, sticky="nsew")

        self._update_mode()

    def _manual_bound_box(self, image: ArrayImage) -> PhantomContext:
        """
        Gets the bound box for the image using `phantom_boundbox_manual`.
        """
        array = image.current_slice_array
        sensitivity = self.sensitivity_var.get()
        top_perc = self.top_perc_var.get()
        bubble_offset = self.bubble_offset_var.get()
        bubble_side = side_map[self.bubble_side_var.get()]
        bounds = phantom_boundbox_manual(array,
                                         sensitivity,
                                         top_perc,
                                         bubble_offset,
                                         bubble_side)
        phantom_shape: None | PhantomShape = self.shape_map[self.man_shape_var.get()]
        if phantom_shape is None:
            phantom_shape = "ellipse"
        phantom = PhantomContext(bounds.xmin,
                                 bounds.xmax,
                                 bounds.ymin,
                                 bounds.ymax,
                                 phantom_shape)
        self._show_fine_tune(phantom)
        return phantom

    def _auto_bound_box(self, image: ArrayImage) -> PhantomContext:
        """
        Gets the bound box for the image using `phantom_boundary_automatic`.
        """
        array = image.current_slice_array
        sensitivity = self.sensitivity_var.get()
        top_perc = self.top_perc_var.get()
        iterations = self.iterations_var.get()
        cull_perc = self.cull_perc_var.get()
        shapes: list[PhantomShape] = []
        for var in self.shape_vars:
            if var.get() != "":
                shape = self.shape_map[var.get()]
                if shape is not None:
                    shapes.append(shape)
        bounds = phantom_boundary_automatic(array,
                                            sensitivity,
                                            top_perc,
                                            iterations,
                                            cull_perc,
                                            shapes)
        self._show_fine_tune(bounds)
        return bounds

    def _update_mode(self):
        """
        Updates the mode of the context manager.
        """
        self.manual_frame.grid_forget()
        self.automatic_frame.grid_forget()
        self.fine_tune_frame.grid_forget()
        if self.direction[0].lower() == "h":
            if self.mode_var.get() == "manual":
                self.manual_frame.grid(column=2, row=0, sticky="nsew")
            elif self.mode_var.get() == "auto":
                self.automatic_frame.grid(column=2, row=0, sticky="nsew")
            elif self.mode_var.get() == "fine tune":
                self.fine_tune_frame.grid(column=2, row=0, sticky="nsew")

        else:
            if self.mode_var.get() == "manual":
                self.manual_frame.grid(column=0, row=1, sticky="nsew")
            elif self.mode_var.get() == "auto":
                self.automatic_frame.grid(column=0, row=1, sticky="nsew")
            elif self.mode_var.get() == "fine tune":
                self.fine_tune_frame.grid(column=0, row=1, sticky="nsew")

    def _show_on_image(self):
        """
        Shows the on image radio button.
        """
        self.on_image_radio.grid(column=0, row=3, sticky="nsew")

    def _show_fine_tune(self, context: PhantomContext):
        """
        Shows the fine tune frame.
        """
        self.fine_tune_frame.xmin_var.set(context.xmin)
        self.fine_tune_frame.xmax_var.set(context.xmax)
        self.fine_tune_frame.ymin_var.set(context.ymin)
        self.fine_tune_frame.ymax_var.set(context.ymax)
        self.fine_tune_frame.shape_var.set(self.inv_shape_map[context.shape])
        self.fine_tune_radio.grid(column=0, row=2, sticky="nsew")

    def get_boundary_roi(self,
                         image: ArrayImage,
                         secondary_images: None | list[ArrayImage] = None,
                         ) -> BaseROI:
        roi = super().get_boundary_roi(image, secondary_images)
        self._show_on_image()
        return roi

    def get_context(self, image: ArrayImage) -> PhantomContext:
        """
        Gets the context for the given image.
        """
        if self.mode_var.get() == "manual":
            return self._manual_bound_box(image)
        elif self.mode_var.get() == "auto":
            return self._auto_bound_box(image)
        elif self.mode_var.get() == "fine tune":
            return self.fine_tune_frame.get_context(image)
        else:
            try:
                roi = image["Phantom Boundary"]
                if isinstance(roi, RectangleROI):
                    return PhantomContext(roi.xmin,
                                          roi.xmax,
                                          roi.ymin,
                                          roi.ymax,
                                          "rectangle")
                else:
                    return PhantomContext(roi.xmin,
                                          roi.xmax,
                                          roi.ymin,
                                          roi.ymax,
                                          "ellipse")
            except KeyError as exc:
                raise ValueError("Image has not had boundaries found") from exc


class BaseContextManagerGenerator[ContextManagerT: BaseContextManager](ABC):
    """
    Base class for context manager generators.
    """

    context_manager_type: type[ContextManagerT]

    @overload
    def __init__(self,
                 *,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
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
                 name: str = ...,
                 padding: Padding = ...,
                 relief: Relief = ...,  # undocumented
                 style: str = "",
                 takefocus: TakeFocusValue = "",
                 underline: int = -1,
                 width: ScreenUnits = 0,
                 ) -> None: ...

    @overload
    def __init__(self,
                 **kw) -> None: ...

    def __init__(self,
                 **kw) -> None:
        self.kw = kw

    def __call__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 direction: DirectionType | None = None,) -> ContextManagerT:
        """
        Creates and returns a context manager.
        """
        if direction is not None:
            self.kw["direction"] = direction
        return self.context_manager_type(parent=parent,
                                         manager=manager,
                                         **self.kw)


class SimpleContextManagerGenerator(BaseContextManagerGenerator[SimpleContextManager]):
    """
    Generator for SimpleContextManager.
    """
    context_manager_type = SimpleContextManager


class PhantomContextManagerGenerator[ContextManagerT: PhantomContextManager](BaseContextManagerGenerator):
    """
    Generator for PhantomContextManager.
    """

    context_manager_type: type[ContextManagerT]

    @overload
    def __init__(self,
                 *,
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
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
                 name: str = ...,
                 padding: Padding = ...,
                 relief: Relief = ...,  # undocumented
                 style: str = "",
                 takefocus: TakeFocusValue = "",
                 underline: int = -1,
                 width: ScreenUnits = 0,
                 ) -> None: ...

    @overload
    def __init__(self,
                 **kw) -> None: ...

    def __init__(self,
                 **kw) -> None:
        super().__init__(**kw)

    def __call__(self,
                 parent: tk.Misc,
                 manager: Manager,
                 direction: DirectionType | None = None,) -> ContextManagerT:
        """
        Creates and returns a phantom context manager.
        """
        if direction is not None:
            self.kw["direction"] = direction
        return self.context_manager_type(parent=parent,
                                         manager=manager,
                                         **self.kw)


class ManualPhantomManagerGenerator(PhantomContextManagerGenerator[ManualPhantomManager]):
    """
    Generator for ManualPhantomManager.
    """
    context_manager_type = ManualPhantomManager


class AutoPhantomManagerGenerator(PhantomContextManagerGenerator[AutoPhantomManager]):
    """
    Generator for AutoPhantomManager.
    """
    context_manager_type = AutoPhantomManager

    @overload
    def __init__(self,
                 *,
                 mode: Literal["auto", "manual"] = "auto",
                 sensitivity: int = 3,
                 top_perc: int = 95,
                 iterations: int = 2,
                 cull_perc: int = 80,
                 bubble_offset: int = 0,
                 bubble_side: SideType = "top",
                 shape: PhantomShapes = None,
                 direction: DirectionType = "Vertical",
                 text: float | str = "Bound Box Options",
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
                 name: str = ...,
                 padding: Padding = ...,
                 relief: Relief = ...,  # undocumented
                 style: str = "",
                 takefocus: TakeFocusValue = "",
                 underline: int = -1,
                 width: ScreenUnits = 0,
                 ) -> None: ...

    @overload
    def __init__(self,
                 **kw) -> None: ...

    def __init__(self,
                 **kw) -> None:
        super().__init__(**kw)
