"""
Functions:
 * half_max_bounds
 * half_max_positions
 * nth_max_bounds
 * nth_max_down_positions
 * nth_max_peaks
 * nth_max_positions
 * nth_max_troughs
 * nth_max_up_positions
 * nth_max_widest_peak
 * nth_max_widest_trough
 * tenth_max_bounds
 * tenth_max_positions

Classes:
 * MinMax
 * MinMaxPix
 * Pixel
 * Position
 * Vector
 """

from dataclasses import dataclass
from collections.abc import Iterable
from typing import Literal
import numpy as np


@dataclass
class Pixel:
    """
    Represents a pixel with x, y coordinates and a value.

    Attributes
    ----------
    x : int
        The x-coordinate of the pixel.
    y : int
        The y-coordinate of the pixel.
    value : int or float, optional
        The value of the pixel (default is 0).
    """
    x: int
    y: int
    value: int | float = 0


@dataclass
class Position:
    """
    Represents a position with x, y coordinates.

    Attributes
    ----------
    x : float
        The x-coordinate of the position.
    y : float
        The y-coordinate of the position.
    """
    x: float
    y: float

    @property
    def tuple(self) -> tuple[float, float]:
        """
        Returns the position as a tuple.
        """
        return (self.x, self.y)

    def __getitem__(self, item: Literal[0, 1, "x", "y"]):
        if item == 0 or item == "x":
            return self.x
        elif item == 1 or item == "y":
            return self.y
        raise IndexError("Incorrect indexing")


@dataclass
class Vector:
    """
    Represents a vector with start and end coordinates.

    Attributes
    ----------
    x1 : float
        The x-coordinate of the start point.
    x2 : float
        The x-coordinate of the end point.
    y1 : float
        The y-coordinate of the start point.
    y2 : float
        The y-coordinate of the end point.
    """
    x1: float
    x2: float
    y1: float
    y2: float


@dataclass
class MinMax:
    """
    Represents minimum and maximum values.

    Attributes
    ----------
    minimum : np.floating or float or int
        The minimum value.
    maximum : np.floating or float or int
        The maximum value.
    difference : np.floating or float or int
    """
    minimum: np.floating | float | int
    maximum: np.floating | float | int

    @property
    def difference(self) -> np.floating | float | int:
        """
        Returns the difference between the maximum and minimum values.
        """
        return self.maximum - self.minimum


@dataclass
class MinMaxPix:
    """
    Represents minimum and maximum pixel position.

    Attributes
    ----------
    minimum : int
        The minimum pixel position.
    maximum : int
        The maximum pixel position.
    """
    minimum: int
    maximum: int

    @property
    def difference(self) -> int:
        """
        Returns the difference between the maximum and minimum pixel position.
        """
        return self.maximum - self.minimum


def nth_max_positions(array: np.ndarray,
                      divisor: float,
                      minimum: float | np.floating | None = None,
                      maximum: float | np.floating | None = None):
    """
    Finds the positions in the array
    where the value is crossing the nth maximum value relative to the minimum.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    divisor : float
        The divisor to calculate the nth maximum value. e.g. 2 for half maximum.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    np.ndarray
        The positions in the array where the value is crossing the nth maximum value.
    """
    if array.ndim != 1:
        raise ValueError("array should be 1 dimensional")
    if minimum is None:
        minimum = np.min(array)
    if maximum is None:
        maximum = np.max(array)

    half_maximum = (maximum + minimum) / divisor
    gte_half_maximum = array >= half_maximum
    lt_half_maximum = array < half_maximum
    mask = ((lt_half_maximum & np.roll(gte_half_maximum, -1))
            | (lt_half_maximum & np.roll(gte_half_maximum, 1)))

    return mask.nonzero()[0]


def nth_max_up_positions(array: np.ndarray,
                         divisor: float,
                         minimum: float | np.floating | None = None,
                         maximum: float | np.floating | None = None):
    """
    Finds the positions in the array
    where the value is increasing and crosses the nth maximum value relative to the minimum.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    divisor : float
        The divisor to calculate the nth maximum value. e.g. 2 for half maximum.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    np.ndarray
        The positions in the array where the value is increasing and crosses the nth maximum value.
    """
    if array.ndim != 1:
        raise ValueError("array should be 1 dimensional")
    if minimum is None:
        minimum = np.min(array)
    if maximum is None:
        maximum = np.max(array)

    half_maximum = (maximum + minimum) / divisor
    gte_half_maximum = array >= half_maximum
    lt_half_maximum = array < half_maximum
    mask = lt_half_maximum & np.roll(gte_half_maximum, -1)

    return mask.nonzero()[0]


def nth_max_down_positions(array: np.ndarray,
                           divisor: float,
                           minimum: float | np.floating | None = None,
                           maximum: float | np.floating | None = None):
    """
    Finds the positions in the array
    where the value is decreasing and crosses the nth maximum value relative to the minimum.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    divisor : float
        The divisor to calculate the nth maximum value. e.g. 2 for half maximum.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    np.ndarray
        The positions in the array where the value is decreasing and crosses the nth maximum value.
    """
    if array.ndim != 1:
        raise ValueError("array should be 1 dimensional")
    if minimum is None:
        minimum = np.min(array)
    if maximum is None:
        maximum = np.max(array)

    half_maximum = (maximum + minimum) / divisor
    gte_half_maximum = array >= half_maximum
    lt_half_maximum = array < half_maximum
    mask = lt_half_maximum & np.roll(gte_half_maximum, 1)

    return mask.nonzero()[0]


def nth_max_bounds(array: np.ndarray,
                   divisor: float,
                   minimum: float | np.floating | None = None,
                   maximum: float | np.floating | None = None) -> MinMaxPix:
    """
    Finds the minimum and maximum pixel locations of the nth maximum value in the array.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    divisor : float
        The divisor to calculate the nth maximum value. e.g. 2 for half maximum.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    MinMaxPix
        The bounds of the nth maximum value in the array.
    """
    nm_positions = nth_max_positions(array, divisor, minimum, maximum)
    return MinMaxPix(min(nm_positions), max(nm_positions))


def nth_max_peaks(array: np.ndarray,
                  divisor: float,
                  minimum: float | np.floating | None = None,
                  maximum: float | np.floating | None = None) -> Iterable[MinMaxPix]:
    """
    Finds the nth maximum positions for peaks in the array.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    divisor : float
        The divisor to calculate the nth maximum value. e.g. 2 for half maximum.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    Iterable[MinMaxPix]
        The peaks of the nth maximum value in the array.
    """
    nm_ups = nth_max_up_positions(array, divisor, minimum, maximum)
    nm_downs = nth_max_down_positions(array, divisor, minimum, maximum)

    n_ups: int = np.size(nm_ups, 0)
    n_downs: int = np.size(nm_downs, 0)
    i_down: int = 0
    i_up: int = 0

    peaks: list[MinMaxPix] = []

    while i_up < n_ups and i_down < n_downs:
        while i_down < n_downs and nm_downs[i_down] < nm_ups[i_up]:
            i_down += 1
        while i_up + 1 < n_ups and nm_ups[i_up + 1] < nm_downs[i_down]:
            i_up += 1
        if nm_downs[i_down] > nm_ups[i_up]:
            peaks.append(MinMaxPix(nm_ups[i_up], nm_downs[i_down]))
        i_down += 1
        i_up += 1

    return peaks


def nth_max_widest_peak(array: np.ndarray,
                        divisor: float,
                        minimum: float | np.floating | None = None,
                        maximum: float | np.floating | None = None) -> MinMaxPix:
    """
    Finds the nth maximum positions for the widest peak in the array.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    divisor : float
        The divisor to calculate the nth maximum value. e.g. 2 for half maximum.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    MinMaxPix
        The widest peak of the nth maximum value in the array.
    """
    peaks = nth_max_peaks(array, divisor, minimum, maximum)
    bounds: MinMaxPix = max(peaks, key=lambda x: x.difference)  # type:ignore
    return bounds


def nth_max_troughs(array: np.ndarray,
                    divisor: float,
                    minimum: float | np.floating | None = None,
                    maximum: float | np.floating | None = None) -> Iterable[MinMaxPix]:
    """
    Finds the nth maximum positions for troughs in the array.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    divisor : float
        The divisor to calculate the nth maximum value. e.g. 2 for half maximum.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    Iterable[MinMaxPix]
        The troughs of the nth maximum value in the array.
    """
    nm_ups = nth_max_up_positions(array, divisor, minimum, maximum)
    nm_downs = nth_max_down_positions(array, divisor, minimum, maximum)

    n_ups: int = np.size(nm_ups, 0)
    n_downs: int = np.size(nm_downs, 0)
    i_down: int = 0
    i_up: int = 0

    troughs: list[MinMaxPix] = []

    while i_up < n_ups and i_down < n_downs:
        while i_up < n_ups and nm_ups[i_up] < nm_downs[i_down]:
            i_up += 1
        while i_down + 1 < n_downs and nm_downs[i_down + 1] < nm_ups[i_up]:
            i_down += 1

        if nm_ups[i_up] > nm_downs[i_down]:
            troughs.append(MinMaxPix(nm_ups[i_up], nm_downs[i_down]))
        i_down += 1
        i_up += 1

    return troughs


def nth_max_widest_trough(array: np.ndarray,
                          divisor: float,
                          minimum: float | np.floating | None = None,
                          maximum: float | np.floating | None = None) -> MinMaxPix:
    """
    Finds the nth maximum positions for the widest trough in the array.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    divisor : float
        The divisor to calculate the nth maximum value. e.g. 2 for half maximum.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    MinMaxPix
        The widest trough of the nth maximum value in the array.
    """
    troughs = nth_max_troughs(array, divisor, minimum, maximum)
    bounds: MinMaxPix = max(troughs, key=lambda x: x.difference)  # type:ignore
    return bounds


def half_max_positions(array: np.ndarray,
                       minimum: float | np.floating | None = None,
                       maximum: float | np.floating | None = None):
    """
    Finds the positions in the array
    where the value is crossing the half maximum value relative to the minimum.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    np.ndarray
        The positions in the array where the value crosses the half maximum value.
    """
    return nth_max_positions(array, 2, minimum, maximum)


def half_max_bounds(array: np.ndarray,
                    minimum: float | np.floating | None = None,
                    maximum: float | np.floating | None = None) -> MinMaxPix:
    """
    Finds the minimum and maximum of half the maximum value in the array.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    MinMaxPix
        The bounds of half the maximum value in the array.
    """
    return nth_max_bounds(array, 2, minimum, maximum)


def tenth_max_positions(array: np.ndarray,
                        minimum: float | np.floating | None = None,
                        maximum: float | np.floating | None = None):
    """
    Finds the positions in the array
    where the value is crossing the tenth maximum value relative to the minimum.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    np.ndarray
        The positions in the array where the value crosses the one-tenth maximum value.
    """
    return nth_max_positions(array, 10, minimum, maximum)


def tenth_max_bounds(array: np.ndarray,
                     minimum: float | np.floating | None = None,
                     maximum: float | np.floating | None = None) -> MinMaxPix:
    """
    Finds the maximum and minimum position of one-tenth the maximum value in the array.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 1 dimensional.
    minimum : float or np.floating or None, optional
        An override for the minimum to use.
        If None, the minimum value of the array is calculated.(default is None)
    maximum : float or np.floating or None, optional
        An override for the maximum to use.
        If None, the maximum value of the array is calculated.(default is None)

    Returns
    -------
    MinMaxPix
        The bounds of one-tenth the maximum value in the array.
    """
    return nth_max_bounds(array, 10, minimum, maximum)
