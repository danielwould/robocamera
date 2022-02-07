

from importlib.resources import read_text
import os
import sys
from flask import Flask, render_template, request, g
import socket
import select
import json

HOST = '192.168.86.37' 
SOCKET_LIST = []
RECV_BUFFER = 4096 
PORT = 9009


app = Flask(__name__)


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
    return render_template('index.html', status_text=status, savepoints=savepoints, move_toggle=move_state, tracking_toggle=tracking_state, feed_rate=values['feed_rate'])


@app.route("/save_savepoint" , methods = ['POST'])
def save_waypoint():
    data = request.get_json()
    savepoint_id = data['savepoint_id']
    response = send_camera_request(json.dumps({"update":"storepoint","savepoint_id":savepoint_id}))
    return response

@app.route("/move_to_savepoint" , methods = ['POST'])
def moveto_waypoint():
    data = request.get_json()
    savepoint_id = data['savepoint_id']
    response = send_camera_request(json.dumps({"action":"movepoint","savepoint_id":savepoint_id}))
    return response

@app.route("/toggle_moveby" , methods = ['POST'])
def toggle_move_mode():
    data = request.get_json()
    state = data['state']
    print("toggle state {}".format(state))
    response = send_camera_request(json.dumps({"toggle":"move_mode"}))
    return response

@app.route("/toggle_tracking" , methods = ['POST'])
def toggle_tracking():
    data = request.get_json()
    state = data['state']
    print("toggle state {}".format(state))
    response = send_camera_request(json.dumps({"toggle":"tracking_mode"}))
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

app.run(host="127.0.0.1", port=8080, debug=True)




