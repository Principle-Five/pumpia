"""
Classes:
 * Instance
 * Patient
 * Series
 * Study
"""

import datetime
from copy import copy
from pathlib import Path
from collections.abc import Callable
from typing import Literal
import pydicom
from pydicom.errors import InvalidDicomError
from pydicom import dcmread
from pydicom.pixels.processing import convert_color_space
import numpy as np
from pumpia.file_handling.dicom_tags import DicomTags, Tag, get_tag
from pumpia.image_handling.image_structures import FileImageSet, ImageCollection


class Patient:
    """
    Represents a patient from a DICOM file.

    Parameters
    ----------
    patient_id : str
        The ID of the patient.
    name : str
        The name of the patient.

    Attributes
    ----------
    patient_id : str
    name : str
    studies : list[Study]
    tag : str
    id_string : str
    menu_options : list[tuple[str, Callable[[], None]]]

    Methods
    -------
    add_study(study: Study)
        Adds a study to the patient.
    """

    def __init__(self, patient_id: str, name: str) -> None:
        self.patient_id: str = str(patient_id)
        self.name: str = str(name)
        self._studies: set[Study] = set()

    def __hash__(self) -> int:
        return hash(self.id_string)

    def __eq__(self, value: object) -> bool:
        """
        Checks equality with another object.

        Parameters
        ----------
        value : object
            The object to compare with.

        Returns
        -------
        bool
            True if equal, False otherwise.
        """
        if isinstance(value, Patient):
            return self.patient_id == value.patient_id
        elif isinstance(value, str):
            return self.id_string == value
        elif isinstance(value, int):
            return hash(self) == value
        else:
            return False

    def __str__(self) -> str:
        """Returns the string representation of the patient.
        This is the patient ID and name."""
        return self.patient_id + ": " + self.name

    @property
    def id_string(self) -> str:
        """Returns the ID string of the patient. This is "DICOM : `patient_id`"."""
        return "DICOM : " + self.patient_id

    @property
    def studies(self) -> list['Study']:
        """Returns the list of studies for the patient."""
        return sorted(self._studies, key=lambda x: x.study_date, reverse=True)

    @property
    def tag(self) -> str:
        """Returns the tag of the patient for use in the manager trees."""
        return "PT" + self.id_string

    @property
    def menu_options(self) -> list[tuple[str, Callable[[], None]]]:
        """Returns the menu options for the patient."""
        return []

    def add_study(self, study: 'Study'):
        """
        Adds a study to the patient.

        Parameters
        ----------
        study : Study
            The study to add.
        """
        self._studies.add(study)


class Study:
    """
    Represents a DICOM study.

    Parameters
    ----------
    patient : Patient
        The patient associated with the study.
    study_id : str
        The ID of the study.
    study_date : datetime.date
        The date of the study.
    study_desc : str
        The description of the study.

    Attributes
    ----------
    patient : Patient
        The patient associated with the study.
    study_id : str
        The ID of the study.
    study_date : datetime.date
        The date of the study.
    study_description : str
        The description of the study.
    series : list[Series]
    tag : str
    id_string : str
    menu_options : list[tuple[str, Callable[[], None]]]

    Methods
    -------
    add_series(series: Series)
        Adds a series to the study.
    """

    def __init__(self,
                 patient: Patient,
                 study_id: str,
                 study_date: datetime.date,
                 study_desc: str) -> None:
        self.patient: Patient = patient
        self.study_id: str = study_id
        self.study_date: datetime.date = study_date
        self.study_description: str = study_desc
        self._series: set[Series] = set()

    def __hash__(self) -> int:
        return hash(self.id_string)

    def __eq__(self, value: object) -> bool:
        """
        Checks equality with another object.

        Parameters
        ----------
        value : object
            The object to compare with.

        Returns
        -------
        bool
            True if equal, False otherwise.
        """
        if isinstance(value, Study):
            return self.study_id == value.study_id
        elif isinstance(value, str):
            return self.id_string == value
        elif isinstance(value, int):
            return hash(self) == value
        else:
            return False

    def __str__(self) -> str:
        """Returns the string representation of the study."""
        return self.study_date.strftime("%d/%m/%Y") + ": " + self.study_description

    @property
    def id_string(self) -> str:
        """Returns the ID string of the study."""
        return self.patient.id_string + " : " + self.study_id

    @property
    def series(self) -> list['Series']:
        """Returns the list of series for the study."""
        return sorted(self._series, key=lambda x: (x.series_number, x.acquisition_number))

    @property
    def tag(self) -> str:
        """Returns the tag of the study for use in the manager trees."""
        return "ST" + self.id_string

    @property
    def menu_options(self) -> list[tuple[str, Callable[[], None]]]:
        """Returns the menu options for the study."""
        return []

    def add_series(self, series: 'Series'):
        """
        Adds a series to the study.

        Parameters
        ----------
        series : Series
            The series to add.
        """
        self._series.add(series)


class Series(ImageCollection):
    """
    Represents a DICOM series.
    Has the same attributes and methods as ImageCollection unless stated below.

    Parameters
    ----------
    study : Study
        The study associated with the series.
    series_id : str
        The ID of the series.
    series_number : int
        The number of the series.
    acquisition_number : int
        The acquisition number of the series.
    series_description : str
        The description of the series.
    is_stack : bool, optional
        Whether the series is a stack (default is False).
    open_dicom : pydicom.Dataset, optional
        The open DICOM dataset (default is None).
    filepath : Path, optional
        The file path of the series (default is None).

    Attributes
    ----------
    study : Study
        The study associated with the series.
    series_id : str
        The ID of the series.
    series_number : int
        The number of the series.
    acquisition_number : int
        The acquisition number of the series.
    series_description : str
        The description of the series.
    is_stack : bool
        Whether the series is a stack.
    loaded : bool
        Whether the series is loaded.
    dicom_dataset : pydicom.Dataset | None
    instances : list[Instance]
    raw_array : np.ndarray

    Methods
    -------
    add_instance(instance: 'Instance')
        Adds an instance to the series.
    load()
        Loads the series from the series filepath.
    unload()
        Unloads the series.
    get_tags(tag: Tag) -> list
        Gets the values of a dicom tag for all instances in the series.
    get_tag(tag: Tag, instance_number: int)
        Gets the value of a tag for a specific instance in the series.
    """

    def __init__(self,
                 study: Study,
                 series_id: str,
                 series_number: int,
                 acquisition_number: int,
                 series_description: str,
                 is_stack: bool = False,
                 open_dicom: pydicom.Dataset | None = None,
                 filepath: Path | None = None) -> None:
        self.study: Study = study
        self.series_id: str = series_id
        self.series_number: int = series_number
        self.acquisition_number: int = acquisition_number
        self.series_description: str = series_description
        self.is_stack: bool = is_stack

        self._filepath: Path | None = copy(filepath)
        self.loaded: bool = False
        self._dicom: pydicom.Dataset | None = None

        if self.is_stack:
            if self._filepath is None:
                raise FileNotFoundError(
                    "a valid filepath must be provided for stack")
            if open_dicom is None:
                try:
                    open_dicom = dcmread(self._filepath)
                except InvalidDicomError as exc:
                    raise InvalidDicomError(
                        "filepath must be a valid DICOM file") from exc
                if get_tag(open_dicom, DicomTags.SamplesPerPixel).value == 1:
                    super().__init__(open_dicom.pixel_array.shape, False, False)
                else:
                    super().__init__(open_dicom.pixel_array.shape, True, True)
            else:
                if get_tag(open_dicom, DicomTags.SamplesPerPixel).value == 1:
                    super().__init__(open_dicom.pixel_array.shape, False, False)
                else:
                    super().__init__(open_dicom.pixel_array.shape, True, True)
        else:
            super().__init__((0, 0, 0), False, False)

        self._image_set: set[Instance] = set()

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Series):
            return hash(self) == hash(value)
        elif isinstance(value, int):
            return hash(self) == value
        elif isinstance(value, str):
            return self.id_string == value
        else:
            return False

    def __str__(self) -> str:
        return (str(self.series_number)
                + "-" + str(self.acquisition_number)
                + ":" + str(self.series_description))

    def __hash__(self) -> int:
        # from docs: A class that overrides __eq__() and does not define __hash__()
        # will have its __hash__() implicitly set to None.
        return super().__hash__()

    @property
    def id_string(self) -> str:
        return self.study.id_string + " : " + self.series_id + "-" + str(self.acquisition_number)

    @property
    def tag(self) -> str:
        return "SR" + self.id_string

    @property
    def filepath(self) -> Path:
        if self._filepath is None:
            return self.current_image.filepath
        else:
            return self._filepath

    @property
    def current_image(self) -> 'Instance':
        return self.instances[self.current_slice]

    @property
    def instances(self) -> list['Instance']:
        """Returns the list of instances for the series."""
        return sorted(self._image_set, key=lambda x: x.sort_value)

    @property
    def image_set(self) -> list['Instance']:
        """For Series this is equivelant to the `instances` property."""
        return self.instances

    @property
    def raw_array(self
                  ) -> np.ndarray[tuple[int, int, int, Literal[3]]
                                  | tuple[int, int, int],
                                  np.dtype]:
        """Returns the raw array of the series as stored in the dicom file.
        This is usually an unsigned dtype so users should be careful when processing."""
        if not self.loaded:
            self.load()
        if self.is_stack and self._dicom is not None:
            return self._dicom.pixel_array
        else:
            return np.concatenate([a.raw_array for a in self.instances])  # type: ignore

    @property
    def array(self
              ) -> np.ndarray[tuple[int, int, int, Literal[3]]
                              | tuple[int, int, int],
                              np.dtype]:
        """Returns the array of the series with corrections defined by the slope and intercept tags.
        If there are no slope and intercept tags then this is equivelant to `raw_array`.
        Accessed through (slice, y-position, x-position[, multisample/RGB values])
        """
        if not self.loaded:
            self.load()
        if self.is_stack:
            raw_array = np.astype(self.raw_array, float)
            if self.get_tag(DicomTags.SamplesPerPixel, 0) == 1:
                try:
                    slope = self.get_tag(DicomTags.RescaleSlope, 0)
                    intercept = self.get_tag(DicomTags.RescaleIntercept, 0)
                    return raw_array * slope + intercept
                except KeyError:
                    return raw_array
            else:
                try:
                    photo_interp = self.get_tag(
                        DicomTags.PhotometricInterpretation, 0)
                    if isinstance(photo_interp, str):
                        return np.astype(convert_color_space(self.raw_array,
                                                             photo_interp,
                                                             'RGB'),
                                         float)
                    else:
                        return raw_array
                except (KeyError, NotImplementedError):
                    return raw_array
        else:
            return np.concatenate([a.array for a in self.instances])  # type: ignore

    @property
    def vmax(self) -> float | None:
        """Returns the default maximum value for the viewing LUT (i.e. white on a grey scale image).
        Calculated from the the window center and width tags.
        This is **not** normally the maximum value in the image,
        however if the relevant tags are not available then this is the fallback."""
        try:
            window_width = self.get_tag(
                DicomTags.WindowWidth, self.current_slice)
            window_center = self.get_tag(
                DicomTags.WindowCenter, self.current_slice)
            if window_center is not None and window_width is not None:
                vmax = window_center + (window_width / 2)
            else:
                raise TypeError("Could not get window width or window center.")
        except TypeError:
            vmax = super().vmax
        except KeyError:
            vmax = super().vmax
        return vmax

    @property
    def vmin(self) -> float | None:
        """Returns the default minimum value for the viewing LUT (i.e. black on a grey scale image).
        Calculated from the the window center and width tags.
        This is **not** normally the minimum value in the image,
        however if the relevant tags are not available then this is the fallback."""
        try:
            window_width = self.get_tag(
                DicomTags.WindowWidth, self.current_slice)
            window_center = self.get_tag(
                DicomTags.WindowCenter, self.current_slice)
            if window_center is not None and window_width is not None:
                vmin = window_center - (window_width / 2)
            else:
                raise TypeError("Could not get window width or window center.")
        except TypeError:
            vmin = super().vmin
        except KeyError:
            vmin = super().vmin
        return vmin

    @property
    def window(self) -> float | None:
        """Returns the default window width from the window width tag.
        If this is not available then it is calculated from the array min and max values."""
        try:
            window = self.get_tag(DicomTags.WindowWidth, self.current_slice)
            if window is not None:
                return float(window)
            else:
                return super().window
        except KeyError:
            return super().window
        except IndexError:
            return super().window
        except TypeError:
            return super().window

    @property
    def level(self) -> float | None:
        """Returns the default level (window centre) from the window center tag.
        If this is not available then it is calculated from the array min and max values."""
        try:
            level = self.get_tag(DicomTags.WindowCenter, self.current_slice)
            if level is not None:
                return float(level)
            else:
                return super().level
        except KeyError:
            return super().level
        except IndexError:
            return super().level

    @property
    def pixel_size(self) -> tuple[float, float, float]:
        """Returns the pixel size of the series in mm as a tuple of 3 floats.
        (slice_thickness, row_spacing, column_spacing)
        """
        try:
            pixel_spacing = self.get_tag(
                DicomTags.PixelSpacing, self.current_slice)
        except KeyError:
            pixel_spacing = (1, 1)
        try:
            slice_thickness = self.get_tag(
                DicomTags.SliceThickness, self.current_slice)
        except KeyError:
            slice_thickness = 1

        if pixel_spacing is None:
            pixel_spacing = (1, 1)
        if slice_thickness is None:
            slice_thickness = 1

        try:
            row_spacing = pixel_spacing[0]
            column_spacing = pixel_spacing[1]
        except TypeError:
            return (slice_thickness, 1, 1)

        return (slice_thickness, row_spacing, column_spacing)

    @property
    def dicom_dataset(self) -> pydicom.Dataset | None:
        """Returns the pydicom dataset of the series."""
        load_stat = self.loaded
        if not self.loaded:
            self.load()

        if self.is_stack:
            dcm = self._dicom
        else:
            dcm = self.instances[self.current_slice].dicom_dataset

        if not load_stat:
            self.unload()

        return dcm

    def add_instance(self, instance: 'Instance'):
        """
        Adds an instance to the series.

        Parameters
        ----------
        instance : Instance
            The instance to add.
        """
        if (self.num_slices == 0
            or (self.shape[1] == instance.shape[1]
                and self.shape[2] == instance.shape[2]
                and self.is_multisample == instance.is_multisample
                and self.is_rgb == instance.is_rgb)):
            self._image_set.add(instance)  # this line is different to parent
            self.shape = (len(self._image_set),
                          instance.shape[1],
                          instance.shape[2])
            self.is_multisample = instance.is_multisample  # for if num_slices == 0
            self.is_rgb = instance.is_rgb  # for if num_slices == 0
        else:
            raise ValueError("Instance incompatible with Series")

    def add_image(self, image: 'Instance'):
        if isinstance(image, Instance):
            self.add_instance(image)
        else:
            raise ValueError("Image must be an Instance")

    def load(self):
        """Loads the series from the series filepath."""
        if not self.loaded:
            if self.is_stack:
                if self.filepath is None:
                    raise FileNotFoundError("No valid filepath found")
                self._dicom = dcmread(self.filepath)
                for instance in self.instances:
                    instance.loaded = True
            else:
                for instance in self.instances:
                    instance.load()
            self.loaded = True

    def unload(self):
        """Unloads the series."""
        if self.loaded:
            if self.is_stack:
                self._dicom = None
                for instance in self.instances:
                    instance.loaded = False
            else:
                for instance in self.instances:
                    instance.unload()
            self.loaded = False

    def get_tags(self, tag: Tag) -> list:
        """
        Gets the values of a DICOM tag for all instances in the series.

        Parameters
        ----------
        tag : Tag
            The tag to get values for.

        Returns
        -------
        list
            The list of values for the tag.
        """
        load_stat = self.loaded
        if not self.loaded:
            self.load()

        values = []
        for instance in self.instances:
            values.append(instance.get_tag(tag))

        if not load_stat:
            self.unload()

        return values

    def get_tag(self, tag: Tag, instance_number: int):
        """
        Gets the value of a DICOM tag for a specific instance in the series.

        Parameters
        ----------
        tag : Tag
            The tag to get the value for.
        instance_number : int
            The instance number to get the tag value for.

        Returns
        -------
        The value of the tag.
        """
        if instance_number < self.num_slices:
            return self.instances[instance_number].get_tag(tag)
        else:
            raise IndexError("instance_number not valid")


class Instance(FileImageSet):
    """
    Represents a DICOM instance.
    Has the same attributes and methods as FileImageSet unless stated below.

    Parameters
    ----------
    series : Series
        The series associated with the instance.
    instance_number : int
        The number of the instance.
    filepath : Path, optional
        The file path of the instance (default is None).
    is_frame : bool, optional
        Whether the instance is a frame (default is False).
    frame_number : int, optional
        The frame number of the instance (default is None).
    dimension_index_values : list or tuple, optional
        The dimension index values of the instance (default is None).

    Attributes
    ----------
    series : Series
        The series associated with the instance.
    instance_number : int
        The number of the instance.
    is_frame : bool
        Whether the instance is a frame.
    frame_number : int | None
        The frame number of the instance.
    dimension_index_values : tuple | None
        The dimension index values of the instance.
    loaded : bool
        Whether the instance is loaded.
    dicom_dataset : pydicom.Dataset | None
    raw_array : np.ndarray

    Methods
    -------
    load()
        Loads the instance from the instance filepath.
    unload()
        Unloads the instance.
    get_tag(tag: Tag)
        Gets the value of a tag for the instance.
    """

    def __init__(self,
                 series: Series,
                 instance_number: int,
                 filepath: Path | None = None,
                 is_frame: bool = False,
                 frame_number: int | None = None,
                 dimension_index_values: list | tuple | None = None) -> None:
        self.series = series
        self.instance_number = instance_number

        self.is_frame = is_frame
        self.frame_number = frame_number

        if isinstance(dimension_index_values, list):
            self.dimension_index_values = tuple(dimension_index_values)
        else:
            self.dimension_index_values = dimension_index_values

        self.loaded = False
        self._dicom: pydicom.Dataset | None = None

        if self.is_frame:
            if series.filepath is None:
                raise FileNotFoundError(
                    "Series does not have a valid filepath")
            super().__init__(
                (series.shape[1], series.shape[2]),
                series.filepath,
                series.is_multisample,
                series.is_rgb)
        else:
            if filepath is None:
                raise FileNotFoundError("A valid filepath must be provided")
            try:
                open_dicom = dcmread(filepath)
            except InvalidDicomError as exc:
                raise InvalidDicomError(
                    "filepath must be a valid DICOM file") from exc
            if get_tag(open_dicom, DicomTags.SamplesPerPixel).value == 1:
                super().__init__(open_dicom.pixel_array.shape, filepath, False, False)
            else:
                super().__init__(open_dicom.pixel_array.shape, filepath, True, True)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Instance):
            return hash(self) == hash(value)
        elif isinstance(value, int):
            return hash(self) == value
        elif isinstance(value, str):
            return self.id_string == value
        else:
            return False

    def __str__(self) -> str:
        if self.is_frame:
            return str(self.frame_number)
        else:
            return str(self.instance_number)

    def __hash__(self) -> int:
        # from docs: A class that overrides __eq__() and does not define __hash__()
        # will have its __hash__() implicitly set to None.
        return super().__hash__()

    @property
    def id_string(self) -> str:
        return self.series.id_string + " : " + str(self)

    @property
    def tag(self) -> str:
        return "IN" + self.id_string

    @property
    def sort_value(self) -> int:
        """Returns the sort value of the instance."""
        if self.is_frame and self.frame_number is not None:
            return self.frame_number
        else:
            return self.instance_number

    @property
    def raw_array(self
                  ) -> np.ndarray[tuple[int, int, int, Literal[3]]
                                  | tuple[int, int, int],
                                  np.dtype]:
        """Returns the raw array of the instance as stored in the dicom file.
        This is usually an unsigned dtype so users should be careful when processing."""
        if not self.loaded:
            self.load()
        if self.is_frame and self.frame_number is not None:
            return np.array([self.series.raw_array[self.frame_number - 1]])  # type: ignore
        elif self._dicom is not None:
            return np.array([self._dicom.pixel_array])  # type: ignore
        else:
            return np.zeros((1, 1, 1))

    @property
    def array(self
              ) -> np.ndarray[tuple[int, int, int, Literal[3]]
                              | tuple[int, int, int],
                              np.dtype]:
        """Returns the array with corrections defined by the slope and intercept tags.
        If there are no slope and intercept tags then this is equivelant to `raw_array`.
        Accessed through (slice, y-position, x-position[, multisample/RGB values])
        """
        if not self.loaded:
            self.load()
        if self.is_frame and self.frame_number is not None:
            return np.array([self.series.array[self.frame_number - 1]])  # type: ignore
        else:
            raw_array = np.astype(self.raw_array, float)
            if self.get_tag(DicomTags.SamplesPerPixel) == 1:
                try:
                    slope = self.get_tag(DicomTags.RescaleSlope)
                    intercept = self.get_tag(DicomTags.RescaleIntercept)
                    return raw_array * slope + intercept
                except KeyError:
                    return raw_array
            else:
                try:
                    photo_interp = self.get_tag(
                        DicomTags.PhotometricInterpretation)
                    if isinstance(photo_interp, str):
                        return np.astype(convert_color_space(self.raw_array,
                                                             photo_interp,
                                                             'RGB'),
                                         float)
                    else:
                        return raw_array
                except (KeyError, NotImplementedError):
                    return raw_array

    @property
    def vmax(self) -> float | None:
        """Returns the default maximum value for the viewing LUT (i.e. white on a grey scale image).
        Calculated from the the window center and width tags.
        This is **not** normally the maximum value in the image,
        however if the relevant tags are not available then this is the fallback."""
        try:
            window_width = self.get_tag(DicomTags.WindowWidth)
            window_center = self.get_tag(DicomTags.WindowCenter)
            if window_center is not None and window_width is not None:
                vmax = window_center + (window_width / 2)
            else:
                raise TypeError("Could not get window width or window center.")
        except TypeError:
            vmax = super().vmax
        except KeyError:
            vmax = super().vmax
        return vmax

    @property
    def vmin(self) -> float | None:
        """Returns the default minimum value for the viewing LUT (i.e. black on a grey scale image).
        Calculated from the the window center and width tags.
        This is **not** normally the minimum value in the image,
        however if the relevant tags are not available then this is the fallback."""
        try:
            window_width = self.get_tag(DicomTags.WindowWidth)
            window_center = self.get_tag(DicomTags.WindowCenter)
            if window_center is not None and window_width is not None:
                vmin = window_center - (window_width / 2)
            else:
                raise TypeError("Could not get window width or window center.")
        except TypeError:
            vmin = super().vmin
        except KeyError:
            vmin = super().vmin
        return vmin

    @property
    def window(self) -> float | None:
        """Returns the default window width from the window width tag.
        If this is not available then it is calculated from the array min and max values."""
        try:
            return self.get_tag(DicomTags.WindowWidth)
        except KeyError:
            return super().window
        except IndexError:
            return super().window

    @property
    def level(self) -> float | None:
        """Returns the default level (window centre) from the window center tag.
        If this is not available then it is calculated from the array min and max values."""
        try:
            return self.get_tag(DicomTags.WindowCenter)
        except KeyError:
            return super().level
        except IndexError:
            return super().level

    @property
    def pixel_size(self) -> tuple[float, float, float]:
        """Returns the pixel size of the instance in mm as a tuple of 3 floats.
        (slice_thickness, row_spacing, column_spacing)
        """
        try:
            pixel_spacing = self.get_tag(DicomTags.PixelSpacing)
        except KeyError:
            pixel_spacing = (1, 1)
        try:
            slice_thickness = self.get_tag(DicomTags.SliceThickness)
        except KeyError:
            slice_thickness = 1

        if pixel_spacing is None:
            pixel_spacing = (1, 1)
        if slice_thickness is None:
            slice_thickness = 1

        try:
            row_spacing = pixel_spacing[0]
            column_spacing = pixel_spacing[1]
        except TypeError:
            return (slice_thickness, 1, 1)

        return (slice_thickness, row_spacing, column_spacing)

    @property
    def dicom_dataset(self) -> pydicom.Dataset | None:
        """Returns the pydicom dataset of the instance."""
        load_stat = self.loaded
        if not self.loaded:
            self.load()

        if self.is_frame:
            dcm = self.series.dicom_dataset
        else:
            dcm = self._dicom

        if not load_stat:
            self.unload()

        return dcm

    def load(self):
        """Loads the instance from the instance filepath."""
        if not self.loaded:
            if self.is_frame:
                self.series.load()
            else:
                self._dicom = dcmread(self.filepath)
            self.loaded = True

    def unload(self):
        """Unloads the instance."""
        if self.loaded:
            if self.is_frame:
                self.series.unload()
            else:
                self._dicom = None
            self.loaded = False

    def get_tag(self, tag: Tag):
        """
        Gets the value of a DICOM tag for the instance.

        Parameters
        ----------
        tag : Tag
            The tag to get the value for.

        Returns
        -------
        The value of the tag.
        """
        load_stat = self.loaded
        if not self.loaded:
            self.load()

        value = None
        if self.is_frame and self.frame_number is not None:
            dataset = self.series.dicom_dataset
            if dataset is not None:
                value = get_tag(dataset, tag, self.frame_number).value
            else:
                value = None
        else:
            dataset = self.dicom_dataset
            if dataset is not None:
                value = get_tag(dataset, tag).value
            else:
                value = None

        if not load_stat:
            self.unload()

        return value
