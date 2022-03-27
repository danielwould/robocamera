import time
class sequence:
    waypoints = []
    sequence_running = False
    sequnce_started_at = None
    current_step = 0
    last_step_triggered_at = None
    step_finished_at = time.time()

    def __init__(self):
        print ("initalised sequence")

    def add_waypoint(self,wp):
        
        self.waypoints.append(wp)

    def update_waypoint(self, index, waypoint):
        self.waypoints[index]=waypoint
        
    def delete_waypoint(self, index=-1):
        print ("delete waypoint")
        if (index==-1):
            if (len(self.waypoints) > 0):
                self.waypoints.pop()
        else:
            del self.waypoints[index]

    def move_waypoint_up(self,item_index):
        if item_index!=0:
            move_item = self.waypoints.pop(item_index)
            self.waypoints.insert((item_index-1),move_item)
    
    def move_waypoint_down(self,item_index):
        if item_index!=len(self.waypoints)-1:
            move_item = self.waypoints.pop(item_index)
            self.waypoints.insert((item_index+1),move_item)


    def start(self):
        print ("starting seuqence")
        self.sequence_running=True
        self.sequnce_started_at= time.time()

    def get_step(self, index):
        return self.waypoints[index]

    def get_next_step(self):
        print ("returning step {} of {}".format(self.current_step+1,len(self.waypoints))) 
        waypoint = self.waypoints[self.current_step]
        self.current_step=self.current_step+1
        if self.current_step==len(self.waypoints):
            self.sequence_running=False
            self.current_step=0
        self.last_step_triggered_at=time.time()
        return waypoint
