"""Some useful types"""

from typing import Literal
import pydicom

type SideType = Literal["top", "bottom", "left", "right"]
type DirectionType = Literal["Horizontal", "h", "H", "Vertical", "v", "V"]
type TagEntries = pydicom.DataElement | list[pydicom.DataElement]
