import serial
import time

class grbl_controller:
    grbl_connection = None
    serial_device = None
    MOCK_MODE = 1
    REAL_MODE = 0
    MODE = REAL_MODE
    dwell_delay=0
    gcode_sequence = ""

    def __init__(self, mode, dwell_delay):
        print("init")
        self.MODE = mode
        self.dwell_delay = dwell_delay

    def set_device(self, device):
        self.serial_device = device
        if self.MODE == self.REAL_MODE:
            self.grbl_connection = serial.Serial(device, 115200, timeout=0.2)

    def reset(self):
        #self.write_gcode("G10 P0 X0 Y0 Z0")
        self.write_gcode("G92 X0 Y0 Z0")
        self.write_gcode("$#")
        self.write_gcode("?")

    def reset_gcode_sequence(self):
        self.gcode_sequence=""

    def set_command_delay(self,value):
        self.dwell_delay = value

    def relative_move(self, move_str, feedrate):

        self.write_gcode("g4 P{}\r\ng91\r\ng94\r\ng1 {} f{}".format(self.dwell_delay,move_str, feedrate))
        
    def absolute_move(self, x, y, z, feedrate, dwell):
        self.write_gcode("g4 P{}\r\ng90\r\ng94\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(self.dwell_delay,x, y, z, feedrate,dwell))
        
    def absolute_move_by_time(self, x, y, z, seconds, dwell):
        # calculate f value from desired
        # f2 = 60/2 = 30s
        feedval = 60 / seconds
        self.write_gcode("g4 P{}\r\ng90\r\ng93\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(self.dwell_delay,x, y, z, feedval, dwell))

    def add_absolute_move_by_time_to_sequence(self, x,y,z,seconds,dwell):
        feedval = 60 / seconds
        if self.gcode_sequence == "":
            #first statement gets initial delay
            self.gcode_sequence="g4 P{}\r\ng90\r\ng93\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(self.dwell_delay,x, y, z, feedval, dwell)
        else:
            self.gcode_sequence=self.gcode_sequence+"\r\ng90\r\ng93\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(x, y, z, feedval, dwell)

    def add_absolute_move_by_feed_to_sequence(self, x,y,z,feedrate,dwell):
        
        if self.gcode_sequence == "":
            #first statement gets initial delay
            self.gcode_sequence="g4 P{}\r\ng90\r\ng94\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(self.dwell_delay,x, y, z, feedrate,dwell)
        else:
            self.gcode_sequence=self.gcode_sequence+"\r\ng90\r\ng94\r\ng1 x{} y{} z{} f{}\r\ng4 P{}".format(x, y, z, feedrate, dwell)

    def run_sequence(self):
        self.write_gcode(self.gcode_sequence)
        self.reset_gcode_sequence()

    def write_gcode(self, gcode_str):
        print("{} : instruction: {}".format(time.ctime(), gcode_str))
        if self.MODE == self.REAL_MODE:
            self.grbl_connection.write(gcode_str.encode())
            self.grbl_connection.write('\n'.encode())
            status = self.grbl_connection.readline()
            count=0
            while count <3:
                if len(status) >2:
                    
                    print("grbl:{} -  {}".format(time.ctime(),status))
                if len(status) <2:
                    count = count +1    
                status = self.grbl_connection.readline()
                
        else:
            print("mocking sending {}".format(gcode_str))
