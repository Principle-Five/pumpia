"""
Functions:
 * check_date
 * check_float
 * check_int
 * check_perc
 * check_signed_float
 * check_signed_int
"""

from datetime import datetime


def check_date(s: str) -> bool:
    """
    Checks if the input string is a valid date in the format DD/MM/YYYY.
    """
    try:
        date = s.strip()
        if date == "":
            return True
        date = date.split("/")
        if len(date) > 3:
            raise NameError
        date = datetime(int(date[2]), int(date[1]), int(date[0]))
        return True
    except ValueError:
        return False


def check_int(s: str) -> bool:
    """
    Checks if the input string is an integer above 0.
    """
    if s.isdecimal() or str(s) == "":
        return True
    else:
        return False


def check_float(s: str) -> bool:
    """
    Checks if the input string is a float above 0.
    """
    if check_int(s):
        return True
    elif len(s) >= 2:
        s = s[0] + str(s[1:]).replace('.', '', 1)
        if s.isdecimal():
            return True
        else:
            return False
    else:
        return False


def check_perc(s: str) -> bool:
    """
    Checks if the input string is a valid percentage (0-100).
    """
    if check_float(s):
        if str(s) == "" or float(s) <= 100:
            return True
        else:
            return False
    else:
        return False


def check_signed_int(s: str) -> bool:
    """
    Checks if the input string is a valid integer.
    """
    if check_int(s):
        return True
    elif len(s) == 1 and s[0] == "-":
        return True
    elif len(s) >= 2:
        if s[0] == "-" and s[1:].isdecimal():
            return True
        else:
            return False
    else:
        return False


def check_signed_float(s: str) -> bool:
    """
    Checks if the input string is a valid float.
    """
    if check_float(s):
        return True
    elif len(s) == 1 and s[0] == "-":
        return True
    elif len(s) >= 2:
        if s[0] == "-" and s[1:].replace(".", "", 1).isdecimal():
            return True
        else:
            return False
    else:
        return False
