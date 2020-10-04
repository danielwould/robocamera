import serial

class grbl_controller:
    
    grbl_connection = None
    serial_device = None

    def __init__(self):
        print ("init")

    def set_device(self,device):
        self.serial_device = device
        self.grbl_connection = serial.Serial(device, 115200, timeout=0.2)

    def relative_move(self,move_str, feedrate):
        self.write_gcode("g91")
        self.write_gcode("g94")
        self.write_gcode("g1 {} f{}".format(move_str, feedrate))


    def absolute_move(self,x, y, z, feedrate):
        self.write_gcode("g90")
        self.write_gcode("g94")
        self.write_gcode("g1 x{} y{} z{} f{}".format(x, y, z, feedrate))

    def absolute_move_by_time(self,x, y, z, seconds):
        #calculate f value from desired
        # f2 = 60/2 = 30s
        feedval = 60/seconds 
        self.write_gcode("g90")
        self.write_gcode("g93") #inverse feed time
        self.write_gcode("g1 x{} y{} z{} f{}".format(x, y, z, feedval))

    def write_gcode(self,gcode_str):
        print(gcode_str)
        self.grbl_connection.write(gcode_str.encode())
        self.grbl_connection.write('\n'.encode())
        status = self.grbl_connection.readline()
        print (status)
    
