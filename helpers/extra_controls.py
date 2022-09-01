import serial
import time
import logging
import threading
import json
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
        #self.serial = serial.Serial(
        self.serial = serial.serial_for_url(
						device.replace('\\', '\\\\'), #Escape for windows
						baudrate,
						bytesize=serial.EIGHTBITS,
						parity=serial.PARITY_NONE,
						stopbits=serial.STOPBITS_ONE,
						timeout=SERIAL_TIMEOUT,
						xonxoff=False,
						rtscts=False)
		# Toggle DTR to reset Arduino
        #try:
        #    self.serial.setDTR(0)
        #except IOError:
        #    pass
        time.sleep(1)
        self.serial.flushInput()
        #try:
        #    self.serial.setDTR(1)
        #except IOError:
        #    pass
        #time.sleep(1)
        self.serial_write("\n\n")
        
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
        self.queue.put("ToggleVideo")

    def serial_write(self, data):
        if data == b"?":
            self.logger.debug("W "+str(type(data))+" : "+str(data))
        else:
            self.logger.info("W "+str(type(data))+" : "+str(data))

        # if sys.version_info[0] == 2:
        #	ret = self.serial.write(str(data))
        if isinstance(data, bytes):
            ret = self.serial.write(data)
        else:
            ret = self.serial.write(data.encode())
        return ret

    def control_thread(self, name):
        self.logger.info("########################################")
        self.logger.info("Thread start for extras control :{}".format(name))
        self.logger.info("########################################")
        # wait for commands to complete (status change to Idle)
        #self.sleep_event    = threading.Event()
        
        commandToSend = None			# next string to send
        lastWriteAt = tg = time.time()
        while self.app_running:
            t = time.time()
            if commandToSend is None:
                try:
                    self.logger.debug("Command queue length {}".format(self.queue.qsize()))
                    commandToSend = self.queue.get_nowait()
                    self.logger.debug("pulled new gcode line to send: {}".format(commandToSend))
                except Empty:
                    #nothing to send
                    commandToSend = None
            if t-lastWriteAt > SERIAL_POLL:
                try:
                    self.serial_write(b"?")
                except Exception as e:
                    self.logger.error("Error writing value to controller")
                    self.logger.error(e)
            try:     
                line = str(self.serial.readline().decode()).strip()
                self.logger.info("Read value: {}".format(line))
                if (line != ''):
                    data = json.loads(line)
                    if ("angleX" in data):
                        self.logger.info("X angle = {}".format(data["angleX"]))
                        self.x_angle=data["angleX"]
                    if ("ToggleVideo" in data):
                        self.logger.info("Toggle Video Confirmed")
                        
            except Exception as e:
                self.logger.error("Error reading value from controller")
                self.logger.error(e)
                    

            if commandToSend != None:
                self.serial_write("{}".format(commandToSend))
                lastWriteAt = t