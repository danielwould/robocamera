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
            time.sleep(1)
            #self.gimbal_inst.status()
            #self.crane_inst.status()
            self.parent.gimbal_pos_text['text']="GimbalPos:{}".format(self.gimbal_inst.current_location_str())
            self.parent.crane_pos_text['text']="CranePos:{}".format(self.crane_inst.current_location_str())