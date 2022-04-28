import numpy as np
import mapgen
import entity
import item

class Floor():
    # hold map and entity info for particular floor
    def __init__(self, map, depth, entities):
        self.map = map
        self.entities = entities
        self.depth = depth
        self.entity_map = np.zeros(map.shape())
        self.item_list = []
        self.item_map = np.zeros(map.shape())

    def get_entity_at_position(self, x, y):
        for ent in self.entities:
            pos = ent.get_pos()
            if pos == (x,y) and ent.class_type.is_alive():
                return ent
        return None

    def get_item_at_position(self, x, y):
        # TODO: handle multiple items on the same tile
        for item in self.item_list:
            pos = item.get_pos()
            if pos == (x,y):
                return item
        return None

    def add_item(self, new_item):
        self.item_list.append(new_item)
        pos = new_item.get_pos()
        self.item_map[pos[0]][pos[1]] = 1

    def remove_item(self, item):
        self.item_list.remove(item)
        pos = item.get_pos()
        self.item_map[pos[0]][pos[1]] = 0

    def get_item_list(self):
        return self.item_list

    def get_item_map(self):
        return self.item_map

    def get_map(self):
        return self.map

    def get_entity_map(self):
        return self.entity_map

    def get_entities(self):
        return self.entities

    def set_entities(self, new_entities):
        self.entities = new_entities
        return self.entities

    def set_entity_pos(self, entity, newx, newy):
        # clear old space
        current_pos = entity.get_pos()
        self.entity_map[current_pos[0]][current_pos[1]] = 0

        # set new position
        entity.set_pos(newx, newy)
        self.entity_map[newx][newy] = 1
        return self.entity_map

    def remove_entity_from_entity_map(self, entity):
        pos = entity.get_pos()
        self.entity_map[pos[0]][pos[1]] = 0

    def get_depth(self):
        return self.depth
