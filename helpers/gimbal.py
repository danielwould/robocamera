from helpers.base_control_object import base_control_object
import time


class gimbal(base_control_object):
    small_step_zoom = 0.2
    big_step_zoom = 1
    
    def __init__(self,rotate_axis, tilt_axis, zoom_axis, controller):
        super().__init__(rotate_axis, tilt_axis, zoom_axis, controller)
        

    def zoom_in_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(self.zoom_axis,0.2)
          
        self.last_command_sent_at = time.time()

    def zoom_out_small(self):

        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(self.zoom_axis,-0.2)
        self.last_command_sent_at = time.time()

    def zoom_in_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(self.zoom_axis,1)
        self.last_command_sent_at = time.time()

    def zoom_out_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(self.zoom_axis,-1)
        self.last_command_sent_at = time.time()

    # override move commands to include the third axis
    

 