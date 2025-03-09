"""
Contains groupings of inputs/outputs.
"""
from pumpia.module_handling.in_outs.simple import BaseIO


class IOGroup:
    """
    Represents a group of linked input / output objects.

    Parameters
    ----------
    linked_ios: list[BaseIO]
        The list of linked input / output objects.

    Attributes
    ----------
    linked_ios: list[BaseIO]
    """

    def __init__(self, linked_ios: list[BaseIO]):
        var_type = linked_ios[0].var_type
        for vt in linked_ios[1:]:
            if vt.var_type is not var_type:
                raise ValueError("IOs not the same variable type")

        self.linked_ios: list[BaseIO] = linked_ios

        for io in self.linked_ios[1:]:
            io.value_var = self.linked_ios[0].value_var
