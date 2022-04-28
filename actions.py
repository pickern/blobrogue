from entity import Entity
import numpy as np

class Base_Attack():
    entity: Entity

    def __init__(self, parent):
        self.requirements = np.array[0, 0, 0, 0] # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = parent # parent should be an entity, used for accessing stats
        self.name = "Base Attack"
        self.cost = 0
        self.aoe = 0
        self.base_damage = 0
        self.accuracy = 1 # between 0 and 1, 1 is max accuracy
        self.range = 1 # range 1 => melee, range > 1 => ranged

    def get_aoe(self):
        return self.aoe

    def get_cost(self):
        return self.cost

    def get_requirements(self):
        return self.requirements

    def get_name(self):
        return self.name

    def get_range(self):
        return self.range

    def get_accuracy(self):
        # attack features that scale with stats can be implemented in these functions
        return self.accuracy

    def get_damage(self):
        # attack features that scale with stats can be implemented in these functions
        return self.base_damage

##### INATE/LEVEL UP ABILITIES #####
class Attack_Flail(Base_Attack):

    def __init__(self, parent):
        self.requirements = np.array([0, 0, 0, 0]) # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = parent # parent should be class_type, used for accessing stats
        self.name = "Flail"
        self.cost = 0
        self.aoe = 0
        self.base_damage = 4
        self.accuracy = .7 # between 0 and 1, 1 is max accuracy
        self.range = 1 # range = 1 => melee, range > 1 => ranged

    def get_damage(self):
        return self.base_damage + self.parent.get_body()

class Attack_Shoot(Base_Attack):

    def __init__(self, parent):
        self.requirements = np.array([0, 0, 0, 0]) # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = parent # parent should be class_type, used for accessing stats
        self.name = "Shoot"
        self.cost = 2
        self.aoe = 0
        self.base_damage = 4
        self.accuracy = .7 # between 0 and 1, 1 is max accuracy
        self.range = 7 # range = 1 => melee, range > 1 => ranged

    def get_damage(self):
        return self.base_damage + self.parent.get_body()

class Attack_Blast(Base_Attack):

    def __init__(self, parent):
        self.requirements = np.array([0, 0, 0, 0]) # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = parent # parent should be class_type, used for accessing stats
        self.name = "Blast"
        self.cost = 5
        self.aoe = 3
        self.base_damage = 4
        self.accuracy = .8 # between 0 and 1, 1 is max accuracy
        self.range = 4 # range = 1 => melee, range > 1 => ranged

    def get_damage(self):
        return self.base_damage + self.parent.get_body()

class Attack_Kick(Base_Attack):

    def __init__(self, parent):
        self.requirements = np.array([0, 1, 0, 0]) # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = parent # parent should be class_type, used for accessing stats
        self.name = "Kick"
        self.cost = 0
        self.aoe = 0
        self.base_damage = 4
        self.accuracy = .6 # between 0 and 1, 1 is max accuracy
        self.range = 1 # range  =1 => melee, range > 1 => ranged

    def get_damage(self):
        return self.base_damage + self.parent.get_leg()*2

class Attack_Punch(Base_Attack):

    def __init__(self, parent):
        self.requirements = np.array([1, 0, 0, 0]) # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = parent # parent should be class_type, used for accessing stats
        self.name = "Punch"
        self.base_damage = 4
        self.aoe = 0
        self.cost = 0
        self.accuracy = 1 # between 0 and 1, 1 is max accuracy
        self.range = 1 # range = 1 => melee, range > 1 => ranged

    def get_damage(self):
        return self.base_damage + self.parent.get_arm()

class Attack_None(Base_Attack):
    def __init__(self, parent):
        self.requirements = np.array([0, 0, 0, 0]) # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = parent # parent should be class_type, used for accessing stats
        self.name = "None"
        self.cost = 0
        self.aoe = 0
        self.base_damage = 0
        self.accuracy = 1 # between 0 and 1, 1 is max accuracy
        self.range = 1 # range = 1 => melee, range > 1 => ranged

    def get_damage(self):
        return 0

##### ITEM ACTIONS #####
class Item_Throw(Base_Attack):
    def __init__(self, item):
        self.requirements = item.get_throw_requirements() # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = None # parent should be class_type, used for accessing stats. FOR ITEMS WILL BE ASSIGNED ON PICKUP.
        self.name = item.get_name()
        self.cost = 0
        self.aoe = 0
        self.weight = item.get_weight()
        self.base_damage = item.get_thrown_damage()
        self.accuracy = 1 # between 0 and 1, 1 is max accuracy
        self.range = 1 # range = 1 => melee, range > 1 => ranged. range will be calced from weight.

    def get_damage(self):
        # TODO: test & refine damage calc
        if self.parent:
            return int((self.base_damage*self.parent.get_arm())/self.weight)
        else:
            return self.base_damage

    def get_range(self):
        # TODO: test & refine damage calc
        if self.parent:
            return int(2 + np.minimum(6, 2*self.parent.get_arm()/self.weight))
        else:
            return 2

class Item_Wield(Base_Attack):
    def __init__(self, parent):
        self.requirements = np.array([0, 0, 0, 0]) # arm, leg, body, mind respectively. min stats to unlock this ability
        self.parent = parent # parent should be class_type, used for accessing stats
        self.name = "None"
        self.cost = 0
        self.aoe = 0
        self.base_damage = 0
        self.accuracy = 1 # between 0 and 1, 1 is max accuracy
        self.range = 1 # range = 1 => melee, range > 1 => ranged

    def get_damage(self):
        return 0

##### SPELL ACTIONS #####
class Spell_Attack(Base_Attack):
    entity: Entity

    def __init__(self, parent):
        self.parent = parent # parent should be an entity, used for accessing sta
        self.name = "Spell Attack"
        self.base_damage = 0
        self.accuracy = 1
        self.range = 1 # range in euclidian distance
        self.cost = 1 # mana cost
        self.area = 1 # aoe diameter

    def get_cost(self):
        return self.cost

    def get_area(self):
        return self.area
