from entity import Entity
import numpy as np

# Sprite constants
PLAYER_SPRITE_INDEX = 0
RAT_SPRITE_INDEX = 3
BLOB_SPRITE_INDEX = 1
MUSCLE_BLOB_SPRITE_INDEX = 4
LEG_BLOB_SPRITE_INDEX = 5
DECONSTITUTED_SPRITE_INDEX = 6

class Base_Component:
    entity: Entity

# Base player class
class Player_Class(Base_Component):

    def __init__(self):
        self.max_hp = 20
        self.hp = 20
        self.power = 5
        self.defense = 2
        self.alive = True
        self.name = "You"

    def get_hp(self):
        return self.hp

    def set_hp(self, new_hp):
        self.hp = new_hp

    def is_alive(self):
        return self.alive

    def change_hp(self, change):
        # process damage or healing

        if change > 0:
        # if above 0, its healing. don't exceed max_hp.
            self.hp = np.minimum(self.max_hp, self.hp + change)
            return change, self.hp
        else:
        # else it's damage
            damage = np.maximum(-1*change - self.defense, 0)
            self.hp -= damage

        # die if hp <= 0
        if self.hp <= 0:
            self.alive = False

        return damage, self.hp

    def get_power(self):
        return self.power

    def get_defense(self):
        return self.defense

    def get_name(self):
        return self.name

# NPC/Monster classes
class Base_NPC(Base_Component):

    def __init__(self):
        self.max_hp = 1
        self.hp = 1
        self.power = 1
        self.defense = 1
        self.alive = True
        self.name = "NPC"

    def get_hp(self):
        return self.hp

    def set_hp(self, new_hp):
        self.hp = new_hp

    def is_alive(self):
        return self.alive

    def change_hp(self, change):
        # process damage or healing

        if change > 0:
        # if above 0, its healing. don't exceed max_hp.
            self.hp = np.minimum(self.max_hp, self.hp + change)
            return change, self.hp
        else:
        # else it's damage
            damage = np.maximum(-1*change - self.defense, 0)
            self.hp -= damage

        # die if hp <= 0
        if self.hp <= 0:
            # print("{name} deconsitutes".format(name = self.owner.get_name()))
            # set sprite index to deconstituted and alive to false
            self.owner.set_sprite_index(DECONSTITUTED_SPRITE_INDEX)
            self.owner.set_block(False)
            self.alive = False

        return damage, self.hp

    def get_power(self):
        return self.power

    def get_defense(self):
        return self.defense

    def get_name(self):
        return self.name


class NPC_Blob(Base_NPC):

    def __init__(self):
        self.name = "Blobman"
        self.max_hp = 6
        self.hp = 6
        self.power = 3
        self.defense = 0
        self.alive = True

class NPC_Muscle_Blob(Base_NPC):

    def __init__(self):
        self.name = "Muscle Blobman"
        self.max_hp = 14
        self.hp = 14
        self.power = 8
        self.defense = 1
        self.alive = True
