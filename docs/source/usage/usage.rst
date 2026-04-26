Usage
=====

See :doc:`example` for an implementation of the below.

:doc:`modules`
--------------
This is how most people will write analysis programs using PumpIA.
Modules automatically handle the user interface aspect of the program.
When subclassing one of the provided modules the following are designed to be replaced or extended:

    * :py:meth:`analyse <pumpia.module_handling.modules.BaseModule.analyse>`
    * :py:meth:`draw_rois <pumpia.module_handling.modules.BaseModule.draw_rois>`
    * :py:meth:`load_commands <pumpia.module_handling.modules.BaseModule.load_commands>`
    * :py:meth:`link_rois_viewers <pumpia.module_handling.modules.BaseModule.link_rois_viewers>`
    * :py:meth:`post_roi_register <pumpia.module_handling.modules.BaseModule.post_roi_register>`
    * :py:meth:`on_image_load <pumpia.module_handling.modules.BaseModule.on_image_load>`

The class method :py:meth:`run <pumpia.module_handling.modules.BaseModule.run>` is used to run the module as a stand alone.

The ``context_manager`` class attribute can be defined for modules, it defaults to :py:class:`SimpleContextManagerGenerator <pumpia.widgets.context_managers.SimpleContextManager>`.
If the class attribute ``show_draw_rois_button`` is set to ``True`` then a button to draw ROIs is shown.
If the class attribute ``show_analyse_button`` is set to ``True`` then a button to analyse the image is shown.
If both are set to ``True`` then a button to do both is also shown.
The ``title`` class attribute is shown in the window title, this defaults to ``Pumpia Module``.

:doc:`fields/fields`
----------------------------
These allow users to provide information to and get information out of the module.
There are three categories of IOs:

    * :doc:`Simple fields <fields/simple>` handle data such as strings, options, numbers, booleans, and dates.
        These can be linked through :py:class:`FieldGroup <pumpia.module_handling.fields.groups.FieldGroup>` in collections so that multiple fields always have the same value.
    * :doc:`Viewer fields <fields/viewer_fields>` represent viewers. These become viewers on module setup as well.
    * :doc:`ROI fields <fields/roi_fields>` handle ROIs created and used by the module.

Fields can be grouped together in the user interface of both modules and collections by using :py:class:`FieldWindow <pumpia.module_handling.fields.windows.FieldWindow>`.

:doc:`context`
--------------
Context is used to pass information into the module for drawing ROIs, it is useful to reduce recalculating information between modules.
In the user interface collections of widgets called `context managers` use the modules ``main_viewer`` to generate the context.
The context manager is set using the ``context_manager`` class attribute, or it can be passed into the module like with collections.
Alternatively a modules `get_context` method can be overwritten.

The following context managers are provided:

    * :py:class:`BaseContextManager <pumpia.widgets.context_managers.BaseContextManager>`
    * :py:class:`SimpleContextManager <pumpia.widgets.context_managers.SimpleContextManager>`
    * :py:class:`PhantomContextManager <pumpia.widgets.context_managers.PhantomContextManager>`
    * :py:class:`ManualPhantomManager <pumpia.widgets.context_managers.ManualPhantomManager>`
    * :py:class:`AutoPhantomManager <pumpia.widgets.context_managers.AutoPhantomManager>`

When creating your own context manager you must provide the :py:meth:`get_context <pumpia.widgets.context_managers.BaseContextManager.get_context>` method.

:doc:`collections`
------------------
Collections are used to group modules together, with a main tab showing the context and any defined viewers.
Only :doc:`viewer fields <fields/viewer_fields>`, :doc:`field groups <fields/groups>`  can be used with collections, any others will be ignored/wont function as expected.

Similar to modules they have context which is shared across all the modules in the collection.
The ``context_manager`` class attribute can be defined for collections, it defaults to :py:class:`SimpleContextManagerGenerator <pumpia.widgets.context_managers.SimpleContextManager>`.
The ``title`` class attribute is shown in the window title, this defaults to ``Pumpia Collection``.

Collections introduce two other useful classes:

    * :py:class:`WindowGroup <pumpia.module_handling.collections.ModulsGroup>` which shows multiple modules in the same tab instead of showing them across multiple tabs.

When subclassing :py:class:`BaseCollection <pumpia.module_handling.collections.BaseCollection>` the following methods are designed to be overwritten:

    * :py:meth:`load_commands <pumpia.module_handling.collections.BaseCollection.load_commands>`
    * :py:meth:`on_image_load <pumpia.module_handling.collections.BaseCollection.on_image_load>`

Logging
-------
Collections and Modules have a ``logger`` attribute which can be used to provide information to the user.
Messages passed to the logger can be viewed on the ``Log`` window of the user interface.

Contents
--------
.. toctree::
    example
    modules
    fields/fields
    collections
    context
    user_interface
