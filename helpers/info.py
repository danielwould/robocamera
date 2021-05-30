import time
import threading

class info():
    def __init__(self, parent):
        self.parent = parent
        self.done = False
        self.thread = threading.Thread(target=self.main)
        self.thread.start()

    def stop(self):
        self.done=True

    def main(self):
        # Loop until the user clicks the close button.
        while not self.done:
            try:
                time.sleep(0.3)
                self.parent.pos_text['text']="GimbalPos:\n{}".format(self.parent.controller.position_str())
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