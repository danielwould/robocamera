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
        try:
            while not self.done:
                time.sleep(0.2)
                #self.gimbal_inst.status()
                #self.crane_inst.status()
                self.parent.gimbal_pos_text['text']="GimbalPos:\n{}".format(self.gimbal_inst.current_location_str())
                self.parent.crane_pos_text['text']="CranePos:\n{}".format(self.crane_inst.current_location_str())
                if self.parent.CONTROL_TOGGLE == self.parent.GIMBAL_CONTROL:
                    self.parent.gimbalToggle["bg"]="#ffcc33"
                    self.parent.gimbalToggle["fg"]="#333333"
                    self.parent.craneToggle["bg"]="#333333"
                    self.parent.craneToggle["fg"]="#ffcc33"
                if self.parent.CONTROL_TOGGLE == self.parent.CRANE_CONTROL:
                    self.parent.gimbalToggle["bg"]="#333333"
                    self.parent.gimbalToggle["fg"]="#ffcc33"
                    self.parent.craneToggle["bg"]="#ffcc33"
                    self.parent.craneToggle["fg"]="#333333"
                if self.parent.MOVE_TOGGLE == self.parent.MOVE_TIME:
                    self.parent.moveFeedToggle["bg"]="#333333"
                    self.parent.moveTimeToggle["bg"]="#ffcc33"
                    self.parent.moveFeedToggle["fg"]="#ffcc33"
                    self.parent.moveTimeToggle["fg"]="#333333"
                if self.parent.MOVE_TOGGLE == self.parent.FEED_RATE:
                    self.parent.moveFeedToggle["bg"]="#ffcc33"
                    self.parent.moveTimeToggle["bg"]="#333333"
                    self.parent.moveFeedToggle["fg"]="#333333"
                    self.parent.moveTimeToggle["fg"]="#ffcc33"
        except:
            print("Error in ui thread")
            time.sleep(1)