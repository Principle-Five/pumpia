"""
Classes:
 * ModuleGroup
"""
import tkinter as tk
from tkinter import ttk
from typing import overload, Self, TYPE_CHECKING
from pumpia.utilities.typing import DirectionType
from pumpia.widgets.typing import ScreenUnits, Cursor, Padding, Relief, TakeFocusValue
from pumpia.module_handling.modules import BaseModule

if TYPE_CHECKING:
    from pumpia.module_handling.collections import BaseCollection
else:
    type BaseCollection = object


class ModuleGroup(ttk.Panedwindow):
    """
    Groups multiple modules into the same tab in the collection.

    Parameters
    ----------
    *modules : BaseModule
    verbose_name : str or None, optional
        The verbose name of the group (default is None).
    direction : DirectionType, optional
        The direction of the modules in the group (default is vertical).
    **kw : dict
        Additional keyword arguments as defined by ttk Panedwindow.

    Attributes
    ----------
    modules : list[BaseModule]
        The list of modules to display.
    verbose_name : str or None
        The verbose name of the group.
    direction : str
        The direction of the modules in the group.

    Methods
    -------
    setup(parent: tk.Misc, verbose_name: str | None = None)
        Sets up the window group.
    on_tab_select()
        Called when the tab containing this window is selected.
    """

    @overload
    def __init__(
        self,
        *modules: BaseModule,
        verbose_name: str | None = None,
        direction: DirectionType = "V",
        border: ScreenUnits = ...,
        borderwidth: ScreenUnits = ...,
        class_: str = "",
        cursor: Cursor = "",
        height: ScreenUnits = 0,
        padding: Padding = ...,
        relief: Relief = ...,
        style: str = "",
        takefocus: TakeFocusValue = "",
        width: ScreenUnits = 0,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *modules: BaseModule,
        verbose_name: str | None = None,
        direction: DirectionType = "V",
        **kwargs) -> None: ...

    # pylint: disable-next=super-init-not-called
    def __init__(self,
                 *modules: BaseModule,
                 verbose_name: str | None = None,
                 direction: DirectionType = "V",
                 **kw) -> None:
        self.module_names: list[str] = []
        self.modules: list[BaseModule] = list(modules)
        self.verbose_name: str | None = verbose_name
        self.name: str = ""

        if direction[0].lower() == "h":
            self.direction: DirectionType = "horizontal"
        else:
            self.direction: DirectionType = "vertical"
        self.kw = kw
        self.kw["orient"] = self.direction

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()
        owner.module_groups.groups[name] = self
        self.module_names = [module.name for module in self.modules]

    def __get__(self, obj: BaseCollection | None, owner=None) -> Self:
        if obj is None:
            return self

        try:
            return obj.module_groups.groups_dict[self.name]  # pyright: ignore[reportReturnType]
        except KeyError:
            group = type(self)(*[],
                               verbose_name=self.verbose_name,
                               direction=self.direction,
                               **self.kw)
            group.setup(parent=obj.notebook)

            modules: list[BaseModule] = []
            for module_name in self.module_names:
                module: BaseModule = getattr(obj, module_name)
                if module.verbose_name is None:
                    name = module.name
                else:
                    name = module.verbose_name
                lf = ttk.Labelframe(group, text=name, labelanchor="nw")
                lf.columnconfigure(0, weight=1)
                lf.rowconfigure(0, weight=1)
                module.setup(parent=lf,
                             manager=obj.manager,
                             context_manager=obj.context_manager,
                             parent_logger=obj.logger)
                module.grid(column=0, row=0, sticky=tk.NSEW)
                group.add(lf, weight=1)
                modules.append(getattr(obj, module_name))

            group.module_names = self.module_names
            group.modules = modules
            obj.module_groups.groups_dict[self.name] = group
            return group

    def setup(self, parent: tk.Misc):
        """
        Sets up the module group.

        Parameters
        ----------
        parent : tk.Misc
            The parent widget.
        """

        super().__init__(parent, **self.kw)

    def on_tab_select(self):
        """
        Called when the tab containing this group is selected.
        Defaults to calling on_tab_select for each module in the group.
        """
        for module in self.modules:
            module.on_tab_select()


class _ModuleGroups:
    def __init__(self, obj: BaseCollection) -> None:
        self.obj: BaseCollection = obj
        self.groups_dict: dict[str, ModuleGroup] = {}

    def __iter__(self):
        for group in self.groups_dict.values():
            yield group


class _ModuleGroupsMeta:
    def __init__(self) -> None:
        self.groups: dict[str, ModuleGroup] = {}
        self.name: str = ""
        self.private_name: str = "_"
        self.base_owner: type[BaseCollection] | None = None

    @property
    def group_names(self) -> list[str]:
        """
        The names of the module groups for the linked collection.
        """
        return list(self.groups.keys())

    def __set_name__(self, owner: type[BaseCollection], name: str):
        self.name = name
        self.private_name = "_" + name
        self.base_owner = owner

    @overload
    def __get__(self, obj: BaseCollection, owner: type[BaseCollection]) -> _ModuleGroups: ...
    @overload
    def __get__(self, obj: None, owner: type[BaseCollection]) -> Self: ...

    def __get__(self,
                obj: BaseCollection | None,
                owner: type[BaseCollection]
                ) -> _ModuleGroups | Self:
        if obj is None:
            if owner is self.base_owner:
                return self
            else:
                meta_obj = type(self)()
                meta_obj.name = self.name
                meta_obj.private_name = self.private_name
                meta_obj.base_owner = owner
                meta_obj.groups = self.groups.copy()
                setattr(owner, self.name, meta_obj)
                return meta_obj

        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            groups = _ModuleGroups(obj)
            setattr(obj, self.private_name, groups)
            return groups
