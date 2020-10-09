# dev notes
# select waypoint for editing - modify/delete

# abort sequence
# pause/resume sequence
# step backward/forward through sequence


import pygame

import time
from data.waypoint import waypoint
from data.cranepos import cranepos
from data.gimbalpos import gimbalpos
from data.sequence import sequence
from helpers.ui import UI
from helpers.ui import TextPrint
from helpers.crane import crane
from helpers.gimbal import gimbal

MOCK = 0

gimbal_inst = gimbal("/dev/ttyACM0", gimbalpos(0, 0, 0), MOCK)
crane_inst = crane("/dev/ttyACM1", cranepos(0, 0), MOCK)

VALID_CHARS = "`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./"
SHIFT_CHARS = '~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'

GIMBAL_CONTROL = 1
CRANE_CONTROL = 0
CONTROL_TOGGLE = GIMBAL_CONTROL

FEED_RATE = 0
MOVE_TIME = 1
MOVE_TOGGLE = FEED_RATE

# x= gimble pan, y= gimble tilt, z= camera zoom, t= boom_tilt
save_position_1 = waypoint(cranepos(0, 0), gimbalpos(0, 0, 0))
save_position_2 = waypoint(cranepos(0, 0), gimbalpos(0, 0, 0))
save_position_3 = waypoint(cranepos(0, 0), gimbalpos(0, 0, 0))
save_position_4 = waypoint(cranepos(0, 0), gimbalpos(0, 0, 0))



def toggle_control(value):
    global CONTROL_TOGGLE
    print("toggle control to")
    print(value)
    CONTROL_TOGGLE = value


def toggle_move_mode(value):
    global MOVE_TOGGLE
    print("toggle move mode to")
    print(value)
    MOVE_TOGGLE = value


def value_button(screen, msg, x, y, w, h, ic, ac, value, ui_info, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(screen, ac, (x, y, w, h))

        if click[0] == 1 and action is not None:
            if ui_info.can_click():
                print("clicked button")
                action(value)
                ui_info.clicked()
    else:
        pygame.draw.rect(screen, ic, (x, y, w, h))

    small_text = pygame.font.SysFont("comicsansms", 14)
    text_surface, text_rect = UI.text_objects(msg, small_text)
    text_rect.center = ((x + int(w / 2)), (y + int(h / 2)))
    screen.blit(text_surface, text_rect)


def waypoint_button(screen, msg, x, y, w, h, ic, ac, value, item_list, ui_info, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(screen, ac, (x, y, w, h))

        if click[0] == 1 and action is not None:
            if ui_info.can_click():
                print("clicked waypoint button")
                action(value, item_list)
                ui_info.clicked()
    else:
        pygame.draw.rect(screen, ic, (x, y, w, h))

    small_text = pygame.font.SysFont("comicsansms", 14)
    text_surface, text_rect = UI.text_objects(msg, small_text)
    text_rect.center = ((x + int(w / 2)), (y + int(h / 2)))
    screen.blit(text_surface, text_rect)


def trigger_button(screen, msg, x, y, w, h, ic, ac, ui_info, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(screen, ac, (x, y, w, h))

        if click[0] == 1 and action is not None:
            if ui_info.can_click():
                print("clicked action button")
                action()
                ui_info.clicked()

    else:
        pygame.draw.rect(screen, ic, (x, y, w, h))

    small_text = pygame.font.SysFont("comicsansms", 14)
    text_surface, text_rect = UI.text_objects(msg, small_text)
    text_rect.center = ((x + int(w / 2)), (y + int(h / 2)))
    screen.blit(text_surface, text_rect)


def set_feed_rate(feedval):
    if CONTROL_TOGGLE == GIMBAL_CONTROL:
        print("updating feeddefault from {} to {}".format(
            feedval, gimbal_inst.get_feed_speed()))
        gimbal_inst.set_feed_speed(feedval)
    if CONTROL_TOGGLE == CRANE_CONTROL:
        print("updating crane feeddefault from {} to {}".format(
            feedval, crane_inst.get_feed_speed()))
        crane_inst.set_feed_speed(feedval)


def set_move_time(seconds):
    if CONTROL_TOGGLE == GIMBAL_CONTROL:
        print("updating gimbal move time from {} to {}".format(
            seconds, gimbal_inst.get_move_duration()))
        gimbal_inst.set_move_duration(seconds)
    if CONTROL_TOGGLE == CRANE_CONTROL:
        print("updating crane move time from {} to {}".format(
            seconds, crane_inst.get_move_duration()))
        crane_inst.set_move_duration(seconds)


def add_waypoint(dwell_input_text, sequence_steps):
    print("add waypoint")  # (x, y, z,focus, feed), dwell time
    wp = waypoint(crane_inst.get_current_location(),
                  gimbal_inst.get_current_location())
    wp.set_dwell_time(int(dwell_input_text))
    wp.set_gimbal_travel_to_feed_rate(gimbal_inst.get_feed_speed())
    wp.set_crane_travel_to_feed_rate(crane_inst.get_feed_speed())
    wp.set_gimbal_travel_to_duration(gimbal_inst.get_move_duration())
    wp.set_crane_travel_to_duration(crane_inst.get_move_duration())
    sequence_steps.add_waypoint(wp)


def delete_waypoint(item, sequence_steps):
    # todo allow for deleting specific waypoint item
    sequence_steps.delete_waypoint()


def start_sequence(sequence_steps):
    print("starting sequence")
    if len(sequence_steps.waypoints) > 0:
        sequence_steps.start()
        trigger_sequence_step(sequence_steps)


def trigger_sequence_step(sequence_steps):
    # TODO this needs to support move base on time
    print("sequence step triger")
    wp = sequence_steps.get_next_step()
    if MOVE_TOGGLE == FEED_RATE:
        print ("move to waypoint by feed rate")
        crane_inst.move_to_waypoint(
            wp.get_crane_position(), wp.get_crane_travel_to_feed_rate())
        gimbal_inst.move_to_waypoint(
            wp.get_gimbal_position(), wp.get_gimbal_travel_to_feed_rate())
    if MOVE_TOGGLE == MOVE_TIME:
        print ("move to waypoint by travel duration")
        crane_inst.move_to_waypoint_by_time(
            wp.get_crane_position(), wp.get_crane_travel_to_duration())
        gimbal_inst.move_to_waypoint_by_time(
            wp.get_gimbal_position(), wp.get_gimbal_travel_to_duration())





def save_point_move(savepoint):
    if MOVE_TOGGLE == FEED_RATE:
        crane_inst.move_to_position_at_rate(savepoint.get_crane_position())
        gimbal_inst.move_to_position_at_rate(savepoint.get_gimbal_position())
    if MOVE_TOGGLE == MOVE_TIME:
        crane_inst.move_to_position_in_time(savepoint.get_crane_position())
        gimbal_inst.move_to_position_in_time(savepoint.get_gimbal_position())


def save_position(savepoint):
    global save_position_1
    global save_position_2
    global save_position_3
    global save_position_4
    crane_position = crane_inst.get_current_location()
    gimbal_position = gimbal_inst.get_current_location()
    new_waypoint = waypoint(
        cranepos(crane_position.get_rotation_pos(), crane_position.get_tilt_pos()),
        gimbalpos(gimbal_position.get_rotation_pos(), gimbal_position.get_tilt_pos(), gimbal_position.get_zoom_pos()))
    if savepoint == 1:
        save_position_1 = new_waypoint
    if savepoint == 2:
        save_position_2 = new_waypoint
    if savepoint == 3:
        save_position_3 = new_waypoint
    if savepoint == 4:
        save_position_4 = new_waypoint

def reset():
    global save_position_1
    global save_position_2
    global save_position_3
    global save_position_4
    crane_inst.reset()
    gimbal_inst.reset()
    save_position_1 = waypoint(cranepos(0, 0), gimbalpos(0, 0, 0))
    save_position_2 = waypoint(cranepos(0, 0), gimbalpos(0, 0, 0))
    save_position_3 = waypoint(cranepos(0, 0), gimbalpos(0, 0, 0))
    save_position_4 = waypoint(cranepos(0, 0), gimbalpos(0, 0, 0))

def tilt_up():
    if CONTROL_TOGGLE == GIMBAL_CONTROL:
        gimbal_inst.tilt_up_small()
    if CONTROL_TOGGLE == CRANE_CONTROL:
        crane_inst.tilt_up_small()


def tilt_down():
    if CONTROL_TOGGLE == GIMBAL_CONTROL:
        gimbal_inst.tilt_down_small()
    if CONTROL_TOGGLE == CRANE_CONTROL:
        crane_inst.tilt_down_small()


def rotate_left():
    if CONTROL_TOGGLE == GIMBAL_CONTROL:
        gimbal_inst.rotate_left_small()
    if CONTROL_TOGGLE == CRANE_CONTROL:
        crane_inst.rotate_left_small()


def rotate_right():
    if CONTROL_TOGGLE == GIMBAL_CONTROL:
        gimbal_inst.rotate_right_small()
    if CONTROL_TOGGLE == CRANE_CONTROL:
        crane_inst.rotate_right_small()


def zoom_in():
    gimbal_inst.zoom_in_small()


def zoom_out():
    gimbal_inst.zoom_out_small()


def main():
    # waypoints is the list of waypoints, and their dwell times
    global save_position_1
    global save_position_2
    global save_position_3
    global save_position_4
    ui_info = UI()
    sequence_steps = sequence()
    countdown = False
    feed_input_text = '1750'
    movetime_input_text = '5'
    dwell_input_text = '10'
    # used to handle button presses registering faster than you can release
    control_last_toggled = time.time()



    pygame.init()

    # Set the width and height of the screen (width, height).
    screen = pygame.display.set_mode((800, 400))

    pygame.display.set_caption("RoboCameraman")

    # Loop until the user clicks the close button.
    done = False

    # Used to manage how fast the screen updates.
    clock = pygame.time.Clock()

    # Initialize the joysticks.
    pygame.joystick.init()

    # Get ready to print.
    text_print = TextPrint()
    waypoint_print = TextPrint()
    waypoint_print.set_location(200, 20)

    font = pygame.font.Font(None, 16)
    font_big = pygame.font.Font(None, 60)
    feed_input_colour_infeed_input_active = (0, 0, 200)
    feed_input_colour_feed_input_active = (0, 200, 0)

    dwell_input_colour_infeed_input_active = (0, 0, 200)
    dwell_input_colour_feed_input_active = (0, 200, 0)

    feed_input_colour = feed_input_colour_infeed_input_active
    dwell_input_colour = dwell_input_colour_infeed_input_active

    feed_input_active = False
    dwell_input_active = False
    feed_input = pygame.Rect(700, 268, 40, 32)
    dwell_input = pygame.Rect(500, 268, 40, 32)
    countdown_rect = pygame.Rect(300, 200, 100, 100)
    # hold_time_input = pygame.Rect(580, 128, 25, 32)

    # -------- Main Program Loop -----------
    while not done:
        if sequence_steps.sequence_running:
            if MOVE_TOGGLE == MOVE_FEED: 
                current_time = time.time()
                if current_time > sequence_steps.step_finished_at:
                    trigger_sequence_step(sequence_steps)
            if MOVE_TOGGLE == MOVE_TIME:
                current_time = time.time()
                current_gimbal_travel_duration = sequence_steps.waypoints[sequnce_steps.current_step].get_gimbal_travel_to_duration()
                current_crane_travel_duration = sequence_steps.waypoints[sequnce_steps.current_step].get_crane_travel_to_duration()
                
                if current_time > self.last_step_triggered_at+max(current_gimbal_travel_duration,current_crane_travel_duration):
                    trigger_sequnce_step(sequence_steps)

        #
        # EVENT PROCESSING STEP
        #
        # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
        # JOYBUTTONUP, JOYHATMOTION
        for event in pygame.event.get():  # User did something.
            if event.type == pygame.QUIT:  # If user clicked close.
                done = True  # Flag that we are done so we exit this loop.
            elif event.type == pygame.JOYBUTTONDOWN:
                print("Joystick button pressed.")
            elif event.type == pygame.JOYBUTTONUP:
                print("Joystick button released.")
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the user clicked on the feed_input rect.
                if feed_input.collidepoint(event.pos):
                    # Toggle the feed_input_active variable.
                    feed_input_active = not feed_input_active

                else:
                    feed_input_active = False
                if dwell_input.collidepoint(event.pos):
                    # Toggle the feed_input_active variable.
                    dwell_input_active = not dwell_input_active

                else:
                    dwell_input_active = False
                feed_input_colour = feed_input_colour_feed_input_active if feed_input_active \
                    else feed_input_colour_infeed_input_active
                dwell_input_colour = dwell_input_colour_feed_input_active if dwell_input_active \
                    else dwell_input_colour_infeed_input_active
            if event.type == pygame.KEYDOWN:
                if feed_input_active:
                    if event.key == pygame.K_RETURN:
                        print(feed_input_text)
                        feed_input_text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        feed_input_text = feed_input_text[:-1]

                    else:
                        feed_input_text += event.unicode
                if dwell_input_active:
                    if event.key == pygame.K_RETURN:
                        dwell_input_text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        dwell_input_text = dwell_input_text[:-1]
                    else:
                        dwell_input_text += event.unicode  #

        # DRAWING STEP
        #
        # First, clear the screen to white. Don't put other drawing commands
        # above this, or they will be erased with this command.
        screen.fill(UI.white)
        text_print.reset()
        waypoint_print.set_location(200, 20)

        # Get count of joysticks.
        joystick_count = pygame.joystick.get_count()

        text_print.tprint(
            screen, "Number of joysticks: {}".format(joystick_count))
        text_print.indent()
        text_print.tprint(screen, "Gimbal position")
        text_print.tprint(screen, "    {}".format(
            gimbal_inst.current_location_str()))
        text_print.tprint(screen, "Crane position")
        text_print.tprint(screen, "    {}".format(
            crane_inst.current_location_str()))
        text_print.tprint(
            screen, "Gimbal feedspeed {}".format(gimbal_inst.get_feed_speed()))
        text_print.tprint(
            screen, "Gimbal move duration {}".format(gimbal_inst.get_move_duration()))

        text_print.tprint(
            screen, "Crane feedspeed {}".format(crane_inst.get_feed_speed()))
        text_print.tprint(
            screen, "Crane move duration {}".format(crane_inst.get_move_duration()))

        text_print.tprint(screen, "Save pos Y (LB)")
        text_print.tprint(screen, "   {}".format(
            save_position_1.location_str()))
        text_print.tprint(screen, "Save pos B (RB)")
        text_print.tprint(screen, "   {}".format(
            save_position_2.location_str()))
        text_print.tprint(screen, "Save pos A (R1)")
        text_print.tprint(screen, "   {}".format(
            save_position_3.location_str()))
        text_print.tprint(screen, "Save pos X (L1)")
        text_print.tprint(screen, "   {}".format(
            save_position_4.location_str()))

        # For each joystick:
        for joystick_num in range(joystick_count):
            joystick = pygame.joystick.Joystick(joystick_num)
            joystick.init()
            axes = joystick.get_numaxes()

            for axis_num in range(axes):

                axis = joystick.get_axis(axis_num)
                if CONTROL_TOGGLE == GIMBAL_CONTROL:
                    if time.time() - gimbal_inst.last_command_sent_at > 0.2:
                        if axis_num == 0:
                            if axis >= 0.99:
                                gimbal_inst.rotate_right_small()
                            if axis == -1:
                                gimbal_inst.rotate_left_small()
                        if axis_num == 1:
                            if axis >= 0.99:
                                gimbal_inst.tilt_down_small()
                            if axis == -1:
                                gimbal_inst.tilt_up_small()
                        if axis_num == 2:
                            if axis >= 0.99:
                                gimbal_inst.rotate_right_large()
                            if axis == -1:
                                gimbal_inst.rotate_left_large()
                        if axis_num == 3:
                            if axis >= 0.99:
                                gimbal_inst.tilt_down_large()
                            if axis == -1:
                                gimbal_inst.tilt_up_large()

                if CONTROL_TOGGLE == CRANE_CONTROL:
                    if time.time() - crane_inst.last_command_sent_at > 0.2:
                        if axis_num == 0:
                            if axis >= 0.99:
                                crane_inst.rotate_right_small()
                            if axis == -1:
                                crane_inst.rotate_left_small()
                        if axis_num == 1:
                            if axis >= 0.99:
                                crane_inst.tilt_down_small()
                            if axis == -1:
                                crane_inst.tilt_up_small()
                        if axis_num == 2:
                            if axis >= 0.99:
                                crane_inst.rotate_right_large()
                            if axis == -1:
                                crane_inst.rotate_left_large()
                        if axis_num == 3:
                            if axis >= 0.99:
                                crane_inst.tilt_down_large()
                            if axis == -1:
                                crane_inst.tilt_up_large()

            text_print.unindent()

            buttons = joystick.get_numbuttons()
            # text_print.tprint(screen, "Number of buttons: {}".format(buttons))
            # text_print.indent()

            for button_num in range(buttons):
                button = joystick.get_button(button_num)
                # text_print.tprint(screen,"Button {:>2} value: {}".format(i, button))
                if button_num == 0:

                    if button == 1:
                        # save position 1 when prssing
                        save_position(1)
                if button_num == 1:
                    if button == 1:
                        save_position(2)
                if button_num == 2:
                    if button == 1:
                        save_position(3)
                if button_num == 3:
                    if button == 1:
                        save_position(4)
                if button_num == 4:
                    if button == 1:
                        save_point_move(save_position_1)
                if button_num == 5:
                    if button == 1:
                        save_point_move(save_position_2)
                if button_num == 6:
                    if button == 1:
                        save_point_move(save_position_3)
                if button_num == 7:
                    if button == 1:
                        save_point_move(save_position_4)
                if button_num == 8:
                    if button == 1:
                        # the reset button first for down and up, we only want to register on down
                        if event.type == pygame.JOYBUTTONDOWN:
                            if time.time() - control_last_toggled > 0.5:
                                if CONTROL_TOGGLE == GIMBAL_CONTROL:
                                    toggle_control(CRANE_CONTROL)
                                    control_last_toggled = time.time()
                                elif CONTROL_TOGGLE == CRANE_CONTROL:
                                    toggle_control(GIMBAL_CONTROL)
                                    control_last_toggled = time.time()

                if button_num == 9:
                    if button == 1:
                        start_sequence(sequence_steps)

            text_print.unindent()

            hats = joystick.get_numhats()

            # Hat position. All or nothing for direction, not a float like
            # get_axis(). Position is a tuple of int values (x, y).
            if time.time() - gimbal_inst.last_command_sent_at > 0.2:
                for hat_num in range(hats):
                    hat = joystick.get_hat(hat_num)
                    # text_print.tprint(screen, "Hat {} value: {}".format(i, str(hat)))
                    # print "Hat {} value: {}".format(i, str(hat))
                    if hat[0] == 1:
                        gimbal_inst.zoom_in_large()
                    if hat[0] == -1:
                        gimbal_inst.zoom_out_large()
                    if hat[1] == -1:
                        gimbal_inst.zoom_in_small()
                    if hat[1] == 1:
                        gimbal_inst.zoom_out_small()

            text_print.unindent()

            text_print.unindent()

        pygame.draw.rect(screen, UI.black, (690, 5, 105, 370), 2)
        if MOVE_TOGGLE == FEED_RATE:
            UI.render_text(screen, "Feed Rate:", 740, 12)
            value_button(screen, "100", 700, 28, 90, 50, UI.yellow,
                         UI.bright_green, 100, ui_info, set_feed_rate)
            value_button(screen, "500", 700, 88, 90, 50, UI.yellow,
                         UI.bright_green, 500, ui_info, set_feed_rate)
            value_button(screen, "1000", 700, 148, 90, 50, UI.yellow,
                         UI.bright_green, 1000, ui_info, set_feed_rate)
            value_button(screen, "2000", 700, 208, 90, 50, UI.yellow,
                         UI.bright_green, 2000, ui_info, set_feed_rate)
            if feed_input_text != '':
                value_button(screen, "custom", 700, 310, 90, 50, UI.blue, UI.bright_blue,
                             int(feed_input_text), ui_info, set_feed_rate)
        if MOVE_TOGGLE == MOVE_TIME:
            UI.render_text(screen, "move time(sec):", 740, 12)
            value_button(screen, "2", 700, 28, 90, 50, UI.yellow,
                         UI.bright_green, 2, ui_info, set_move_time)
            value_button(screen, "5", 700, 88, 90, 50, UI.yellow,
                         UI.bright_green, 5, ui_info, set_move_time)
            value_button(screen, "10", 700, 148, 90, 50, UI.yellow,
                         UI.bright_green, 10, ui_info, set_move_time)
            value_button(screen, "20", 700, 208, 90, 50, UI.yellow,
                         UI.bright_green, 20, ui_info, set_move_time)
            if movetime_input_text != '':
                value_button(screen, "custom", 700, 310, 90, 50, UI.blue, UI.bright_blue,
                             int(movetime_input_text), ui_info, set_move_time)
        waypoint_button(screen, "Add Way-point", 580, 28, 90, 50,
                        UI.yellow, UI.bright_green, dwell_input_text, sequence_steps, ui_info, add_waypoint)
        waypoint_button(screen, "Delete Way-point", 580, 88, 90, 50,
                        UI.yellow, UI.bright_green, 0, sequence_steps, ui_info, delete_waypoint)

        if CONTROL_TOGGLE == GIMBAL_CONTROL:
            value_button(screen, "Gimbal", 200, 248, 90, 50, UI.yellow,
                         UI.bright_green, GIMBAL_CONTROL, ui_info, toggle_control)
            value_button(screen, "Crane", 295, 248, 90, 50, UI.grey,
                         UI.bright_green, CRANE_CONTROL, ui_info, toggle_control)
        if CONTROL_TOGGLE == CRANE_CONTROL:
            value_button(screen, "Gimbal", 200, 248, 90, 50, UI.grey,
                         UI.bright_green, GIMBAL_CONTROL, ui_info, toggle_control)
            value_button(screen, "Crane)", 295, 248, 90, 50, UI.yellow,
                         UI.bright_green, CRANE_CONTROL, ui_info, toggle_control)

        if MOVE_TOGGLE == FEED_RATE:
            value_button(screen, "Move mm/min", 200, 308, 90, 50, UI.yellow,
                         UI.bright_green, FEED_RATE, ui_info, toggle_move_mode)
            value_button(screen, "move sec", 295, 308, 90, 50, UI.grey,
                         UI.bright_green, MOVE_TIME, ui_info, toggle_move_mode)
        if MOVE_TOGGLE == MOVE_TIME:
            value_button(screen, "Move mm/min", 200, 308, 90, 50, UI.grey,
                         UI.bright_green, FEED_RATE, ui_info, toggle_move_mode)
            value_button(screen, "move sec)", 295, 308, 90, 50, UI.yellow,
                         UI.bright_green, MOVE_TIME, ui_info, toggle_move_mode)

        # controller buttons
        # screen, msg, x, y, w, h, ic, ac, ui_info, action=None):
        trigger_button(screen, "U", 60, 300, 30, 30,
                       UI.yellow, UI.bright_green, ui_info, tilt_up)
        trigger_button(screen, "D", 60, 350, 30, 30,
                       UI.yellow, UI.bright_green, ui_info, tilt_down)
        trigger_button(screen, "L", 10, 325, 30, 30,
                       UI.yellow, UI.bright_green, ui_info, rotate_left)
        trigger_button(screen, "R", 110, 325, 30, 30,
                       UI.yellow, UI.bright_green, ui_info, rotate_right)
        trigger_button(screen, "Zi", 150, 300, 30, 30,
                       UI.yellow, UI.bright_green, ui_info, zoom_in)
        trigger_button(screen, "Zo", 150, 350, 30, 30,
                       UI.yellow, UI.bright_green, ui_info, zoom_out)
        #onscreen save position
        value_button(screen, "Y", 10, 260, 30, 30,
                       UI.yellow, UI.bright_green, 1, ui_info, save_position)
        value_button(screen, "B", 40, 260, 30, 30,
                       UI.yellow, UI.bright_green, 2, ui_info, save_position)
        value_button(screen, "A", 80, 260, 30, 30,
                       UI.yellow, UI.bright_green, 3, ui_info, save_position)
        value_button(screen, "X", 110, 260, 30, 30,
                       UI.yellow, UI.bright_green, 4, ui_info, save_position)

        # reset button
        trigger_button(screen, "RESET", 650, 340, 30, 30,
                       UI.yellow, UI.bright_green, ui_info, reset)

        pygame.draw.rect(screen, UI.black, (190, 5, 490, 370), 2)
        wpitem = 0
        for wp in sequence_steps.waypoints:
            # Render the current text.
            waypoint_print.tprint(screen, wp.location_str())
            waypoint_print.tprint(screen, wp.get_feed_info())
            wpitem = wpitem + 1

        # Render the current text.
        txt_surface = None
        if MOVE_TOGGLE == FEED_RATE:
            txt_surface = font.render(feed_input_text, True, feed_input_colour)
        if MOVE_TOGGLE == MOVE_TIME:
            txt_surface = font.render(movetime_input_text, True, feed_input_colour)
        # Resize the box if the text is too long.

        width = min(100, txt_surface.get_width() + 10)
        feed_input.w = width
        # Blit the text.
        screen.blit(txt_surface, (feed_input.x + 5, feed_input.y + 5))
        # Blit the feed_input rect.
        pygame.draw.rect(screen, feed_input_colour, feed_input, 2)

        UI.render_text(screen, "Dwell time at waypoint (s):", 580, 235)

        # Render the current text.
        dwell_txt_surface = font.render(
            dwell_input_text, True, dwell_input_colour)
        # Resize the box if the text is too long.
        dwell_width = min(100, dwell_txt_surface.get_width() + 10)
        dwell_input.w = dwell_width
        # Blit the text.
        screen.blit(dwell_txt_surface, (dwell_input.x + 5, dwell_input.y + 5))
        # Blit the feed_input rect.
        pygame.draw.rect(screen, dwell_input_colour, dwell_input, 2)

        if countdown:
            pygame.draw.rect(screen, (255, 0, 0), countdown_rect, 2)
            timeleft = sequence_steps.step_finished_at - time.time()
            UI.render_text(screen, "Waypoint :{}".format(sequence_steps.current_step), 250, 200)
            txt_countdown = font_big.render(
                "{0:3.2}".format(timeleft), True, (255, 0, 0))
            screen.blit(txt_countdown,
                        (countdown_rect.x + 5, countdown_rect.y + 5))

        #
        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT
        #

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 20 frames per second.
        clock.tick(20)

    # Close the window and quit.
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()


if __name__ == "__main__":
    main()
