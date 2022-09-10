
class waypoint:
    id=1
    dwell_time = 10
    feed_rate = 250
    travel_duration = 10
    xpos=0
    ypos=0
    zpos=0
    apos=0
    bpos=0
    

    def __init__(self, id,xyzpos, abcpos):
        self.id=id
        self.xpos = xyzpos.get_rotation_pos()
        self.ypos = xyzpos.get_tilt_pos()
        self.zpos = xyzpos.get_zoom_pos()
        self.apos = abcpos.get_rotation_pos()
        self.bpos = abcpos.get_tilt_pos()

        self.feed_rate=200
        

    


    def set_dwell_time(self,time):
        self.dwell_time = time

    def get_dwell_time(self):
        return self.dwell_time

    def set_feed_rate(self,feedrate):
        self.feed_rate = feedrate

    def get_feed_rate(self):
        return self.feed_rate

    def set_travel_duration(self,seconds):
        self.travel_duration = seconds

    def get_travel_duration(self):
        return self.travel_duration


    def location_str(self):
        return "Position: x{} y{} z{} a{} b{}".format(self.xpos,self.ypos, self.zpos, self.apos, self.bpos)
    def get_feed_info(self):
        return "dwell {} f:{} td:{}".format(self.dwell_time,self.feed_rate,self.travel_duration)
    def get_waypoint_data(self, id):
        return {
            'id': id,
            'x': self.xpos,
            'y': self.ypos,
            'z': self.zpos,
            'a': self.apos,
            'b': self.bpos,
            'feed': self.feed_rate,
            'travel_duration': self.travel_duration,
            'dwell_time': self.dwell_time
        }