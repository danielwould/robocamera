
class waypoint:

    dwell_time = 10
    gimbal_travel_feed_rate = 250
    crane_travel_feed_rate = 500

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

    def location_str(self):
        return "gimbal {} crane {}".format(self.gimbalpos.current_location_str(),self.cranepos.current_location_str())
    def get_feed_info(self):
        return "dwell {} cf:{} gf: {}".format(self.dwell_time,self.crane_travel_feed_rate,self.gimbal_travel_feed_rate)