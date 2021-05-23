from helpers.base_control_object import base_control_object
import time


class gimbal(base_control_object):
    small_step_zoom = 0.2
    big_step_zoom = 1
    
    def __init__(self,rotate_axis, tilt_axis, zoom_axis, controller):
        super().__init__(rotate_axis, tilt_axis, zoom_axis, controller)
        

    def zoom_in_small(self):
        self.controller.relative_move("{}-{}".format(self.zoom_axis,
            self.small_step_zoom))
        self.last_command_sent_at = time.time()

    def zoom_out_small(self):
        self.controller.relative_move(
            "{}{}".format(self.zoom_axis,self.small_step_zoom))
        self.last_command_sent_at = time.time()

    def zoom_in_large(self):
        self.controller.relative_move("{}-{}".format(
            self.zoom_axis,self.big_step_zoom))
        self.last_command_sent_at = time.time()

    def zoom_out_large(self):
        self.controller.relative_move(
            "{}{}".format(self.zoom_axis,self.big_step_zoom))
        self.last_command_sent_at = time.time()

    # override move commands to include the third axis
    

 