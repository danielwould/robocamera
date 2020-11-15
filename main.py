# dev notes
# select waypoint for editing - modify/delete

# abort sequence
# pause/resume sequence
# step backward/forward through sequence


import time
from data.waypoint import waypoint
from data.location import location
from data.sequence import sequence
from helpers.ui import UI
from helpers.ui import TextPrint
from helpers.crane import crane
from helpers.gimbal import gimbal
from helpers.CNC import CNC
from helpers.joystick import Joystick
from helpers.info import info
import os
import sys
try:
	import Tkinter as tk
	from Queue import *
	from Tkinter import *
	import tkMessageBox
except ImportError:
	import tkinter as tk
	from queue import *
	from tkinter import *
	import tkinter.messagebox as tkMessageBox


PRGPATH=os.path.abspath(os.path.dirname(__file__))
sys.path.append(PRGPATH)
sys.path.append(os.path.join(PRGPATH, 'helpers'))
sys.path.append(os.path.join(PRGPATH, 'data'))
sys.path.append(os.path.join(PRGPATH, 'helpers/controllers'))


VALID_CHARS = "`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./"
SHIFT_CHARS = '~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'


class RobotCamera(tk.Frame):
    
    GIMBAL_CONTROL = 1
    CRANE_CONTROL = 0
    CONTROL_TOGGLE = GIMBAL_CONTROL

    FEED_RATE = 0
    MOVE_TIME = 1
    MOVE_TOGGLE = FEED_RATE

    # x= gimble pan, y= gimble tilt, z= camera zoom, t= boom_tilt
    save_position_1 = waypoint(location(0, 0, 0), location(0, 0, 0))
    save_position_2 = waypoint(location(0, 0, 0), location(0, 0, 0))
    save_position_3 = waypoint(location(0, 0, 0), location(0, 0, 0))
    save_position_4 = waypoint(location(0, 0, 0), location(0, 0, 0))

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.init_controllers()
        self.init_joysticks()
        self.init_info_updater()
        self.pack()
        self.create_widgets()

    def init_controllers(self):
        MOCK = 0
        self.gimbal_inst = gimbal("/dev/ttyACM1", MOCK,0,"Gimbal")
        self.gimbal_inst.set_small_step_rotate(0.2)
        self.gimbal_inst.set_big_step_rotate(2)
        self.gimbal_inst.set_small_step_tilt(0.2)
        self.gimbal_inst.set_big_step_tilt(2)
        self.crane_inst = crane("/dev/ttyACM1", MOCK,0.4,"Crane")

    def init_joysticks(self):
        self.joy = Joystick(self, self.gimbal_inst, self.crane_inst)

    def init_info_updater(self):
        self.info_update = info(self,self.gimbal_inst,self.crane_inst)


    def create_widgets(self):
        
        self.gimbal_pos_text = tk.Label(self,text="GimbalPos", relief=tk.RIDGE)
        self.gimbal_pos_text.pack()
        self.crane_pos_text = tk.Label(self,text="CranePos", relief=tk.RIDGE)
        self.crane_pos_text.pack()


        self.up = tk.Button(self, text="U", fg="yellow", command=self.tilt_up)
        self.up.pack(side="top")

        self.left = tk.Button(self, text="L", fg="yellow", command=self.rotate_left)
        self.left.pack(side="left")

        self.right = tk.Button(self, text="R", fg="yellow", command=self.rotate_right)
        self.right.pack(side="right")
        self.down = tk.Button(self, text="D", fg="yellow", command=self.tilt_down)
        self.down.pack(side="bottom")

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.quit)
        self.quit.pack(side="bottom")

    def say_hi(self):
        print("hi there, everyone!")


    def toggle_control(self,value):
        print("toggle control to")
        print(value)
        CONTROL_TOGGLE = value

    def toggle_move_mode(self,value):
        print("toggle move mode to")
        print(value)
        MOVE_TOGGLE = value

   

    def set_feed_rate(self, feedval):
        if CONTROL_TOGGLE == GIMBAL_CONTROL:
            print("updating feeddefault from {} to {}".format(
                feedval, self.gimbal_inst.get_feed_speed()))
            self.gimbal_inst.set_feed_speed(feedval)
        if CONTROL_TOGGLE == CRANE_CONTROL:
            print("updating crane feeddefault from {} to {}".format(
                feedval, self.crane_inst.get_feed_speed()))
            self.crane_inst.set_feed_speed(feedval)

    def set_delay_rate(self,val):
        print("set crane delay to {}".format(val))
        self.crane_inst.set_command_delay(val)



    def set_move_time(self,seconds):
        if CONTROL_TOGGLE == GIMBAL_CONTROL:
            print("updating gimbal move time from {} to {}".format(
                seconds, self.gimbal_inst.get_move_duration()))
            self.gimbal_inst.set_move_duration(seconds)
        if CONTROL_TOGGLE == CRANE_CONTROL:
            print("updating crane move time from {} to {}".format(
                seconds, self.crane_inst.get_move_duration()))
            self.crane_inst.set_move_duration(seconds)


    def add_waypoint(dwell_input_text, sequence_steps):
        print("add waypoint")  # (x, y, z,focus, feed), dwell time
        crane_position = crane_inst.get_current_location()
        gimbal_position = gimbal_inst.get_current_location()
        wp = waypoint(
            location(crane_position.get_rotation_pos(), crane_position.get_tilt_pos(),crane_position.get_zoom_pos()),
            location(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()))
        wp.set_dwell_time(int(dwell_input_text))
        wp.set_gimbal_travel_to_feed_rate(gimbal_inst.get_feed_speed())
        wp.set_crane_travel_to_feed_rate(crane_inst.get_feed_speed())
        wp.set_gimbal_travel_to_duration(gimbal_inst.get_move_duration())
        wp.set_crane_travel_to_duration(crane_inst.get_move_duration())
        sequence_steps.add_waypoint(wp)


    def delete_waypoint(item, sequence_steps):
        # todo allow for deleting specific waypoint item
        sequence_steps.delete_waypoint()


    def start_sequence(sequence_steps):
        print("starting sequence")
        if len(sequence_steps.waypoints) > 0:
            sequence_steps.start()
            trigger_sequence_step(sequence_steps)


    def trigger_sequence_step(sequence_steps):
        # TODO this needs to support move base on time
        print("sequence step triger")
        wp = sequence_steps.get_next_step()
        if MOVE_TOGGLE == FEED_RATE:
            print ("move to waypoint by feed rate")
            crane_inst.move_to_waypoint(
                wp.get_crane_position(), wp.get_crane_travel_to_feed_rate())
            gimbal_inst.move_to_waypoint(wp.get_gimbal_position(), wp.get_gimbal_travel_to_feed_rate())
            
        if MOVE_TOGGLE == MOVE_TIME:
            print ("move to waypoint by travel duration")
            crane_inst.move_to_waypoint_by_time(
                wp.get_crane_position(), wp.get_crane_travel_to_duration())
            gimbal_inst.move_to_waypoint_by_time(
                wp.get_gimbal_position(), wp.get_gimbal_travel_to_duration())
        
    def trigger_whole_sequence(sequence_steps):
        global crane_inst
        global gimbal_inst
        if len(sequence_steps.waypoints) > 0:
            for i in range(len(sequence_steps.waypoints)): 
        
            #for wp in sequence_steps.waypoints:
                if MOVE_TOGGLE == FEED_RATE:
                    crane_inst.add_waypoint_by_feedrate_to_sequqnce(sequence_steps.waypoints[i].get_crane_position(), sequence_steps.waypoints[i].get_crane_travel_to_feed_rate(),sequence_steps.waypoints[i].get_dwell_time())
                    gimbal_inst.add_waypoint_by_feedrate_to_sequqnce(sequence_steps.waypoints[i].get_gimbal_position(), sequence_steps.waypoints[i].get_gimbal_travel_to_feed_rate(),sequence_steps.waypoints[i].get_dwell_time())
                if MOVE_TOGGLE == MOVE_TIME:
                    crane_inst.add_waypoint_by_time_to_sequqnce(sequence_steps.waypoints[i].get_crane_position(),sequence_steps.waypoints[i].get_crane_travel_to_duration(),sequence_steps.waypoints[i].get_dwell_time())
                    gimbal_inst.add_waypoint_by_time_to_sequqnce(sequence_steps.waypoints[i].get_gimbal_position(), sequence_steps.waypoints[i].get_gimbal_travel_to_duration(),sequence_steps.waypoints[i].get_dwell_time())
        print("===========")
        print("built crane sequence")
        crane_inst.get_current_gcode_sequence("crane")
        print("===========")
        print("built gimbal sequence")
        gimbal_inst.get_current_gcode_sequence("gimbal")
        print("===========")

        crane_inst.trigger_sequence("crane")
        gimbal_inst.trigger_sequence("gimbal")
        #set location to last wp


    def save_point_move(savepoint):
        if MOVE_TOGGLE == FEED_RATE:
            crane_inst.move_to_position_at_rate(savepoint.get_crane_position())
            gimbal_inst.move_to_position_at_rate(savepoint.get_gimbal_position())
        if MOVE_TOGGLE == MOVE_TIME:
            crane_inst.move_to_position_in_time(savepoint.get_crane_position())
            gimbal_inst.move_to_position_in_time(savepoint.get_gimbal_position())
            

    def save_position(savepoint):
        global save_position_1
        global save_position_2
        global save_position_3
        global save_position_4
        crane_position = crane_inst.get_current_location()
        gimbal_position = gimbal_inst.get_current_location()
        new_waypoint = waypoint(
            cranepos(crane_position.get_rotation_pos(), crane_position.get_tilt_pos()),
            gimbalpos(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()))
        if savepoint == 1:
            save_position_1 = new_waypoint
        if savepoint == 2:
            save_position_2 = new_waypoint
        if savepoint == 3:
            save_position_3 = new_waypoint
        if savepoint == 4:
            save_position_4 = new_waypoint

    def reset():
        global save_position_1
        global save_position_2
        global save_position_3
        global save_position_4
        
        crane_inst.reset()
        gimbal_inst.reset()

        save_position_1 = waypoint(location(0, 0,0), location(0, 0, 0))
        save_position_2 = waypoint(location(0, 0,0), location(0, 0, 0))
        save_position_3 = waypoint(location(0, 0,0), location(0, 0, 0))
        save_position_4 = waypoint(location(0, 0,0), location(0, 0, 0))

    def tilt_up(self):
        print("up")
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            self.gimbal_inst.tilt_up_small()
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            self.crane_inst.tilt_up_small()


    def tilt_down(self):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            self.gimbal_inst.tilt_down_small()
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            self.crane_inst.tilt_down_small()


    def rotate_left(self):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            self.gimbal_inst.rotate_left_small()
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            self.crane_inst.rotate_left_small()


    def rotate_right(self):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            self.gimbal_inst.rotate_right_small()
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            self.crane_inst.rotate_right_small()


    def zoom_in(self):
        self.gimbal_inst.zoom_in_small()


    def zoom_out(self):
        self.gimbal_inst.zoom_out_small()

    def quit(self):
        self.gimbal_inst.stop()
        self.crane_inst.stop()
        self.joy.stop()
        self.info_update.stop()
        time.sleep(0.5)
        self.master.destroy()


if __name__ == "__main__":
    #main()
    root = tk.Tk()
    app = RobotCamera(master=root)
    app.mainloop()