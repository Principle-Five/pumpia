"""Some useful tkinter types"""


from tkinter.font import Font
from typing import Literal, Any
from collections.abc import Callable

FontDescription = (
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
Anchor = Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"]
ButtonCommand = str | Callable[[], Any]
Compound = Literal["top", "left", "center", "right", "bottom", "none"]
# manual page: Tk_GetCursor
Cursor = str | tuple[str] | tuple[str, str] | tuple[str, str, str] | tuple[str, str, str, str]
# example when it's sequence:  entry['invalidcommand'] = [entry.register(print), '%P']
EntryValidateCommand = str | list[str] | tuple[str, ...] | Callable[[], bool]
EntryValidateOptions = Literal["none", "focus", "focusin", "focusout", "key", "all"]
Relief = Literal["raised", "sunken", "flat", "ridge", "solid", "groove"]
ScreenUnits = str | float  # Often the right instead of int. Manual page: Tk_GetPixels
# -xscrollcommand and -yscrollcommand in 'options' manual page
XYScrollCommand = str | Callable[[float, float], object]
TakeFocusValue = bool | Literal[0, 1, ""] | Callable[[str], bool | None]
Padding = (
    ScreenUnits
    | tuple[ScreenUnits]
    | tuple[ScreenUnits, ScreenUnits]
    | tuple[ScreenUnits, ScreenUnits, ScreenUnits]
    | tuple[ScreenUnits, ScreenUnits, ScreenUnits, ScreenUnits]
)
