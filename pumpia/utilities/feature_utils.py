"""
Functions:
 * ellipse_eq
 * ellipse_eq_min_max
 * phantom_boundary_automatic
 * phantom_boundbox_manual
 * rectangle_eq
 * rectangle_eq_min_max
 * single_feature_boundbox
 """

import numpy as np
from scipy.optimize import curve_fit
from pumpia.utilities.array_utils import nth_max_widest_peak, nth_max_bounds, MinMaxPix
from pumpia.utilities.typing import SideType

from pumpia.module_handling.context import BoundBoxContext, PhantomContext, PhantomShapes


def ellipse_eq(pos: np.ndarray,
               xc: float,
               yc: float,
               a: float,
               b: float) -> np.ndarray:
    """
    Ellipse equation.

    Parameters
    ----------
    pos : np.ndarray
        The positions array.
    xc : float
        The x-center of the ellipse.
    yc : float
        The y-center of the ellipse.
    a : float
        The width of the ellipse.
    b : float
        The height of the ellipse.

    Returns
    -------
    np.ndarray
        The result of the ellipse equation.
    """
    if pos.ndim != 2 or pos.shape[1] != 2:
        raise ValueError("Incorrect shape for position")
    return ((pos[:, 0] - xc) / a)**2 + ((pos[:, 1] - yc) / b)**2


def ellipse_eq_min_max(pos: np.ndarray,
                       xmin: float,
                       ymin: float,
                       xmax: float,
                       ymax: float) -> np.ndarray:
    """
    Ellipse equation using min and max values.

    Parameters
    ----------
    pos : np.ndarray
        The positions array.
    xmin : float
        The minimum x-coordinate.
    ymin : float
        The minimum y-coordinate.
    xmax : float
        The maximum x-coordinate.
    ymax : float
        The maximum y-coordinate.

    Returns
    -------
    np.ndarray
        The result of the ellipse equation.
    """
    if pos.ndim != 2 or pos.shape[1] != 2:
        raise ValueError("Incorrect shape for position")
    return (((2 * pos[:, 0] - (xmax + xmin)) / (xmax - xmin))**2
            + ((2 * pos[:, 1] - (ymax + ymin)) / (ymax - ymin))**2)


def rectangle_eq(pos: np.ndarray,
                 xmin: float,
                 ymin: float,
                 a: float,
                 b: float) -> np.ndarray:
    """
    Rectangle equation.

    Parameters
    ----------
    pos : np.ndarray
        The positions array.
    xmin : float
        The minimum x-coordinate.
    ymin : float
        The minimum y-coordinate.
    a : float
        The width of the rectangle.
    b : float
        The height of the rectangle.

    Returns
    -------
    np.ndarray
        The result of the rectangle equation.
    """
    if pos.ndim != 2 or pos.shape[1] != 2:
        raise ValueError("Incorrect shape for position")
    return (np.min([np.abs(xmin - pos[:, 0]), np.abs(xmin + a - pos[:, 0]),
            np.abs(ymin - pos[:, 1]), np.abs(ymin + b - pos[:, 1])], axis=0))


def rectangle_eq_min_max(pos: np.ndarray,
                         xmin: float,
                         ymin: float,
                         xmax: float,
                         ymax: float) -> np.ndarray:
    """
    Rectangle equation using min and max values.

    Parameters
    ----------
    pos : np.ndarray
        The positions array.
    xmin : float
        The minimum x-coordinate.
    ymin : float
        The minimum y-coordinate.
    xmax : float
        The maximum x-coordinate.
    ymax : float
        The maximum y-coordinate.

    Returns
    -------
    np.ndarray
        The result of the rectangle equation.
    """
    if pos.ndim != 2 or pos.shape[1] != 2:
        raise ValueError("Incorrect shape for position")
    return (np.min(np.array([np.abs(pos[:, 0] - xmin), np.abs(pos[:, 0] - xmax),
            np.abs(pos[:, 1] - ymin), np.abs(pos[:, 1] - ymax)]), axis=0))


def single_feature_boundbox(array: np.ndarray,
                            divisor: float = 2,
                            top_perc: float = 95) -> BoundBoxContext:
    """
    Finds the bounding box for an array with a single feature.

    Parameters
    ----------
    array : np.ndarray
        The input array. should be 2 dimensional
    divisor : float, optional
        The divisor to calculate the nth maximum value (default is 2).
    top_perc : float, optional
        The percentile to calculate the working maximum from, to exclude outliers (default is 95).

    Returns
    -------
    BoundBoxContext
        The bounding box context.
    """
    if array.ndim != 2:
        raise ValueError("array should be 2 dimensional")
    if 0 > top_perc or top_perc > 100:
        raise ValueError("top_perc must be between 0 and 100")
    max_val = np.percentile(array, top_perc)
    h_profile = np.max(array, axis=0)
    v_profile = np.max(array, axis=1)
    h_bounds: MinMaxPix = nth_max_widest_peak(h_profile, divisor, maximum=max_val)  # type:ignore
    v_bounds: MinMaxPix = nth_max_widest_peak(v_profile, divisor, maximum=max_val)  # type:ignore

    return BoundBoxContext(h_bounds.minimum,
                           h_bounds.maximum,
                           v_bounds.minimum,
                           v_bounds.maximum)


def phantom_boundbox_manual(array: np.ndarray,
                            sensitivity: float = 2,
                            top_perc: float = 95,
                            bubble_offset: int = 0,
                            bubble_side: SideType = "top") -> BoundBoxContext:
    """
    Finds the bounding box for a phantom with bubble info provided manually.

    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 2 dimensional
    sensitivity : float, optional
        The sensitivity for boundary detection.
        e.g. 2 would use half the maximum, 10 would use a tenth (default is 2).
    top_perc : float, optional
        The percentile to calculate the working maximum from, to exclude outliers (default is 95).
    bubble_offset : int, optional
        The bubble offset for boundary detection in pixels (default is 0).
    bubble_side : SideType, optional
        The side of the phantom the bubble is on (default is "top").

    Returns
    -------
    BoundBoxContext
        The bounding box context.
    """
    bbox = single_feature_boundbox(array, sensitivity, top_perc)
    if bubble_offset != 0:
        if bubble_side == "top":
            bbox.ymin -= bubble_offset
        elif bubble_side == "bottom":
            bbox.ymax += bubble_offset
        elif bubble_side == "left":
            bbox.xmin -= bubble_offset
        elif bubble_side == "right":
            bbox.xmax += bubble_offset
    return bbox


def phantom_boundary_automatic(array: np.ndarray,
                               sensitivity: float = 3,
                               top_perc: float = 95,
                               iterations: int = 2,
                               cull_perc: float = 80,
                               shape: PhantomShapes = None
                               ) -> PhantomContext:
    """
    Finds the boundary of a phantom automatically.

    This is done by finding the pixel positions of the boundary of the phantom,
    using the nth maximum method.
    The boundary is then fitted to an ellipse and a rectangle.
    The worst fitting positions are removed and the fitting is repeated.
    The best fitting shape after n iterations is returned.


    Parameters
    ----------
    array : np.ndarray
        The input array. Should be 2 dimensional
    sensitivity : float, optional
        The sensitivity for boundary detection.
        e.g. 2 would use half the maximum, 10 would use a tenth(default is 3).
    top_perc : float, optional
        The percentile to calculate the working maximum from, to exclude outliers (default is 95).
    iterations : int, optional
        The number of iterations in the algorithm (default is 2).
    cull_perc : float, optional
        The percentile to determine how many positions are kept each iteration (default is 80).
    shape : PhantomShapes, optional
        The shape of the phantom.
        Calculated if not given (default is None).

    Returns
    -------
    PhantomContext
        The phantom context.
    """
    if 0 >= top_perc or top_perc > 100:
        raise ValueError("top_perc must be between 0 and 100")
    if 0 >= cull_perc or cull_perc > 100:
        raise ValueError("cull_perc must be between 0 and 100")
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    if array.ndim != 2:
        raise ValueError("array should be 2 dimensional")

    max_val = float(np.percentile(array, top_perc))
    points: list[tuple[float, float]] = []

    for y in range(array.shape[0]):
        line = array[y, :]
        try:
            bounds = nth_max_bounds(line, sensitivity, maximum=max_val)
            points.append((bounds.minimum, y))
            points.append((bounds.maximum, y))
        except ValueError:
            pass

    for x in range(array.shape[1]):
        line = array[:, x]
        try:
            bounds = nth_max_bounds(line, sensitivity, maximum=max_val)
            points.append((x, bounds.minimum))
            points.append((x, bounds.maximum))
        except ValueError:
            pass

    val_bounds = ((0, 0, 0, 0), (array.shape[1], array.shape[0], array.shape[1], array.shape[0]))

    points_array: np.ndarray = np.array(points)

    if (shape is None
            or (isinstance(shape, list) and "ellipse" in shape)
            or shape == "ellipse"):
        ellipse: bool = True
    else:
        ellipse: bool = False

    if (shape is None
            or (isinstance(shape, list) and "rectangle" in shape)
            or shape == "rectangle"):
        rect: bool = True
    else:
        rect: bool = False

    if not (rect or ellipse):
        raise ValueError("Invalid Shape")

    if ellipse:
        ellipse_points_array = points_array.copy()
        ellipse_fit = (0, 0, array.shape[1], array.shape[0])
        # pylint: disable-next=unbalanced-tuple-unpacking
        ellipse_fit, ellipse_pcov = curve_fit(ellipse_eq_min_max,
                                              ellipse_points_array,
                                              np.ones((len(ellipse_points_array),)),
                                              ellipse_fit,
                                              bounds=val_bounds)

        for _ in range(iterations - 1):
            ellipse_diffs = np.square(ellipse_eq_min_max(ellipse_points_array, *ellipse_fit) - 1)
            ellipse_max_diff = np.percentile(ellipse_diffs, cull_perc)
            ellipse_diffs_mask = ellipse_diffs > ellipse_max_diff
            ellipse_points_array = np.delete(ellipse_points_array, ellipse_diffs_mask, axis=0)

            if len(ellipse_points_array) < len(ellipse_fit):
                break

            # pylint: disable-next=unbalanced-tuple-unpacking
            ellipse_fit, ellipse_pcov = curve_fit(ellipse_eq_min_max,
                                                  ellipse_points_array,
                                                  np.ones((len(ellipse_points_array),)),
                                                  ellipse_fit,
                                                  bounds=val_bounds)
        ellipse_error = np.diag(ellipse_pcov)
        ellipse_fit_error = np.sum(ellipse_error / np.square(ellipse_fit))

    if rect:
        rect_points_array = points_array.copy()
        rect_fit = (0, 0, array.shape[1], array.shape[0])
        # pylint: disable-next=unbalanced-tuple-unpacking
        rect_fit, rect_pcov = curve_fit(rectangle_eq_min_max,
                                        rect_points_array,
                                        np.zeros((len(rect_points_array),)),
                                        rect_fit,
                                        bounds=val_bounds)

        for _ in range(iterations - 1):
            rect_diffs = np.square(rectangle_eq_min_max(rect_points_array, *rect_fit) - 1)
            rect_max_diff = np.percentile(rect_diffs, cull_perc)
            rect_diffs_mask = rect_diffs > rect_max_diff
            rect_points_array = np.delete(rect_points_array, rect_diffs_mask, axis=0)

            if len(rect_points_array) < len(rect_fit):
                break

            # pylint: disable-next=unbalanced-tuple-unpacking
            rect_fit, rect_pcov = curve_fit(rectangle_eq_min_max,
                                            rect_points_array,
                                            np.zeros((len(rect_points_array),)),
                                            rect_fit,
                                            bounds=val_bounds)

        rect_error = np.diag(rect_pcov)
        rect_fit_error = np.sum(rect_error / np.square(rect_fit))

    if ellipse and rect:
        if rect_fit_error < ellipse_fit_error:  # type:ignore
            xmin = round(rect_fit[0])
            ymin = round(rect_fit[1])
            xmax = round(rect_fit[2])
            ymax = round(rect_fit[3])

            return PhantomContext(xmin, xmax, ymin, ymax, "rectangle")

        else:
            xmin = round(ellipse_fit[0])
            ymin = round(ellipse_fit[1])
            xmax = round(ellipse_fit[2])
            ymax = round(ellipse_fit[3])

            return PhantomContext(xmin, xmax, ymin, ymax, "ellipse")

    elif rect:
        xmin = round(rect_fit[0])
        ymin = round(rect_fit[1])
        xmax = round(rect_fit[2])
        ymax = round(rect_fit[3])

        return PhantomContext(xmin, xmax, ymin, ymax, "rectangle")

    else:
        xmin = round(ellipse_fit[0])
        ymin = round(ellipse_fit[1])
        xmax = round(ellipse_fit[2])
        ymax = round(ellipse_fit[3])

        return PhantomContext(xmin, xmax, ymin, ymax, "ellipse")
