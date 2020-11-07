import serial
import time

class grbl_controller:
    grbl_connection = None
    serial_device = None
    MOCK_MODE = 1
    REAL_MODE = 0
    MODE = REAL_MODE
    dwell_delay=0

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


    def relative_move(self, move_str, feedrate):

        self.write_gcode("g4 P{}\r\ng91\r\ng94\r\ng1 {} f{}".format(self.dwell_delay,move_str, feedrate))
        
    def absolute_move(self, x, y, z, feedrate):
        self.write_gcode("g4 P{}\r\ng90\r\ng94\r\ng1 x{} y{} z{} f{}".format(self.dwell_delay,x, y, z, feedrate))
        
    def absolute_move_by_time(self, x, y, z, seconds):
        # calculate f value from desired
        # f2 = 60/2 = 30s
        feedval = 60 / seconds
        self.write_gcode("g4 P{}\r\ng90\r\ng93\r\ng1 x{} y{} z{} f{}".format(self.dwell_delay,x, y, z, feedval))
        
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
