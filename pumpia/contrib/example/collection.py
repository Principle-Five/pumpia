from pumpia.contrib.example.module import ExampleModule
from pumpia.module_handling.module_collections import (BaseCollection,
                                                       OutputFrame,
                                                       WindowGroup)
from pumpia.module_handling.in_outs.viewer_ios import ArrayViewerIO
from pumpia.module_handling.in_outs.groups import IOGroup
from pumpia.widgets.viewers import BaseViewer
from pumpia.image_handling.image_structures import ImageCollection
from pumpia.utilities.tkinter_utils import tk_copy


class ExampleCollection(BaseCollection):
    """
    An example collection.

    This collection demonstrates the use of the PumpIA collections.
    It has 2 viewers in the main window and loads 2 `ExampleModule` instances into a second window.
    """
    viewer1 = ArrayViewerIO(row=0, column=0)
    viewer2 = ArrayViewerIO(row=0, column=1, main=True)

    module1 = ExampleModule()
    module2 = ExampleModule()

    average_output = OutputFrame()

    # makes sure the two modules are in the same window in the collection
    group = WindowGroup([module1, module2])

    def load_outputs(self):
        self.average_output.register_output(self.module1.average, verbose_name="Average 1")
        self.average_output.register_output(self.module2.average, verbose_name="Average 2")
        IOGroup([self.module1.size, self.module2.size])

    def on_image_load(self, viewer: BaseViewer) -> None:
        # loads the image loaded into a viewer into the relevant modules viewer
        # if the image is an ImageCollection then only loads the first image into the module
        if viewer is self.viewer1:
            if self.viewer1.image is not None:
                image = self.viewer1.image
                if isinstance(image, ImageCollection):
                    self.module1.viewer.load_image(image.image_set[0])
                else:
                    self.module1.viewer.load_image(image)

        elif viewer is self.viewer2:
            if self.viewer2.image is not None:
                image = self.viewer2.image
                if isinstance(image, ImageCollection):
                    self.module2.viewer.load_image(image.image_set[0])
                else:
                    self.module2.viewer.load_image(image)

    def load_commands(self):
        self.register_command("Copy Averages", self.copy_averages)

    def copy_averages(self):
        """
        Copy the values of the averages to the clipboard, comma seperated.
        """
        tk_copy(", ".join([str(self.module1.average.value), str(self.module2.average.value)]))
