"""
Some useful tkinter utilities

Functions:
 * remove_state_persistents
"""
import platform
import tkinter as tk

MODS = {0: 'Shift',
        1: 'Lock',
        2: 'Control',
        3: 'Mod1',
        4: 'Mod2',
        5: 'Mod3',
        6: 'Mod4',
        7: 'Mod5',
        8: 'Button1',
        9: 'Button2',
        10: 'Button3',
        11: 'Button4',
        12: 'Button5',
        17: 'Alt'}


def remove_state_persistents(state: int | str) -> int:
    """
    Removes persistants (e.g. caps-lock, scroll-lock, num-lock) from a modifying state
    as described at https://wiki.tcl-lang.org/page/Modifier+Keys

    Parameters
    ----------
    state : int|str
        state of a tkinter event (tk.Event.state)

    Returns
    -------
    int
        the state without any persistants

    Raises
    ------
    ValueError
        if state cannot be cast to an integer
    """

    plat_system = platform.system()

    if isinstance(state, str):
        try:
            state = int(state)
        except ValueError as exc:
            raise ValueError("State not an integer") from exc

    new_state: int = 0

    for i, n in MODS.items():
        mod_state = 1 << i
        if state & mod_state:
            if n != 'Lock':
                if plat_system == 'Linux':
                    if n != 'Mod2':
                        new_state += mod_state
                elif plat_system == 'Windows':
                    if (n != 'Mod1'
                            and n != 'Mod3'):
                        new_state += mod_state
                else:
                    new_state += mod_state

    return new_state


def tk_copy(text: str):
    """
    Copy text to the clipboard using tkinter.
    """
    win = tk.Tk()
    win.withdraw()
    win.clipboard_clear()
    win.clipboard_append(text)
    win.update()  # now it stays on the clipboard after the window is closed
    win.destroy()
