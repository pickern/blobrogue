from entity import Entity
import numpy as np
import actions
import inspect

# Sprite constants
PLAYER_SPRITE_INDEX = 0
RAT_SPRITE_INDEX = 3
BLOB_SPRITE_INDEX = 1
MUSCLE_BLOB_SPRITE_INDEX = 4
LEG_BLOB_SPRITE_INDEX = 5
DECONSTITUTED_SPRITE_INDEX = 6

# stupid system for keeping track of player sprite
PLAYER_SPRITE_INDEX_LIST = (0,6,4,2,1,7,5,3)

class Base_Component:
    entity: Entity

# Base player class
class Player_Class(Base_Component):

    def __init__(self):
        # stats
        self.max_hp = 20
        self.hp = 20
        self.max_mana = 10
        self.mana = 10
        # temp hp stores fractional hp to track regen and such, current_hp = floor(temp_hp)
        self.temp_hp = self.hp
        self.regen = .2
        self.temp_mana = self.mana
        self.mana_regen = .2
        # defense and evasion are seconary stats calced from primary stats
        self.defense = 2
        self.evasion = 10
        # primary stats
        self.arm = 0
        self.leg = 0
        self.body = 0
        self.mind = 0

        self.inventory=[]
        self.throw_actions=[]
        self.wield_actions=[]


        # initialize actions. keeps a list of all actions and which ones are available to player.
        self.all_actions=[]
        for act in inspect.getmembers(actions,inspect.isclass):
            if act[0].startswith("Attack"):
                self.all_actions.append(act[1](self))

        # init available actions and add as applicable
        self.available_actions = []
        stat_block = np.array([self.arm, self.leg, self.body, self.mind])
        for act in self.all_actions:
            if np.all(np.greater_equal(stat_block, act.get_requirements())):
                self.available_actions.append(act)
                if act.get_name() == "Flail":
                    self.active_melee = act
                if act.get_name() == "Shoot":
                    self.active_ranged = act

        for act in self.available_actions:
            self.all_actions.remove(act)

        self.xp = 0
        self.level = 1
        self.did_level_up = False

        # utility info
        self.alive = True
        self.name = "You"
        self.sprite_index = 0

    def get_inventory(self):
        return self.inventory

    def add_item(self, item):
        # add to inventory
        self.inventory.append(item)
        # add abilities if able
        # add throw action
        act = item.get_throw_action()
        stat_block = np.array([self.arm, self.leg, self.body, self.mind])
        if np.all(np.greater_equal(stat_block, act.get_requirements())):
            act.parent = self
            self.throw_actions.append(act)
            # self.available_actions.append(act)

        # add wield action if applicable
        if item.is_weapon():
            act = item.get_weapon_action()
            stat_block = np.array([self.arm, self.leg, self.body, self.mind])
            if np.all(np.greater_equal(stat_block, act.get_requirements())):
                act.parent = self
                self.wield_actions.append(act)

    def remove_item(self, item):
        # remove item & associated action
        self.inventory.remove(item)
        self.throw_actions.remove(item.get_throw_action)
        if item.is_weapon():
            self.wield_actions.remove(item.get_weapon_action)

    def did_level(self):
        return self.did_level_up

    def level_up(self, stat):
        # TODO: allow updating multiple stats at once
        self.did_level_up = False
        self.level += 1
        self.xp -= 100

        # update primary & cooresponging secondary stats
        if stat == "arm":
            self.arm += 2
            self.defense = self.defense + self.arm//2 + self.body//2
        elif stat == "leg":
            self.leg += 2
            self.evasion = np.maximum(0, 10 + self.leg - self.body//2)
        elif stat == "body":
            self.body += 2
            self.max_hp = 20 + self.body * 3
            self.regen = .2 + self.body *.1
            self.evasion = np.maximum(0, 10 + self.leg - self.body//2)
            self.defense = self.defense + self.arm//2 + self.body//2
        elif stat == "mind":
            self.mind += 2
            self.max_mana = 10 + self.mind * 4
            self.mana_regen = .2 + self.mind *.1

        # check for new abilities to add
        stat_block = np.array([self.arm, self.leg, self.body, self.mind])
        for act in self.all_actions:
            if np.all(np.greater_equal(stat_block, act.get_requirements())):
                self.available_actions.append(act)
                self.all_actions.remove(act)

        # TODO: check is new item abilities can be added

        # update sprite in a very silly way
        new_index = self.arm/np.maximum(1,self.arm) + 2*self.leg/np.maximum(1,self.leg) + 4*self.mind/np.maximum(1,self.mind)
        self.sprite_index = PLAYER_SPRITE_INDEX_LIST[int(new_index)]

    def update_passive(self):
        # updates passive counters whenever a turn passes
        self.temp_hp = np.minimum(self.temp_hp + self.regen, self.max_hp)
        self.hp = int(np.floor(self.temp_hp))
        self.temp_mana = np.minimum(self.temp_mana + self.mana_regen, self.max_mana)
        self.mana = int(np.floor(self.temp_mana))

    def spend_mana(self, cost):
        self.mana -= cost
        self.temp_mana = self.mana

    def get_hp(self):
        return self.hp

    def get_max_hp(self):
        return self.max_hp

    def get_mana(self):
        return self.mana

    def get_max_mana(self):
        return self.max_mana

    def get_hp_regen(self):
        return self.regen

    def get_mana_regen(self):
        return self.mana_regen

    def set_hp(self, new_hp):
        self.hp = new_hp
        self.temp_hp = new_hp

    def get_arm(self):
        return self.arm

    def get_leg(self):
        return self.leg

    def get_body(self):
        return self.body

    def get_mind(self):
        return self.mind

    def is_alive(self):
        return self.alive

    def change_hp(self, change):
        # process damage or healing

        if change > 0:
        # if above 0, its healing. don't exceed max_hp.
            self.hp = np.minimum(self.max_hp, self.hp + change)
            self.temp_hp = self.hp
            return change, self.hp
        else:
        # else it's damage
            damage = np.maximum(-1*change - self.defense, 0)
            self.hp -= damage
            self.temp_hp = self.hp

        # die if hp <= 0
        if self.hp <= 0:
            self.alive = False

        return damage, self.hp

    def get_available_actions(self):
        return self.available_actions

    def set_active_melee(self, new_melee):
        self.active_melee = new_melee

    def set_active_ranged(self, new_ranged):
        self.active_ranged = new_ranged

    def get_active_melee(self):
        return self.active_melee

    def get_active_ranged(self):
        return self.active_ranged

    def get_attack(self):
        # don't use this
        # returns attack damage and name
        return self.active_melee.get_damage(), self.active_melee.get_name()

    def get_defense(self):
        return self.defense

    def get_evasion(self):
        return self.evasion

    def get_name(self):
        return self.name

    def get_xp(self):
        return self.xp

    def get_level(self):
        return self.level

    def gain_xp(self, gain):
        # handle xp and level up every 100 xp
        self.xp += gain
        if self.xp >= 100:
            self.did_level_up = True
            return True
        else:
            return False

    def get_sprite_index(self):
        return self.sprite_index

# NPC/Monster classes
class Base_NPC(Base_Component):

    def __init__(self, friendly=False):
        self.max_hp = 1
        self.hp = 1
        # power and defense will be removed
        self.power = 1
        self.defense = 1
        self.evasion = 5
        self.alive = True
        self.name = "NPC"
        self.xp = 0
        self.sprite_index = 0
        self.friendly=friendly

    def is_friendly(self):
        return self.friendly

    def get_evasion(self):
        return self.evasion

    def get_xp(self):
        return self.xp

    def get_hp(self):
        return self.hp

    def get_max_hp(self):
        return self.max_hp

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
            # set sprite index to deconstituted and alive to false
            self.owner.floor.remove_entity_from_entity_map(self.owner)
            if self.friendly:
                self.sprite_index = 17
            else:
                self.sprite_index = 26
            self.owner.set_block(False)
            self.alive = False

        return damage, self.hp

    def get_power(self):
        return self.power

    def get_defense(self):
        return self.defense

    def get_name(self):
        return self.name

    def get_sprite_index(self):
        return self.sprite_index


class NPC_Blob(Base_NPC):

    def __init__(self, friendly=False):
        self.name = "Blobman"
        self.max_hp = 6
        self.hp = 6
        self.power = 3
        self.evasion = 10
        self.defense = 0
        self.alive = True
        self.xp = 100
        self.friendly=friendly

        if friendly:
            self.sprite_index = 9
        else:
            self.sprite_index = 18

class NPC_Muscle_Blob(Base_NPC):

    def __init__(self, friendly=False):
        self.name = "Muscle Blobman"
        self.max_hp = 14
        self.hp = 14
        self.power = 8
        self.defense = 1
        self.evasion = 0
        self.alive = True
        self.xp = 15
        self.friendly=friendly

        if friendly:
            self.sprite_index = 11
        else:
            self.sprite_index = 20

class NPC_Dynamic_Blob(Base_NPC):

    def __init__(self, stat_points, friendly=False):
        self.friendly = friendly
        self.stat_points = stat_points # total stat points will determine xp given

        # stat points are randomly allocated
        self.arm = 0
        self.leg = 0
        self.body = 0
        self.mind = 0
        for i in range(0, stat_points):
            temp_stat = np.random.randint(0,4)
            if temp_stat == 0:
                self.arm += 1
            elif temp_stat == 1:
                self.leg += 1
            elif temp_stat == 2:
                self.body += 1
            elif temp_stat == 3:
                self.mind += 1

        # determine name & sprite based on stats
        # name is based on highest stat, sprite is based on all sprites like player
        new_index = self.arm/np.maximum(1,self.arm) + 2*self.leg/np.maximum(1,self.leg) + 4*self.mind/np.maximum(1,self.mind)
        if self.friendly:
            self.sprite_index = PLAYER_SPRITE_INDEX_LIST[int(new_index)] + 9
        else:
            self.sprite_index = PLAYER_SPRITE_INDEX_LIST[int(new_index)] + 18

        self.name = "Blobman"
        temp_highest_stat = 0
        if self.arm > temp_highest_stat:
            self.name = "Armed Blobman"
            temp_highest_stat = self.arm
        if self.leg > temp_highest_stat:
            self.name = "Legged Blobman"
            temp_highest_stat = self.leg
        if self.body > temp_highest_stat:
            self.name = "Full Body Blobman"
            temp_highest_stat = self.body
        if self.mind > temp_highest_stat:
            self.name = "Brainman"

        self.max_hp = 8 + self.body * 3
        self.hp = self.max_hp
        self.max_mana = 8 + self.mind * 4
        self.mana = self.max_mana
        self.temp_mana = self.mana
        self.mana_regen = .2 + self.mind *.1
        self.defense = 0 + self.arm//2 + self.body//2
        self.evasion = np.maximum(0, 10 + self.leg - self.body//2)
        self.power = 4 # TODO: REPLACE WITH ACTION BASED ON STATS
        self.alive = True

        self.xp = self.stat_points * 4

        def update_passive(self):
            self.temp_mana = np.minimum(self.temp_mana + self.mana_regen, self.max_mana)
            self.mana = int(np.floor(self.temp_mana))
