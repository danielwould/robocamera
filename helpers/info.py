import time
import threading
import sys
import traceback

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
        loopcount =0
        while not self.done:
            try:
                loopcount=loopcount+1
                time.sleep(0.3)
                self.parent.status_text['text']="State:{}, lastUpdated:{}".format(self.parent.controller.get_grbl_status(), self.parent.controller.get_lastUpdateTime())
                self.parent.pos_text['text']="Pos:\n{}".format(self.parent.controller.position_str())
                self.parent.transbuffer_text['text']="GcodeLines buff/tot {}/{} chars buff/tot {}/{}".format(self.parent.controller.bufferedGcodeCount(),self.parent.controller.all_time_gcode_lines,self.parent.controller.bufferredCharCount(),self.parent.controller.all_time_character_count)
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
                if self.parent.TRACKING == True:
                    self.parent.trackingToggle["bg"]="#ffcc33"
                    self.parent.trackingToggle["fg"]="#333333"
                else:
                    self.parent.trackingToggle["fg"]="#ffcc33"
                    self.parent.trackingToggle["bg"]="#333333"
                if (self.parent.trackingId == 1):
                    self.parent.trackingToggle1["bg"]="#ffcc33"
                    self.parent.trackingToggle1["fg"]="#333333"
                    self.parent.trackingToggle2["fg"]="#ffcc33"
                    self.parent.trackingToggle2["bg"]="#333333"
                    self.parent.trackingToggle3["fg"]="#ffcc33"
                    self.parent.trackingToggle3["bg"]="#333333"
                elif (self.parent.trackingId == 2):
                    self.parent.trackingToggle1["fg"]="#ffcc33"
                    self.parent.trackingToggle1["bg"]="#333333"
                    self.parent.trackingToggle2["bg"]="#ffcc33"
                    self.parent.trackingToggle2["fg"]="#333333"
                    self.parent.trackingToggle3["fg"]="#ffcc33"
                    self.parent.trackingToggle3["bg"]="#333333"
                elif (self.parent.trackingId == 3):
                    self.parent.trackingToggle1["fg"]="#ffcc33"
                    self.parent.trackingToggle1["bg"]="#333333"
                    self.parent.trackingToggle2["fg"]="#ffcc33"
                    self.parent.trackingToggle2["bg"]="#333333"
                    self.parent.trackingToggle3["bg"]="#ffcc33"
                    self.parent.trackingToggle3["fg"]="#333333"
                if self.parent.TRACKING_RENDER == True:
                    self.parent.trackingRenderToggle["bg"]="#ffcc33"
                    self.parent.trackingRenderToggle["fg"]="#333333"
                else:
                    self.parent.trackingRenderToggle["fg"]="#ffcc33"
                    self.parent.trackingRenderToggle["bg"]="#333333"
                if loopcount ==10:
                    if self.parent.first_move==True:
                        #once we've moved once then start saving position
                        #every 3 seconds save position information to a file
                        self.parent.save_state_to_file()
                    loopcount=0

            except Exception as e:
                print("Unexpected error in ui thread:", e)
                time.sleep(1)