"""
Functions:
 * not_rgb
"""

from typing import TypeGuard
from pumpia.image_handling.image_structures import BaseImageSet, ArrayImage


def not_rgb(image: BaseImageSet) -> TypeGuard[ArrayImage]:
    """
    Checks if the image is not an RGB image.

    Parameters
    ----------
    image : BaseImageSet
        The image to check.

    Returns
    -------
    bool
        True if the image is not an RGB image, False otherwise.
    """
    return isinstance(image, ArrayImage) and not image.is_rgb
