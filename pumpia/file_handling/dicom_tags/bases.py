"""
Base classes and functions for DICOM handling.
"""
import dataclasses as dc
from dataclasses import dataclass
from typing import overload, Literal
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
            get_first: Literal[False] = False) -> pydicom.DataElement | list[pydicom.DataElement]: ...


@overload
def get_tag(dicom_image: pydicom.Dataset | pydicom.DataElement,
            tag: Tag,
            frame: int | None = None,
            get_first: Literal[True] = True) -> pydicom.DataElement: ...


def get_tag(dicom_image: pydicom.Dataset | pydicom.DataElement,
            tag: Tag,
            frame: int | None = None,
            get_first: bool = False) -> pydicom.DataElement | list[pydicom.DataElement]:
    """
    Returns the dicom element from the pydicom Dataset defined by tag.
    If the Dataset is a stack then the frame can be provided for frame specific elements.

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
        pydicom DataElement of the provided tag, or a list of pydicom DataElements for the provided tag.
        Use DataElement.value attribute to get the value of the element.

    Raises
    ------
    KeyError
        raised if an element is not found.
    """
    element: pydicom.DataElement | list[pydicom.DataElement] | None = None

    try:
        element = dicom_image[int(tag)]
    except KeyError:
        pass

    if element is None:
        for seq_link in tag.links:
            try:
                sequence = get_tag(dicom_image, seq_link.tag, frame, get_first)
                if isinstance(sequence, pydicom.DataElement):
                    value = sequence.value
                    if seq_link.frame_link and frame is not None:
                        element = get_tag(value[frame - 1], tag, frame, get_first)
                    else:
                        if get_first:
                            element = get_tag(value[0], tag, frame, get_first)
                        else:
                            element = []
                            for entry in value:
                                subelement = get_tag(entry, tag, frame, get_first)
                                if isinstance(subelement, pydicom.DataElement):
                                    element.append(subelement)
                                else:
                                    element.extend(subelement)
                else:
                    if get_first:
                        element = get_tag(sequence[0].value[0], tag, frame, get_first)
                    else:
                        element = []
                        for entry in sequence:
                            for value in entry.value:
                                subelement = get_tag(value, tag, frame, get_first)
                                if isinstance(subelement, pydicom.DataElement):
                                    element.append(subelement)
                                else:
                                    element.extend(subelement)
            except KeyError:
                pass

    if element is None:
        raise KeyError(f"{tag}, {tag.name}")
    elif isinstance(element, list):
        if len(element) == 0:
            raise KeyError(f"{tag}, {tag.name}")
        elif len(element) == 1:
            element = element[0]

    return element
