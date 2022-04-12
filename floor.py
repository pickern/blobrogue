import numpy as np
import mapgen
import entity

class Floor():
    # hold map and entity info for particular floor
    def __init__(self, map, depth, entities):
        self.map = map
        self.entities = entities
        self.depth = depth
        self.entity_map = np.zeros(map.shape())

    def get_entity_at_position(self, x, y):
        for ent in self.entities:
            pos = ent.get_pos()
            if pos == (x,y):
                return ent

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

    def get_depth(self):
        return self.depth
