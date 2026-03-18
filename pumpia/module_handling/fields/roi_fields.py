"""
Contains inputs/outputs for ROIs
"""

from collections.abc import Callable
from typing import overload, Any, Self
import tkinter as tk
from tkinter import ttk
from pumpia.module_handling.manager import Manager
from pumpia.widgets.viewers import (BaseViewer,
                                    ManualROIType)
from pumpia.image_handling.roi_structures import (BaseROI,
                                                  EllipseROI,
                                                  RectangleROI,
                                                  LineROI,
                                                  Angle,
                                                  PointROI)
from pumpia.image_handling.image_structures import ArrayImage
from pumpia.module_handling.modules import BaseModule


class _ROIFields:
    def __init__(self, obj: BaseModule) -> None:
        self.obj: BaseModule = obj
        self.rois_dict: dict[str, BaseROIField] = {}

    def __iter__(self):
        for window in self.rois_dict.values():
            yield window


class _ROIFieldsMeta:
    def __init__(self) -> None:
        self.rois: dict[str, BaseROIField] = {}
        self.name: str = ""
        self.private_name: str = "_"

    @property
    def roi_names(self) -> list[str]:
        return list(self.rois.keys())

    def __set_name__(self, owner: type[BaseModule], name: str):
        self.name = name
        self.private_name = "_" + name

    @overload
    def __get__(self, obj: BaseModule, owner=None) -> _ROIFields: ...
    @overload
    def __get__(self, obj: None, owner=None) -> Self: ...

    def __get__(self, obj: BaseModule | None, owner=None) -> _ROIFields | Self:
        if obj is None:
            return self

        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            windows = _ROIFields(obj)
            setattr(obj, self.private_name, windows)
            return windows


class BaseROIField[ROI:BaseROI]:
    """
    Base class for input handling of ROIs.

    Parameters
    ----------
    name: str, optional
        The name of the ROI(default is None).
    show_button: bool, optional
        Whether to show the button to select the ROI as active(default is True).
    button_style: str, optional
        The style of the `show_button` (default is None).

    Attributes
    ----------
    name: str | None
    roi: BaseROI | None
    post_register_command: Callable[[BaseROIField, bool|None], Any]
        Command called after ROI is registered.
        This should accept an ROI and a boolean indicating if it was a manual draw.
    label_var: tk.StringVar
    select_button: ttk.Button
    draw_button: ttk.Button

    Methods
    -------
    register_roi(roi: ROI)
        Registers an ROI.
    set_parent(parent: tk.Misc)
        Sets the parent of the ROI.
    set_manager(manager: Manager)
        Sets the manager of the ROI.
    set_as_active()
        Sets the ROI as the active ROI.
    """

    def __init__(self,
                 name: str | None = None,
                 *,
                 default_type: ManualROIType = "ROI ellipse",
                 allow_manual_draw: bool = True,
                 button_style: str | None = None):
        self._name: str | None = name
        self._private_name: str = ""
        self.roi: ROI | None = None
        self.default_type: ManualROIType = default_type
        self.viewer: BaseViewer | None = None
        self.allow_manual_draw: bool = allow_manual_draw
        self._parent: tk.Misc | None = None
        self._label_var: tk.StringVar | None = None
        self._select_button: ttk.Button | None = None
        self._draw_button: ttk.Button | None = None
        self._button_style: str | None = button_style
        self._manager: Manager | None = None
        self._postdraw_command: Callable[[BaseROI | None], Any] | None = None
        self.post_register_command: Callable[[BaseROIField, bool], Any] | None = None

    def __set_name__(self, owner: type[BaseModule], name: str):
        self._private_name = name
        if self.name is None:
            self.name = name.replace("_", " ").title()
        owner.rois.rois[self._private_name] = self

    def __get__(self, obj: BaseModule | None, owner=None) -> Self:
        if obj is None:
            return self

        try:
            return obj.rois.rois_dict[self._private_name]  # pyright: ignore[reportReturnType]
        except KeyError:
            roi_field = type(self)(name=self.name,
                                   default_type=self.default_type,
                                   allow_manual_draw=self.allow_manual_draw,
                                   button_style=self._button_style)
            obj.rois.rois_dict[self._private_name] = roi_field
            return roi_field

    @property
    def name(self) -> str | None:
        """
        The name of the ROI.
        """
        return self._name

    @name.setter
    def name(self, val: str):
        self._name = val
        if self._label_var is not None:
            self._label_var.set(val)

    def register_roi(self, roi: ROI | None, update_viewers: bool = False):
        """
        Registers an ROI.
        """
        if roi is not None:
            self.select_button.configure(state="normal")
            if roi.name != self.name:
                roi = roi.move_to_image(roi.image,
                                        roi.slice_num,
                                        self.name,
                                        True)  # type: ignore
        else:
            self.select_button.configure(state="disabled")
        self.roi = roi
        if self.post_register_command is not None:
            self.post_register_command(self, update_viewers)

    @property
    def label_var(self) -> tk.StringVar:
        """
        The label variable of the ROI.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
        if self.name is None:
            raise ValueError("Name has not been set")
        if self._label_var is None:
            self._label_var = tk.StringVar(self._parent, value=self.name)
        return self._label_var

    @property
    def select_button(self) -> ttk.Button:
        """
        The button to select the ROI.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
        if self._select_button is None:
            var = self.label_var
            if self._button_style is None:
                self._select_button = ttk.Button(self._parent,
                                                 textvariable=var,
                                                 command=self.set_as_active,
                                                 state="disabled")
            else:
                self._select_button = ttk.Button(self._parent,
                                                 style=self._button_style,
                                                 textvariable=var,
                                                 command=self.set_as_active,
                                                 state="disabled")
        return self._select_button

    @property
    def draw_button(self) -> ttk.Button:
        """
        The button to mannually redraw the ROI.
        """
        if self._parent is None:
            raise ValueError("Parent has not been set")
        if self._draw_button is None:
            if self._button_style is None:
                self._draw_button = ttk.Button(self._parent,
                                               text="Draw",
                                               command=self.manual_draw)
            else:
                self._draw_button = ttk.Button(self._parent,
                                               style=self._button_style,
                                               text="Draw",
                                               command=self.manual_draw)
        return self._draw_button

    def set_parent(self, parent: tk.Misc):
        """
        Sets the parent of the ROI.
        """
        if self._parent is None:
            self._parent = parent
        else:
            raise ValueError("Parent already set")

    def set_manager(self, manager: Manager):
        """
        Sets the manager of the ROI.
        """
        if self._manager is None:
            self._manager = manager
        else:
            raise ValueError("Manager already set")

    def set_as_active(self):
        """
        Sets the ROI as the active ROI.
        """
        if self._manager is None:
            raise ValueError("Manager has not been set")
        if self.roi is not None:
            self._manager.focus = self.roi

    def manual_draw(self, postdraw_command: Callable[[BaseROI | None], Any] | None = None):
        """
        Manually draw the ROI.

        Parameters
        ----------
        postdraw_command: Callable[[], Any] | None, optional
            A command to call once the ROI has been drawn(default is None).

        Raises
        ------
        AttributeError
            If self.viewer is None
        """
        if self.name is not None:
            if self.viewer is not None and isinstance(self.viewer.image, ArrayImage):
                if self.draw_button["text"] == "Draw":
                    try:
                        self.viewer.image.remove_roi(self.viewer.image[self.name])
                        self.viewer.update()
                    except KeyError:
                        pass
                    self._postdraw_command = postdraw_command
                    self.draw_button.configure(text="Stop Draw")
                    self.viewer.manual_roi_draw(self.default_type,
                                                self.name,
                                                postdraw_command=self._finish_draw)
                else:
                    self._finish_draw()
            else:
                if self.viewer is None:
                    raise AttributeError("`viewer` attribute must not be None for manual redraw.")
                else:
                    raise ValueError("viewer must have suitable image loaded")
        else:
            raise AttributeError("`verbose_name` not set.")

    def _finish_draw(self, roi: BaseROI | None = None):
        """
        Ran after manual draw is completed.
        """
        self.draw_button.configure(text="Draw")
        self.register_roi(roi, True)  # type: ignore
        if self._postdraw_command is not None:
            self._postdraw_command(roi)
            self._postdraw_command = None


class GeneralROIField(BaseROIField[BaseROI]):
    """
    Represents a general ROI input.
    Has the same attributes and methods as BaseROIField unless stated below.
    """


class RectangleROIField(BaseROIField[RectangleROI]):
    """
    Represents a RectangleROI input.
    Has the same attributes and methods as BaseROIField unless stated below.
    """

    def __init__(self,
                 name: str | None = None,
                 *,
                 allow_manual_draw: bool = True,
                 button_style: str | None = None):
        super().__init__(name,
                         default_type="ROI rectangle",
                         allow_manual_draw=allow_manual_draw,
                         button_style=button_style)


class EllipseROIField(BaseROIField[EllipseROI]):
    """
    Represents an EllipseROI input.
    Has the same attributes and methods as BaseROIField unless stated below.
    """

    def __init__(self,
                 name: str | None = None,
                 *,
                 allow_manual_draw: bool = True,
                 button_style: str | None = None):
        super().__init__(name,
                         default_type="ROI ellipse",
                         allow_manual_draw=allow_manual_draw,
                         button_style=button_style)


class LineROIField(BaseROIField[LineROI]):
    """
    Represents a LineROI input.
    Has the same attributes and methods as BaseROIField unless stated below.
    """

    def __init__(self,
                 name: str | None = None,
                 *,
                 allow_manual_draw: bool = True,
                 button_style: str | None = None):
        super().__init__(name,
                         default_type="ROI line",
                         allow_manual_draw=allow_manual_draw,
                         button_style=button_style)


class AngleROIField(BaseROIField[Angle]):
    """
    Represents an Angle ROI input.
    Has the same attributes and methods as BaseROIField unless stated below.
    """

    def __init__(self,
                 name: str | None = None,
                 *,
                 allow_manual_draw: bool = True,
                 button_style: str | None = None):
        super().__init__(name,
                         default_type="Angle",
                         allow_manual_draw=allow_manual_draw,
                         button_style=button_style)


class PointROIField(BaseROIField[PointROI]):
    """
    Represents a PointROI input.
    Has the same attributes and methods as BaseROIField unless stated below.
    """

    def __init__(self,
                 name: str | None = None,
                 *,
                 allow_manual_draw: bool = True,
                 button_style: str | None = None):
        super().__init__(name,
                         default_type="ROI point",
                         allow_manual_draw=allow_manual_draw,
                         button_style=button_style)
