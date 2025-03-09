"""
Classes:
 * ArrayViewer
 * BaseTempROI
 * BaseViewer
 * DicomViewer
 * MonochromeViewer
 * TempAngle
 * TempCircle
 * TempEllipse
 * TempLine
 * TempPoint
 * TempRectangle
 * TempSquare
 * Viewer
"""

import math
from abc import ABC, abstractmethod
import tkinter as tk
from collections.abc import Callable
from typing import Any, Self, TypeGuard, Literal
import numpy as np
from PIL import Image, ImageTk
from pumpia.module_handling.manager import Manager, MouseOptionsType
from pumpia.image_handling.image_structures import BaseImageSet, ImageCollection, ArrayImage
from pumpia.image_handling.roi_structures import (BaseROI,
                                                  Angle,
                                                  PointROI,
                                                  CircleROI,
                                                  EllipseROI,
                                                  SquareROI,
                                                  RectangleROI,
                                                  LineROI,
                                                  ROI_COLOUR,
                                                  ACTIVE_ROI_COLOUR)
from pumpia.file_handling.dicom_structures import Series, Instance
from pumpia.utilities.tkinter_utils import remove_state_persistents
from pumpia.utilities.array_utils import Position

RESIZE_DIST = 20
TEMP_ROI_COLOUR = "yellow"

ManualROIType = Literal["Angle",
                        "ROI point",
                        "ROI circle",
                        "ROI ellipse",
                        "ROI square",
                        "ROI rectangle",
                        "ROI line"]


def _showable_array_image(image: BaseImageSet) -> TypeGuard[ArrayImage]:
    """
    Checks if the image is a showable array image for a Viewer.
    """
    return (isinstance(image, ArrayImage) and (image.array.ndim == 3
                                               or (image.array.ndim == 4
                                                   and image.is_multisample)))


def _monochrome_image(image: BaseImageSet) -> TypeGuard[ArrayImage]:
    """
    Checks if the image is a monochrome image.
    """
    return isinstance(image, ArrayImage) and image.array.ndim == 3 and not image.is_multisample


class BaseTempROI(ABC):
    """
    Base class for temporary ROIs.

    Parameters
    ----------
    num_points : int, optional
        The number of points for the ROI e.g. a square ROI is 2 (default is 1).

    Attributes
    ----------
    points : list[Position]
        The points of the ROI.
    completed : bool
        Whether the ROI is completed.

    Methods
    -------
    add_point(x: float, y: float)
        Adds a point to the ROI.
    temp_drawing_points(x: int, y: int, aspect: float = 1) -> list[Position]
        Returns the temporary drawing points for the ROI.
    """

    def __init__(self, num_points: int = 1):
        self._points: list[Position] = []
        self.num_points: int = num_points

    def add_point(self, x: float, y: float):
        """
        Adds a point to the ROI.

        Parameters
        ----------
        x : float
            The x-coordinate of the point.
        y : float
            The y-coordinate of the point.
        """
        self._points.append(Position(x, y))

    @abstractmethod
    def temp_drawing_points(self, x: int, y: int, aspect: float = 1) -> list[Position]:
        """
        Returns the temporary drawing points for the ROI,
        based on current points for the ROI, mouse positions x and y,
        and the aspect of the image.
        """

    @property
    def completed(self) -> bool:
        """
        Checks if the ROI is completed.
        """
        return len(self.points) >= self.num_points

    @property
    def points(self) -> list[Position]:
        """
        Returns the points of the ROI.
        """
        return self._points


class TempAngle(BaseTempROI):
    """
    Temporary ROI for an angle.
    """

    def __init__(self):
        super().__init__(3)

    def temp_drawing_points(self, x: int, y: int, _: float = 1) -> list[Position]:
        temp_points = self.points.copy()
        temp_points.append(Position(x, y))
        return temp_points


class TempPoint(BaseTempROI):
    """
    Temporary ROI for a point.
    """

    def temp_drawing_points(self, x: int, y: int, aspect: float = 1) -> list[Position]:
        return self.points


class TempCircle(BaseTempROI):
    """
    Temporary ROI for a circle.
    """

    def __init__(self):
        super().__init__(2)

    def temp_drawing_points(self, x: int, y: int, aspect: float = 1) -> list[Position]:
        if len(self.points) == 1:
            radius = round(math.sqrt((self.points[0].x - x)**2
                                     + (self.points[0].y - y)**2))
            return [Position(self.points[0].x - radius, self.points[0].y - radius * aspect),
                    Position(self.points[0].x + radius, self.points[0].y + radius * aspect)]

        else:
            return []

    @property
    def radius(self) -> float:
        """
        Returns the radius of the circle ROI.
        """
        if len(self.points) == 2:
            return math.sqrt((self.points[0].x - self.points[1].x)**2
                             + (self.points[0].y - self.points[1].y)**2)
        else:
            return 0


class TempEllipse(BaseTempROI):
    """
    Temporary ROI for an ellipse.
    """

    def __init__(self):
        super().__init__(2)

    def temp_drawing_points(self, x: int, y: int, _: float = 1) -> list[Position]:
        if len(self.points) == 1:
            temp_points = [Position(self.points[0].x, self.points[0].y),
                           Position(x, y)]
            return temp_points
        else:
            return []


class TempSquare(BaseTempROI):
    """
    Temporary ROI for a square.
    """

    def __init__(self):
        super().__init__(2)

    def temp_drawing_points(self, x: int, y: int, aspect: float = 1) -> list[Position]:
        if len(self.points) == 1:
            diff = max(abs(self.points[0].x - x), abs(self.points[0].y - y))
            x_diff = round(math.copysign(diff, (x - self.points[0].x)))
            y_diff = round(math.copysign(diff, (y - self.points[0].y))) * aspect
            temp_points = [Position(self.points[0].x, self.points[0].y),
                           Position(self.points[0].x + x_diff, self.points[0].y + y_diff)]
            return temp_points
        else:
            return []

    @property
    def side_length(self):
        """
        Returns the side length of the square ROI.
        """
        if len(self._points) == 2:
            return max(abs(self._points[0].x - self._points[1].x),
                       abs(self._points[0].y - self._points[1].y))
        else:
            return 0

    @property
    def points(self) -> list[Position]:
        if len(self._points) == 2:
            x_diff = round(math.copysign(self.side_length,
                           (self._points[1].x - self._points[0].x)))
            y_diff = round(math.copysign(self.side_length,
                           (self._points[1].y - self._points[0].y)))
            temp_points = [Position(self._points[0].x, self._points[0].y),
                           Position(self._points[0].x + x_diff, self._points[0].y + y_diff)]
            return temp_points
        else:
            return self._points


class TempRectangle(BaseTempROI):
    """
    Temporary ROI for a rectangle.
    """

    def __init__(self):
        super().__init__(2)

    def temp_drawing_points(self, x: int, y: int, _: float = 1) -> list[Position]:
        if len(self.points) == 1:
            temp_points = [Position(self.points[0].x, self.points[0].y),
                           Position(x, y)]
            return temp_points
        else:
            return []


class TempLine(BaseTempROI):
    """
    Temporary ROI for a line.
    """

    def __init__(self):
        super().__init__(2)

    def temp_drawing_points(self, x: int, y: int, _: float = 1) -> list[Position]:
        temp_points = self.points.copy()
        temp_points.append(Position(x, y))
        return temp_points


class BaseViewer[ImageT: BaseImageSet](ABC, tk.Canvas):
    """
    Base class for viewers. Do not use directly.

    Method `can_show_image` must be overwritten by the user when subclassing `BaseViewer`.
    `image_type` class attribute should also be set to the expected image type,
    default is `BaseImageSet`.

    If allowed the user can drag and drop a valid image from a
    `Manager` treeview into the viewer to load it.

    The following shortcuts are provided for user interaction:
    - Mouse wheel: Scroll through image slices.
    - Control + Mouse wheel: Zoom in/out.
    - Mouse wheel button + drag: Adjust window/level.
    - Control + r: Reset image viewing parameters.

    Parameters
    ----------
    tk_parent : tk.Misc
        The parent widget.
    manager : Manager
        The manager object.
    allow_drag_drop : bool, optional
        Whether to allow drag and drop of images into the viewer(default is True).
    allow_drawing_rois : bool, optional
        Whether to allow drawing ROIs on the viewer (default is True).
    validation_command : Callable[[ImageT], bool], optional
        The validation command ran when an image is loaded,
        if validation fails then image is not shown.
        Must accept an image of the type viewable by the viewer (default is None).
    preload_command : Callable[[Self, ImageT], ImageT], optional
        The preload command to process a loaded image before it is shown.
        Must accept and return an image of the type viewable by the viewer(default is None).

    Attributes
    ----------
    manager : Manager
        The manager object.
    allow_drag_drop : bool
        Whether to allow drag and drop of images into the viewer.
    allow_drawing_rois : bool
        Whether to allow drawing ROIs on the viewer.
    validation_command : Callable[[ImageT], bool] or None
        The validation command ran when an image is loaded.
    preload_command : Callable[[Self, ImageT], ImageT] or None
        The preload command to process a loaded image before it is shown.
    mouse_x : float
        The x-coordinate of the last mouse event.
    mouse_y : float
        The y-coordinate of the last mouse event.
    last_event_time : int
        The time of the last event.
    center : Position
        The center position of the viewer.
    current_slice : int
        The current slice number of the image.
    manual_override : bool
        Whether manual ROI drawing is active.
    image : T or None
        The current image showing on the Viewer.
    pil_image : Image.Image
        The PIL image object.
    pil_tkimage : ImageTk.PhotoImage
        The PIL image object as a Tkinter PhotoImage.
    zoom_factor : float
    current_image : T or None

    Methods
    -------
    add_load_trace(func: Callable[[], Any])
        Adds a load trace function. This function is called when an image is loaded.
    remove_load_trace(func: Callable[[], Any])
        Removes a load trace function.
    can_show_image(cls, image: T) -> bool
        Checks if the viewer can show the image.
    unload_images()
        Unloads the images from the viewer.
    load_image(image: T)
        Loads an image into the viewer.
    viewer_to_image_pos(position: Position) -> Position
        Converts viewer coordinates to image coordinates.
    image_to_viewer_pos(position: Position) -> Position
        Converts image coordinates to viewer coordinates.
    update()
        Updates the viewer.
    reset_image()
        Resets the image to its original state.
    manual_roi_draw(roi: ManualROIType, name: str | None = None, replace: bool = True, cache: bool = True, roi_colour: str = ROI_COLOUR, active_colour: str = ACTIVE_ROI_COLOUR)
        Starts manual ROI drawing.
    stop_manual_roi_draw()
        Stops manual ROI drawing.
    change_slice(amount: int = 1)
        Changes the current slice of the image by amount of slices.
    set_slice(slice_num: int)
        Sets the current slice of the image.
    change_zoom(amount: float = 1)
        Changes the zoom level of the image.
    window_level(window_delta: float, level_delta: float)
        Adjusts the window and level of the image.
    set_window_level(window: float, level: float)
        Sets the window and level of the image.
    move_image(delta_x: float, delta_y: float)
        Moves the image on the viewer based on the given deltas.
    set_image_loc(x: float, y: float)
        Sets the image location on the viewer.
    """

    image_type: type[ImageT] | tuple[type[ImageT], ...] = BaseImageSet  # type: ignore

    def __init__(self,
                 tk_parent: tk.Misc,
                 manager: Manager,
                 *,
                 allow_drag_drop: bool = True,
                 allow_drawing_rois: bool = True,
                 allow_changing_rois: bool = True,
                 # pylint: disable-next=undefined-variable
                 validation_command: Callable[[ImageT], bool] | None = None,
                 # pylint: disable-next=undefined-variable
                 preload_command: Callable[[Self, ImageT], ImageT] | None = None) -> None:
        super().__init__(tk_parent, background="black", highlightthickness=0, bd=0)
        self.manager: Manager = manager
        self.manager.viewers.append(self)
        self.allow_drag_drop: bool = allow_drag_drop
        self.allow_drawing_rois: bool = allow_drawing_rois
        self.allow_changing_rois: bool = allow_changing_rois
        # pylint: disable-next=undefined-variable
        self.validation_command: Callable[[ImageT], bool] | None = validation_command
        # pylint: disable-next=undefined-variable
        self.preload_command: Callable[[Self, ImageT], ImageT] | None = preload_command
        self.mouse_x: float = 0
        self.mouse_y: float = 0
        self.last_event_time: int = 0
        self.center: Position = Position(0, 0)
        self._updating: bool = False
        self._x: float = 0
        self._y: float = 0
        self._zoom: float = 0
        self._rotation: float = 0
        self._user_window: float | None = None
        self._user_level: float | None = None
        self.current_slice: int = 0

        self._temp_roi: BaseTempROI | None = None
        self._temp_roi_id: int | None = None
        self._temp_roi_move_bind: str | None = None

        self._temp_mouse_release_bind: str | None = None
        self._temp_move_roi: BaseROI | None = None

        self._temp_action: ManualROIType | None = None
        self._roi_name: str | None = None
        self._roi_replace: bool = True
        self._roi_cache: bool = True
        self._manual_roi_colour: str = ROI_COLOUR
        self._manual_active_colour: str = ACTIVE_ROI_COLOUR
        self.manual_override: bool = False
        self._postdraw_command: Callable[[BaseROI | None], Any] | None = None

        self._load_traces: set[Callable[[], Any]] = set()

        self.bind("<Enter>", self._entered)
        self.bind('<Leave>', self._leaving)
        self.bind('<Configure>', self._configure_window)

        # pylint: disable-next=undefined-variable
        self.image: ImageT | None = None
        self._axes_array: np.ndarray = np.empty((0, 0))
        self.pil_image: Image.Image = Image.fromarray(self._axes_array)
        self.pil_tkimage: ImageTk.PhotoImage = ImageTk.PhotoImage(
            self.pil_image)
        self._image_id: int = self.create_image(self.center.tuple,
                                                image=self.pil_tkimage)

    @property
    def zoom_factor(self) -> float:
        """
        The zoom factor.
        """
        return 2**self._zoom

    @property  # pylint: disable-next=undefined-variable
    def current_image(self) -> ImageT | None:
        """
        The current image showing on the Viewer.
        """
        if isinstance(self.image, ArrayImage):
            self.image.current_slice = self.current_slice
            if isinstance(self.image, ImageCollection):
                return self.image.current_image
        return self.image

    def _entered(self, event: tk.Event):
        """
        Handles the event when the mouse enters the viewer.
        """
        self.bind_all("<MouseWheel>", self._scroll_image)
        self.bind_all("<Control-MouseWheel>", self._scroll_zoom)
        self.bind_all("<Button-2>", self._set_mouse_loc)
        self.bind_all("<B2-Motion>", self._mouse_wheel_window_level)
        self.bind_all("<Button-1>", self._mouse_click)
        self.bind_all("<B1-Motion>", self._mouse_click_motion)
        self.bind_all("<Control-r>", self._reset_shortcut)
        if self._temp_roi is not None:
            self._temp_roi_move_bind = self.bind("<Motion>",
                                                 self._mouse_roi_move)

        if self.allow_drag_drop and self.manager.select_time == event.time:
            image = self.manager.focus
            if isinstance(image, self.image_type):
                self.load_image(image)  # type: ignore

    def _leaving(self, _):
        """
        Handles the event when the mouse leaves the viewer.
        """
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Control-MouseWheel>")
        self.unbind_all("<Button-2>")
        self.unbind_all("<B2-Motion>")
        self.unbind_all("<Button-1>")
        self.unbind_all("<ButtonRelease-1>")
        self.unbind_all("<B1-Motion>")
        self.unbind_all("<Control-r>")
        self.unbind_all("<Motion>")

    def add_load_trace(self, func: Callable[[], Any]):
        """
        Adds a load trace function. This function is called when an image is loaded.
        """
        self._load_traces.add(func)

    def remove_load_trace(self, func: Callable[[], Any]):
        """
        Removes a load trace function.
        """
        self._load_traces.remove(func)

    @classmethod
    @abstractmethod  # pylint: disable-next=undefined-variable
    def can_show_image(cls, image: ImageT) -> bool:
        """
        Checks if the viewer can show the image.
        Users must overwrite this when subclassing BaseViewer.
        """

    def unload_images(self):
        """
        Unloads the images from the viewer.
        """
        self.image = None
        self.update()

    # pylint: disable-next=undefined-variable
    def load_image(self, image: ImageT):
        """
        Loads an image into the viewer.
        """
        if self.manual_override:
            self.stop_manual_roi_draw()

        if self.preload_command is not None:
            image = self.preload_command(self, image)

        if self.can_show_image(image):
            if self.validation_command is None or self.validation_command(image):
                self.image = image
                if isinstance(self.image, ArrayImage):
                    self._x = self.image.x
                    self._y = self.image.y
                    self._zoom = self.image.zoom
                    self._rotation = self.image.rotation
                    self._user_window = self.image.user_window
                    self._user_level = self.image.user_level
                    self.current_slice = self.image.current_slice

                self._run_load_traces()
                self.update()
            else:
                raise TypeError("Image Validation Failed")
        else:
            raise TypeError("Can't show image")

    def _run_load_traces(self):
        """
        Runs the load trace functions.
        """
        for func in self._load_traces:
            func()

    def viewer_to_image_pos(self, position: Position) -> Position:
        """
        Converts viewer coordinates to image coordinates.
        """
        if isinstance(self.image, ArrayImage):
            x_new = ((position.x - self.center.x - self.image.x)
                     / self.zoom_factor
                     + self.image.shape[2] / 2)
            y_new = ((position.y - self.center.y - self.image.y)
                     / (self.zoom_factor * self.image.aspect)
                     + self.image.shape[1] / 2)
            return Position(x_new, y_new)
        else:
            return position

    def image_to_viewer_pos(self, position: Position) -> Position:
        """
        Converts image coordinates to viewer coordinates.
        """
        if isinstance(self.image, ArrayImage):
            x_new = ((position.x - self.image.shape[2] / 2) * self.zoom_factor
                     + self.center.x + self.image.x)
            y_new = ((position.y - self.image.shape[1] / 2) * self.zoom_factor * self.image.aspect
                     + self.center.y + self.image.y)
            return Position(x_new, y_new)
        else:
            return position

    def _update_router(self):
        """
        Updates the viewer with the current image.
        """
        if self.image is None:
            self._axes_array: np.ndarray = np.empty((0, 0))
            self.pil_image: Image.Image = Image.fromarray(self._axes_array)
            self.pil_tkimage: ImageTk.PhotoImage = ImageTk.PhotoImage(
                self.pil_image)
            self.itemconfigure(
                self._image_id, image=self.pil_tkimage)

        elif isinstance(self.image, ArrayImage):
            #####################################################
            # The following code calculates the part of the image
            # that is going to be visible in the viewer
            # and then crops the image to that part
            # DO NOT TOUCH UNLESS YOU KNOW WHAT YOU ARE DOING

            self.center.x = self.winfo_width() / 2
            self.center.y = self.winfo_height() / 2

            orig_width = math.floor(
                self.image.shape[2] * self.zoom_factor)
            orig_height = math.floor(
                self.image.shape[1] * self.zoom_factor * self.image.aspect)

            if orig_width < 1 or orig_height < 1:
                new_width = new_height = 1
                self._axes_array = self.image.array[self.current_slice]
            else:
                lower_w = math.floor(
                    (orig_width / 2 - self.center.x - self._x) / self.zoom_factor)
                upper_w = math.ceil(
                    (orig_width / 2 + self.center.x - self._x) / self.zoom_factor)
                if lower_w < 0:
                    lower_w = 0
                if upper_w > self.image.shape[2]:
                    upper_w = self.image.shape[2]
                if lower_w >= upper_w:
                    if lower_w >= self.image.shape[2]:
                        lower_w = self.image.shape[2] - 1
                    upper_w = lower_w + 1

                lower_h = math.floor(
                    (orig_height / 2 - self.center.y - self._y) / self.zoom_factor)
                upper_h = math.ceil(
                    (orig_height / 2 + self.center.y - self._y) / self.zoom_factor)
                if lower_h < 0:
                    lower_h = 0
                if upper_h > self.image.shape[1]:
                    upper_h = self.image.shape[1]
                if lower_h >= upper_h:
                    if lower_h >= self.image.shape[1]:
                        lower_h = self.image.shape[1] - 1
                    upper_h = lower_h + 1

                self._axes_array = self.image.array[self.current_slice,
                                                    lower_h:upper_h,
                                                    lower_w:upper_w]

                new_width = math.floor(
                    self._axes_array.shape[1] * self.zoom_factor)
                new_height = math.floor(
                    self._axes_array.shape[0] * self.zoom_factor * self.image.aspect)

                if new_width < 1 or new_height < 1:
                    new_width = new_height = 1

            try:
                ix = lower_w * self.zoom_factor - (orig_width - new_width) / 2
                iy = lower_h * self.zoom_factor - (orig_height - new_height) / 2
            except UnboundLocalError:
                ix = -(orig_width - new_width) / 2
                iy = -(orig_height - new_height) / 2

            if self._axes_array.ndim == 2:
                if (self._user_level is not None
                        and self._user_window is not None):
                    mult = 255 / self._user_window
                    intercept = (self._user_level
                                 - (self._user_window / 2))
                    array_to_show = (self._axes_array - intercept) * mult
                    array_to_show[array_to_show > 255] = 255
                    array_to_show[array_to_show < 0] = 0
                    array_to_show = array_to_show.astype(np.uint8)

                    self.pil_image = Image.fromarray(array_to_show, mode='L')

            elif self._axes_array.ndim == 3 and self.image.is_rgb:
                self.pil_image = Image.fromarray(
                    self._axes_array, mode='RGB')

            self.pil_image = self.pil_image.resize((new_width, new_height),
                                                   resample=Image.Resampling.NEAREST)

            self.pil_tkimage = ImageTk.PhotoImage(self.pil_image)
            self.itemconfigure(
                self._image_id, image=self.pil_tkimage)

            imw = self.pil_image.width
            imh = self.pil_image.height

            self.moveto(
                self._image_id,
                round(self.center.x - imw / 2 + ix + self._x, 0),
                round(self.center.y - imh / 2 + iy + self._y, 0))
            #####################################################

            for roi in self.image.get_rois(self.current_slice):
                if not roi.hidden:
                    if roi.active:
                        colour = roi.active_colour
                    else:
                        colour = roi.colour

                    if isinstance(roi, (CircleROI, EllipseROI)):
                        min_point = self.image_to_viewer_pos(
                            Position(roi.xmin, roi.ymin))
                        max_point = self.image_to_viewer_pos(
                            Position(roi.xmax + 1, roi.ymax + 1))
                        self.create_oval(min_point.x, min_point.y,
                                         max_point.x, max_point.y, outline=colour)

                    elif isinstance(roi, (SquareROI, RectangleROI)):
                        min_point = self.image_to_viewer_pos(
                            Position(roi.xmin, roi.ymin))
                        max_point = self.image_to_viewer_pos(
                            Position(roi.xmax + 1, roi.ymax + 1))
                        self.create_rectangle(min_point.x, min_point.y,
                                              max_point.x, max_point.y, outline=colour)

                    elif isinstance(roi, Angle):
                        pos1 = self.image_to_viewer_pos(
                            Position(roi.x1, roi.y1))
                        posc = self.image_to_viewer_pos(
                            Position(roi.x, roi.y))
                        pos2 = self.image_to_viewer_pos(
                            Position(roi.x2, roi.y2))
                        self.create_line([(pos1.x, pos1.y), (posc.x, posc.y), (pos2.x, pos2.y)],
                                         fill=colour)

                    elif isinstance(roi, PointROI):
                        pos = self.image_to_viewer_pos(Position(roi.x, roi.y))
                        pos1 = self.image_to_viewer_pos(
                            Position(roi.x + 1, roi.y + 1))
                        self.create_rectangle(pos.x, pos.y, pos1.x, pos1.y,
                                              fill=colour, outline=colour)

                    elif isinstance(roi, LineROI):
                        pos1 = self.image_to_viewer_pos(
                            Position(roi.x1, roi.y1))
                        pos2 = self.image_to_viewer_pos(
                            Position(roi.x2, roi.y2))
                        self.create_line([(pos1.x, pos1.y), (pos2.x, pos2.y)],
                                         fill=colour)

    def update(self):
        """
        Updates the viewer.
        """
        self._updating = True
        for item in self.find_all():
            if item != self._image_id:
                self.delete(item)
        self._update_router()
        super().update()
        self._updating = False

    def _reset_shortcut(self, event: tk.Event):
        """
        Resets the image when the shortcut `ctrl + r` is triggered.
        """
        # state 4 is Control key modifier
        if remove_state_persistents(event.state) == 4:
            self.reset_image()

    def reset_image(self):
        """
        Resets the image to its original state.
        """
        if (isinstance(self.image, ArrayImage)
                and not self._updating):
            self._updating = True
            self.image.reset()
            self._x = self.image.x
            self._y = self.image.y
            self._zoom = self.image.zoom
            self._rotation = self.image.rotation
            self._user_window = self.image.user_window
            self._user_level = self.image.user_level
            self.update()
            self._updating = False

    def manual_roi_draw(self,
                        roi: ManualROIType,
                        name: str | None = None,
                        replace: bool = True,
                        cache: bool = True,
                        roi_colour: str = ROI_COLOUR,
                        active_colour: str = ACTIVE_ROI_COLOUR,
                        postdraw_command: Callable[[BaseROI | None], Any] | None = None):
        """
        Starts manual ROI drawing.
        Used when drawing an ROI is started programatically, not through the UI.

        Parameters
        ----------
        roi : ManualROIType
            The type of ROI to draw.
        name : str or None, optional
            The name of the ROI (default is None).
        replace : bool, optional
            Whether to replace an existing ROI with the same name (default is True).
        cache : bool, optional
            Whether to cache the ROI values (default is True).
        roi_colour : str, optional
            The colour of the ROI (default is ROI_COLOUR).
        active_colour : str, optional
            The active colour of the ROI (default is ACTIVE_ROI_COLOUR).
        postdraw_command: Callable[[], Any] | None
            A command to call once the ROI has been drawn (default is None).
        """
        self._temp_action = roi
        self._roi_name = name
        self._roi_replace = replace
        self._roi_cache = cache
        self._manual_roi_colour = roi_colour
        self._manual_active_colour = active_colour
        self.manual_override = True
        self._postdraw_command = postdraw_command

    def stop_manual_roi_draw(self, roi: BaseROI | None = None):
        """
        Stops manual ROI drawing.
        In case manual ROI drawing was started programatically but didn't end.
        """
        if self._postdraw_command is not None:
            self._postdraw_command(roi)
        self._temp_action = None
        self._roi_name = None
        self._roi_replace = True
        self._roi_cache = True
        self._manual_roi_colour = ROI_COLOUR
        self._manual_active_colour = ACTIVE_ROI_COLOUR
        self.manual_override = False
        self._postdraw_command = None

    def _scroll_image(self, event: tk.Event):
        """
        Scrolls through the image slices.
        For use with mouse wheel events.
        """
        # state 0 is no modifiers e.g.Control/Alt/Shift
        if (isinstance(self.image, ArrayImage)
                and remove_state_persistents(event.state) == 0):
            if event.num == 4 or event.delta > 0:
                self.change_slice(-1)
            elif event.num == 5 or event.delta < 0:
                self.change_slice(1)

    def change_slice(self, amount: int = 1):
        """
        Changes the current slice of the image by amount of slices.
        """
        if isinstance(self.image, ArrayImage):
            self.image.current_slice = self.current_slice
            self.image.change_slice(amount)
            self.current_slice = self.image.current_slice
            self.update()

    def set_slice(self, slice_num: int):
        """
        Sets the current slice of the image.
        """
        if isinstance(self.image, ArrayImage):
            self.image.current_slice = slice_num
            self.current_slice = self.image.current_slice
            self.update()

    def _scroll_zoom(self, event: tk.Event):
        """
        For zooming when using control + mousewheel shortcut.
        """
        # state 4 is Control key modifier
        if (isinstance(self.image, ArrayImage)
                and remove_state_persistents(event.state) == 4
                and not self._updating):
            self._updating = True
            if event.num == 4 or event.delta == 120:
                self.change_zoom(0.1)
            elif event.num == 5 or event.delta == -120:
                self.change_zoom(-0.1)
            self._updating = False

    def change_zoom(self, amount: float = 1):
        """
        Changes the zoom level of the image.
        """
        if isinstance(self.image, ArrayImage):
            orig_zoom = self.zoom_factor
            self._zoom += amount
            self.image.zoom = self._zoom
            self._x = self._x * self.zoom_factor / orig_zoom
            self._y = self._y * self.zoom_factor / orig_zoom
            self.image.x = self._x
            self.image.y = self._y
            self.update()

    def _set_mouse_loc(self, event: tk.Event):
        """
        Sets the mouse location.
        """
        self.mouse_x = event.x
        self.mouse_y = event.y

    def _mouse_click(self, event: tk.Event):
        """
        Handles mouse click events.
        """
        self._set_mouse_loc(event)
        self._mouse_click_motion(event)

        if self._temp_roi is not None:
            self._temp_roi.add_point(event.x, event.y)
            if self._temp_roi.completed:
                self._end_roi_draw()

    def _event_window_level(self, event: tk.Event):
        """
        Handles window/level events when dragging mouse.
        """
        level_delta = event.x - self.mouse_x
        window_delta = self.mouse_y - event.y
        self._set_mouse_loc(event)
        self.window_level(window_delta, level_delta)

    def window_level(self, window_delta: float, level_delta: float):
        """
        Adjusts the window and level of the image.
        """
        if (isinstance(self.image, ArrayImage)
                and not self._updating):
            if (self._user_level is not None
                    and self._user_window is not None):
                self._updating = True
                self.image.user_level = self._user_level + level_delta
                self.image.user_window = self._user_window + window_delta
                self._user_level = self.image.user_level
                self._user_window = self.image.user_window
                self.update()
                self._updating = False

    def set_window_level(self, window: float, level: float):
        """
        Sets the window and level of the image.
        """
        if (isinstance(self.image, ArrayImage)
                and not self._updating):
            if (self._user_level is not None
                    and self._user_window is not None):
                self._updating = True
                self.image.user_level = level
                self.image.user_window = window
                self._user_level = self.image.user_level
                self._user_window = self.image.user_window
                self.update()
                self._updating = False

    def _mouse_wheel_window_level(self, event: tk.Event):
        """
        Handles mouse wheel button events for window/level adjustment.
        """
        # state 512 is button 2 (mouse wheel button)
        if remove_state_persistents(event.state) == 512:
            self._event_window_level(event)

    def _action_router(self, action: MouseOptionsType, event: tk.Event):
        """
        Routes the mouse action based on the current action.
        """
        if action == "Pointer":
            self.update()
        elif remove_state_persistents(event.state) == 256:
            if action == "Drag":
                self._mouse_drag(event)
            elif action == "Zoom":
                self._mouse_zoom(event)
            elif action == "Window/Level":
                self._event_window_level(event)
        elif self._temp_roi is None and self.allow_drawing_rois:
            if action == "Angle":
                self._temp_roi = TempAngle()
            elif action == "ROI point":
                self._temp_roi = TempPoint()
            elif action == "ROI circle":
                self._temp_roi = TempCircle()
            elif action == "ROI ellipse":
                self._temp_roi = TempEllipse()
            elif action == "ROI square":
                self._temp_roi = TempSquare()
            elif action == "ROI rectangle":
                self._temp_roi = TempRectangle()
            elif action == "ROI line":
                self._temp_roi = TempLine()

            if self._temp_roi is not None:
                self._temp_roi_move_bind = self.bind("<Motion>",
                                                     self._mouse_roi_move)

    def _mouse_click_motion(self, event: tk.Event):
        """
        Handles mouse click + motion events.
        """
        if self._temp_action is None:
            action = self.manager.current_action
        else:
            action = self._temp_action

        if (isinstance(self.manager.focus, BaseROI)
            and not self.manager.focus.hidden
                and self._temp_roi is None
                and self.allow_changing_rois):
            if self.manager.focus.image == self.current_image:
                im_pos = self.viewer_to_image_pos(
                    Position(self.mouse_x, self.mouse_y))

                if self.manager.roi_action == "Move":
                    if self.manager.focus.pixel_is_in(im_pos.x, im_pos.y):
                        if self._temp_move_roi is None:
                            self.bind("<ButtonRelease-1>", self._release_roi)
                            self._temp_move_roi = self.manager.focus
                        self._move_roi(event)
                    elif self._temp_move_roi is None:
                        self.manager.focus.active = False
                        self.manager.focus = None
                        self._action_router(action, event)

                elif self.manager.roi_action == "Resize":
                    dist = RESIZE_DIST / self.zoom_factor
                    if self.manager.focus.pixel_is_on(im_pos.x, im_pos.y, dist):
                        if self._temp_move_roi is None:
                            self.bind("<ButtonRelease-1>", self._release_roi)
                            self._temp_move_roi = self.manager.focus
                        self._resize_roi(event)
                    elif (not self.manager.focus.pixel_is_in(im_pos.x, im_pos.y)
                          and self._temp_move_roi is None):
                        self.manager.focus.active = False
                        self.manager.focus = None
                        self._action_router(action, event)

                elif self.manager.roi_action == "None":
                    self.manager.focus.active = False
                    self.manager.focus = None
                    self._action_router(action, event)
            else:
                self._action_router(action, event)
        else:
            self._action_router(action, event)

    def _release_roi(self, _: tk.Event):
        """
        Releases the ROI after moving or resizing.
        """
        if self._temp_move_roi is not None:
            self.manager.add_roi(self._temp_move_roi)
            self._temp_move_roi = None
        self.unbind_all("<ButtonRelease-1>")

    def _move_roi(self, event: tk.Event):
        """
        Moves the ROI based on mouse movement.
        """
        if self._temp_move_roi is not None and not self._updating:
            self._updating = True
            event_pos = self.viewer_to_image_pos(Position(event.x, event.y))
            mouse_pos = self.viewer_to_image_pos(
                Position(self.mouse_x, self.mouse_y))
            delta_x = math.floor(event_pos.x) - math.floor(mouse_pos.x)
            delta_y = math.floor(event_pos.y) - math.floor(mouse_pos.y)
            self._temp_move_roi.move(delta_x, delta_y)
            self._set_mouse_loc(event)
            self.manager.add_roi(self._temp_move_roi, True)
            self.manager.update_viewers()
            self._updating = False

    def _resize_roi(self, event: tk.Event):
        """
        Resizes the ROI based on mouse movement.
        """
        if self._temp_move_roi is not None and not self._updating:
            self._updating = True
            event_pos = self.viewer_to_image_pos(Position(event.x, event.y))
            mouse_pos = self.viewer_to_image_pos(
                Position(self.mouse_x, self.mouse_y))

            if isinstance(self._temp_move_roi, EllipseROI):
                if mouse_pos.x - self._temp_move_roi.x != 0:
                    delta_x = abs((event_pos.x - self._temp_move_roi.x)
                                  / (mouse_pos.x - self._temp_move_roi.x))
                else:
                    if self._temp_move_roi.a == 0:
                        self._temp_move_roi.a = round(abs(
                            (event_pos.x - self._temp_move_roi.x)))
                    delta_x = 1

                if mouse_pos.y - self._temp_move_roi.y != 0:
                    delta_y = abs((event_pos.y - self._temp_move_roi.y)
                                  / (mouse_pos.y - self._temp_move_roi.y))
                else:
                    if self._temp_move_roi.b == 0:
                        self._temp_move_roi.b = round(abs(
                            (event_pos.y - self._temp_move_roi.y)))
                    delta_y = 1

                new_w = round(2 * delta_x * self._temp_move_roi.a)
                new_h = round(2 * delta_y * self._temp_move_roi.b)

                if new_w == 0:
                    new_w = 1

                if new_h == 0:
                    new_h = 1

                self._temp_move_roi.resize_bbox(new_w, new_h)

            elif isinstance(self._temp_move_roi, CircleROI):
                new_d = 2 * round(math.sqrt((event_pos.x - self._temp_move_roi.x)**2
                                            + (event_pos.y - self._temp_move_roi.y)**2))
                self._temp_move_roi.resize_bbox(new_d, new_d)

            elif isinstance(self._temp_move_roi, RectangleROI):
                delta_top = abs(mouse_pos.y - self._temp_move_roi.ymin)
                delta_bot = abs(mouse_pos.y - self._temp_move_roi.ymax)
                delta_left = abs(mouse_pos.x - self._temp_move_roi.xmin)
                delta_right = abs(mouse_pos.x - self._temp_move_roi.xmax)

                new_h = self._temp_move_roi.ymax - self._temp_move_roi.ymin
                new_w = self._temp_move_roi.xmax - self._temp_move_roi.xmin

                dist = RESIZE_DIST / self.zoom_factor

                move_u = False
                move_l = False

                if delta_top < dist or delta_bot < dist:
                    if delta_top < delta_bot:
                        new_h = self._temp_move_roi.ymax - event_pos.y
                        move_u = True
                    else:
                        new_h = event_pos.y - self._temp_move_roi.ymin

                if delta_left < dist or delta_right < dist:
                    if delta_left < delta_right:
                        new_w = self._temp_move_roi.xmax - event_pos.x
                        move_l = True
                    else:
                        new_w = event_pos.x - self._temp_move_roi.xmin

                new_h = round(new_h)
                new_w = round(new_w)

                self._temp_move_roi.resize_bbox(new_w, new_h)

                delta_x = round(event_pos.x - self._temp_move_roi.xmin)
                delta_y = round(event_pos.y - self._temp_move_roi.ymin)

                if move_l and move_u:
                    self._temp_move_roi.move(delta_x, delta_y)
                elif move_l:
                    self._temp_move_roi.move(delta_x, 0)
                elif move_u:
                    self._temp_move_roi.move(0, delta_y)

            elif isinstance(self._temp_move_roi, SquareROI):
                delta_top = abs(mouse_pos.y - self._temp_move_roi.ymin)
                delta_bot = abs(mouse_pos.y - self._temp_move_roi.ymax)
                delta_left = abs(mouse_pos.x - self._temp_move_roi.xmin)
                delta_right = abs(mouse_pos.x - self._temp_move_roi.xmax)

                new_h = 0
                new_w = 0

                move_u = False
                move_l = False

                if delta_top < delta_bot:
                    new_h = self._temp_move_roi.ymax - event_pos.y
                    move_u = True
                else:
                    new_h = event_pos.y - self._temp_move_roi.ymin

                if delta_left < delta_right:
                    new_w = self._temp_move_roi.xmax - event_pos.x
                    move_l = True
                else:
                    new_w = event_pos.x - self._temp_move_roi.xmin

                if new_h == 0 and new_w == 0:
                    new_h = self._temp_move_roi.r
                    new_w = self._temp_move_roi.r

                new_h = round(new_h)
                new_w = round(new_w)

                self._temp_move_roi.resize_bbox(new_w, new_h)

                delta_x = round(event_pos.x - self._temp_move_roi.xmin)
                delta_y = round(event_pos.y - self._temp_move_roi.ymin)

                if move_l and move_u:
                    if new_w > new_h:
                        delta_y = delta_x
                    elif new_h > new_w:
                        delta_x = delta_y
                    self._temp_move_roi.move(delta_x, delta_y)
                elif move_l:
                    if new_h > new_w:
                        delta_x = 0
                    self._temp_move_roi.move(delta_x, 0)
                elif move_u:
                    if new_w > new_h:
                        delta_y = 0
                    self._temp_move_roi.move(0, delta_y)

            self._set_mouse_loc(event)
            self.manager.add_roi(self._temp_move_roi, True)
            self.manager.update_viewers()
            self._updating = False

    def _end_roi_draw(self):
        """
        Ends the ROI drawing process.
        """
        if self._temp_roi_move_bind is not None:
            self.unbind("<Motion>", self._temp_roi_move_bind)
            self._temp_roi_move_bind = None
        if self._temp_roi_id is not None:
            self.delete(self._temp_roi_id)
            self._temp_roi_id = None

        if isinstance(self.current_image, ArrayImage) and self._temp_roi is not None:

            points = [self.viewer_to_image_pos(p)
                      for p in self._temp_roi.points]
            new_roi: BaseROI | None = None
            try:
                if isinstance(self._temp_roi, TempAngle):
                    new_roi = Angle(self.current_image,
                                    math.floor(points[1].x),
                                    math.floor(points[1].y),
                                    math.floor(points[0].x),
                                    math.floor(points[0].y),
                                    math.floor(points[2].x),
                                    math.floor(points[2].y),
                                    slice_num=self.current_image.current_slice,
                                    name=self._roi_name,
                                    replace=self._roi_replace,
                                    cache_values=self._roi_cache,
                                    colour=self._manual_roi_colour,
                                    active_colour=self._manual_active_colour)

                elif isinstance(self._temp_roi, TempPoint):
                    new_roi = PointROI(self.current_image,
                                       math.floor(points[0].x),
                                       math.floor(points[0].y),
                                       slice_num=self.current_image.current_slice,
                                       name=self._roi_name,
                                       replace=self._roi_replace,
                                       cache_values=self._roi_cache,
                                       colour=self._manual_roi_colour,
                                       active_colour=self._manual_active_colour)

                elif isinstance(self._temp_roi, TempCircle):
                    new_roi = CircleROI(self.current_image,
                                        math.floor(points[0].x),
                                        math.floor(points[0].y),
                                        round(self._temp_roi.radius /
                                              self.zoom_factor),
                                        slice_num=self.current_image.current_slice,
                                        name=self._roi_name,
                                        replace=self._roi_replace,
                                        cache_values=self._roi_cache,
                                        colour=self._manual_roi_colour,
                                        active_colour=self._manual_active_colour)

                elif isinstance(self._temp_roi, TempEllipse):
                    centre_x = math.floor((points[0].x + points[1].x) / 2)
                    centre_y = math.floor((points[0].y + points[1].y) / 2)
                    a = abs(round((points[0].x - points[1].x) / 2))
                    b = abs(round((points[0].y - points[1].y) / 2))
                    new_roi = EllipseROI(self.current_image,
                                         centre_x,
                                         centre_y,
                                         a,
                                         b,
                                         slice_num=self.current_image.current_slice,
                                         name=self._roi_name,
                                         replace=self._roi_replace,
                                         cache_values=self._roi_cache,
                                         colour=self._manual_roi_colour,
                                         active_colour=self._manual_active_colour)

                elif isinstance(self._temp_roi, TempSquare):
                    xmin = min(points[0].x, points[1].x)
                    ymin = min(points[0].y, points[1].y)
                    new_roi = SquareROI(self.current_image,
                                        math.floor(xmin),
                                        math.floor(ymin),
                                        round(self._temp_roi.side_length /
                                              self.zoom_factor),
                                        slice_num=self.current_image.current_slice,
                                        name=self._roi_name,
                                        replace=self._roi_replace,
                                        cache_values=self._roi_cache,
                                        colour=self._manual_roi_colour,
                                        active_colour=self._manual_active_colour)

                elif isinstance(self._temp_roi, TempRectangle):
                    xmin = min(points[0].x, points[1].x)
                    ymin = min(points[0].y, points[1].y)
                    xmax = max(points[0].x, points[1].x)
                    ymax = max(points[0].y, points[1].y)
                    new_roi = RectangleROI(self.current_image,
                                           math.floor(xmin),
                                           math.floor(ymin),
                                           math.floor(xmax),
                                           math.floor(ymax),
                                           slice_num=self.current_image.current_slice,
                                           name=self._roi_name,
                                           replace=self._roi_replace,
                                           cache_values=self._roi_cache,
                                           colour=self._manual_roi_colour,
                                           active_colour=self._manual_active_colour)

                elif isinstance(self._temp_roi, TempLine):
                    new_roi = LineROI(self.current_image,
                                      math.floor(points[0].x),
                                      math.floor(points[0].y),
                                      math.floor(points[1].x),
                                      math.floor(points[1].y),
                                      slice_num=self.current_image.current_slice,
                                      name=self._roi_name,
                                      replace=self._roi_replace,
                                      cache_values=self._roi_cache,
                                      colour=self._manual_roi_colour,
                                      active_colour=self._manual_active_colour)
            except ValueError:
                pass

            if new_roi is not None:
                # self._temp_roi = None
                if self.manual_override:
                    self.stop_manual_roi_draw(new_roi)
                # This must be below lines above as add_roi updates viewer which ends manual draw
                self.manager.add_roi(new_roi)

        self._temp_roi = None
        self.stop_manual_roi_draw()

    def _mouse_roi_move(self, event: tk.Event):
        """
        Handles mouse movement for drawing ROIs.
        """
        if isinstance(self.image, ArrayImage):
            aspect = self.image.aspect
        else:
            aspect = 1
        if self._temp_roi is not None:
            points = [(p.x, p.y)
                      for p in self._temp_roi.temp_drawing_points(event.x, event.y, aspect)]
            if self._temp_roi_id is not None:
                self.delete(self._temp_roi_id)

            if len(points) > 0:
                if isinstance(self._temp_roi, (TempAngle, TempLine)):
                    self._temp_roi_id = self.create_line(
                        points, fill=TEMP_ROI_COLOUR)
                elif isinstance(self._temp_roi, (TempCircle, TempEllipse)):
                    self._temp_roi_id = self.create_oval(
                        points, outline=TEMP_ROI_COLOUR)
                elif isinstance(self._temp_roi, (TempSquare, TempRectangle)):
                    self._temp_roi_id = self.create_rectangle(
                        points, outline=TEMP_ROI_COLOUR)

    def _mouse_drag(self, event: tk.Event):
        """
        Handles moving the image in the viewer using the mouse.
        """
        delta_x = event.x - self.mouse_x
        delta_y = event.y - self.mouse_y
        self._set_mouse_loc(event)
        self.move_image(delta_x, delta_y)

    def move_image(self, delta_x: float, delta_y: float):
        """
        Moves the image on the viewer based on the given deltas.
        """
        if (isinstance(self.image, ArrayImage)
                and not self._updating):
            self._updating = True
            self._x += delta_x
            self._y += delta_y
            self.image.x = self._x
            self.image.y = self._y
            self.update()
            self._updating = False

    def set_image_loc(self, x: float, y: float):
        """
        Sets the image location on the viewer.
        """
        if (isinstance(self.image, ArrayImage)
                and not self._updating):
            self._updating = True
            self._x = x
            self._y = y
            self.image.x = self._x
            self.image.y = self._y
            self.update()
            self._updating = False

    def _mouse_zoom(self, event: tk.Event):
        """
        Handles mouse zoom events through option setting.
        """
        if (isinstance(self.image, ArrayImage)
                and not self._updating):
            self._updating = True
            delta_y = 0.01 * (self.mouse_y - event.y)
            self.mouse_x = event.x
            self.mouse_y = event.y
            self.change_zoom(delta_y)
            self._updating = False

    def _configure_window(self, *_):
        """
        Handles window configuration events.
        """
        self.update()


class Viewer(BaseViewer[BaseImageSet]):
    """
    Viewer for displaying all images.
    """
    image_type = BaseImageSet

    @classmethod
    def can_show_image(cls, image: BaseImageSet) -> bool:
        return _showable_array_image(image)


class ArrayViewer(BaseViewer[ArrayImage]):
    """
    Viewer for displaying `ArrayImage` images.
    """
    image_type = ArrayImage

    @classmethod
    def can_show_image(cls, image: BaseImageSet) -> TypeGuard[ArrayImage]:
        return _showable_array_image(image)


class MonochromeViewer(BaseViewer[ArrayImage]):
    """
    Viewer for displaying monochrome ArrayImage images (i.e. not RGB or multisample).
    """
    image_type = ArrayImage

    @classmethod
    def can_show_image(cls, image: BaseImageSet) -> TypeGuard[ArrayImage]:
        return _showable_array_image(image) and not image.is_multisample


class DicomViewer(BaseViewer[Series | Instance]):
    """
    Viewer for displaying DICOM Series or Instance images.
    """
    image_type = (Series, Instance)

    @classmethod
    def can_show_image(cls, image: BaseImageSet) -> TypeGuard[Series | Instance]:
        return _showable_array_image(image) and isinstance(image, cls.image_type)


class MonochromeDicomViewer(BaseViewer[Series | Instance]):
    """
    Viewer for displaying monochrome DICOM Series or Instance images (i.e. not RGB or multisample).
    """
    image_type = (Series, Instance)

    @classmethod
    def can_show_image(cls, image: BaseImageSet) -> TypeGuard[Series | Instance]:
        return (_showable_array_image(image)
                and isinstance(image, cls.image_type)
                and not image.is_rgb)
