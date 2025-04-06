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

    * Patient
    * Study
    * Series
    * Instance

The DICOM file path and pydicom Dataset can be accessed through either `Series` or `Instance`.
For `Series` these will be for the current instance defined by the ``current_slice`` attribute.

:doc:`dicom_tags`
-----------------
DICOM tag handling is different to pydicom to allow for the handling of classic and enhanced DICOM files.

Contents
--------
.. toctree::
    general_images
    dicoms
    dicom_tags
