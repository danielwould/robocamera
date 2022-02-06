
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
import socket
import select
HOST = '' 
SOCKET_LIST = []
RECV_BUFFER = 4096 
PORT = 9009

PRGPATH=os.path.abspath(os.path.dirname(__file__))
sys.path.append(PRGPATH)
sys.path.append(os.path.join(PRGPATH, 'helpers'))
sys.path.append(os.path.join(PRGPATH, 'data'))
sys.path.append(os.path.join(PRGPATH, 'helpers/controllers'))


VALID_CHARS = "`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./"
SHIFT_CHARS = '~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'


class RobotCamera():

    def __init__(self):
        #super().__init__(master)
        #self.master = master
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
        self.savepoints = []
        self.savepoints.append(self.save_position_1)
        self.savepoints.append(self.save_position_2)
        self.savepoints.append(self.save_position_3)
        self.savepoints.append(self.save_position_4)
        
        self.first_move=False
        
        
        self.sequence_steps = sequence()
        
        self.init_controllers()
        self.init_joysticks()
        #self.init_info_updater()
        #self.pack()
        #self.create_widgets()

    def init_controllers(self):
        
        self.controller=grbl_controller(0,"RoboCamera")
        
        if sys.platform == "win32":
            print("connecting to windows com device")
            self.controller.set_device("COM1", 115200,"RoboCamera")
        else:
            print("connecting to linux tty device")
            self.controller.set_device("/dev/ttyACM0", 115200,"RoboCamera")


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
        #TODO re-enable
        #self.tracker = aruco_tracker(self.controller,self)
        #self.tracker.initialise_video()


    def init_joysticks(self):
        self.joy = Joystick(self, self.gimbal_inst, self.crane_inst)

    def init_info_updater(self):
        self.info_update = info(self)


    
        
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

    def toggle_move_mode(self):
        if self.MOVE_TOGGLE==self.MOVE_TIME:
            self.MOVE_TOGGLE = self.FEED_RATE
        else:
            self.MOVE_TOGGLE = self.MOVE_TIME

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


    def set_feed_rate(self, value):
        print("updating feeddefault from {} to {}".format(self.controller.get_feed_speed(),value))
        self.controller.set_feed_speed(value)
        

    def set_move_time(self, value):
        self.controller.set_move_duration(value)

    def set_timelapse_time(self, value):
        self.timelapse_time = value
        
    def set_timelapse_steps(self, value):
        self.timelapse_steps = value

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


    def save_point_move(self,savepoint_id):
        if savepoint_id == 1:
            savepoint=self.save_position_1
        if savepoint_id == 2:
            savepoint=self.save_position_2
        if savepoint_id == 3:
            savepoint=self.save_position_3
        if savepoint_id == 4:
            savepoint=self.save_position_4
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

    
    def crane_tilt_up(self):
        self.crane_inst.tilt_jog(1)


    def crane_tilt_down(self):
        self.crane_inst.tilt_jog(-1)


    def crane_rotate_left(self):
        self.crane_inst.rotate_jog(-1)


    def crane_rotate_right(self):
        self.crane_inst.rotate_jog(-1)

    def gimbal_tilt_up(self):
        self.gimbal_inst.tilt_jog(1)

    def gimbal_tilt_down(self):
        self.gimbal_inst.tilt_jog(-1)
        
    def gimbal_rotate_left(self):
        self.gimbal_inst.rotate_jog(1)
        
    def gimbal_rotate_right(self):
        self.gimbal_inst.rotate_jog(1)
        
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
        #self.info_update.stop()
        self.controller.stop()
        #self.master.destroy()
        self.tracker.stop_tracking()
        sys.exit(0)

def camera_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    rc = RobotCamera()
 
    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
 
    print ("RoboCamera server started on port {}".format(str(PORT)))
 
    while 1:

        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 0 : poll and never block
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
      
        for sock in ready_to_read:
            # a new connection request recieved
            if sock == server_socket: 
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                print ("Client (%s, %s) connected" % addr)
                
                #response(sockfd,"Welcome to robocamera")             
            # a message from a client, not a new connection
            else:
                # process data recieved from client, 
                try:
                    # receiving data from the socket.
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        # there is something in the socket
                        print("Received request {}".format(data)  )
                        #handle command
                        request = json.loads(data)
                        resp_message = handle_request(request, rc)
                        #send response
                        
                        response(sock,json.dumps(resp_message))
                    else:
                        # remove the socket that's broken    
                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)

                except Exception as e:
                    if False:
                        print("do nothing")

    server_socket.close()
    
def response(socket,message):
    socket.send(message.encode("utf-8"))
    print("sent response {}".format(message))

def handle_request(request, rc):
    print ("request is for {}".format(request["request"]))
    response={"response":"pong"}
    if request["request"] == "status":
        response = {"status":rc.controller.get_grbl_status(), "last_update":rc.controller.get_lastUpdateTime(),"position":rc.controller.position_str()}
    elif request["request"] == "savepoints":
        response = {"savepoint_1": rc.save_position_1.location_str(),"savepoint_2": rc.save_position_2.location_str(),"savepoint_3": rc.save_position_3.location_str(),"savepoint_4": rc.save_position_4.location_str()}
    elif request["request"] == "toggles":
        response = {"move_mode":rc.MOVE_TOGGLE,"tracking_mode": rc.TRACKING}
    elif request["request"] == "values":
        response = {"feed_rate":rc.controller.get_feed_speed(),"move_time": rc.controller.get_move_duration(),"timelapse_time":rc.timelapse_time,"timelapse_steps":rc.timelapse_steps}

    elif request["update"] == "storepoint":
        #save current location as savepoint
        rc.save_position(request["savepoint_id"])
        response = {"result":"savepoint_stored"}
    elif request["action"] == "movepoint":
        #save current location as savepoint
        rc.save_point_move(request["savepoint_id"])
        response = {"result":"moved_to_savepoint"}
    elif request["action"] == "zoom_in":
        rc.zoom_in()
        response = {"result":"zoomed_in"}
    elif request["action"] == "zoom_out":
        rc.zoom_out()
        response = {"result":"zoomed_out"}
    elif request["action"] == "gimbal_rotate_left":
        rc.gimbal_rotate_left()
        response = {"result":"gimbal_rotate_left"}
    elif request["action"] == "gimbal_rotate_right":
        rc.gimbal_rotate_right()
        response = {"result":"gimbal_rotate_right"}
    elif request["action"] == "gimbal_tilt_up":
        rc.gimbal_tilt_up()
        response = {"result":"gimbal_tilt_up"}
    elif request["action"] == "gimbal_tilt_down":
        rc.gimbal_tilt_down()
        response = {"result":"gimbal_tilt_down"}
    elif request["action"] == "gimbal_rotate_left":
        rc.gimbal_rotate_left()
        response = {"result":"crane_rotate_left"}
    elif request["action"] == "crane_rotate_right":
        rc.crane_rotate_right()
        response = {"result":"crane_rotate_right"}
    elif request["action"] == "crane_tilt_up":
        rc.crane_tilt_up()
        response = {"result":"crane_tilt_up"}
    elif request["action"] == "crane_tilt_down":
        rc.crane_tilt_down()
        response = {"result":"crane_tilt_down"}
    elif request["toggle"]=="move_mode":
        rc.toggle_move_mode()
        response = {"result": rc.MOVE_TOGGLE}
    elif request["toggle"]=="tracking_mode":
        rc.toggle_tracking_mode()
        response = {"result": rc.TRACKING}
    elif request["update"]=="feed_rate":
        rc.set_feed_rate(request["feed_rate"])
        response = {"result": "OK"}
    elif request["update"]=="move_time":
        rc.set_move_time(request["move_time"])
        response = {"result": "OK"}
    elif request["update"]=="time_lapse_time":    
        rc.set_timelapse_time(request["timelapse_time"])
        response = {"result": "OK"}
    elif request["update"]=="time_lapse_steps":    
        rc.set_timelapse_steps(request["timelapse_steps"])
        response = {"result": "OK"}

    return response

if __name__ == "__main__":

    sys.exit(camera_server())