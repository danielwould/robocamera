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
from helpers.grbl_controller import grbl_controller
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
       
        self.controller=grbl_controller(MOCK,0)
        self.controller.set_device("/dev/ttyACM0", 115200,"CameraArm")
        #self.controller.set_device("COM3", 115200,"CameraArm")

        self.gimbal_inst = gimbal("x","y","z", self.controller)
        self.gimbal_inst.set_small_step_rotate(0.2)
        self.gimbal_inst.set_big_step_rotate(2)
        self.gimbal_inst.set_small_step_tilt(0.2)
        self.gimbal_inst.set_big_step_tilt(2)
        self.crane_inst = crane("a","b","b",self.controller)
        self.controller.reset()

    def init_joysticks(self):
        self.joy = Joystick(self, self.gimbal_inst, self.crane_inst)

    def init_info_updater(self):
        self.info_update = info(self)


    def create_widgets(self):

        #
        #controller location display
        #
        left = Frame(self,relief=tk.SUNKEN)
        left.pack(side="left")
        
        location_info = Frame(left,relief=tk.RIDGE)
        location_info.pack(side="top") 

        self.pos_text = tk.Label(location_info,text="Pos", relief=tk.RIDGE)
        self.pos_text.config(font=("Courier", 16))
        self.pos_text.pack(side="left", padx=10)
        
        info = Frame(left,relief=tk.SUNKEN)
        info.pack(side="left")
        #
        #savepoints
        #
        savepoint_info = Frame(info,relief=tk.RIDGE)
        savepoint_info.pack(side="top")
        savepoint_saves = Frame (savepoint_info)
        savepoint_saves.pack(side="left")
        savepoint_moves = Frame (savepoint_info)
        savepoint_moves.pack(side="right")
        self.set_savepoint_1 = tk.Button(savepoint_saves, text="Save", fg="#ffcc33", bg="#333333", command=lambda :self.save_position(1))
        self.set_savepoint_1.config(font=("Courier", 5))
        self.set_savepoint_1.pack(side="top", padx=2, pady=2)
        self.set_savepoint_2 = tk.Button(savepoint_saves, text="Save", fg="#ffcc33", bg="#333333",
                                         command=lambda: self.save_position(2))
        self.set_savepoint_2.config(font=("Courier", 5))
        self.set_savepoint_2.pack(side="top", padx=2, pady=2)
        self.set_savepoint_3 = tk.Button(savepoint_saves, text="Save", fg="#ffcc33", bg="#333333",
                                         command=lambda: self.save_position(3))
        self.set_savepoint_3.config(font=("Courier", 5))
        self.set_savepoint_3.pack(side="top", padx=2, pady=2)
        self.set_savepoint_4 = tk.Button(savepoint_saves, text="Save", fg="#ffcc33", bg="#333333",
                                         command=lambda: self.save_position(4))
        self.set_savepoint_4.config(font=("Courier", 5))
        self.set_savepoint_4.pack(side="top", padx=2, pady=2)

        self.sp1_pos_text = tk.Label(savepoint_info,text="Y/LB", relief=tk.RIDGE)
        self.sp1_pos_text.config(font=("Courier", 8))
        self.sp1_pos_text.pack(pady=5)

        self.sp2_pos_text = tk.Label(savepoint_info,text="B/RB", relief=tk.RIDGE)
        self.sp2_pos_text.config(font=("Courier", 8))
        self.sp2_pos_text.pack(pady=5)

        self.sp3_pos_text = tk.Label(savepoint_info,text="X/L1", relief=tk.RIDGE)
        self.sp3_pos_text.config(font=("Courier", 8))
        self.sp3_pos_text.pack(pady=5)

        self.sp4_pos_text = tk.Label(savepoint_info,text="A/R1", relief=tk.RIDGE)
        self.sp4_pos_text.config(font=("Courier", 8))
        self.sp4_pos_text.pack(pady=5)

        self.move_savepoint_1 = tk.Button(savepoint_moves, text="Move", fg="#ffcc33", bg="#333333",
                                        command=lambda: self.save_point_move(self.save_position_1))
        self.move_savepoint_1.config(font=("Courier", 5))
        self.move_savepoint_1.pack(side="top", padx=2, pady=2)
        self.move_savepoint_2 = tk.Button(savepoint_moves, text="Move", fg="#ffcc33", bg="#333333",
                                         command=lambda: self.save_point_move(self.save_position_2))
        self.move_savepoint_2.config(font=("Courier", 5))
        self.move_savepoint_2.pack(side="top", padx=2, pady=2)
        self.move_savepoint_3 = tk.Button(savepoint_moves, text="Move", fg="#ffcc33", bg="#333333",
                                         command=lambda: self.save_point_move(self.save_position_3))
        self.move_savepoint_3.config(font=("Courier", 5))
        self.move_savepoint_3.pack(side="top", padx=2, pady=2)
        self.move_savepoint_4 = tk.Button(savepoint_moves, text="Move", fg="#ffcc33", bg="#333333",
                                         command=lambda: self.save_point_move(self.save_position_4))
        self.move_savepoint_4.config(font=("Courier", 5))
        self.move_savepoint_4.pack(side="top", padx=2, pady=2)
        #waypoints

        self.waypoint_start = tk.Button(info, text="Run", fg="#ffcc33", bg="#333333",
                                        command=self.trigger_whole_sequence)
        self.waypoint_start.config(font=("Courier", 5))
        self.waypoint_start.pack(side="bottom")
        self.waypoint_listbox = Listbox(info, width=60)
        self.waypoint_listbox.pack(side="bottom")



        right_side = Frame(self,relief=tk.RIDGE)
        right_side.pack(side="right")
        #
        #on screen move controls
        #
        Motion_controls = Frame(right_side,relief=tk.RIDGE)
        Motion_controls.pack(side="top")
        self.up = tk.Button(Motion_controls, text="U", fg="#ffcc33",bg="#333333", command=self.tilt_up)
        self.up.config(font=("Courier", 22))
        self.up.pack(side="top", padx=2,pady=2)
        self.left = tk.Button(Motion_controls, text="L", fg="#ffcc33",bg="#333333", command=self.rotate_left)
        self.left.config(font=("Courier", 22))
        self.left.pack(side="left", padx=2,pady=2)
        self.right = tk.Button(Motion_controls, text="R", fg="#ffcc33",bg="#333333", command=self.rotate_right)
        self.right.config(font=("Courier", 22))
        self.right.pack(side="right", padx=2,pady=2)
        self.down = tk.Button(Motion_controls, text="D", fg="#ffcc33",bg="#333333", command=self.tilt_down)
        self.down.config(font=("Courier", 22))
        self.down.pack(side="bottom", padx=2,pady=2)

        #
        #controls that toggle behaviour
        #
        Toggle_controls = Frame(right_side,relief=tk.GROOVE)
        Toggle_controls.pack(side="top")

        controller_select = Frame(Toggle_controls,relief=tk.GROOVE)
        controller_select.pack(side="top")
        button_pairs = Frame(controller_select,relief=tk.GROOVE)
        button_pairs.pack(side="left")
        self.gimbalToggle = tk.Button(button_pairs, text="Gimbal", fg="#ffcc33",bg="#333333", command=lambda: self.toggle_control(self.GIMBAL_CONTROL))
        self.gimbalToggle.pack(side="top", padx=2,pady=2)
        self.craneToggle = tk.Button(button_pairs, text="Crane", fg="#ffcc33",bg="#333333", command=lambda: self.toggle_control(self.CRANE_CONTROL))
        self.craneToggle.pack(side="bottom", padx=2,pady=2)
        move_select = Frame(controller_select,relief=tk.GROOVE)
        move_select.pack(side="right")
        self.moveFeedToggle = tk.Button(move_select, text="Feed mm/s", fg="#ffcc33",bg="#333333", command=lambda: self.toggle_move_mode(self.FEED_RATE))
        self.moveFeedToggle.pack(side="top", padx=2,pady=2)
        self.moveTimeToggle = tk.Button(move_select, text="Move Time", fg="#ffcc33",bg="#333333", command=lambda: self.toggle_move_mode(self.MOVE_TIME))
        self.moveTimeToggle.pack(side="bottom", padx=2,pady=2)

        #
        #manipulate waypoints
        #
        wayPoint_controls = Frame(Toggle_controls,relief=tk.RIDGE)
        wayPoint_controls.pack(side="top")
        self.addWaypoint = tk.Button(wayPoint_controls, text="Add Waypoint", fg="#333333",bg="#ffcc33",
                              command=lambda: self.add_waypoint(self.dwell_time.get()))
        self.addWaypoint.pack(padx=2,pady=2)
        self.deleteWaypoint = tk.Button(wayPoint_controls, text="Del Waypoint", fg="#333333",bg="#ffcc33",
                              command=self.delete_waypoint)
        self.deleteWaypoint.pack(padx=2,pady=2)

        options_controls = Frame(left,relief=tk.GROOVE)
        options_controls.pack(side="right")

        dwell = Frame(options_controls)
        dwell.pack(side="top")
        self.dwell_label = tk.Label(dwell,text="DwellTime", relief=tk.RIDGE)
        self.dwell_label.config(font=("Courier", 12))
        self.dwell_label.pack(side="top")
        self.dwell_time = StringVar(dwell)
        self.dwell_time.set(1) # initial value
        self.dwell_select = OptionMenu(dwell, self.dwell_time, 1, 2,5,10,15,20)
        self.dwell_select.pack(side="bottom")

        feed = Frame(options_controls)
        feed.pack(side="top")
        self.feedrate_label = tk.Label(feed,text="FeedRate", relief=tk.RIDGE)
        self.feedrate_label.config(font=("Courier", 12))
        self.feedrate_label.pack(side="top")
        self.feed_rate = StringVar(feed)
        self.feed_rate.set(1000) # initial value
        self.feed_rate = OptionMenu(feed, self.feed_rate, 100, 200,500,700,1000,1500)
        self.feed_rate.pack(side="bottom")

        move = Frame(options_controls)
        move.pack(side="top")
        self.movetime_label = tk.Label(move,text="MoveDuration", relief=tk.RIDGE)
        self.movetime_label.config(font=("Courier", 12))
        self.movetime_label.pack(side="top")
        self.move_duration = StringVar(move)
        self.move_duration.trace("w",self.set_move_time)
        self.move_duration.set(10) # initial value
        self.move_duration_select = OptionMenu(move, self.move_duration, 2, 5,10,20,30,60,120)
        self.move_duration_select.pack(side="bottom")
        
        self.crane_delay = Scale(options_controls, from_=0, to=2000, tickinterval=100)
        self.crane_delay.set(500)
        self.crane_delay.pack()
        #exit application
        self.quit = tk.Button(wayPoint_controls, text="QUIT", fg="red",
                              command=self.quit)
        self.quit.pack(side="bottom", pady=50)

    def toggle_control(self,value):
        print("toggle control to")
        print(value)
        self.CONTROL_TOGGLE = value
        
    def toggle_move_mode(self,value):
        print("toggle move mode to")
        print(value)
        self.MOVE_TOGGLE = value

   

    def set_feed_rate(self, feedval):
        print("updating feeddefault from {} to {}".format(
               feedval, self.controller.get_feed_speed()))
        self.controller.set_feed_speed(feedval)
        

    def set_move_time(self, *args):
        self.controller.set_move_duration(int(self.move_duration.get()))
        


    def add_waypoint(self,dwell_input_text):
        print("add waypoint")  # (x, y, z,focus, feed), dwell time
        crane_position = self.crane_inst.get_current_location()
        gimbal_position = self.gimbal_inst.get_current_location()
        wp = waypoint(
            location(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()),
            location(crane_position.get_rotation_pos(), crane_position.get_tilt_pos(),crane_position.get_zoom_pos())
            )
        wp.set_dwell_time(self.dwell_time.get())
        wp.set_feed_rate(self.controller.get_feed_speed())
        wp.set_travel_duration(self.controller.get_move_duration())
       
        self.sequence_steps.add_waypoint(wp)
        self.waypoint_listbox.insert("end","{} dwell for:{}".format(wp.location_str(),self.dwell_time.get()))

    def delete_waypoint(self):
        # todo allow for deleting specific waypoint item
        self.sequence_steps.delete_waypoint()
        self.waypoint_listbox.delete(self.waypoint_listbox.size()-1,self.waypoint_listbox.size())
            
        
    def trigger_whole_sequence(self):
        self.crane_inst.set_command_delay(self.crane_delay.get())
        if len(self.sequence_steps.waypoints) > 0:
            for i in range(len(self.sequence_steps.waypoints)): 
        
            #for wp in sequence_steps.waypoints:
                if self.MOVE_TOGGLE == self.FEED_RATE:
                    self.controller.add_absolute_move_by_feed_to_sequence(self.sequence_steps.waypoints[i].xpos,self.sequence_steps.waypoints[i].ypos,self.sequence_steps.waypoints[i].zpos,self.sequence_steps.waypoints[i].apos,self.sequence_steps.waypoints[i].bpos,self.sequence_steps.waypoints[i].get_feed_rate(),self.sequence_steps.waypoints[i].get_dwell_time() )
                if self.MOVE_TOGGLE == self.MOVE_TIME:
                    self.controller.add_absolute_move_by_time_to_sequence(self.sequence_steps.waypoints[i].xpos,self.sequence_steps.waypoints[i].ypos,self.sequence_steps.waypoints[i].zpos,self.sequence_steps.waypoints[i].apos,self.sequence_steps.waypoints[i].bpos,self.sequence_steps.waypoints[i].get_travel_duration(),self.sequence_steps.waypoints[i].get_dwell_time())
                    
        
        self.controller.print_gcode_sequence()
        

        self.controller.run_sequence()
        
        #set location to last wp


    def save_point_move(self,savepoint):
        self.crane_inst.set_command_delay(self.crane_delay.get())
        
        if self.MOVE_TOGGLE == self.FEED_RATE:
            self.controller.absolute_move(savepoint.xpos,savepoint.ypos,savepoint.xpos, savepoint.apos,savepoint.bpos,savepoint.get_feed_rate(),savepoint.get_dwell_time())
        if self.MOVE_TOGGLE == self.MOVE_TIME:
            self.controller.absolute_move_by_time(savepoint.xpos,savepoint.ypos,savepoint.zpos, savepoint.apos,savepoint.bpos,savepoint.get_travel_duration(),savepoint.get_dwell_time())
            

    def save_position(self,savepoint):
        
        crane_position = self.crane_inst.get_current_location()
        gimbal_position = self.gimbal_inst.get_current_location()
        new_waypoint = waypoint(
            location(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()),
            location(crane_position.get_rotation_pos(), crane_position.get_tilt_pos(),0)
            )
        if savepoint == 1:
            self.save_position_1 = new_waypoint
            self.sp1_pos_text['text'] = "Y/LB : {}".format(new_waypoint.location_str())
        if savepoint == 2:
            self.save_position_2 = new_waypoint
            self.sp2_pos_text['text'] = "B/RB : {}".format(new_waypoint.location_str())
        if savepoint == 3:
            self.save_position_3 = new_waypoint
            self.sp3_pos_text['text'] = "X/L1 : {}".format(new_waypoint.location_str())
        if savepoint == 4:
            self.save_position_4 = new_waypoint
            self.sp4_pos_text['text'] = "A/R1 : {}".format(new_waypoint.location_str())

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
    root.geometry("800x400")
    app = RobotCamera(master=root)
    app.mainloop()