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
        return sorted(self._series, key=lambda x: x.sort_value)

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
    series_description : str
        The description of the series.
    series_number : int
        The number of the series.
    acquisition_number : int
        The acquisition number of the series.
    instance_number : int
        The instance number of the series.
        Required if series is a stack, ignored otherwise.
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
    instance_number : int
        The instance number of the series.
        Int if series is a stack, None otherwise.
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
    get_tags(tag: Tag) -> list
        Gets the values of a dicom tag for all instances in the series.
    get_tag(tag: Tag, instance_number: int)
        Gets the value of a tag for a specific instance in the series.
    """

    def __init__(self,
                 study: Study,
                 series_id: str,
                 series_description: str,
                 series_number: int,
                 acquisition_number: int,
                 instance_number: int | None = None,
                 is_stack: bool = False,
                 open_dicom: pydicom.Dataset | None = None,
                 filepath: Path | None = None) -> None:
        self.study: Study = study
        self.series_id: str = series_id
        self.series_number: int = series_number
        self.acquisition_number: int = acquisition_number
        self.series_description: str = series_description
        self.is_stack: bool = is_stack

        if self.is_stack:
            if instance_number is None:
                raise ValueError("instance number must be provided for stack")
            self.instance_number: int | None = instance_number
        else:
            self.instance_number = None

        self._filepath: Path | None = copy(filepath)

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
            num_samples = get_tag(open_dicom, DicomTags.SamplesPerPixel).value
            try:
                photo_interp = get_tag(open_dicom, DicomTags.PhotometricInterpretation).value
            except KeyError:
                photo_interp = None
            if num_samples == 1:
                super().__init__(open_dicom.pixel_array.shape)
            elif isinstance(photo_interp, str):
                super().__init__(open_dicom.pixel_array.shape, num_samples, "RGB")
            else:
                super().__init__(open_dicom.pixel_array.shape, num_samples)

        else:
            super().__init__((0, 0, 0))

        self._dicom: pydicom.Dataset | None = open_dicom
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
        if self.is_stack:
            return (str(self.series_number)
                    + "-" + str(self.acquisition_number)
                    + "-" + str(self.instance_number)
                    + ":" + str(self.series_description))
        return (str(self.series_number)
                + "-" + str(self.acquisition_number)
                + ":" + str(self.series_description))

    def __hash__(self) -> int:
        # from docs: A class that overrides __eq__() and does not define __hash__()
        # will have its __hash__() implicitly set to None.
        return super().__hash__()

    @property
    def id_string(self) -> str:
        if self.is_stack:
            return (self.study.id_string
                    + " : " + self.series_id
                    + "-" + str(self.acquisition_number)
                    + "-" + str(self.instance_number))
        else:
            return (self.study.id_string
                    + " : " + self.series_id
                    + "-" + str(self.acquisition_number))

    @property
    def tag(self) -> str:
        return "SR" + self.id_string

    @property
    def sort_value(self) -> tuple[int, int] | tuple[int, int, int]:
        """Returns the sort value of the series."""
        if self.is_stack and self.instance_number is not None:
            return (self.series_number, self.acquisition_number, self.instance_number)
        else:
            return (self.series_number, self.acquisition_number)

    @property
    def filepath(self) -> Path:
        """
        The file path of the current image for the series.
        """
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
        if self.is_stack and self._dicom is not None:
            return self._dicom.pixel_array
        else:
            return np.concatenate([a.raw_array for a in self.instances])  # type: ignore

    @property
    def image_array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        """Returns an array suitable for passing to the viewer"""
        if self.is_stack:
            raw_array = self.raw_array
            if not self.is_colour:
                try:
                    slope = self.get_tag(DicomTags.RescaleSlope)
                    intercept = self.get_tag(DicomTags.RescaleIntercept)
                    return raw_array * slope + intercept
                except KeyError:
                    return raw_array
            else:
                try:
                    photo_interp = self.get_tag(DicomTags.PhotometricInterpretation)
                    if isinstance(photo_interp, str):
                        if photo_interp != "RGB":
                            return convert_color_space(self.raw_array,
                                                       photo_interp,
                                                       'RGB')
                        else:
                            return raw_array
                    else:
                        try:
                            slope = self.get_tag(DicomTags.RescaleSlope)
                            intercept = self.get_tag(DicomTags.RescaleIntercept)
                            return raw_array * slope + intercept
                        except KeyError:
                            return raw_array
                except (KeyError, NotImplementedError):
                    try:
                        slope = self.get_tag(DicomTags.RescaleSlope)
                        intercept = self.get_tag(DicomTags.RescaleIntercept)
                        return raw_array * slope + intercept
                    except KeyError:
                        return raw_array
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
        if self.is_stack:
            raw_array = np.astype(self.raw_array, float)
            if not self.is_colour:
                try:
                    slope = self.get_tag(DicomTags.RescaleSlope)
                    intercept = self.get_tag(DicomTags.RescaleIntercept)
                    return raw_array * slope + intercept
                except KeyError:
                    return raw_array
            else:
                try:
                    photo_interp = self.get_tag(DicomTags.PhotometricInterpretation)
                    if isinstance(photo_interp, str):
                        if photo_interp != "RGB":
                            return np.astype(convert_color_space(self.raw_array,
                                                                 photo_interp,
                                                                 'RGB'),
                                             float)
                        else:
                            return raw_array
                    else:
                        try:
                            slope = self.get_tag(DicomTags.RescaleSlope)
                            intercept = self.get_tag(DicomTags.RescaleIntercept)
                            return raw_array * slope + intercept
                        except KeyError:
                            return raw_array
                except (KeyError, NotImplementedError):
                    try:
                        slope = self.get_tag(DicomTags.RescaleSlope)
                        intercept = self.get_tag(DicomTags.RescaleIntercept)
                        return raw_array * slope + intercept
                    except KeyError:
                        return raw_array
        else:
            return np.concatenate([a.array for a in self.instances])  # type: ignore

    @property
    def current_slice_array(self) -> np.ndarray[tuple[int, int, int] | tuple[int, int], np.dtype]:
        """
        The array representation of the current slice.
        """
        return self.instances[self.current_slice].current_slice_array

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
            window = self.get_tag(DicomTags.WindowWidth)
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
            level = self.get_tag(DicomTags.WindowCenter)
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
        """Returns the pydicom dataset of the series."""
        if self.is_stack:
            dcm = self._dicom
        else:
            dcm = self.instances[self.current_slice].dicom_dataset

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
                and self.num_samples == instance.num_samples
                and self.mode == instance.mode)):
            self._image_set.add(instance)  # this line is different to parent
            self.shape = (len(self._image_set),
                          instance.shape[1],
                          instance.shape[2])
            self.num_samples = instance.num_samples  # for if num_slices == 0
            self.mode = instance.mode  # for if num_slices == 0
        else:
            raise ValueError("Instance incompatible with Series")

    def add_image(self, image: 'Instance'):
        if isinstance(image, Instance):
            self.add_instance(image)
        else:
            raise ValueError("Image must be an Instance")

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
        values = []
        for instance in self.instances:
            values.append(instance.get_tag(tag))

        return values

    def get_tag(self, tag: Tag, instance_number: int | None = None):
        """
        Gets the value of a DICOM tag for a specific instance in the series.

        Parameters
        ----------
        tag : Tag
            The tag to get the value for.
        instance_number : int | None
            The instance number to get the tag value for.
            If None uses the current instance (default is None).

        Returns
        -------
        The value of the tag.
        """
        if instance_number is None:
            instance_number = self.current_slice
        if instance_number < self.num_slices:
            return self.instances[instance_number].get_tag(tag)
        else:
            raise IndexError("instance_number not valid")


class Instance(FileImageSet):
    """
    Represents a DICOM instance if file has 1 frame or a frame if file has multiple frames.
    Has the same attributes and methods as FileImageSet unless stated below.

    Parameters
    ----------
    series : Series
        The series associated with the instance.
    slice_number : int
        The slice number of the instance.
        For a frame this will be the frame number, otherwise this will be the instance number.
    filepath : Path, optional
        The file path of the instance (default is None).
    is_frame : bool, optional
        Whether the instance is a frame (default is False).
    dimension_index_values : list or tuple, optional
        The dimension index values of the instance (default is None).

    Attributes
    ----------
    series : Series
        The series associated with the instance.
    slice_number : int
        The slice number of the instance.
    is_frame : bool
        Whether the instance is a frame.
    dimension_index_values : tuple | None
        The dimension index values of the instance.
    loaded : bool
        Whether the instance is loaded.
    dicom_dataset : pydicom.Dataset | None
    raw_array : np.ndarray

    Methods
    -------
    get_tag(tag: Tag)
        Gets the value of a tag for the instance.
    """

    def __init__(self,
                 series: Series,
                 slice_number: int,
                 filepath: Path | None = None,
                 is_frame: bool = False,
                 dimension_index_values: list | tuple | None = None,
                 open_dicom: pydicom.Dataset | None = None,) -> None:
        self.series: Series = series

        self.is_frame: bool = is_frame

        self.slice_number: int = slice_number

        if isinstance(dimension_index_values, list):
            self.dimension_index_values = tuple(dimension_index_values)
        else:
            self.dimension_index_values = dimension_index_values

        self.loaded: bool = False

        if self.is_frame:
            if series.filepath is None:
                raise FileNotFoundError(
                    "Series does not have a valid filepath")
            super().__init__(
                (series.shape[1], series.shape[2]),
                series.filepath,
                series.num_samples,
                series.mode)
        else:
            if filepath is None:
                raise FileNotFoundError("A valid filepath must be provided")
            if open_dicom is None:
                try:
                    open_dicom = dcmread(filepath)
                except InvalidDicomError as exc:
                    raise InvalidDicomError(
                        "filepath must be a valid DICOM file") from exc
            num_samples = get_tag(open_dicom, DicomTags.SamplesPerPixel).value
            try:
                photo_interp = get_tag(open_dicom, DicomTags.PhotometricInterpretation).value
            except KeyError:
                photo_interp = None
            if num_samples == 1:
                super().__init__(open_dicom.pixel_array.shape, filepath)
            elif isinstance(photo_interp, str):
                super().__init__(open_dicom.pixel_array.shape, filepath, num_samples, "RGB")
            else:
                super().__init__(open_dicom.pixel_array.shape, filepath, num_samples)

        self._dicom: pydicom.Dataset | None = open_dicom

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
        return str(self.slice_number)

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
        return self.slice_number

    @property
    def raw_array(self
                  ) -> np.ndarray[tuple[int, int, int, Literal[3]]
                                  | tuple[int, int, int],
                                  np.dtype]:
        """Returns the raw array of the instance as stored in the dicom file.
        This is usually an unsigned dtype so users should be careful when processing."""
        if self.is_frame:
            return np.array([self.series.raw_array[self.slice_number - 1]])  # type: ignore
        elif self._dicom is not None:
            return np.array([self._dicom.pixel_array])  # type: ignore
        else:
            return np.zeros((1, 1, 1), dtype=np.uint8)

    @property
    def image_array(self) -> np.ndarray[tuple[int, int, int, int] | tuple[int, int, int], np.dtype]:
        """Returns an array suitable for passing to the viewer"""
        raw_array = self.raw_array
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
                    if photo_interp != "RGB":
                        return convert_color_space(self.raw_array,
                                                   photo_interp,
                                                   'RGB')
                    else:
                        return raw_array
                else:
                    try:
                        slope = self.get_tag(DicomTags.RescaleSlope)
                        intercept = self.get_tag(DicomTags.RescaleIntercept)
                        return raw_array * slope + intercept
                    except KeyError:
                        return raw_array
            except (KeyError, NotImplementedError):
                try:
                    slope = self.get_tag(DicomTags.RescaleSlope)
                    intercept = self.get_tag(DicomTags.RescaleIntercept)
                    return raw_array * slope + intercept
                except KeyError:
                    return raw_array

    @property
    def array(self
              ) -> np.ndarray[tuple[int, int, int, Literal[3]]
                              | tuple[int, int, int],
                              np.dtype]:
        """Returns the array with corrections defined by the slope and intercept tags.
        If there are no slope and intercept tags then this is equivelant to `raw_array`.
        Accessed through (slice, y-position, x-position[, multisample/RGB values])
        """
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
                    if photo_interp != "RGB":
                        return np.astype(convert_color_space(self.raw_array,
                                                             photo_interp,
                                                             'RGB'), float)
                    else:
                        return raw_array
                else:
                    try:
                        slope = self.get_tag(DicomTags.RescaleSlope)
                        intercept = self.get_tag(DicomTags.RescaleIntercept)
                        return raw_array * slope + intercept
                    except KeyError:
                        return raw_array
            except (KeyError, NotImplementedError):
                try:
                    slope = self.get_tag(DicomTags.RescaleSlope)
                    intercept = self.get_tag(DicomTags.RescaleIntercept)
                    return raw_array * slope + intercept
                except KeyError:
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
        if self.is_frame:
            dcm = self.series.dicom_dataset
        else:
            dcm = self._dicom

        return dcm

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
        value = None
        if self.is_frame:
            dataset = self.series.dicom_dataset
            if dataset is not None:
                value = get_tag(dataset, tag, self.slice_number).value
            else:
                value = None
        else:
            dataset = self.dicom_dataset
            if dataset is not None:
                value = get_tag(dataset, tag).value
            else:
                value = None

        return value
