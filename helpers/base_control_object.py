from helpers.grbl_controller import grbl_controller
import time

class base_control_object:
    
    small_step_rotate = 1
    big_step_rotate = 10
    small_step_tilt = 1
    big_step_tilt = 10
    last_command_sent_at = time.time()
    command_throttle_limit=0.2
    last_position_in_sequence=None
    rotate_axis = "x"
    tilt_axis = "y"
    zoom_axis = "z"

    def __init__(self, rotate_axis, tilt_axis, zoom_axis, controller):
        self.rotate_axis = rotate_axis
        self.tilt_axis = tilt_axis
        self.zoom_axis = zoom_axis
        self.controller=controller

    def reset(self):
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
    
    def get_current_location(self):
        return self.controller.currentlocation(self.rotate_axis,self.tilt_axis,self.zoom_axis)


    
    def open_connection(self):
        self.controller.set_device(self.device)

    def rotate_right_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("{}{}".format(self.rotate_axis,
                self.small_step_rotate))
            self.last_command_sent_at = time.time()
            

    def rotate_left_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "{}-{}".format(self.rotate_axis,self.small_step_rotate))
            self.last_command_sent_at = time.time()
            
    

    def rotate_right_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("{}{}".format(self.rotate_axis,
                self.big_step_rotate))
            self.last_command_sent_at = time.time()
            

    def rotate_left_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "{}-{}".format(self.rotate_axis,self.big_step_rotate))
            self.last_command_sent_at = time.time()
            

    def tilt_up_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("{}-{}".format(self.tilt_axis,
                self.small_step_tilt))
            self.last_command_sent_at = time.time()
            

    def tilt_down_small(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "{}{}".format(self.tilt_axis,self.small_step_tilt))
            self.last_command_sent_at = time.time()
            

    def tilt_up_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move("{}-{}".format(
                self.tilt_axis,self.big_step_tilt))
            self.last_command_sent_at = time.time()
            

    def tilt_down_large(self):
        if time.time()-self.last_command_sent_at > self.command_throttle_limit:
            self.controller.relative_move(
                "{}{}".format(self.tilt_axis,self.big_step_tilt))
            self.last_command_sent_at = time.time()
           
    def rotate_jog(self,multiplier):
        self.controller.relative_move("{}{}".format(self.rotate_axis,(1*multiplier)))

    def tilt_jog(self,multiplier):
        self.controller.relative_move("{}{}".format(self.tilt_axis,(1*multiplier)))

    def cancel_jog(self):
        self.controller.cancel_jog()  

    def status(self):
        self.controller.status()
