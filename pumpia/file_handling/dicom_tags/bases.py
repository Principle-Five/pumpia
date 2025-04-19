import dataclasses as dc
from dataclasses import dataclass
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
    as_tuple : list[tuple[int, int]]
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

    def get(self) -> tuple[int, int]:
        """
        returns the tag as a Tuple of (group, element)

        Returns
        -------
        Tuple
            (group, element)
        """
        return self.as_tuple

    def __int__(self) -> int:
        return (self.group << 16) | self.element

    def __eq__(self, value) -> bool:
        if isinstance(value, Tag):
            return self.get() == value.get()
        elif isinstance(value, tuple):
            return self.get() == value
        elif isinstance(value, int):
            return int(self) == value
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.get())

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


def get_tag(dicom_image: pydicom.Dataset | pydicom.DataElement,
            tag: Tag,
            frame: int | None = None) -> pydicom.DataElement:
    """
    Returns the dicom element from the pydicom Dataset defined by tag.
    If the Dataset is a stack then the frame can be provided for frame specific elements.

    Parameters
    ----------
    dicom_image : Dataset
        pydicom Dataset to be searched
    tag : Tag
        tag of element to be returned
    frame : int, optional
        frame number (starting at 1) if relevant, by default None

    Returns
    -------
    DataElement
        pydicom Dataelement of the provided tag.
        Use DataElement.value attribute to get the value of the element.

    Raises
    ------
    KeyError
        raised if an element is not found.
    """
    element = None

    try:
        element = dicom_image[int(tag)]
    except KeyError:
        pass

    sequence = None
    for seq in tag.links:
        try:
            if seq.frame_link and frame is not None:
                sequence = get_tag(dicom_image, seq.tag, frame).value
                element = sequence[frame - 1][tag.as_tuple]
            elif not seq.frame_link:
                sequence = get_tag(dicom_image, seq.tag, frame).value
                element = sequence[0][tag.as_tuple]
        except (KeyError, IndexError):
            pass

    if element is None:
        raise KeyError(f"{tag.as_tuple}, {tag.name}")

    return element
