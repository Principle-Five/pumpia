"""
Classes:
 * Manager
"""

import datetime
import typing
from typing import TYPE_CHECKING, Literal
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from pathlib import Path
from pydicom import dcmread, FileDataset
from pydicom.errors import InvalidDicomError
from pumpia.file_handling.dicom_structures import Patient, Study, Series, Instance
from pumpia.image_handling.image_structures import BaseImageSet, FileImageSet
from pumpia.image_handling.roi_structures import BaseROI
from pumpia.file_handling.dicom_tags import DicomTags, get_tag
from pumpia.utilities.dicom_utils import show_dicom_tags
from pumpia.utilities.typing import DirectionType
from pumpia.utilities.tkinter_utils import tk_copy

if TYPE_CHECKING:
    from pumpia.widgets.viewers import BaseViewer

ReducedMouseOptionsType = Literal["Pointer",
                                  "Zoom",
                                  "Drag",
                                  "Window/Level"]

MouseOptionsType = Literal["Pointer",
                           "Zoom",
                           "Drag",
                           "Window/Level",
                           "Angle",
                           "ROI point",
                           "ROI circle",
                           "ROI ellipse",
                           "ROI square",
                           "ROI rectangle",
                           "ROI line"]

ROIOptionsType = Literal["None",
                         "Move",
                         "Resize"]

#    "ROI polygon",
#    "ROI free",
#    "ROI sector"]
MouseOptions: tuple[MouseOptionsType] = typing.get_args(MouseOptionsType)
ReducedMouseOptions: tuple[ReducedMouseOptionsType] = typing.get_args(ReducedMouseOptionsType)
ROIOptions: tuple[ROIOptionsType] = typing.get_args(ROIOptionsType)


class Manager:
    """
    Manages the data and shared widgets of the application.

    Users can drag images from the treeview widgets created by a Manager
    into a `Viewer` to show that image in the viewer.

    Right click menus within the treeviews have different options depending on the focus,
    for example:

    - copy the filepath for images loaded from files
    - show the tags of DICOM images
    - delete ROIs


    Attributes
    ----------
    patients : set[Patient]
        The set of patients.
    select_time : int
        The time of the last selection.
    focus : Patient | Study | BaseImageSet | BaseROI | None
    selected : list[Patient | Study | BaseImageSet | BaseROI]
        The list of selected items.
    current_action : MouseOptionsType
        The current mouse action.
    roi_action : ROIOptionsType
        The current ROI action.
    viewers : list[BaseViewer]
        The list of viewers.

    Methods
    -------
    load_folder(add: bool = True, tk_parent: tk.Misc | None = None, counter_column: int = 0, counter_row: int = 0, counter_stack_direction: DirectionType = "Vertical") -> None
        Loads DICOM files from a folder.
    load_images(files: list[Path], add: bool = True, tk_parent: tk.Misc | None = None, counter_column: int = 0, counter_row: int = 0, counter_stack_direction: DirectionType = "Vertical") -> None
        Loads images from a list of files.
    load_dicom(open_dicom: FileDataset, file: Path) -> Series | Instance
        Loads a DICOM file.
    update_trees()
        Updates the treeviews with the current data.
    add_roi(roi: BaseROI, moving: bool = False)
        Adds an ROI to the treeviews.
    delete_current_roi()
        Deletes the current focus if it is an ROI.
    show_tags()
        Shows the DICOM tags of the current focus if a DICOM file.
    copy_filepath()
        Copies the filepath of the current focus to the clipboard.
    copy_filepath_as_posix()
        Copies the filepath of the current focus to the clipboard in POSIX format.
    copy_directory()
        Copies the directory of the current focus to the clipboard.
    copy_directory_as_posix()
        Copies the directory of the current focus to the clipboard in POSIX format.
    update_viewers(image: BaseImageSet | None = None)
        Updates the viewers linked to the Manager.
    get_tree_frame(parent: tk.Misc, allow_delete_roi: bool = True) -> ttk.Frame
        Returns a frame containing a treeview.
    get_mouse_options_combobox(parent: tk.Misc, size: Literal["full", "reduced"] = "full") -> ttk.Combobox
        Returns a combobox for selecting mouse options.
    set_current_action(option: MouseOptionsType)
        Sets the current action.
    get_roi_options_frame(parent: tk.Misc, direction: DirectionType = "Vertical") -> ttk.Labelframe
        Returns a frame containing ROI options.
    set_current_roi_action(option: ROIOptionsType)
        Sets the current ROI action.
    """

    def __init__(self) -> None:
        self.patients: set[Patient] = set()
        self._treeviews: list[ttk.Treeview] = []
        self._current_action_vars: list[tk.StringVar] = []
        self._current_action_menus: list[ttk.Combobox] = []
        self._current_roi_vars: list[tk.StringVar] = []
        self._current_roi_frames: list[ttk.Labelframe] = []
        self.select_time: int = 0
        self.selected: list[Patient | Study | BaseImageSet | BaseROI] = []
        self._focus: Patient | Study | BaseImageSet | BaseROI | None = None
        self.current_action: MouseOptionsType = MouseOptions[0]
        self.roi_action: ROIOptionsType = ROIOptions[0]
        self.viewers: list[BaseViewer] = []

    @property
    def focus(self) -> Patient | Study | BaseImageSet | BaseROI | None:
        """
        The current focus, usually the last selected thing in a tree.
        """
        return self._focus

    @focus.setter
    def focus(self, focus: Patient | Study | BaseImageSet | BaseROI | None):
        if isinstance(self._focus, BaseROI):
            self._focus.active = False
            self.update_viewers(self._focus.image)
        self._focus = focus
        if isinstance(self._focus, BaseROI):
            self._focus.active = True
            self.update_viewers(self._focus.image)

    def load_folder(self,
                    add: bool = True,
                    tk_parent: tk.Misc | None = None,
                    counter_column: int = 0,
                    counter_row: int = 0,
                    counter_stack_direction: DirectionType = "Vertical") -> None:
        """
        Loads DICOM files from a folder.

        Parameters
        ----------
        add : bool, optional
            Whether to add to the existing data (default is True).
        tk_parent : tk.Misc, optional
            The parent widget for the loading information (default is None) .
        counter_column : int, optional
            The column position for the loading information (default is 0) .
        counter_row : int, optional
            The row position for the loading information. (default is 0).
        counter_stack_direction : DirectionType, optional
            The direction of the loading information (default is "Vertical").
        """
        directory = Path(askdirectory())
        if directory.is_dir() and str(directory) != ".":
            files = [dirpath / f
                     for (dirpath, _, filenames) in directory.walk()
                     for f in filenames]

            self.load_images(files,
                             add,
                             tk_parent,
                             counter_column,
                             counter_row,
                             counter_stack_direction)

    def load_images(self,
                    files: list[Path],
                    add: bool = True,
                    tk_parent: tk.Misc | None = None,
                    counter_column: int = 0,
                    counter_row: int = 0,
                    counter_stack_direction: DirectionType = "Vertical") -> None:
        """
        Loads images from a list of files.

        Parameters
        ----------
        files : list[Path]
            The list of files.
        add : bool, optional
            Whether to add to the existing data (default is True).
        tk_parent : tk.Misc, optional
            The parent widget for the loading information (default is None) .
        counter_column : int, optional
            The column position for the loading information (default is 0) .
        counter_row : int, optional
            The row position for the loading information. (default is 0).
        counter_stack_direction : DirectionType, optional
            The direction of the loading information (default is "Vertical").
        """
        if not add:
            self.patients: set[Patient] = set()
            for viewer in self.viewers:
                viewer.unload_images()

        if tk_parent is not None:
            file_count = 0
            total_files = len(files)
            count_frame = tk.Frame(tk_parent)
            count_frame.grid(column=counter_column,
                             row=counter_row, sticky="nsew")

            count_label = ttk.Label(
                count_frame, text=f"{file_count}/{total_files}", anchor="center")

            count_bar = ttk.Progressbar(
                count_frame, maximum=total_files)

            if counter_stack_direction[0].lower() == "h":
                count_label.grid(column=0, row=0, sticky="nsew")
                count_bar.grid(column=1, row=0, sticky="nsew")
            else:
                count_label.grid(column=0, row=0, sticky="nsew")
                count_bar.grid(column=0, row=1, sticky="nsew")

            tk_parent.update()

        for file in files:
            try:
                open_dicom = dcmread(file)
            except InvalidDicomError:
                pass
            else:
                try:
                    _ = open_dicom.pixel_array
                except AttributeError:
                    pass
                else:
                    self.load_dicom(open_dicom, file)

            if tk_parent is not None:
                file_count += 1
                count_label["text"] = f"{file_count}/{total_files}"
                count_bar.step(1)
                tk_parent.update()

        if tk_parent is not None:
            count_frame.destroy()
        self.update_trees()

    def load_dicom(self, open_dicom: FileDataset, file: Path) -> Series | Instance:
        """
        Loads a DICOM file.

        Parameters
        ----------
        open_dicom : FileDataset
            The open DICOM dataset.
        file : Path
            The file path.

        Returns
        -------
        Series or Instance
            The loaded series or instance.
        """
        # load patient
        patient_id = get_tag(open_dicom, DicomTags.PatientID).value
        patient_id_str = "DICOM : " + patient_id
        if patient_id_str in self.patients:
            for pt in self.patients:
                if pt == patient_id_str:
                    patient = pt
        else:
            patient_name = get_tag(open_dicom, DicomTags.PatientName).value
            patient = Patient(patient_id, patient_name)
            self.patients.add(patient)

        # load study
        study_id = get_tag(open_dicom, DicomTags.StudyInstanceUID).value
        study_id_str = patient.id_string + " : " + study_id
        if study_id_str in patient.studies:
            for sd in patient.studies:
                if sd == study_id_str:
                    study = sd
        else:
            study_date = get_tag(open_dicom, DicomTags.StudyDate).value
            try:
                study_desc = get_tag(
                    open_dicom, DicomTags.StudyDescription).value
            except KeyError:
                study_desc = ""
            study_date = datetime.date(int(study_date[:4]),
                                       int(study_date[4:6]),
                                       int(study_date[6:]))
            study = Study(patient, study_id, study_date, study_desc)
            patient.add_study(study)

        # load series
        try:
            series_description = get_tag(
                open_dicom, DicomTags.SeriesDescription).value
        except KeyError:
            series_description = ""
        series_number = get_tag(open_dicom, DicomTags.SeriesNumber).value
        series_id = get_tag(open_dicom, DicomTags.SeriesInstanceUID).value
        try:
            acquisition_number = int(
                open_dicom[DicomTags.AcquisitionNumber.get()].value)
        except KeyError:
            acquisition_number = 0

        try:
            no_of_frames = get_tag(
                open_dicom, DicomTags.NumberOfFrames).value
            if no_of_frames == 1:
                is_stack = False
            else:
                is_stack = True
        except KeyError:
            is_stack = False

        series_id_str = study.id_string + " : " + series_id + "-" + str(acquisition_number)
        if series_id_str in study.series:
            for sr in study.series:
                if sr == series_id_str:
                    series = sr
        else:
            if is_stack:
                series = Series(study,
                                series_id,
                                series_number,
                                acquisition_number,
                                series_description,
                                is_stack,
                                open_dicom,
                                file)
            else:
                series = Series(study,
                                series_id,
                                series_number,
                                acquisition_number,
                                series_description,
                                is_stack)
            study.add_series(series)

        # load instance
        if is_stack:
            for frame_number in range(1, no_of_frames + 1):
                instance_id_str = series.id_string + " : " + str(frame_number)
                if instance_id_str in series.instances:
                    for ins in series.instances:
                        if ins == instance_id_str:
                            instance = ins
                else:
                    instance_number = get_tag(open_dicom,
                                              DicomTags.InstanceNumber,
                                              frame_number).value
                    dimension_index_values = get_tag(open_dicom,
                                                     DicomTags.DimensionIndexValues,
                                                     frame_number).value
                    instance = Instance(series,
                                        instance_number,
                                        file,
                                        True,
                                        frame_number,
                                        dimension_index_values)
                    try:
                        series.add_instance(instance)
                    except ValueError:
                        pass
        else:
            instance_number = get_tag(
                open_dicom, DicomTags.InstanceNumber).value
            instance_id_str = series.id_string + " : " + str(instance_number)
            if instance_id_str in series.instances:
                for ins in series.instances:
                    if ins == instance_id_str:
                        instance = ins
            else:
                instance = Instance(series, instance_number, file, False)
                try:
                    series.add_instance(instance)
                except ValueError:
                    pass

        if is_stack:
            return series
        else:
            return instance

    def update_trees(self):
        """
        Updates the treeviews with the current data.
        """
        for tree in self._treeviews:
            tree.delete(*tree.get_children())
            if len(self.patients) > 0:
                tree.insert('', 'end', iid='Dicoms', text="Dicoms", open=True)
                for pt in sorted(self.patients, key=str):
                    pt_id = pt.tag
                    pt_text = str(pt)
                    tree.insert("Dicoms",
                                'end',
                                iid=pt_id,
                                text=pt_text,
                                tags=('selected',
                                      pt.id_string))
                    for st in pt.studies:
                        st_id = st.tag
                        st_text = str(st)
                        tree.insert(pt_id,
                                    'end',
                                    iid=st_id,
                                    text=st_text,
                                    open=True,
                                    tags=('selected',
                                          st.id_string))
                        for sr in st.series:
                            sr_id = sr.tag
                            sr_text = str(sr)
                            if sr.filepath is not None:
                                sr_filepath = sr.filepath
                            else:
                                sr_filepath = ""
                            tree.insert(st_id,
                                        'end',
                                        iid=sr_id,
                                        text=sr_text,
                                        values=[sr_filepath],
                                        tags=('selected',
                                              sr.id_string))
                            for ins in sr.instances:
                                ins_id = ins.tag
                                ins_text = str(ins)
                                if ins.filepath is not None:
                                    ins_filepath = ins.filepath
                                else:
                                    ins_filepath = ""
                                tree.insert(sr_id,
                                            'end',
                                            iid=ins_id,
                                            text=ins_text,
                                            values=[ins_filepath],
                                            tags=('selected',
                                                  ins.id_string))

                                rois = ins.get_rois()
                                if len(rois) > 0:
                                    ins_roi_id = ins_id + "_rois"
                                    tree.insert(ins_id,
                                                'end',
                                                iid=ins_roi_id,
                                                text="ROIs",
                                                open=True)

                                    for roi in rois:
                                        roi_id = roi.tag
                                        roi_text = str(roi)
                                        roi_values = [roi.values_str]
                                        tree.insert(ins_roi_id,
                                                    'end',
                                                    iid=roi_id,
                                                    text=roi_text,
                                                    values=roi_values,
                                                    tags=('selected',
                                                          roi.id_string))

    def add_roi(self, roi: BaseROI, moving: bool = False):
        """
        Adds an ROI to the treeviews.

        Parameters
        ----------
        roi : BaseROI
            The ROI to add.
        moving : bool, optional
            Whether the ROI is being moved (default is False).
        """
        for tree in self._treeviews:

            ins_id = roi.image.tag
            ins_roi_id = roi.image.tag + "_rois"
            if ins_roi_id not in tree.get_children(ins_id):
                tree.insert(ins_id,
                            'end',
                            iid=ins_roi_id,
                            text="ROIs",
                            open=True)
            roi_id = roi.tag
            roi_text = str(roi)
            if not moving:
                roi_values = [roi.values_str]
            else:
                roi_values = ["Changing"]
            try:
                roi_index = tree.index(roi_id)
                tree.delete(roi_id)
            except tk.TclError:
                roi_index = 'end'
            tree.insert(ins_roi_id,
                        roi_index,
                        iid=roi_id,
                        text=roi_text,
                        values=roi_values,
                        tags=('selected',
                              roi.id_string),)

        self.focus = roi

    def delete_current_roi(self):
        """
        Deletes the current focus if it is an ROI.
        """
        if isinstance(self.focus, BaseROI):
            self.focus.image.remove_roi(self.focus)
            for tree in self._treeviews:
                roi_id = self.focus.tag
                try:
                    tree.delete(roi_id)
                except tk.TclError:
                    pass
                if len(self.focus.image.get_rois()) == 0:
                    ins_roi_id = self.focus.image.tag + "_rois"
                    try:
                        tree.delete(ins_roi_id)
                    except tk.TclError:
                        pass
            self.update_viewers(self.focus.image)
            self.focus = None

    def show_tags(self):
        """
        Shows the DICOM tags of the current focus if a DICOM file.
        """
        if isinstance(self.focus, (Series, Instance)):
            show_dicom_tags(self.focus)

    def copy_filepath(self):
        """
        Copies the filepath of the current focus to the clipboard.
        """
        if (isinstance(self.focus, (Series, FileImageSet))
                and self.focus.filepath is not None):
            tk_copy(str(self.focus.filepath.resolve()))

    def copy_filepath_as_posix(self):
        """
        Copies the filepath of the current focus to the clipboard in POSIX format.
        """
        if (isinstance(self.focus, (Series, FileImageSet))
                and self.focus.filepath is not None):
            tk_copy(self.focus.filepath.resolve().as_posix())

    def copy_directory(self):
        """
        Copies the directory of the current focus to the clipboard.
        """
        if (isinstance(self.focus, (Series, FileImageSet))
                and self.focus.filepath is not None):
            tk_copy(str(self.focus.filepath.parent.resolve()))

    def copy_directory_as_posix(self):
        """
        Copies the directory of the current focus to the clipboard in POSIX format.
        """
        if (isinstance(self.focus, (Series, FileImageSet))
                and self.focus.filepath is not None):
            tk_copy(self.focus.filepath.parent.resolve().as_posix())

    def update_viewers(self, image: BaseImageSet | None = None):
        """
        Updates the viewers linked to the Manager.
        If image is given then it only updates the viewers linked to that image.

        Parameters
        ----------
        image : BaseImageSet or None, optional
            The image to update (default is None).
        """
        if image is not None:
            for viewer in self.viewers:
                if viewer.current_image is not None and viewer.current_image is image:
                    viewer.update()
        else:
            for viewer in self.viewers:
                viewer.update()

    def _set_selected(self, tree: ttk.Treeview, _: tk.Event):
        """
        Sets the selected item in the treeview.

        Parameters
        ----------
        tree : ttk.Treeview
            The treeview widget.
        """
        focus = None
        if tree.parent(tree.focus()) != "":
            focus_hashes = tree.item(tree.focus())["tags"][1].split(" : ")
            if focus_hashes[0] == "DICOM":
                for pt in self.patients:
                    if pt == " : ".join(focus_hashes[: 2]):
                        focus = pt

                if len(focus_hashes) >= 3 and isinstance(focus, Patient):
                    for st in focus.studies:
                        if st == " : ".join(focus_hashes[:3]):
                            focus = st

                if len(focus_hashes) >= 4 and isinstance(focus, Study):
                    for sr in focus.series:
                        if sr == " : ".join(focus_hashes[:4]):
                            focus = sr

                if len(focus_hashes) >= 5 and isinstance(focus, Series):
                    for ins in focus.instances:
                        if ins == " : ".join(focus_hashes[:5]):
                            focus = ins

                if len(focus_hashes) >= 6 and isinstance(focus, Instance):
                    for roi in focus.get_rois():
                        if roi == " : ".join(focus_hashes[:6]):
                            focus = roi

            for sel in self.selected:
                if isinstance(sel, BaseROI):
                    sel.active = False
            self.selected = []
            current_sel: Patient | Study | BaseImageSet | BaseROI | None = None
            for selection in tree.selection():
                selection_hashes = tree.item(selection)['tags'][1].split(" : ")
                current_sel = None
                if selection_hashes[0] == "DICOM":
                    for pt in self.patients:
                        if pt == " : ".join(selection_hashes[:2]):
                            current_sel = pt

                    if len(selection_hashes) >= 3 and isinstance(current_sel, Patient):
                        for st in current_sel.studies:
                            if st == " : ".join(selection_hashes[:3]):
                                current_sel = st

                    if len(selection_hashes) >= 4 and isinstance(current_sel, Study):
                        for sr in current_sel.series:
                            if sr == " : ".join(selection_hashes[:4]):
                                current_sel = sr

                    if len(selection_hashes) >= 5 and isinstance(current_sel, Series):
                        for ins in current_sel.instances:
                            if ins == " : ".join(selection_hashes[:5]):
                                current_sel = ins

                    if len(selection_hashes) >= 6 and isinstance(current_sel, Instance):
                        for roi in current_sel.get_rois():
                            if roi == " : ".join(selection_hashes[:6]):
                                current_sel = roi
                                current_sel.active = True

                if current_sel is not None:
                    self.selected.append(current_sel)
        self.focus = focus
        self.update_viewers()

    def _set_select_time(self, event: tk.Event):
        """
        Sets the select time.
        For use with drag and drop into Viewers.

        Parameters
        ----------
        event : tk.Event
            The event object.
        """
        self.select_time = event.time

    def get_tree_frame(self, parent: tk.Misc, allow_delete_roi: bool = True) -> ttk.Frame:
        """
        Returns a frame containing a treeview.

        Parameters
        ----------
        parent : tk.Misc
            The parent widget.
        allow_delete_roi : bool, optional
            Whether to allow deleting ROIs (default is True).

        Returns
        -------
        ttk.Frame
            The frame containing the treeview.
        """
        current_frame = ttk.Frame(parent)
        current_frame.columnconfigure(0, weight=1)
        current_frame.rowconfigure(0, weight=1)

        current_tree = ttk.Treeview(current_frame)
        current_tree.tag_bind('selected',
                              '<<TreeviewSelect>>',
                              lambda event: self._set_selected(current_tree, event))
        current_tree.bind("<ButtonRelease-1>", self._set_select_time)
        current_tree['columns'] = ['measurements']
        current_tree.heading('measurements', text='Measurements')
        current_tree.grid(row=0, column=0, sticky='nsew')

        yscrollbar = ttk.Scrollbar(
            current_frame, orient=tk.VERTICAL, command=current_tree.yview)
        current_tree.configure(yscrollcommand=yscrollbar.set)
        yscrollbar.grid(row=0, column=1, sticky='ns')

        xscrollbar = ttk.Scrollbar(
            current_frame, orient=tk.HORIZONTAL, command=current_tree.xview)
        current_tree.configure(xscrollcommand=xscrollbar.set)
        xscrollbar.grid(row=1, column=0, columnspan=2, sticky='ew')

        def popup_menu(event: tk.Event):
            menu = tk.Menu(current_frame, tearoff=False)
            if isinstance(self.focus, BaseROI):
                if allow_delete_roi:
                    menu.add_command(
                        label="Delete ROI", command=self.delete_current_roi)

                for label, command in self.focus.menu_options:
                    menu.add_command(label=label, command=command)

            elif isinstance(self.focus, (Series, Instance, FileImageSet)):
                if isinstance(self.focus, (Series, Instance)):
                    menu.add_command(label="Show Tags", command=self.show_tags)
                menu.add_command(label="Copy Filepath",
                                 command=self.copy_filepath)
                menu.add_command(label="Copy Filepath as posix",
                                 command=self.copy_filepath_as_posix)
                menu.add_command(label="Copy Directory",
                                 command=self.copy_directory)
                menu.add_command(label="Copy Directory as posix",
                                 command=self.copy_directory_as_posix)
                for label, command in self.focus.menu_options:
                    menu.add_command(label=label, command=command)

            menu.tk_popup(event.x_root, event.y_root)

        def tree_enter(_: tk.Event):
            current_frame.bind_all("<Button-3>", popup_menu)

        def tree_exit(_: tk.Event):
            current_frame.unbind_all("<Button-3>")

        current_tree.bind("<Enter>", tree_enter)
        current_tree.bind("<Leave>", tree_exit)

        self._treeviews.append(current_tree)
        self.update_trees()

        return current_frame

    def get_mouse_options_combobox(self,
                                   parent: tk.Misc,
                                   size: Literal["full", "reduced"] = "full"
                                   ) -> ttk.Combobox:
        """
        Returns a combobox for selecting mouse options.

        Parameters
        ----------
        parent : tk.Misc
            The parent widget.
        size : Literal["full", "reduced"], optional
            The options to be included in the combobox (default is "full").

        Returns
        -------
        ttk.Combobox
            The combobox for selecting mouse options.
        """
        if size == "reduced":
            if self.current_action not in ReducedMouseOptions:
                self.set_current_action("Pointer")
            options = ReducedMouseOptions
        else:
            options = MouseOptions
        current_var = tk.StringVar(parent, value=self.current_action)
        current_var.trace_add(
            'write', lambda *_: self._current_action_selected(current_var))
        current_combo = ttk.Combobox(
            parent, textvariable=current_var, values=options, height=7, state="readonly")
        self._current_action_vars.append(current_var)
        self._current_action_menus.append(current_combo)
        return current_combo

    def _current_action_selected(self, var: tk.StringVar):
        """
        Sets the current action based on the selected value in the combobox.

        Parameters
        ----------
        var : tk.StringVar
            The variable associated with the combobox.
        """
        option = var.get()
        if (option in MouseOptions
                or option in ReducedMouseOptions):
            self.set_current_action(option)

    def set_current_action(self, option: MouseOptionsType):
        """
        Sets the current action.

        Parameters
        ----------
        option : MouseOptionsType
            The action to set.
        """
        self.current_action = option
        for other_var in self._current_action_vars:
            other_var.set(self.current_action)

    def get_roi_options_frame(self,
                              parent: tk.Misc,
                              direction: DirectionType = "Vertical"
                              ) -> ttk.Labelframe:
        """
        Returns a frame containing ROI options.

        Parameters
        ----------
        parent : tk.Misc
            The parent widget.
        direction : DirectionType, optional
            The direction of the options (default is "Vertical").

        Returns
        -------
        ttk.Labelframe
            The frame containing ROI options.
        """
        current_var = tk.StringVar(parent, value=self.roi_action)
        current_var.trace_add(
            'write', lambda *_: self._current_roi_action_selected(current_var))
        current_frame = ttk.Labelframe(parent, text="ROI options")
        self._current_roi_vars.append(current_var)
        self._current_roi_frames.append(current_frame)

        rad_buttons: list[ttk.Radiobutton] = []
        for index, opt in enumerate(ROIOptions):
            rad_buttons.append(ttk.Radiobutton(
                current_frame, variable=current_var, text=opt, value=opt))

            if direction[0].lower() == "h":
                rad_buttons[-1].grid(row=0, column=index, sticky="nsew")
            else:
                rad_buttons[-1].grid(row=index, column=0, sticky="nsew")

        return current_frame

    def _current_roi_action_selected(self, var: tk.StringVar):
        """
        Sets the current ROI action based on the selected value in the roi actions options.

        Parameters
        ----------
        var : tk.StringVar
            The variable associated with the radiobuttons.
        """
        option = var.get()
        if option in ROIOptions:
            self.set_current_roi_action(option)

    def set_current_roi_action(self, option: ROIOptionsType):
        """
        Sets the current ROI action.

        Parameters
        ----------
        option : ROIOptionsType
            The ROI action to set.
        """
        self.roi_action = option
        for other_var in self._current_roi_vars:
            other_var.set(self.roi_action)
