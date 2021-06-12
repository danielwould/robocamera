import pygame
import threading
import time

class Joystick():

    deadzone = 0.05
    joystick_moving = False
    
    
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
        
        control_last_toggled = time.time()
        last_command_sent_at = time.time()
        # Loop until the user clicks the close button.
        
        # Initialize the joysticks.

        pygame.init()
        pygame.joystick.init()
        # -------- Main Program Loop -----------
        while not self.done:
            
            #
            # EVENT PROCESSING STEP
            #
            # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
            # JOYBUTTONUP, JOYHATMOTION
 
            # Get count of joysticks.
            joystick_count = pygame.joystick.get_count()
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    print ("Joystick button pressed")

            # For each joystick:
            for joystick_num in range(joystick_count):
                joystick = pygame.joystick.Joystick(joystick_num)
                joystick.init()
                axes = joystick.get_numaxes()
                xjog=0
                yjog=0
                ajog=0
                bjog=0
                for axis_num in range(axes):

                    axis = joystick.get_axis(axis_num)
                                        
                    if (axis >= self.deadzone ) | (axis <= -self.deadzone):
                        if axis_num == 0:
                            #self.gimbal_inst.rotate_jog(axis)
                            xjog=axis
                        if axis_num == 1:
                            #self.gimbal_inst.tilt_jog(axis)
                            yjog=axis
                        if axis_num == 2:
                            #self.crane_inst.rotate_jog(axis)
                            ajog=axis
                        if axis_num == 3:
                            #self.crane_inst.tilt_jog(axis)
                            bjog=axis
                    
                #combined jog
                #
                if ( (xjog != 0)| (yjog != 0) | (ajog!= 0) | (bjog != 0) ):
                    self.joystick_moving=True
                    self.parent.tracker.set_static_tracking(False)
                    self.control_last_toggled = time.time()
                    if ((self.parent.TRACKING == True) & ((xjog==0) & (yjog==0)) ):
                        #if we're tracking allow tracking input to joystick jog
                        (trackingxjog, trackingyjog) = self.parent.tracker.get_jogmultipliers()
                        print("adjusting jog with tracking deltas x{} y{}".format(trackingxjog,trackingyjog))
                        self.parent.controller.jog(trackingxjog,trackingyjog,ajog,bjog)   
                    else: 
                        self.parent.controller.jog(xjog,yjog,ajog,bjog)             
                else:
                    if (self.joystick_moving ==True):
                        self.parent.controller.jog_cancel()
                        self.joystick_moving=False

                if (time.time()-control_last_toggled > 0.5):
                    self.parent.tracker.set_static_tracking(True)
 
                buttons = joystick.get_numbuttons()
                if time.time() - last_command_sent_at > 0.2:
                            
                    for button_num in range(buttons):
                        button = joystick.get_button(button_num)
                        if button_num == 0:

                            if button == 1:
                                # save position 1 when prssing
                                self.parent.save_position(1)
                        if button_num == 1:
                            if button == 1:
                                self.parent.save_position(2)
                        if button_num == 2:
                            if button == 1:
                                self.parent.save_position(3)
                        if button_num == 3:
                            if button == 1:
                                self.parent.save_position(4)
                        if button_num == 4:
                            if button == 1:
                                self.parent.save_point_move(self.parent.save_position_1)
                                last_command_sent_at=time.time()                        
                        if button_num == 5:
                            if button == 1:
                                self.parent.save_point_move(self.parent.save_position_2)
                                last_command_sent_at=time.time()
                        if button_num == 6:
                            if button == 1:
                                self.parent.save_point_move(self.parent.save_position_3)
                                last_command_sent_at=time.time()
                        if button_num == 7:
                            if button == 1:
                                self.parent.save_point_move(self.parent.save_position_4)
                                last_command_sent_at=time.time()
                        if button_num == 8:
                            if button == 1:
                                # the reset button first for down and up, we only want to register on down
                                if event.type == pygame.JOYBUTTONDOWN:
                                    if time.time() - control_last_toggled > 0.5:
                                        if self.parent.MOVE_TOGGLE == self.parent.MOVE_TIME:
                                            self.parent.toggle_move_mode(self.parent.FEED_RATE)
                                            control_last_toggled = time.time()
                                        elif self.parent.MOVE_TOGGLE == self.parent.FEED_RATE:
                                            self.parent.toggle_move_mode(self.parent.MOVE_TIME)
                                            control_last_toggled = time.time()

                        if button_num == 9:
                            if button == 1:
                                if (time.time() - last_command_sent_at) >0.5:
                                    self.parent.trigger_whole_sequence()
                                    last_command_sent_at=time.time()

                hats = joystick.get_numhats()

                # Hat position. All or nothing for direction, not a float like
                # get_axis(). Position is a tuple of int values (x, y).
                if time.time() - self.gimbal_inst.last_command_sent_at > 0.2:
                    for hat_num in range(hats):
                        hat = joystick.get_hat(hat_num)
                        # text_print.tprint(screen, "Hat {} value: {}".format(i, str(hat)))
                        # print "Hat {} value: {}".format(i, str(hat))
                        if hat[0] == 1:
                            self.gimbal_inst.zoom_in_large()
                        if hat[0] == -1:
                            self.gimbal_inst.zoom_out_large()
                        if hat[1] == -1:
                            self.gimbal_inst.zoom_in_small()
                        if hat[1] == 1:
                            self.gimbal_inst.zoom_out_small()


        # stop handling joysticks

        pygame.joystick.quit()
        pygame.quit()
