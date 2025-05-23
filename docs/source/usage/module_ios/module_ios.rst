Module Inputs and Outputs
=========================

:doc:`simple`
-------------
Simple IOs represent the following:

    * Strings
    * Integers
    * Floats
    * Dates

Inputs can also be options or booleans.

Outputs are reset before analysis if their ``reset_on_analysis`` parameter is set to ``True``, this may be useful for debugging.

Labels are automatically generated by replacing underscores with spaces and capitalising words, unless provided by ``verbose_name``.
For inputs the ttk style for the label and entry can be provided.
For outputs the ttk style for the name and value labels can be provided seperatly.

:doc:`groups`
-------------
``IOGroup`` can only be used with collections.
Put them in the ``load_outputs`` method of the collection.

:doc:`viewer_ios`
-----------------
Viewer IOs have the same parameters as :py:class:`Viewers <pumpia.widgets.viewers.BaseViewer>`, with the addition of the row and column that to position the viewer.
The following viewer IOs are provided:

    * :py:class:`ViewerIO <pumpia.module_handling.in_outs.viewer_ios.ViewerIO>`
    * :py:class:`ArrayViewerIO <pumpia.module_handling.in_outs.viewer_ios.ArrayViewerIO>`
    * :py:class:`MonochromeViewerIO <pumpia.module_handling.in_outs.viewer_ios.MonochromeViewerIO>`
    * :py:class:`DicomViewerIO <pumpia.module_handling.in_outs.viewer_ios.DicomViewerIO>`
    * :py:class:`MonochromeDicomViewerIO <pumpia.module_handling.in_outs.viewer_ios.MonochromeDicomViewerIO>`

:doc:`roi_ios`
--------------
If an :doc:`ROI </components/rois>` is generated procedurally then it must be registered with the relevant input using ``register_roi`` to access it in the user interface.
A registered ROI can be accessed through the ``roi`` attribute.

The following ROI IOs are provided:

    * :py:class:`InputGeneralROI <pumpia.module_handling.in_outs.roi_ios.InputGeneralROI>`
    * :py:class:`InputRectangleROI <pumpia.module_handling.in_outs.roi_ios.InputRectangleROI>`
    * :py:class:`InputEllipseROI <pumpia.module_handling.in_outs.roi_ios.InputEllipseROI>`
    * :py:class:`InputLineROI <pumpia.module_handling.in_outs.roi_ios.InputLineROI>`
    * :py:class:`InputAngle <pumpia.module_handling.in_outs.roi_ios.InputAngle>`
    * :py:class:`InputPointROI <pumpia.module_handling.in_outs.roi_ios.InputPointROI>`

Contents
--------
.. toctree::
    simple
    groups
    viewer_ios
    roi_ios
