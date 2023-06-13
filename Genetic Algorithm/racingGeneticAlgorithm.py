import pygame
pygame.init()
import math
import random
import os
from PIL import Image
import numpy as np

# variables
windowSize = [1920,1080]
pixelSize = 5
tilePixels = 32
tileSize = pixelSize*tilePixels
fps = 2000
quit = False
fillColour = (102,232,77)
humanCar = True
track1Pos = [0,0]
track2Pos = [6*tileSize,0]
treeDensity = 1000
numberOfCars = 200
carCutoff = 20
numberOfChildren = 9
initialBrainSize = 100
brainExpansion = 1
mutations = 5
maxBrain = 10000000
drawBackground = True
generation = 0
generationGap = 1

cars = []

track = [
[0,0,0,0,0,0],
[4,1,1,1,1,3],
[5,3,4,1,1,6],
[0,2,5,1,3,0],
[0,5,7,3,2,0],
[0,0,0,5,6,0]]

checkpoints = [[3,4],[3,5],[4,5],[4,4],[4,3],[3,3],[2,3],[2,2],[3,2],[4,2],[5,2],[5,1],[4,1],[3,1],[2,1],[1,1],[0,1],[0,2],[1,2],[1,3],[1,4],[2,4]]

# find starting postion
startPos = [0,0]
for i in enumerate(track):
	for j in enumerate(i[1]):
		if j[1] >= 7:
			startPos = [j[0]+0.5, i[0]+0.5]
			startAngle = 0

# load images
groundTiles = [pygame.image.load(f"images/ground{i+1}.png") for i in range(9)]
wallTiles = [pygame.image.load(f"images/wall{i+1}.png") for i in range(9)]
carSprite = pygame.image.load("images/car.png")

# pygame setup
clock = pygame.time.Clock()
os.environ['SDL_VIDEO_CENTERED'] = '1'
win = pygame.display.set_mode(windowSize)

# car object
class car(object):
	# initiate object
	def __init__(self, pos, angle, brain):
		self.pos = pos #game_units
		self.angle = angle #rad
		self.brain = brain.copy() #array of inputs
		self.velocity = 0 #game_units/tick
		self.acceleration = 0.006 #game_units/tick^2
		self.deceleration = 0.001 #game_units/tick^2
		self.turningSpeed = 0.5 #rad/tick
		self.turningFriction = 0.01 #game_units/tick^2
		self.dead = False #keeps track of if collided with wall
		self.score = 0 #reward
		self.checkpoint = 0 #keeps track of index of latest chechpoint obtained
		self.time = 0
		self.finishTime = 0
		self.done = False

	# takes an input array, [forward = 1/backward = -1, left = 1/right = -1]
	def inputs(self, directions):
		# handle forward/backward
		if not self.dead and not self.done:
			if directions[0] == 1:
				self.accelerate()
			elif directions[0] == -1:
				self.decelerate()
			# handle left/right
			if directions[1] == 1:
				self.turnLeft()
			elif directions[1] == -1:
				self.turnRight()

	# handles running the input function if the car is still alive
	def callInputs(self):
		if self.time < len(self.brain):
			self.inputs(self.brain[self.time])

	# accelerates the car for a tick
	def accelerate(self):
		self.velocity += self.acceleration

	# decelerates the car for a tick
	def decelerate(self):
		self.velocity -= self.deceleration

	# turns the car left for a tick
	def turnLeft(self):
		self.angle += self.turningSpeed
		if self.velocity > 0:
			self.velocity -= abs(self.turningFriction*self.velocity)
		if self.velocity < 0:
			self.velocity += abs(self.turningFriction*self.velocity)

	# turns the car right for a tick
	def turnRight(self):
		self.angle -= self.turningSpeed
		if self.velocity > 0:
			self.velocity -= abs(self.turningFriction*self.velocity)
		if self.velocity < 0:
			self.velocity += abs(self.turningFriction*self.velocity)

	# applies velocities
	def move(self):
		if not self.dead and not self.done:
			self.pos[0] += self.velocity*math.cos(self.angle)
			self.pos[1] -= self.velocity*math.sin(self.angle)

			self.collide()
			self.handleChechpoint()
		
		self.time += 1

	# detects if the car has collided with anything, returns a bool of the result
	def collide(self):
		if collisionMap.getpixel((self.pos[0]*tilePixels, self.pos[1]*tilePixels))[2] == 255:
			self.dead = True

	# handles collecting checkpoints
	def handleChechpoint(self):
		if self.checkpoint < len(checkpoints) and [int(self.pos[0]), int(self.pos[1])] == checkpoints[self.checkpoint]:
			self.checkpoint += 1

		# executes various checks to see how far the next checkpoint is from the car
		if self.checkpoint == len(checkpoints) and not self.done:
			if int(self.pos[0]) != checkpoints[0][0]:
				delX = min(abs(checkpoints[0][0] - self.pos[0]), abs(checkpoints[0][0] + 1 - self.pos[0]))
			else:
				delX = 0
			if int(self.pos[1]) != checkpoints[0][1]:
				delY = min(abs(checkpoints[0][1] - self.pos[1]), abs(checkpoints[0][1] + 1 - self.pos[1]))
			else:
				delY = 0

			if delX + delY < 0.5:
				global maxBrain, drawBackground
				self.finishTime = self.time
				drawBackground = True
				maxBrain = self.finishTime + 2
				self.done = True


	# calculate the score of the car based off the checkpoint number and the distance to the next checkpoint
	def calculateScore(self):
		
		# used if the car has not yet reached the end, the score is based off the checkpoint number and the distance to next checkpoint
		if self.checkpoint != len(checkpoints):
			if int(self.pos[0]) != checkpoints[self.checkpoint][0]:
				delX = 1 - min(abs(checkpoints[self.checkpoint][0] - self.pos[0]), abs(checkpoints[self.checkpoint][0] + 1 - self.pos[0]))
			else:
				delX = 0
			if int(self.pos[1]) != checkpoints[self.checkpoint][1]:
				delY = 1 - min(abs(checkpoints[self.checkpoint][1] - self.pos[1]), abs(checkpoints[self.checkpoint][1] + 1 - self.pos[1]))
			else:
				delY = 0

			self.score = self.checkpoint + delX + delY

		# used if the car has reached the end, checkpoints no longer matter and the score is based off the time taken to get to the end
		else:
			if int(self.pos[0]) != checkpoints[0][0]:
				delX = 1 - min(abs(checkpoints[0][0] - self.pos[0]), abs(checkpoints[0][0] + 1 - self.pos[0]))
			else:
				delX = 0
			if int(self.pos[1]) != checkpoints[0][1]:
				delY = 1 - min(abs(checkpoints[0][1] - self.pos[1]), abs(checkpoints[0][1] + 1 - self.pos[1]))
			else:
				delY = 0

			if self.done:
				self.score = 1000000 - self.finishTime

			else:
				self.score = self.checkpoint + delX + delY


	# handles mutating the current brain
	def mutate(self):
		for i in range(mutations):
			self.brain = self.brain[:]
			self.brain[biasedRandom(0,len(self.brain)-1)][random.randint(0,1)] = random.randint(-1,1)

	# draws the car to the screen
	def draw(self, offset):
		rotatedSprite = pygame.transform.rotate(carSprite, self.angle*180/math.pi)
		rotatedRect = rotatedSprite.get_rect(center = carSprite.get_rect(center = [self.pos[0]*tileSize+offset, self.pos[1]*tileSize]).center)

		win.blit(rotatedSprite, rotatedRect)


# enter a min and a max value and it will return a random value biased to the max
def biasedRandom(minimum, maximum):
	randomRange = 0
	for i in range(1, maximum-minimum+2):
		randomRange += i

	randomValue = random.randint(0,randomRange)

	index = minimum
	searchValue = 0
	for i in range(1, maximum-minimum+2):
		searchValue += i
		if searchValue >= randomValue:
			break
		index += 1

	return index

# draws the ground at a given top left coordinate
def drawGround(pos):
	for i in enumerate(track):
		for j in enumerate(i[1]):
			win.blit(groundTiles[j[1]], (pos[0] + j[0]*tileSize, pos[1] - pixelSize + i[0]*tileSize))

# draws the walls at a given top left coordinate
def drawWalls(pos):
	for i in enumerate(track):
		for j in enumerate(i[1]):
			win.blit(wallTiles[j[1]], (pos[0] + j[0]*tileSize, pos[1] - pixelSize + i[0]*tileSize))

# renders a png of the whole background image
def renderBackground():
	background = Image.new('RGBA', windowSize, (0,0,0,0))
	
	groundTiles = [Image.open(f"images/ground{i+1}.png") for i in range(9)]
	wallTiles = [Image.open(f"images/wall{i+1}.png") for i in range(9)]

	renderTrees()

	treeOverlay = Image.open("rendered/treeOverlay.png")

	for i in enumerate(track):
		for j in enumerate(i[1]):

			background.paste(groundTiles[j[1]], (track1Pos[0] + j[0]*tileSize, track1Pos[1] - pixelSize + i[0]*tileSize),groundTiles[j[1]])
			background.paste(wallTiles[j[1]], (track1Pos[0] + j[0]*tileSize, track1Pos[1] - pixelSize + i[0]*tileSize),wallTiles[j[1]])
			background.paste(groundTiles[j[1]], (track2Pos[0] + j[0]*tileSize, track2Pos[1] - pixelSize + i[0]*tileSize),groundTiles[j[1]])
			background.paste(wallTiles[j[1]], (track2Pos[0] + j[0]*tileSize, track2Pos[1] - pixelSize + i[0]*tileSize),wallTiles[j[1]])


	background.paste(treeOverlay, (0,0), treeOverlay)

	background.save(f"rendered/background.png")

# renders a png of the collision map
def renderCollisions():
	collisionMap = Image.new('RGBA', (tilePixels*6, tilePixels*6), (0,0,0,0))
	
	collisionTiles = [Image.open(f"images/collision{i+1}.png") for i in range(9)]

	for i in enumerate(track):
		for j in enumerate(i[1]):

			collisionMap.paste(collisionTiles[j[1]], (track1Pos[0] + j[0]*tilePixels, track1Pos[1] + i[0]*tilePixels),collisionTiles[j[1]])

	collisionMap.save(f"rendered/collisionMap.png")

# renders a grass map as well as a tree overlay
def renderTrees():
	grassMap = Image.new('RGBA', (tilePixels*6, tilePixels*6), (0,0,0,0))
	
	grassTiles = [Image.open(f"images/grass{i+1}.png") for i in range(9)]

	for i in enumerate(track):
		for j in enumerate(i[1]):

			grassMap.paste(grassTiles[j[1]], (track1Pos[0] + j[0]*tilePixels, track1Pos[1] + i[0]*tilePixels),grassTiles[j[1]])

	grassMap.save(f"rendered/grassMap.png")

	treeSprite = Image.open("images/tree.png")
	treeOverlay = Image.new('RGBA', windowSize, (0,0,0,0))

	trees = []

	for i in range(treeDensity):
		treePos = [random.randint(0,6*tilePixels-1),random.randint(0,6*tilePixels-1)]


		if grassMap.getpixel((treePos[0],treePos[1]))[2] == 255:
			if random.randint(0,1) == 1:
				treePos = [treePos[0]+6*tilePixels, treePos[1]]
			trees.append([treePos[1],treePos[0]])

	trees.sort()

	newTrees = [[i[1], i[0]] for i in trees]

	for tree in newTrees:
		treeOverlay.paste(treeSprite, ((tree[0]-4)*pixelSize, (tree[1]-11)*pixelSize),treeSprite)

	treeOverlay.save(f"rendered/treeOverlay.png")

# main draw function - handles drawing/calling seperate draw funtions
def draw():
	win.fill(fillColour)

	if drawBackground:
		win.blit(background, (0,0))

	for _car in cars:
		_car.draw(0)

	cars[0].draw(6*tileSize)

	pygame.display.update()

# spawns default cars (generation 1)
def setupCars():
	global cars

	for i in range(numberOfCars):
		cars.append(car(startPos[:], startAngle, [[random.randint(-1,1), random.randint(-1,1)] for j in range(initialBrainSize)]))

# handles going from generation to generation
def newGeneration():
	global cars, generation

	# calculate scores of all final cars
	scores = []

	for _car in enumerate(cars):
		_car[1].calculateScore()
		scores.append([_car[1].score, _car[0]])

	# only keep best cars
	scores.sort()
	scores = scores[::-1]
	scores = scores[0:carCutoff]

	print(generation, len(cars[0].brain), scores[0][0])

	# increase the length of the surviving cars brains so each generation can last longer and learn more of the track
	brains = []
	for value in scores:
		current_brain = cars[value[1]].brain
		
		if generation % generationGap == 0 and len(current_brain) < maxBrain:
			for i in range(brainExpansion):
				current_brain.append(current_brain[-1])

		brains.append(current_brain)

	# create and mutate offspring
	cars = []
	for brain in brains:
		cars.append(car(startPos[:], startAngle, brain))

		for i in range(numberOfChildren):
			newBrain = []
			for subBrain in brain:
				subInputs = []
				for subInput in subBrain:
					subInputs.append(subInput)
				newBrain.append(subInputs)


			cars.append(car(startPos[:], startAngle, newBrain))
			cars[-1].mutate()

	generation += 1

 

# INITIAL SETUP
renderBackground()
renderCollisions()

setupCars()

# load sprites
background = pygame.image.load("rendered/background.png")
collisionMap = Image.open("rendered/collisionMap.png")

# game loop
while not quit:
	clock.tick(fps)
		
	for event in pygame.event.get():
		#exit
		if event.type == pygame.QUIT:
			quit = True

	for _car in cars:
		_car.callInputs()
		_car.move()

	# update screen
	if drawBackground:
		draw()
		fps = 60

	if cars[0].time > len(cars[0].brain):
		print(clock.get_fps())
		newGeneration()

# exit
pygame.quit()