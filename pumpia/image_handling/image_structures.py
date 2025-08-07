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
import matplotlib.pyplot as plt

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
    num_samples: int
        Number of samples in the image, `>1` for colour images, e.g. RGB is 3 (default is 1).
    mode: str | None
        Mode of the image e.g. RGB (default is None)

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
    num_samples: int
        Number of samples in the image, >1 for colour images (e.g. RGB is 3)
    mode: str | None
        Mode of the image for viewing e.g. RGB (see Pillow modes for more)
    is_multisample : bool
    is_rgb : bool
    current_slice : int
    location : tuple[float, float]
    num_slices : int
    raw_array : np.ndarray
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
    add_roi(roi: 'BaseROI', replace: bool = True)
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
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, int, int],
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, int],
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, ...],
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        ...

    def __init__(self,
                 shape: tuple[int, ...],
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        self._current_slice: int = 0
        self._rois: set['BaseROI'] = set()
        self.x: float = 0
        self.y: float = 0
        self.zoom: float = 0
        self.rotation: float = 0
        self._user_window: float | None = None
        self._user_level: float | None = None
        self.num_samples: int = num_samples
        self.mode: str | None = mode

        if len(shape) == 4:
            self.shape: tuple[int, int, int] = shape[:-1]
            self.num_samples = shape[-1]
        elif len(shape) == 3 and not self.is_multisample:
            self.shape: tuple[int, int, int] = shape
        elif len(shape) == 3 and self.is_multisample:
            self.shape: tuple[int, int, int] = (1, shape[0], shape[1])
            self.num_samples = shape[-1]
        elif len(shape) == 2:
            self.shape: tuple[int, int, int] = (1, shape[0], shape[1])
        else:
            raise ValueError("wrong dimensions for array")

    @property
    def is_multisample(self) -> bool:
        """Whether the image is multisample.
        i.e. has more than one sample per pixel, such as RGB."""
        return self.num_samples > 1

    @property
    def is_colour(self) -> bool:
        """Whether the image is RGB."""
        return (not self.mode is None) and self.is_multisample

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
    def height(self) -> int:
        """
        The height of the image
        """
        return self.shape[1]

    @property
    def width(self) -> int:
        """
        The width of the image
        """
        return self.shape[2]

    @property
    @abstractmethod
    def raw_array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        """Returns the raw array of the image as stored in the file.
        This is usually an unsigned dtype so users should be careful when processing."""

    @property
    @abstractmethod
    def image_array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        """Returns the raw array of the image as stored in the file.
        This is usually an unsigned dtype so users should be careful when processing."""

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
        if not self.is_colour:
            return float(np.max(self.current_slice_array))
        else:
            return None

    @property
    def vmin(self) -> float | None:
        """
        The minimum value of the current slice, None if the image is multi-sample.
        """
        if not self.is_colour:
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

    def add_roi(self, roi: 'BaseROI', replace: bool = True):
        """
        Adds an ROI to the image.

        Parameters
        ----------
        roi : BaseROI
            The ROI to add.
        replace : bool, optional
            Whether to replace an existing ROI with the same name (default is True).
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

    def plot_z_profile(self):
        """
        Plots the z profile of the image in a new window.
        """
        plt.clf()
        plt.plot(self.z_profile, ".-")
        try:
            name = str(f"{self} z profile")
            plt.title(f"Vertical Profile for {name}")
        except NotImplementedError:
            plt.title("Vertical Profile")
        plt.xlabel("Position (Pixels)")
        plt.ylabel("Value")
        plt.show()

    @property
    def menu_options(self) -> list[tuple[str, Callable[[], None]]]:
        options = super().menu_options
        options.extend([("Plot z Profile", self.plot_z_profile)])
        return options


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
    num_samples: int
        Number of samples in the image (default is 1).
    mode: str | None
        Mode of the image e.g. RGB (default is None)

    Attributes
    ----------
    filepath : Path
        The file path of the image.
    """

    @overload
    def __init__(self,
                 shape: tuple[int, int, int, int],
                 filepath: Path,
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, int, int],
                 filepath: Path,
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        ...

    @overload
    def __init__(self,
                 shape: tuple[int, int],
                 filepath: Path,
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        ...

    def __init__(self,
                 shape: tuple[int, ...],
                 filepath: Path,
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        super().__init__(shape, num_samples, mode)
        self._filepath: Path = copy(filepath)

    def __str__(self) -> str:
        return str(self.filepath)

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
        return "FILE : " + str(self.filepath)


class ImageCollection(ArrayImage):
    """
    Represents a collection of ArrayImage objects.
    Has the same attributes and methods as ArrayImage unless stated below.

    Parameters
    ----------
    shape : tuple[int, ...]
        The shape of the image.
    num_samples: int
        Number of samples in the image (default is 1).
    mode: str | None
        Mode of the image e.g. RGB (default is None)

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
    def __init__(self, shape: tuple[int, int, int, int],
                 num_samples: int = 1,
                 mode: str | None = None
                 ) -> None:
        ...

    @overload
    def __init__(self, shape: tuple[int, int, int],
                 num_samples: int = 1,
                 mode: str | None = None) -> None:
        ...

    @overload
    def __init__(self, shape: tuple[int, int],
                 num_samples: int = 1,
                 mode: str | None = None) -> None:
        ...

    def __init__(self, shape: tuple[int, ...],
                 num_samples: int = 1,
                 mode: str | None = None) -> None:
        super().__init__(shape, num_samples, mode)
        self._image_set: set[ArrayImage] = set()

    @property
    def image_set(self) -> list[ArrayImage]:
        """
        The list of images in the collection.
        """
        return list(self._image_set)

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
        if not self.is_colour:
            return float(np.max(self.current_slice_array))
        else:
            return None

    @property
    def vmin(self) -> float | None:
        if not self.is_colour:
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
                and self.num_samples == image.num_samples
                and self.mode == image.mode)):
            self._image_set.add(image)
            self.shape = (len(self._image_set),
                          image.shape[1],
                          image.shape[2])
            self.num_samples = image.num_samples  # for if num_slices == 0
            self.mode = image.mode  # for if num_slices == 0
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

    def add_roi(self, roi: 'BaseROI', replace: bool = True):
        """
        Adds an ROI to the image collection.

        Parameters
        ----------
        roi : BaseROI
            The ROI to add.
        replace : bool, optional
            Whether to replace an existing ROI with the same name (default is True).
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
