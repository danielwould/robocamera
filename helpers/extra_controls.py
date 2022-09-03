import serial
import time
import logging
import threading
import json
import sys
try:
    from Queue import *
except ImportError:
    from queue import *
SERIAL_POLL = 1
SERIAL_TIMEOUT = 0.10  # 

#This class connects to an arduino and supports reading values from it and sending commands
#initial usecase - read a potentiometer value that represents the gimbal tilt
# write requests to start/stop video recording by actuating a servo
class extra_controller:
    serial_device = None
    app_running = False
    x_angle=None
    recording=False
    def __init__(self,name):
        
        self.name="init"
        
        self.logger = logging.getLogger(name)
        hdlr = logging.FileHandler('./{}.log'.format(name))
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr) 
        self.logger.setLevel(logging.INFO)
        self.queue = Queue()
        

    def set_device(self, device, baudrate, name):
        self.serial_device = device
        self.serial = serial.Serial(device,baudrate,timeout=1)
        
        time.sleep(1)
        self.serial.flushInput()
        self.serial.flushOutput()
        self.app_running = True
        self.thread = threading.Thread(
            target=self.control_thread, args=(name,))
        #self.thread.daemon = True
        self.thread.start()

    def toggle_video(self):
        if self.recording==False:
            self.recording=True
        else:
            self.recording=False
        self.logger.info("requesting video record toggle")
        self.queue.put("r")

    def serial_write(self, data):
        ret = self.serial.write(data.encode())
        time.sleep(0.5)
        #self.logger.info("serial return code {}".format(ret))
        return ret

    def control_thread(self, name):
        self.logger.info("########################################")
        self.logger.info("Thread start for extras control :{}".format(name))
        self.logger.info("########################################")
        # wait for commands to complete (status change to Idle)
        self.sleep_event    = threading.Event()
        
        commandToSend = None			# next string to send
        lastWriteAt = tg = time.time()
        while self.app_running:
            t = time.time()
            time.sleep(0.1)
            if commandToSend is None:
                try:
                    #self.logger.debug("Command queue length {}".format(self.queue.qsize()))
                    commandToSend = self.queue.get_nowait()
                    #self.logger.debug("pulled new gcode line to send: {}".format(commandToSend))
                except Empty:
                    #nothing to send
                    commandToSend = None
            if t-lastWriteAt > SERIAL_POLL:
                try:
                    #self.logger.info("requesting status")
                    self.serial_write("?\n")
                    #self.logger.info("? sent")

                except Exception as e:
                    self.logger.error("Error writing value to controller")
                    self.logger.error(e)
            try:     
                line = str(self.serial.readline().decode()).strip()
                #self.logger.info("Read value: {}".format(line))
                if (line != ''):
                    data = json.loads(line)
                    if ("angleX" in data):
                        #self.logger.info("X angle = {}".format(data["angleX"]))
                        self.x_angle=data["angleX"]
                    if ("ToggleVideo" in data):
                        self.logger.info("Toggle Video Confirmed")
                        
            except Exception as e:
                #self.logger.error("Error reading value from controller")
                self.logger.debug(e)
                    

            if commandToSend != None:
                self.logger.info("sending command {}".format(commandToSend))
                self.serial_write("{}\n".format(commandToSend))
                commandToSend=None
                lastWriteAt = t
