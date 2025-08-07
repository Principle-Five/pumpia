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
    pil_image : PIL.Image.Image
    raw_array : np.ndarray
    """

    def __init__(self, image: Image.Image, path: Path):
        self.pil_image: Image.Image = image

        self.format = image.format
        n_frames = getattr(image, "n_frames", 1)
        if image.mode[0] == "P":
            n_bands = 3  # assume pallets are 'RGB'
        else:
            n_bands = len(image.getbands())
        super().__init__((n_frames, image.height, image.width, n_bands), path, mode=image.mode)

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
        """Returns the raw array of the image as stored in the file.
        This is usually an unsigned dtype so users should be careful when processing."""
        frame_list = [np.array(frame) for frame in ImageSequence.Iterator(self.pil_image)]

        try:
            array: np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype] = (
                np.array(frame_list))  # type: ignore
        except ValueError as exc:
            if self.pil_image.format == "GIF":
                array: np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype] = (
                    np.array(frame_list[1:]))  # type: ignore
            else:
                raise exc

        return array

    @property
    def image_array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        """Returns an array suitable for passing to the viewer"""
        return self.raw_array

    @property
    def array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        frame_list = [np.array(frame) for frame in ImageSequence.Iterator(self.pil_image)]

        try:
            array: np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype] = (
                np.array(frame_list, float))  # type: ignore
        except ValueError as exc:
            if self.pil_image.format == "GIF":
                array: np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype] = (
                    np.array(frame_list[1:], float))  # type: ignore
            else:
                raise exc

        return array

    # current_slice_array could be optimised here, but need to be careful with GIFs

    @property
    def id_string(self) -> str:
        return "GENERAL : " + str(self.filepath)
