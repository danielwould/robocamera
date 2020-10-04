class gimbalpos:
    def __init__(self, rotation_pos, tilt_pos, zoom_pos):
        self.rotation_pos = rotation_pos
        self.tilt_pos = tilt_pos
        self.zoom_pos = zoom_pos

    def reset(self):
        self.tilt_pos = 0
        self.rotation_pos = 0
        self.zoom_pos = 0

    def current_location_str(self):
        return "rot:{},tilt:{},zoom:{}".format(self.rotation_pos, self.tilt_pos, self.zoom_pos)

    def get_rotation_pos(self):
        return self.rotation_pos

    def get_tilt_pos(self):
        return self.tilt_pos

    def get_zoom_pos(self):
        return self.zoom_pos

    def increment_tilt(self, amount):
        self.tilt_pos = self.tilt_pos + amount

    def decrement_tilt(self, amount):
        self.tilt_pos = self.tilt_pos - amount

    def increment_rotation(self, amount):
        self.rotation_pos = self.rotation_pos + amount

    def decrement_rotation(self, amount):
        self.rotation_pos = self.rotation_pos - amount

    def increment_zoom(self, amount):
        self.zoom_pos = self.zoom_pos + amount

    def decrement_zoom(self, amount):
        self.zoom_pos = self.zoom_pos - amount
