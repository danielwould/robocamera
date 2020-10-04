import time
import pygame



class UI:
    # Define some feed_input_colours.
    black = (0, 0, 0)
    white = (255, 255, 255)
    red = (200, 0, 0)
    green = (0, 200, 0)
    blue = (0, 0, 200)
    yellow = (255, 204,51) #makergeek yellow
    grey = (51,51,51) # makergeek grey
    bright_red = (255, 0, 0)
    bright_green = (0, 255, 0)
    bright_blue = (0, 0, 255)
    def __init__(self):
        self.last_click_time = time.time()
        
    def can_click(self):
        if (time.time()-self.last_click_time > 0.5):
            return True
        else:
            return False

    def clicked(self):
        self.last_click_time=time.time()

    @staticmethod
    def render_text(screen, msg, x, y):
        smallText = pygame.font.SysFont("comicsansms", 14)
        textSurf, textRect = UI.text_objects(msg, smallText)
        textRect.center = ((x), (y))
        screen.blit(textSurf, textRect)

    @staticmethod
    def text_objects(text, font):
        textSurface = font.render(text, True, UI.black)
        return textSurface, textSurface.get_rect()

# This is a simple class that will help us print to the screen.
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint(object):
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 14)

    def tprint(self, screen, textString):
        textBitmap = self.font.render(textString, True, UI.black)
        screen.blit(textBitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def set_location(self, x, y):
        self.x = x
        self.y = y

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10