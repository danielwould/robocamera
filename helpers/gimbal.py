from helpers.base_control_object import base_control_object
import time

class gimbal(base_control_object):
    small_step_zoom = 0.2
    big_step_zoom = 1

    def __init__(self, device, position, mode):
        super().__init__(device, position, mode)

    def zoom_in_small(self):
        self.controller.relative_move("z{}".format(
            self.small_step_zoom), self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.increment_zoom(self.small_step_zoom)

    def zoom_out_small(self):
        self.controller.relative_move(
            "z-{}".format(self.small_step_zoom), self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.decrement_zoom(self.small_step_zoom)

    def zoom_in_large(self):
        self.controller.relative_move("z{}".format(
            self.big_step_zoom), self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.increment_zoom(self.big_step_zoom)

    def zoom_out_large(self):
        self.controller.relative_move(
            "z-{}".format(self.big_step_zoom), self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.decrement_zoom(self.big_step_zoom)
    
   
