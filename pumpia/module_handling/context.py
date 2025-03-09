"""
Classes:
 * BaseContext
 * BoundBoxContext
 * CentreContext
 * PhantomContext
 """

from typing import Literal

PhantomShape = Literal["rectangle", "ellipse"]
PhantomShapes = None | PhantomShape | list[PhantomShape]


class BaseContext:
    """
    Base class for context.
    """


class PhantomContext(BaseContext):
    """
    Context for phantom shapes.

    Parameters
    ----------
    xmin : int
        The minimum x-coordinate.
    xmax : int
        The maximum x-coordinate.
    ymin : int
        The minimum y-coordinate.
    ymax : int
        The maximum y-coordinate.
    shape : PhantomShape
        The shape of the phantom.
    """

    def __init__(self, xmin: int, xmax: int, ymin: int, ymax: int, shape: PhantomShape):
        self.xmin: int = xmin
        self.xmax: int = xmax
        self.ymin: int = ymin
        self.ymax: int = ymax
        self.shape: PhantomShape = shape

    @property
    def xcent(self) -> float:
        """
        The x co-ordinate of the center of the phantom.
        """
        return (self.xmax + self.xmin) / 2

    @property
    def ycent(self) -> float:
        """
        The y co-ordinate of the center of the phantom.
        """
        return (self.ymax + self.ymin) / 2

    @property
    def y_length(self) -> int:
        """
        Returns the y-length of the phantom.
        """
        return self.ymax - self.ymin

    @property
    def x_length(self) -> int:
        """
        Returns the x-length of the phantom.
        """
        return self.xmax - self.xmin


class BoundBoxContext(BaseContext):
    """
    Context for bounding box.

    Parameters
    ----------
    xmin : int
        The minimum x-coordinate.
    xmax : int
        The maximum x-coordinate.
    ymin : int
        The minimum y-coordinate.
    ymax : int
        The maximum y-coordinate.
    """

    def __init__(self, xmin: int, xmax: int, ymin: int, ymax: int):
        self.xmin: int = xmin
        self.xmax: int = xmax
        self.ymin: int = ymin
        self.ymax: int = ymax


class SimpleContext(BaseContext):
    """
    Context for center coordinates.

    Parameters
    ----------
    xcent : float
        The x-center coordinate.
    ycent : float
        The y-center coordinate.
    width : int
        The width of the image.
    height : int
        The height of the image.
    """

    def __init__(self, xcent: float, ycent: float, width: int, height: int) -> None:
        self.xcent: float = xcent
        self.ycent: float = ycent
        self.width: int = width
        self.height: int = height
