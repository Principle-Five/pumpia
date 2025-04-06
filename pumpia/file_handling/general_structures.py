"""
Classes:
 * GeneralImage
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageSequence
from pumpia.image_handling.image_structures import FileImageSet


class GeneralImage(FileImageSet):
    """
    Represents an image from a file.
    Has the same attributes and methods as FileImageSet unless stated below.

    Parameters
    ----------
    image : PIL.Image.Image
        The PIL image.
    path : Path
        The path to the image.

    Attributes
    ----------
    raw_array : np.ndarray
    """

    def __init__(self, image: Image.Image, path: Path):
        self._array: np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype] = (
            np.array([np.array(frame) for frame in ImageSequence.Iterator(image)]))  # type: ignore
        self.format = image.format
        super().__init__(self._array.shape, path, mode=image.mode)

    def __hash__(self) -> int:
        # from docs: A class that overrides __eq__() and does not define __hash__()
        # will have its __hash__() implicitly set to None.
        return super().__hash__()

    def __eq__(self, value: object) -> bool:
        if isinstance(value, GeneralImage):
            return hash(self) == hash(value)
        elif isinstance(value, int):
            return hash(self) == value
        elif isinstance(value, str):
            return self.id_string == value
        else:
            return False

    @property
    def raw_array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        """Returns the raw array of the series as stored in the file.
        This is usually an unsigned dtype so users should be careful when processing."""
        return self._array

    @property
    def array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        return np.astype(self._array, float)

    @property
    def id_string(self) -> str:
        return "GENERAL : " + str(self.filepath)
