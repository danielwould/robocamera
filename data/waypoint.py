
class waypoint:

    dwell_time = 10
    gimbal_travel_feed_rate = 250
    crane_travel_feed_rate = 500
    gimbal_travel_duration = 10
    crane_travel_duration = 10

    def __init__(self, cranepos, gimbalpos):
        self.cranepos = cranepos
        self.gimbalpos = gimbalpos
        self.gimbal_travel_feed_rate=200
        self.crane_travel_feed_rate=500

    def get_crane_position(self):
        return self.cranepos

    def get_gimbal_position(self):
        return self.gimbalpos

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

    def set_crane_travel_to_duration(self,seconds):
        self.crane_travel_duration = seconds

    def get_crane_travel_to_duration(self):
        return self.crane_travel_duration

    def set_gimbal_travel_to_duration(self,seconds):
        self.gimbal_travel_duration = seconds

    def get_gimbal_travel_to_duration(self):
        return self.gimbal_travel_duration

    def location_str(self):
        return "gimbal {} crane {}".format(self.gimbalpos.location_str(),self.cranepos.location_str())
    def get_feed_info(self):
        return "dwell {} cf:{} cd:{} gf:{} gd:{}".format(self.dwell_time,self.crane_travel_feed_rate,self.crane_travel_duration,self.gimbal_travel_feed_rate,self.gimbal_travel_duration)