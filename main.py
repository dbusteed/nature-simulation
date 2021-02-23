#!/usr/bin/python3.8


# only using standard libraries, wahoo!
from random import randint, choice, random, shuffle
from statistics import mean
from time import sleep
from os import system
from sys import exit
import traceback
from importlib import import_module



#----------------------#
#                      #
#   SIMULATION SETUP   #
#                      #
#----------------------#

# colors for printing to the console.
# replace these with blank strings
# to disable color support (but make
# sure to edit the tiles below so that
# they are distinguishable)
#
BG_BLUE = '\033[44m'
BG_GREEN = '\033[42m'
BG_RED = '\033[41m'
BG_CYAN = '\033[46m'
BG_MAGENTA = '\033[45m'
BG_YELLOW = '\033[43m'
FG_WHITE = '\033[1m'
FG_RED = '\033[1;31m'
FG_YELLOW = '\033[1;33m'
FG_MAGENTA = '\033[1;35m'
FG_CYAN = '\033[1;36m'
NC = '\033[0m'

# different tiles for the grid
WATER_TILE = f'{BG_BLUE} {NC}'
PLANT_TILE = f'{BG_GREEN} {NC}'
OPEN_TILE = " "

# grid / world dimensions
WORLD_X = 30
WORLD_Y = 10
WORLD_AREA = WORLD_X * WORLD_Y

# initial amount of water and plants.
# when editing, change the demoninator of
# this expression:
#   Ex: 10% = int(1 / .10) = 1 out of 10
#
WATER_FACTOR = int(1 / .03)
PLANT_FACTOR = int(1 / .05)

#
# settings for the nomads
#
NOMAD_COUNT = 40        # number of starting nomads
MUTATION_CHANCE = 0.9   # pct chance offspring will mutate
REPRODUCTION_CHANCE = 0.5   # pct chance females will reproduce when meeting a male
REPRODUCTION_CHANCE_DECREASE = 0.05
GESTATION = 30
BASE_SENSE = 4     # starting sense value for nomads   
BASE_STAMINA = 30  # starting stamina value for nomads
BASE_TRIBAL = 5

# plant stuff
#  - how often plants regrow (1 out of X times)
#  - how many plants regrow each time
#  - limit for how many plants grow in the world
#    
PLANT_GROWTH_RATE = 8
PLANT_GROWTH_AMT = 10
MAX_PLANT_PCT = .30

# output stuff
#  - name of the output file
#  - how often data is written
#     (lower number for more frequent writes)
#
OUTPUT_FILE = "stats.csv"
OUTPUT_WRITE_INTERVAL = 20

# speed of simulation
# (i had issues with lower than 0.1)
SPEED = .15

MAP_DIR = "maps"

# When set to None, the map/world will be randomly
# generated. To specfiy other maps, set MAP to 
# a string of a filename found in the maps directory.
# Example: for maps/river.py, set MAP to "river"
MAP = "swirl"

DEBUG = False


#-----------------#
#                 #
#   NOMAD CLASS   #
#                 #
#-----------------#

class Nomad:
    
    def __init__(self, pos, tob=0, sense=BASE_SENSE, stamina=BASE_STAMINA, tribal=BASE_TRIBAL, tribe=None, allegiance=0):    
        
        # attributes for basic actions
        self.pos = pos
        self.thirst = 0
        self.hunger = 0
        self.target = None
        self.goal = 'drink'
        self.tribes = {
            None: FG_WHITE,
            'red': FG_RED,
            'cyan': FG_CYAN,
            'magenta': FG_MAGENTA,
            'yellow': FG_YELLOW
        }
        self.areas = {
            'none': '',
            'red': BG_RED,
            'cyan': BG_CYAN,
            'magenta': BG_MAGENTA,
            'yellow': BG_YELLOW
        }
        self.tribe = tribe
        self.goals = {
            'eat': PLANT_TILE,
            'drink': WATER_TILE
        }

        # tribe stuff
        self.allegiance = allegiance

        self.tribal = tribal
        
        # Time Of Birth, and somewhat random 
        # age of adulthood
        self.tob = tob
        self.adult_age = randint(40,60)
        
        # attribues passed down that from the 
        # parents, can be mutated
        self.sense = sense
        self.stamina = stamina
        
        # these are set to static numbers for now, 
        # but can use the lines below instead, that 
        # base these off of the sense and stamina,
        # forcing the evolution process to deal 
        # with a trade-off
        #
        self.fatigue = 1
        base_lifespan = 800 + (self.allegiance * 10)

        # self.fatigue = sense // 2
        # base_lifespan = int((-10 * stamina) + 1300)
        
        # a little randomness in the lifespan or else an entire
        # generation dies at the same time
        self.lifespan = randint(base_lifespan-100, base_lifespan+100)

        # genders are randomly assigned at "birth",
        # and have different attributes for the females
        if randint(1,2) == 1:
            self.gender = 'male'
            self.marker = f'{self.tribes[self.tribe]}m{NC}'
        else:
            self.gender = 'female'
            self.marker = f'{self.tribes[self.tribe]}f{NC}'
            self.reproduction_chance = REPRODUCTION_CHANCE
            self.pregnant = False
            self.gestation = 0
            self.child_genes = {}


    # this handles everything that the nomad does,
    # and is called for each nomad in the main loop
    #
    def tick(self, t):

        # status object for returning to the main process
        status = {'dead': False, 'offspring': None}

        # the nomad grows up if they reach their adult_age
        if (t - self.tob) == self.adult_age:
            self.marker = f'{self.tribes[self.tribe]}M{NC}' if self.gender == 'male' else f'{self.tribes[self.tribe]}F{NC}'

        # reproduction stuff for female nomads
        if self.marker.endswith(f"F{NC}") or self.marker.endswith(f"P{NC}"):
            
            # if they are pregnant, either gestate the child more,
            # or give birth to it by passing the genes into the status object
            if self.pregnant:
                if self.gestation:
                    self.gestation -= 1
                else:
                    around = self._get_surroundings()
                    if OPEN_TILE in [a[1] for a in around]:
                        self.child_genes['pos'] = [a[0] for a in around if a[1] == OPEN_TILE][0]
                        status['offspring'] = self.child_genes
                        self.marker = f'{self.tribes[self.tribe]}F{NC}'
                        self.reproduction_chance -= REPRODUCTION_CHANCE_DECREASE
                    self.pregnant = False

            # if they aren't pregnant, first check if they are willing to mate
            elif random() <= self.reproduction_chance:
                
                # get the surroundings
                around = self._get_surroundings()
                
                # check if an adult male is nearby...
                if 'Nomad' in [a[1].__class__.__qualname__ for a in around]:
                    anis = [a for a in around if a[1].__class__.__qualname__ == 'Nomad']
                    if [a for a in anis if a[1].marker.endswith(f"M{NC}")]:
                        
                        # ... if so, mix the genes with the father, and
                        # start the pregnancy process. also handle the allegiances
                        # to the tribe
                        father = [a[1] for a in anis if a[1].marker.endswith(f"M{NC}")][0]

                        #
                        #   COMMENT OUT THIS SECTION TO DISABLES TRIBES
                        #

                        if not self.tribe and not father.tribe:
                            random_tribe = choice(list(self.tribes.keys())[1:])
                            self.tribe = random_tribe
                            self.allegiance = 1
                            father.tribe = random_tribe
                            father.marker = f'{self.tribes[self.tribe]}M{NC}'
                            father.allegiance = 1
                        
                        elif not self.tribe:
                            self.tribe = father.tribe
                            self.allegiance = 1
                        
                        elif not father.tribe:
                            father.tribe = self.tribe
                            father.marker = f'{self.tribes[self.tribe]}M{NC}'
                            father.allegiance = 1

                        elif self.tribe == father.tribe:
                            self.allegiance += 1
                            father.allegiance += 1

                        else:
                            self.allegiance -= 1
                            father.allegiance -= 1
                            
                            if self.allegiance <= 0:
                                self.tribe = None
                                self.allegiance = 0

                            if father.allegiance <= 0:
                                father.tribe = None
                                father.marker = f'{self.tribes[self.tribe]}M{NC}'
                                father.allegiance = 0

                        #
                        #   END OF TRIBE SECTION
                        #
                            
                        self.child_genes = {
                            'sense': self._mix_genes(father, 'sense'),
                            'stamina': self._mix_genes(father, 'stamina'),
                            'tribal': min(max(1, self._mix_genes(father, 'tribal')), 10),
                            'tribe': self.tribe,
                            'allegiance': min(max(1, self.allegiance), 10)
                        }
                        self.pregnant = True
                        self.gestation = GESTATION
                        self.marker = f'{self.tribes[self.tribe]}P{NC}'


        # movement stuff
        #   first check if the nomad has a target 
        if self.target:
            diff = (self.target[0] - self.pos[0], self.target[1] - self.pos[1])

            # if they next to the target
            if abs(diff[0]) + abs(diff[1]) == 1:
                func = getattr(self, self.goal)
                func() # this will either be `eat()` or `drink()`
                
                # get a new goal by checking if the nomad
                # is more hungry, or more thirsty
                self.target = None
                self.goal = max([('eat',self.hunger), ('drink',self.thirst)], key=lambda x: x[1])[0]
                
            # if not next to target, keep moving
            else:
                if abs(diff[0]) > abs(diff[1]):
                    step = int(diff[0] / abs(diff[0]))
                    if self._is_open((self.pos[0]+step, self.pos[1])):
                        world[self.pos[0]][self.pos[1]] = OPEN_TILE
                        self.pos = (self.pos[0]+step, self.pos[1])
                        world[self.pos[0]][self.pos[1]] = self
                    else:
                        self.target = None

                else:
                    step = int(diff[1] / abs(diff[1]))
                    if self._is_open((self.pos[0], self.pos[1]+step)):
                        world[self.pos[0]][self.pos[1]] = OPEN_TILE
                        self.pos = (self.pos[0], self.pos[1]+step)
                        world[self.pos[0]][self.pos[1]] = self
                    else:
                        self.target = None

        # if they don't have a target, try to find a new one
        else:
            i = 1
            while (not self.target) and i <= self.sense:
                if self._is_target((i*1, 0)):
                    self.target = (self.pos[0]+(i*1), self.pos[1])
                elif self._is_target((i*-1, 0)):
                    self.target = (self.pos[0]+(i*-1), self.pos[1])
                elif self._is_target((0,i*1)):
                    self.target = (self.pos[0], self.pos[1]+(i*1))
                elif self._is_target((0,i*-1)):
                    self.target = (self.pos[0], self.pos[1]+(i*-1))
            
                i += 1
                
            # but if they couldnt find a target, just wander around
            i = 0
            wander = True
            mvmts = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            shuffle(mvmts)
            
            while wander and i < len(mvmts):
                new_pos = (self.pos[0] + mvmts[i][0], self.pos[1] + mvmts[i][1])
                if self._is_open(new_pos):
                    world[self.pos[0]][self.pos[1]] = OPEN_TILE
                    self.pos = new_pos
                    world[self.pos[0]][self.pos[1]] = self
                    wander = False
                i += 1

        
        # check if there is a rebellion
        #   the formula `y = -x + 11` ensures that when `tribal`
        #   is at 10, there is 1% chance to rebel, while when it is at
        #   1, there is a 10% chance of rebllion
        if self.tribe and randint(1, 5000) <= (-self.tribal) + 11:
            while True:
                new_tribe = choice(list(self.tribes.keys())[1:])
                if new_tribe != self.tribe:
                    break
            self.tribe = new_tribe
            self.marker = f'{self.tribes[self.tribe]}{"M" if self.gender == "male" else "F"}{NC}'
            self.allegiance = 10

        # CONSOLIDATE around = get_surroundings better
        around = self._get_surroundings()

        if self.tribe and self.allegiance == 10:
            for n in [n[1] for n in around if n[1].__class__.__qualname__ == 'Nomad']:
                if n.tribe != self.tribe:
                    n.hunger += 10
                    break
                
        # get thisty and hungry
        self.thirst += randint(0, self.fatigue)
        self.hunger += randint(0, self.fatigue)

        # check if the nomad died of hunger, thirst, or old age
        if self.thirst > self.stamina \
            or self.hunger > self.stamina \
            or ((t - self.tob) > self.lifespan) \
            or len([a[1] for a in around if a[1].__class__.__qualname__ == 'Nomad']) == 4:

            status['dead'] = True

        return status

    #
    # helper functions for reproducing and moving
    # around the grid
    #
    def _mix_genes(self, father, trait):
        spread = abs(getattr(self, trait) - getattr(father, trait))
        if spread == 0:
            spread = 1

        value = int((getattr(self, trait) + getattr(father, trait)) / 2)
        if random() < MUTATION_CHANCE:
            value = randint(value-spread, value+spread)

        return value

    def _is_open(self, new_pos):
        return ((new_pos[0] >= 0 and new_pos[0] < WORLD_Y) \
            and (new_pos[1] >= 0 and new_pos[1] < WORLD_X) \
            and (world[new_pos[0]][new_pos[1]] == OPEN_TILE))
    
    def _is_valid(self, new_pos):
        return ((new_pos[0] >= 0 and new_pos[0] < WORLD_Y) \
            and (new_pos[1] >= 0 and new_pos[1] < WORLD_X))

    def _is_target(self, mvmt):
        new_pos = (self.pos[0] + mvmt[0], self.pos[1] + mvmt[1])
        return ((new_pos[0] >= 0 and new_pos[0] < WORLD_Y) \
            and (new_pos[1] >= 0 and new_pos[1] < WORLD_X) \
            and (world[new_pos[0]][new_pos[1]] == self.goals[self.goal]))

    def _get_surroundings(self):
        ret = []
        for y,x in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if self._is_valid((self.pos[0]+y, self.pos[1]+x)):
                ret.append([
                    (self.pos[0]+y, self.pos[1]+x),
                    world[self.pos[0]+y][self.pos[1]+x]
                ])
        return ret

    #
    # basic nomad actions
    #
    def drink(self):
        self.thirst = 0

    def eat(self):
        world[self.target[0]][self.target[1]] = OPEN_TILE
        self.hunger = 0

    # useful for debugging
    def debug(self):
        o = 'Nomad:\n'
        o += f' POS: {self.pos},'
        o += f' THR: {self.thirst},'
        o += f' HGR: {self.hunger},'
        o += f' GOL: {self.goal},'
        o += f' TGT: {self.target},'
        o += f' SNS: {self.sense}\n'
        o += f' STM: {self.stamina},'
        o += f' LSP: {self.lifespan},'
        o += f' TRB: {self.tribe},'
        o += f' ALG: {self.allegiance}'
        return o

    #
    # this allows to print representation of the
    # Nomad object (the marker) easily
    #
    def __str__(self):
        return self.marker


#-------------------#
#                   #
#   BUILD THE MAP   #
#                   #
#-------------------#

if MAP:
    _map = import_module(MAP_DIR + "." + MAP)
    WORLD_X = _map._world_x
    WORLD_Y = _map._world_y
    WORLD_AREA = WORLD_X * WORLD_Y
    world = []
    for i in range(WORLD_Y):
        tiles = []
        for j in range(WORLD_X):
            if _map._world[i][j]:
                tiles.append(WATER_TILE)
            else:
                tiles.append(OPEN_TILE)
        world.append(tiles)

else:
    # create the "world" grid, and add some water tiles
    world = []
    for i in range(WORLD_Y):
        tiles = []
        for j in range(WORLD_X):
            if randint(1,WATER_FACTOR) == 1:
                tiles.append(WATER_TILE)
            else:
                tiles.append(OPEN_TILE) 
        world.append(tiles)

    # grab the coords for every water tile...
    water_tiles = [
        (ix,iy) for ix, row in enumerate(world)
        for iy, i in enumerate(row) if i == WATER_TILE]

    # ...and make each one a bigger body of water
    for ix,iy in water_tiles:
        try:
            world[ix][iy+1] = WATER_TILE
            world[ix][iy-1] = WATER_TILE
            world[ix+1][iy] = WATER_TILE
            world[ix-1][iy] = WATER_TILE
            world[ix+1][iy+1] = WATER_TILE
            world[ix-1][iy-1] = WATER_TILE
            world[ix-1][iy+1] = WATER_TILE
            world[ix+1][iy-1] = WATER_TILE
        except:
            pass

# next, grab the coords for the open spaces...
open_tiles = [
    (ix,iy) for ix, row in enumerate(world)
    for iy, i in enumerate(row) if i == OPEN_TILE]

# ...and put some plants there
plant_count = 0
for ix,iy in open_tiles:
    if randint(1,PLANT_FACTOR) == 1:
        world[ix][iy] = PLANT_TILE
        plant_count += 1

# finally, find the remaining open spots...
open_tiles = [
    (ix,iy) for ix, row in enumerate(world)
    for iy, i in enumerate(row) if i == OPEN_TILE]

# ...and put some nomads there!
nomads = []
a_count = 0
while a_count < NOMAD_COUNT:
    for ix,iy in open_tiles:
        if randint(1,50) == 1:
            nomads.append(Nomad((ix,iy)))
            a_count += 1

# limit the number of nomads to the 
# constant defined above
nomads = nomads[:NOMAD_COUNT]

# put the nomads on the map
for a in nomads:
    world[a.pos[0]][a.pos[1]] = a


#---------------#
#               #
#   MAIN LOOP   #
#               #
#---------------#

time = 0
clear = lambda: system('clear')

try:
    # file for writing simulation stats
    stats_file = open(OUTPUT_FILE, "w")
    stats_file.write(f"time,world area,plant count,population,female population,sense,stamina,allegiance,tribal\n")

    # continue simulation until all the nomads die,
    # or user hits Ctrl+c (see execption below)
    while len(nomads) > 0:

        # clear the sceen and print the map
        # if time % 2 == 0:
        clear()
        for i in range(WORLD_Y):
            for j in range(WORLD_X):
                print(world[i][j], end='')
            print()
        print()    
        print(f" Time: {time},  # of Nomads: {len(nomads)}")

        # iterate thru each nomad and call the `tick()` method.
        # this will cause the nomad to do stuff, and also
        # provide info about any new births or deaths.
        #
        # the `one_dead` thing is a clunky way of dealing
        # with deleting from the nomad list while iterating.
        # basically, only one nomad can die per loop
        #
        one_dead = False
        for i,a in enumerate(nomads[:]):

            ret = a.tick(time)
            if ret['dead']:
                if not one_dead:
                    del nomads[i]
                    world[a.pos[0]][a.pos[1]] = OPEN_TILE
                    one_dead = True

            if ret['offspring']:
                g = ret['offspring']
                new_a = Nomad(g['pos'], time, g['sense'], g['stamina'], g['tribal'], g['tribe'], g['allegiance'])
                nomads.append(new_a)
                world[g['pos'][0]][g['pos'][1]] = new_a
                

        # check to see if more plants will grow
        if time % PLANT_GROWTH_RATE == 0:

            # check if below max pct for the plants in the world
            if plant_count / WORLD_AREA < MAX_PLANT_PCT:

                # if so, grow some more plants
                open_tiles = [
                    (ix,iy) for ix, row in enumerate(world)
                    for iy, i in enumerate(row) if i == OPEN_TILE]

                for _ in range(PLANT_GROWTH_AMT):
                    try:
                        t = choice(open_tiles)
                        world[t[0]][t[1]] = PLANT_TILE
                    except:
                        pass
            
            # grab a count of plants for next time
            plant_count = sum([1 for x in world for y in x if y == PLANT_TILE])

        # write stats about the simulation to a CSV file.
        # adjust OUTPUT_WRITE_INTERVAL for different data granularity
        if time % OUTPUT_WRITE_INTERVAL == 0:
            output = f"{time},{WORLD_AREA},{plant_count},{len(nomads)}"
            output += "," + str(len([a for a in nomads if a.gender == 'female']))
            output += "," + str(mean([a.sense for a in nomads]))
            output += "," + str(mean([a.stamina for a in nomads]))
            output += ',' + str(mean([a.allegiance for a in nomads]))
            output += ',' + str(mean([a.tribal for a in nomads]))
            stats_file.write(f"{output}\n")
            
        # sleep, and increment time
        sleep(SPEED)
        time += 1


# catch Ctrl+c for early exit
except KeyboardInterrupt:
    stats_file.close()

    if DEBUG:
        for n in nomads:
            print(n.debug())
    
    print('\nthanks for playing!')
    exit(0)

except Exception as e:
    stats_file.close()
    print("\nUh oh, unexpected Error!")
    print(traceback.format_exc())
    exit(0)


print('\nall the nomads died, thanks for playing!')
