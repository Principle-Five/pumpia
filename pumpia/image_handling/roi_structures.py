"""
Classes:
 * Angle
 * BaseROI
 * CircleROI
 * EllipseROI
 * LineROI
 * PointROI
 * RectangleROI
 * SquareROI
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
import math
from typing import TYPE_CHECKING, overload
import numpy as np
import matplotlib.pyplot as plt
from pumpia.utilities.array_utils import Pixel


if TYPE_CHECKING:
    from pumpia.image_handling.image_structures import ArrayImage

ROI_COLOUR = "yellow"
ACTIVE_ROI_COLOUR = "red"

PixelStatsType = tuple[float, ...] | float


class BaseROI(ABC):
    """
    Base class for Region of Interest (ROI) in an image.

    Parameters
    ----------
    image : ArrayImage
        The image associated with the ROI.
    slice_num : int, optional
        The slice number of the ROI (default is 0).
    name : str, optional
        The name of the ROI (default is None).
    replace : bool, optional
        Whether to replace an existing ROI with the same name (default is False).
    cache_values : bool, optional
        Whether to cache pixel values and calculated values (default is True).
    colour : str, optional
        The colour of the ROI.
    active_colour : str, optional
        The colour of the ROI when it is selected.

    Attributes
    ----------
    image : ArrayImage
        The image associated with the ROI.
    slice_num : int
        The slice number of the ROI.
    cache_values : bool
        Whether to cache pixel values and calculated values.
    colour : str
        The colour of the ROI.
    active_colour : str
        The colour of the ROI when it is selected.
    active : bool
        Whether the ROI is active.
    hidden : bool
        Whether the ROI is hidden.
    id_string : str
    storage_string : str
    tag : str
    pixel_values : list[int | float | list[float]]
    pixel_array : np.ndarray
    mask : np.ndarray
    area : float
    perimeter : float
    mean : PixelStatsType
    std : PixelStatsType
    xmin : int
    xmax : int
    ymin : int
    ymax : int
    xcent : float
    ycent : float
    values_str : str
    menu_options : list[tuple[str, Callable[[], None]]]

    Methods
    -------
    delete_cache()
        Deletes the cached values of the ROI.
    pixel_is_in(x: float, y: float) -> bool
        Checks if a pixel is inside the ROI.
    pixel_is_on(x: float, y: float, dist: float = 0) -> bool
        Checks if a pixel is on the boundary of the ROI.
    move(x: int = 0, y: int = 0)
        Moves the ROI by the specified amount.
    enlarge(x: float = 1, y: float = 1)
        Enlarges the ROI by the specified amount.
    resize_bbox(x: int = 0, y: int = 0)
        Resizes the bounding box of the ROI.
    rotate(angle: float = 0)
        Rotates the ROI by the specified angle.
    copy_to_image(image: ArrayImage, slice_num: int, name: str | None = None, replace: bool = False, cache_values: bool = True, colour: str = ROI_COLOUR, active_colour: str = ACTIVE_ROI_COLOUR) -> 'BaseROI'
        Copies the ROI to another image.
    move_to_image(image: ArrayImage, slice_num: int, name: str | None = None, replace: bool = False, cache_values: bool = True, colour: str = ROI_COLOUR, active_colour: str = ACTIVE_ROI_COLOUR) -> 'BaseROI'
        Moves the ROI to another image.
    """

    def __init__(self,
                 image: 'ArrayImage',
                 *,
                 slice_num: int = 0,
                 name: str | None = None,
                 replace: bool = False,
                 cache_values: bool = True,
                 colour: str = ROI_COLOUR,
                 active_colour: str = ACTIVE_ROI_COLOUR) -> None:
        self.image: 'ArrayImage' = image

        self.slice_num = slice_num
        self.cache_values: bool = cache_values

        self._pixel_values: list[int | float | list[float]] = []
        self._pixel_array: np.ndarray[tuple[int, int] | tuple[int, int, int],
                                      np.dtype] = np.empty((0, 0))
        self._mask: np.ndarray[tuple[int, int], np.dtype[np.bool]] = np.ones((0, 0), dtype=np.bool)
        self._area: float | None = None
        self._perimeter: float | None = None
        self._mean: PixelStatsType | None = None
        self._std: PixelStatsType | None = None
        self._xmin: int | None = None
        self._xmax: int | None = None
        self._ymin: int | None = None
        self._ymax: int | None = None
        self._xcent: float | None = None
        self._ycent: float | None = None

        self.colour: str = colour
        self.active_colour: str = active_colour

        self.active: bool = False
        self.hidden: bool = False

        if name is None:
            num_rois = len(self.image.get_rois(self.slice_num))
            self.name = "ROI" + str(num_rois)
            while self in self.image.get_rois(self.slice_num):
                num_rois += 1
                self.name = "ROI" + str(num_rois)
            self.image.add_roi(self)

        else:
            self.name = name
            self.image.add_roi(self, replace)

    def __hash__(self):
        """
        Returns the hash of the ROI.

        Returns
        -------
        int
            The hash of the ROI.
        """
        return hash(self.id_string)

    def __eq__(self, value: object) -> bool:
        """
        Checks equality with another object.

        Parameters
        ----------
        value : object
            The object to compare with.

        Returns
        -------
        bool
            True if equal, False otherwise.
        """
        if isinstance(value, BaseROI):
            return value.id_string == self.id_string
        if isinstance(value, str):
            return self.id_string == value
        else:
            return False

    @property
    def id_string(self) -> str:
        """
        Returns the ID string of the ROI.

        Returns
        -------
        str
            The ID string of the ROI.
        """
        return self.image.id_string + " : " + str(self.slice_num) + " ; " + self.name

    @property
    @abstractmethod
    def storage_string(self) -> str:
        """
        Returns the string used for storage of the ROI.
        This should contain all the information required to recreate the ROI.

        Returns
        -------
        str
            The storage string of the ROI.
        """

    def __str__(self) -> str:
        """
        Returns the string representation of the ROI.

        Returns
        -------
        str
            The name of the ROI.
        """
        return self.name

    def delete_cache(self):
        """
        Deletes the cached values of the ROI.
        """
        self._pixel_values = []
        self._pixel_array = np.empty((0, 0))
        self._area = None
        self._perimeter = None
        self._mean = None
        self._std = None
        self._xmin = None
        self._xmax = None
        self._ymin = None
        self._ymax = None
        self._xcent = None
        self._ycent = None

    @overload
    def pixel_is_in(self,
                    x: float,
                    y: float
                    ) -> bool: ...

    @overload
    def pixel_is_in(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    @abstractmethod
    def pixel_is_in(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        """
        Checks if a pixel is inside the ROI.

        Parameters
        ----------
        x : float
            The x-coordinate of the pixel.
        y : float
            The y-coordinate of the pixel.

        Returns
        -------
        bool
            True if the pixel is inside the ROI, False otherwise.
        """

    @overload
    def pixel_is_on(self,
                    x: float,
                    y: float,
                    dist: float = 0
                    ) -> bool: ...

    @overload
    def pixel_is_on(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    @abstractmethod
    def pixel_is_on(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        """
        Checks if a pixel is on the boundary of the ROI.

        Parameters
        ----------
        x : float
            The x-coordinate of the pixel.
        y : float
            The y-coordinate of the pixel.
        dist : float, optional
            The distance from the boundary in pixels (default is 0).

        Returns
        -------
        bool
            True if the pixel is on the boundary of the ROI, False otherwise.
        """

    @abstractmethod
    def move(self, x: int = 0, y: int = 0):
        """
        Moves the ROI by the specified amount.

        Parameters
        ----------
        x : int, optional
            The amount to move in the x-direction (default is 0).
        y : int, optional
            The amount to move in the y-direction (default is 0).
        """

    @abstractmethod
    def enlarge(self, x: float = 1, y: float = 1):
        """
        Enlarges the ROI by the specified amount.

        Parameters
        ----------
        x : float, optional
            The factor to enlarge by in the x-direction (default is 1).
        y : float, optional
            The factor to enlarge by in the y-direction (default is 1).
        """

    @abstractmethod
    def resize_bbox(self, x: int = 0, y: int = 0):
        """
        Resizes the bounding box of the ROI.

        Parameters
        ----------
        x : int, optional
            The new width of the bounding box (default is 0).
        y : int, optional
            The new height of the bounding box (default is 0).
        """

    @abstractmethod
    def rotate(self, angle: float = 0):
        """
        Rotates the ROI by the specified angle.

        Parameters
        ----------
        angle : float, optional
            The angle to rotate by (default is 0).
        """

    @abstractmethod
    def copy_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR) -> 'BaseROI':
        """
        Copies the ROI to another image.

        Parameters
        ----------
        image : ArrayImage
            The image to copy to.
        slice_num : int
            The slice number of the new ROI.
        name : str, optional
            The name of the new ROI. If not given the name of the current ROI is used.
        replace : bool, optional
            Whether to replace an existing ROI with the same name (default is False).
        cache_values : bool, optional
            Whether to cache pixel values in the new ROI (default is True).
        colour : str, optional
            The colour of the new ROI.
        active_colour : str, optional
            The active colour of the new ROI.

        Returns
        -------
        BaseROI
            The new ROI.
        """

    def move_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR):
        """
        Moves the ROI to another image.

        Parameters
        ----------
        image : ArrayImage
            The image to move to.
        slice_num : int
            The slice number of the new ROI.
        name : str, optional
            The name of the new ROI. If not given the name of the current ROI is used.
        replace : bool, optional
            Whether to replace an existing ROI with the same name (default is False).
        cache_values : bool, optional
            Whether to cache pixel values in the new ROI (default is True).

        Returns
        -------
        The new ROI.
        """
        self.image.remove_roi(self)
        return self.copy_to_image(image,
                                  slice_num,
                                  name,
                                  replace,
                                  cache_values,
                                  colour,
                                  active_colour)

    def _load_pixels(self):
        """
        Loads the pixel values of the ROI.
        """
        array: np.ndarray[tuple[int, int, int]
                          | tuple[int, int], np.dtype] = self.image.array[self.slice_num]
        indices = np.indices(array.shape[:2])
        mask = self.pixel_is_in(indices[1],
                                indices[0])
        self._mask = mask
        masked_array: np.ndarray[tuple[int, int, int] | tuple[int, int], np.dtype]
        if array.ndim == 2:
            masked_array = array * mask
        elif array.ndim == 3:
            masked_array = array * np.expand_dims(mask, axis=2)  # type: ignore

        if self.image.is_multisample:
            pixel_array = np.zeros(
                (self.ymax - self.ymin + 1, self.xmax - self.xmin + 1, array.shape[-1]))
        else:
            pixel_array = np.zeros(
                (self.ymax - self.ymin + 1, self.xmax - self.xmin + 1))

        xmin_i = max(0, self.xmin)
        xmax_i = min(self.image.shape[2] - 1, self.xmax)
        ymin_i = max(0, self.ymin)
        ymax_i = min(self.image.shape[1] - 1, self.ymax)

        if xmin_i < xmax_i and ymin_i < ymax_i:
            i_array = masked_array[ymin_i:ymax_i + 1, xmin_i:xmax_i + 1]
            pixel_array[ymin_i - self.ymin:ymax_i - self.ymin + 1,
                        xmin_i - self.xmin:xmax_i - self.xmin + 1] = i_array

        self._pixel_array = pixel_array

        pixel_value_list = list(array[mask])

        if len(pixel_value_list) == 0:
            if self.image.is_multisample:
                self._pixel_values = [list(np.zeros(array.shape[-1]))]
            else:
                self._pixel_values = [0]
        else:
            self._pixel_values = pixel_value_list

    @property
    def tag(self) -> str:
        """
        The tag of the ROI for use in manager treeviews.
        """
        return "RO" + self.id_string

    @property
    def pixel_values(self) -> list[int | float | list[float]]:
        """
        The list of pixel values in the ROI.
        May be a list of lists for multisample images.
        """
        if len(self._pixel_values) == 0 or not self.cache_values:
            self._load_pixels()
        return self._pixel_values

    @property
    def pixel_array(self) -> np.ndarray[tuple[int, int] | tuple[int, int, int], np.dtype]:
        """
        The array of pixel values in the ROI.
        Array has the same shape as the boundbox of the ROI.
        """
        if self._pixel_array.shape[:2] == (0, 0) or not self.cache_values:
            self._load_pixels()
        return self._pixel_array

    @property
    def mask(self) -> np.ndarray[tuple[int, int], np.dtype[np.bool]]:
        """
        The mask array of the ROI.
        """
        if self._mask.shape[:2] == (0, 0) or not self.cache_values:
            self._load_pixels()
        return self._mask

    @property
    @abstractmethod
    def area(self) -> float:
        """
        The area of the ROI.
        """

    @property
    @abstractmethod
    def perimeter(self) -> float:
        """
        The perimeter of the ROI.
        """

    @property
    def mean(self) -> PixelStatsType:
        """
        The mean pixel value in the ROI.
        If the image is RGB or multi-sample, returns a tuple of means.
        """
        if self._mean is None or not self.cache_values:
            if self.pixel_array.ndim > 2:
                self._mean = tuple(np.mean(self.pixel_values, axis=0).astype(float))
            else:
                self._mean = np.mean(self.pixel_values).astype(float)
        return self._mean  # type: ignore

    @property
    def std(self) -> PixelStatsType:
        """
        Returns the standard deviation of pixel values in the ROI.
        If the image is RGB or multi-sample, returns a tuple of standard deviations.
        """
        if self._std is None or not self.cache_values:
            if self.pixel_array.ndim > 2:
                self._std = tuple(np.std(self.pixel_values, axis=0).astype(float))
            else:
                self._std = np.std(self.pixel_values).astype(float)
        return self._std  # type: ignore

    @property
    @abstractmethod
    def xmin(self) -> int:
        """
        The minimum x-coordinate of the ROI.
        """

    @property
    @abstractmethod
    def xmax(self) -> int:
        """
        The maximum x-coordinate of the ROI.
        """

    @property
    @abstractmethod
    def ymin(self) -> int:
        """
        The minimum y-coordinate of the ROI.
        """

    @property
    @abstractmethod
    def ymax(self) -> int:
        """
        The maximum y-coordinate of the ROI.
        """

    @property
    @abstractmethod
    def xcent(self) -> float:
        """
        The x-coordinate of the centroid of the ROI.
        """

    @property
    @abstractmethod
    def ycent(self) -> float:
        """
        The y-coordinate of the centroid of the ROI.
        """

    @property
    @abstractmethod
    def values_str(self) -> str:
        """
        The string representation of the ROI values.
        """

    @property
    def menu_options(self) -> list[tuple[str, Callable[[], None]]]:
        """
        The menu options for the ROI.

        Returns
        -------
        list of tuple
            The menu options for the ROI in the form `(string to show in menu, function to call)`.
        """
        return []


class Angle(BaseROI):
    """
    Represents an angle ROI.
    Has the same attributes and methods as BaseROI unless stated below.

    Parameters
    ----------
    x : int
        The x-coordinate of the vertex.
    y : int
        The y-coordinate of the vertex.
    x1 : int
        The x-coordinate of the first point.
    y1 : int
        The y-coordinate of the first point.
    x2 : int
        The x-coordinate of the second point.
    y2 : int
        The y-coordinate of the second point.

    Attributes
    ----------
    x : int
        The x-coordinate of the vertex.
    y : int
        The y-coordinate of the vertex.
    x1 : int
        The x-coordinate of the first point.
    y1 : int
        The y-coordinate of the first point.
    x2 : int
        The x-coordinate of the second point.
    y2 : int
        The y-coordinate of the second point.
    angle : float
    angle_degrees : float
    """

    def __init__(self, image: 'ArrayImage',
                 x: int,
                 y: int,
                 x1: int,
                 y1: int,
                 x2: int,
                 y2: int,
                 *,
                 slice_num: int = 0,
                 name: str | None = None,
                 replace: bool = False,
                 cache_values: bool = True,
                 colour: str = ROI_COLOUR,
                 active_colour: str = ACTIVE_ROI_COLOUR):

        if ((x, y) == (x1, y1)
            or (x, y) == (x2, y2)
                or (x1, y1) == (x2, y2)):
            raise ValueError("Points must be in different places")
        self.x: int = x
        self.y: int = y
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2

        self._angle: float | None = None
        super().__init__(image,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def storage_string(self) -> str:
        return (self.id_string
                + " ; " + "Angle"
                + " ; " + str(self.x)
                + " ; " + str(self.y)
                + " ; " + str(self.x1)
                + " ; " + str(self.y1)
                + " ; " + str(self.x2)
                + " ; " + str(self.y2))

    @overload
    def pixel_is_in(self,
                    x: float,
                    y: float
                    ) -> bool: ...

    @overload
    def pixel_is_in(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_in(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return False

    @overload
    def pixel_is_on(self,
                    x: float,
                    y: float,
                    dist: float = 0
                    ) -> bool: ...

    @overload
    def pixel_is_on(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_on(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return False

    def move(self, x: int = 0, y: int = 0):
        self.x += x
        self.y += y
        self.x1 += x
        self.y1 += y
        self.x2 += x
        self.y2 += y
        self.delete_cache()

    def delete_cache(self):
        self._angle = None
        super().delete_cache()

    def enlarge(self, x: float = 1, y: float = 1):
        pass

    def resize_bbox(self, x: int = 0, y: int = 0):
        pass

    def rotate(self, angle: float = 0):
        pass

    def copy_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR) -> 'Angle':
        if name is None:
            name = self.name
        return Angle(image,
                     self.x,
                     self.y,
                     self.x1,
                     self.y1,
                     self.x2,
                     self.y2,
                     slice_num=slice_num,
                     name=name,
                     replace=replace,
                     cache_values=cache_values,
                     colour=colour,
                     active_colour=active_colour)

    @property
    def angle(self) -> float:
        """
        Returns the angle of the ROI in radians.

        Returns
        -------
        float
            The angle of the ROI.
        """
        if self._angle is None or not self.cache_values:
            ax = self.x1 - self.x
            ay = self.y1 - self.y
            bx = self.x2 - self.x
            by = self.y2 - self.y
            a = math.sqrt(ax**2 + ay**2)
            b = math.sqrt(bx**2 + by**2)
            cosa = (ax * bx + ay * by) / (a * b)
            self._angle = math.acos(cosa)
        return self._angle

    @property
    def angle_degrees(self) -> float:
        """
        Returns the angle of the ROI in degrees.

        Returns
        -------
        float
            The angle of the ROI in degrees.
        """
        return self.angle * 180 / math.pi

    @property
    def pixels(self) -> list[Pixel]:
        """
        Not implemented for Angle ROI.
        """
        raise NotImplementedError

    @property
    def area(self) -> float:
        """
        Not implemented for Angle ROI
        """
        raise NotImplementedError

    @property
    def perimeter(self) -> float:
        """
        Not implemented for Angle ROI
        """
        raise NotImplementedError

    @property
    def mean(self) -> PixelStatsType:
        """
        Not implemented for Angle ROI
        """
        raise NotImplementedError

    @property
    def std(self) -> PixelStatsType:
        """
        Not implemented for Angle ROI
        """
        raise NotImplementedError

    @property
    def xmin(self) -> int:
        if self._xmin is None or not self.cache_values:
            self._xmin = min(self.x, self.x1, self.x2)
        return self._xmin

    @property
    def xmax(self) -> int:
        if self._xmax is None or not self.cache_values:
            self._xmax = max(self.x, self.x1, self.x2)
        return self._xmax

    @property
    def ymin(self) -> int:
        if self._ymin is None or not self.cache_values:
            self._ymin = min(self.y, self.y1, self.y2)
        return self._ymin

    @property
    def ymax(self) -> int:
        if self._ymax is None or not self.cache_values:
            self._ymax = max(self.y, self.y1, self.y2)
        return self._ymax

    @property
    def xcent(self) -> int:
        """
        Returns the x-coordinate vertex of the angle.
        """
        return self.x

    @property
    def ycent(self) -> int:
        """
        Returns the y-coordinate of the vertex of the angle.
        """
        return self.y

    @property
    def values_str(self) -> str:
        vals = f"Angle: {self.angle_degrees:.1f} degrees"
        return vals


class PointROI(BaseROI):
    """
    Represents a point ROI.
    Has the same attributes and methods as BaseROI unless stated below.

    Parameters
    ----------
    x : int
        The x-coordinate of the point.
    y : int
        The y-coordinate of the point.

    Attributes
    ----------
    x : int
        The x-coordinate of the point.
    y : int
        The y-coordinate of the point.
    """

    def __init__(self, image: 'ArrayImage',
                 x: int,
                 y: int,
                 *,
                 slice_num: int = 0,
                 name: str | None = None,
                 replace: bool = False,
                 cache_values: bool = True,
                 colour: str = ROI_COLOUR,
                 active_colour: str = ACTIVE_ROI_COLOUR):
        self.x: int = x
        self.y: int = y
        super().__init__(image,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def storage_string(self) -> str:
        return (self.id_string
                + " ; " + "Point"
                + " ; " + str(self.x)
                + " ; " + str(self.y))

    @overload
    def pixel_is_in(self,
                    x: float,
                    y: float
                    ) -> bool: ...

    @overload
    def pixel_is_in(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_in(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return ((np.floor(x) == self.x) & (np.floor(y) == self.y))

    @overload
    def pixel_is_on(self,
                    x: float,
                    y: float,
                    dist: float = 0
                    ) -> bool: ...

    @overload
    def pixel_is_on(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_on(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return ((np.abs(self.x - x) <= dist)
                & (np.abs(self.y - y) <= dist))

    def move(self, x: int = 0, y: int = 0):
        self.x += x
        self.y += y
        self.delete_cache()

    def enlarge(self, x: float = 1, y: float = 1):
        pass

    def resize_bbox(self, x: int = 0, y: int = 0):
        pass

    def rotate(self, angle: float = 0):
        pass

    def copy_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR) -> 'PointROI':
        if name is None:
            name = self.name
        return PointROI(image,
                        self.x,
                        self.y,
                        slice_num=slice_num,
                        name=name,
                        replace=replace,
                        cache_values=cache_values,
                        colour=colour,
                        active_colour=active_colour)

    @property
    def area(self) -> float:
        if self._area is None or not self.cache_values:
            self._area = 1
        return self._area

    @property
    def perimeter(self) -> float:
        if self._perimeter is None or not self.cache_values:
            self._perimeter = 4
        return self._perimeter

    @property
    def xmin(self) -> int:
        return self.x

    @property
    def xmax(self) -> int:
        return self.x

    @property
    def ymin(self) -> int:
        return self.y

    @property
    def ymax(self) -> int:
        return self.y

    @property
    def xcent(self) -> int:
        return self.x

    @property
    def ycent(self) -> int:
        return self.y

    @property
    def values_str(self) -> str:
        if isinstance(self.mean, tuple):
            mean_str = f"[{", ".join([f"{val:.1f}" for val in self.mean])}], "
        else:
            mean_str = f"{self.mean:.1f}, "

        return (f"x: {self.x}, "
                + f"y: {self.y}, "
                + f"Value: {mean_str}, ")


class CircleROI(BaseROI):
    """
    Represents a circle ROI.

    This can only be used with images with a pixel width/height ration of 1.
    For this reason it is not recommended to use it programatically
    and it is left out of most documentation.

    Has the same attributes and methods as BaseROI unless stated below.

    Parameters
    ----------
    x : int
        The x-coordinate of the center of the circle.
    y : int
        The y-coordinate of the center of the circle.
    r : int
        The radius of the circle.

    Attributes
    ----------
    x : int
        The x-coordinate of the center of the circle.
    y : int
        The y-coordinate of the center of the circle.
    r : int
        The radius of the circle.
    """

    def __init__(self,
                 image: 'ArrayImage',
                 x: int,
                 y: int,
                 r: int,
                 *,
                 slice_num: int = 0,
                 name: str | None = None,
                 replace: bool = False,
                 cache_values: bool = True,
                 colour: str = ROI_COLOUR,
                 active_colour: str = ACTIVE_ROI_COLOUR):
        if image.aspect != 1:
            raise ValueError("Images pixels need to be isotropic to use Circles")
        if r <= 0:
            raise ValueError("Radius must be greater than 0")
        self.x: int = x
        self.y: int = y
        self.r: int = r
        super().__init__(image,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def storage_string(self) -> str:
        return (self.id_string
                + " ; " + "Circle"
                + " ; " + str(self.x)
                + " ; " + str(self.y)
                + " ; " + str(self.r))

    @overload
    def pixel_is_in(self,
                    x: float,
                    y: float
                    ) -> bool: ...

    @overload
    def pixel_is_in(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_in(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return (x - self.x)**2 + (y - self.y)**2 < self.r**2

    @overload
    def pixel_is_on(self,
                    x: float,
                    y: float,
                    dist: float = 0
                    ) -> bool: ...

    @overload
    def pixel_is_on(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_on(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return np.abs(np.sqrt((x - self.x)**2 + (y - self.y)**2) - self.r) <= dist

    def move(self, x: int = 0, y: int = 0):
        self.x += x
        self.y += y
        self.delete_cache()

    def enlarge(self, x: float = 1, y: float = 1):
        f = max(abs(x), abs(y))
        self.r = abs(round(self.r * f))
        if self.r == 0:
            self.r = 1
        self.delete_cache()

    def resize_bbox(self, x: int = 0, y: int = 0):
        self.r = round(max(abs(x), abs(y)) / 2)
        if self.r == 0:
            self.r = 1
        self.delete_cache()

    def rotate(self, angle: float = 0):
        pass

    def copy_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR) -> 'CircleROI':
        if name is None:
            name = self.name
        return CircleROI(image,
                         self.x,
                         self.y,
                         self.r,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def area(self) -> float:
        if self._area is None or not self.cache_values:
            self._area = math.pi * (self.r**2)
        return self._area

    @property
    def perimeter(self) -> float:
        if self._perimeter is None or not self.cache_values:
            self._perimeter = 2 * math.pi * self.r
        return self._perimeter

    @property
    def xmin(self) -> int:
        if self._xmin is None or not self.cache_values:
            self._xmin = self.x - self.r
        return self._xmin

    @property
    def xmax(self) -> int:
        if self._xmax is None or not self.cache_values:
            self._xmax = self.x + self.r
        return self._xmax

    @property
    def ymin(self) -> int:
        if self._ymin is None or not self.cache_values:
            self._ymin = self.y - self.r
        return self._ymin

    @property
    def ymax(self) -> int:
        if self._ymax is None or not self.cache_values:
            self._ymax = self.y + self.r
        return self._ymax

    @property
    def xcent(self) -> int:
        return self.x

    @property
    def ycent(self) -> int:
        return self.y

    @property
    def values_str(self) -> str:
        if isinstance(self.mean, tuple):
            mean_str = f"[{", ".join([f"{val:.1f}" for val in self.mean])}], "
        else:
            mean_str = f"{self.mean:.1f}, "

        if isinstance(self.std, tuple):
            std_str = f"[{", ".join([f"{val:.1f}" for val in self.std])}], "
        else:
            std_str = f"{self.std:.1f}, "

        return (f"Area: {self.area:.1f}, "
                + f"Perimeter: {self.perimeter:.1f}, "
                + f"Mean: {mean_str}, "
                + f"Std: {std_str}")


class EllipseROI(BaseROI):
    """
    Represents an ellipse ROI.
    Has the same attributes and methods as BaseROI unless stated below.

    Parameters
    ----------
    x : int
        The x-coordinate of the center of the ellipse.
    y : int
        The y-coordinate of the center of the ellipse.
    a : int
        The semi-major axis of the ellipse.
    b : int
        The semi-minor axis of the ellipse.

    Attributes
    ----------
    x : int
        The x-coordinate of the center of the ellipse.
    y : int
        The y-coordinate of the center of the ellipse.
    a : int
        The semi-major axis of the ellipse.
    b : int
        The semi-minor axis of the ellipse.
    """

    def __init__(self,
                 image: 'ArrayImage',
                 x: int,
                 y: int,
                 a: int,
                 b: int,
                 *,
                 slice_num: int = 0,
                 name: str | None = None,
                 replace: bool = False,
                 cache_values: bool = True,
                 colour: str = ROI_COLOUR,
                 active_colour: str = ACTIVE_ROI_COLOUR):
        if a <= 0 or b <= 0:
            raise ValueError("Axes must be greater than 0")
        self.x: int = x
        self.y: int = y
        self.a: int = a
        self.b: int = b
        super().__init__(image,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def storage_string(self) -> str:
        return (self.id_string
                + " ; " + "Ellipse"
                + " ; " + str(self.x)
                + " ; " + str(self.y)
                + " ; " + str(self.a)
                + " ; " + str(self.b))

    @overload
    def pixel_is_in(self,
                    x: float,
                    y: float
                    ) -> bool: ...

    @overload
    def pixel_is_in(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_in(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:

        return ((x - self.x) / self.a)**2 + ((y - self.y) / self.b)**2 < 1

    @overload
    def pixel_is_on(self,
                    x: float,
                    y: float,
                    dist: float = 0
                    ) -> bool: ...

    @overload
    def pixel_is_on(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_on(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:

        return np.abs(((x - self.x) / self.a)**2 + ((y - self.y) / self.b)**2 - 1) <= dist

    def move(self, x: int = 0, y: int = 0):
        self.x += x
        self.y += y
        self.delete_cache()

    def enlarge(self, x: float = 1, y: float = 1):
        self.a = abs(round(self.a * x))
        self.b = abs(round(self.b * y))

        if self.a == 0:
            self.a = 1
        elif self.a < 0:
            self.a = abs(self.a)

        if self.b == 0:
            self.b = 1
        elif self.b < 0:
            self.b = abs(self.b)

        self.delete_cache()

    def resize_bbox(self, x: int = 0, y: int = 0):
        self.a = round(x / 2)
        self.b = round(y / 2)

        if self.a == 0:
            self.a = 1
        elif self.a < 0:
            self.a = abs(self.a)

        if self.b == 0:
            self.b = 1
        elif self.b < 0:
            self.b = abs(self.b)

        self.delete_cache()

    def rotate(self, angle: float = 0):
        """
        Not implemented for Ellipse roi.
        """
        raise NotImplementedError

    def copy_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR) -> 'EllipseROI':
        if name is None:
            name = self.name
        return EllipseROI(image,
                          self.x,
                          self.y,
                          self.a,
                          self.b,
                          slice_num=slice_num,
                          name=name,
                          replace=replace,
                          cache_values=cache_values,
                          colour=colour,
                          active_colour=active_colour)

    @property
    def area(self) -> float:
        if self._area is None or not self.cache_values:
            self._area = math.pi * self.a * self.b
        return self._area

    @property
    def perimeter(self) -> float:
        """
        Not implemented for Ellipse ROI.
        """
        raise NotImplementedError

    @property
    def xmin(self) -> int:
        if self._xmin is None or not self.cache_values:
            self._xmin = self.x - self.a
        return self._xmin

    @property
    def xmax(self) -> int:
        if self._xmax is None or not self.cache_values:
            self._xmax = self.x + self.a
        return self._xmax

    @property
    def ymin(self) -> int:
        if self._ymin is None or not self.cache_values:
            self._ymin = self.y - self.b
        return self._ymin

    @property
    def ymax(self) -> int:
        if self._ymax is None or not self.cache_values:
            self._ymax = self.y + self.b
        return self._ymax

    @property
    def xcent(self) -> int:
        return self.x

    @property
    def ycent(self) -> int:
        return self.y

    @property
    def values_str(self) -> str:
        if isinstance(self.mean, tuple):
            mean_str = f"[{", ".join([f"{val:.1f}" for val in self.mean])}], "
        else:
            mean_str = f"{self.mean:.1f}, "

        if isinstance(self.std, tuple):
            std_str = f"[{", ".join([f"{val:.1f}" for val in self.std])}], "
        else:
            std_str = f"{self.std:.1f}, "

        return (f"Area: {self.area:.1f}, "
                + f"Mean: {mean_str}, "
                + f"Std: {std_str}")


class SquareROI(BaseROI):
    """
    Represents a square ROI.

    This can only be used with images with a pixel width/height ration of 1.
    For this reason it is not recommended to use it programatically
    and it is left out of most documentation.

    Has the same attributes and methods as BaseROI unless stated below.

    Parameters
    ----------
    xmin : int
        The minimum x-coordinate of the square.
    ymin : int
        The minimum y-coordinate of the square.
    r : int
        The side length of the square.

    Attributes
    ----------
    x : int
        The minimum x-coordinate of the square.
    y : int
        The minimum y-coordinate of the square.
    r : int
        The side length of the square.
    h_profile : np.ndarray
    v_profile : np.ndarray

    Methods
    -------
    plot_h_profile()
        Plots the horizontal profile of the ROI in a new window.
    plot_v_profile()
        Plots the vertical profile of the ROI in a new window.
    """

    def __init__(self,
                 image: 'ArrayImage',
                 xmin: int,
                 ymin: int,
                 r: int,
                 *,
                 slice_num: int = 0,
                 name: str | None = None,
                 replace: bool = False,
                 cache_values: bool = True,
                 colour: str = ROI_COLOUR,
                 active_colour: str = ACTIVE_ROI_COLOUR):
        if image.aspect != 1:
            raise ValueError("Images pixels need to be isotropic to use Squares")
        if r <= 0:
            raise ValueError("Side length must be greater than 0")
        self.x: int = xmin
        self.y: int = ymin
        self.r: int = r
        self._h_profile: np.ndarray[tuple[int] | tuple[int, int], np.dtype] | None = None
        self._v_profile: np.ndarray[tuple[int] | tuple[int, int], np.dtype] | None = None
        super().__init__(image,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def storage_string(self) -> str:
        return (self.id_string
                + " ; " + "Square"
                + " ; " + str(self.x)
                + " ; " + str(self.y)
                + " ; " + str(self.r))

    def delete_cache(self):
        super().delete_cache()
        self._h_profile = None
        self._v_profile = None

    @overload
    def pixel_is_in(self,
                    x: float,
                    y: float
                    ) -> bool: ...

    @overload
    def pixel_is_in(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_in(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return ((self.xmin <= x)
                & (x <= self.xmax)
                & (self.ymin <= y)
                & (y <= self.ymax))

    @overload
    def pixel_is_on(self,
                    x: float,
                    y: float,
                    dist: float = 0
                    ) -> bool: ...

    @overload
    def pixel_is_on(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_on(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return ((((np.abs(self.xmin - x) <= dist)
                  | (np.abs(x - self.xmax) <= dist))
                & (self.ymin - dist <= y)
                & (y <= self.ymax + dist))
                | ((self.xmin - dist <= x)
                & (x <= self.xmax + dist)
                & ((np.abs(self.ymin - y) <= dist)
                   | (np.abs(y - self.ymax) <= dist))))

    def move(self, x: int = 0, y: int = 0):
        self.x += x
        self.y += y
        self.delete_cache()

    def enlarge(self, x: float = 1, y: float = 1):
        f = max(x, y, key=abs)
        r = round(self.r * f)
        if r < 0:
            if x < 0:
                self.x = self.xmax
            if y < 0:
                self.y = self.ymax
        self.r = abs(r)
        self.delete_cache()

    def resize_bbox(self, x: int = 0, y: int = 0):
        r = max(x, y, key=abs)
        if r < 0:
            if x < 0:
                self.x = self.xmax
            if y < 0:
                self.y = self.ymax
        self.r = abs(r)
        self.delete_cache()

    def rotate(self, angle: float = 0):
        """
        Not implemented for Square ROI.
        """
        raise NotImplementedError

    def copy_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR) -> 'SquareROI':
        if name is None:
            name = self.name
        return SquareROI(image,
                         self.xmin,
                         self.ymin,
                         self.r,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def area(self) -> float:
        if self._area is None or not self.cache_values:
            self._area = self.r**2
        return self._area

    @property
    def perimeter(self) -> float:
        if self._perimeter is None or not self.cache_values:
            self._perimeter = 4 * self.r
        return self._perimeter

    @property
    def xmin(self) -> int:
        if self._xmin is None or not self.cache_values:
            self._xmin = self.x
        return self._xmin

    @property
    def xmax(self) -> int:
        if self._xmax is None or not self.cache_values:
            self._xmax = self.x + self.r
        return self._xmax

    @property
    def ymin(self) -> int:
        if self._ymin is None or not self.cache_values:
            self._ymin = self.y
        return self._ymin

    @property
    def ymax(self) -> int:
        if self._ymax is None or not self.cache_values:
            self._ymax = self.y + self.r
        return self._ymax

    @property
    def xcent(self) -> float:
        if self._xcent is None or not self.cache_values:
            self._xcent = self.xmin + self.r / 2
        return self._xcent

    @property
    def ycent(self) -> float:
        if self._ycent is None or not self.cache_values:
            self._ycent = self.ymin + self.r / 2
        return self._ycent

    @property
    def h_profile(self) -> np.ndarray[tuple[int] | tuple[int, int], np.dtype]:
        """
        The horizontal profile of the ROI.
        """
        if self._h_profile is None or not self.cache_values:
            self._h_profile = np.sum(self.pixel_array, axis=0)
        return self._h_profile  # type: ignore

    @property
    def v_profile(self) -> np.ndarray[tuple[int] | tuple[int, int], np.dtype]:
        """
        The vertical profile of the ROI.
        """
        if self._v_profile is None or not self.cache_values:
            self._v_profile = np.sum(self.pixel_array, axis=1)
        return self._v_profile  # type: ignore

    @property
    def values_str(self) -> str:
        if isinstance(self.mean, tuple):
            mean_str = f"[{", ".join([f"{val:.1f}" for val in self.mean])}], "
        else:
            mean_str = f"{self.mean:.1f}, "

        if isinstance(self.std, tuple):
            std_str = f"[{", ".join([f"{val:.1f}" for val in self.std])}], "
        else:
            std_str = f"{self.std:.1f}, "

        return (f"Area: {self.area:.1f}, "
                + f"Perimeter: {self.perimeter:.1f}, "
                + f"Mean: {mean_str}, "
                + f"Std: {std_str}")

    @property
    def menu_options(self) -> list[tuple[str, Callable[[], None]]]:
        options = super().menu_options
        options.extend([("Plot Horizontal Profile", self.plot_h_profile),
                        ("Plot Vertical Profile", self.plot_v_profile)])
        return options

    def plot_h_profile(self):
        """
        Plots the horizontal profile of the ROI in a new window.
        """
        plt.clf()
        plt.plot(self.h_profile)
        try:
            name = str(self.image)
            plt.title(f"Horizontal Profile for {name}")
        except NotImplementedError:
            plt.title("Horizontal Profile")
        plt.xlabel("Position (Pixels)")
        plt.ylabel("Value")
        plt.show()

    def plot_v_profile(self):
        """
        Plots the vertical profile of the ROI in a new window.
        """
        plt.clf()
        plt.plot(self.v_profile)
        try:
            name = str(self.image)
            plt.title(f"Vertical Profile for {name}")
        except NotImplementedError:
            plt.title("Vertical Profile")
        plt.xlabel("Position (Pixels)")
        plt.ylabel("Value")
        plt.show()


class RectangleROI(BaseROI):
    """
    Represents a rectangle ROI.
    Has the same attributes and methods as BaseROI unless stated below.

    Parameters
    ----------
    xmin : int
        The minimum x-coordinate of the rectangle.
    ymin : int
        The minimum y-coordinate of the rectangle.
    xmax : int
        The maximum x-coordinate of the rectangle.
    ymax : int
        The maximum y-coordinate of the rectangle.

    Attributes
    ----------
    x : int
        The minimum x-coordinate of the rectangle.
    y : int
        The minimum y-coordinate of the rectangle.
    a : int
        The width of the rectangle.
    b : int
        The height of the rectangle.
    h_profile : np.ndarray
    v_profile : np.ndarray

    Methods
    -------
    plot_h_profile()
        Plots the horizontal profile of the ROI in a new window.
    plot_v_profile()
        Plots the vertical profile of the ROI in a new window.
    """

    def __init__(self,
                 image: 'ArrayImage',
                 xmin: int,
                 ymin: int,
                 xmax: int,
                 ymax: int,
                 *,
                 slice_num: int = 0,
                 name: str | None = None,
                 replace: bool = False,
                 cache_values: bool = True,
                 colour: str = ROI_COLOUR,
                 active_colour: str = ACTIVE_ROI_COLOUR):
        if xmin == xmax or ymin == ymax:
            raise ValueError("Side lengths must be greater than 0")
        self.x: int = min(xmin, xmax)
        self.y: int = min(ymin, ymax)
        self.a: int = max(xmax, xmin) - min(xmin, xmax)
        self.b: int = max(ymax, ymin) - min(ymin, ymax)
        self._h_profile: np.ndarray[tuple[int] | tuple[int, int], np.dtype] | None = None
        self._v_profile: np.ndarray[tuple[int] | tuple[int, int], np.dtype] | None = None
        super().__init__(image,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def storage_string(self) -> str:
        return (self.id_string
                + " ; " + "Rectangle"
                + " ; " + str(self.x)
                + " ; " + str(self.y)
                + " ; " + str(self.a)
                + " ; " + str(self.b))

    def delete_cache(self):
        super().delete_cache()
        self._h_profile = None
        self._v_profile = None

    @overload
    def pixel_is_in(self,
                    x: float,
                    y: float
                    ) -> bool: ...

    @overload
    def pixel_is_in(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_in(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return ((self.xmin <= x)
                & (x <= self.xmax)
                & (self.ymin <= y)
                & (y <= self.ymax))

    @overload
    def pixel_is_on(self,
                    x: float,
                    y: float,
                    dist: float = 0
                    ) -> bool: ...

    @overload
    def pixel_is_on(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_on(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return ((((np.abs(self.xmin - x) <= dist)
                 | (np.abs(x - self.xmax) <= dist))
                & (self.ymin - dist <= y)
                & (y <= self.ymax + dist))
                | ((self.xmin - dist <= x)
                & (x <= self.xmax + dist)
                & ((np.abs(self.ymin - y) <= dist)
                   | (np.abs(y - self.ymax) <= dist))))

    def move(self, x: int = 0, y: int = 0):
        self.x += x
        self.y += y
        self.delete_cache()

    def enlarge(self, x: float = 1, y: float = 1):
        a = round(self.a * x)
        b = round(self.b * y)
        if a < 0:
            self.x = self.xmax
        self.a = abs(a)

        if b < 0:
            self.y = self.ymax
        self.b = abs(b)

        self.delete_cache()

    def resize_bbox(self, x: int = 0, y: int = 0):
        a = round(x)
        b = round(y)
        if a < 0:
            self.x = self.xmax
        self.a = abs(a)

        if b < 0:
            self.y = self.ymax
        self.b = abs(b)

        self.delete_cache()

    def rotate(self, angle: float = 0):
        """
        Not implemented for Rectangle ROI.
        """
        raise NotImplementedError

    def copy_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR) -> 'RectangleROI':
        if name is None:
            name = self.name
        return RectangleROI(image,
                            self.xmin,
                            self.ymin,
                            self.xmax,
                            self.ymax,
                            slice_num=slice_num,
                            name=name,
                            replace=replace,
                            cache_values=cache_values,
                            colour=colour,
                            active_colour=active_colour)

    @property
    def area(self) -> float:
        if self._area is None or not self.cache_values:
            self._area = (self.xmax - self.xmin) * (self.ymax - self.ymin)
        return self._area

    @property
    def perimeter(self) -> float:
        if self._perimeter is None or not self.cache_values:
            self._perimeter = 2 * (self.xmax - self.xmin) + 2 * (self.ymax - self.ymin)
        return self._perimeter

    @property
    def xmin(self) -> int:
        if self._xmin is None or not self.cache_values:
            self._xmin = self.x
        return self._xmin

    @property
    def xmax(self) -> int:
        if self._xmax is None or not self.cache_values:
            self._xmax = self.x + self.a
        return self._xmax

    @property
    def ymin(self) -> int:
        if self._ymin is None or not self.cache_values:
            self._ymin = self.y
        return self._ymin

    @property
    def ymax(self) -> int:
        if self._ymax is None or not self.cache_values:
            self._ymax = self.y + self.b
        return self._ymax

    @property
    def xcent(self) -> float:
        if self._xcent is None or not self.cache_values:
            self._xcent = self.xmin + self.a / 2
        return self._xcent

    @property
    def ycent(self) -> float:
        if self._ycent is None or not self.cache_values:
            self._ycent = self.ymin + self.b / 2
        return self._ycent

    @property
    def h_profile(self) -> np.ndarray[tuple[int] | tuple[int, int], np.dtype]:
        """
        The horizontal profile of the ROI.
        """
        if self._h_profile is None or not self.cache_values:
            self._h_profile = np.sum(self.pixel_array, axis=0)
        return self._h_profile  # type: ignore

    @property
    def v_profile(self) -> np.ndarray[tuple[int] | tuple[int, int], np.dtype]:
        """
        The vertical profile of the ROI.
        """
        if self._v_profile is None or not self.cache_values:
            self._v_profile = np.sum(self.pixel_array, axis=1)
        return self._v_profile  # type: ignore

    @property
    def values_str(self) -> str:
        if isinstance(self.mean, tuple):
            mean_str = f"[{", ".join([f"{val:.1f}" for val in self.mean])}], "
        else:
            mean_str = f"{self.mean:.1f}, "

        if isinstance(self.std, tuple):
            std_str = f"[{", ".join([f"{val:.1f}" for val in self.std])}], "
        else:
            std_str = f"{self.std:.1f}, "

        return (f"Area: {self.area:.1f}, "
                + f"Perimeter: {self.perimeter:.1f}, "
                + f"Mean: {mean_str}, "
                + f"Std: {std_str}")

    @property
    def menu_options(self) -> list[tuple[str, Callable[[], None]]]:
        options = super().menu_options
        options.extend([("Plot Horizontal Profile", self.plot_h_profile),
                        ("Plot Vertical Profile", self.plot_v_profile)])
        return options

    def plot_h_profile(self):
        """
        Plots the horizontal profile of the ROI in a new window.
        """
        plt.clf()
        plt.plot(self.h_profile)
        try:
            name = str(self.image)
            plt.title(f"Horizontal Profile for {name}")
        except NotImplementedError:
            plt.title("Horizontal Profile")
        plt.xlabel("Position (Pixels)")
        plt.ylabel("Value")
        plt.show()

    def plot_v_profile(self):
        """
        Plots the vertical profile of the ROI in a new window.
        """
        plt.clf()
        plt.plot(self.v_profile)
        try:
            name = str(self.image)
            plt.title(f"Vertical Profile for {name}")
        except NotImplementedError:
            plt.title("Vertical Profile")
        plt.xlabel("Position (Pixels)")
        plt.ylabel("Value")
        plt.show()


class LineROI(BaseROI):
    """
    Represents a line ROI.
    Has the same attributes and methods as BaseROI unless stated below.

    Parameters
    ----------
    x1 : int
        The x-coordinate of the first point.
    y1 : int
        The y-coordinate of the first point.
    x2 : int
        The x-coordinate of the second point.
    y2 : int
        The y-coordinate of the second point.

    Attributes
    ----------
    x1 : int
        The x-coordinate of the first point.
    y1 : int
        The y-coordinate of the first point.
    x2 : int
        The x-coordinate of the second point.
    y2 : int
        The y-coordinate of the second point.
    length : float
    profile : np.ndarray
    x_len : int
    y_len : int

    Methods
    -------
    plot_profile()
        Plots the profile of the ROI in a new window.
    """

    def __init__(self,
                 image: 'ArrayImage',
                 x1: int,
                 y1: int,
                 x2: int,
                 y2: int,
                 *,
                 slice_num: int = 0,
                 name: str | None = None,
                 replace: bool = False,
                 cache_values: bool = True,
                 colour: str = ROI_COLOUR,
                 active_colour: str = ACTIVE_ROI_COLOUR):
        if (x1, y1) == (x2, y2):
            raise ValueError("Line ends must not be in the same place")
        self._length: float | None = None
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2
        super().__init__(image,
                         slice_num=slice_num,
                         name=name,
                         replace=replace,
                         cache_values=cache_values,
                         colour=colour,
                         active_colour=active_colour)

    @property
    def storage_string(self) -> str:
        return (self.id_string
                + " ; " + "Line"
                + " ; " + str(self.x1)
                + " ; " + str(self.y1)
                + " ; " + str(self.x2)
                + " ; " + str(self.y2))

    @overload
    def pixel_is_in(self,
                    x: float,
                    y: float
                    ) -> bool: ...

    @overload
    def pixel_is_in(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_in(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]]
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return False

    @overload
    def pixel_is_on(self,
                    x: float,
                    y: float,
                    dist: float = 0
                    ) -> bool: ...

    @overload
    def pixel_is_on(self,
                    x: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> np.ndarray[tuple[int, ...], np.dtype[np.bool]]: ...

    def pixel_is_on(self,
                    x: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    y: float | np.ndarray[tuple[int, ...], np.dtype[np.floating]],
                    dist: float = 0
                    ) -> bool | np.ndarray[tuple[int, ...], np.dtype[np.bool]]:
        return False

    def move(self, x: int = 0, y: int = 0):
        self.x1 += x
        self.y1 += y
        self.x2 += x
        self.y2 += y
        self.delete_cache()

    def delete_cache(self):
        self._length = None
        return super().delete_cache()

    def enlarge(self, x: float = 1, y: float = 1):
        """
        Not implemented for Line ROI.
        """
        raise NotImplementedError

    def resize_bbox(self, x: int = 0, y: int = 0):
        """
        Not implemented for Line ROI.
        """
        raise NotImplementedError

    def rotate(self, angle: float = 0):
        """
        Not implemented for Line ROI.
        """
        raise NotImplementedError

    def copy_to_image(self,
                      image: 'ArrayImage',
                      slice_num: int,
                      name: str | None = None,
                      replace: bool = False,
                      cache_values: bool = True,
                      colour: str = ROI_COLOUR,
                      active_colour: str = ACTIVE_ROI_COLOUR) -> 'LineROI':
        if name is None:
            name = self.name
        return LineROI(image,
                       self.x1,
                       self.y1,
                       self.x2,
                       self.y2,
                       slice_num=slice_num,
                       name=name,
                       replace=replace,
                       cache_values=cache_values,
                       colour=colour,
                       active_colour=active_colour)

    def _load_pixels(self):
        array: np.ndarray = self.image.array[self.slice_num]
        num_points = round(self.length) + 1
        if self.length == 0:
            x_frac = 1
            y_frac = 1
        else:
            x_frac = (self.x2 - self.x1) / self.length
            y_frac = (self.y2 - self.y1) / self.length
        if self.image.is_multisample:
            pixel_array = np.empty((1, num_points, array.shape[-1]))
        else:
            pixel_array = np.empty((1, num_points,))
        pixel_value_list: list[int | float | list[float]] = []
        for d in range(num_points):
            x = round(self.x1 + d * x_frac)
            y = round(self.y1 + d * y_frac)
            pixel_array[0, d] = array[y, x]
            pixel_value_list.append(array[y, x])

        if len(pixel_value_list) == 0:
            if self.image.is_rgb:
                self._pixel_values = [[0, 0, 0]]
            else:
                self._pixel_values = [0]
        else:
            self._pixel_values = pixel_value_list

        self._pixel_array = pixel_array

    @property
    def area(self) -> float:
        return self.length

    @property
    def perimeter(self) -> float:
        return 2 * self.length + 2

    @property
    def length(self) -> float:
        """
        The length of the line.
        """
        if self._length is None or not self.cache_values:
            self._length = math.sqrt((self.x1 - self.x2)**2 + (self.y1 - self.y2)**2)
        return self._length

    @property
    def profile(self) -> np.ndarray[tuple[int, int] | tuple[int, int, int], np.dtype]:
        """
        The profile of the line.
        """
        return self.pixel_array[0]

    @property
    def xmin(self) -> int:
        if self._xmin is None or not self.cache_values:
            self._xmin = min(self.x1, self.x2)
        return self._xmin

    @property
    def xmax(self) -> int:
        if self._xmax is None or not self.cache_values:
            self._xmax = max(self.x1, self.x2)
        return self._xmax

    @property
    def ymin(self) -> int:
        if self._ymin is None or not self.cache_values:
            self._ymin = min(self.y1, self.y2)
        return self._ymin

    @property
    def ymax(self) -> int:
        if self._ymax is None or not self.cache_values:
            self._ymax = max(self.y1, self.y2)
        return self._ymax

    @property
    def x_len(self) -> int:
        """
        Returns the length of the line in the x-direction.
        """
        return self.xmax - self.xmin

    @property
    def y_len(self) -> int:
        """
        Returns the length of the line in the y-direction.
        """
        return self.ymax - self.ymin

    @property
    def xcent(self) -> float:
        if self._xcent is None or not self.cache_values:
            self._xcent = (self.x1 + self.x2) / 2
        return self._xcent

    @property
    def ycent(self) -> float:
        if self._ycent is None or not self.cache_values:
            self._ycent = (self.y1 + self.y2) / 2
        return self._ycent

    @property
    def values_str(self) -> str:
        if isinstance(self.mean, tuple):
            mean_str = f"[{", ".join([f"{val:.1f}" for val in self.mean])}], "
        else:
            mean_str = f"{self.mean:.1f}, "

        if isinstance(self.std, tuple):
            std_str = f"[{", ".join([f"{val:.1f}" for val in self.std])}], "
        else:
            std_str = f"{self.std:.1f}, "

        return (f"Length: {self.length:.1f}, "
                + f"x: {self.x_len}, "
                + f"y: {self.y_len}, "
                + f"Mean: {mean_str}, "
                + f"Std: {std_str}")

    @property
    def menu_options(self) -> list[tuple[str, Callable[[], None]]]:
        options = super().menu_options
        options.extend([("Plot Profile", self.plot_profile)])
        return options

    def plot_profile(self):
        """
        Plots the profile of the ROI in a new window.
        """
        plt.clf()
        plt.plot(self.profile)
        try:
            name = str(self.image)
            plt.title(f"Profile for {name}")
        except NotImplementedError:
            plt.title("Profile")
        plt.xlabel("Position (Pixels)")
        plt.ylabel("Pixel Value")
        plt.show()
