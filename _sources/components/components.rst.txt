Core Components
===============

Most people will want to use PumpIA through the :doc:`modules </usage/modules>` and :doc:`collections </usage/collections>` as described in :doc:`usage </usage/usage>`,
however the core components and how they iteract are described for anyone who wants more control over them, or who wants to embed them in their own program.

:doc:`manager`
--------------
This is the central piece of the program, it controls the loading of all images and links all the other components together.
Use the manager to get the treeviews and widgets for the controls within the program.
Users can right click on different entries in treeviews for different options.
There is typically only one manager per program.

:doc:`viewers`
--------------
These are the widgets which show the images.
There are a few different kinds depending on if the image loaded should be limited.
Viewers have multiple shortcuts to make it easier for the end user.

:doc:`images`
-------------
Different classes which represent images and collections of images.
Also see :doc:`file handling </file_handling/file_handling>`.

:doc:`rois`
-----------
These represent regions of interest of different shapes.

Contents
--------
.. toctree::
    manager
    viewers
    images
    rois
