"""
Classes:
 * DateVar
"""

import tkinter as tk
from tkinter import messagebox as tkmessagebox
from datetime import date

from pumpia.utilities.string_validators import check_date


class DateVar(tk.StringVar):
    """
    var for dates
    """

    def get(self) -> date:
        """
        gets DateVar as python date object

        Gets date from underlying string object, should be format `d/m/y`.

        Raises:
            ValueError: if date in underlying string variable is an invalid format

        Returns:
            date: DateVar as date object
        """
        r_date = super().get()
        r_date = r_date.strip()
        try:
            r_date = r_date.split("/")
            if len(r_date[2]) == 2:
                r_date[2] = "20" + r_date[2]
            return date(int(r_date[2]), int(r_date[1]), int(r_date[0]))

        except ValueError as exc:
            tkmessagebox.showerror("Date Error", "Invalid Date \n Format d/m/y required")
            raise ValueError("Invalid Date: format d/m/y required") from exc

    def set(self, value: date | str) -> None:
        """
        Set the variable to value.
        If value is a string must be in format `d/m/y`.

        Raises:
            ValueError: if date is invalid format
        """
        if isinstance(value, date):
            value = value.strftime("%d/%m/%Y")
        elif not check_date(value):
            raise ValueError("Invalid Date: format d/m/y required")
        return super().set(value)
