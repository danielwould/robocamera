import time
import threading

class info():
    def __init__(self, parent, gimbal,crane):
        self.parent = parent
        self.gimbal_inst = gimbal
        self.crane_inst = crane
        self.done = False
        self.thread = threading.Thread(target=self.main)
        self.thread.start()

    def stop(self):
        self.done=True

    def main(self):
        # Loop until the user clicks the close button.
        while not self.done:
            time.sleep(0.5)
            #self.gimbal_inst.status()
            #self.crane_inst.status()
            self.parent.gimbal_pos_text['text']="GimbalPos:\n{}".format(self.gimbal_inst.current_location_str())
            self.parent.crane_pos_text['text']="CranePos:\n{}".format(self.crane_inst.current_location_str())
            if self.parent.CONTROL_TOGGLE == self.parent.GIMBAL_CONTROL:
                self.parent.gimbalToggle["bg"]="green"
                self.parent.craneToggle["bg"]="grey"
            if self.parent.CONTROL_TOGGLE == self.parent.CRANE_CONTROL:
                self.parent.gimbalToggle["bg"]="grey"
                self.parent.craneToggle["bg"]="green"
            if self.parent.MOVE_TOGGLE == self.parent.MOVE_TIME:
                self.parent.moveFeedToggle["bg"]="grey"
                self.parent.moveTimeToggle["bg"]="green"
            if self.parent.MOVE_TOGGLE == self.parent.FEED_RATE:
                self.parent.moveFeedToggle["bg"]="green"
                self.parent.moveTimeToggle["bg"]="grey"
            