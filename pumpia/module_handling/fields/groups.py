"""
Contains groupings of inputs/outputs.
"""
from typing import overload, Self
from pumpia.module_handling.fields.fields import BaseField
from pumpia.module_handling.module_collections import BaseCollection


class _FieldGroups:
    def __init__(self, obj: BaseCollection) -> None:
        self.groups_dict: dict[str, FieldGroup] = {}
        self.obj: BaseCollection = obj

    def __iter__(self):
        for module in self.groups_dict.values():
            yield module


class _FieldGroupsMeta:
    def __init__(self) -> None:
        self.groups: dict[str, FieldGroup] = {}
        self.name: str = ""
        self.private_name: str = "_"

    @property
    def group_names(self) -> list[str]:
        return list(self.groups.keys())

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        self.private_name = "_" + name

    @overload
    def __get__(self, obj: BaseCollection, owner=None) -> _FieldGroups: ...
    @overload
    def __get__(self, obj: None, owner=None) -> Self: ...

    def __get__(self, obj: BaseCollection | None, owner=None) -> _FieldGroups | Self:
        if obj is None:
            return self

        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            groups = _FieldGroups(obj)
            setattr(obj, self.private_name, groups)
            return groups


class FieldGroup:
    """
    Represents a group of linked input / output objects.
    IOs should only be a member of one group.

    Parameters
    ----------
    linked_ios: list[BaseIO]
        The list of linked input / output objects.

    Attributes
    ----------
    linked_ios: list[BaseIO]
    """

    def __init__(self, fields: list[BaseField]):
        self.name: str = ""
        self.module_fields: list[tuple[str, str]] = [(field.module.name, field.name)
                                                     for field in fields
                                                     if field.module is not None]

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        owner.field_groups.groups[name] = self
