
try:
    import numpy as np
    import pygame
    from pygame.locals import *
    import sys
    import os
    import getopt
    import engine
    from socket import *
except (ImportError, err):
    print("couldn't load module. %s" % (err))
    sys.exit(2)

# general application states
STATE_MENU = 0
STATE_GAME = 1
STATE_SETTINGS = 2
STATE_SCORES = 3
STATE_QUIT = 4

class Menu_Item:
    # holder class for menu display
    def __init__(self, message, index, state, font, color, selected_color):
        # text to be displayed
        self.message = message
        # index in list
        self.index = index
        # state that selecting this menu option will trigger. see general app states above.
        self.state = state

        # renders for selected/deselected
        self.not_selected_render = font.render(message, True, color)
        self.selected_render = font.render(message, True, selected_color)

    def get_message(self):
        return self.message

    def get_index(self):
        return self.index

    def get_state(self):
        return self.state

    def get_selected(self):
        return self.selected_render

    def get_not_selected(self):
        return self.not_selected_render

def main():
    # init state
    STATE = STATE_MENU

    # setup pygame and load menu
    pygame.init()

    # screen to be passed to engine
    screenx = 960
    screeny = 540
    screen = pygame.display.set_mode((screenx,screeny))

    # font setup
    MENU_FONT_SIZE = 24
    text_color = (255,255,255)
    selected_color = (0,255,0)
    font = pygame.font.SysFont(None, MENU_FONT_SIZE)

    # create menu
    menu_layer = pygame.Surface((screenx,screeny), flags=SRCALPHA)
    menu_layer.fill((0,0,0))

    item_new_game = Menu_Item("New Game", 0, STATE_GAME, font, text_color, selected_color)
    item_settings = Menu_Item("Settings", 1, STATE_SETTINGS, font, text_color, selected_color)
    item_quit = Menu_Item("Quit", 2, STATE_QUIT, font, text_color, selected_color)


    menu_items = [item_new_game, item_settings, item_quit]

    selected_index = 0
    n_item = 0
    for item in menu_items:
        if n_item == selected_index:
            menu_layer.blit(item.get_selected(), (10, n_item*30 + 10))
        else:
            menu_layer.blit(item.get_not_selected(), (10, n_item*30 + 10))
        n_item += 1

    screen.blit(menu_layer, (0,0))

    pygame.display.flip()

    # display update flag
    update_display = True

    # main loop
    while True:
        if STATE == STATE_MENU:
            # menu inputs
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    update_display = True
                    if event.key == K_UP:
                        selected_index = (selected_index - 1)%len(menu_items)
                    if event.key == K_DOWN:
                        selected_index = (selected_index + 1)%len(menu_items)
                    if event.key == K_RETURN:
                        STATE = menu_items[selected_index].get_state()

                if event.type == QUIT:
                    return

            # update display if needed
            if update_display:
                menu_layer.fill((0,0,0))
                n_item = 0
                for item in menu_items:
                    if n_item == selected_index:
                        menu_layer.blit(item.get_selected(), (10, n_item*30 + 10))
                    else:
                        menu_layer.blit(item.get_not_selected(), (10, n_item*30 + 10))
                    n_item += 1
                screen.blit(menu_layer, (0,0))
                pygame.display.flip()

            # reset flag
            update_display = False

        elif STATE == STATE_GAME:
            # run game & revert to menu state afterwards
            engine.main(screen, screenx, screeny)

            # reset menu variables
            STATE = STATE_MENU
            update_display = True

        elif STATE == STATE_SETTINGS:
            print("TODO: settings")
            STATE = STATE_MENU

        elif STATE == STATE_QUIT:
            return


if __name__ == "__main__":
    main()
