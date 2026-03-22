"""
Contains inputs/outputs representing viewers
"""

from collections.abc import Callable
from abc import ABC, abstractmethod
from typing import Self, overload, TYPE_CHECKING
from pumpia.widgets.viewers import (BaseViewer,
                                    Viewer,
                                    ArrayViewer,
                                    MonochromeViewer,
                                    DicomViewer,
                                    MonochromeDicomViewer)

from pumpia.image_handling.image_structures import BaseImageSet

if TYPE_CHECKING:
    from pumpia.module_handling.modules import BaseModule
    from pumpia.module_handling.module_collections import BaseCollection


class _Viewers:
    def __init__(self, obj: BaseCollection | BaseModule) -> None:
        self.obj: BaseCollection | BaseModule = obj
        self.viewers: dict[str, BaseViewer] = {}

    def __iter__(self):
        for viewer in self.viewers.values():
            yield viewer


class _ViewerFieldsMeta:
    def __init__(self) -> None:
        self.viewer_fields: dict[str, BaseViewerField] = {}
        self.name: str = ""
        self.private_name: str = "_"
        self.base_owner: type[BaseCollection | BaseModule] | None = None

    @property
    def viewer_names(self) -> list[str]:
        return list(self.viewer_fields.keys())

    def __set_name__(self, owner: type[BaseCollection | BaseModule], name: str):
        self.name = name
        self.private_name = "_" + name
        self.base_owner = owner

    @overload
    def __get__(self, obj: BaseCollection | BaseModule, owner: type[BaseCollection | BaseModule]) -> _Viewers: ...
    @overload
    def __get__(self, obj: None, owner: type[BaseCollection | BaseModule]) -> Self: ...

    def __get__(self, obj: BaseCollection | BaseModule | None, owner: type[BaseCollection | BaseModule]) -> _Viewers | Self:
        if obj is None:
            if owner is self.base_owner:
                return self
            else:
                meta_obj = type(self)()
                meta_obj.name = self.name
                meta_obj.private_name = self.private_name
                meta_obj.base_owner = owner
                setattr(owner, self.name, meta_obj)
                return meta_obj

        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            viewers = _Viewers(obj)
            setattr(obj, self.private_name, viewers)
            return viewers


class BaseViewerField[ViewerT:BaseViewer](ABC):
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
        owner.viewers.viewer_fields[name] = self

    @overload
    def __get__(self, obj: BaseCollection | BaseModule, owner=None) -> ViewerT: ...
    @overload
    def __get__(self, obj: None, owner=None) -> Self: ...

    def __get__(self, obj: BaseCollection | BaseModule | None, owner=None) -> ViewerT | Self:
        if obj is None:
            return self

        try:
            return obj.viewers.viewers[self.name]  # pyright: ignore[reportReturnType]
        except KeyError as exc:
            if obj.manager is None:
                raise ValueError("object manager needs to be set") from exc
            viewer = self.viewer_type(tk_parent=obj.viewer_frame,
                                      manager=obj.manager,
                                      allow_drag_drop=self.allow_drag_drop,
                                      allow_drawing_rois=self.allow_drawing_rois,
                                      allow_changing_rois=self.allow_changing_rois,
                                      validation_command=self.validation_command)
            obj.viewers.viewers[self.name] = viewer
            return viewer
        except AttributeError:
            return self

    @property
    @abstractmethod
    def viewer_type(self) -> type[ViewerT]:
        pass


class ViewerField(BaseViewerField[Viewer]):
    """
    Represents a viewer input / output.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    @property
    def viewer_type(self):
        return Viewer


class ArrayViewerField(BaseViewerField[ArrayViewer]):
    """
    Represents an array viewer input / output.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    @property
    def viewer_type(self):
        return ArrayViewer


class MonochromeViewerField(BaseViewerField[MonochromeViewer]):
    """
    Represents a monochrome viewer input / output.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    @property
    def viewer_type(self):
        return MonochromeViewer


class DicomViewerField(BaseViewerField[DicomViewer]):
    """
    Represents a DICOM viewer input / output.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    @property
    def viewer_type(self):
        return DicomViewer


class MonochromeDicomViewerField(BaseViewerField[MonochromeDicomViewer]):
    """
    Represents a DICOM viewer input / output for monochrome images.
    Has the same attributes and methods as BaseViewerField unless stated below.
    """
    @property
    def viewer_type(self):
        return MonochromeDicomViewer
