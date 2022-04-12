import numpy as np
import random as rand
import sys

# Terrain constants
MAP_WALL = 0
MAP_FLOOR = 1
MAP_DOOR = 2
MAP_HALL = 3
MAP_UP_STAIR = 4
MAP_DOWN_STAIR = 5

# values for terminal output
DISPLAY_VALUES = {
    MAP_WALL : " ",
    MAP_FLOOR: ".",
    MAP_DOOR: "+",
    MAP_HALL: "#",
    MAP_UP_STAIR: "<",
    MAP_DOWN_STAIR: ">"
}

class Map:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.map, self.node_list, self.rooms_list, self.entrance, self.exit, self.trans_map, self.masked_map, self.revealed_map = make_map(x,y)

    def get_map(self):
        return self.map

    def get_rooms(self):
        return self.rooms_list

    def get_trans_map(self):
        return self.trans_map

    def get_masked_map(self):
        return self.masked_map

    def get_revealed_map(self):
        return self.revealed_map

    def update_revealed_map(self, vis_map):
        self.revealed_map = np.clip((self.revealed_map + vis_map), 0, 1)
        return self.revealed_map

    def shape(self):
        return self.x, self.y

    def nodes(self):
        return self.nodes_list

    def get_entrance(self):
        return self.entrance

    def get_exit(self):
        return self.exit

def make_map(mapx, mapy, num_nodes = 16, num_rooms = 16):
    # Parameters:
    #   mapx - int, x dimension
    #   mapy - int, y dimension

    # initialize map
    map = np.zeros((mapx,mapy), dtype=int)

    # make nodes
    #   nodes are anchor points for hallway/room generation
    node_list_x = np.random.randint(10,mapx-10,(1,num_nodes))
    node_list_y = np.random.randint(10,mapy-10,(1,num_nodes))
    node_list = (node_list_x.flatten(),node_list_y.flatten())

    # connect nodes
    i0 = 0
    while i0 < num_nodes:
        map = connect_nodes(map,node_list[0][i0], node_list[1][i0], node_list[0][(i0+1)%num_nodes], node_list[1][(i0+1)%num_nodes])
        i0 += 1

    # draw nodes
    for i in range(0,num_nodes):
        map[node_list[0][i]][node_list[1][i]] = MAP_HALL
        i += 1

    # add rooms
    map, rooms_list = add_rooms(num_rooms, map, node_list)

    # add stairs
    # TODO: make more interesting
    map_with_stairs = np.copy(map)
    entrance = (node_list[0][0], node_list[1][0])
    map_with_stairs[entrance] = MAP_UP_STAIR
    exit = (node_list[0][1], node_list[1][1])
    map_with_stairs[exit] = MAP_DOWN_STAIR

    trans_map = make_transparency_map(map)
    masked_map = make_wall_tile_map(map_with_stairs)
    revealed_map = map = np.zeros((mapx,mapy), dtype=int)

    return map_with_stairs, node_list, rooms_list, entrance, exit, trans_map, masked_map, revealed_map

def make_transparency_map(map):
    # implemented so that only walls currently block sight
    # opaque = 1, open = 0
    trans_map = np.zeros(map.shape)
    x = 0
    y = 0
    for x in range(0,map.shape[0]):
        for y in range(0,map.shape[1]):
            if map[x][y] == MAP_WALL:
                trans_map[x][y] = 1
            else:
                trans_map[x][y] = 0

    return trans_map

def make_wall_tile_map(map):
    # determine what tiles to display for each wall
    mult_mask = np.zeros((3,3))
    mult_mask[0][1] = 2
    mult_mask[1][0] = 1
    mult_mask[1][2] = 8
    mult_mask[2][1] = 4

    # make wall map, 1 for walls and 0 for everything else
    wall_map = np.copy(map)
    for x in range(0,map.shape[0]):
        for y in range(0,map.shape[1]):
            if map[x][y] == 0:
                wall_map[x][y] = 1
            else:
                wall_map[x][y] = 0

    # unique value for each arrangement of walls on the 4 cardinals from given point, 0-15s
    masked_map = 15*np.ones(map.shape)
    for x in range(0,wall_map.shape[0]-2):
        for y in range(0,wall_map.shape[1]-2):
            array_slice = wall_map[x:x+3,y:y+3]
            masked_map[x+1][y+1] = np.sum(np.multiply(array_slice,mult_mask), dtype=np.int32)

    return masked_map.astype(np.int)


def connect_nodes(map, node1x, node1y, node2x, node2y):
    # straight horizontal lines from each node connected by a vertical line at random breakpoint
    x_dif = node2x - node1x
    y_dif = node2y - node1y
    break_point = rand.randint(0,np.absolute(x_dif))
    # horiztonal portions
    for i1 in range(0,np.absolute(x_dif)):
        if i1 < break_point:
            temp_y = node1y
        else:
            temp_y = node2y
        map[node1x + i1*np.sign(x_dif)][temp_y] = MAP_HALL
    # vertical portion
    for i1 in range(0,np.absolute(y_dif)):
        map[node1x + break_point*np.sign(x_dif)][node1y + i1*np.sign(y_dif)] = MAP_HALL

    return map

def add_rooms(n, map, nodes_list):
    # places n rooms at the first n nodes
    # parameters:
    #   n - number of rooms (int, less than length of nodes_list)
    #   map - the map, 2d array
    #   nodes_list = list of node coodinates used for room locations

    rooms_list = []

    for iter in range(n):
        # size & location
        width = rand.randint(3, 10)
        height = rand.randint(3, 10)
        loc_x = nodes_list[0][iter]
        loc_y = nodes_list[1][iter]

        # shift from the node point to make it more interesting
        x_offset = rand.randint(0,width-1)
        y_offset = rand.randint(0,height-1)

        # carve out rooms
        for x in range(0,width):
            for y in range(0,height):
                if (x+loc_x-x_offset) < map.shape[0] and (x+loc_x-x_offset) >= 0 and (y+loc_y-y_offset) < map.shape[1] and (y+loc_y-y_offset) >= 0:
                    map[x+loc_x - x_offset][y+loc_y - y_offset] = MAP_FLOOR

        # add to room_list
        rooms_list.append((loc_x - x_offset, loc_y - y_offset, width, height))

    return map, rooms_list

def printmap(map):
# prints out map to terminal for testing
    for row in map:
        for col in row:
            print(DISPLAY_VALUES[col], end="")
        print()

def main():
    printmap(make_map(50, 100))

if __name__ == "__main__":
    main()
