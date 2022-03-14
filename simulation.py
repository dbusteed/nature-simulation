import pandas as pd
import zmq
from random import randint, choice, random, shuffle
from statistics import mean
from time import sleep
from os import system
from sys import exit


#----------------------#
#   SIMULATION SETUP   #
#----------------------#

# colors for printing to the console.
# replace these with blank strings
# to disable color support (but make
# sure to edit the tiles below so that
# they are distinguishable)
#
BG_BLUE = '\033[44m'
BG_GREEN = '\033[42m'
FG_RED = '\033[1;31m'
NC = '\033[0m'

# different tiles for the grid
WATER_TILE = f'{BG_BLUE} {NC}'
PLANT_TILE = f'{BG_GREEN} {NC}'
OPEN_TILE = " "

# grid / world dimensions
WORLD_X = 25
WORLD_Y = 10
WORLD_AREA = WORLD_X * WORLD_Y

# initial amount of water and plants.
# when editing, change the demoninator of
# this expression:
#   Ex: 10% = int(1 / .10) = 1 out of 10
#
WATER_FACTOR = int(1 / .02)
PLANT_FACTOR = int(1 / .05)

# settings for the animals
#  - number of starting animals
#  - pct chance offspring will mutate
#  - pct chance females will reproduce when
#     when encountering a male
#  - starting sense value for anumals
#  - starting stamina value for animals
#
ANIMAL_COUNT = 15
MUTATION_CHANCE = 0.9
REPRODUCTION_CHANCE = 0.5
BASE_SENSE = 4
BASE_STAMINA = 40

# plant stuff
#  - how often plants regrow (1 out of X times)
#  - how many plants regrow each time
#  - limit for how many plants grow in the world
#    
PLANT_GROWTH_RATE = 10
PLANT_GROWTH_AMT = 3
MAX_PLANT_PCT = .20

# output stuff
#  - how often data is written
#     (lower number for more frequent updates)
#
OUTPUT_WRITE_INTERVAL = 20

# speed of simulation
# (i had issues with lower than 0.1)
SPEED = .1


#---------------------#
#   SETUP LIVE PLOT   #
#---------------------#

socket = zmq.Context(zmq.REP).socket(zmq.PUB)
socket.bind("tcp://*:8899")


#------------------#
#   ANIMAL CLASS   #
#------------------#

class Animal:
    def __init__(self, pos, tob=0, sense=BASE_SENSE, stamina=BASE_STAMINA):    
        
        # attributes for basic actions
        self.pos = pos
        self.thirst = 0
        self.hunger = 0
        self.target = None
        self.goal = 'drink'
        self.goals = { 'eat': PLANT_TILE, 'drink': WATER_TILE }
        
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
        base_lifespan = 800

        # self.fatigue = sense // 2
        # base_lifespan = int((-10 * stamina) + 1300)
        
        # a little randomness in the lifespan or else an entire
        # generation dies at the same time
        self.lifespan = randint(base_lifespan-100, base_lifespan+100)

        # genders are randomly assigned at "birth",
        # and have different attributes for the females
        if randint(1,2) == 1:
            self.gender = 'male'
            self.marker = f'{FG_RED}m{NC}'
        else:
            self.gender = 'female'
            self.marker = f'{FG_RED}f{NC}'
            self.reproduction_chance = REPRODUCTION_CHANCE
            self.pregnant = False
            self.gestation = 0
            self.child_genes = {}


    # this handles everything that the animal does,
    # and is called for each animal in the main loop
    #
    def tick(self, t):

        # status object for returning to the main process
        status = {'dead': False, 'offspring': None}

        # the animal grows up if they reach their adult_age
        if (t - self.tob) == self.adult_age:
            self.marker = f'{FG_RED}M{NC}' if self.gender == 'male' else f'{FG_RED}F{NC}'

        # reproduction stuff for female animals
        if self.marker == f'{FG_RED}F{NC}' or self.marker == f'{FG_RED}P{NC}':
            
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
                        self.marker = f'{FG_RED}F{NC}'
                    self.pregnant = False

            # if they aren't pregnant, first check if they are willing to mate
            elif random() <= self.reproduction_chance:
                
                # get the surroundings
                around = self._get_surroundings()
                
                # check if an adult male is nearby...
                if 'Animal' in [a[1].__class__.__qualname__ for a in around]:
                    anis = [a for a in around if a[1].__class__.__qualname__ == 'Animal']
                    if [a for a in anis if a[1].marker == f'{FG_RED}M{NC}']:
                        
                        # ... if so, mix the genes with the father, and
                        # start the pregnancy process
                        father = [a[1] for a in anis if a[1].marker == f'{FG_RED}M{NC}'][0]
                        self.child_genes = {
                            'sense': self._mix_genes(father, 'sense'),
                            'stamina': self._mix_genes(father, 'stamina'),
                        }
                        self.pregnant = True
                        self.gestation = 30
                        self.marker = f'{FG_RED}P{NC}'


        # movement stuff
        #
        # first check if the animal has a target 
        if self.target:
            diff = (self.target[0] - self.pos[0], self.target[1] - self.pos[1])

            # if they next to the target
            if abs(diff[0]) + abs(diff[1]) == 1:
                func = getattr(self, self.goal)
                func() # this will either be `eat()` or `drink()`
                
                # get a new goal by checking if the animal
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

        
        # get thisty and hungry
        self.thirst += randint(0, self.fatigue)
        self.hunger += randint(0, self.fatigue)

        # check if the animal died of hunger, thirst, or old age
        if self.thirst > self.stamina \
            or self.hunger > self.stamina \
            or ((t - self.tob) > self.lifespan):

            status['dead'] = True

        return status

    #
    # helper functions for reproducting and moving
    # around the grid
    #
    def _mix_genes(self, father, trait):
        spread = abs(getattr(self, trait) - getattr(father, trait))
        if spread == 0:
            spread = 2

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
    # basic animal actions
    #
    def drink(self):
        self.thirst = 0

    def eat(self):
        world[self.target[0]][self.target[1]] = OPEN_TILE
        self.hunger = 0

    # useful for debugging
    def debug(self):
        o = 'Animal:\n'
        o += f' POS: {self.pos}'
        o += f' THR: {self.thirst}'
        o += f' HGR: {self.hunger}\n'
        o += f' GOL: {self.goal}'
        o += f' TGT: {self.target}\n'
        o += f' SNS: {self.sense}'
        o += f' STM: {self.stamina}'
        o += f' LSP: {self.lifespan}'
        return o

    #
    # this allows to print representation of the
    # Animal object (the marker) easily
    #
    def __str__(self):
        return self.marker



#-------------------#
#   BUILD THE MAP   #
#-------------------#

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

# ...and put some animals there!
animals = []
a_count = 0
while a_count < ANIMAL_COUNT:
    for ix,iy in open_tiles:
        if randint(1,50) == 1:
            animals.append(Animal((ix,iy)))
            a_count += 1

# limit the number of animals to the 
# constant defined above
animals = animals[:ANIMAL_COUNT]

# put the animals on the map
for a in animals:
    world[a.pos[0]][a.pos[1]] = a



#---------------#
#   GAME LOOP   #
#---------------#
 
time = 0
clear = lambda: system('clear')

try:
    # continue simulation until all the animals die,
    # or user hits Ctrl+c (see execption below)
    while len(animals) > 0:

        # clear the sceen and print the map
        clear()
        for i in range(WORLD_Y):
            for j in range(WORLD_X):
                print(world[i][j], end='')
            print()

        # iterate thru each animal and call the `tick()` method.
        # this will cause the animal to do stuff, and also
        # provide info about any new births or deaths.
        #
        # the `one_dead` thing is a clunky way of dealing
        # with deleting from the animal list while iterating.
        # basically, only one animal can die per loop
        #
        one_dead = False
        for i,a in enumerate(animals[:]):
            ret = a.tick(time)
            if ret['dead']:
                if not one_dead:
                    del animals[i]
                    world[a.pos[0]][a.pos[1]] = OPEN_TILE
                    one_dead = True

            if ret['offspring']:
                genes = ret['offspring']
                new_a = Animal(genes['pos'], time, genes['sense'], genes['stamina'])
                animals.append(new_a)
                world[genes['pos'][0]][genes['pos'][1]] = new_a

        # check to see if more plants will grow
        if time % PLANT_GROWTH_RATE == 0:

            # check if below max pct for the plants in the world
            if plant_count / WORLD_AREA < MAX_PLANT_PCT:

                # if so, grow some more plants
                open_tiles = [
                    (ix,iy) for ix, row in enumerate(world)
                    for iy, i in enumerate(row) if i == OPEN_TILE]
                for _ in range(PLANT_GROWTH_AMT):
                    t = choice(open_tiles)
                    world[t[0]][t[1]] = PLANT_TILE
            
            # grab a count of plants for next time
            plant_count = sum([1 for x in world for y in x if y == PLANT_TILE])

        # write stats about the simulation to a CSV file.
        # adjust OUTPUT_WRITE_INTERVAL for different data granularity
        if time % OUTPUT_WRITE_INTERVAL == 0:
            row = [
                len(animals),
                len([a for a in animals if a.gender == 'female']),
                plant_count,
                mean([a.sense for a in animals]),
                mean([a.stamina for a in animals])
            ]
            socket.send_pyobj(row)
            
        # simple output for monitoring simulation
        # print()
        # print(f" Time: {time},  # of Animals: {len(animals)}")

        # sleep, and increment time
        sleep(SPEED)
        time += 1


# catch Ctrl+c for early exit
except KeyboardInterrupt:
    print('\nthanks for playing!')
    exit(0)

except Exception as e:
    print("\nUh oh, unexpected Error!")
    print(e)


print('\nall the animals died, thanks for playing!')
