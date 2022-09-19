
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
from helpers.extra_controls import extra_controller
import os
import sys
import json
import socket
import select
import random
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
        self.extra_controls = extra_controller("ExtraControls")
        if sys.platform == "win32":
            print("connecting to windows com device")
            #self.controller.set_device("COM3", 115200,"RoboCamera")
            self.extra_controls.set_device("COM3",115200,"ExtraControls")
        else:
            print("connecting to linux tty device")
            self.extra_controls.set_device("/dev/ttyACM1",115200,"ExtraControls")
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
        self.extra_controls.set_controller(self.controller)
        self.tracker = aruco_tracker(self.controller,self)
        self.tracker.initialise_video()
        time.sleep(1)
        self.controller.auto_level_gimbal()



    def init_joysticks(self):
        self.joy = Joystick(self, self.gimbal_inst, self.crane_inst)

    def init_info_updater(self):
        self.info_update = info(self)


    
        
    def timelapse(self, duration, step_interval):
        #trigger a timelapse from current position to Save position 2
        savepoint = self.save_position_2
        self.controller.absolute_move_timelapse(savepoint.xpos,savepoint.ypos,savepoint.zpos, savepoint.apos,savepoint.bpos, duration,  step_interval)

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

    def toggle_video(self):
        self.extra_controls.toggle_video()
        
    def add_waypoint(self,dwell_time):
        print("add waypoint")  # (x, y, z,focus, feed), dwell time
        crane_position = self.crane_inst.get_current_location()
        gimbal_position = self.gimbal_inst.get_current_location()
        wp = waypoint(len(self.sequence_steps.waypoints),
            location(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()),
            location(crane_position.get_rotation_pos(), crane_position.get_tilt_pos(),crane_position.get_zoom_pos())
            )
        wp.set_dwell_time(dwell_time)
        wp.set_feed_rate(self.controller.get_feed_speed())
        wp.set_travel_duration(self.controller.get_move_duration())
               
        self.sequence_steps.add_waypoint(wp)

    def edit_waypoint(self,id,feed_rate,move_time,dwell_time):
        print("edit waypoint")  # (x, y, z,focus, feed), dwell time
        wp = self.sequence_steps.waypoints[id]
        wp.set_feed_rate(feed_rate)
        wp.set_travel_duration(move_time)
        wp.set_dwell_time(dwell_time)
        self.sequence_steps.update_waypoint(id,wp)

    def alter_waypoint_sequence(self,id,direction):
        print("change waypoint order")  # (x, y, z,focus, feed), dwell time
        if (direction == "up"):
            self.sequence_steps.move_waypoint_up(id)
        else:
            self.sequence_steps.move_waypoint_down(id)
        

    def remove_waypoint(self, id):
        # todo allow for deleting specific waypoint item
        self.sequence_steps.delete_waypoint(index=id)
            

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
        if savepoint_id == 0:
            savepoint=self.save_position_1
        if savepoint_id == 1:
            savepoint=self.save_position_2
        if savepoint_id == 2:
            savepoint=self.save_position_3
        if savepoint_id == 3:
            savepoint=self.save_position_4
        self.move_to_location(savepoint)

    def way_point_move(self,waypoint_id):
        print("moving to waypoint")
        waypoint = self.sequence_steps.waypoints[waypoint_id]
        self.move_to_location(waypoint)
    
    def random_way_point_move(self):
        print("moving to random waypoint")
        crane_position = self.crane_inst.get_current_location()
        gimbal_position = self.gimbal_inst.get_current_location()
        waypoint = random.choice(self.sequence_steps.waypoints)
        random_guesses=0
        #don't just pick the current location but set a max for testing with no new positions
        while (waypoint.xpos == gimbal_position.get_rotation_pos() 
           and waypoint.ypos == gimbal_position.get_tilt_pos()
           and waypoint.zpos == gimbal_position.get_zoom_pos()
           and waypoint.apos == crane_position.get_rotation_pos()
           and waypoint.bpos == crane_position.get_tilt_pos() 
           and random_guesses <10):
            random_guesses=random_guesses+1
            waypoint = random.choice(self.sequence_steps.waypoints)

        self.move_to_location(waypoint)

    def move_to_location(self,location):
        if self.MOVE_TOGGLE == self.FEED_RATE:
            self.controller.absolute_move(location.xpos,location.ypos,location.zpos, location.apos,location.bpos,self.controller.get_feed_speed(),location.get_dwell_time())
        if self.MOVE_TOGGLE == self.MOVE_TIME:
            self.controller.absolute_move_by_time(location.xpos,location.ypos,location.zpos, location.apos,location.bpos,self.controller.get_move_duration(),location.get_dwell_time())



    def save_position(self,savepoint):
        
        crane_position = self.crane_inst.get_current_location()
        gimbal_position = self.gimbal_inst.get_current_location()
        new_waypoint = waypoint(savepoint,
            location(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()),
            location(crane_position.get_rotation_pos(), crane_position.get_tilt_pos(),0)
            )
        #new_waitpoint.set_feed_rate(self.controller.get_feed_speed())
        if savepoint == 0:
            self.save_position_1 = new_waypoint
            
        if savepoint == 1:
            self.save_position_2 = new_waypoint
            
        if savepoint == 2:
            self.save_position_3 = new_waypoint
            
        if savepoint == 3:
            self.save_position_4 = new_waypoint
            

    
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
        isHtml = False
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
                        if (data.decode("utf8").startswith("GET")):
                            isHtml=True
                            data=b'{"request":"status"}'
                        #handle command
                        request = json.loads(data)
                        resp_message = handle_request(request, rc)
                        #send response
                        if isHtml:
                            httpresp="HTTP/1.0 200 OK\n\n"+json.dumps(resp_message)
                            response(sock,httpresp)
                        else:
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
    print ("request is for {}".format(request))
    response={"response":"pong"}
    if ("request" in request):
        if request["request"] == "status":
            response = {"status":rc.controller.get_grbl_status(), "last_update":rc.controller.get_lastUpdateTime(),"work_pos":rc.controller.work_position_str(),"machine_pos":rc.controller.machine_position_str(),"gimbal_tilt_reading":rc.extra_controls.x_angle }
        elif request["request"] == "controls":
            response = {"toggles":{"recording":"/toggle/record_switch","tracking":"/toggle/tracking_switch"}, "controls":{"move_random","/move_to_random_waypoint"}}
        elif request["request"] == "savepoints":
            response = {"savepoint_1": rc.save_position_1.location_str(),"savepoint_2": rc.save_position_2.location_str(),"savepoint_3": rc.save_position_3.location_str(),"savepoint_4": rc.save_position_4.location_str()}
        elif request["request"] == "toggles":
            response = {"move_mode":rc.MOVE_TOGGLE,"tracking_mode": rc.TRACKING, "recording":rc.extra_controls.recording}
        elif request["request"] == "values":
            response = {"feed_rate":rc.controller.get_feed_speed(),"feed_rate_values":[100,200,500,1000,1500,2000],"move_time": rc.controller.get_move_duration(),"move_time_values":[1,2,5,10,15,30,60,120,300],"timelapse_time":rc.timelapse_time,"timelapse_steps":rc.timelapse_steps,"tracking_mode":rc.tracker.get_tracking_mode(),"tracking_modes": rc.tracker.get_tracking_modes()}
        elif request["request"] == "waypoints":
            waypoint_payload =[]
            index=0
            for wp in rc.sequence_steps.waypoints:
                waypoint_payload.append(wp.get_waypoint_data(index))
                index=index+1
            response = json.dumps(waypoint_payload)
        elif request["request"] == "limits":
            response = {"Gimbal":{
            "pan_min":{"label":"Pan min","state":rc.controller.gimbal_pan_min_locked,
            "value":rc.controller.gimbal_pan_min},
            "pan_max":{"label":"Pan max","state": rc.controller.gimbal_pan_max_locked,
            "value":rc.controller.gimbal_pan_max},
            "tilt_min":{"label":"Tilt min","state":rc.controller.gimbal_tilt_min_locked,
            "value":rc.controller.gimbal_tilt_min},
            "tilt_max":{"label":"Tilt max","state":rc.controller.gimbal_tilt_max_locked,
            "value":rc.controller.gimbal_tilt_max},
            "z_min":{"label":"Zoom min","state":rc.controller.z_min_locked,
            "value":rc.controller.z_min},
            "z_max":{"label":"Zoom max","state":rc.controller.z_max_locked,
            "value":rc.controller.z_max},
            },
            "Crane":{"pan_min":{"label":"Pan min","state":rc.controller.crane_pan_min_locked,
            "value":rc.controller.crane_pan_min},
            "pan_max":{"label":"Pan max","state": rc.controller.crane_pan_max_locked,
            "value":rc.controller.crane_pan_max},
            "tilt_min":{"label":"Tilt min","state":rc.controller.crane_tilt_min_locked,
            "value":rc.controller.crane_tilt_min},
            "tilt_max":{"label":"Tilt max","state":rc.controller.crane_tilt_max_locked,
            "value":rc.controller.crane_tilt_max},
            }}
        
    elif("update" in request):
        if request["update"] == "storepoint":
            #save current location as savepoint
            rc.save_position(request["savepoint_id"])
            response = {"result":"savepoint_stored"}
        elif request["update"] == "waypoint":
            #save current location as savepoint
            print ("edit waypoint")
            rc.edit_waypoint(request["id"], request["feed_rate"],request["move_time"],request["dwell_time"])
            waypoint_payload =[]
            index=0
            for wp in rc.sequence_steps.waypoints:
                waypoint_payload.append(wp.get_waypoint_data(index))
                index=index+1
            print("return updated waypoints")
            response = json.dumps(waypoint_payload)
        elif request["update"] == "waypoint_sequence":
            print ("update waypoint sequence")
            rc.alter_waypoint_sequence(request["id"],request["direction"])
            waypoint_payload =[]
            index=0
            for wp in rc.sequence_steps.waypoints:
                waypoint_payload.append(wp.get_waypoint_data(index))
                index=index+1
            print("return updated waypoints")
            response = json.dumps(waypoint_payload)
        elif request["update"]=="feed-select":
            rc.set_feed_rate(request["feed-select"])
            response = {"result": "OK"}
        elif request["update"]=="time-select":
            rc.set_move_time(request["time-select"])
            response = {"result": "OK"}
        elif request["update"]=="time_lapse_time":    
            rc.set_timelapse_time(request["timelapse_time"])
            response = {"result": "OK"}
        elif request["update"]=="time_lapse_steps":    
            rc.set_timelapse_steps(request["timelapse_steps"])
            response = {"result": "OK"}
        elif request["update"]=="tracking-select":    
            rc.tracker.set_tracking_mode(request["tracking-select"])
            response = {"result": "OK"}
    elif("reset" in request):
        if request["reset"] == "limits":
            rc.controller.reset_limits()
    elif("add" in request):
        if request["add"] == "waypoint":
            rc.add_waypoint(request["dwell-time"])
            waypoint_payload =[]
            index=0
            for wp in rc.sequence_steps.waypoints:
                waypoint_payload.append(wp.get_waypoint_data(index))
                index=index+1
            response = json.dumps(waypoint_payload)
    elif("remove" in request):
        if request["remove"] == "waypoint":
            rc.remove_waypoint(request["id"])
            waypoint_payload =[]
            index=0
            for wp in rc.sequence_steps.waypoints:
                waypoint_payload.append(wp.get_waypoint_data(index))
                index=index+1
            response = json.dumps(waypoint_payload)
    elif("action" in request):
        if request["action"] == "movepoint":
            #save current location as savepoint
            if "savepoint_id" in request:
                rc.save_point_move(request["savepoint_id"])
                response = {"result":"moved_to_savepoint"}
            if "waypoint_id" in request:
                rc.way_point_move(request["waypoint_id"])
                response = {"result":"moved_to_waypoint"}
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
        elif request["action"] == "timelapse":
            rc.timelapse(request["duration"],request["step-interval"])
            response = {"result":"crane_tilt_down"}
        elif request["action"]=="waypoint_sequence":
            rc.trigger_whole_sequence()
            response = {"result":"sequence_running"}
        elif request["action"]=="waypoint_random":
            rc.random_way_point_move()
            response = {"result":"random_move","move_mode":rc.MOVE_TOGGLE,"tracking_mode": rc.TRACKING, "recording":rc.extra_controls.recording}
    elif "toggle" in request:
        if request["toggle"]=="moveby_switch":
            rc.toggle_move_mode()
            response = {"result": rc.MOVE_TOGGLE}
        elif request["toggle"]=="tracking_switch":
            rc.toggle_tracking_mode()
            response = {"result": rc.TRACKING,"move_mode":rc.MOVE_TOGGLE,"tracking_mode": rc.TRACKING, "recording":rc.extra_controls.recording}
        elif request["toggle"]=="record_switch":
            rc.toggle_video()
            response = {"result": "success","move_mode":rc.MOVE_TOGGLE,"tracking_mode": rc.TRACKING, "recording":rc.extra_controls.recording}
        elif request["toggle"]=="Gimbal_pan_min":
            rc.controller.toggle_gimbal_pan_min_locked()
            response = {"result": rc.controller.gimbal_pan_min_locked}
        elif request["toggle"]=="Gimbal_pan_max":
            rc.controller.toggle_gimbal_pan_max_locked()
            response = {"result": rc.controller.gimbal_pan_max_locked}
        elif request["toggle"]=="Gimbal_tilt_min":
            rc.controller.toggle_gimbal_tilt_min_locked()
            response = {"result": rc.controller.gimbal_tilt_min_locked}
        elif request["toggle"]=="Gimbal_tilt_max":
            rc.controller.toggle_gimbal_tilt_max_locked()
            response = {"result": rc.controller.gimbal_tilt_max_locked}
        elif request["toggle"]=="Gimbal_z_min":
            rc.controller.toggle_zoom_min_locked()
            response = {"result": rc.controller.z_min_locked}
        elif request["toggle"]=="Gimbal_z_max":
            rc.controller.toggle_zoom_max_locked()
            response = {"result": rc.controller.z_max_locked}
        elif request["toggle"]=="Crane_pan_min":
            rc.controller.toggle_crane_pan_min_locked()
            response = {"result": rc.controller.crane_pan_min_locked}
        elif request["toggle"]=="Crane_pan_max":
            rc.controller.toggle_crane_pan_max_locked()
            response = {"result": rc.controller.crane_pan_max_locked}
        elif request["toggle"]=="Crane_tilt_min":
            rc.controller.toggle_crane_tilt_min_locked()
            response = {"result": rc.controller.crane_tilt_min_locked}
        elif request["toggle"]=="Crane_tilt_max":
            rc.controller.toggle_crane_tilt_max_locked()
            response = {"result": rc.controller.crane_tilt_max_locked}
    return response

if __name__ == "__main__":

    sys.exit(camera_server())
