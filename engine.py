# GENERAL TODO:
# major systems:
#   - todo for items:
#       - generation, test with map & blitting
#       - inventory management & GUI
#           - make inventory screen, wield select screen, throw select screen
#           - display inventory in regular GUI
#       - player interaction with items
#           - check item abilities to add on level up
#           - handle stackable items
#           - handle removing items on throw
#   - proper monster AI/general pathfinding
#   - character sheet view
#   - help menu (prob do last)
# floor/balance/scoring/game design/win condition
# misc items & optimizations noted elsewhere (ctrl-f "BUG" for bugs)


try:
    import numpy as np
    import pygame
    from pygame.locals import *
    import mapgen
    import fov
    import entity
    import sys
    import os
    import item
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

# Item sprite constants
ITEM_CORN_INDEX = 0
ITEM_EVIL_CORN_INDEX = 1
ITEM_SWORD_INDEX = 2
ITEM_ROCK_INDEX = 3

# sprite starts for extended spritesheet
PLAYER_SPRITES = 0
NPC_SPRITES = 9
ENEMY_SPRITES = 18

# Constant/utitlity tiles
REVEALED_TILE = pygame.Surface((32,32), flags=SRCALPHA)
BORDER_TILE = pygame.Surface((32,32), flags=SRCALPHA)
TARGET_TILE_VALID = pygame.Surface((32,32), flags=SRCALPHA)
TARGET_TILE_INVALID = pygame.Surface((32,32), flags=SRCALPHA)
REVEALED_TILE.fill((0,0,0,180))
TARGET_TILE_VALID.fill((0,250,0,90))
TARGET_TILE_INVALID.fill((250,0,0,90))
BORDER_TILE.fill((100,100,100))

# hold list of all messages displayed
GUI_FONT_SIZE = 24
MESSAGE_FONT_SIZE = 12
MESSAGE_LOG = []

# game states
STATE_PLAYER_TURN = 0
STATE_MONSTER_TURN = 1
STATE_DEAD = 2
STATE_LEVEL_UP = 3
STATE_ABILITY_MENU_MELEE = 4
STATE_ABILITY_MENU_RANGED = 6
STATE_TARGETTING = 5
STATE_VIEW_INVENTORY = 7
STATE_VIEW_CHARACTER = 8
STATE_EXAMINE = 9
STATE_HELP_MENU = 10

# CIRCLE_LIST = []
# RING_LIST = []

def make_circles(max_radius=8):
    # makes numpy arrays of circles up to max radius
    # returns list of filled circles and unfilled rings up to max radius
    x = np.arange(-8,8+1)
    y = np.arange(-8,8+1)
    x_grid, y_grid = np.meshgrid(x, y)
    base_circle = np.sqrt(x_grid**2 + y_grid**2)
    circle_list = []
    ring_list = []
    for i in range(2, max_radius + 1):
        radius = i-.5
        circle_list.append(base_circle <= radius)
        ring_list.append((base_circle <= radius) & (base_circle > (radius - 1)))

    return circle_list, ring_list

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

def blit_entities(entity_layer, player, floor, vis_map, sprites, item_sprites, x_offset=0, y_offset=0):
    # blits entities (player, monsters, items, etc) to entity layer

    # transparent fill
    entity_layer.fill((0,0,0,0))

    entity_list = floor.get_entities()
    item_list = floor.get_item_list()

    for item in item_list:
        x = item.get_pos()[0]
        y = item.get_pos()[1]
        if vis_map[x][y] == 1:
            entity_layer.blit(item_sprites[item.get_sprite_index()], (x*32,y*32))

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

def blit_gui(gui_layer, background_layer, player):
    # TODO: Truncate regen values in case they decide to get long
    # TODO: clean this up for the love of god

    # fill
    gui_layer.fill((0,0,0))

    # minimap
    gui_layer.blit(pygame.transform.smoothscale(background_layer,(200,200)),(0,0))

    # character info
    hp = gui_font.render("HP: {cur} / {max} | +{reg}".format(cur = player.class_type.get_hp(), max = player.class_type.get_max_hp(), reg = player.class_type.get_hp_regen()), True, text_color)
    gui_layer.blit(hp, (210, 10))
    hp = gui_font.render("Mana: {cur} / {max} | +{reg}".format(cur = player.class_type.get_mana(), max = player.class_type.get_max_mana(), reg = player.class_type.get_mana_regen()), True, text_color)
    gui_layer.blit(hp, (210, 30))
    xp = gui_font.render("XP: {cur} / 100 | Level {lev}".format(cur = player.class_type.get_xp(), lev = player.class_type.get_level()), True, text_color)
    gui_layer.blit(xp, (210, 60))
    arm = gui_font.render("Arm: {arm}".format(arm = player.class_type.get_arm()), True, text_color)
    gui_layer.blit(arm, (210, 90))
    leg = gui_font.render("Leg: {leg}".format(leg = player.class_type.get_leg()), True, text_color)
    gui_layer.blit(leg, (210, 120))
    body = gui_font.render("Body: {body}".format(body = player.class_type.get_body()), True, text_color)
    gui_layer.blit(body, (210, 150))
    mind = gui_font.render("Mind: {mind}".format(mind = player.class_type.get_mind()), True, text_color)
    gui_layer.blit(mind, (210, 180))
    mind = gui_font.render("Melee: {mind}".format(mind = player.class_type.get_active_melee().get_name()), True, text_color)
    gui_layer.blit(mind, (210, 210))
    mind = gui_font.render("Ranged: {mind}".format(mind = player.class_type.get_active_ranged().get_name()), True, text_color)
    gui_layer.blit(mind, (210, 240))

def blit_ability_menu(player, menu_layer, is_melee=True):
    # blits menu of abilities to be selected. allows choosing melee or ranged.
    menu_layer.fill((50,50,50))
    the_alphabet = "abcdefghijklmnopqrstuvwxyz"
    abilities = player.class_type.get_available_actions()
    choice_dict = {} # compiles available options, will be returned to use for selection
    header_1 = gui_font.render("Ability", True, text_color)
    header_2 = gui_font.render("Damage", True, text_color)
    header_3 = gui_font.render("Accuracy", True, text_color)
    header_4 = gui_font.render("Range", True, text_color)
    header_5 = gui_font.render("Cost", True, text_color)
    menu_layer.blit(header_1, (20, 20))
    menu_layer.blit(header_2, (120, 20))
    menu_layer.blit(header_3, (220, 20))
    menu_layer.blit(header_4, (320, 20))
    menu_layer.blit(header_5, (420, 20))
    i = 0

    for act in abilities:
        # Collect list of melee abilities and blit
        if is_melee:
            if act.get_range() == 1 and act.get_name() != "None":
                act_props = [act.get_damage(), act.get_accuracy(), act.get_range(), act.get_cost()]
                item = gui_font.render("({letter}) - {act_name}".format(letter = the_alphabet[i], act_name = act.get_name()), True, text_color)
                menu_layer.blit(item, (20, 50 + 30*i))
                j = 1
                for prop in act_props:
                    menu_layer.blit(gui_font.render("{x}".format(x=prop), True, text_color), (20+100*j, 50+30*i))
                    j += 1
                choice_dict[the_alphabet[i]] = act
                i += 1
        # Else collect ranged abilities
        else:
            if act.get_range() != 1 and act.get_name() != "None":
                act_props = [act.get_damage(), act.get_accuracy(), act.get_range(), act.get_cost()]
                item = gui_font.render("({letter}) - {act_name}".format(letter = the_alphabet[i], act_name = act.get_name()), True, text_color)
                menu_layer.blit(item, (20, 50 + 30*i))
                j = 1
                for prop in act_props:
                    menu_layer.blit(gui_font.render("{x}".format(x=prop), True, text_color), (20+100*j, 50+30*i))
                    j += 1
                choice_dict[the_alphabet[i]] = act
                i += 1
    return choice_dict

def get_line(endx, endy, aoe=1):
    # assume line is coming from 0,0. endx and endy should be ints
    # returns list of points on the line
    # TODO: not sure if this will be symmetrical. test & figure this out

    temp_y = 0
    point_list = [(0,0)]
    abs_x = np.abs(endx)
    abs_y = np.abs(endy)
    if endx != 0:
        slope = endy/endx
        if np.abs(slope) < 1:
            for i in range(0, int(abs_x)+1):
                temp_y = np.round(i*slope)*np.sign(endx)
                point_list.append((i*np.sign(endx), temp_y))
        else:
            slope = endx/endy
            for i in range(0, int(abs_y)+1):
                temp_x = np.round(i*slope)*np.sign(endy)
                point_list.append((temp_x, i*np.sign(endy)))
    else:
        slope = 0
        for i in range(0, int(abs_y)+1):
            temp_x = np.round(i*slope)*np.sign(endy)
            point_list.append((temp_x, i*np.sign(endy)))

    return point_list

def get_circle_points(radius):
    circle = CIRCLE_LIST[radius-2]
    x = 0
    y = 0
    point_list = []
    for row in circle:
        y = 0
        for col in row:
            if circle[x][y] == True:
                point_list.append((x,y))
            y += 1
        x += 1

    return point_list

def blit_targetting(player, floor, aux_layer, target, vis_map):
    # updates target view and returns if target is valid
    # we assume that visible tiles are targetable as long as they are in range and not blocked by another entity
    # TODO: decide how line draw colors should display with AOE

    aoe = player.class_type.get_active_ranged().get_aoe()
    is_valid = False
    entity_map = floor.get_entity_map()
    wall_map = floor.get_map().get_map()
    adjusted_target = (player.get_pos()[0] + target[0], player.get_pos()[1] + target[1])

    # check if in range and visible
    # TODO: auto-target closest enemy?
    # TODO: blit border for area within range
    if np.sqrt(target[0]**2 + target[1]**2) <= player.class_type.get_active_ranged().get_range() and vis_map[adjusted_target[0]][adjusted_target[1]] == 1:
        is_valid = True

    # blit line to targetted tile
    aux_layer.fill((0,0,0,0)) # transparent fill
    line_points = get_line(target[0], target[1])
    aoe_points = []
    if aoe > 1:
        circle_points = get_circle_points(aoe)
        # adjust circle points
        for point_0 in circle_points:
            new_point = (point_0[0]-8+target[0], point_0[1]-8+target[1])
            line_points.append(new_point)
            aoe_points.append(new_point)

    blocked = False
    num_blockers = 0
    for point in line_points:
        adjusted_point = (int(player.get_pos()[0] + point[0]), int(player.get_pos()[1] + point[1]))
        if is_valid and not blocked:
            aux_layer.blit(TARGET_TILE_VALID, ((point[0]+player.get_pos()[0])*32, (point[1]+player.get_pos()[1])*32))
        else:
            aux_layer.blit(TARGET_TILE_INVALID, ((point[0]+player.get_pos()[0])*32, (point[1]+player.get_pos()[1])*32))
        if adjusted_point != player.get_pos() and adjusted_point != adjusted_target:
            if wall_map[adjusted_point[0]][adjusted_point[1]] == MAP_WALL or entity_map[adjusted_point[0]][adjusted_point[1]] == 1:
                blocked = True
                num_blockers += 1

    return is_valid, num_blockers, aoe_points


def move_if_valid(player, floor, dx, dy):
    # check destination to make sure it's valid, then move
    map = floor.get_map().get_map()
    entity_map = floor.get_entity_map()
    pos = player.get_pos()
    x = pos[0] + dx
    y = pos[1] + dy

    # check wall and entity map for potential collisions
    if map[x][y] != MAP_WALL:
        if entity_map[x][y] == 1:
            bumped_entity = floor.get_entity_at_position(x, y)
            # if entity blocks movement bump, else move
            # this conditional is currently redundant since dead monsters are removed from entity map. keeping it in case something changes.
            # TODO BUG: handle when living entity is standing on dead entity
            if bumped_entity.does_block():
                attack_entity(player, bumped_entity, player.class_type.get_active_melee())
            else:
                player.move(dx, dy)
        # move if nothing blocks
        else:
            player.move(dx,dy)
    return False

def attack_entity(player, target_entity, attack, hit_modifier=0):
    # player - the player
    # target entity - entity being targetted by attack
    # attack - the action being used to attack
    # hit_modifier - situational modifier affecting hit chance. works like evasion basically.
    temp_damage = attack.get_damage()
    attack_name = attack.get_name()
    if attack.get_cost() > 0:
        player.class_type.spend_mana(attack.get_cost())

    hit_roll = np.random.randint(0,100)
    if hit_roll <= attack.get_accuracy()*100 - target_entity.class_type.get_evasion() + hit_modifier:
        damage, target_hp = target_entity.class_type.change_hp(-1*temp_damage)
        print_log("You {name} at the {monster} for {dam} damage".format(name=attack_name, monster = target_entity.get_name(), dam = damage), font, text_color_good)
        if not target_entity.is_alive():
            # Result == true means level up occurred
            result = player.class_type.gain_xp(target_entity.class_type.get_xp())
            print_log("The {monster} deconstitutes".format(monster = target_entity.get_name()), font, text_color)
            if result:
                print_log("Your level increases to {level}!".format(level=player.class_type.get_level()+1), font, text_color_good)
                print_log("Choose state to increase: (a)rm, (l)eg, (b)ody, (m)ind", font, text_color_good)
    else:
        print_log("You miss", font, text_color)

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
    the_map = the_floor.get_map().get_map()
    rooms_list = the_floor.get_map().get_rooms() # room = (top left x, top left y, width, height)
    num_monsters = 20
    num_items = 20
    placement_rooms = np.random.randint(0, len(rooms_list), size=num_monsters)

    # TODO: item generation, better monster generation

    for i in range(0,num_items):
        temp_room = rooms_list[placement_rooms[i]]
        item_x = np.random.randint(0,temp_room[2]-1) + temp_room[0]
        item_y = np.random.randint(0,temp_room[3]-1) + temp_room[1]
        # if monster_square is unoccupied and a floor tile, place monster
        if the_floor.get_item_map()[item_x][item_y] == 0 and the_map[item_x][item_y] == MAP_FLOOR:
            new_item = item.Item_Rock(item_x, item_y, floor=the_floor)
            the_floor.add_item(new_item)

    # make monsters
    entities = []

    for i in range(0,num_monsters):
        temp_room = rooms_list[placement_rooms[i]]
        entity_x = np.random.randint(0,temp_room[2]-1) + temp_room[0]
        entity_y = np.random.randint(0,temp_room[3]-1) + temp_room[1]
        # if monster_square is unoccupied and a floor tile, place monster
        if the_floor.get_entity_map()[entity_x][entity_y] == 0 and the_map[entity_x][entity_y] == MAP_FLOOR:
            # generate blobs with stat totals based on floor depth
            ran = np.random.randint(0,4) + the_floor.get_depth()*2
            new_entity = entity.Entity(entity_x, entity_y, MUSCLE_BLOB_SPRITE_INDEX, floor=the_floor, ai = ai.Monster_Basic(), class_type=classes.NPC_Dynamic_Blob(ran))
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

    global CIRCLE_LIST
    global RING_LIST
    CIRCLE_LIST, RING_LIST = make_circles()
    # init display layers
    global background_layer
    global entity_layer
    global gui_layer
    global message_layer
    global menu_layer
    global pre_screen
    background_layer = pygame.Surface((mapx*32,mapy*32), flags=SRCALPHA)
    menu_layer = pygame.Surface((game_view_x - 60, game_view_y - 60), flags=SRCALPHA)
    entity_layer = pygame.Surface((mapx*32,mapy*32), flags=SRCALPHA)
    aux_layer = pygame.Surface((mapx*32,mapy*32), flags=SRCALPHA)
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
    global gui_font
    text_color = (255,255,255)
    text_color_good = (0,255,0)
    text_color_bad = (255,0,0)
    text_colors = (text_color, text_color_good, text_color_bad)
    font = pygame.font.SysFont(None, MESSAGE_FONT_SIZE)
    gui_font = pygame.font.SysFont(None, GUI_FONT_SIZE)

    # load tiles, wall tiles, entity sprites
    tiles = load_sprite_sheet("RLtiles.png", spritex,spritey)
    wall_tiles = load_sprite_sheet("RLtiles_beveled.png", spritex,spritey)
    sprites = load_sprite_sheet("blobs_extended.png", spritex,spritey)
    item_sprites = load_sprite_sheet("item_sprites.png", spritex,spritey)

    # make player & other entities
    player = entity.Entity(0, 0, PLAYER_SPRITE_INDEX, "You", class_type=classes.Player_Class())

    # load floor
    current_floor = load_floor(current_floor, player, "DOWN")

    # visibility map
    vis_map = np.zeros(current_floor.get_map().get_map().shape)
    vis_map = update_fov(player, current_floor)

    # draw map & entities
    blit_map_vis(background_layer, current_map, tiles, wall_tiles, vis_map)
    blit_entities(entity_layer, player, current_floor, vis_map, sprites, item_sprites)

    # update flags
    update_view = True

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
                        update_view = True # if action taken, update view. TODO: more specific cases for update

                        ##### TURN CHANGING ACTIONS #####
                        # MOVEMENT
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
                        # PICKUP ITEM
                        if event.unicode == ",":
                            # TODO: handle multiple items on same tile
                            temp_item = current_floor.get_item_at_position(player.get_pos()[0], player.get_pos()[1])
                            if temp_item:
                                player.class_type.add_item(temp_item)
                                current_floor.remove_item(temp_item)
                                print_log("You pick up the {name}".format(name=temp_item.get_name()), font, text_color)
                                GAME_STATE = STATE_MONSTER_TURN
                            else:
                                print_log("Nothing here to pick up", font, text_color)
                        # WAIT
                        if event.unicode == ".":
                            GAME_STATE = STATE_MONSTER_TURN

                        # ENTER TARGETTING STATE FOR RANGED ATTACK
                        if event.unicode == "f":
                            if player.class_type.get_active_ranged() and player.class_type.get_active_ranged().get_name() != "None":
                                if player.class_type.get_active_ranged().get_cost() > player.class_type.get_mana():
                                    print_log("Not enough mana", font, text_color)
                                else:
                                    GAME_STATE = STATE_TARGETTING
                            else:
                                print_log("No ranged ability selected", font, text_color)

                        # STAIR ACTIONS
                        if event.unicode == "<":
                            current_floor = move_up_floor(player, current_floor, floor_list)
                            current_map = current_floor.get_map()
                        if event.unicode == ">":
                            current_floor = move_down_floor(player, current_floor, floor_list)
                            current_map = current_floor.get_map()

                        # NON-TURN/MENU ACTIONS
                        if event.unicode == "a":
                            # melee ability menu
                            GAME_STATE = STATE_ABILITY_MENU_MELEE
                        if event.unicode == "A":
                            # ranged ability menu
                            GAME_STATE = STATE_ABILITY_MENU_RANGED
                        if event.unicode == "w":
                            # TODO: weild weapon - will set active melee
                            pass
                        if event.unicode == "W":
                            # TODO: wear item
                            pass
                        if event.unicode == "t":
                            # TODO: set active ranged to throwing item
                            pass
                        if event.unicode == "c":
                            # TODO: character sheet view
                            pass
                        if event.unicode == "i":
                            # TODO: inventory view
                            pass
                        if event.unicode == "x":
                            # TODO: examine view
                            pass

                    if event.type == QUIT:
                        return

                # change state from monster turn to level up if level up occured
                if player.class_type.did_level():
                    GAME_STATE = STATE_LEVEL_UP

        elif GAME_STATE == STATE_MONSTER_TURN:
            # update player passives. laziest way to do this.
            player.class_type.update_passive()
            # Handle monster turns
            for ent in current_floor.get_entities():
                # only living entities take turns
                if ent.is_alive():
                    # take_turn will return a tuple (message, quality int) for message to display and goodness of message is applicable
                    # should return None otherwise
                     result = ent.ai.take_turn(player)
                     if result:
                         print_log(result[0], font, text_colors[result[1]])

            # revert state to player
            GAME_STATE = STATE_PLAYER_TURN
            update_view = True

        elif GAME_STATE == STATE_DEAD:
            # TODO: handle score screen, restart, etc
            # Wait for input, then return to main menu
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    return

        elif GAME_STATE == STATE_LEVEL_UP:
            # wait for input to determine stat to increase, then go to monster turn
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.unicode == "a":
                        player.class_type.level_up("arm")
                        GAME_STATE = STATE_MONSTER_TURN
                    elif event.unicode == "l":
                        player.class_type.level_up("leg")
                        GAME_STATE = STATE_MONSTER_TURN
                    elif event.unicode == "b":
                        player.class_type.level_up("body")
                        GAME_STATE = STATE_MONSTER_TURN
                    elif event.unicode == "m":
                        player.class_type.level_up("mind")
                        GAME_STATE = STATE_MONSTER_TURN

        elif GAME_STATE == STATE_ABILITY_MENU_MELEE:
            # blit menu and wait for input
            choices = blit_ability_menu(player, menu_layer)
            screen.blit(menu_layer, (30,30))
            pygame.display.flip()
            in_menu = True
            while in_menu:
                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.unicode in choices:
                            player.class_type.set_active_melee(choices[event.unicode])
                            in_menu = False
                        elif event.key == K_ESCAPE:
                            in_menu = False
            update_view = True
            GAME_STATE = STATE_PLAYER_TURN

        elif GAME_STATE == STATE_ABILITY_MENU_RANGED:
            # blit menu and wait for input
            choices = blit_ability_menu(player, menu_layer, False)
            screen.blit(menu_layer, (30,30))
            pygame.display.flip()
            in_menu = True
            while in_menu:
                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.unicode in choices:
                            player.class_type.set_active_ranged(choices[event.unicode])
                            in_menu = False
                        elif event.key == K_ESCAPE:
                            in_menu = False

            update_view = True
            GAME_STATE = STATE_PLAYER_TURN

        elif GAME_STATE == STATE_TARGETTING:
            update_view = True
            target = np.array([0,0])

            # snapshot of pre screen. used to refresh between targetting blits so we don't have to re-blit everything.
            pre_screen_copy = pre_screen.copy()

            # get init target
            target_is_valid, num_blockers, aoe_points = blit_targetting(player, current_floor, aux_layer, target, vis_map)

            # setup targetting view
            pre_screen.blit(aux_layer, ((x_off-mapx/2)*-32,(y_off-mapy/2)*-32))
            screen.blit(pygame.transform.smoothscale(pre_screen, (ZOOM*game_view_x, ZOOM*game_view_y)), ((ZOOM-1)*game_view_x/-2,(ZOOM-1)*game_view_y/-2))
            screen.blit(gui_layer, (screenx-gui_x, 0))
            screen.blit(message_layer, (screenx-gui_x, screeny-100))
            pygame.display.flip()

            # flags
            targetting = True
            update_targetting_view = False

            while targetting:
                update_targetting_view = False
                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        update_targetting_view = True
                        # movement keys adjust targetting square
                        if event.key == K_UP or event.unicode == "k":
                            target[0] += 0
                            target[1] -= 1
                        elif event.key == K_DOWN or event.unicode == "j":
                            target[0] += 0
                            target[1] += 1
                        elif event.key == K_LEFT or event.unicode == "h":
                            target[0] -= 1
                            target[1] += 0
                        elif event.key == K_RIGHT or event.unicode == "l":
                            target[0] += 1
                            target[1] -= 0
                        elif event.unicode == "y":
                            target[0] -= 1
                            target[1] -= 1
                        elif event.unicode == "u":
                            target[0] += 1
                            target[1] -= 1
                        elif event.unicode == "b":
                            target[0] -= 1
                            target[1] += 1
                        elif event.unicode == "n":
                            target[0] += 1
                            target[1] += 1
                        elif event.key == K_ESCAPE:
                            # exit targetting
                            targetting = False
                            GAME_STATE = STATE_PLAYER_TURN
                        elif event.key == K_RETURN:
                            # do attack if valid
                            if target_is_valid:
                                targetting = False
                                # TODO: dynamic targetting, check everything in a line to see if it would hit something behind target
                                # do attack at target
                                if len(aoe_points) > 0: # aoe attacks
                                    target_points = aoe_points
                                    target_points.append((0,0))
                                    for t_point in target_points:
                                        target_entity = current_floor.get_entity_at_position(player.get_pos()[0] + target[0] + t_point[0], player.get_pos()[1] + target[1] + t_point[1])
                                        if target_entity:
                                            attack_entity(player, target_entity, player.class_type.get_active_ranged(), 0)
                                else: # single point attack
                                    target_entity = current_floor.get_entity_at_position(player.get_pos()[0] + target[0], player.get_pos()[1] + target[1])
                                    if target_entity:
                                        attack_entity(player, target_entity, player.class_type.get_active_ranged(), num_blockers*-5)
                                    # else fire into distance
                                    else:
                                        print_log("You {name} into the distance...".format(name = player.class_type.get_active_ranged().get_name()), font, text_color)
                            # if not valid, stay in targetting
                            else:
                                print_log("Target not valid", font, text_color)

                # update view if needed
                if update_targetting_view:
                    target_is_valid, num_blockers, aoe_points = blit_targetting(player, current_floor, aux_layer, target, vis_map)
                    pre_screen.blit(pre_screen_copy, (0,0))
                    pre_screen.blit(aux_layer, ((x_off-mapx/2)*-32,(y_off-mapy/2)*-32))
                    screen.blit(pygame.transform.smoothscale(pre_screen, (ZOOM*game_view_x, ZOOM*game_view_y)), ((ZOOM-1)*game_view_x/-2,(ZOOM-1)*game_view_y/-2))
                    screen.blit(gui_layer, (screenx-gui_x, 0))
                    screen.blit(message_layer, (screenx-gui_x, screeny-100))
                    pygame.display.flip()

            # update state if needed. if not, player exitted targetting and state == player turn
            if player.class_type.did_level():
                GAME_STATE = STATE_LEVEL_UP
            elif GAME_STATE == STATE_TARGETTING:
                GAME_STATE = STATE_MONSTER_TURN

        # update FOV & map if needed
        if update_view:
            # update map
            vis_map = update_fov(player, current_floor)
            blit_map_vis(background_layer, current_map, tiles, wall_tiles, vis_map)

            # update GUI
            blit_gui(gui_layer, background_layer, player)

        # update tiles & sprites
        blit_entities(entity_layer, player, current_floor, vis_map, sprites, item_sprites)

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
        update_view = False

if __name__ == "__main__":
    main()
