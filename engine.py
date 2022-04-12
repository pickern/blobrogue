# GENERAL TODO:
# make engine class to pass things around more easily
#   - decide on system for printing messages to log from various places. maybe return strings? or access engine from subclasses?
# systems and GUI elements for:
#   - items/inventory/abilities
#   - player stats/progression/xp
# floor/game design and win condition
# score
# misc items & optimizations noted elsewhere

try:
    import numpy as np
    import pygame
    from pygame.locals import *
    import mapgen
    import fov
    import entity
    import sys
    import os
    import classes
    import getopt
    import floor
    import ai
    from socket import *
except (ImportError, err):
    print("couldn't load module. %s" % (err))
    sys.exit(2)

# Terrain constants
MAP_WALL = 0
MAP_FLOOR = 1
MAP_DOOR = 2
MAP_HALL = 3
MAP_UP_STAIR = 4
MAP_DOWN_STAIR = 5

# FOV constants
FOV_UNSEEN = 0 # hidden tiles
FOV_VISIBLE = 1 # visible tiles
FOV_REVEALED = 2 # tiles that have been seen but not in current FOV

ZOOM = 4

# Sprite constants
PLAYER_SPRITE_INDEX = 0
RAT_SPRITE_INDEX = 3
BLOB_SPRITE_INDEX = 1
MUSCLE_BLOB_SPRITE_INDEX = 4
LEG_BLOB_SPRITE_INDEX = 5
DECONSTITUTED_SPRITE_INDEX = 6

# Constant/utitlity tiles
REVEALED_TILE = pygame.Surface((32,32), flags=SRCALPHA)
BORDER_TILE = pygame.Surface((32,32), flags=SRCALPHA)
REVEALED_TILE.fill((0,0,0,180))
BORDER_TILE.fill((100,100,100))

# hold list of all messages displayed
MESSAGE_FONT_SIZE = 12
MESSAGE_LOG = []

# game states
STATE_PLAYER_TURN = 0
STATE_MONSTER_TURN = 1
STATE_DEAD = 2

def load_png(name):
    # load image and return object
    fullname = os.path.join(name)
    try:
        image = pygame.image.load(fullname)
        if image.get_alpha() is None:
            image = image.convert()
        else:
            image = image.convert_alpha()
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit
    return image, image.get_rect()

def load_sprite_sheet(name, spritex, spritey):
    # name - name of png file containing sprite sheet
    # spritex/spritey - x/y dimension of sprites
    temp_sheet, temp_rect = load_png(name)
    sheet_x = temp_sheet.get_width()
    sheet_y = temp_sheet.get_height()
    sprite_array = []
    i = 0
    while i*spritex < sheet_x:
        sprite_array.append(pygame.Surface.subsurface(temp_sheet,(i*32,0,spritex,spritey)))
        i += 1

    return sprite_array

def blit_map_vis(background_layer, map, tiles, wall_tiles, vis_map, x_offset=0, y_offset=0):
    # blits map tiles to background
    x = 0
    y = 0

    background_layer.fill((0,0,0,255))
    tempmap = map.get_map()
    wall_map = map.get_masked_map()
    revealed_map = map.get_revealed_map()
    for row in tempmap:
        y = 0
        for col in row:
            # grey border
            if x == 0 or y == 0 or x == tempmap.shape[0] - 1 or y == tempmap.shape[1] - 1:
                background_layer.blit(BORDER_TILE, (x*32, y*32))
            elif vis_map[x][y] == 1:
                # draw tile normally if visible
                if col == MAP_FLOOR or col == MAP_HALL:
                    background_layer.blit(tiles[2], (x*32,y*32))
                elif col == MAP_UP_STAIR:
                    background_layer.blit(tiles[4], (x*32, y*32))
                elif col == MAP_DOWN_STAIR:
                    background_layer.blit(tiles[3], (x*32, y*32))
                elif col == MAP_WALL:
                    # handle specific wall tiles
                    background_layer.blit(wall_tiles[wall_map[x][y]], (x*32, y*32))
            elif revealed_map[x][y] == 1:
                # if not visible but revealed, draw shaded rectangle over tile
                if col == MAP_FLOOR or col == MAP_HALL:
                    background_layer.blit(tiles[2], (x*32,y*32))
                elif col == MAP_UP_STAIR:
                    background_layer.blit(tiles[4], (x*32, y*32))
                elif col == MAP_DOWN_STAIR:
                    background_layer.blit(tiles[3], (x*32, y*32))
                elif col == MAP_WALL:
                    # handle specific wall tiles
                    background_layer.blit(wall_tiles[wall_map[x][y]], (x*32, y*32))
                # apply shading to non-visible revealed tiles
                background_layer.blit(REVEALED_TILE, (x*32, y*32))

            y += 1
            # end for
        x += 1
        # end for

def blit_entities(entity_layer, player, floor, vis_map, sprites, x_offset=0, y_offset=0):
    # blits entities (player, monsters, items, etc) to entity layer

    # transparent fill
    entity_layer.fill((0,0,0,0))

    entity_list = floor.get_entities()

    # blit other entities
    # TODO: blit living monsters last to prevent incorrect overlaps
    for ent in entity_list:
        x = ent.get_pos()[0]
        y = ent.get_pos()[1]
        if vis_map[x][y] == 1:
            if ent.is_visible() == False:
                print_log("{name} comes into view".format(name = ent.get_name()), font, text_color)
                ent.set_visible(True)
            entity_layer.blit(sprites[ent.get_sprite_index()], (x*32,y*32))
        else:
            ent.set_visible(False)

    # blit player last
    x = player.get_pos()[0]*32
    y = player.get_pos()[1]*32
    entity_layer.blit(sprites[player.get_sprite_index()], (x,y))

def move_if_valid(entity, floor, dx, dy):
    # check destination to make sure it's valid, then move
    map = floor.get_map().get_map()
    entity_map = floor.get_entity_map()
    pos = entity.get_pos()
    x = pos[0] + dx
    y = pos[1] + dy

    # check wall and entity map for potential collisions
    if map[x][y] != MAP_WALL:
        if entity_map[x][y] == 1:
            bumped_entity = floor.get_entity_at_position(x, y)
            # if entity blocks movement bump, else move
            if bumped_entity.does_block():
                damage, bumped_hp = bumped_entity.class_type.change_hp(-1*entity.class_type.power)
                print_log("You hit the {monster} for {dam} damage".format(monster = bumped_entity.get_name(), dam = damage), font, text_color_good)
                print_log("The {monster} has {hp} hp".format(monster = bumped_entity.get_name(), hp = bumped_hp), font, text_color)
            else:
                entity.move(dx, dy)
        # move if nothing blocks
        else:
            entity.move(dx,dy)

def move_up_floor(player, floor, floor_list):
    # move up floor if valid, returns floor
    map = floor.get_map()
    if map.get_map()[player.get_pos()] == MAP_UP_STAIR and floor.get_depth() > 0:
        return load_floor(floor_list[floor.get_depth() - 1], player, "UP")
    else:
        print_log("Can't go up here", font, text_color)
        return floor

def move_down_floor(player, floor, floor_list):
    # move up floor if valid, returns floor
    map = floor.get_map()
    if map.get_map()[player.get_pos()] == MAP_DOWN_STAIR and floor.get_depth() < (len(floor_list)-1):
        return load_floor(floor_list[floor.get_depth() + 1], player, "DOWN")
    else:
        print_log("Can't go down here", font, text_color)
        return floor

def create_floor(mapx, mapy, depth=0, entities=[]):
    # create floor, returns floor
    the_floor = floor.Floor(mapgen.Map(mapx,mapy), depth, entities)

    # TODO: item generation, better monster generation
    # make monsters
    num_monsters = 20
    entities = []
    rooms_list = the_floor.get_map().get_rooms() # room = (top left x, top left y, width, height)
    placement_rooms = np.random.randint(0, len(rooms_list), size=num_monsters)
    for i in range(0,num_monsters):
        temp_room = rooms_list[placement_rooms[i]]
        entity_x = np.random.randint(0,temp_room[2]-1) + temp_room[0]
        entity_y = np.random.randint(0,temp_room[3]-1) + temp_room[1]
        # if monster_square is unoccupied, place monster
        # TODO: make sure doesn't overlap player. probably forbid spawning on entrance
        if the_floor.get_entity_map()[entity_x][entity_y] == 0:
            new_entity = entity.Entity(entity_x, entity_y, MUSCLE_BLOB_SPRITE_INDEX, floor=the_floor, ai = ai.Monster_Basic(), class_type=classes.NPC_Muscle_Blob())
            the_floor.set_entity_pos(new_entity, entity_x, entity_y)
            entities.append(new_entity)
        the_floor.set_entities(entities)

    return the_floor

def load_floor(new_floor, player, direction="DOWN"):
    # load in new floor and place player on entrance/exit, returns floor
    # new_floor - floor object for destination floor
    # player - player
    # destination - string to decide if player should be placed on entrance or exit "DOWN" or "UP"
    new_map = new_floor.get_map()

    if direction == "DOWN":
        new_location = new_map.get_entrance()
    elif direction == "UP":
        new_location = new_map.get_exit()

    new_floor.set_entity_pos(player, new_location[0], new_location[1])
    player.set_floor(new_floor)

    print_log("You enter floor {floornum}".format(floornum=new_floor.get_depth()), font, text_color)

    return new_floor

def update_fov(player, floor, range_limit = 8):
    # update FOV
    current_map = floor.get_map()
    vis_map = fov.calc_fov(player.get_pos(), range_limit, floor)

    # update revealed map
    current_map = floor.get_map()
    current_map.update_revealed_map(vis_map)
    return vis_map

def print_log(message, font, color):
    # display message on screen

    # place in log
    MESSAGE_LOG.append(message)

    # create text image
    text_height = MESSAGE_FONT_SIZE
    text = font.render(message, True, color)

    # scrool up & block out line for new message
    message_layer.scroll(0,-1*text_height)
    message_layer.fill((50,50,50), (5, 100-text_height, 400, text_height))
    message_layer.blit(text,(5,100-text_height))

    return message_layer

def main(screen, screenx, screeny):
    # setup floor
    mapx = 80
    mapy = 80
    num_floors = 10
    floor_list = []
    for i in range(num_floors):
        floor_list.append(create_floor(mapx,mapy,i))

    current_floor = floor_list[0]
    current_map = current_floor.get_map()

    # setup basic display and layers
    # sprite size
    spritex = 32
    spritey = 32

    # main game window size
    game_view_x = 540
    game_view_y = 540

    # gui size - takes up the right side of the window
    gui_x = screenx - game_view_x
    gui_y = screeny - 100

    # init display layers
    global background_layer
    global entity_layer
    global gui_layer
    global message_layer
    global pre_screen
    background_layer = pygame.Surface((mapx*32,mapy*32), flags=SRCALPHA)
    entity_layer = pygame.Surface((mapx*32,mapy*32), flags=SRCALPHA)
    gui_layer = pygame.Surface((gui_x,gui_y))
    message_layer = pygame.Surface((gui_x,100))
    pre_screen = pygame.Surface((mapx*32,mapy*32))
    pygame.display.flip()

    gui_layer.fill((70,70,70))
    # message log/text setup
    message_layer.fill((50,50,50))
    global text_color
    global text_color_good
    global text_color_bad
    global font
    text_color = (255,255,255)
    text_color_good = (0,255,0)
    text_color_bad = (255,0,0)
    font = pygame.font.SysFont(None, MESSAGE_FONT_SIZE)

    # load tiles, wall tiles, entity sprites
    tiles = load_sprite_sheet("RLtiles.png", spritex,spritey)
    wall_tiles = load_sprite_sheet("RLtiles_beveled.png", spritex,spritey)
    sprites = load_sprite_sheet("blobs.png", spritex,spritey)

    # make player & other entities
    player = entity.Entity(0, 0, PLAYER_SPRITE_INDEX, "You", class_type=classes.Player_Class())

    # load floor
    current_floor = load_floor(current_floor, player, "DOWN")

    # visibility map
    vis_map = np.zeros(current_floor.get_map().get_map().shape)
    vis_map = update_fov(player, current_floor)

    # draw map & entities
    blit_map_vis(background_layer, current_map, tiles, wall_tiles, vis_map)
    blit_entities(entity_layer, player, current_floor, vis_map, sprites)

    # update flags
    updateView = True

    # init game_state
    global GAME_STATE
    GAME_STATE = STATE_PLAYER_TURN
    # main loop
    while 1:
        # handle player turn
        if GAME_STATE == STATE_PLAYER_TURN:

            # check if alive
            if player.class_type.is_alive() == False:
                print_log("You deconstitute... press any key to exit", font, text_color_bad)
                GAME_STATE = STATE_DEAD

            # hand inputs
            else:
                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        updateView = True # if action taken, update view. TODO: more specific cases for update

                        if event.key == K_UP or event.unicode == "k":
                            move_if_valid(player, current_floor, 0,-1)
                            GAME_STATE = STATE_MONSTER_TURN
                        if event.key == K_DOWN or event.unicode == "j":
                            move_if_valid(player, current_floor, 0,1)
                            GAME_STATE = STATE_MONSTER_TURN
                        if event.key == K_LEFT or event.unicode == "h":
                            move_if_valid(player, current_floor, -1,0)
                            GAME_STATE = STATE_MONSTER_TURN
                        if event.key == K_RIGHT or event.unicode == "l":
                            move_if_valid(player, current_floor, 1,0)
                            GAME_STATE = STATE_MONSTER_TURN
                        if event.unicode == "y":
                            move_if_valid(player, current_floor, -1,-1)
                            GAME_STATE = STATE_MONSTER_TURN
                        if event.unicode == "u":
                            move_if_valid(player, current_floor, 1,-1)
                            GAME_STATE = STATE_MONSTER_TURN
                        if event.unicode == "b":
                            move_if_valid(player, current_floor, -1,1)
                            GAME_STATE = STATE_MONSTER_TURN
                        if event.unicode == "n":
                            move_if_valid(player, current_floor, 1,1)
                            GAME_STATE = STATE_MONSTER_TURN
                        if event.unicode == ".":
                            GAME_STATE = STATE_MONSTER_TURN

                        if event.unicode == "<":
                            current_floor = move_up_floor(player, current_floor, floor_list)
                            current_map = current_floor.get_map()
                        if event.unicode == ">":
                            current_floor = move_down_floor(player, current_floor, floor_list)
                            current_map = current_floor.get_map()

                    if event.type == QUIT:
                        return

        elif GAME_STATE == STATE_MONSTER_TURN:
            # Handle monster turns
            # TODO: filter for only living monsters
            for ent in current_floor.get_entities():
                if ent.is_alive():
                    ent.ai.take_turn(player)
            GAME_STATE = STATE_PLAYER_TURN

        elif GAME_STATE == STATE_DEAD:
            # TODO: handle score screen, restart, etc
            # Wait for input, then return to main menu
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    return

        # update FOV & map if needed
        if updateView:
            vis_map = update_fov(player, current_floor)
            blit_map_vis(background_layer, current_map, tiles, wall_tiles, vis_map)
            gui_layer.blit(pygame.transform.smoothscale(background_layer,(200,200)),(0,0))

        # update tiles & sprites
        blit_entities(entity_layer, player, current_floor, vis_map, sprites)

        # offset to center on player
        x_off, y_off = player.get_pos()

        # blit to pre-screen and scale to display
        pre_screen.blit(background_layer, ((x_off-mapx/2)*-32,(y_off-mapy/2)*-32))
        pre_screen.blit(entity_layer, ((x_off-mapx/2)*-32,(y_off-mapy/2)*-32))
        screen.blit(pygame.transform.smoothscale(pre_screen, (ZOOM*game_view_x, ZOOM*game_view_y)), ((ZOOM-1)*game_view_x/-2,(ZOOM-1)*game_view_y/-2))
        screen.blit(gui_layer, (screenx-gui_x, 0))
        screen.blit(message_layer, (screenx-gui_x, screeny-100))

        pygame.display.flip()

        # reset the update flags
        updateView = False

if __name__ == "__main__":
    main()
