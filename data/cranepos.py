class cranepos:
    def __init__(self, rotation_pos, tilt_pos):
        self.tilt_pos = tilt_pos
        self.rotation_pos = rotation_pos

    def reset(self):
        self.tilt_pos = 0
        self.rotation_pos = 0

    def current_location_str(self):
        return "rot:{},tilt:{}".format(self.rotation_pos, self.tilt_pos)

    def set_location(self, position):
        self.rotation_pos = position.get_rotation_pos()
        self.tilt_pos = position.get_tilt_pos()

    def get_rotation_pos(self):
        return self.rotation_pos

    def get_tilt_pos(self):
        return self.tilt_pos

    def increment_tilt(self, amount):
        self.tilt_pos = self.tilt_pos + amount

    def decrement_tilt(self, amount):
        self.tilt_pos = self.tilt_pos - amount

    def increment_rotation(self, amount):
        self.rotation_pos = self.rotation_pos + amount

    def decrement_rotation(self, amount):
        self.rotation_pos = self.rotation_pos - amount
