# Nature Simulation

A very simplistic simulation of some animals surviving and evolving in a little environment

I thought this would be interesting to make after watching some videos on YouTube, and decided to make it "console friendly", rather than using a legit 3D game engine like Unity

<br>

## Example

<img alt="demo of simulation" src="./other/demo.gif" height="400" width="350">

<br>

## How It Works

1. The "world" is a 2D grid that contains open spaces, water, and plants
2. The "animals" explore the world, drinking water, eating plants, and reproducing
3. Male and female animals start off as children, and can reproduce after maturing
4. Two attributes of the animals (sense and stamina) are passed down to offspring
5. The "genes" can mutate, producing animals with different traits than the parents
6. Animals can die from hunger, thirst, or old age

<br>

## How To Use

### Step 1

After downloading the repo, all you need is Python 3.6+ to run the simulation

Run with `python`, or specify your Python path and run as an execuable
```bash
$ python main.py

# OR 

$ chmod +x main.py
$ ./main.py
```

### Step 2

When the simulation finishes (or you exit early with `Ctrl+c`), you can view the results of the simulation with the `view_stats.py` script

Unlike `main.py` that only uses the Python Standard Library, `view_stats.py` requires the following packages:

* matplotlib
* seaborn
* pandas

With those packages installed, you can view the `stats.csv` file that was created during the simulation. Run this script in a similar matter as before:
```bash
$ python view_stats.py

# OR

$ chmod +x view_stats.py
$ ./view_stats.py
```

### Step 3

Tweak some of the variables in `main.py` and run the simulation again!

There are a number of constants defined at the beginning of the file, as well as any changes you decide to make within the program itself

<br>

## Notes

I've only tested this on Ubuntu Linux. I imagine this should work on MacOS because it also uses bash/zsh. I plan on testing it on Windows at some point

## TODO


print less often?

bug with the exponential growth?
- trying to replicate
- maybe die with over-population
  - how to track? 
  - if at any point completely surrounded => base_lifespan--

resources

search for mates

tribes
- disputes
- benefits of tribes
  - maybe allegiance has a positve relationship with base_lifespan


[ ] tribe rebellions
    - what happens when one tribe takes over?
    - random chance?
    - maybe if hungry / thirsty?
      - but then they'd rebel right before dying?
    - maybe tied to the gene for "tribal-ness"
      - better name? "tribal"
      - from 0 to 1, how tribal is this nomad
      - tribal gene determines
        - if it will engage in fights (high tribal)
        - if it will rebel (low tribal)

    - 0 to 1
    - start at 0.5
      - 50% chance will join a tribe when mating?
      or maybe will always join a tribe when mating, but their allegiance only changes randomly

      - random chance to see if will fight others
      - random to see if they will rebel

      - do rebellions first!
        - if tribal is 1, then 10% chance of leaving
        - if tribal is 10, then 1% chance of leaving
      

    
[ ] selective mating based on tribe

[ ] tribal wars
    - best way to "attack"?

[ ] maybe allegiance drops over time, more so if low `tribal`
    - 