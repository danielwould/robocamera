# dev notes
# select waypoint for editing - modify/delete

# abort sequence
# pause/resume sequence
# step backward/forward through sequence


from threading import current_thread
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
from helpers.tracking.aruco_tracker import aruco_tracker
import os
import sys
import json
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
        self.TRACKING = False
        self.TRACKING_RENDER = False
        self.trackingId =1
        self.timelapse_time = 600
        self.timelapse_steps = 3
        self.save_position_1 = waypoint(1,location(0, 0, 0), location(0, 0, 0))
        self.save_position_2 = waypoint(2,location(0, 0, 0), location(0, 0, 0))
        self.save_position_3 = waypoint(3,location(0, 0, 0), location(0, 0, 0))
        self.save_position_4 = waypoint(4,location(0, 0, 0), location(0, 0, 0))
        self.first_move=False
        self.sequence_steps = sequence()
        
        self.init_controllers()
        self.init_joysticks()
        self.init_info_updater()
        self.pack()
        self.create_widgets()

    def init_controllers(self):
        
        self.controller=grbl_controller(0)
        
        if sys.platform == "win32":
            print("connecting to windows com device")
            self.controller.set_device("COM7", 115200,"CameraArm")
        else:
            print("connecting to linux tty device")
            self.controller.set_device("/dev/ttyACM0", 115200,"CameraArm")


        self.gimbal_inst = gimbal("x","y","z", self.controller)
        self.gimbal_inst.set_small_step_rotate(0.2)
        self.gimbal_inst.set_big_step_rotate(2)
        self.gimbal_inst.set_small_step_tilt(0.2)
        self.gimbal_inst.set_big_step_tilt(2)
        self.crane_inst = crane("a","b","b",self.controller)
        self.crane_inst.set_small_step_rotate(2)
        self.crane_inst.set_big_step_rotate(10)
        self.crane_inst.set_small_step_tilt(2)
        self.crane_inst.set_big_step_tilt(10)
        #self.controller.reset()
        self.tracker = aruco_tracker(self.controller,self)
        self.tracker.initialise_video()


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
        self.status_text = tk.Label(location_info,text="status", relief=tk.RIDGE)
        self.status_text.config(font=("Courier", 16))
        self.status_text.pack(side="top", padx=10)
        self.pos_text = tk.Label(location_info,text="Pos", relief=tk.RIDGE)
        self.pos_text.config(font=("Courier", 16))
        self.pos_text.pack(side="left", padx=10)
        
        info = Frame(left,relief=tk.SUNKEN)
        info.pack(side="left")
        transmission_buffer = Frame(info,relief=tk.RIDGE)
        transmission_buffer.pack(side="top")
        self.transbuffer_text = tk.Label(transmission_buffer,text="Pos", relief=tk.RIDGE)
        self.transbuffer_text.config(font=("Courier", 12))
        self.transbuffer_text.pack(side="left", padx=10)
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

        move_select = Frame(Toggle_controls,relief=tk.GROOVE)
        move_select.pack()
        self.moveFeedToggle = tk.Button(move_select, text="Feed mm/s", fg="#ffcc33",bg="#333333", command=lambda: self.toggle_move_mode(self.FEED_RATE))
        self.moveFeedToggle.pack(padx=2,pady=2)
        self.moveTimeToggle = tk.Button(move_select, text="Move Time", fg="#ffcc33",bg="#333333", command=lambda: self.toggle_move_mode(self.MOVE_TIME))
        self.moveTimeToggle.pack(padx=2,pady=2)
        self.trackingToggle = tk.Button(move_select, text="Tracking", fg="#ffcc33",bg="#333333", command=self.toggle_tracking_mode)
        self.trackingToggle.pack(padx=2,pady=2)
        self.trackingToggle1 = tk.Button(move_select, text="Track 1", fg="#ffcc33",bg="#333333", command=lambda: self.set_tracking_id(1))
        self.trackingToggle1.pack(padx=2,pady=2)
        self.trackingToggle2 = tk.Button(move_select, text="Centre Tracker", fg="#ffcc33",bg="#333333", command=lambda: self.set_tracking_id(2))
        self.trackingToggle2.pack(padx=2,pady=2)
        self.trackingToggle3 = tk.Button(move_select, text="1/3 Tracker", fg="#ffcc33",bg="#333333", command=lambda: self.set_tracking_id(3))
        self.trackingToggle3.pack(padx=2,pady=2)
        self.trackingRenderToggle = tk.Button(move_select, text="TrackRender", fg="#ffcc33",bg="#333333", command=self.toggle_tracking_render)
        self.trackingRenderToggle.pack(padx=2,pady=2)
        #
        #manipulate waypoints
        #
        wayPoint_controls = Frame(Toggle_controls,relief=tk.RIDGE)
        wayPoint_controls.pack(side="top")
        self.addWaypoint = tk.Button(wayPoint_controls, text="Add Waypoint", fg="#333333",bg="#ffcc33",
                              command= self.add_waypoint)
        self.addWaypoint.pack(padx=2,pady=2)
        self.deleteWaypoint = tk.Button(wayPoint_controls, text="Del Waypoint", fg="#333333",bg="#ffcc33",
                              command=self.delete_waypoint)
        self.deleteWaypoint.pack(padx=2,pady=2)
        self.editWaypoint = tk.Button(wayPoint_controls, text="Edit Waypoint", fg="#333333",bg="#ffcc33",
                              command=self.edit_waypoint)
        self.editWaypoint.pack(padx=2,pady=2)

        self.setCraneTiltMax = tk.Button(wayPoint_controls, text="Crane Tilt Max", fg="#333333",bg="#ffcc33",
                              command=self.controller.set_crane_tilt_max)
        self.setCraneTiltMax.pack(padx=2,pady=2)
        self.setCraneTiltMin = tk.Button(wayPoint_controls, text="Crane Tilt Min", fg="#333333",bg="#ffcc33",
                              command=self.controller.set_crane_tilt_min)
        self.setCraneTiltMin.pack(padx=2,pady=2)
        self.setGimbalTiltMax = tk.Button(wayPoint_controls, text="Gimbal Tilt Max", fg="#333333",bg="#ffcc33",
                              command=self.controller.set_gimbal_tilt_max)
        self.setGimbalTiltMax.pack(padx=2,pady=2)
        self.setGimbalTiltMin = tk.Button(wayPoint_controls, text="Gimabl Tilt Min", fg="#333333",bg="#ffcc33",
                              command=self.controller.set_gimbal_tilt_min)
        self.setGimbalTiltMin.pack(padx=2,pady=2)

        self.setInitPosition = tk.Button(wayPoint_controls, text="Init Position", fg="#333333",bg="#ffcc33",
                              command=self.set_initial_pos)
        self.setInitPosition.pack(padx=2,pady=2)
        
        self.timelapse = tk.Button(wayPoint_controls, text="Timelapse", fg="#333333",bg="#ffcc33",
                              command=self.timelapse)
        self.timelapse.pack(padx=2,pady=2)

        options_controls = Frame(left,relief=tk.GROOVE)
        options_controls.pack(side="right")

        dwell = Frame(options_controls)
        dwell.pack(side="top")
        self.dwell_label = tk.Label(dwell,text="DwellTime", relief=tk.RIDGE)
        self.dwell_label.config(font=("Courier", 12))
        self.dwell_label.pack(side="top")
        self.dwell_time = StringVar(dwell)
        self.dwell_time.set(0) # initial value
        self.dwell_select = OptionMenu(dwell, self.dwell_time, 0,1, 2,5,10,15,20,30)
        self.dwell_select.pack(side="bottom")

        feed = Frame(options_controls)
        feed.pack(side="top")
        self.feedrate_label = tk.Label(feed,text="FeedRate", relief=tk.RIDGE)
        self.feedrate_label.config(font=("Courier", 12))
        self.feedrate_label.pack(side="top")
        self.feed_rate = StringVar(feed)
        self.feed_rate.trace("w",self.set_feed_rate)
        self.feed_rate.set(1000) # initial value
        self.feed_rate = OptionMenu(feed, self.feed_rate, 100, 200,500,700,1000,1500,2000,2500,3000)
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
        
        timelapse_total = Frame(options_controls)
        timelapse_total.pack(side="top")
        self.timelapse_label = tk.Label(timelapse_total,text="TimelapseDuration", relief=tk.RIDGE)
        self.timelapse_label.config(font=("Courier", 12))
        self.timelapse_label.pack(side="top")
        self.timelapse_duration = StringVar(timelapse_total)
        self.timelapse_duration.trace("w",self.set_timelapse_time)
        self.timelapse_duration.set(600) # initial value
        self.timelapse_duration_select = OptionMenu(timelapse_total, self.timelapse_duration, 600, 1200,1800,2400)
        self.timelapse_duration_select.pack(side="bottom")
        
        timelapse_interval = Frame(options_controls)
        timelapse_interval.pack(side="top")
        self.timelapseInterval_label = tk.Label(timelapse_interval,text="TimelapseInterval", relief=tk.RIDGE)
        self.timelapseInterval_label.config(font=("Courier", 12))
        self.timelapseInterval_label.pack(side="top")
        self.timelapse_stepinterval = StringVar(timelapse_interval)
        self.timelapse_stepinterval.trace("w",self.set_timelapse_steps)
        self.timelapse_stepinterval.set(3) # initial value
        self.timelapse_stepinterval_select = OptionMenu(timelapse_interval, self.timelapse_stepinterval, 1,2,3,4,5,6,7,8,9,10)
        self.timelapse_stepinterval_select.pack(side="bottom")


        self.loadstate = tk.Button(wayPoint_controls, text="Load State", fg="black",
                              command=self.load_state_from_file)
        self.loadstate.pack(padx=2, pady=2)
        
        self.reset = tk.Button(wayPoint_controls, text="RESET", fg="red",
                              command=self.controller.reset)
        self.reset.pack(padx=2, pady=2)

        self.dump_buffer = tk.Button(wayPoint_controls, text="EtyBuf", fg="red",
                              command=self.controller.emptybuffer)
        self.dump_buffer.pack(padx=2, pady=2)
        self.quit = tk.Button(wayPoint_controls, text="QUIT", fg="red",
                              command=self.quit)
        self.quit.pack(padx=2, pady=20)
    
        
    def timelapse(self):
        #trigger a timelapse from current position to Save position 2
        savepoint = self.save_position_2
        self.controller.absolute_move_timelapse(savepoint.xpos,savepoint.ypos,savepoint.zpos, savepoint.apos,savepoint.bpos, self.timelapse_time,  self.timelapse_steps)

    def set_initial_pos(self):
        #initial position should be min gimbal tilt, max crane tilt, middle position pan on both, zoom all the way out
        self.controller.set_crane_pan_middle()
        self.controller.set_crane_tilt_max()
        self.controller.set_gimbal_pan_middle()
        self.controller.set_gimbal_tilt_min()
        self.controller.set_zoom_min()

    def toggle_move_mode(self,value):
        print("toggle move mode to")
        print(value)
        self.MOVE_TOGGLE = value

    def set_tracking_id(self,id):
        self.trackingId = id
        self.tracker.set_tracking_target(id)

    def toggle_tracking_mode(self):
        print("toggle tracking")
        if (self.TRACKING == True):
            self.TRACKING = False
            self.tracker.stop_tracking()
        else:
            self.TRACKING = True
            self.tracker.start_tracking(self.trackingId)

    def toggle_tracking_render(self):
        print("toggle tracking render")
        if (self.TRACKING_RENDER == True):
            self.TRACKING_RENDER = False
            self.tracker.render_tracker(False)
        else:
            self.TRACKING_RENDER = True
            self.tracker.render_tracker(True)


    def set_feed_rate(self, feedval):
        print("updating feeddefault from {} to {}".format(
               feedval, self.controller.get_feed_speed()))
        self.controller.set_feed_speed(feedval)
        

    def set_move_time(self, *args):
        self.controller.set_move_duration(int(self.move_duration.get()))

    def set_timelapse_time(self, *args):
        self.timelapse_time = (int(self.timelapse_duration.get()))
        
    def set_timelapse_steps(self, *args):
        self.timelapse_steps = (int(self.timelapse_stepinterval.get()))

    def add_waypoint(self):
        skip_waypoint=False
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
        new_waypoint_str = "{} dwell for:{}".format(wp.location_str(),self.dwell_time.get())
            
        if (self.waypoint_listbox.size() > 0):
            index = self.waypoint_listbox.size()-1
            
            last_waypoint = self.sequence_steps.get_step(index)
            if (last_waypoint == new_waypoint_str):
                skip_waypoint=True
        if (skip_waypoint == False):
            self.sequence_steps.add_waypoint(wp)
            self.waypoint_listbox.insert("end",new_waypoint_str)

    def delete_waypoint(self):
        # todo allow for deleting specific waypoint item
        
        selected = self.waypoint_listbox.curselection()
        if selected:
            self.waypoint_listbox.delete(selected)
            self.sequence_steps.delete_waypoint(index=selected[0])
        else:
            self.waypoint_listbox.delete(self.waypoint_listbox.size()-1,self.waypoint_listbox.size())
            self.sequence_steps.delete_waypoint()
            
        
    def edit_waypoint(self):
        selected = self.waypoint_listbox.curselection()
        if selected:
            index = selected[0]
            
        else:
            index = self.waypoint_listbox.size()-1
            
        waypoint_to_edit = self.sequence_steps.get_step(index)
        self.editwaypoint=editWaypointPopup(self.master, waypoint_to_edit)
        self.master.wait_window(self.editwaypoint.top)
        print("edited waypoint value {} {}".format(self.editwaypoint.value.location_str(),self.editwaypoint.value.get_feed_info()))
        self.sequence_steps.update_waypoint(index, self.editwaypoint.value)
        self.waypoint_listbox.insert(index,"{} dwell for:{}".format(self.editwaypoint.value.location_str(),self.editwaypoint.value.get_dwell_time()))
        self.waypoint_listbox.delete(index+1)
    
    def entryValue(self):
        return self.editwaypoint.value
        




    def trigger_whole_sequence(self):
        #turn off tracking if it's on
        was_tracking = False
        if (self.TRACKING == True):
            self.TRACKING = False
            self.tracker.pause_tracking()
            was_tracking = True
        
        if len(self.sequence_steps.waypoints) > 0:
            for i in range(len(self.sequence_steps.waypoints)): 
        
            #for wp in sequence_steps.waypoints:
                if self.MOVE_TOGGLE == self.FEED_RATE:
                    self.controller.add_absolute_move_by_feed_to_sequence(self.sequence_steps.waypoints[i].xpos,self.sequence_steps.waypoints[i].ypos,self.sequence_steps.waypoints[i].zpos,self.sequence_steps.waypoints[i].apos,self.sequence_steps.waypoints[i].bpos,self.sequence_steps.waypoints[i].get_feed_rate(),self.sequence_steps.waypoints[i].get_dwell_time() )
                if self.MOVE_TOGGLE == self.MOVE_TIME:
                    self.controller.add_absolute_move_by_time_to_sequence(self.sequence_steps.waypoints[i].xpos,self.sequence_steps.waypoints[i].ypos,self.sequence_steps.waypoints[i].zpos,self.sequence_steps.waypoints[i].apos,self.sequence_steps.waypoints[i].bpos,self.sequence_steps.waypoints[i].get_travel_duration(),self.sequence_steps.waypoints[i].get_dwell_time())
                    
        
        self.controller.print_gcode_sequence()
        self.controller.run_sequence()
        if (was_tracking):
            self.TRACKING = True
            self.tracker.resume_tracking()
        
        #set location to last wp


    def save_point_move(self,savepoint):
        
        if self.MOVE_TOGGLE == self.FEED_RATE:
            self.controller.absolute_move(savepoint.xpos,savepoint.ypos,savepoint.zpos, savepoint.apos,savepoint.bpos,self.controller.get_feed_speed(),savepoint.get_dwell_time())
        if self.MOVE_TOGGLE == self.MOVE_TIME:
            self.controller.absolute_move_by_time(savepoint.xpos,savepoint.ypos,savepoint.zpos, savepoint.apos,savepoint.bpos,self.controller.get_move_duration(),savepoint.get_dwell_time())
            

    def save_position(self,savepoint):
        
        crane_position = self.crane_inst.get_current_location()
        gimbal_position = self.gimbal_inst.get_current_location()
        new_waypoint = waypoint(savepoint,
            location(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()),
            location(crane_position.get_rotation_pos(), crane_position.get_tilt_pos(),0)
            )
        #new_waitpoint.set_feed_rate(self.controller.get_feed_speed())
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

        self.save_position_1 = waypoint(1,location(0, 0,0), location(0, 0, 0))
        self.save_position_2 = waypoint(2,location(0, 0,0), location(0, 0, 0))
        self.save_position_3 = waypoint(3,location(0, 0,0), location(0, 0, 0))
        self.save_position_4 = waypoint(4,location(0, 0,0), location(0, 0, 0))
        self.sp1_pos_text['text'] = "Y/LB : {}".format(new_waypoint.location_str())
        self.sp2_pos_text['text'] = "B/RB : {}".format(new_waypoint.location_str())
        self.sp3_pos_text['text'] = "X/L1 : {}".format(new_waypoint.location_str())
        self.sp4_pos_text['text'] = "A/R1 : {}".format(new_waypoint.location_str())

    def tilt_up(self):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            self.gimbal_inst.tilt_jog(1)
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            self.crane_inst.tilt_jog(1)


    def tilt_down(self):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            self.gimbal_inst.tilt_jog(-1)
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            self.crane_inst.tilt_jog(-1)


    def rotate_left(self):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            self.gimbal_inst.rotate_jog(1)
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            self.crane_inst.rotate_jog(-1)


    def rotate_right(self):
        if self.CONTROL_TOGGLE == self.GIMBAL_CONTROL:
            self.gimbal_inst.rotate_jog(1)
        if self.CONTROL_TOGGLE == self.CRANE_CONTROL:
            self.crane_inst.rotate_jog(-1)


    def zoom_in(self):
        self.gimbal_inst.zoom_in_small()


    def zoom_out(self):
        self.gimbal_inst.zoom_out_small()

    def save_state_to_file(self):
        data = {}
        current_pos ={}
        data['RoboCam'] = []
        current_pos['Position'] = []
        current_pos['Position'].append(self.controller.position_data())
        
        data['RoboCam'].append(current_pos)
        sp_data = {}
        sp_data['SavePoints'] = []
        sp_data['SavePoints'].append(self.save_position_1.get_waypoint_data())
        sp_data['SavePoints'].append(self.save_position_2.get_waypoint_data())
        sp_data['SavePoints'].append(self.save_position_3.get_waypoint_data())
        sp_data['SavePoints'].append(self.save_position_4.get_waypoint_data())
        
        data['RoboCam'].append(sp_data)

        with open('RoboCam_state.json', 'w') as outfile:
            json.dump(data, outfile)

    def load_state_from_file(self):
        with open('RoboCam_state.json') as json_file:
            data = json.load(json_file)
            state = data['RoboCam']
            print(state)
            savepoints = state[1]['SavePoints']
            print(savepoints)
            for sp in range(len(savepoints)):
                print(sp)
                print (savepoints[sp])
                if (sp==1):
                    self.save_position_1 = waypoint(savepoints[sp]['id'],location(savepoints[sp]['x'],savepoints[sp]['y'],savepoints[sp]['z']), location(savepoints[sp]['a'], savepoints[sp]['b'], 0))
                if (sp==2):
                    self.save_position_2 = waypoint(savepoints[sp]['id'],location(savepoints[sp]['x'],savepoints[sp]['y'],savepoints[sp]['z']), location(savepoints[sp]['a'], savepoints[sp]['b'], 0))
                if (sp==3):
                    self.save_position_3 = waypoint(savepoints[sp]['id'],location(savepoints[sp]['x'],savepoints[sp]['y'],savepoints[sp]['z']), location(savepoints[sp]['a'], savepoints[sp]['b'], 0))
                if (sp==4):
                    self.save_position_4 = waypoint(savepoints[sp]['id'],location(savepoints[sp]['x'],savepoints[sp]['y'],savepoints[sp]['z']), location(savepoints[sp]['a'], savepoints[sp]['b'], 0))
            self.sp1_pos_text['text'] = "Y/LB : {}".format(self.save_position_1.location_str())
            self.sp2_pos_text['text'] = "B/RB : {}".format(self.save_position_2.location_str())
            self.sp3_pos_text['text'] = "X/L1 : {}".format(self.save_position_3.location_str())
            self.sp4_pos_text['text'] = "A/R1 : {}".format(self.save_position_4.location_str())
            current_position = state[0]['Position'][0]
            print (current_position)
            #self.controller.set_position(current_position['wx'],current_position['wy'],current_position['wz'],current_position['wa'],current_position['wb'])
        #once we've loaded state we can start saving it again
        self.first_move=True
    

    def quit(self):
        self.joy.stop()
        self.info_update.stop()
        self.controller.stop()
        self.master.destroy()
        self.tracker.stop_tracking()
        sys.exit(0)

class editWaypointPopup(object):
    def __init__(self,master, waypointvalue):

        top=self.top=Toplevel(master)
               
        self.l=Label(top,text="Edit Waypoint")
        self.l.pack()
        x = StringVar(root, value=waypointvalue.xpos)
        y = StringVar(root, value=waypointvalue.ypos)
        z = StringVar(root, value=waypointvalue.zpos)
        a = StringVar(root, value=waypointvalue.apos)
        b = StringVar(root, value=waypointvalue.bpos)
        dwell = StringVar(root, value=waypointvalue.dwell_time)
        self.x=Entry(top,textvariable = x)
        self.x.pack()
        self.y=Entry(top,textvariable = y)
        self.y.pack()
        self.z=Entry(top,textvariable = z)
        self.z.pack()
        self.a=Entry(top,textvariable = a)
        self.a.pack()
        self.b=Entry(top,textvariable = b)
        self.b.pack()
        self.dwell=Entry(top,textvariable = dwell)
        self.dwell.pack()
        
        self.okbutton=Button(top,text='Ok',command=self.cleanup)
        self.okbutton.pack()
    def cleanup(self):
        editedWaypoint = waypoint(location(self.x.get(), self.y.get(),self.z.get()), location(self.a.get(), self.b.get(), 0))
        editedWaypoint.set_dwell_time(self.dwell.get())
        self.value=editedWaypoint
        self.top.destroy()

if __name__ == "__main__":
    #main()
    root = tk.Tk()
    #root.withdraw()
    #root.geometry("800x400")
    #app = RobotCamera(master=root)
    app = RobotCamera(root)
    app.mainloop()
    sys.exit(0)
