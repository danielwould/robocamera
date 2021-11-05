# -*- coding: utf-8 -*-
from __future__ import absolute_import
import serial
import time
import threading
import sys
import re
import os
import glob
try:
    from Queue import *
except ImportError:
    from queue import *

from helpers.controllers._GenericGRBL import ERROR_CODES
from data.location import location
import logging


SERIAL_POLL = 1
SERIAL_TIMEOUT = 0.10  # s
G_POLL = 20  # s
RX_BUFFER_SIZE = 128

GPAT = re.compile(r"[A-Za-z]\s*[-+]?\d+.*")
FEEDPAT = re.compile(r"^(.*)[fF](\d+\.?\d+)(.*)$")

CONNECTED = "Connected"
NOT_CONNECTED = "Not connected"

IDPAT = re.compile(r".*\bid:\s*(.*?)\)")
PARENPAT = re.compile(r"(\(.*?\))")
SEMIPAT = re.compile(r"(;.*)")
OPPAT = re.compile(r"(.*)\[(.*)\]")
CMDPAT = re.compile(r"([A-Za-z]+)")
BLOCKPAT = re.compile(r"^\(Block-([A-Za-z]+):\s*(.*)\)")
AUXPAT = re.compile(r"^(%[A-Za-z0-9]+)\b *(.*)$")

STOP = 0
SKIP = 1
ASK = 2
MSG = 3
WAIT = 4
UPDATE = 5

XY = 0
XZ = 1
YZ = 2

CW = 2
CCW = 3

WCS = ["G54", "G55", "G56", "G57", "G58", "G59"]

DISTANCE_MODE = {"G90": "Absolute",
                 "G91": "Incremental"}
FEED_MODE = {"G93": "1/Time",
             "G94": "unit/min",
             "G95": "unit/rev"}
UNITS = {"G20": "inch",
         "G21": "mm"}
PLANE = {"G17": "XY",
         "G18": "XZ",
         "G19": "YZ"}

# Modal Mode from $G and variable set
MODAL_MODES = {
    "G0"	: "motion",
    "G1"	: "motion",
    "G2"	: "motion",
    "G3"	: "motion",
    "G38.2"	: "motion",
    "G38.3"	: "motion",
    "G38.4"	: "motion",
    "G38.5"	: "motion",
    "G80"	: "motion",

    "G54": "WCS",
    "G55": "WCS",
    "G56": "WCS",
    "G57": "WCS",
    "G58": "WCS",
    "G59": "WCS",

    "G17": "plane",
    "G18": "plane",
    "G19": "plane",

    "G90"	: "distance",
    "G91"	: "distance",

    "G91.1": "arc",

    "G93": "feedmode",
    "G94": "feedmode",
    "G95": "feedmode",

    "G20"	: "units",
    "G21"	: "units",

    "G40"	: "cutter",

    "G43.1": "tlo",
    "G49": "tlo",

    "M0"	: "program",
    "M1"	: "program",
    "M2"	: "program",
    "M30"	: "program",

    "M3": "spindle",
    "M4": "spindle",
    "M5": "spindle",

    "M7": "coolant",
    "M8": "coolant",
    "M9": "coolant",
}
prgpath = os.path.abspath(os.path.dirname(__file__))
#steps/mm x,y,z,a,b
#X $100=80.000
#Y $101=80.000
#Z $102=40.000
#tecnically a/b steps/degree
#A $103=80.000
#B $104=40.000

#max rate mm/min
#X $110=9000.000
#Y $111=9000.000
#Z $112=300.000
#max rate mm/degree
#A $113=9000.000
#B $114=9000.000

#accel mm/s2
#X #$120=10.000
#Y #$121=10.000
#Z #$122=10.000
#accel mm/deg2
#A $123=100.000
#B $124=100.000

#max travel mm or degrees
#X $130=200.000
#Y $131=200.000
#Z $132=200.000
#A $133=360.000
#B $134=180.000


class grbl_controller:
    serial_device = None
    dwell_delay = 0
    gcode_sequence = []
    app_running = False
    buffer_length=0
    buffered_chars = 0
    all_time_gcode_lines =0
    all_time_character_count=0
    grbl_status="disconnected"
    lastResponseTime = 0
    reset_buffer = False

    crane_tilt_min=None
    crane_tilt_max=None
    crane_pan_middle=None
    gimbal_tilt_min=None
    gimbal_tilt_max=None
    gimbal_pan_middle=None
    z_min=None
    z_max=None
    z_medium=None

    xjog_factor=0.8
    yjog_factor=0.6
    ajog_factor=1
    bjog_factor=1

    def __init__(self, dwell_delay):
        
        self.name="init"
        self.controllers = {}
        self.controllerLoad()
        self.controllerSet("GRBL1")
        self.dwell_delay = dwell_delay
        self.current_move_duration = 10
        self.current_feed_speed = 1000
        self.gcode_sequence = []
        self.log = Queue()  # Log queue returned from GRBL
        self.queue = Queue()  # Command queue to be send to GRBL
        self.pendant = Queue()  # Command queue to be executed from Pendant
        self.serial = None
        self.thread = None
        self.stop_signal = False

        self._posUpdate = False  # Update position
        self._probeUpdate = False  # Update probe
        self._gUpdate = False  # Update $G
        self._update = None		# Generic update

        self.running = False
        self.runningPrev = None
        self.cleanAfter = False
        self._runLines = 0
        self._quit = 0		# Quit counter to exit program
        self._stop = False  # Raise to stop current run
        self._pause = False  # machine is on Hold
        self._alarm = True		# Display alarm message if true
        self._msg = None
        self._sumcline = 0
        self._lastFeed = 0
        self._newFeed = 0

        self._onStart = ""
        self._onStop = ""
        
        

    def set_device(self, device, baudrate, name):
        self.logger = logging.getLogger(name)
        hdlr = logging.FileHandler('./{}.log'.format(name))
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr) 
        self.logger.setLevel(logging.INFO)
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
        try:
            self.serial.setDTR(0)
        except IOError:
            pass
        time.sleep(1)
        self.serial.flushInput()
        try:
            self.serial.setDTR(1)
        except IOError:
            pass
        time.sleep(1)
        self.serial_write("\n\n")
        self._gcount = 0
        self._alarm  = True
        self.app_running = True
        self.thread = threading.Thread(
            target=self.control_thread, args=(name,))
        #self.thread.daemon = True
        self.thread.start()

  
    def controllerLoad(self):
        # Find plugins in the controllers directory and load them
        for f in glob.glob("%s/controllers/*.py" % (prgpath)):
            name, ext = os.path.splitext(os.path.basename(f))
            if name[0] == '_':
                continue
            #self.logger.info("Loaded motion controller plugin: %s"%(name))
            try:
                exec("import %s" % (name))
                self.controllers[name] = eval("%s.Controller(self)" % (name))
            except (ImportError, AttributeError):
                typ, val, tb = sys.exc_info()
                self.logger.info("Error loading controller logic {},{},{}".format(typ, val, tb))
    # ----------------------------------------------------------------------

    def controllerSet(self, ctl):
        #self.logger.info("Activating motion controller plugin: %s"%(ctl))
        if ctl in self.controllers.keys():
            self.controller = ctl
            self.mcontrol = self.controllers[ctl]

    def reset(self):
        self.mcontrol._wcsSet(0,0,0)
        self.mcontrol.unlock()
        self.mcontrol.viewParameters()
        self.mcontrol.viewSettings()

        #self.write_gcode("G10 P0 X0 Y0 Z0")
        # Toggle DTR to reset Arduino
    def stop(self):
        self.app_running=False
        

    def reset_gcode_sequence(self):
        self.gcode_sequence = []

    def set_command_delay(self, value):
        self.dwell_delay = round(value/1000,4)

    def set_move_duration(self,value):
        self.current_move_duration=value
    
    def get_move_duration(self):
        return self.current_move_duration


    def set_feed_speed(self,value):
        self.current_feed_speed=value
    
    def get_feed_speed(self):
        return self.current_feed_speed

    def set_crane_tilt_min(self):
        #set current crane tilt as lowestpoint
        self.crane_tilt_min = self.mcontrol.cnc_obj.vars["wb"]
    
    def set_crane_tilt_max(self):
        #set current crane tilt as heightpoint
        self.crane_tilt_max = self.mcontrol.cnc_obj.vars["wb"]

    def set_crane_pan_middle(self):
        #set current crane pan as centred
        self.crane_pan_middle = self.mcontrol.cnc_obj.vars["wa"]

    def set_gimbal_tilt_min(self):
         #set current gimbal tilt as lowestpoint
        self.gimbal_tilt_min = self.mcontrol.cnc_obj.vars["wy"]
    
    def set_gimbal_tilt_max(self):
         #set current gimbal tilt as hightestpoint
        self.gimbal_tilt_max = self.mcontrol.cnc_obj.vars["wy"]

    def set_gimbal_pan_middle(self):
        #set current gimbal pan as centred
        self.crane_pan_middle = self.mcontrol.cnc_obj.vars["wx"]

    def set_zoom_min(self):
        #set current z as full wide
        self.z_min = self.mcontrol.cnc_obj.vars["wz"]
    
    def set_zoom_max(self):
        #set current z as full wide
        self.z_max = self.mcontrol.cnc_obj.vars["wz"]
    
    def set_zoom_medium(self):
        #set current z as full wide
        self.z_medium = self.mcontrol.cnc_obj.vars["wz"]

    def zoom_full_out(self):
        if (self.z_min is not None):
            self.absolute_move(self.mcontrol.cnc_obj.vars["wx"],self.mcontrol.cnc_obj.vars["wy"],self.z_min,self.mcontrol.cnc_obj.vars["wa"],self.mcontrol.cnc_obj.vars["wb"],self.get_feed_speed(),0)

    def zoom_full_in(self):
        if (self.z_max is not None):
            self.absolute_move(self.mcontrol.cnc_obj.vars["wx"],self.mcontrol.cnc_obj.vars["wy"],self.z_max,self.mcontrol.cnc_obj.vars["wa"],self.mcontrol.cnc_obj.vars["wb"],self.get_feed_speed(),0)

    def zoom_medium(self):
        if (self.z_medium is not None):
            self.absolute_move(self.mcontrol.cnc_obj.vars["wx"],self.mcontrol.cnc_obj.vars["wy"],self.z_medium,self.mcontrol.cnc_obj.vars["wa"],self.mcontrol.cnc_obj.vars["wb"],self.get_feed_speed(),0)

    def relative_move(self, axis, multiplier):
        jogStep = self.current_feed_speed / 600;
        jogStep = jogStep*multiplier
        if (axis == "z"):
            if (self.z_max is not None):
                #current setup has z -negative moves zooming in
                if (jogStep+self.mcontrol.cnc_obj.vars["wz"] < self.z_max):
                    self.logger.info("detected zoom in too far command")
                    return
            if (self.z_min is not None):
                if (jogStep+self.mcontrol.cnc_obj.vars["wz"] > self.z_min):
                    self.logger.info("detected zoom out too far command")
                    return
        if (self.buffer_length==0):
            self.queue.put("$J=G91 {}{} f{}\n".format(axis,jogStep, self.current_feed_speed))
        else:
            self.logger.info("throttling jog move queue is {} long".format(self.queue.qsize()))
        time.sleep(0.1)

    def jog(self, xaxis_multiplier, yaxis_multiplier, aaxis_multiplier, baxis_multiplier):

        jogStep = self.current_feed_speed / 600;
        xjogStep = jogStep*self.xjog_factor*xaxis_multiplier
        yjogStep = jogStep*self.yjog_factor*yaxis_multiplier
        ajogStep = jogStep*self.ajog_factor*aaxis_multiplier
        bjogStep = jogStep*self.bjog_factor*baxis_multiplier
        #drop any move that takes us outside min/max bounds
        #if (self.crane_tilt_max is not None):
        #    if (bjogStep+self.mcontrol.cnc_obj.vars["wb"] > self.crane_tilt_max):
        #        bjogStep=0
        #if (self.crane_tilt_min is not None):
        #    if (bjogStep-self.mcontrol.cnc_obj.vars["wb"] < self.crane_tilt_min):
        #        bjogStep=0
        #if (self.gimbal_tilt_max is not None):
        #    if (yjogStep+self.mcontrol.cnc_obj.vars["wy"] > self.gimbal_tilt_max):
        #        yjogStep=0
        #if (self.gimbal_tilt_min is not None):
        #    if (yjogStep-self.mcontrol.cnc_obj.vars["wy"] < self.gimbal_tilt_min):
        #        yjogStep=0

        #only jog if the buffer is clear
        if (self.buffer_length==0):
            self.queue.put("$J=G91 x{} y{} a{} b{} f{}\n".format(xjogStep,yjogStep,ajogStep,bjogStep, self.current_feed_speed))
        else:
            self.logger.info("throttling jog move queue is {} long".format(self.queue.qsize()))
        time.sleep(0.1)
    
    def jog_cancel(self):
        self.serial_write("0x85")
        
    def tracking_jog(self, xaxis_multiplier, yaxis_multiplier):
        #only accept tracking jog if controller is idle otherwise jogging should feed into joystick moves
        #if self.grbl_status == "Idle":
        jogStep = self.current_feed_speed / 600;
        xjogStep = jogStep*self.xjog_factor*xaxis_multiplier
        yjogStep = jogStep*self.yjog_factor*yaxis_multiplier
        #only jog if the buffer is clear
        if (self.buffer_length==0):
            self.queue.put("$J=G91 x{} y{} f{}\n".format(xjogStep,yjogStep,self.current_feed_speed))
        else:
            self.logger.info("throttling tracking jog move queue is {} long".format(self.queue.qsize()))
        time.sleep(0.1)


    def absolute_move(self, x, y, z, a, b, feedrate, dwell):
        self.sendGCode("g90")
        self.sendGCode("g94")
        self.sendGCode("g1 x{} y{} z{} a{} b{} f{}".format(x, y, z, a,b,feedrate))
        
    def absolute_move_by_time(self, x, y, z, a, b, seconds, dwell):
        # calculate f value from desired
        # f2 = 60/2 = 30s
        feedval = 60 / seconds
        self.sendGCode("g90")
        self.sendGCode("g93")
        self.sendGCode("g1 x{} y{} z{} a{} b{} f{}".format(x, y, z, a,b,feedval))
        
    def absolute_move_timelapse(self, x, y, z, a, b, timelapse_duration_secs,minimum_time_between_steps):
        #figure out difference between current location and desired location for each axis
        #figure out smallest incremental step we send to grbl
        #devide the differences up into an even number of those small increments
        #devide the desired wait time between those steps
        xdiff = abs(x-self.mcontrol.cnc_obj.vars["wx"])
        ydiff = abs(x-self.mcontrol.cnc_obj.vars["wy"])
        zdiff = abs(x-self.mcontrol.cnc_obj.vars["wz"])
        adiff = abs(x-self.mcontrol.cnc_obj.vars["wa"])
        bdiff = abs(x-self.mcontrol.cnc_obj.vars["wb"])
        self.logger.info("timelapse: x_diff {}, y_diff {}, z_diff {}, a_diff {}, b_diff {}".format(xdiff,ydiff,zdiff,adiff,bdiff))

        jogstep=0.1
        #firgure out how many 0.1 jogs it would take to evenly move through the timelapse time
        #then normalise the step distances to the desired actual time between steps
        if (xdiff >0):
            x_steps = xdiff /jogstep
            x_step_every_exact = timelapse_duration_secs/x_steps
            x_steps = jogstep *(minimum_time_between_steps/x_step_every_exact)
        else:
            x_steps=0
            x_step_every=timelapse_duration_secs

        if (ydiff >0):
            y_steps = ydiff /jogstep
            y_step_every_exact = timelapse_duration_secs/y_steps
            y_steps = jogstep *(minimum_time_between_steps/y_step_every_exact)
        else:
            y_steps=0
            y_step_every=timelapse_duration_secs

        if (zdiff >0):
            z_steps = zdiff /jogstep
            z_step_every_exact = timelapse_duration_secs/z_steps
            z_steps = jogstep *(minimum_time_between_steps/z_step_every_exact)
        else:
            z_steps=0
            z_step_every=timelapse_duration_secs

        if (adiff >0):
            a_steps = adiff /jogstep
            a_step_every_exact = timelapse_duration_secs/a_steps
            a_steps = jogstep *(minimum_time_between_steps/a_step_every_exact)
        else:
            a_steps=0
            a_step_every=timelapse_duration_secs

        if (bdiff >0):
            b_steps = bdiff /jogstep
            b_step_every_exact = timelapse_duration_secs/b_steps
            b_steps = jogstep *(minimum_time_between_steps/b_step_every_exact)
        else:
            b_steps=0
            b_step_every=timelapse_duration_secs

        self.logger.info("timelapse moves: x {}, y {}, z {}, a {}, b {}".format(x_steps,y_steps,z_steps,a_steps,b_steps))
        step=0
               
        steps = int(timelapse_duration_secs/minimum_time_between_steps)
        for x in range(1, steps):
            self.logger.info("timelapse move at {}".format(time.time()))
            self.queue.put("$J=G91 x{} y{} z{} a{} b{} f{}\n".format(x_steps,y_steps,z_steps,a_steps,b_steps, self.current_feed_speed))
            time.sleep(minimum_time_between_steps)

    def add_absolute_move_by_time_to_sequence(self, x, y, z, a, b, seconds, dwell):
        feedval = 60 / seconds
        if len(self.gcode_sequence) == 0:
            # first statement gets initial delay
            self.gcode_sequence.append("g04 P{}".format(self.dwell_delay))
        self.gcode_sequence.append("g90")
        self.gcode_sequence.append("g93")
        self.gcode_sequence.append("g1 x{} y{} z{} a{} b{} f{}".format(x, y, z,a,b, feedval))
        self.gcode_sequence.append("g4 P{}".format(dwell))

    def add_absolute_move_by_feed_to_sequence(self, x, y, z, a, b, feedrate, dwell):

        if len(self.gcode_sequence) == 0:
            # first statement gets initial delay
            self.gcode_sequence.append("g04 P{}".format(self.dwell_delay))
        self.gcode_sequence.append("g90")
        self.gcode_sequence.append("g94")
        self.gcode_sequence.append("g1 x{} y{} z{} a{} b{} f{}".format(x, y, z,a,b, feedrate))
        self.gcode_sequence.append("g4 P{}".format(dwell))


    def print_gcode_sequence(self):
        seq_num = 0
        self.logger.info("Current gcode sequence")
        self.logger.info("########### START ##############")
        for gcode in self.gcode_sequence:
            self.logger.info("{}:{}".format(seq_num, gcode))
            seq_num = seq_num+1
        self.logger.info("########### END ##############")

    def run_sequence(self):
        self.logger.info("Queuing stored gcode sequence")
        for gcode in self.gcode_sequence:
            self.queue.put(gcode+"\n")
        self.reset_gcode_sequence()
        #wait for idle again
        self.logger.info("sequence written to queue, grbl status = {}".format(self.grbl_status))
        time.sleep(2)
        self.logger.info("slept 2 seconds after sequence queued, grbl status = {}".format(self.grbl_status))
        while (self.grbl_status != "Idle"):
            time.sleep(0.5)
            self.logger.info("waiting for idle post sequence run")

    

    def sendGCode(self, cmd):
        self.logger.info("{} : instruction:\n{}".format(time.ctime(), cmd))
        if self.serial and not self.running:
            if isinstance(cmd, tuple):
                self.queue.put(cmd)
            else:
                self.queue.put(cmd+"\n")

    def position_str(self):
        pos_str =  "wx:{},wy:{},wz:{},wa:{},wb:{}\nmx:{},my:{},mz:{},ma:{},mb:{}".format(self.mcontrol.cnc_obj.vars["wx"], self.mcontrol.cnc_obj.vars["wy"], self.mcontrol.cnc_obj.vars["wz"],self.mcontrol.cnc_obj.vars["wa"],self.mcontrol.cnc_obj.vars["wb"],self.mcontrol.cnc_obj.vars["mx"], self.mcontrol.cnc_obj.vars["my"], self.mcontrol.cnc_obj.vars["mz"],self.mcontrol.cnc_obj.vars["ma"],self.mcontrol.cnc_obj.vars["mb"])
        self.logger.debug("returning position: {}".format(pos_str))
        return pos_str
        
    
    
         
    def currentlocation(self, rotation_axis, tilt_axis, zoom_axis):
        loc = location(self.mcontrol.cnc_obj.vars["w{}".format(rotation_axis)],self.mcontrol.cnc_obj.vars["w{}".format(tilt_axis)],self.mcontrol.cnc_obj.vars["w{}".format(zoom_axis)])
        return loc

    # ----------------------------------------------------------------------
    # Serial write
    # ----------------------------------------------------------------------

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

    def emptyQueue(self):
        while self.queue.qsize() > 0:
            try:
                self.queue.get_nowait()
            except:
                break

    def status(self):
        self.sio_status=True
    
    def get_grbl_status(self):
        return self.grbl_status

    def get_lastUpdateTime(self):
        return self.lastResponseTime
   
    def controllerStateChange(self, state):
        self.logger.info("Controller state changed to: %s (Running: %s)" %
              (state, self.running))
        self.grbl_status = state
        #if state in ("Idle"):
        #    self.mcontrol.viewParameters()
        #    self.mcontrol.viewState()

    def update_buffer_info(self, cline, sline):
        self.buffer_length = len(sline)
        self.buffered_chars = sum(cline)
        

    def bufferedGcodeCount(self):
        return self.buffer_length
    
    def bufferredCharCount(self):
        return self.buffered_chars

    def emptybuffer(self):
        self.reset_buffer=True


    def control_thread(self, name):
        self.logger.info("########################################")
        self.logger.info("Thread start for grbl on :{}".format(name))
        self.logger.info("########################################")
        # wait for commands to complete (status change to Idle)
        #self.sleep_event    = threading.Event()
        self.sio_wait = False
        self.sio_status = False		# waiting for status <...> report
        cline = []		# length of pipeline commands
        sline = []			# pipeline commands
        gcodeToSend = None			# next string to send
        lastWriteAt = tg = time.time()
        while self.app_running:
            self.update_buffer_info(cline,sline)

            try:
                if self.reset_buffer == True:
                    for line in sline:
                        self.logger.info("dumpping buffered line: {}".format(line) )                
                    sline=[]    
                    cline=[]
                    self.reset_buffer=False
                #print ("gcode queue length {}".format(self.queue.qsize()))

                t = time.time()
              
                # Anything to receive?
                
                    
                #if self.serial.inWaiting():
                try:
                    line = str(self.serial.readline().decode()).strip()
                except:
                    self.emptyQueue()
                    return

                # print "<R<",repr(line)
                # print "*-* stack=",sline,"sum=",sum(cline),"wait=",wait,"pause=",self._pause
                if not line:
                    pass
                elif self.mcontrol.parseLine(line, cline, sline):
                    self.lastResponseTime = time.strftime('%X')
                    pass


                # refresh machine position?
                if gcodeToSend is None:
                    try:
                        self.logger.debug("Command queue length {}".format(self.queue.qsize()))
                        gcodeToSend = self.queue.get_nowait()
                        self.logger.debug("pulled new gcode line to send: {}".format(gcodeToSend))
                    except Empty:
                        #nothing to send
                        gcodeToSend = None
                
                    if gcodeToSend is not None:
                        self.all_time_gcode_lines = self.all_time_gcode_lines+1
                        self.all_time_character_count = self.all_time_character_count+len(gcodeToSend)
                        sline.append(gcodeToSend)
                        cline.append(len(gcodeToSend))
                        self.logger.debug("send buffer size {}".format(sum(cline)))

                if gcodeToSend is not None and sum(cline) < RX_BUFFER_SIZE:
                    # Bookkeeping of the buffers
                
                    self._sumcline = sum(cline)
        #				if isinstance(tosend, list):
        #					self.serial_write(str(tosend.pop(0)))
        #					if not tosend: tosend = None

                    # print ">S>",repr(tosend),"stack=",sline,"sum=",sum(cline)
                    if self.mcontrol.gcode_case > 0:
                        gcodeToSend = gcodeToSend.upper()
                    if self.mcontrol.gcode_case < 0:
                        gcodeToSend = gcodeToSend.lower()
                    self.logger.debug("writing queued instruction {}".format(gcodeToSend))
                    self.serial_write(gcodeToSend.encode())

                    gcodeToSend = None
                else:
                    if t-lastWriteAt > SERIAL_POLL:
                        self.serial_write(b"?")
                        lastWriteAt = t
                        self.sio_status = True
                    #else:
                    #    if t-tg > G_POLL:
                    #        self.sendGCode("$G\n")
                            
            except:
                self.logger.error("Exception in thread for {}".format(name))   
        self.logger.info("########################################")
        self.logger.info("Thread stopping for grbl on :{}".format(name))
        self.logger.info("########################################")
        