import sys, random

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtOpenGL import *

class World(QApplication):

  # Size of each individual cell, in pixels
  cellSize = 100

  # Size of the world (to be set later)
  size = None

  # QRect representing the field
  rect = None
  
  # enumeration for world directions
  North, South, East, West = range(4)

  # Direction moving vectors
  movingVector = {North : QPoint(0, -1),
                  South : QPoint(0, 1),
                  East  : QPoint(1, 0),
                  West  : QPoint(-1, 0)}

  # Enumeration for the world object types
  Nothing, Grass, Rock, Pond, Fruit, Item, Monster = range(7) 

  def __init__(self, filename):
    super(World, self).__init__(sys.argv)

    # Lists containing various objects in the world
    self.rocks = []
    self.ponds = []
    self.fruits = []
    self.monsters = []
    self.rubberRing = None

    worldFile = open(filename, "r")
    worldFileLines = worldFile.readlines()

    # Determine the size of the world using the number of the rows in the files
    World.size = len(worldFileLines)

    World.rect = QRect(0, 0, World.size, World.size)

    # Create a graphics scene to display objects
    self.scene = QGraphicsScene()
    self.scene.setSceneRect(0, 0, self.cellSize * self.size, self.cellSize * self.size);

    self.view = QGraphicsView(self.scene)
    # Set up the view to use OpenGL as a rendering engine
    self.view.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
    self.view.setDragMode(QGraphicsView.ScrollHandDrag)
    self.view.setBackgroundBrush(QPixmap('./images/grass.png'));
    self.view.setWindowTitle('Monsters');
    self.view.resize(800, 600);
    self.view.show()

    # Add all the objects from the file to the world
    for y in range(self.size): # No. of line
      for x in range(self.size): # No. of character

        char = worldFileLines[y][x]

        pos = QPoint(x, y)

        if char == '.': # Nothing (grass)
          pass
        elif char == '#': # Rock
          self.rocks.append(Rock(random.randint(1,4), self, pos))
        elif char == '~': # Pond
          self.ponds.append(Pond(self, pos))
        elif char == '*': # Source of gems
          #TODO: place a source of gems
          pass
        else:
          #TODO: throw an error here
          pass

    # Add some fruits at random positions
    for fruit in range(5):
      self.addRandomFruit()

    # Create rubber ring
    self.rubberRing = RubberRing(self)
    self.rubberRing._setRandomPos()


  def randomEmptyPos(self):
    ''' Returns random empty position in the world '''
    pos = None

    while True:
      pos = QPoint(random.randint(0, self.size - 1),
                   random.randint(0, self.size - 1))
      if not pos in self.occupiedPositions():
        break

    return pos

  def simulate(self):
    ''' Begins the simulation process '''
    # Start the behaviour of the monsters
    for monster in self.monsters:
      monster._behaviourTimer.start()

    self.exec_()


  def occupiedPositions(self):
    ''' Returns a list of cell positions that already contain objects '''
    return (self.obstaclePositions() + self.fruitPositions() + self.itemPositions())

  def itemPositions(self):
    positions = []

    if self.rubberRing != None:
      positions.append(self.rubberRing._pos)

    return positions


  def obstaclePositions(self):
    ''' Returns a list of cell positions where monster can not go '''
    return (self.rockPositions() + self.monsterPositions() 
           + self.monsterTargets() + self.pondPositions())

  def fruitPositions(self):
    ''' Returns a list of QPoints of cell positions containing fruit '''
    return [fruit._pos for fruit in self.fruits]

  def rockPositions(self):
    ''' Returns a list of QPoints of cell positions containing rock '''
    return [fruit._pos for fruit in self.rocks]

  def pondPositions(self):
    return [pond._pos for pond in self.ponds]

  def monsterPositions(self):
    ''' Returns a list of QPoints of cell positions containing moster '''
    return [fruit._pos for fruit in self.monsters]

  def monsterTargets(self):
    ''' Returns a list of QPoints of cell positions where some of the monster
        want to go '''
    return [monster._targetPos for monster in self.monsters if monster._targetPos is not None]

  def addRandomFruit(self):
    ''' Places random fruit at the random place in the world '''

    # Get random float from 0.0 to 1.0
    randomNumber = random.random()

    # Choose which fruit type should be placed. We want certain types of fruit to apper less.
    # In order to do it, we split range [0,1] into sectors. For each fruit type the size of its
    # sector is determined by its probability. The bigger probability is,
    # the bigger sector it gets. If random number is within some fruit type
    # sector, than the fruit of that type is placed
    previousSum = 0
    for fruitType in Fruit._fruitProbability.keys():
      previousSum += Fruit._fruitProbability[fruitType]

      # If the number is in this sector, use this type of fruit
      if randomNumber <= previousSum:
        fruitTypeToPlace = fruitType
        break

    fruit = Fruit(fruitTypeToPlace, self)
    fruit._setRandomPos()

    # Place fruit
    self.fruits.append(fruit)

  def getFruitAtPos(self, pos):
    ''' Returns fruit object located at the specified position, or None '''
    for fruit in self.fruits:
      if fruit._pos == pos and fruit._isVanished == False:
        return fruit

    return None

  def getItemAtPos(self, pos):
    ''' Returns item object located at the specified position, or None '''
    if self.rubberRing._pos == pos and self.rubberRing._isVanished == False:
      return self.rubberRing

  def addMonster(self, monster):
    ''' Adds a new monster to the list '''
    self.monsters.append(monster)
    monster._setRandomPos()

class WorldObject(QWidget):
  def __init__(self, world, image, z, position = None):
    super(WorldObject, self).__init__()

    self._world = world
    self._pos = QPoint(0,0)

    if position != None:
      self._pos = position

    scaledPixmap = QPixmap(image).scaled(World.cellSize, World.cellSize, mode = Qt.SmoothTransformation)
    self._graphicsItem = QGraphicsPixmapItem(scaledPixmap)
    self._graphicsItem.setPos(self._pos * World.cellSize) 
    self._graphicsItem.setTransformOriginPoint(self._graphicsItem.boundingRect().center()) 
    self._graphicsItem.setZValue(z)

    self._world.scene.addItem(self._graphicsItem)

  def _setPos(self, newPos):
    self._pos = newPos
    self._graphicsItem.setPos(newPos * World.cellSize)

  def _setRandomPos(self): 
    self._setPos(self._world.randomEmptyPos())

  def __del__(self):
    self._world.scene.removeItem(self._graphicsItem)

class PickableWorldObject(WorldObject):
  def __init__(self, world, image, position = None):
    super(PickableWorldObject, self).__init__(world, image, 1, position)

     # Timer for animating the vanishing process      
    self._vanishTimer = QTimer()
    self._vanishTimer.setInterval(10)
    self._vanishTimer.timeout.connect(self._vanishStep)

    # Timer for animating the appearing process
    self._appearTimer = QTimer()
    self._appearTimer.setInterval(10)
    self._appearTimer.timeout.connect(self._appearStep)
    
    # Position along the animation timeline, between 0.0 and 1.0
    self._animationStep = 0.0

    # Variable to avoid picking object one more time while it is in the process
    # of vanishing
    self._isVanished = False

    # Start the appearing animation
    self.appear()

  def vanish(self):
    ''' Start the vanishing process '''
    self._animationStep = 0.0
    self._vanishTimer.start()

    # Mark item as vanished so it could not be used again
    self._isVanished = True
  
  def _vanishStep(self):
    ''' Step the vanishing animation along by one '''
    self._animationStep +=  0.1
    self._graphicsItem.setScale(1.0 - self._animationStep)
    self._graphicsItem.setOpacity(1.0 - self._animationStep)
    
    if (self._animationStep >= 1.0):
      self._vanishTimer.stop()
      self._graphicsItem.setScale(1.0)
      # Run a callback
      self._vanishFinished()

    self._world.scene.update()
    
  def appear(self):
    ''' Start the appearing process '''
    self._animationStep = 0.0
    self._graphicsItem.setScale(0.1)
    self._graphicsItem.setOpacity(0.1)
    self._appearTimer.start()
    self._world.scene.update()

    # Mark item as active, so it can be used again
    self._isVanished = False

  def _appearStep(self):
    ''' Step the appearing animation along by one '''
    self._animationStep += 0.1
    self._graphicsItem.setScale(self._animationStep)
    self._graphicsItem.setOpacity(self._animationStep)
    
    if (self._animationStep >= 1.0):
      self._appearTimer.stop()
      self._graphicsItem.setScale(1.0)
      self._graphicsItem.setOpacity(1.0)
    
    self._world.scene.update()

  def _vanishFinished(self):
    ''' Callback function. Called, when vanishing process is finished.
        To be implemented in subclasses as necessary '''
    pass

class Rock(WorldObject):

  def __init__(self, rockType, world, position = None):
    super(Rock, self).__init__(world, './images/boulder%d.png' % rockType, 1, position)

class Pond(WorldObject):

  def __init__(self, world, position = None):
    super(Pond, self).__init__(world, './images/pond.png', 1, position)

class RubberRing(PickableWorldObject):

  def __init__(self, world, position = None):
    super(RubberRing, self).__init__(world, './images/rubber_ring.png', position)

    self._ownerLeaveTimer = QTimer()
    self._ownerLeaveTimer.setSingleShot(True)
    self._ownerLeaveTimer.setInterval(5000)
    self._ownerLeaveTimer.timeout.connect(self._leaveOwner)

    self._owner = None

  def setOwner(self, owner):
    self._owner = owner
    self._ownerLeaveTimer.start()

  def _leaveOwner(self):
    self._owner._items.remove(self)

    self._owner.say("I have lost the ring.")

    # Show the ring at the new random position
    self._setRandomPos()
    self.appear()

class Fruit(PickableWorldObject):

  # Energy amount for each type of fruit
  _energyForFruit = {1 : 5,
                     2 : 10,
                     3 : 15,
                     4 : 20}

  # Probability of each fruit to appear
  _fruitProbability = {1 : 0.4,
                       2 : 0.3,
                       3 : 0.2,
                       4 : 0.1}

  def __init__(self, fruitType, world, position = None):
    super(Fruit, self).__init__(world,'./images/fruit%d.png' % fruitType, position)

    # Variable to store the type of the fruit
    self._type = fruitType

  def type(self):
    return self._type

  def _vanishFinished(self):
    # Remove fruit from the world
    self._world.fruits.remove(self)


class SpeechBubble:
  textMargin = 10

  arrowWidth = 10
  arrowHeight = 10
  arrowPosition = 40

  def __init__(self, world):
    self._world = world

    # Font used
    self._font = QFont("arial", 10)
    # Font metrics for determining the size of the message
    self._fm = QFontMetrics(self._font)

    # Timer to hide bubble after some time
    self._hideTimer = QTimer()
    self._hideTimer.setSingleShot(True)
    self._hideTimer.timeout.connect(self.hide)

    # Create graphics item for the bubble
    self._graphicsItem = QGraphicsPixmapItem()
    self._graphicsItem.setZValue(100)

    self._world.scene.addItem(self._graphicsItem)

  def setMessage(self, message):
    # Crop the string to the allowed length
    message = message[:140]

    # Determine the size of message
    textWidth = self._fm.width(message)
    textHeight = self._fm.height()

    # If message is long, split it into two lines
    if len(message) > 70:
      bubbleWidth = self._fm.width(message[:70]) + SpeechBubble.textMargin * 2
      bubbleHeight = self._fm.height() * 2 + SpeechBubble.textMargin * 2
    else:
      bubbleWidth = textWidth + SpeechBubble.textMargin * 2
      bubbleHeight = textHeight + SpeechBubble.textMargin * 2

    # Create pixmap to draw on
    bubble = QPixmap(bubbleWidth, bubbleHeight + SpeechBubble.arrowHeight)
    bubble.fill(Qt.transparent)

    bubblPath = QPainterPath()
    # Create bubble box
    bubblPath.addRoundRect(QRectF(1,1,bubbleWidth - 2,bubbleHeight - 2), 10, 30)
    # Create arrow
    bubblPath.moveTo(QPointF(SpeechBubble.arrowPosition, bubbleHeight - 1))
    bubblPath.lineTo(QPointF(SpeechBubble.arrowPosition + SpeechBubble.arrowWidth / 2, 
                              bubbleHeight + SpeechBubble.arrowHeight))
    bubblPath.lineTo(QPointF(SpeechBubble.arrowPosition + SpeechBubble.arrowWidth, bubbleHeight - 1))
    # Merge arrow with bubble box
    bubblPath = bubblPath.simplified()

    # Draw bubble
    bubblePainter = QPainter(bubble)
    bubblePainter.setRenderHint(QPainter.Antialiasing)
    bubblePainter.setBrush(QBrush(Qt.white))
    bubblePainter.setPen(Qt.black)
    bubblePainter.setOpacity(0.7)
    bubblePainter.drawPath(bubblPath)

    # Draw text on bubble
    bubblePainter.setRenderHint(QPainter.TextAntialiasing)
    bubblePainter.setOpacity(1)
    bubblePainter.setFont(self._font)
    bubblePainter.drawText(QRectF(self.textMargin, self.textMargin, bubbleWidth, bubbleHeight), 
                           Qt.TextWordWrap | Qt.AlignTop, message)

    del bubblePainter

    self._graphicsItem.setPixmap(bubble)

  def setPos(self, x, y):
    ''' Set the position of this speech bubble in that way that x and y are the coords of
        the arrow '''
    newX = x - SpeechBubble.arrowPosition - SpeechBubble.arrowWidth / 2
    newY = y - self._graphicsItem.boundingRect().height() - SpeechBubble.arrowHeight

    self._graphicsItem.setPos(newX, newY);

  def show(self, seconds = None):
    ''' Show the bubble for specified number of seconds, or forever if seconds is None '''
    if seconds != None:
      # Start a timer to hide the bubble after specified time
      self._hideTimer.start(seconds * 1000)

    self._graphicsItem.show()

  def hide(self):
    self._graphicsItem.hide()

class Monster(WorldObject):

  _energyPenaltyOccupied = 5
  _energyPerMove = 1
  _energyCriticalLevel = 10
  _energyMax = 50
  _energyPerSecond = 10

  def __init__(self, world, monsterType, position = None):
    image = './images/monster%d.png' % monsterType

    super(Monster, self).__init__(world, image, 2, position)
    
    self._speed = 1.0
    self._t = 0.0 # Animation parameter
    
    # Variables to control the 'wobble' of a monster as it moves
    self._wobbleCount = 0
    self._wobbleDirection = 1

    # The cell to which a monster is about to move
    self._targetPos = None
    
    # Timer for controlling the move animation
    self._moveTimer = QTimer(self)
    self._moveTimer.timeout.connect(self._updatePosition)
    
    # A 0-time timer to allow behaviour to be controlled by a slot rather than
    # called directly as a function
    self._behaviourTimer = QTimer(self)
    self._behaviourTimer.setInterval(0)
    self._behaviourTimer.setSingleShot(True)
    self._behaviourTimer.timeout.connect(self.behaviour)

    # Speech bubble with the message monster is currently saying
    self._speechBubble = SpeechBubble(self._world)
    self._updateSpeechBubblePos()

    # Variable to store energy of the monster
    self._energy = Monster._energyMax

    # Timer to control sleeping
    self._sleepTimer = QTimer(self)
    self._sleepTimer.setInterval(1000)
    self._sleepTimer.timeout.connect(self._sleep)

    # Variables to control sleeping
    self._isSleeping = False
    self._leftSleeping = 0

    # List of items monster has (accesible by monster author)
    self._items = []

    self.onCreate() # Callback

  @Slot()
  def _updatePosition(self):
    ''' Update the position of the monster if we are in the process of movement '''
    
    # Step the animation parameter on a bit
    self._t += 0.05

    # Arrange for the monster to wobble as it moves
    self._wobbleCount += 1
    self._graphicsItem.setRotation(self._wobbleCount * self._wobbleDirection)
    if (self._wobbleCount > 4):
      self._wobbleDirection *= -1
      self._wobbleCount = 0
      
    # Calculate the new position
    newPos = QPointF(self._pos) + QPointF(self._targetPos - self._pos) * self._t

    self._graphicsItem.setPos(newPos * World.cellSize)

    # Move the speech bubble together with the monster
    self._updateSpeechBubblePos()
    
    # Redraw the field
    self._world.scene.update()
    
    # if the animation is complete, reset everything ready for the next move
    if self._t >= 1.0:
      self._moveTimer.stop() 
      self._setPos(self._targetPos)
      self._targetPos = None
      self._behaviourTimer.start()

  def _updateSpeechBubblePos(self):
    ''' Update speech bubble position so it is right above the monster '''

    if self._speechBubble != None:
      monsterWidth = self._graphicsItem.boundingRect().width()
      monsterX = self._graphicsItem.x()
      monsterY = self._graphicsItem.y()

      self._speechBubble.setPos(monsterX + monsterWidth / 2, monsterY);

  def _increaseEnergy(self, amount):
    # Increase energy to the maximum of energyMax
    self._energy = min((self._energy + amount), Monster._energyMax)
    
    if self._speed < 1.0 and self._energy > Monster._energyCriticalLevel:
      # If we were low on energy, and regained it, return to the normal speed
      self._speed = 1.0
    

  def _reduceEnergy(self, amount):
    # Reduce energy to the minimum of 0
    self._energy = max((self._energy - amount), 0);

    if self._energy == 0:
      # If have no energy, go to sleep for the period necessary to restore it
      # up to the critical level
      self.say("No energy left. Good night!")
      self.sleep(Monster._energyMax / Monster._energyPerSecond)
    elif self._energy < Monster._energyCriticalLevel:
      # If energy is below critical level, reduce the speed
      self._speed = 0.3
      self.say("Low on energy")

  def _sleep(self):
    if self._isSleeping:
      if self._leftSleeping > 0:
        self._leftSleeping -= 1
        self._increaseEnergy(Monster._energyPerSecond)
        self.say("Zzz...")
      else:
        self._isSleeping = False
        self._behaviourTimer.start()
        self._sleepTimer.stop()
        self.say("Good morning!")

  #=============================================================================
  # Beginning of monster creators API
  #=============================================================================

  def pos(self):
    ''' Returns the monster position on the field '''
    return self._pos

  def energy(self):
    ''' Returns amount of monsters energy '''
    return self._energy
        
  def observe(self, direction):
    ''' Returns  the type of object located in specified direction '''
    # Calculate the target cell
    target = self._pos + World.movingVector[direction]
      
    if not World.rect.contains(target):
      # Tried to move off the edge of the world   
      return World.Nothing
    elif target in self._world.rockPositions():
      return World.Rock
    elif target in self._world.pondPositions():
      return World.Pond
    elif target in self._world.monsterPositions() or target in self._world.monsterTargets():
      return World.Monster
    elif target in self._world.fruitPositions():
      return World.Fruit
    elif target in self._world.itemPositions():
      return World.Item
    else:
      return World.Grass

  def canMove(self, direction):
    ''' Returns fTrue if monster can move in specified direction, 
        False otherwise '''
    # Calculate the target cell
    target = self._pos + World.movingVector[direction]

    if not World.rect.contains(target):
      return False
    elif target in self._world.pondPositions() and self._world.rubberRing in self._items:
      return True
    elif target in self._world.obstaclePositions():
      return False
    else:
      return True
    
  def move(self, direction):
    ''' Move monster in specified direction '''
    if self._isSleeping:
      return

    if self.canMove(direction): 
      self._targetPos = self._pos + World.movingVector[direction]

      if self._targetPos in self._world.pondPositions():
        self.say("Whoaa! I am swimming")
      
      self._t = 0.0
      self._moveTimer.setInterval(10 / self._speed)
      self._moveTimer.start()

      # Reduce energy for move
      self._reduceEnergy(Monster._energyPerMove)
    else:
      # Penalise on energy for moving to occupied cell
      self._reduceEnergy(Monster._energyPenaltyOccupied)

      self._behaviourTimer.start()

  def moveRandomly(self):
    ''' Moves monster to the random movable direction '''
    allDirections = [World.North, World.South, World.East, World.West]
    movableDirections = [d for d in allDirections if self.canMove(d)]
    
    if len(movableDirections) != 0:
      self.move(random.choice(movableDirections))

  def isOnFruit(self):
    ''' Returns True if monster is standing on a fruit, and False otherwise '''
    return self._world.getFruitAtPos(self._pos) != None

  def eatFruit(self):
    ''' Eat the fruit which monster is currently standing on.
        Returns type of fruit eaten, or -1 if are not standing on the
        fruit '''
    fruit = self._world.getFruitAtPos(self._pos)

    self.say("Yum, fruit")

    # Return -1 if we are not on the fruit
    if fruit == None:
      return -1

    # Retain energy for eating fruit
    self._increaseEnergy(Fruit._energyForFruit[fruit.type()])
    fruit.vanish()
    
    # Place a new random fruit somewhere in the world
    self._world.addRandomFruit()

    # Return fruit type, so monster can now what it has eaten
    return fruit.type()

  def smell(self):
    ''' Return all the fruit positions within a certain Manhattan Distance.
        The returned object is a list of tuples (fruitPosition, fruitType) '''
    return [(fruit._pos, fruit._type) for fruit in self._world.fruits 
            if (fruit._pos - self._pos).manhattanLength() <= 15]

  def pickItem(self):
    item = self._world.getItemAtPos(self._pos)

    if item != None:
      if item == self._world.rubberRing:
        self.say("Wow! I can swim now.")

      self._items.append(item)

      item.vanish()

      if item == self._world.rubberRing:
        item.setOwner(self)

  def isOnItem(self):
    ''' Returns True if monster is standing on a item, and False otherwise '''
    return self._world.getItemAtPos(self._pos) != None

  def say(self, message, seconds = 1):
    ''' Show speech bubble above the monster with the specified message. Bubble
        dissapears after the specified number of seconds, or lasts forever if seconds is None '''
    self._speechBubble.setMessage(message)
    self._speechBubble.show(seconds)

  def sleep(self, seconds):
    ''' Sleep for the specified number of seconds '''
    self._isSleeping = True
    self._leftSleeping = seconds

    self._sleepTimer.start()

  @Slot()
  def behaviour(self):
    ''' The main behaviour method. Is called each time monster can perform an 
        action. To be implemented by monsters creators '''
    pass 

  def onCreate(self):
    ''' Method called when monster is created. To be implemented by monsters 
        creators '''
    pass

  #=============================================================================
  # End of monster creators API
  #=============================================================================

class DefaultMonster(Monster):

  def onCreate(self):
    self.say("Hi! I am DefaultMonster")

  def behaviour(self):
    if self.isOnFruit():
      self.eatFruit()

    if self.isOnItem():
      self.pickItem()

    # get a list of all fruit positions that are within range
    nearbyFruit = self.smell()
      
    if len(nearbyFruit) > 0:
      # if there are fruit in the list, then try to move towards one
      
      # sort the fruit positions into ascending Manhattan distance order
      pointsSortedByDistance = sorted(nearbyFruit, key = lambda d: (d[0]-self._pos).manhattanLength() )
      
      # ... and select the closest one as the target
      nearestFruitPosition = pointsSortedByDistance[0][0]
      
      # try to move towards that fruit, testing for allowed movement
      if self.pos().x() < nearestFruitPosition.x() and self.canMove(World.East):
        self.move(World.East)
      elif self.pos().x() > nearestFruitPosition.x() and self.canMove(World.West):
        self.move(World.West)
      elif self.pos().y() > nearestFruitPosition.y() and self.canMove(World.North):
        self.move(World.North)
      elif self.pos().y() < nearestFruitPosition.y() and self.canMove(World.South):
        self.move(World.South)
      else:
        # no movement towards the fruit is possible, so try something random instead
        self.moveRandomly()
    else:
      # no fruit in range, so move about randomly
      self.moveRandomly()


