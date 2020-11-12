# -*- coding: utf-8 -*-
import serial
import time
import threading

SERIAL_POLL = 0.125
SERIAL_TIMEOUT = 0.10  # s
G_POLL = 10  # s
RX_BUFFER_SIZE = 128

GPAT = re.compile(r"[A-Za-z]\s*[-+]?\d+.*")
FEEDPAT = re.compile(r"^(.*)[fF](\d+\.?\d+)(.*)$")

CONNECTED = "Connected"
NOT_CONNECTED = "Not connected"

IDPAT    = re.compile(r".*\bid:\s*(.*?)\)")
PARENPAT = re.compile(r"(\(.*?\))")
SEMIPAT  = re.compile(r"(;.*)")
OPPAT    = re.compile(r"(.*)\[(.*)\]")
CMDPAT   = re.compile(r"([A-Za-z]+)")
BLOCKPAT = re.compile(r"^\(Block-([A-Za-z]+):\s*(.*)\)")
AUXPAT   = re.compile(r"^(%[A-Za-z0-9]+)\b *(.*)$")

STOP   = 0
SKIP   = 1
ASK    = 2
MSG    = 3
WAIT   = 4
UPDATE = 5

XY   = 0
XZ   = 1
YZ   = 2

CW   = 2
CCW  = 3

WCS  = ["G54", "G55", "G56", "G57", "G58", "G59"]

DISTANCE_MODE = { "G90" : "Absolute",
		  "G91" : "Incremental" }
FEED_MODE     = { "G93" : "1/Time",
		  "G94" : "unit/min",
		  "G95" : "unit/rev"}
UNITS         = { "G20" : "inch",
		  "G21" : "mm" }
PLANE         = { "G17" : "XY",
		  "G18" : "XZ",
		  "G19" : "YZ" }

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

	"G54"   : "WCS",
	"G55"   : "WCS",
	"G56"   : "WCS",
	"G57"   : "WCS",
	"G58"   : "WCS",
	"G59"   : "WCS",

	"G17"   : "plane",
	"G18"   : "plane",
	"G19"   : "plane",

	"G90"	: "distance",
	"G91"	: "distance",

	"G91.1" : "arc",

	"G93"   : "feedmode",
	"G94"   : "feedmode",
	"G95"   : "feedmode",

	"G20"	: "units",
	"G21"	: "units",

	"G40"	: "cutter",

	"G43.1" : "tlo",
	"G49"   : "tlo",

	"M0"	: "program",
	"M1"	: "program",
	"M2"	: "program",
	"M30"	: "program",

	"M3"    : "spindle",
	"M4"    : "spindle",
	"M5"    : "spindle",

	"M7"    : "coolant",
	"M8"    : "coolant",
	"M9"    : "coolant",
}


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
        self.MODE = mode
        self.dwell_delay = dwell_delay
        self.gcode_sequence = []
        self.log = Queue()  # Log queue returned from GRBL
        self.queue = Queue()  # Command queue to be send to GRBL
        self.pendant = Queue()  # Command queue to be executed from Pendant
        self.serial = None
        self.thread = None

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

    def set_device(self, device):
        self.serial_device = device
        if self.MODE == self.REAL_MODE:
            self.serial = serial.Serial(device, 115200, timeout=0.2)
        x = threading.Thread(target=self.control_thread,
                             args=(self.serial_device,))
        x.start()

    def reset(self):
        #self.write_gcode("G10 P0 X0 Y0 Z0")
        self.write_gcode("G92 X0 Y0 Z0")
        self.write_gcode("$#")
        self.write_gcode("?")

    def reset_gcode_sequence(self):
        self.gcode_sequence = []

    def set_command_delay(self, value):
        self.dwell_delay = value

    def relative_move(self, move_str, feedrate):

        self.write_gcode("g91\r\ng94\r\ng1 {} f{}".format(move_str, feedrate))

    def absolute_move(self, x, y, z, feedrate, dwell):
        self.write_gcode("g4 P{}\r\ng90\r\ng94\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(
            self.dwell_delay, x, y, z, feedrate, dwell))

    def absolute_move_by_time(self, x, y, z, seconds, dwell):
        # calculate f value from desired
        # f2 = 60/2 = 30s
        feedval = 60 / seconds
        self.write_gcode("g4 P{}\r\ng90\r\ng93\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(
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
            self.write_gcode(gcode)
        self.reset_gcode_sequence()

    def write_gcode(self, gcode_str):
        print("{} : instruction: {}".format(time.ctime(), gcode_str))
        if self.MODE == self.REAL_MODE:
            self.serial.write(gcode_str.encode())
            self.serial.write('\n'.encode())
            status = self.serial.readline()
            count = 0

            while (status == b'ok\r\n') or (status == b'error\r\n'):
                print("grbl:{} ->{}<-".format(time.ctime(), status))
                count = count + 1
                status = self.serial.readline()
                if count > 200:
                    print("waited too long for ok")
                    break

        else:
            print("mocking sending {}".format(gcode_str))

    def read_output(self):
        if self.MODE == self.REAL_MODE:
            status = self.serial.readline()
            if status != b'':
                print(status.decode("utf-8"))
                return status.decode("utf-8")
        else:
            return "pong"

    def control_thread(self, name):
        print("Thread start for grbl on :{}".format(name))
        self.sio_wait   = False		# wait for commands to complete (status change to Idle)
		self.sio_status = False		# waiting for status <...> report
        cline = []		# length of pipeline commands
        sline = []			# pipeline commands
        tosend = None			# next string to send
        tr = time.time()
        while self.thread:
            time.sleep(0.01)
            t = time.time()
            # refresh machine position?
            if t-tr > SERIAL_POLL:
                self.write_gcode("?")
                tr = t

                # Fetch new command to send if...
            if tosend is None and not self.sio_wait and not self._pause and self.queue.qsize() > 0:
                try:
                    tosend = self.queue.get_nowait()
                    # print "+++",repr(tosend)
                    if isinstance(tosend, tuple):
                        # print "gcount tuple=",self._gcount
                        # wait to empty the grbl buffer and status is Idle
                        if tosend[0] == WAIT:
                            # Don't count WAIT until we are idle!
                            self.sio_wait = True
                            # print "+++ WAIT ON"
                            # print "gcount=",self._gcount, self._runLines
                        elif tosend[0] == MSG:
                            # Count executed commands as well
                            self._gcount += 1
                            if tosend[1] is not None:
                                # show our message on machine status
                                self._msg = tosend[1]
                        elif tosend[0] == UPDATE:
                            # Count executed commands as well
                            self._gcount += 1
                            self._update = tosend[1]
                        else:
                            # Count executed commands as well
                            self._gcount += 1
                        tosend = None

                    elif not isinstance(tosend, str):
                        try:
                            tosend = self.gcode.evaluate(tosend, self)
#							if isinstance(tosend, list):
#								cline.append(len(tosend[0]))
#								sline.append(tosend[0])
                            if isinstance(tosend, str):
                                tosend += "\n"
                            else:
                                # Count executed commands as well
                                self._gcount += 1
                                # print "gcount str=",self._gcount
                            # print "+++ eval=",repr(tosend),type(tosend)
                        except:
                            for s in str(sys.exc_info()[1]).splitlines():
                                self.log.put((Sender.MSG_ERROR, s))
                            self._gcount += 1
                            tosend = None
                except Empty:
                    break

                

                    # Bookkeeping of the buffers
                    sline.append(tosend)
                    cline.append(len(tosend))

            # Anything to receive?
            if self.serial.inWaiting() or tosend is None:
                try:
                    line = str(self.serial.readline().decode()).strip()
                except:
                    self.emptyQueue()
                    self.close()
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
                tosend = None
                
                # WARNING if runLines==maxint then it means we are
                # still preparing/sending lines from from bCNC.run(),
                # so don't stop
                if self._runLines != sys.maxsize:
                    self._stop = False

            # print "tosend='%s'"%(repr(tosend)),"stack=",sline,
            #	"sum=",sum(cline),"wait=",wait,"pause=",self._pause
            if tosend is not None and sum(cline) < RX_BUFFER_SIZE:
                self._sumcline = sum(cline)
#				if isinstance(tosend, list):
#					self.serial_write(str(tosend.pop(0)))
#					if not tosend: tosend = None

                # print ">S>",repr(tosend),"stack=",sline,"sum=",sum(cline)
                if self.mcontrol.gcode_case > 0:
                    tosend = tosend.upper()
                if self.mcontrol.gcode_case < 0:
                    tosend = tosend.lower()

                self.serial_write(tosend)

                tosend = None
                if not self.running and t-tg > G_POLL:
                    tosend = b"$G\n"  # FIXME: move to controller specific class
                    sline.append(tosend)
                    cline.append(len(tosend))
                    tg = t
