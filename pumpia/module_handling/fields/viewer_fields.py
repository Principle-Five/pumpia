"""
Contains inputs/outputs representing viewers
"""

from collections.abc import Callable
from pumpia.widgets.viewers import (BaseViewer,
                                    Viewer,
                                    ArrayViewer,
                                    MonochromeViewer,
                                    DicomViewer,
                                    MonochromeDicomViewer)

from pumpia.image_handling.image_structures import BaseImageSet
from pumpia.module_handling.modules import BaseModule
from pumpia.module_handling.module_collections import BaseCollection


class _ViewerFieldsMeta:
    def __init__(self) -> None:
        self.fields: dict[str, BaseViewerField] = {}
        self.name: str = ""
        self.private_name: str = "_"

    @property
    def viewer_names(self) -> list[str]:
        return list(self.fields.keys())


class BaseViewerField():
    """
    Base class for viewer input / output handling.

    Parameters
    ----------
    row: int
        The row position of the viewer.
    column: int
        The column position of the viewer.
    allow_drag_drop: bool, optional
        Whether to allow drag and drop(default is True).
    allow_drawing_rois: bool, optional
        Whether to allow drawing ROIs(default is True).
    validation_command: Callable[[BaseImageSet], bool], optional
        The validation command(default is None).
    main: bool, optional
        Whether the viewer is the main viewer(default is False).

    Attributes
    ----------
    row: int
    column: int
    allow_drag_drop: bool
    allow_drawing_rois: bool
    validation_command: Callable[[BaseImageSet], bool] | None
    main: bool
    """
    viewer_type: type[BaseViewer]

    # pylint: disable-next=super-init-not-called
    def __init__(self,
                 row: int,
                 column: int,
                 *,
                 allow_drag_drop: bool = True,
                 allow_drawing_rois: bool = True,
                 allow_changing_rois: bool = True,
                 validation_command: Callable[[BaseImageSet], bool] | None = None,
                 main: bool = False):
        self.row: int = row
        self.column: int = column
        self.allow_drag_drop: bool = allow_drag_drop
        self.allow_drawing_rois: bool = allow_drawing_rois
        self.allow_changing_rois: bool = allow_changing_rois
        self.validation_command: Callable[[BaseImageSet], bool] | None = validation_command
        self.main = main
        self.name: str = ""

    def __set_name__(self, owner: type[BaseCollection | BaseModule], name: str):
        self.name = name
        owner.viewer_fields.fields[name] = self


class ViewerField(BaseViewerField, Viewer):
    """
    Represents a viewer input / output.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    viewer_type: type[Viewer] = Viewer


class ArrayViewerField(BaseViewerField, ArrayViewer):
    """
    Represents an array viewer input / output.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    viewer_type: type[ArrayViewer] = ArrayViewer


class MonochromeViewerField(BaseViewerField, MonochromeViewer):
    """
    Represents a monochrome viewer input / output.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    viewer_type: type[MonochromeViewer] = MonochromeViewer


class DicomViewerField(BaseViewerField, DicomViewer):
    """
    Represents a DICOM viewer input / output.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    viewer_type: type[DicomViewer] = DicomViewer


class MonochromeDicomViewerField(BaseViewerField, DicomViewer):
    """
    Represents a DICOM viewer input / output for monochrome images.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    viewer_type: type[MonochromeDicomViewer] = MonochromeDicomViewer
