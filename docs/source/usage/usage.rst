Usage
=====

See :doc:`example` for an implementation of the below.

:doc:`modules`
--------------
This is how most people will write analysis programs using PumpIA.
Modules automatically handle the user interface aspect of the program.
When subclassing one of the provided modules the user must overwrite :py:meth:`analyse <pumpia.module_handling.modules.BaseModule.analyse>`, however the following are also designed to be replaced or extended:

    * :py:meth:`draw_rois <pumpia.module_handling.modules.BaseModule.draw_rois>`
    * :py:meth:`load_commands <pumpia.module_handling.modules.BaseModule.load_commands>`
    * :py:meth:`link_rois_viewers <pumpia.module_handling.modules.BaseModule.link_rois_viewers>`
    * :py:meth:`post_roi_register <pumpia.module_handling.modules.BaseModule.post_roi_register>`
    * :py:meth:`on_image_load <pumpia.module_handling.modules.BaseModule.on_image_load>`

The class method :py:meth:`run <pumpia.module_handling.modules.BaseModule.run>` is used to run the module as a stand alone.

:doc:`module_ios/module_ios`
----------------------------
These allow users to provide information to and get information out of the module.
There are three categories of IOs:

    * :doc:`Simple IOs <module_ios/simple>` handle IOs such as strings, options, numbers, and dates. These can be linked through :py:class:`IOGroup <pumpia.module_handling.in_outs.groups.IOGroup>` so that multiple IOs always have the same value.
    * :doc:`Viewer IOs <module_ios/viewer_ios>` represent viewers. These become viewers on module setup as well.
    * :doc:`ROI IOs <module_ios/roi_ios>` handle ROIs created and used by the module.

:doc:`context`
--------------
Context is used to pass information into the module for drawing ROIs.
In the user interface collections of widgets called `context managers` use the modules ``main_viewer`` to generate the context.
Each context manager requires a `context manager generator` which is used to create the context manager when running the module, this is set using the ``context_manager_generator`` class attribute.
Alternatively a modules `get_context` method can be overwritten.

Three context managers and generators are provided:

    * :py:class:`BaseContextManager <pumpia.widgets.context_managers.BaseContextManager>` : :py:class:`BaseContextManagerGenerator <pumpia.widgets.context_managers.BaseContextManagerGenerator>`
    * :py:class:`ManualPhantomManager <pumpia.widgets.context_managers.ManualPhantomManager>` : :py:class:`ManualPhantomManagerGenerator <pumpia.widgets.context_managers.ManualPhantomManagerGenerator>`
    * :py:class:`AutoPhantomManager <pumpia.widgets.context_managers.AutoPhantomManager>` : :py:class:`AutoPhantomManagerGenerator <pumpia.widgets.context_managers.AutoPhantomManagerGenerator>`

When creating your own context manager you must provide the :py:meth:`get_context <pumpia.widgets.context_managers.BaseContextManager.get_context>` method.

:doc:`collections`
------------------
Collections are used to group modules together, with a main tab showing the context and any defined viewers.
Only :doc:`viewer IOs <module_ios/viewer_ios>` can be used with collections, any others will be ignored/wont function as expected.

Similar to modules they have context which is shared across all the modules in the collection.
The ``context_manager_generator`` class attribute must be defined for collections.

Collections introduce two other useful classes:

    * :py:class:`OutputFrame <pumpia.module_handling.module_collections.OutputFrame>` which shows outputs from different modules in the main tab for ease of viewing.
    * :py:class:`WindowGroup <pumpia.module_handling.module_collections.WindowGroup>` which shows multiple modules in the same tab instead of showing them across multiple tabs.

When subclassing :py:class:`BaseCollection <pumpia.module_handling.module_collections.BaseCollection>` the following methods are designed to be overwritten:

    * :py:meth:`load_outputs <pumpia.module_handling.module_collections.BaseCollection.load_outputs>`
    * :py:meth:`load_commands <pumpia.module_handling.module_collections.BaseCollection.load_commands>`
    * :py:meth:`on_image_load <pumpia.module_handling.module_collections.BaseCollection.on_image_load>`


Contents
--------
.. toctree::
    example
    modules
    module_ios/module_ios
    collections
    context
