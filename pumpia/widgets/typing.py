"""Some useful tkinter types"""


from tkinter.font import Font
from typing import Literal, Any
from collections.abc import Callable

type FontDescription = (
    str  # "Helvetica 12"
    | Font  # A font object constructed in Python
    | list[Any]  # ["Helvetica", 12, BOLD]
    | tuple[str]  # ("Liberation Sans",) needs wrapping in tuple/list to handle spaces
    | tuple[str, int]  # ("Liberation Sans", 12)
    | tuple[str, int, str]  # ("Liberation Sans", 12, "bold")
    | tuple[str, int, list[str] | tuple[str, ...]]  # e.g. bold and italic
)

# Some widgets have an option named -compound that accepts different values
# than the _Compound defined here. Many other options have similar things.
type Anchor = Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"]
type ButtonCommand = str | Callable[[], Any]
type Compound = Literal["top", "left", "center", "right", "bottom", "none"]
# manual page: Tk_GetCursor
type Cursor = str | tuple[str] | tuple[str, str] | tuple[str, str, str] | tuple[str, str, str, str]
# example when it's sequence:  entry['invalidcommand'] = [entry.register(print), '%P']
type EntryValidateCommand = str | list[str] | tuple[str, ...] | Callable[[], bool]
type EntryValidateOptions = Literal["none", "focus", "focusin", "focusout", "key", "all"]
type Relief = Literal["raised", "sunken", "flat", "ridge", "solid", "groove"]
type ScreenUnits = str | float  # Often the right instead of int. Manual page: Tk_GetPixels
# -xscrollcommand and -yscrollcommand in 'options' manual page
type XYScrollCommand = str | Callable[[float, float], object]
type TakeFocusValue = bool | Literal[0, 1, ""] | Callable[[str], bool | None]
type Padding = (
    ScreenUnits
    | tuple[ScreenUnits]
    | tuple[ScreenUnits, ScreenUnits]
    | tuple[ScreenUnits, ScreenUnits, ScreenUnits]
    | tuple[ScreenUnits, ScreenUnits, ScreenUnits, ScreenUnits]
)
