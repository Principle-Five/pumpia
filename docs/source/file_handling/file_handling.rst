File Handling
=============

The :doc:`manager </components/manager>` is used to handle files and make sure all components have access to the loaded ones.

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
    dicoms
    dicom_tags
