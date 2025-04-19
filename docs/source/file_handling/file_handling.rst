File Handling
=============

The :doc:`manager </components/manager>` is used to handle files and make sure all components have access to the loaded ones.

:doc:`general_images`
---------------------
Loaded general images can be accessed through the ``general_images`` attribute of the manager.
These are loaded in using Pillow, this means if Pillow can open the image then PumpIA should be able to as well.
The Pillow Image object does is not stored anywhere.

:doc:`dicoms`
-------------
Loaded DICOMS can be accessed through the ``patients`` attribute of the manager.
This provides a set of all patients loaded from DICOM files.

Four classes are used to group and handle DICOM files:

    * :py:class:`Patient <pumpia.file_handling.dicom_structures.Patient>`
    * :py:class:`Study <pumpia.file_handling.dicom_structures.Study>`
    * :py:class:`Series <pumpia.file_handling.dicom_structures.Series>`
    * :py:class:`Instance <pumpia.file_handling.dicom_structures.Instance>`

The DICOM file path and pydicom Dataset can be accessed through either
:py:class:`Series <pumpia.file_handling.dicom_structures.Series>` or :py:class:`Instance <pumpia.file_handling.dicom_structures.Instance>`.
For :py:class:`Series <pumpia.file_handling.dicom_structures.Series>` these will be for the current instance defined by the ``current_slice`` attribute.

:doc:`dicom_tags`
-----------------
DICOM tag handling is different to pydicom to allow for the handling of classic and enhanced DICOM files.
These are accessed through the ``get_tag`` method for a
:py:class:`Series <pumpia.file_handling.dicom_structures.Series>` or :py:class:`Instance <pumpia.file_handling.dicom_structures.Instance>`.
The user must pass in a :py:class:`Tag <pumpia.file_handling.dicom_tags.Tag>`, these represent DICOM tags.
DICOM tags given in the DICOM standard are available through the :py:mod:`dicom_tags <pumpia.file_handling.dicom_tags>` module.
These are available as class attributes for the following classes representing different modalities:

    * :py:class:`DicomTags <pumpia.file_handling.dicom_tags.DicomTags>` - Contains all tags. It is recommended to try one of the following first.
    * :py:class:`XRAYTags <pumpia.file_handling.dicom_tags.XRAYTags>`
    * :py:class:`CTTags <pumpia.file_handling.dicom_tags.CTTags>`
    * :py:class:`NucMedTags <pumpia.file_handling.dicom_tags.NucMedTags>`
    * :py:class:`MRTags <pumpia.file_handling.dicom_tags.MRTags>`
    * :py:class:`USTags <pumpia.file_handling.dicom_tags.USTags>`

For example given an MRI instance ``mr_image`` the following would get the echo time tag value.

.. code-block:: python

    from pumpia.file_handling.dicom_tags import MRTags

    echo_time = mr_image.get_tag(MRTags.EchoTime)


Contents
--------
.. toctree::
    general_images
    dicoms
    dicom_tags
