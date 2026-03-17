"""
Contains groupings of inputs/outputs.
"""
from typing import overload, Self
from pumpia.module_handling.fields.fields import BaseField
from pumpia.module_handling.module_collections import BaseCollection


class _FieldGroups:
    def __init__(self, obj: BaseCollection) -> None:
        self.obj: BaseCollection = obj
        self.groups_dict: dict[str, FieldGroup] = {}

    def __iter__(self):
        for group in self.groups_dict.values():
            yield group


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

    def __init__(self, *fields: BaseField, verbose_name: str | None = None):
        self.verbose_name: str | None = verbose_name
        self.module_field_names: list[tuple[str, str]] = [(field.module.name, field.name)
                                                          for field in fields
                                                          if field.module is not None]
        self.fields: list[BaseField] = []
        self.name: str = ""

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()
        owner.field_groups.groups[name] = self

    def __get__(self, obj: BaseCollection | None, owner=None) -> Self:
        if obj is None:
            return self

        try:
            return obj.field_groups.groups_dict[self.name]  # pyright: ignore[reportReturnType]
        except KeyError as exc:
            fields: list[BaseField] = []
            for module_name, field_name in self.module_field_names:
                fields.append(getattr(getattr(obj, module_name), field_name))

            value_type = fields[0].value_type
            for field in fields[1:]:
                if field.value_type is not value_type:
                    raise ValueError(f"Field values are not the same type for group {self.name}") from exc
                field.value = fields[0].value_store

            group = type(self)(*[], verbose_name=self.verbose_name)
            group.module_field_names = self.module_field_names
            group.fields = fields
            obj.field_groups.groups_dict[self.name] = group
            return group
