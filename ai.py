from entity import Entity
import mapgen
import numpy as np
import tcod
import classes

STATE_WANDERING = 0
STATE_SEARCHING = 1
STATE_ATTACKING = 2

class Base_Component:
    entity: Entity

class Monster_Basic(Base_Component):

    def __init__(self):
        self.state = STATE_WANDERING
        self.target = (-1,-1)

    def take_turn(self, player):
        # returns message to display and int for goodness of message (if applicable)
        #   0 = neutral message, 1 = good message, 2 = bad message
        # takes player to get position, probably change this later
        # assume it sees player if player sees it

        # update state
        if self.owner.is_visible():
            self.state = STATE_ATTACKING
        else:
            if self.state == STATE_ATTACKING or self.state == STATE_SEARCHING:
                self.state = STATE_SEARCHING
            else:
                self.state = STATE_WANDERING

        # take action
        if self.state == STATE_WANDERING:
            # pick a random direction, if tile is clear, move there
            direction = np.random.randint(0,8)*45
            current_pos = self.owner.get_pos()
            new_x, new_y = rotate(1,0,direction)
            new_x += current_pos[0]
            new_y += current_pos[1]
            wall_map = self.owner.floor.get_map().get_map()
            entity_map = self.owner.floor.get_entity_map()

            # move if available
            if wall_map[new_x][new_y] != mapgen.MAP_WALL and entity_map[new_x][new_y] == 0:
                self.owner.floor.set_entity_pos(self.owner, new_x, new_y)

        elif self.state == STATE_ATTACKING:
            # currently, if player is visible, there should be a viable square to move toward them
            # move toward player
            # get relative position
            self.target = player.get_pos()
            current_pos = self.owner.get_pos()
            dx = self.target[0] - current_pos[0]
            dy = self.target[1] - current_pos[1]

            # if player is adjacent ie distance < 1.5, attack
            if np.sqrt(dx**2 + dy**2) < 1.5:
                to_hit = np.random.randint(0,100)
                if to_hit <= 100 - player.class_type.get_evasion():
                    damage, newhp = player.class_type.change_hp(-1*self.owner.class_type.power)
                    return "{name} strikes for {dam} damage!".format(name = self.owner.get_name(), dam = damage), 2
                else:
                    return "{name} swings and misses".format(name = self.owner.get_name()), 1

            # otherwise move
            else:
                # get step direction
                dx_step = np.sign(dx)
                dy_step = np.sign(dy)

                # check to see if tile is open, if so move
                wall_map = self.owner.floor.get_map().get_map()
                entity_map = self.owner.floor.get_entity_map()

                # step directions for tiles to left and right of ideal tile
                dx_left, dy_left = rotate(dx_step, dy_step, 45)
                dx_right, dy_right = rotate(dx_step, dy_step, -45)

                # check tiles for good move
                if wall_map[current_pos[0] + dx_step][current_pos[1] + dy_step] != mapgen.MAP_WALL and entity_map[current_pos[0] + dx_step][current_pos[1] + dy_step] == 0:
                    self.owner.floor.set_entity_pos(self.owner, current_pos[0] + dx_step, current_pos[1] + dy_step)
                # check left
                elif wall_map[current_pos[0] + dx_left][current_pos[1] + dy_left] != mapgen.MAP_WALL and entity_map[current_pos[0] + dx_left][current_pos[1] + dy_left] == 0:
                        self.owner.floor.set_entity_pos(self.owner, current_pos[0] + dx_left, current_pos[1] + dy_left)
                    # check right
                elif wall_map[current_pos[0] + dx_right][current_pos[1] + dy_right] != mapgen.MAP_WALL and entity_map[current_pos[0] + dx_right][current_pos[1] + dy_right] == 0:
                        self.owner.floor.set_entity_pos(self.owner, current_pos[0] + dx_right, current_pos[1] + dy_right)
                # else do nothing

        elif self.state == STATE_SEARCHING:
            # keep moving toward last target, reverting to wandering once target reached
            # get relative position
            current_pos = self.owner.get_pos()
            dx = self.target[0] - current_pos[0]
            dy = self.target[1] - current_pos[1]

            # if reached last target, go back to wandering
            if np.sqrt(dx**2 + dy**2) < 1.5:
                self.state = STATE_WANDERING

            # otherwise move
            else:
                # get step direction
                dx_step = np.sign(dx)
                dy_step = np.sign(dy)
                # check to see if tile is open, if so move
                wall_map = self.owner.floor.get_map().get_map()
                entity_map = self.owner.floor.get_entity_map()

                # step directions for tiles to left and right of ideal tile
                dx_left, dy_left = rotate(dx_step, dy_step, 45)
                dx_right, dy_right = rotate(dx_step, dy_step, -45)

                # check tiles for good move
                # TODO: still move if entity on square is non_blocking
                if wall_map[current_pos[0] + dx_step][current_pos[1] + dy_step] != mapgen.MAP_WALL and entity_map[current_pos[0] + dx_step][current_pos[1] + dy_step] == 0:
                    self.owner.floor.set_entity_pos(self.owner, current_pos[0] + dx_step, current_pos[1] + dy_step)
                # check left
                elif wall_map[current_pos[0] + dx_left][current_pos[1] + dy_left] != mapgen.MAP_WALL and entity_map[current_pos[0] + dx_left][current_pos[1] + dy_left] == 0:
                    self.owner.floor.set_entity_pos(self.owner, current_pos[0] + dx_left, current_pos[1] + dy_left)
                # check right
                elif wall_map[current_pos[0] + dx_right][current_pos[1] + dy_right] != mapgen.MAP_WALL and entity_map[current_pos[0] + dx_right][current_pos[1] + dy_right] == 0:
                    self.owner.floor.set_entity_pos(self.owner, current_pos[0] + dx_right, current_pos[1] + dy_right)
                # else do nothing
        return None

def find_path(entity, floor, target):
    # TODO: actual pathfinding
    pass

def rotate(x, y, degrees=45):
    # rotates vector (x,y) by degrees, rounds vector values to 1
    # needs refining if to be used in general cases, rint is unreliable

    theta = np.deg2rad(degrees)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    new_x = np.rint(x*cos_theta - y*sin_theta).astype(int)
    new_y = np.rint(x*sin_theta + y*cos_theta).astype(int)
    return new_x, new_y
