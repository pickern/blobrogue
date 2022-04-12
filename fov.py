import numpy as np
import floor
import mapgen
import sys

# FOV constants
FOV_UNSEEN = 0 # hidden tiles
FOV_VISIBLE = 1 # visible tiles
FOV_REVEALED = 2 # tiles that have been seen but not in current FOV

class Slope:
    # slope class for convenient vector comparison. represents a vector with slope y/x coming from origin
    def __init__(self, y, x):
        self.y = y
        self.x = x

    def greater(self, y, x):
        return self.y*x > self.x*y

    def greater_or_equal(self, y, x):
        return self.y*x >= self.x*y

    def less(self, y, x):
        return self.y*x < self.x*y

    def less_or_equal(self, y, x):
        return self.y*x <= self.x*y

def get_distance(x, y):
    # returns distance between x and y coordinate and origin (treated as (0,0))
    return np.sqrt(x**2 + y**2)

def blocks_light(x, y, octant, origin, trans_map):
    # accepts x and y coordinates of a tile and determines if it blocks light
    nx = origin[0]
    ny = origin[1]
    # adjust coordinate for correct octant
    if octant == 0:
        nx += x
        ny -= y
    elif octant == 1:
        nx += y
        ny -= x
    elif octant == 2:
        nx -= y
        ny -= x
    elif octant == 3:
        nx -= x
        ny -= y
    elif octant == 4:
        nx -= x
        ny += y
    elif octant == 5:
        nx -= y
        ny += x
    elif octant == 6:
        nx += y
        ny += x
    elif octant == 7:
        nx += x
        ny += y

    # check in bounds, out of bounds treated as opaque
    if nx < trans_map.shape[0] and ny < trans_map.shape[1]:
        return trans_map[int(nx)][int(ny)] == 1
    else:
        return True

def set_visible(x, y, octant, origin, vis_map):
    nx = origin[0]
    ny = origin[1]

    # adjust coordinate for octant
    if octant == 0:
        nx += x
        ny -= y
    elif octant == 1:
        nx += y
        ny -= x
    elif octant == 2:
        nx -= y
        ny -= x
    elif octant == 3:
        nx -= x
        ny -= y
    elif octant == 4:
        nx -= x
        ny += y
    elif octant == 5:
        nx -= y
        ny += x
    elif octant == 6:
        nx += y
        ny += x
    elif octant == 7:
        nx += x
        ny += y

    # make visible if in bounds, ignore out of bounds
    if nx < vis_map.shape[0] and ny < vis_map.shape[1]:
        vis_map[int(nx)][int(ny)] = FOV_VISIBLE
    return vis_map

def compute(octant, origin, range_limit, x_init, top, bottom, floor, vis_map):
    # computes visiblity for tiles within range_limit in given octant
    x = x_init
    trans_map = floor.get_map().get_trans_map()

    # computes outward starting with adjacent tiles to origin
    while x <= range_limit:
        # compute y coordinates for top and bottom of sector with top > bottom
        # start with top
        topY = 0
        if top.x == 1: # topY = 1 until top vector collides with something
            topY = x
        else: # top.x < 1, calculate topY based on new slope
            topY = np.floor(((x*2-1) * top.y + top.x)/(top.x*2))
            if blocks_light(x, topY, octant, origin, trans_map):
                if top.greater_or_equal(topY*2+1, x*2) and not blocks_light(x, topY+1, octant, origin, trans_map):
                    # if beveled top left, increase topY. else light is blocked.
                    topY += 1
            else: # light is not blocked, light can pass
                ax = x*2
                if blocks_light(x+1, topY+1, octant, origin, trans_map):
                    # if tile above and to the right is a wall, use bottom right
                    ax += 1
                if top.greater(topY*2+1, ax):
                    topY += 1

        # then compute bottom analogously
        bottomY = 0
        if bottom.y == 0: # bottom is 0 until it collides with something
            bottomY = 0
        else: # bottom > 0, compute bottom from adjusted slope
            bottomY = np.floor(((x*2-1) * bottom.y + bottom.x)/(bottom.x*2))
            if bottom.greater_or_equal(bottomY*2+1, x*2) and blocks_light(x, bottomY, octant, origin, trans_map) and not blocks_light(x, bottomY+1, octant, origin, trans_map):
                bottomY += 1

        # now compute visibility for all tiles in column at given x coordinate
        wasOpaque = -1 # -1 = not applicable, 0 = was not opaque, 1 = was opaque
        y = topY
        while y >= bottomY:

            if range_limit < 0 or get_distance(x, y) <= range_limit:
                isOpaque = blocks_light(x, y, octant, origin, trans_map)

                # all tiles in column are assumed to be visible
                isVisible = ((y != topY or top.greater_or_equal(y, x)) and (y != bottomY or bottom.less_or_equal(y, x)))

                # set visibility
                if isVisible:
                    vis_map = set_visible(x, y, octant, origin, vis_map)

                # now check to see if we need to continue, update top/bottom vectors, etc
                if x != range_limit:
                    if isOpaque:
                        if wasOpaque == 0: # found clear-to-opaque transition
                            nx = x*2
                            ny = y*2+1
                            if top.greater(ny, nx): # maintain top > bottom
                                if(y == bottomY): # adjust bottom if we're at bottom of sector
                                    bottom = Slope(ny,nx)
                                    break
                                else: # if we're in the middle of the sector, recurse. we don't adjust bottom if there's a chance for an opaque-to-clear transition below.
                                    vis_map = compute(octant, origin, range_limit, x+1, top, Slope(ny,nx), floor, vis_map)
                            else: # if bottom >= top, sector is empty
                                if (y == bottomY):
                                    return vis_map
                        # if no transition, continue as is
                        wasOpaque = 1

                    else: # not opaque/clear
                        if wasOpaque > 0: # found clear-to-opaque transition
                            nx = x*2
                            ny = y*2+1
                            if bottom.greater_or_equal(ny, nx): # return if new top will hit bottom
                                return vis_map
                            top = Slope(ny,nx) # adjust top if still above bottom
                        wasOpaque = 0
                        # if no transition, continue as is
            y -= 1
            # end y while

        # wasOpaque = -1 implies we hit range limit or sector is empty, so break
        # wasOpaque = 1 implies we recursed and didn't find a transition back to clear, so recursion has aready done the work
        if wasOpaque != 0:
            break

        x += 1
        # end x while
    return vis_map

def calc_fov(origin, range_limit, the_floor):
    # will need to use transparency map, bevel map, and visibility map
    # public facing function, calcs fov from origin out to distance rangelimit
    # adapted from http://www.adammil.net/blog/v125_roguelike_vision_algorithms.html#mycode
    # thanks adam milazzo <3 <3 <3
    map = the_floor.get_map()
    vis_map = np.zeros(map.get_map().shape)
    vis_map[origin[0]][origin[1]] = FOV_VISIBLE

    # compute for each octant (45 degree wedge)
    # view cones can be made by restricting number of octants
    for octant in range(0,8):
        vis_map = compute(octant, origin, range_limit, 1, Slope(1,1), Slope(0,1), the_floor, vis_map)

    return vis_map
