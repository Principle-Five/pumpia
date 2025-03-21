PumpIA documentation
====================

Introduction
------------

PumpIA is a python framework designed to allow users to visualise the analysis of images through a user interface.
It does not do any image analysis itself, but rather provides a platform for users to write their own analysis code and view the results.
This means that the full power of python and its libraries are available to the user.

Requirements
------------
PumpIA has been designed to use the minimum number of dependencies, so the user interface relies on `tkinter <https://docs.python.org/3/library/tkinter.html>`_.
PumpIA has the following dependencies:

* `numpy <https://numpy.org/>`_
* `scipy <https://scipy.org/>`_
* `pillow <https://pillow.readthedocs.io/en/stable/>`_
* `pydicom <https://pydicom.github.io/pydicom/stable/>`_
* `matplotlib <https://matplotlib.org/>`_

See `pydicom: Compression of Pixel Data <https://pydicom.github.io/pydicom/stable/tutorials/pixel_data/compressing.html#compression-of-pixel-data>`_ for information on how to install the required libraries for reading compressed dicom files.

Installation
------------

PumpIA requires `python <https://www.python.org>`_ 3.12 or greater.
To use PumpIA, install it using pip:

.. code-block:: console

   (.venv) $ pip install pumpia

Contents
--------

.. toctree::
   :includehidden:
   :titlesonly:
   :maxdepth: 2

   components/components
   usage/usage
   file_handling/file_handling
   utilities/utilities
   widgets/widgets
