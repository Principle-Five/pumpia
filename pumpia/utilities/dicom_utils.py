"""
Some useful dicom utilities

Functions:
 * show_dicom_tags
"""
from dataclasses import dataclass, field
import tkinter as tk
import pydicom
from pumpia.file_handling.dicom_structures import Series, Instance
from pumpia.widgets.treeviews import SearchTreeview, DiffTreeview


@dataclass
class TagInfo:
    tag: str
    name: str
    children: dict[str, 'TagInfo'] = field(default_factory=dict)
    values: list[str] = field(default_factory=list)


def show_dicom_tags(dicom: pydicom.Dataset | Series | Instance):
    """
    Displays the DICOM tags in a seperate window.

    Parameters
    ----------
    dicom : pydicom.Dataset or Series or Instance
        The DICOM dataset, series, or instance to display the tags for.
    """
    title = "DICOM Tags"
    if isinstance(dicom, (Series, Instance)):
        if dicom.dicom_dataset is not None:
            title = title + ": " + dicom.full_string
            dicom = dicom.dicom_dataset
        else:
            return

    root = tk.Toplevel()
    root.title(title)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.resizable(True, True)

    tree = SearchTreeview(root, columns=["Name", "Value"])
    tree.heading("#0", text="Tag")
    tree.heading("Name", text="Name")
    tree.heading("Value", text="Value")

    tree.column("#0", stretch=False)
    tree.column("Name", stretch=True)
    tree.column("Value", stretch=True)

    def add_to_tree(elem: pydicom.DataElement | pydicom.Dataset, parent: str = ''):
        """
        Adds elements to the treeview.

        Parameters
        ----------
        elem : pydicom.DataElement or pydicom.Dataset
            The DICOM element or dataset to add to the treeview.
        parent : str, optional
            The parent item in the treeview (default is '').
        """
        if isinstance(elem, pydicom.Dataset):
            for item in elem:
                add_to_tree(item, parent)

        elif isinstance(elem, pydicom.DataElement):
            tag = f"({elem.tag.group:04X}, {elem.tag.element:04X})"
            entry = tree.insert(parent,
                                'end',
                                text=tag,
                                values=[str(elem.name).strip(),
                                        str(elem.repval).strip()])
            if elem.VR == 'SQ':
                for index, item in enumerate(elem.value):
                    if len(elem.value) > 1:
                        sq_index = tree.insert(entry,
                                               'end',
                                               text=str(index + 1))
                        add_to_tree(item, sq_index)
                    else:
                        add_to_tree(item, entry)
    add_to_tree(dicom)

    tree.grid(column=0, row=0, sticky=tk.NSEW)


def compare_dicom_tags(*dicoms: pydicom.Dataset | Series | Instance):
    """
    Compares the DICOM tags in a seperate window.

    Parameters
    ----------
    dicom : pydicom.Dataset or Series or Instance
        The DICOM dataset, series, or instance to display the tags for.
    """
    title = "DICOM Tags Comparison"
    dicom_datasets: list[pydicom.Dataset] = []
    columns = ["Name"]
    diff_checks: list[bool] = [False]
    for i, dicom in enumerate(dicoms):
        columns.append(f"Value{i}")
        diff_checks.append(True)
        if isinstance(dicom, (Series, Instance)):
            if dicom.dicom_dataset is not None:
                dicom_datasets.append(dicom.dicom_dataset)
            else:
                return
        else:
            dicom_datasets.append(dicom)

    root = tk.Toplevel()
    root.title(title)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.resizable(True, True)

    tree = DiffTreeview(root, columns=columns, diff_checks=diff_checks)
    tree.heading("#0", text="Tag")
    tree.heading("Name", text="Name")
    tree.column("#0", stretch=False)
    tree.column("Name", stretch=False)

    for i, dicom in enumerate(dicoms):
        tree.column(f"Value{i}", stretch=True)
        if isinstance(dicom, (Series, Instance)):
            tree.heading(f"Value{i}", text=dicom.full_string)
        else:
            tree.heading(f"Value{i}", text=f"DICOM {i}")

    dicom_values: TagInfo = TagInfo("", "")

    def add_to_dict(elem: pydicom.DataElement | pydicom.Dataset, index: int, parent: TagInfo = dicom_values):
        """
        Adds elements to the treeview.

        Parameters
        ----------
        elem : pydicom.DataElement or pydicom.Dataset
            The DICOM element or dataset to add to the treeview.
        parent : str, optional
            The parent item in the treeview (default is '').
        """
        if isinstance(elem, pydicom.Dataset):
            for item in elem:
                add_to_dict(item, index, parent)

        elif isinstance(elem, pydicom.DataElement):
            tag = f"({elem.tag.group:04X}, {elem.tag.element:04X})"
            if tag not in parent.children:
                parent.children[tag] = TagInfo(tag, str(elem.name).strip())
            while len(parent.children[tag].values) < index:
                parent.children[tag].values.append("")
            parent.children[tag].values.append(str(elem.repval).strip())

            if elem.VR == 'SQ':
                for i, item in enumerate(elem.value):
                    if len(elem.value) > 1:
                        name = str(i + 1)
                        if name not in parent.children[tag].children:
                            parent.children[tag].children[name] = TagInfo(name, "")
                        add_to_dict(item, index, parent.children[tag].children[name])
                    else:
                        add_to_dict(item, index, parent.children[tag])

    for i, dicom in enumerate(dicom_datasets):
        add_to_dict(dicom, i)

    def add_to_tree(elem: TagInfo, parent: str = ''):
        """
        Adds elements to the treeview.

        Parameters
        ----------
        elem : pydicom.DataElement or pydicom.Dataset
            The DICOM element or dataset to add to the treeview.
        parent : str, optional
            The parent item in the treeview (default is '').
        """
        for tag, child in elem.children.items():
            entry = tree.insert(parent,
                                'end',
                                text=tag,
                                values=[child.name,
                                        *child.values])
            add_to_tree(child, entry)

    add_to_tree(dicom_values)

    tree.grid(column=0, row=0, sticky=tk.NSEW)
