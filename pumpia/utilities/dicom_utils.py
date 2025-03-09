"""
Some useful dicom utilities

Functions:
 * show_dicom_tags
"""
import tkinter as tk
from tkinter import ttk
import pydicom
from pumpia.file_handling.dicom_structures import Series, Instance


def show_dicom_tags(dicom: pydicom.Dataset | Series | Instance):
    """
    Displays the DICOM tags in a seperate window.

    Parameters
    ----------
    dicom : pydicom.Dataset or Series or Instance
        The DICOM dataset, series, or instance to display the tags for.
    """
    if isinstance(dicom, (Series, Instance)):
        if dicom.dicom_dataset is not None:
            dicom = dicom.dicom_dataset
        else:
            return

    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.resizable(True, True)

    tree = ttk.Treeview(root, columns=["Name", "Value"])
    tree.heading("#0", text="Tag")
    tree.heading("Name", text="Name")
    tree.heading("Value", text="Value")

    tree.column("#0", stretch=False)
    tree.column("Name", stretch=True)
    tree.column("Value", stretch=True)

    yscrollbar = ttk.Scrollbar(
        root, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=yscrollbar.set)
    yscrollbar.grid(row=0, column=1, sticky='ns')

    xscrollbar = ttk.Scrollbar(
        root, orient=tk.HORIZONTAL, command=tree.xview)
    tree.configure(xscrollcommand=xscrollbar.set)
    xscrollbar.grid(row=1, column=0, columnspan=2, sticky='ew')

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
                                values=[elem.name,
                                        elem.repval])
            if elem.VR == 'SQ':
                for item in elem.value:
                    add_to_tree(item, entry)

    add_to_tree(dicom)

    tree.grid(column=0, row=0, sticky='nsew')

    root.mainloop()
