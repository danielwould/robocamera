from helpers.base_control_object import base_control_object
import time


class gimbal(base_control_object):
    small_step_zoom = 0.2
    big_step_zoom = 1

    def __init__(self, device, position, mode):
        super().__init__(device, position, mode)

    def zoom_in_small(self):
        self.controller.relative_move("z-{}".format(
            self.small_step_zoom), self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.increment_zoom(self.small_step_zoom)

    def zoom_out_small(self):
        self.controller.relative_move(
            "z{}".format(self.small_step_zoom), self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.decrement_zoom(self.small_step_zoom)

    def zoom_in_large(self):
        self.controller.relative_move("z-{}".format(
            self.big_step_zoom), self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.increment_zoom(self.big_step_zoom)

    def zoom_out_large(self):
        self.controller.relative_move(
            "z{}".format(self.big_step_zoom), self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.decrement_zoom(self.big_step_zoom)

    # override move commands to include the third axis
    def move_to_position_at_rate(self, position):
        self.controller.absolute_move(position.get_rotation_pos(), position.get_tilt_pos(), position.get_zoom_pos(),
                                      self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.set_location(position)

    def move_to_position_in_time(self, position):
        self.controller.absolute_move_by_time(position.get_rotation_pos(), position.get_tilt_pos(),
                                              position.get_zoom_pos(),
                                              self.current_move_duration)
        self.last_command_sent_at = time.time()
        self.currentlocation.set_location(position)

    def move_to_waypoint(self, position, feed_rate):
        self.controller.absolute_move(position.get_rotation_pos(), position.get_tilt_pos(), position.get_zoom_pos(),
                                      feed_rate)
        self.last_command_sent_at = time.time()
        self.currentlocation.set_location(position)
