from helpers.grbl_controller import grbl_controller
import time

class base_control_object:
    current_feed_speed = 1000
    current_move_duration = 10
    small_step_rotate = 1
    big_step_rotate = 10
    small_step_tilt = 1
    big_step_tilt = 5
    last_command_sent_at = time.time()
    currentlocation = None
    command_throttle_limit=0.2

    def __init__(self, device, position, mode):
        self.device = device
        self.currentlocation=position
        self.controller=grbl_controller(mode)
        self.controller.set_device(self.device)

    async def reset(self):
        self.currentlocation.reset()
        self.controller.reset()

    def set_small_step_rotate(self, value):
        self.small_step_rotate = value

    def set_big_step_rotate(self, value):
        self.big_step_rotate = value

    def set_small_step_tilt(self, value):
        self.small_step_tilt = value

    def set_big_step_tilt(self, value):
        self.big_step_tilt = value

    def current_location_str(self):
        return self.currentlocation.current_location_str()
    
    def get_current_location(self):
        return self.currentlocation

    def set_feed_speed(self,value):
        self.current_feed_speed=value
    
    def get_feed_speed(self):
        return self.current_feed_speed

    def set_move_duration(self,value):
        self.current_move_duration=value
    
    def get_move_duration(self):
        return self.current_move_duration

    def open_connection(self):
        self.controller.set_device(self.device)

    def rotate_right_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("x{}".format(
                self.small_step_rotate), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            self.currentlocation.increment_rotation(self.small_step_rotate)

    def rotate_left_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "x-{}".format(self.small_step_rotate), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            self.currentlocation.decrement_rotation(self.small_step_rotate)

    def rotate_right_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("x{}".format(
                self.big_step_rotate), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            self.currentlocation.increment_rotation(self.big_step_rotate)

    def rotate_left_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "x-{}".format(self.big_step_rotate), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            self.currentlocation.decrement_rotation(self.big_step_rotate)

    def tilt_up_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("y-{}".format(
                self.small_step_tilt), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            self.currentlocation.decrement_tilt(self.small_step_tilt)

    def tilt_down_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "y{}".format(self.small_step_tilt), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            self.currentlocation.increment_tilt(self.small_step_tilt)

    def tilt_up_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("y-{}".format(
                self.big_step_tilt), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            self.currentlocation.decrement_tilt(self.big_step_tilt)

    def tilt_down_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "y{}".format(self.big_step_tilt), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            self.currentlocation.increment_tilt(self.big_step_tilt)

    async def move_to_position_at_rate(self, position):
        self.controller.absolute_move(position.get_rotation_pos(),position.get_tilt_pos(),0,self.current_feed_speed)
        self.last_command_sent_at = time.time()
        self.currentlocation.set_location(position)

    async def move_to_position_in_time(self, position):
        self.controller.absolute_move_by_time(position.get_rotation_pos(),position.get_tilt_pos(),0,self.current_move_duration)
        self.last_command_sent_at = time.time()
        self.currentlocation.set_location(position)


    async def move_to_waypoint(self, position, feed_rate):
        self.controller.absolute_move(position.get_rotation_pos(),position.get_tilt_pos(),0,feed_rate)
        self.last_command_sent_at = time.time()
        self.currentlocation.set_location(position)
        
    async def move_to_waypoint_by_time(self, position, duration):
        self.controller.absolute_move_by_time(position.get_rotation_pos(),position.get_tilt_pos(),0,duration)
        self.last_command_sent_at = time.time()
        self.currentlocation.set_location(position)

