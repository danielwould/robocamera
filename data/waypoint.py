
class waypoint:

    dwell_time = 10
    gimbal_travel_feed_rate = 250
    crane_travel_feed_rate = 500
    travel_duration = 10
    

    def __init__(self, pos):
        self.pos = pos
        self.gimbal_travel_feed_rate=200
        self.crane_travel_feed_rate=500


    def get_position(self):
        return self.pos

    def set_dwell_time(self,time):
        self.dwell_time = time

    def get_dwell_time(self):
        return self.dwell_time

    def set_crane_travel_to_feed_rate(self,feedrate):
        self.crane_travel_feed_rate = feedrate

    def get_crane_travel_to_feed_rate(self):
        return self.crane_travel_feed_rate

    def set_gimbal_travel_to_feed_rate(self,feedrate):
        self.gimbal_travel_feed_rate = feedrate

    def get_gimbal_travel_to_feed_rate(self):
        return self.gimbal_travel_feed_rate

    def set_travel_duration(self,seconds):
        self.travel_duration = seconds

    def get_travel_duration(self):
        return self.travel_duration


    def location_str(self):
        return "Position: {}".format(self.pos.location_str())
    def get_feed_info(self):
        return "dwell {} cf:{} gf:{} td:{}".format(self.dwell_time,self.crane_travel_feed_rate,self.gimbal_travel_feed_rate,self.travel_duration)