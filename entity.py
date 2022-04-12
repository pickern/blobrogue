import floor

# Sprite constants
PLAYER_SPRITE_INDEX = 0
RAT_SPRITE_INDEX = 3
BLOB_SPRITE_INDEX = 1
MUSCLE_BLOB_SPRITE_INDEX = 4
LEG_BLOB_SPRITE_INDEX = 5
DECONSTITUTED_SPRITE_INDEX = 6

class Entity:
    #  generic class for entities that do things such as player, monsters, NPC's
    def __init__(self, x, y, sprite_index, name = "Entity", floor=None, visible=False, ai=None, class_type=None):
        self.x = x
        self.y = y
        self.visible = visible
        self.name = name
        self.sprite_index = sprite_index
        self.ai = ai
        self.class_type = class_type
        self.floor = floor
        self.blocks_movement = True

        # assign ownership to components as applicable
        if self.ai:
            self.ai.owner = self

        if self.class_type:
            self.class_type.owner = self

    def move(self, dx, dy):
        # update entity map on floor
        if self.floor != None:
            self.floor.set_entity_pos(self, self.x + dx, self.y + dy)

        else:
            self.x += dx
            self.y += dy

    def set_pos(self, newx, newy):
        self.x = newx
        self.y = newy

    def is_alive(self):
        if self.class_type:
            return self.class_type.is_alive()
        else:
            return False

    def get_name(self):
        if self.class_type:
            return self.class_type.get_name()
        else:
            self.name

    def is_visible(self):
        return self.visible

    def set_visible(self, value):
        self.visible = value

    def get_pos(self):
        return (self.x,self.y)

    def set_floor(self, floor):
        self.floor = floor

    def set_sprite_index(self, new_index):
        self.sprite_index = new_index

    def get_sprite_index(self):
        return self.sprite_index

    def does_block(self):
        return self.blocks_movement

    def set_block(self, new_block):
        self.blocks_movement = new_block
