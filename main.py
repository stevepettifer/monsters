from monsters import *
from bender import Bender

class MyMonster(Monster):
  def onCreate(self):
    self.say("Hi! I am MyMonster")

  def behaviour(self):
    if self.isOnFruit():
      self.eatFruit()

    if self.isOnItem():
      self.pickItem()
      
    self.moveRandomly()

# Create the world (should be done after simulation is created)
world = World("worlds/water.world")

# Add monsters to the world
world.addMonster(DefaultMonster(world, 1))
world.addMonster(DefaultMonster(world, 2))
world.addMonster(MyMonster(world, 3))
world.addMonster(Bender(world, 9))

# Start the simulation
world.simulate()