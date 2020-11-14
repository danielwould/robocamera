class location:
    def __init__(self, rotation_pos, tilt_pos, zoom_pos):
        self.rotation_pos = rotation_pos
        self.tilt_pos = tilt_pos
        self.zoom_pos = zoom_pos

    def get_rotation_pos(self):
        return self.rotation_pos

    def get_tilt_pos(self):
        return self.tilt_pos

    def get_zoom_pos(self):
        return self.zoom_pos

   
