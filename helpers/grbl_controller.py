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

SERIAL_POLL = 0.125
SERIAL_TIMEOUT = 0.10  # s
G_POLL = 10  # s
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
        print("init")
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
        self.sio_wait = False
        self.sio_status = False		# waiting for status <...> report
        self.cline = []		# length of pipeline commands
        self.sline = []			# pipeline commands
        self.gcodeToSend = None			# next string to send
        self.lastWriteAt = tg = time.time()
        

    def set_device(self, device, baudrate, name):
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
        self._gcount = 0
        self._alarm = True
        self.name=name
#        self.thread = threading.Thread(
#            target=self.control_thread, args=(name,))
#        self.thread.start()

    def stop(self):
        self.stop_signal=True
   
    def controllerLoad(self):
        # Find plugins in the controllers directory and load them
        for f in glob.glob("%s/controllers/*.py" % (prgpath)):
            name, ext = os.path.splitext(os.path.basename(f))
            if name[0] == '_':
                continue
            #print("Loaded motion controller plugin: %s"%(name))
            try:
                exec("import %s" % (name))
                self.controllers[name] = eval("%s.Controller(self)" % (name))
            except (ImportError, AttributeError):
                typ, val, tb = sys.exc_info()
                print("Error loading controller logic {},{},{}".format(typ, val, tb))
    # ----------------------------------------------------------------------

    def controllerSet(self, ctl):
        #print("Activating motion controller plugin: %s"%(ctl))
        if ctl in self.controllers.keys():
            self.controller = ctl
            self.mcontrol = self.controllers[ctl]

    def reset(self):
        #self.write_gcode("G10 P0 X0 Y0 Z0")
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

    def reset_gcode_sequence(self):
        self.gcode_sequence = []

    def set_command_delay(self, value):
        self.dwell_delay = value

    def relative_move(self, move_str, feedrate):

        self.sendGCode("g91\r\ng94\r\ng1 {} f{}".format(move_str, feedrate))

    def absolute_move(self, x, y, z, feedrate, dwell):
        self.sendGCode("g4 P{}\r\ng90\r\ng94\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(
            self.dwell_delay, x, y, z, feedrate, dwell))

    def absolute_move_by_time(self, x, y, z, seconds, dwell):
        # calculate f value from desired
        # f2 = 60/2 = 30s
        feedval = 60 / seconds
        self.sendGCode("g4 P{}\r\ng90\r\ng93\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(
            self.dwell_delay, x, y, z, feedval, dwell))

    def add_absolute_move_by_time_to_sequence(self, x, y, z, seconds, dwell):
        feedval = 60 / seconds
        if len(self.gcode_sequence) == 0:
            # first statement gets initial delay
            self.gcode_sequence.append("g04 P{}\r\ng90\r\ng93\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(
                self.dwell_delay, x, y, z, feedval, dwell))
        else:
            self.gcode_sequence.append(
                "\r\ng90\r\ng93\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(x, y, z, feedval, dwell))

    def add_absolute_move_by_feed_to_sequence(self, x, y, z, feedrate, dwell):

        if len(self.gcode_sequence) == 0:
            # first statement gets initial delay
            self.gcode_sequence.append("g04 P{}\r\ng90\r\ng94\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(
                self.dwell_delay, x, y, z, feedrate, dwell))
        else:
            self.gcode_sequence.append(
                "\r\ng90\r\ng94\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(x, y, z, feedrate, dwell))

    def print_gcode_sequence(self, name):
        seq_num = 0
        for gcode in self.gcode_sequence:
            print("{}:{}:{}".format(name, seq_num, gcode))
            seq_num = seq_num+1

    def run_sequence(self, name):
        for gcode in self.gcode_sequence:
            self.sendGCode(gcode)
        self.reset_gcode_sequence()

    def sendGCode(self, cmd):
        print("{} : instruction: {}".format(time.ctime(), cmd))
        if self.serial and not self.running:
            if isinstance(cmd, tuple):
                self.queue.put(cmd)
            else:
                self.queue.put(cmd+"\n")

    def position_str(self):
        return "wx:{},wy:{},wz:{},mx:{},my:{},mz:{}".format(self.mcontrol.cnc_obj.vars["wx"], self.mcontrol.cnc_obj.vars["wy"], self.mcontrol.cnc_obj.vars["wz"], self.mcontrol.cnc_obj.vars["mx"], self.mcontrol.cnc_obj.vars["my"], self.mcontrol.cnc_obj.vars["mz"])
    
    
         
    def currentlocation(self):
        loc = location(self.mcontrol.cnc_obj.vars["wx"],self.mcontrol.cnc_obj.vars["wy"],self.mcontrol.cnc_obj.vars["wz"])
        return loc

    # ----------------------------------------------------------------------
    # Serial write
    # ----------------------------------------------------------------------

    def serial_write(self, data):
        #print("W "+str(type(data))+" : "+str(data))

        # if sys.version_info[0] == 2:
        #	ret = self.serial.write(str(data))
        if self.MODE == self.REAL_MODE:
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
        self.mcontrol.viewStatusReport()

    def tick(self,name):
        self.control_thread(name)


    def controllerStateChange(self, state):
        print("Controller state changed to: %s (Running: %s)" %
              (state, self.running))
        if state in ("Idle"):
            self.mcontrol.viewParameters()
            self.mcontrol.viewState()

        if self.cleanAfter == True and self.running == False and state in ("Idle"):
            self.cleanAfter = False

    def control_thread(self, name):
        print("Thread start for grbl on :{}".format(name))
        # wait for commands to complete (status change to Idle)
        #while self.stop_signal != True:
        #    if ( True == self.sleep_event.wait( timeout=0.2 ) ):
        #        break
        t = time.time()
        # refresh machine position?
        if t-self.lastWriteAt > SERIAL_POLL:
            self.serial_write(b"?")
            self.lastWriteAt = t

            # Fetch new command to send if...
        if gcodeToSend is None and not self.sio_wait and not self._pause and self.queue.qsize() > 0:
            try:
                gcodeToSend = self.queue.get_nowait()
                # print "+++",repr(tosend)
                if isinstance(gcodeToSend, tuple):
                    # print "gcount tuple=",self._gcount
                    # wait to empty the grbl buffer and status is Idle
                    if gcodeToSend[0] == WAIT:
                        # Don't count WAIT until we are idle!
                        self.sio_wait = True
                        # print "+++ WAIT ON"
                        # print "gcount=",self._gcount, self._runLines
                    elif gcodeToSend[0] == MSG:
                        # Count executed commands as well
                        self._gcount += 1
                        if gcodeToSend[1] is not None:
                            # show our message on machine status
                            self._msg = gcodeToSend[1]
                    elif gcodeToSend[0] == UPDATE:
                        # Count executed commands as well
                        self._gcount += 1
                        self._update = gcodeToSend[1]
                    else:
                        # Count executed commands as well
                        self._gcount += 1
                    gcodeToSend = None
            except:
                return

                # Bookkeeping of the buffers
                sline.append(gcodeToSend)
                cline.append(len(gcodeToSend))

        # Anything to receive?
        if self.MODE == self.REAL_MODE:
            if self.serial.inWaiting() or gcodeToSend is None:
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

        # Received external message to stop
        if self._stop:
            self.emptyQueue()
            self.gcodeToSend = None

            # WARNING if runLines==maxint then it means we are
            # still preparing/sending lines from from bCNC.run(),
            # so don't stop
            if self._runLines != sys.maxsize:
                self._stop = False

        # print "tosend='%s'"%(repr(tosend)),"stack=",sline,
        #	"sum=",sum(cline),"wait=",wait,"pause=",self._pause
        if self.gcodeToSend is not None and sum(cline) < RX_BUFFER_SIZE:
            self._sumcline = sum(cline)
#				if isinstance(tosend, list):
#					self.serial_write(str(tosend.pop(0)))
#					if not tosend: tosend = None

            # print ">S>",repr(tosend),"stack=",sline,"sum=",sum(cline)
            if self.mcontrol.gcode_case > 0:
                self.gcodeToSend = self.gcodeToSend.upper()
            if self.mcontrol.gcode_case < 0:
                self.gcodeToSend = self.gcodeToSend.lower()

            self.serial_write(self.gcodeToSend)

            self.gcodeToSend = None
            if not self.running and t-self.tg > G_POLL:
                gcodeToSend = b"$G\n"  # FIXME: move to controller specific class
                sline.append(self.gcodeToSend)
                cline.append(len(self.gcodeToSend))
                self.tg = t
