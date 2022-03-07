
import os
import sys
from flask import Flask, render_template, request, g,send_from_directory
import socket
import select
import json


HOST = '192.168.86.37' 
SOCKET_LIST = []
RECV_BUFFER = 4096 
PORT = 9009


app = Flask(__name__)


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.route("/")
def index():
    
    print("homepage")
    status=send_camera_request(json.dumps({"request":"status"}))
    savepoints= send_camera_request(json.dumps({"request":"savepoints"}))
    toggle_state = send_camera_request(json.dumps({"request":"toggles"}))

    print(toggle_state)
    if toggle_state["move_mode"] == 1:
        move_state="checked"
    else:
        move_state=""
    if toggle_state["tracking_mode"] == True:
        tracking_state="checked"
    else:
        tracking_state=""
    values = send_camera_request(json.dumps({"request":"values"}))
    waypoints = json.loads(send_camera_request(json.dumps({"request":"waypoints"})))
    limits = send_camera_request(json.dumps({"request":"limits"}))
    
    return render_template('index.html', 
                        status_text=status,
                        savepoints=savepoints,
                        move_toggle=move_state, 
                        tracking_toggle=tracking_state, 
                        feed_rate=values['feed_rate'],
                        feed_rate_values=values['feed_rate_values'],
                        move_time=values['move_time'],
                        move_time_values=values['move_time_values'],
                        tracking_mode=values["tracking_mode"],
                        tracking_modes=values["tracking_modes"],
                        dwell_time=10,
                        dwell_time_values=[10,20,30,60],
                        waypoints = waypoints,
                        limits=limits)

@app.route("/refresh/<id>" , methods = ['POST'])
def refresh_info(id):
    response=send_camera_request(json.dumps({"request":id}))
    return response

@app.route("/tracker_glyph")
def tracker_glyph():
    values = send_camera_request(json.dumps({"request":"values"}))
    return render_template('aruco_tracker.html',tracking_mode=values["tracking_mode"], aruco_glyph="")

@app.route("/save_savepoint" , methods = ['POST'])
def save_waypoint():
    data = request.get_json()
    savepoint_id = data['savepoint_id']
    response = send_camera_request(json.dumps({"update":"storepoint","savepoint_id":savepoint_id}))
    return response

@app.route("/add_waypoint" , methods = ['POST'])
def add_waypoint():
    data = request.get_json()
    dwell_time = data['dwell_time']
    response = send_camera_request(json.dumps({"add":"waypoint","dwell-time":dwell_time}))
    return response

@app.route("/timelapse_start" , methods = ['POST'])
def timelapse_start():
    data = request.get_json()
    tl_duration = data['duration']
    tl_stepinterval = data['step-interval']
    response = send_camera_request(json.dumps({"action":"timelapse","duration":tl_duration,"step-interval":tl_stepinterval}))
    return response


@app.route("/move_to_savepoint" , methods = ['POST'])
def moveto_waypoint():
    data = request.get_json()
    savepoint_id = data['savepoint_id']
    response = send_camera_request(json.dumps({"action":"movepoint","savepoint_id":savepoint_id}))
    return response


@app.route("/toggle/<id>" , methods = ['POST'])
def toggle_flip(id):
    data = request.get_json()
    
    response = send_camera_request(json.dumps({"toggle":id}))
    return response 

@app.route("/update/<id>" , methods = ['POST'])
def dropdown_select(id):
    data = request.get_json()
    value = data[id]
    print("toggle {} {}".format(id,value))
    response = send_camera_request(json.dumps({"update":id, id: value }))
    return response 

def send_camera_request(request_message):
   
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
     
    # connect to remote host
    try :
        s.connect((HOST, PORT))
    except :
        print ('Unable to connect')
        return ""
     
    print ('Connected to roboCamera server.')
    socket_list = [s]
        
    # Get the list sockets which are readable
    ready_to_read,ready_to_write,in_error = select.select(socket_list , socket_list, [])
    print ("sockets ready for communication")    
    for sock in ready_to_write:
        print("sending request {}".format(request_message))
        s.send(request_message.encode("utf-8"))
    ready_to_read,ready_to_write,in_error = select.select(socket_list,[], [])
    for sock in ready_to_read:             
        if sock == s:
            print("reading data from socket")
            # incoming message from remote server, s

            data = sock.recv(4096)
            if not data :
                print('\nDisconnected from chat server')
                return ""
            else :
                print (data)
                return json.loads(data)
    print("returning")
    return "no data"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

HOST=get_ip()
app.run(host=HOST, port=8080, debug=True)



