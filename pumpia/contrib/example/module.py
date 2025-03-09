import math

from pumpia.widgets.viewers import BaseViewer
from pumpia.module_handling.modules import BaseModule
from pumpia.module_handling.in_outs.roi_ios import BaseInputROI, InputEllipseROI
from pumpia.module_handling.in_outs.viewer_ios import ArrayViewerIO
from pumpia.module_handling.in_outs.simple import PercInput, FloatOutput, IntOutput
from pumpia.module_handling.context import SimpleContext
from pumpia.image_handling.roi_structures import EllipseROI
from pumpia.utilities.tkinter_utils import tk_copy


class ExampleModule(BaseModule):
    """
    An Example Module.

    This module demonstrates the use of the PumpIA modules.
    It draws an ellipse ROI on an image based on the size of image and input from the user.
    The analysis calculates the average pixel value within the ellipse,
    or the root sum of squares of the means if a multisample image.
    """
    viewer = ArrayViewerIO(row=0, column=0)
    size = PercInput(80, verbose_name="Size (%)")
    ellipse_roi = InputEllipseROI("Ellipse ROI")

    width = IntOutput(verbose_name="Width (px)")
    height = IntOutput(verbose_name="Height (px)")
    average = FloatOutput()

    def link_rois_viewers(self):
        self.ellipse_roi.viewer = self.viewer

    def draw_rois(self, context: SimpleContext, batch: bool = False):
        if self.viewer.image is not None:
            factor = self.size.value / 100
            a = round(factor * context.width / 2)
            b = round(factor * context.height / 2)
            self.ellipse_roi.register_roi(EllipseROI(self.viewer.image,
                                                     round(context.xcent),
                                                     round(context.ycent),
                                                     a,
                                                     b,
                                                     slice_num=self.viewer.current_slice))

    def post_roi_register(self, roi_input: BaseInputROI):
        if self.ellipse_roi.roi is not None and self.manager is not None:
            self.manager.add_roi(self.ellipse_roi.roi)

    def analyse(self, batch: bool = False):
        if self.ellipse_roi.roi is not None:
            roi = self.ellipse_roi.roi
            mean = roi.mean
            if isinstance(mean, (float, int)):
                self.average.value = mean
            else:
                self.average.value = math.sqrt(math.sumprod(mean, mean))

    def on_image_load(self, viewer: BaseViewer) -> None:
        if viewer is self.viewer:
            image = self.viewer.image
            if image is not None:
                self.height.value = image.shape[1]
                self.width.value = image.shape[2]

    def load_commands(self):
        self.register_command("Copy Average", self.copy_average)

    def copy_average(self):
        """
        Copy the value of the average to the clipboard.
        """
        tk_copy(str(self.average.value))
