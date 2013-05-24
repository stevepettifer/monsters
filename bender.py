from monsters import *

# A monster which gathers the knowledge about the world map and then uses Lees algorithm to find
# a path towards the most valuable fruit
class Bender(Monster):

  allDirections = [World.North, World.East, World.West, World.South]

  def onCreate(self):
    self.fruitValue = {}
    self.field = {}

    for x in range(World.size):
      for y in range(World.size):
        self.field[QPoint(x,y)] = '?'

    self.say("Hi! I am Bender")

  def getFruitValue(self, fruitType):
    if fruitType in self.fruitValue.keys():
      return self.fruitValue[fruitType]
    else:
      return 0

  def cmpFruit(self, firstFruit, secondFruit):
    (firstFruitPos, firstFruitType) = firstFruit
    (secondFruitPos, secondFruitType) = secondFruit

    firstFruitValue = self.getFruitValue(firstFruitType)
    secondFruitValue = self.getFruitValue(secondFruitType)

    if firstFruitValue < secondFruitValue:
      return 1
    elif firstFruitValue == secondFruitValue:
      firstFruitDistance = (firstFruitPos - self.pos()).manhattanLength()
      secondFruitDistance = (secondFruitPos - self.pos()).manhattanLength()
      if  firstFruitDistance < secondFruitDistance:
        return -1
      elif firstFruitDistance == secondFruitDistance: 
        return 0
      else:
        return 1
    else:
      return -1

  def behaviour(self):
    if self.isOnFruit():
      energyBefore = self.energy()
      fruitType = self.eatFruit()
      self.fruitValue[fruitType] = self.energy() - energyBefore

    if self.isOnItem():
      self.pickItem()

    for direction in self.allDirections:
      target = self.pos() + World.movingVector[direction]

      if self.canMove(direction):
        self.field[target] = '.'
      else:
        self.field[target] = '#'

    direction = self.getDirection()
      
    if direction != None and self.canMove(direction):
      self.move(direction)
    else:
      self.moveRandomly()
      
    #for y in range(0,World.size):
    #  row = ""
    #  for x in range(0,World.size):
    #    if QPoint(x,y) == self.pos():
    #      row += 'O'
    #    else:
    #      row += self.field[QPoint(x,y)]
    #  print row
    #print ''

  def getDirection(self):

    for d in self.allDirections:
      if self.field[self.pos() + World.movingVector[d]] == '?': # Move to unknown
        return d

    fieldCopy = {}
  
    for cell in self.field.keys():
      if self.field[cell] == '#':
        fieldCopy[cell] = -2
      elif self.field[cell] == '?':
        fieldCopy[cell] = -1
      else:
        fieldCopy[cell] = 0

    # Start position
    fieldCopy[self.pos()] = 1
    
    haveMore = True
    iteration = 1 

    while haveMore:
      haveMore = False

      for pos in fieldCopy.keys():

        if fieldCopy[pos] == iteration:
          haveMore = True

          for d in self.allDirections:
            target = pos + World.movingVector[d]

            if World.rect.contains(target) and fieldCopy[target] == 0:
                fieldCopy[target] = iteration + 1

      iteration += 1

    nearbyFruitPos = [p for (p, t) in self.smell() if fieldCopy[p] > 1]

    nearbyFruitPos = sorted(nearbyFruitPos, key = lambda p: fieldCopy[p])

    if len(nearbyFruitPos) != 0:
      currentPos = nearbyFruitPos[0]
    else:
      currentPos = None

    accessible = [cell for cell in fieldCopy.keys() if fieldCopy[cell] > 1]

    bestCell = None

    for cell in accessible:
      unknown = 0
      for neighbour in (cell + World.movingVector[d] for d in self.allDirections):
        if fieldCopy[neighbour] == -1:
          unknown += 1

      if unknown > 0 and (bestCell == None or fieldCopy[cell] < fieldCopy[bestCell]):
        bestCell = cell

    if bestCell != None:
      if currentPos == None or fieldCopy[bestCell] < fieldCopy[currentPos]:
        currentPos = bestCell

    if currentPos == None:
      return None

    iteration = fieldCopy[currentPos]
    # Follow path from current position to the one next to monster position
    while iteration != 2:
      for d in self.allDirections:
        newPos = currentPos + World.movingVector[d]
        if World.rect.contains(newPos) and fieldCopy[newPos] == iteration - 1:
          currentPos = newPos
      iteration -= 1
  
    vector = currentPos - self.pos()

    for direction in World.movingVector.keys():
      if World.movingVector[direction] == vector:
        return direction