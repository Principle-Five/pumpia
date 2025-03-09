"""
Classes:
 * ArrayImage
 * BaseImageSet
 * FileImageSet
 * ImageCollection
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from copy import copy
from typing import TYPE_CHECKING, overload, Literal
import numpy as np

if TYPE_CHECKING:
    from pumpia.image_handling.roi_structures import BaseROI


class BaseImageSet(ABC):
    """
    Abstract base class for images that can be shown.

    Attributes
    ----------
    tag : str
    id_string : str
    menu_options : list[tuple[str, Callable[[], None]]]
    """

    def __hash__(self) -> int:
        return hash(self.id_string)

    @property
    @abstractmethod
    def tag(self) -> str:
        """
        The tag of the image set for use in the manager trees.
        """

    @property
    @abstractmethod
    def id_string(self) -> str:
        """
        The ID string of the image set.
        """

    @property
    def menu_options(self) -> list[tuple[str, Callable[[], None]]]:
        """
        Returns the menu options for the ROI.

        Returns
        -------
        list of tuple
            The menu options for the ROI in the form `(string to show in menu, function to call)`.
        """
        return []


class ArrayImage(BaseImageSet):
    """
    Represents an image based on an array.
    Has the same attributes and methods as BaseImageSet unless stated below.

    Parameters
    ----------
    shape : tuple[int, ...]
        The shape of the image.
    is_multisample : bool
        Whether the image is multisample. i.e. has more than one sample per pixel, such as RGB.
    is_rgb : bool
        Whether the image is RGB.

    Attributes
    ----------
    x : float
        The x location of the image on a Viewer.
    y : float
        The y location of the image on a Viewer.
    zoom : float
        The zoom level of the image on a Viewer.
    rotation : float
        The rotation of the image on a Viewer.
    shape : tuple[int, ...]
        The shape of the image.
    is_multisample : bool
        Whether the image is multisample. i.e. has more than one sample per pixel, such as RGB.
    is_rgb : bool
        Whether the image is RGB.
    current_slice : int
    location : tuple[float, float]
    num_slices : int
    array : np.ndarray
    current_slice_array : np.ndarray
    vmax : float | None
    vmin : float | None
    window : float | None
    level : float | None
    rois : set['BaseROI']
    roi_names : list[str]
    user_window : float | None
    user_level : float | None
    pixel_size : tuple[float, float, float]
    aspect : float
    z_profile : np.ndarray

    Methods
    -------
    get_rois(slice_num: int | Literal["All"] | None = None) -> set['BaseROI']
        Returns the set of ROIs in the image.
    add_roi(roi: 'BaseROI', replace: bool = False)
        Adds an ROI to the image.
    remove_roi(roi: 'BaseROI')
        Removes an ROI from the image.
    change_slice(amount: int = 1) -> None
        Changes the current slice by the given amount.
    reset()
        Resets the image properties to their default values.
    """

    @overload
    def __init__(self,
                 shape: tuple[int, int, int, int],
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, int, int],
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, int],
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, ...],
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        ...

    def __init__(self,
                 shape: tuple[int, ...],
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        self._current_slice: int = 0
        self._rois: set['BaseROI'] = set()
        self.x: float = 0
        self.y: float = 0
        self.zoom: float = 0
        self.rotation: float = 0
        self._user_window: float | None = None
        self._user_level: float | None = None
        self.is_multisample: bool = False

        if len(shape) == 4:
            self.shape: tuple[int, int, int] = shape[:-1]
            self.is_multisample = is_multisample
            self.is_rgb = is_rgb
        elif len(shape) == 3 and not is_multisample:
            self.shape: tuple[int, int, int] = shape
            self.is_multisample = False
            self.is_rgb = False
        elif len(shape) == 3 and is_multisample:
            self.shape: tuple[int, int, int] = (1, shape[0], shape[1])
            self.is_multisample = True
            self.is_rgb = is_rgb
        elif len(shape) == 2:
            self.shape: tuple[int, int, int] = (1, shape[0], shape[1])
            self.is_multisample = False
            self.is_rgb = False
        else:
            raise ValueError("wrong dimensions for array")

    @property
    def current_slice(self) -> int:
        """
        The current slice number.
        """
        return self._current_slice

    @current_slice.setter
    def current_slice(self, value: int):
        self._current_slice = value % self.num_slices

    @property
    def location(self) -> tuple[float, float]:
        """
        The location of the image on a Viewer.
        """
        return (self.x, self.y)

    @property
    def num_slices(self) -> int:
        """
        The number of slices in the image.
        """
        return self.shape[0]

    @property
    @abstractmethod
    def array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        """
        The array representation of the image.
        Accessed through (slice, y-position, x-position[, multisample/RGB values])
        """

    @property
    def current_slice_array(self) -> np.ndarray[tuple[int, int, int] | tuple[int, int], np.dtype]:
        """
        The array representation of the current slice.
        """
        return self.array[self.current_slice]

    @property
    def vmax(self) -> float | None:
        """
        The maximum value of the current slice, None if the image is multi-sample.
        """
        if not self.is_multisample:
            return float(np.max(self.current_slice_array))
        else:
            return None

    @property
    def vmin(self) -> float | None:
        """
        The minimum value of the current slice, None if the image is multi-sample.
        """
        if not self.is_multisample:
            return float(np.min(self.current_slice_array))
        else:
            return None

    @property
    def window(self) -> float | None:
        """
        The default window width of the current slice or None if the image is multi-sample.
        Calculated as the difference between the maximum and minimum values.
        """
        if (self.vmin is not None
                and self.vmax is not None):
            return self.vmax - self.vmin
        else:
            return None

    @property
    def level(self) -> float | None:
        """
        The default level value of the current slice or None if the image is multi-sample.
        Calculated as the average of the maximum and minimum values.
        """
        if (self.vmin is not None
                and self.vmax is not None):
            return (self.vmax + self.vmin) / 2
        else:
            return None

    @property
    def rois(self) -> set['BaseROI']:
        """
        The set of ROIs in the image.
        """
        return self.get_rois("All")

    @property
    def roi_names(self) -> list[str]:
        """
        The list of ROI names in the image.
        """
        return [roi.name for roi in self.rois]

    def __getitem__(self, roi_name: str) -> 'BaseROI':
        """
        Returns the ROI with the given name.

        Parameters
        ----------
        roi_name : str
            The name of the ROI.

        Returns
        -------
        BaseROI
            The ROI with the given name.

        Raises
        ------
        KeyError
            If the ROI is not found.
        """
        for roi in self.get_rois():
            if roi.name == roi_name:
                return roi
        raise KeyError("ROI not found")

    def get_rois(self, slice_num: int | Literal["All"] | None = None) -> set['BaseROI']:
        """
        Returns the set of ROIs in the image.

        Parameters
        ----------
        slice_num : int or Literal["All"] or None, optional
            The slice number to get the ROIs for,
            or "All" to get all ROIs,
            or None to get the ROIs for the current slice.
        """
        if slice_num == "All":
            return self._rois
        elif slice_num is None:
            slice_num = self.current_slice
        roi_set: set[BaseROI] = set()
        for roi in self._rois:
            if roi.slice_num == slice_num:
                roi_set.add(roi)
        return roi_set

    def add_roi(self, roi: 'BaseROI', replace: bool = False):
        """
        Adds an ROI to the image.

        Parameters
        ----------
        roi : BaseROI
            The ROI to add.
        replace : bool, optional
            Whether to replace an existing ROI with the same name (default is False).
        """
        if roi in self.get_rois() and replace:
            self.remove_roi(roi)
            self._rois.add(roi)
        elif roi not in self.get_rois():
            self._rois.add(roi)

    def remove_roi(self, roi: 'BaseROI'):
        """
        Removes an ROI from the image.

        Parameters
        ----------
        roi : BaseROI
            The ROI to remove.
        """
        self._rois.remove(roi)

    @property
    def user_window(self) -> float | None:
        """
        The user-defined window width value.
        """
        if self._user_window is None:
            return self.window
        else:
            return self._user_window

    @user_window.setter
    def user_window(self, value: float):
        if value < 1:
            self._user_window = 1
        else:
            self._user_window = value

    @property
    def user_level(self) -> float | None:
        """
        The user-defined level value.
        """
        if self._user_level is None:
            return self.level
        else:
            return self._user_level

    @user_level.setter
    def user_level(self, value: float):
        self._user_level = value

    @property
    def pixel_size(self) -> tuple[float, float, float]:
        """
        The pixel size of the image (slice_thickness, row_spacing, column_spacing)
        """
        return (1.0, 1.0, 1.0)

    @property
    def aspect(self) -> float:
        """
        The aspect ratio of the image.
        """
        return self.pixel_size[2] / self.pixel_size[1]

    @property
    def z_profile(self) -> np.ndarray[tuple[int], np.dtype]:
        """
        The Z profile of the image.
        """
        return np.sum(self.array, axis=(1, 2))

    def change_slice(self, amount: int = 1) -> None:
        """
        Changes the current slice by the given amount.
        """
        self._current_slice = (self.current_slice + amount) % self.num_slices

    def reset(self):
        """
        Resets the image properties to their default values.
        """
        self.x = 0
        self.y = 0
        self.zoom = 0
        self.rotation = 0
        self._user_window = None
        self._user_level = None


class FileImageSet(ArrayImage):
    """
    Represents an ArrayImage built from a file.
    Has the same attributes and methods as ArrayImage unless stated below.

    Parameters
    ----------
    shape : tuple[int, ...]
        The shape of the image.
    filepath : Path
        The file path of the image.
    is_multisample : bool
        Whether the image is multisample.
    is_rgb : bool
        Whether the image is RGB.

    Attributes
    ----------
    filepath : Path
        The file path of the image.
    """

    @overload
    def __init__(self,
                 shape: tuple[int, int, int, int],
                 filepath: Path,
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, int, int],
                 filepath: Path,
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, int],
                 filepath: Path,
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        ...

    def __init__(self,
                 shape: tuple[int, ...],
                 filepath: Path,
                 is_multisample: bool,
                 is_rgb: bool
                 ) -> None:
        super().__init__(shape, is_multisample, is_rgb)
        self._filepath: Path = copy(filepath)

    @property
    def tag(self) -> str:
        return "FI" + self.id_string

    @property
    def filepath(self) -> Path:
        """
        The file path of the image.
        """
        return self._filepath

    @property
    def id_string(self) -> str:
        return str(self.filepath)


class ImageCollection(ArrayImage):
    """
    Represents a collection of ArrayImage objects.
    Has the same attributes and methods as ArrayImage unless stated below.

    Parameters
    ----------
    shape : tuple[int, ...]
        The shape of the image.
    is_multisample : bool
        Whether the image is multisample.
    is_rgb : bool
        Whether the image is RGB.

    Attributes
    ----------
    image_set : list[ArrayImage]
        The list of images in the collection.
    current_image : ArrayImage
        The current image object.

    Methods
    -------
    add_image(image: ArrayImage)
        Adds an image to the collection.
    """

    @overload
    def __init__(self, shape: tuple[int, int, int, int], is_multisample: bool, is_rgb: bool
                 ) -> None:
        ...

    @overload
    def __init__(self, shape: tuple[int, int, int], is_multisample: bool, is_rgb: bool) -> None:
        ...

    @overload
    def __init__(self, shape: tuple[int, int], is_multisample: bool, is_rgb: bool) -> None:
        ...

    def __init__(self, shape: tuple[int, ...], is_multisample: bool, is_rgb: bool) -> None:
        super().__init__(shape, is_multisample, is_rgb)
        self._image_set: list[ArrayImage] = []

    @property
    def image_set(self) -> list[ArrayImage]:
        """
        The list of images in the collection.
        """
        return self._image_set

    @property
    def array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        return np.array([a.array[0] for a in self.image_set], dtype=float)  # type: ignore

    @property
    def current_slice_array(self) -> np.ndarray:
        """
        The `array` of the current image.
        """
        return self.image_set[self.current_slice].current_slice_array

    @property
    def current_image(self) -> ArrayImage:
        """
        The current image object.
        """
        return self.image_set[self.current_slice]

    @property
    def vmax(self) -> float | None:
        if not self.is_rgb:
            return float(np.max(self.current_slice_array))
        else:
            return None

    @property
    def vmin(self) -> float | None:
        if not self.is_rgb:
            return float(np.min(self.current_slice_array))
        else:
            return None

    @property
    def window(self) -> float | None:
        if (self.vmin is not None
                and self.vmax is not None):
            return self.vmax - self.vmin
        else:
            return None

    @property
    def level(self) -> float | None:
        if (self.vmin is not None
                and self.vmax is not None):
            return (self.vmax + self.vmin) / 2
        else:
            return None

    @property
    def user_window(self) -> float | None:
        if self._user_window is None:
            return self.window
        else:
            return self._user_window

    @user_window.setter
    def user_window(self, value: float):
        if value < 1:
            self._user_window = 1
            for i in self.image_set:
                i.user_window = 1
        else:
            self._user_window = value
            for i in self.image_set:
                i.user_window = value

    @property
    def user_level(self) -> float | None:
        if self._user_level is None:
            return self.level
        else:
            return self._user_level

    @user_level.setter
    def user_level(self, value: float):
        self._user_level = value
        for i in self.image_set:
            i.user_level = value

    @property
    def pixel_size(self) -> tuple[float, float, float]:
        return self.image_set[self.current_slice].pixel_size

    @property
    def aspect(self) -> float:
        return self.image_set[self.current_slice].aspect

    def add_image(self, image: ArrayImage):
        """
        Adds an image to the collection.

        Parameters
        ----------
        image : ArrayImage
            The image to add.

        Raises
        ------
        ValueError
            If the image is incompatible with the collection.
        """
        if (self.num_slices == 0
            or (self.shape[1] == image.shape[1]
                and self.shape[2] == image.shape[2]
                and self.is_rgb == image.is_rgb
                and self.is_multisample == image.is_multisample)):
            self._image_set.append(image)
            self.shape = (len(self._image_set),
                          image.shape[1],
                          image.shape[2])
            self.is_multisample = image.is_multisample  # for if num_slices == 0
            self.is_rgb = image.is_rgb  # for if num_slices == 0
        else:
            raise ValueError("Image incompatible with Collection")

    def get_rois(self, slice_num: int | Literal["All"] | None = None) -> set['BaseROI']:
        """
        Returns the set of ROIs in the image collection.

        Parameters
        ----------
        slice_num : int or Literal["All"] or None, optional
            The slice number to get the ROIs for,
            or "All" to get all ROIs,
            or None to get the ROIs for the current slice.
        """
        if slice_num is None:
            return self.image_set[self.current_slice].get_rois()
        elif slice_num == "All":
            roi_set: set[BaseROI] = set()
            for image in self.image_set:
                for roi in image.rois:
                    roi_set.add(roi)
            return roi_set
        else:
            return self.image_set[slice_num].get_rois()

    def add_roi(self, roi: 'BaseROI', replace: bool = False):
        """
        Adds an ROI to the image collection.

        Parameters
        ----------
        roi : BaseROI
            The ROI to add.
        replace : bool, optional
            Whether to replace an existing ROI with the same name (default is False).
        """
        roi.image = self.image_set[roi.slice_num]
        roi.slice_num = self.image_set[roi.slice_num].current_slice
        if roi in roi.image.get_rois() and replace:
            roi.image.remove_roi(roi)
            roi.image.add_roi(roi)
        elif roi not in roi.image.get_rois():
            roi.image.add_roi(roi)

    def remove_roi(self, roi: 'BaseROI'):
        """
        Removes an ROI from the image collection.
        """
        self.image_set[roi.slice_num].remove_roi(roi)
