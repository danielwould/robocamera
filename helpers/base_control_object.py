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
    command_throttle_limit=0.2
    last_position_in_sequence=None

    def __init__(self, device, mode,dwell_delay,name):
        self.device = device
        self.controller=grbl_controller(mode,dwell_delay)
        self.controller.set_device(self.device, 115200,name)

    def reset(self):
        self.currentlocation.reset()
        self.controller.reset()

    def stop(self):
        self.controller.stop()

    def set_command_delay(self, value):
        self.controller.set_command_delay(value)

    def set_small_step_rotate(self, value):
        self.small_step_rotate = value

    def set_big_step_rotate(self, value):
        self.big_step_rotate = value

    def set_small_step_tilt(self, value):
        self.small_step_tilt = value

    def set_big_step_tilt(self, value):
        self.big_step_tilt = value

    def current_location_str(self):
        return self.controller.position_str()
    
    def get_current_location(self):
        return self.controller.currentlocation()

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
            

    def rotate_left_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "x-{}".format(self.small_step_rotate), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            

    def rotate_right_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("x{}".format(
                self.big_step_rotate), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            

    def rotate_left_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "x-{}".format(self.big_step_rotate), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            

    def tilt_up_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("y-{}".format(
                self.small_step_tilt), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            

    def tilt_down_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "y{}".format(self.small_step_tilt), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            

    def tilt_up_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("y-{}".format(
                self.big_step_tilt), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            

    def tilt_down_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "y{}".format(self.big_step_tilt), self.current_feed_speed)
            self.last_command_sent_at = time.time()
            

    def move_to_position_at_rate(self, position):
        self.controller.absolute_move(position.get_rotation_pos(),position.get_tilt_pos(),0,self.current_feed_speed,0)
        self.last_command_sent_at = time.time()
        

    def move_to_position_in_time(self, position):
        self.controller.absolute_move_by_time(position.get_rotation_pos(),position.get_tilt_pos(),0,self.current_move_duration,0)
        self.last_command_sent_at = time.time()
        


    def move_to_waypoint(self, position, feed_rate, dwell):
        self.controller.absolute_move(position.get_rotation_pos(),position.get_tilt_pos(),0,feed_rate, dwell)
        self.last_command_sent_at = time.time()
        
        
    def move_to_waypoint_by_time(self, position, duration, dwell):
        self.controller.absolute_move_by_time(position.get_rotation_pos(),position.get_tilt_pos(),0,duration, dwell)
        self.last_command_sent_at = time.time()
        

    def add_waypoint_by_time_to_sequqnce(self, position, duration, dwell):
        self.controller.add_absolute_move_by_time_to_sequence(position.get_rotation_pos(),position.get_tilt_pos(),0,duration, dwell)
        self.last_position_in_sequence = position
        print("{} time waypoint added to gcode sequence".format(time.ctime()))

    def add_waypoint_by_feedrate_to_sequqnce(self, position, duration, dwell):
        self.controller.add_absolute_move_by_feed_to_sequence(position.get_rotation_pos(),position.get_tilt_pos(),0,duration, dwell)
        self.last_position_in_sequence = position
        print("{} feedraet waypoint added to gcode sequence".format(time.ctime()))
        
    def trigger_sequence(self, name):
        self.controller.run_sequence(name)
        
    def get_current_gcode_sequence(self,name):
        self.controller.print_gcode_sequence(name)

    def status(self):
        self.controller.status()

    def tick(self):
        self.controller.tick()