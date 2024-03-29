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


class grbl_controller:
    serial_device = None
    MOCK_MODE = 1
    REAL_MODE = 0
    MODE = REAL_MODE
    dwell_delay = 0
    gcode_sequence = []

    thread = True

    def __init__(self, mode, dwell_delay):
        
        self.name="init"
        self.controllers = {}
        self.controllerLoad()
        self.controllerSet("GRBL1")
        self.MODE = mode
        self.dwell_delay = dwell_delay
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
        if self.MODE == self.REAL_MODE:
            #self.serial = serial.Serial(device, 115200, timeout=0.2)
            self.serial = serial.serial_for_url(
                device.replace('\\', '\\\\'),  # Escape for windows
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
            self.serial_write(b"\n\n")
            #soft reset grbl
            self.serial_write(b"\030")
        self._gcount = 0
        self._alarm = True
        self.name=name
        self.thread = threading.Thread(
            target=self.control_thread, args=(name,))
        self.thread.start()


    def stop(self):
        self.stop_signal=True
   
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
        #self.write_gcode("G10 P0 X0 Y0 Z0")
        # Toggle DTR to reset Arduino
        

    def reset_gcode_sequence(self):
        self.gcode_sequence = []

    def set_command_delay(self, value):
        self.dwell_delay = round(value/1000,4)

    def relative_move(self, move_str, feedrate):
        self.sendGCode("g91")
        self.sendGCode("g94")
        self.sendGCode("g1 {} f{}".format(move_str, feedrate))

    def absolute_move(self, x, y, z, feedrate, dwell):
        self.sendGCode("g04 P{}".format(self.dwell_delay))
        self.sendGCode("g90")
        self.sendGCode("g94")
        self.sendGCode("g1 x{} y{} z{} f{}".format(x, y, z, feedrate))
        self.sendGCode("g4 P{}".format(dwell))

    def absolute_move_by_time(self, x, y, z, seconds, dwell):
        # calculate f value from desired
        # f2 = 60/2 = 30s
        feedval = 60 / seconds
        self.sendGCode("g04 P{}".format(self.dwell_delay))
        self.sendGCode("g90")
        self.sendGCode("g93")
        self.sendGCode("g1 x{} y{} z{} f{}".format(x, y, z, feedval))
        self.sendGCode("g4 P{}".format(dwell))

    def add_absolute_move_by_time_to_sequence(self, x, y, z, seconds, dwell):
        feedval = 60 / seconds
        if len(self.gcode_sequence) == 0:
            # first statement gets initial delay
            self.gcode_sequence.append("g04 P{}".format(self.dwell_delay))
        self.gcode_sequence.append("g90")
        self.gcode_sequence.append("g93")
        self.gcode_sequence.append("g1 x{} y{} z{} f{}".format(x, y, z, feedval))
        self.gcode_sequence.append("g4 P{}".format(dwell))

    def add_absolute_move_by_feed_to_sequence(self, x, y, z, feedrate, dwell):

        if len(self.gcode_sequence) == 0:
            # first statement gets initial delay
            self.gcode_sequence.append("g04 P{}".format(self.dwell_delay))
        self.gcode_sequence.append("g90")
        self.gcode_sequence.append("g94")
        self.gcode_sequence.append("g1 x{} y{} z{} f{}".format(x, y, z, feedrate))
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

    def sendGCode(self, cmd):
        self.logger.info("{} : instruction:\n{}".format(time.ctime(), cmd))
        if self.serial and not self.running:
            if isinstance(cmd, tuple):
                self.queue.put(cmd)
            else:
                self.queue.put(cmd+"\n")

    def position_str(self):
        pos_str =  "wx:{},wy:{},wz:{}\nmx:{},my:{},mz:{}".format(self.mcontrol.cnc_obj.vars["wx"], self.mcontrol.cnc_obj.vars["wy"], self.mcontrol.cnc_obj.vars["wz"], self.mcontrol.cnc_obj.vars["mx"], self.mcontrol.cnc_obj.vars["my"], self.mcontrol.cnc_obj.vars["mz"])
        self.logger.debug("returning position: {}".format(pos_str))
        return pos_str
        
    
    
         
    def currentlocation(self):
        loc = location(self.mcontrol.cnc_obj.vars["wx"],self.mcontrol.cnc_obj.vars["wy"],self.mcontrol.cnc_obj.vars["wz"])
        return loc

    # ----------------------------------------------------------------------
    # Serial write
    # ----------------------------------------------------------------------

    def serial_write(self, data):
        self.logger.debug("W "+str(type(data))+" : "+str(data))

        # if sys.version_info[0] == 2:
        #	ret = self.serial.write(str(data))
        if self.MODE == self.REAL_MODE:
            if isinstance(data, bytes):
                ret = self.serial.write(data)
            else:
                ret = self.serial.write(data.encode())
            self.logger.debug("grbl response {}".format(ret))
            return ret

    def emptyQueue(self):
        while self.queue.qsize() > 0:
            try:
                self.queue.get_nowait()
            except:
                break

    def status(self):
        self.sio_status=True

   
    def controllerStateChange(self, state):
        self.logger.info("Controller state changed to: %s (Running: %s)" %
              (state, self.running))
        #if state in ("Idle"):
        #    self.mcontrol.viewParameters()
        #    self.mcontrol.viewState()


    def control_thread(self, name):
        self.logger.info("########################################")
        self.logger.info("Thread start for grbl on :{}".format(name))
        self.logger.info("########################################")
        # wait for commands to complete (status change to Idle)
        self.sleep_event    = threading.Event()
        self.sio_wait = False
        self.sio_status = False		# waiting for status <...> report
        cline = []		# length of pipeline commands
        sline = []			# pipeline commands
        gcodeToSend = None			# next string to send
        lastWriteAt = tg = time.time()
        while self.stop_signal != True:
            try:
                time.sleep(0.1)
                #print ("gcode queue length {}".format(self.queue.qsize()))

                t = time.time()

                # Anything to receive?
                if self.MODE == self.REAL_MODE:
                    if self.serial.inWaiting():
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
                            pass


                # refresh machine position?
                if gcodeToSend is None:
                    try:
                        self.logger.debug("Command queue length {}".format(self.queue.qsize()))
                        gcodeToSend = self.queue.get_nowait()
                    except Empty:
                        #nothing to send
                        gcodeToSend = None
                
                    if gcodeToSend is not None:
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
                    else:
                        if t-tg > G_POLL:
                            self.serial_write(b"$G\n")
                            tg = t
            except:
                self.logger.error("Exception in thread for {}".format(name))   
        self.logger.info("########################################")
        self.logger.info("Thread stopping for grbl on :{}".format(name))
        self.logger.info("########################################")
        