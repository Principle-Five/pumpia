"""
Contains groupings of inputs/outputs.
"""
from typing import overload, Self, TYPE_CHECKING
from pumpia.module_handling.fields.fields import BaseField

if TYPE_CHECKING:
    from pumpia.module_handling.collections import BaseCollection


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
        self.base_owner: type[BaseCollection] | None = None

    @property
    def group_names(self) -> list[str]:
        return list(self.groups.keys())

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        self.private_name = "_" + name
        self.base_owner = owner

    @overload
    def __get__(self, obj: BaseCollection, owner: type[BaseCollection]) -> _FieldGroups: ...
    @overload
    def __get__(self, obj: None, owner: type[BaseCollection]) -> Self: ...

    def __get__(self, obj: BaseCollection | None, owner: type[BaseCollection]) -> _FieldGroups | Self:
        if obj is None:
            if owner is self.base_owner:
                return self
            else:
                meta_obj = type(self)()
                meta_obj.name = self.name
                meta_obj.private_name = self.private_name
                meta_obj.base_owner = owner
                setattr(owner, self.name, meta_obj)
                return meta_obj

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
        self.fields: list[BaseField] = list(fields)
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
            fields: list[BaseField] = [getattr(getattr(obj, field.module.name).fields, field.name)
                                       for field in self.fields
                                       if field.module is not None]

            value_type = fields[0].value_type
            for field in fields[1:]:
                if field.value_type is not value_type:
                    raise ValueError(f"Field values are not the same type for group {self.name}") from exc
                field.value = fields[0].value_store

            group = type(self)(*fields, verbose_name=self.verbose_name)
            obj.field_groups.groups_dict[self.name] = group
            return group
        except AttributeError:
            return self
