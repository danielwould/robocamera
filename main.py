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
    
    
    

    

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.GIMBAL_CONTROL = 1
        self.CRANE_CONTROL = 0
        self.CONTROL_TOGGLE = self.GIMBAL_CONTROL
        self.FEED_RATE = 0
        self.MOVE_TIME = 1
        self.MOVE_TOGGLE = self.FEED_RATE

        self.save_position_1 = waypoint(location(0, 0, 0), location(0, 0, 0))
        self.save_position_2 = waypoint(location(0, 0, 0), location(0, 0, 0))
        self.save_position_3 = waypoint(location(0, 0, 0), location(0, 0, 0))
        self.save_position_4 = waypoint(location(0, 0, 0), location(0, 0, 0))
        
        self.sequence_steps = sequence()
        
        self.init_controllers()
        self.init_joysticks()
        self.init_info_updater()
        self.pack()
        self.create_widgets()

    def init_controllers(self):
        MOCK = 0
        self.gimbal_inst = gimbal("/dev/ttyACM0", MOCK,0,"Gimbal")
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

        #
        #controller location display
        #
        info = Frame(self,relief=tk.SUNKEN)
        info.pack(side="left")
        location_info = Frame(info,relief=tk.RIDGE)
        location_info.pack(side="top") 

        self.gimbal_pos_text = tk.Label(location_info,text="GimbalPos", relief=tk.RIDGE)
        self.gimbal_pos_text.config(font=("Courier", 22))
        self.gimbal_pos_text.pack()
        self.crane_pos_text = tk.Label(location_info,text="CranePos", relief=tk.RIDGE)
        self.crane_pos_text.config(font=("Courier", 20))
        self.crane_pos_text.pack()


        #
        #savepoints
        #
        savepoint_info = Frame(info,relief=tk.RIDGE)
        savepoint_info.pack(side="left") 
        self.sp1_pos_text = tk.Label(savepoint_info,text="Y/LB", relief=tk.RIDGE)
        self.sp1_pos_text.config(font=("Courier", 12))
        self.sp1_pos_text.pack()
        self.sp2_pos_text = tk.Label(savepoint_info,text="B/RB", relief=tk.RIDGE)
        self.sp2_pos_text.config(font=("Courier", 12))
        self.sp2_pos_text.pack()
        self.sp3_pos_text = tk.Label(savepoint_info,text="X/L1", relief=tk.RIDGE)
        self.sp3_pos_text.config(font=("Courier", 12))
        self.sp3_pos_text.pack()
        self.sp4_pos_text = tk.Label(savepoint_info,text="A/R1", relief=tk.RIDGE)
        self.sp4_pos_text.config(font=("Courier", 12))
        self.sp4_pos_text.pack()

        #waypoints
        
        self.waypoint_listbox = Listbox(info, width=60)
        self.waypoint_listbox.pack(side="bottom")
        #
        #on screen move controls
        #
        Motion_controls = Frame(self,relief=tk.RIDGE)
        Motion_controls.pack()
        self.up = tk.Button(Motion_controls, text="U", fg="yellow",bg="grey", command=self.tilt_up)
        self.up.config(font=("Courier", 22))
        self.up.pack(side="top")
        self.left = tk.Button(Motion_controls, text="L", fg="yellow",bg="grey", command=self.rotate_left)
        self.left.config(font=("Courier", 22))
        self.left.pack(side="left")
        self.right = tk.Button(Motion_controls, text="R", fg="yellow",bg="grey", command=self.rotate_right)
        self.right.config(font=("Courier", 22))
        self.right.pack(side="right")
        self.down = tk.Button(Motion_controls, text="D", fg="yellow",bg="grey", command=self.tilt_down)
        self.down.config(font=("Courier", 22))
        self.down.pack(side="bottom")

        #
        #controls that toggle behaviour
        #
        Toggle_controls = Frame(self,relief=tk.GROOVE)
        Toggle_controls.pack()
        controller_select = Frame(Toggle_controls,relief=tk.GROOVE)
        controller_select.pack(side="left")
        self.gimbalToggle = tk.Button(controller_select, text="Gimbal", fg="yellow",bg="black", command=lambda: self.toggle_control(self.GIMBAL_CONTROL))
        self.gimbalToggle.pack(side="top")
        self.craneToggle = tk.Button(controller_select, text="Crane", fg="yellow",bg="black", command=lambda: self.toggle_control(self.CRANE_CONTROL))
        self.craneToggle.pack(side="bottom")
        move_select = Frame(Toggle_controls,relief=tk.GROOVE)
        move_select.pack(side="right")
        self.moveFeedToggle = tk.Button(move_select, text="Feed mm/s", fg="yellow",bg="black", command=lambda: self.toggle_move_mode(self.FEED_RATE))
        self.moveFeedToggle.pack(side="top")
        self.moveTimeToggle = tk.Button(move_select, text="Move Time", fg="yellow",bg="black", command=lambda: self.toggle_move_mode(self.MOVE_TIME))
        self.moveTimeToggle.pack(side="bottom")

        #
        #manipulate waypoints
        #
        wayPoint_controls = Frame(self,relief=tk.RIDGE)
        wayPoint_controls.pack()
        self.addWaypoint = tk.Button(wayPoint_controls, text="Add Waypoint", fg="black",
                              command=lambda: self.add_waypoint(self.dwell_time.get()))
        self.addWaypoint.pack()
        self.deleteWaypoint = tk.Button(wayPoint_controls, text="Del Waypoint", fg="black",
                              command=self.delete_waypoint)
        self.deleteWaypoint.pack()

        options_controls = Frame(self,relief=tk.GROOVE)
        options_controls.pack(side="right")
        dwell = Frame(options_controls)
        dwell.pack(side="right")
        self.dwell_label = tk.Label(dwell,text="DwellTime", relief=tk.RIDGE)
        self.dwell_label.config(font=("Courier", 12))
        self.dwell_label.pack(side="top")
        self.dwell_time = StringVar(dwell)
        self.dwell_time.set(1) # initial value
        self.dwell_select = OptionMenu(dwell, self.dwell_time, 1, 2,5,10,15,20)
        self.dwell_select.pack(side="bottom")

        feed = Frame(options_controls)
        feed.pack(side="right")
        self.feedrate_label = tk.Label(feed,text="FeedRate", relief=tk.RIDGE)
        self.feedrate_label.config(font=("Courier", 12))
        self.feedrate_label.pack(side="top")
        self.feed_rate = StringVar(feed)
        self.feed_rate.set(1000) # initial value
        self.feed_rate = OptionMenu(feed, self.feed_rate, 100, 200,500,700,1000,1500)
        self.feed_rate.pack(side="bottom")

        move = Frame(options_controls)
        move.pack(side="right")
        self.movetime_label = tk.Label(move,text="MoveDuration", relief=tk.RIDGE)
        self.movetime_label.config(font=("Courier", 12))
        self.movetime_label.pack(side="top")
        self.move_duration = StringVar(move)
        self.move_duration.set(10) # initial value
        self.move_duration = OptionMenu(move, self.move_duration, 2, 5,10,20,30,60,120)
        self.move_duration.pack(side="bottom")
        

        #exit application
        self.quit = tk.Button(wayPoint_controls, text="QUIT", fg="red",
                              command=self.quit)
        self.quit.pack(side="bottom")

    def say_hi(self):
        print("hi there, everyone!")


    def toggle_control(self,value):
        print("toggle control to")
        print(value)
        self.CONTROL_TOGGLE = value

    def toggle_move_mode(self,value):
        print("toggle move mode to")
        print(value)
        self.MOVE_TOGGLE = value

   

    def set_feed_rate(self, feedval):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            print("updating feeddefault from {} to {}".format(
                feedval, self.gimbal_inst.get_feed_speed()))
            self.gimbal_inst.set_feed_speed(feedval)
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            print("updating crane feeddefault from {} to {}".format(
                feedval, self.crane_inst.get_feed_speed()))
            self.crane_inst.set_feed_speed(feedval)

    def set_delay_rate(self,val):
        print("set crane delay to {}".format(val))
        self.crane_inst.set_command_delay(val)



    def set_move_time(self,seconds):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            print("updating gimbal move time from {} to {}".format(
                seconds, self.gimbal_inst.get_move_duration()))
            self.gimbal_inst.set_move_duration(seconds)
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            print("updating crane move time from {} to {}".format(
                seconds, self.crane_inst.get_move_duration()))
            self.crane_inst.set_move_duration(seconds)


    def add_waypoint(self,dwell_input_text):
        print("add waypoint")  # (x, y, z,focus, feed), dwell time
        crane_position = self.crane_inst.get_current_location()
        gimbal_position = self.gimbal_inst.get_current_location()
        wp = waypoint(
            location(crane_position.get_rotation_pos(), crane_position.get_tilt_pos(),crane_position.get_zoom_pos()),
            location(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()))
        wp.set_dwell_time(self.dwell_time.get())
        wp.set_gimbal_travel_to_feed_rate(self.gimbal_inst.get_feed_speed())
        wp.set_crane_travel_to_feed_rate(self.crane_inst.get_feed_speed())
        wp.set_gimbal_travel_to_duration(self.gimbal_inst.get_move_duration())
        wp.set_crane_travel_to_duration(self.crane_inst.get_move_duration())
        self.sequence_steps.add_waypoint(wp)
        self.waypoint_listbox.insert("end","{} dwell for:{}".format(wp.location_str(),self.dwell_time.get()))

    def delete_waypoint(self):
        # todo allow for deleting specific waypoint item
        self.sequence_steps.delete_waypoint()
        self.waypoint_listbox.delete(self.waypoint_listbox.size()-1,self.waypoint_listbox.size())
            
        
    def trigger_whole_sequence(self):
        if len(self.sequence_steps.waypoints) > 0:
            for i in range(len(self.sequence_steps.waypoints)): 
        
            #for wp in sequence_steps.waypoints:
                if self.MOVE_TOGGLE == self.FEED_RATE:
                    self.crane_inst.add_waypoint_by_feedrate_to_sequqnce(sequence_steps.waypoints[i].get_crane_position(), sequence_steps.waypoints[i].get_crane_travel_to_feed_rate(),sequence_steps.waypoints[i].get_dwell_time())
                    self.gimbal_inst.add_waypoint_by_feedrate_to_sequqnce(sequence_steps.waypoints[i].get_gimbal_position(), sequence_steps.waypoints[i].get_gimbal_travel_to_feed_rate(),sequence_steps.waypoints[i].get_dwell_time())
                if self.MOVE_TOGGLE == self.MOVE_TIME:
                    self.crane_inst.add_waypoint_by_time_to_sequqnce(sequence_steps.waypoints[i].get_crane_position(),sequence_steps.waypoints[i].get_crane_travel_to_duration(),sequence_steps.waypoints[i].get_dwell_time())
                    self.gimbal_inst.add_waypoint_by_time_to_sequqnce(sequence_steps.waypoints[i].get_gimbal_position(), sequence_steps.waypoints[i].get_gimbal_travel_to_duration(),sequence_steps.waypoints[i].get_dwell_time())
        print("===========")
        print("built crane sequence")
        self.crane_inst.get_current_gcode_sequence("crane")
        print("===========")
        print("built gimbal sequence")
        self.gimbal_inst.get_current_gcode_sequence("gimbal")
        print("===========")

        self.crane_inst.trigger_sequence("crane")
        self.gimbal_inst.trigger_sequence("gimbal")
        #set location to last wp


    def save_point_move(self,savepoint):
        if self.MOVE_TOGGLE == self.FEED_RATE:
            self.crane_inst.move_to_position_at_rate(savepoint.get_crane_position())
            self.gimbal_inst.move_to_position_at_rate(savepoint.get_gimbal_position())
        if self.MOVE_TOGGLE == self.MOVE_TIME:
            self.crane_inst.move_to_position_in_time(savepoint.get_crane_position())
            self.gimbal_inst.move_to_position_in_time(savepoint.get_gimbal_position())
            

    def save_position(self,savepoint):
        
        crane_position = self.crane_inst.get_current_location()
        gimbal_position = self.gimbal_inst.get_current_location()
        new_waypoint = waypoint(
            location(crane_position.get_rotation_pos(), crane_position.get_tilt_pos(),0),
            location(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()))
        if savepoint == 1:
            self.save_position_1 = new_waypoint
            sp1_pos_text['text'] = "Y/LB : {}".format(new_waypoint.location_str)
        if savepoint == 2:
            self.ave_position_2 = new_waypoint
            sp2_pos_text['text'] = "B/RB : {}".format(new_waypoint.location_str)
        if savepoint == 3:
            self.save_position_3 = new_waypoint
            sp3_pos_text['text'] = "X/L1 : {}".format(new_waypoint.location_str)
        if savepoint == 4:
            self.save_position_4 = new_waypoint
            sp4_pos_text['text'] = "A/R1 : {}".format(new_waypoint.location_str)

    def reset():
        
        self.crane_inst.reset()
        self.gimbal_inst.reset()

        self.save_position_1 = waypoint(location(0, 0,0), location(0, 0, 0))
        self.save_position_2 = waypoint(location(0, 0,0), location(0, 0, 0))
        self.save_position_3 = waypoint(location(0, 0,0), location(0, 0, 0))
        self.save_position_4 = waypoint(location(0, 0,0), location(0, 0, 0))
        sp1_pos_text['text'] = "Y/LB : {}".format(new_waypoint.location_str)
        sp1_pos_text['text'] = "B/RB : {}".format(new_waypoint.location_str)
        sp1_pos_text['text'] = "X/L1 : {}".format(new_waypoint.location_str)
        sp1_pos_text['text'] = "A/R1 : {}".format(new_waypoint.location_str)

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