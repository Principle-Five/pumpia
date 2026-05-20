"""
Base classes and functions for DICOM handling.
"""
import dataclasses as dc
from dataclasses import dataclass
from typing import overload, Literal, Any
import pydicom


@dataclass()
class Tag:
    """
    dataclass representing a dicom tag

    Parameters
    ----------
    name : str
        the name of the tag as defined in the dicom standards.
    keyword : str
        the keyword of the tag as defined in the dicom standards.
    group : int
        the group of the dicom tag
    element : int
        the element of the dicom tag
    links : list[TagLink]
        a list of TagLinks that hold any sequences the tag may be part of.
    alternative_tags : list[tuple[int, int]]
        a list of alternative tuples that could represent this tag

    Attributes
    ----------
    name : str
    keyword : str
    group : int
    element : int
    links : list[TagLink]
    alternative_tags : list[tuple[int, int]]
    as_tuple : tuple[int, int]
        This tag as a tuple of (group, element).

    Methods
    -------
    get() -> tuple[int, int]
        return the dicom tag as a tuple of (group, element).
    """
    name: str
    keyword: str
    group: int
    element: int
    links: list['TagLink'] = dc.field(default_factory=list)
    alternative_tags: list[tuple[int, int]] = dc.field(default_factory=list)

    @property
    def as_tuple(self) -> tuple[int, int]:
        """
        This tag as a tuple of (group, element).
        """
        return (self.group, self.element)

    def __int__(self) -> int:
        return (self.group << 16) | self.element

    def __eq__(self, value) -> bool:
        if isinstance(value, Tag):
            return self.as_tuple == value.as_tuple
        elif isinstance(value, tuple):
            return self.as_tuple == value
        elif isinstance(value, int):
            return int(self) == value
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.as_tuple)

    def __str__(self) -> str:
        return f"({self.group:04X}, {self.element:04X})"


@dataclass
class TagLink:
    """
    Class to hold links between tags and sequences

    Parameters
    ----------
    tag : Tag
        the tag of the sequence
    frame_link : bool
        if the link is related to a frame.
        (requires a frame number to access correct value through `get_tag`)
    """
    tag: Tag
    frame_link: bool = False


@overload
def get_tag(dicom_image: pydicom.Dataset | pydicom.DataElement,
            tag: Tag,
            frame: int | None = None,
            get_first: Literal[False] = False
            ) -> list[pydicom.DataElement]: ...


@overload
def get_tag(dicom_image: pydicom.Dataset | pydicom.DataElement,
            tag: Tag,
            frame: int | None = None,
            get_first: Literal[True] = True
            ) -> pydicom.DataElement: ...


def get_tag(dicom_image: pydicom.Dataset | pydicom.DataElement,
            tag: Tag,
            frame: int | None = None,
            get_first: bool = False
            ) -> pydicom.DataElement | list[pydicom.DataElement]:
    """
    Returns the dicom element from the pydicom Dataset defined by tag.
    If the Dataset is an enhanced dicom then the frame can be provided for frame specific elements.

    Parameters
    ----------
    dicom_image : Dataset | DataElement
        pydicom Dataset/DataElement to be searched
    tag : Tag
        tag of element to be returned
    frame : int, optional
        frame number (starting at 1) if relevant, by default None
    get_first : bool, optional
        whether to get the first value for a matching tag in dicom_image

    Returns
    -------
    DataElement | list[DataElement]
        pydicom DataElement of the provided tag,
        or a list of pydicom DataElements for the provided tag.
        Use DataElement.value attribute to get the value of the element.

    Raises
    ------
    KeyError
        raised if an element is not found.
    """
    elements: list[pydicom.DataElement] | None = None

    try:
        if get_first:
            return dicom_image[int(tag)]
        else:
            return [dicom_image[int(tag)]]
    except KeyError:
        pass

    if elements is None:
        elements = []
        for seq_link in tag.links:
            try:
                sequence = get_tag(dicom_image, seq_link.tag, frame, False)
            except KeyError:
                continue
            for seq in sequence:
                value = seq.value
                if seq_link.frame_link and frame is not None:
                    try:
                        element = get_tag(value[frame - 1], tag, frame, False)
                        if get_first:
                            return element[0]
                        elements.extend(element)
                    except KeyError:
                        pass
                    except IndexError as exc:
                        raise IndexError("'frame' is invalid number.") from exc
                else:
                    for entry in value:
                        try:
                            element = get_tag(entry, tag, frame, False)
                            if get_first:
                                return element[0]
                            elements.extend(element)
                        except KeyError:
                            pass

    if isinstance(element, list):
        if len(element) == 0:
            raise KeyError(f"{tag}, {tag.name}")
        elif get_first:
            return element[0]

    return element


@overload
def get_value(dicom_image: pydicom.Dataset | pydicom.DataElement,
              tag: Tag,
              frame: int | None = None,
              get_first: Literal[False] = False) -> Any | list[Any]: ...


@overload
def get_value(dicom_image: pydicom.Dataset | pydicom.DataElement,
              tag: Tag,
              frame: int | None = None,
              get_first: Literal[True] = True) -> Any: ...


def get_value(dicom_image: pydicom.Dataset | pydicom.DataElement,
              tag: Tag,
              frame: int | None = None,
              get_first: bool = False) -> Any | list[Any]:
    """
    Returns the value of the dicom element from the pydicom Dataset defined by tag.
    If the Dataset is an enhanced dicom then the frame can be provided for frame specific elements.

    Parameters
    ----------
    dicom_image : Dataset | DataElement
        pydicom Dataset/DataElement to be searched
    tag : Tag
        tag of element to be returned
    frame : int, optional
        frame number (starting at 1) if relevant, by default None
    get_first : bool, optional
        whether to get the first value for a matching tag in dicom_image

    Returns
    -------
    Any | list[Any]
        value of the pydicom DataElement of the provided tag,
        or a list of values for pydicom DataElements for the provided tag.

    Raises
    ------
    KeyError
        raised if an element is not found.
    """
    tag_object = get_tag(dicom_image, tag, frame, get_first)
    if isinstance(tag_object, list):
        value = [t.value for t in tag_object]
    else:
        value = tag_object.value

    return value
