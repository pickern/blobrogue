import actions
import numpy as np

class Base_Item():

    def __init__(self, x, y, floor=None, visible=False, action=None):
        # general info
        self.x = x
        self.y = y
        self.visible = visible
        self.name = "Default item"
        self.sprite_index = 0
        self.floor = floor
        self.description = "Default item" # tooltip to display when viewing item
        self.action = action # ability granted to player by item
        self.blocks_movement = False
        self.stackable = False
        self.weight = 0

        # stats to be used if weapon
        self.weapon = False
        self.weapon_damage = 0
        self.requirement = np.array([0,0,0,0])
        self.throw_requirement = np.array([0,0,0,0])
        self.weapon_action = 0
        self.throw_action = 0

    def get_weapon_action(self):
        return self.weapon_action

    def get_throw_action(self):
        return self.throw_action

    def is_weapon(self):
        # if item is a weapon, swing action will be generated
        return self.weapon

    def get_weapon_damage(self):
        return self.weapon_damage

    def get_weapon_requirements(self):
        return self.requirements

    def get_throw_requirements(self):
        return self.throw_requirements

    def get_thrown_damage(self):
        # all items are throwable, get throw damage
        return 0

    def on_use(self):
        # behavior for item on use
        pass

    def on_eat(self):
        # behavior for item on eat
        pass

    def on_throw(self):
        # behavior for item when thrown
        pass

    def set_pos(self, newx, newy):
        self.x = newx
        self.y = newy

    def get_name(self):
        return self.name

    def is_visible(self):
        return self.visible

    def set_visible(self, value):
        self.visible = value

    def get_pos(self):
        return (self.x,self.y)

    def get_weight(self):
        return self.weight

    def set_floor(self, floor):
        self.floor = floor

    def get_description(self):
        return self.description

    def set_sprite_index(self, new_index):
        self.sprite_index = new_index

    def get_sprite_index(self):
        return self.sprite_index

    def does_block(self):
        return self.blocks_movement

    def set_block(self, new_block):
        self.blocks_movement = new_block

class Item_Rock(Base_Item):

    def __init__(self, x, y, floor=None, visible=False, action=None):
        self.x = x
        self.y = y
        self.visible = visible
        self.name = "Rock"
        self.sprite_index = 3
        self.floor = floor
        self.description = "It's a rock" # tooltip to display when viewing item
        self.action = action # ability granted to player by item
        self.blocks_movement = False
        self.weight = 6
        self.stackable = True
        self.weapon = False
        self.throw_requirements = np.array([1,0,0,0])

        self.throw_action = actions.Item_Throw(self)

    def get_thrown_damage(self):
        return 6
