import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
import math
from functools import reduce
import operator
from operator import itemgetter

import random

debugMain = False

vertices = 	[[1,1], [4,3], [5,6], [3,8], [2,10], [1,9], [5,10], [6,8], [8,8], [8,6],
			[6,4], [2,8], [4,6], [6,0], [10,4], [7,8], [5,11], [9.5,4.5], [2,3], [4,4],
			[6,5], [4.5,4.5], [10.5, 5.5], [9,9], [14,14], [10,10], [14,6], [12,8], [14,10], [0,10],
			[4,12], [8,14], [2,14]
			]
lines = [([1,0],"A"), ([1,2],"B"), ([2,3],"B"), ([3,4],"B"), ([3,5],"A"), ([2,6],"A"), ([2,7],"B"), ([7,15],"A"), ([8,9],"A"), ([9,10],"A"), ([10,2],"A"), ([9,17],"B"), ([17,14],"A"), ([15,8],"B"), ([6,16],"B")]
# lines = [([0,1],"A"), ([1,2],"B"), ([3,2],"B"), ([3,4],"A")]
# lines = [([0,1],"A"), ([1,2],"B")]
# lines = [([0,18],"A"), ([18,19],"B"), ([19,20],"A"), ([20,8],"B")]
# lines = [([0,18],"A"), ([18,19],"B")]
# lines = [([1,0],"A"), ([1,2],"B"), ([2,3],"B"), ([3,4],"B"), ([3,5],"A")]
# lines = [([0,18],"A"), ([18,19],"B"), ([19,21],"A"), ([21,2],"B"), ([2,3],"B"), ([3,4],"B"), ([3,5],"A"), ([2,6],"A"), ([2,7],"B"), ([7,15],"A"), ([8,9],"A"), ([9,10],"A"), ([10,2],"A"), ([9,17],"B"), ([17,14],"A"), ([15,8],"B"), ([6,16],"B"), ([22,17], "B")]
# lines = [([23,25],"B"), ([24,25],"A") , ([25,27],"A"), ([26,27], "B"),  ([27,28], "B"), ([29,30], "B"), ([30,31], "A"), ([30,32], "B")]
# lines = [([23,25],"A"), ([24,25],"A") , ([25,27],"A"), ([26,27], "A"),  ([27,28], "A"), ([29,30], "A"), ([30,31], "A"), ([30,32], "A")]
# lines = [([23,25],"B"), ([24,25],"A") , ([25,27],"A"), ([26,27], "B"),  ([27,28], "B"), ([29,30], "B"), ([30,31], "A"), ([30,32], "B"), ([0,18],"A"), ([18,19],"B"), ([19,21],"A"), ([21,2],"B"), ([2,3],"B"), ([3,4],"B"), ([3,5],"A"), ([2,6],"A"), ([2,7],"B"), ([7,15],"A"), ([8,9],"A"), ([9,10],"B"), ([10,2],"B"), ([9,17],"B"), ([17,14],"A"), ([15,8],"B"), ([6,16],"B"), ([22,17], "B")]

# vertices = [[-10.718745231628418, -10.718745231628418], [10.718745231628418, -10.718745231628418], [-10.718745231628418, 10.718745231628418], [10.718745231628418, 10.718745231628418]]
# lines = [([2, 0], 'B'), ([0, 1], 'A'), ([3, 2], 'A'), ([3,1], 'B')]

# vertices = [[-1.4187122587827616e-07, 11.571640014648438], [-5.785820007324219, 10.021334648132324], [-10.021334648132324, 5.785819053649902], [-11.571640014648438, -4.492888479035173e-07], [-10.021334648132324, -5.785820960998535], [-5.785820484161377, -10.021334648132324], [8.697535349710961e-07, -11.571640014648438], [5.7858195304870605, -10.021334648132324], [10.021334648132324, -5.785819053649902], [11.571640014648438, 1.9451397292868933e-07], [10.021334648132324, 5.785819053649902], [5.785821914672852, 10.021333694458008], [4.394995301026938e-08, 3.283268690109253], [-2.5706377029418945, 4.452475547790527], [-2.8433938026428223, 1.6416343450546265], [-5.141277313232422, -2.3208869492918893e-07], [-2.8433938026428223, -1.6416345834732056], [-2.570638656616211, -4.452476501464844], [3.3098245921792113e-07, -3.283269166946411], [2.5706381797790527, -4.452476501464844], [2.8433947563171387, -1.6416341066360474], [5.141275882720947, 5.3952732059769914e-08], [2.8433947563171387, 1.641634225845337], [2.5706393718719482, 4.452475547790527]]
# lines = [([0, 1], 'A'), ([1, 2], 'B'), ([2, 3], 'A'), ([3, 4], 'B'), ([4, 5], 'B'), ([5, 6], 'B'), ([6, 7], 'A'), ([7, 8], 'B'), ([8, 9], 'B'), ([9, 10], 'A'), ([10, 11], 'B'), ([0, 11], 'A'), ([12, 13], 'B'), ([13, 14], 'A'), ([14, 15], 'A'), ([15, 16], 'A'), ([16, 17], 'A'), ([17, 18], 'B'), ([18, 19], 'A'), ([19, 20], 'A'), ([20, 21], 'A'), ([21, 22], 'B'), ([22, 23], 'B'), ([12, 23], 'A'), ([0,12], 'A'), ([1, 13], 'A'), ([7, 19], 'A'), ([8, 20], 'B'), ([4, 16], 'A'), ([5, 17], 'A'), ([11, 23], 'B'), ([2, 14], 'A'), ([9, 21], 'A'), ([6, 18], 'B'), ([3, 15], 'A'), ([10, 22], 'A')]

# vertices = 	[[1,1], [2,3], [6,4], [8,8], [8,2]]
# lines = [([0,1],'A'), ([1,2],'B'), ([2,3], 'A'), ([2,4], 'B')]
# lines = [([0,1],'A'), ([1,2],'B'), ([1,3], 'A')]

usedVerticesList = []
arcsDict = []
linesDict = []

minAngle = 5
defaults = {"street" : {
				"type" : "A",
				"width" : ".2",
				"radius" : ".3"
			}
}






# a function to sort vertices around a center, clockwise
# if center is not passed, it is calculated
# index is necessary when the verList contains other information
# for example if vertList has the vertex, streetWidth and streetRadius,
# the format is [[[1, 1], [0.2, 0.25]], [[5, 6], [0.2, 0.25]]]
# with index = 0 only [1,1] and [5,6] are taken in account
def sortVertices(vertlist, centerPoint="calc", index = "Null"):
	tmpVertList = []
	if index != "Null":
		for el in vertlist:
			tmpVertList.append(el[index])
	else:
		tmpVertList = vertlist

	if (centerPoint == "calc"):
		center = tuple(map(operator.truediv, reduce(lambda x, y: map(operator.add, x, y), tmpVertList), [len(tmpVertList)] * 2))
	else:
		center = centerPoint

	list = sorted(tmpVertList, key=lambda coord: (-135 - math.degrees(math.atan2(*tuple(map(operator.sub, coord, center))[::-1]))) % 360)

	# if vertList contains more info, this has to be added back to the list
	result = []
	if index != "Null":
		for el in list:
			ind = findElementIndex(el, vertlist, 0)
			data = vertlist[ind][1]
			result.append([el, data])
	else:
		result = list

	return(result)

# a function to get the opposite direction
def oppositeDirection(direction):
	if direction == "up":
		result = "down"
	else:
		result = "up"
	return(result)

# a function to calculate the vertices around the filletCenter
# centerIndex is the index of the point around which rotate all the vertices
# filletCenter is the center of the arc
# A and B define the extremes of the arc
# minAngle is the minimum angle to subdivide the arc
# revert is to force to revert the order of the found vertices
def getArcVertices(centerIndex, filletCenter, vertA, vertB, minAngle, type, rad, revert=False):
	# print(filletCenter, vertA, vertB, minAngle, type)
	revertVertices = False
	tmpVertices = []

	# vertA and vertB need to be in the correct order
	if (pointIsLeft(filletCenter, vertA, vertB)):
		A = vertB
		B = vertA
		# because the angle is > 180, it will be necessary to revert the order of the vertices
		if type == "node":
			revertVertices = True
	else:
		A = vertA
		B = vertB
		# the angle between A, B and the filletCenter
	angle = carnot(filletCenter, [A, B])

	# the slope of line OA
	slopeOA = getLineSlope(filletCenter, A)
	if (slopeOA == None): # line is vertical
		slopeAngle = math.pi/2
	else: # all other cases
		slopeAngle = math.atan(slopeOA)
		# print(centerIndex, slopeAngle)

	#how many times to divide the corner AOB
	divisions = math.ceil(math.degrees(angle) / minAngle)
	if (divisions <= 0):
		divisions = 1

	# the resulting angle
	partialAngle = angle / divisions

	# all the vertices defining the curve between A and B are found
	ind = 1
	while (ind < divisions):
		# the increased angle
		newAngle = partialAngle * ind

		newSlope = math.tan(slopeAngle - newAngle)
		newPointA = pointFromCenter(filletCenter, newSlope, "up", rad)
		if not(pointInsideCorner(newPointA, filletCenter, [A, B])):
			newPointA = pointFromCenter(filletCenter, newSlope, "up", -1 * rad)
		# plt.plot([filletCenter[0], newPointA[0]], [filletCenter[1], newPointA[1]], marker=".", markersize=10, color="red")
		# plt.text(newPointA[0], newPointA[1], "A")

		# vertices are added to the list
		tmpVertices.append(newPointA)
		ind = ind + 1

	# in case the node has an angle > 180
	if revertVertices:
		tmpVertices = tmpVertices[::-1]
		tmpVertices.insert(0, (B))
		tmpVertices.append(A)
	else:
		tmpVertices.insert(0, A)
		tmpVertices.append(B)

	if revert == True:
	 	tmpVertices = tmpVertices[::-1]



	return(tmpVertices)





# A function tu find the line index given a vertex and the index of the center
def findLineIndex(vert, centerIndex):
	elIndex = findElementIndex(vert, vertices)
	toFind = [centerIndex, elIndex]
	toFind.sort()
	result = findElementIndex(toFind, lines, 0)
	return(result)


# a function to find the index of the given point
# index is needed when the lists is similar to
# [[4.8, 11], [5.2, 11], [5.2, 10], [4.8, 10]]
# and we want to look only at the first element
def findElementIndex(el, list, index = "Null"):
	xEl = el[0]
	yEl = el[1]

	tmpList = []
	if index != "Null":
		for el in list:
			tmpList.append(el[index])
	else:
		tmpList = list

	foundX = [x for x, y in enumerate(tmpList) if y[0] == xEl]
	for x in foundX:
		element = tmpList[x]
		if (element[1] == yEl):
			return (x)

#function to find the intersection point of two lines
def intersectionPoint(lineAB, lineCD):
	A = lineAB[0]
	B = lineAB[1]
	C = lineCD[0]
	D = lineCD[1]

	m1 = getLineSlope(A, B)
	m2 = getLineSlope(C, D)

	if (m1 != m2): #when lines are not parallel
		xA = A[0]
		yA = A[1]

		xC = C[0]
		yC = C[1]

		if (m1 == None):
			d2 = yC - (m2 * xC)
			xIntersect = xA
			yIntersect = m2 * xIntersect + d2

		elif (m2 == None):
			d1 = yA - (m1 * xA)
			xIntersect = xC
			yIntersect = m1 * xIntersect + d1
		else:
			d1 = yA - (m1 * xA)
			d2 = yC - (m2 * xC)

			xIntersect = (d1 - d2) / (m2 - m1)
			yIntersect = m1 * xIntersect + d1

		return([xIntersect, yIntersect])
	else: #when lines are parallel
		tmpPoints = (A, B, C, D)
		dupes = [x for n, x in enumerate(tmpPoints) if x in tmpPoints[:n]]
		if dupes:
			return(dupes[0])

# a function to establish if lines are parallel
def linesAreParallel(lineA, lineB):
	result = False

	A = lineA[0]
	B = lineA[1]

	C = lineB[0]
	D = lineB[1]

	slopeA = getLineSlope(A, B)
	slopeB = getLineSlope(C, D)

	if slopeA != None and slopeB != None:
		diffSlope = abs(slopeA-slopeB)
		# if the difference between the two sloped is less than 1e-3, 0.001, the lines
		# are considered parallel
		if (diffSlope < 1e-3):
			result = True
	elif slopeA == slopeB and slopeA == None:
		result = True

	return(result)

# a function to collect the used vertices
def usedVertices(lineList):
	usedVerts = []
	vertCollection = []

	# retrieves all the vertices from the given lines
	for el in lineList:
		line = el[0]
		vertA = line[0]
		vertB = line[1]
		usedVerts.append(vertA)
		usedVerts.append(vertB)
	#only unique values
	usedVerts = set(usedVerts)

	#collect all the lines starting from each vertex
	for vert in usedVerts:
		# finds all the lines which have that vert
		line = [index for index, lineList in enumerate(lineList) if vert in lineList[0]]
		# a collection of vertices where for each vertex are listed the lines starting from that specific vertex
		vertCollection.append([vert, line])
	return(vertCollection)

#function to calculate the distance between two points
def getDistance(vertA, vertB):
	xA = vertA[0]
	yA = vertA[1]

	xB = vertB[0]
	yB = vertB[1]

	dist = math.sqrt((xA-xB)**2 + (yA-yB)**2)
	return(dist)

# a function to the if the value of the properties are the same
def testEqualProperty(verts, property):
	if property == "width":
		index = 0
	else:
		index = 1

	vertA = verts[0]
	vertB = verts[1]
	propA = vertA[1][index]
	propB = vertB[1][index]

	if propA == propB:
		result = True
	else:
		result = False

	return(result)


# a function to get the maximum value between two properties
def getMaximumProperty(verts, property):
	if property == "width":
		index = 0
	else:
		index = 1

	vertA = verts[0]
	vertB = verts[1]
	propA = vertA[1][index]
	propB = vertB[1][index]
	if propA >= propB:
		result = propA
	else:
		result = propB
	return(result)

# a function to get the minimum value between two properties
def getMinimumProperty(verts, property):
	if property == "width":
		index = 0
	else:
		index = 1

	vertA = verts[0]
	vertB = verts[1]
	propA = vertA[1][index]
	propB = vertB[1][index]
	if propA <= propB:
		result = propA
	else:
		result = propB
	return(result)

# function to find the center of the fillet
# radius and width are specified to get the fillets when lines are parallel
def findFilletCenter(center, vertList, givenWidth = None, givenRadius = None):
	# indexO = findElementIndex(center, vertices)
	# print(center, indexO)

	#it is necessary to select the minimun radius between the two lines
	if givenRadius == None:
		radius = getMinimumProperty(vertList, "radius")
	else:
		radius = givenRadius

	#first finds all the parallel lines which are around the center
	parallelList = []
	verts = []
	# print(vertList)
	for i, el in enumerate(vertList):
		vert = el[0]
		verts.append(vert)
		# indexVert = findElementIndex(vert, vertices)
		tmpAO = [center, vert]
		if givenWidth == None:
			width = el[1][0]
		else:
			width = givenWidth
		# print("W/R", vert, width, radius)
		parallelList.append(parallelLine(tmpAO, (width + radius)))

	firstSet = parallelList[0]
	secondSet = parallelList[1]


	if debugMain:
		for line in firstSet:
			A = line[0]
			B = line[1]
			xA = A[0]
			yA = A[1]

			xB = B[0]
			yB = B[1]

			plt.plot([xA, xB], [yA, yB], color="blue")

		for line in secondSet:
			A = line[0]
			B = line[1]
			xA = A[0]
			yA = A[1]

			xB = B[0]
			yB = B[1]

			plt.plot([xA, xB], [yA, yB], color="green")

	# look for the intersections between the 2 sets of 4 lines
	# intersections are always 4, but only the one inside the
	# triangle defined by the center and A and B
	# is the center of the fillet
	for lineA in firstSet:
		for lineB in secondSet:
			intersection = intersectionPoint(lineA, lineB)
			# plt.plot(intersection[0], intersection[1], marker=".",  markersize=10, color="orange")
			if (intersection != None):
				# lines = [lineA, lineB]
				test = pointInsideCorner(intersection, center, verts)
				if (test):
					if debugMain: plt.plot(intersection[0], intersection[1], marker=".", markersize=10, color="red")
					return(intersection)
			else: # lines are parallels
				int = pointPerpendicularToLine(center, lineB, width+radius)
				return(int)
				break


# function to get a point once an origin and the slope are given
# if the distance is not specified, value is 1
# direction from the center need to be indicated
def pointFromCenter(center, slope, direction, distance=1):
	if slope != None:
		angle = math.atan(slope)
		if (direction == "up"):
			angle = angle + math.pi
		xA = distance * math.cos(angle) + center[0]
		yA = distance * math.sin(angle) + center[1]
		tmp = [xA, yA]
	else:
		if direction == "up":
			tmp = [xA, yA + distance]
		else:
			tmp = [xA, yA - distance]

	return(tmp)


# #function to calculate the slope of a line
def getLineSlope(A, B):
	xA = A[0]
	yA = A[1]

	xB = B[0]
	yB = B[1]

	#calculate the slope of the line, m
	if (xB != xA): #the line is not vertical
		m = ((yB-yA)/(xB-xA))

	else: # the line is vertical
		m = None
	return(m)

#function to get the direction "up" or "down" of a line
def getLineDirection(pointA, pointB, m):
	yPointA = pointA[1]
	ypointB = pointB[1]

	if (m >= 0):
		if (yPointA <= ypointB): #direction is up
			direction = "up"
		else:
			direction = "down"
	else:
		if (yPointA <= ypointB): #direction is up
			direction = "down"
		else: direction = "up"

	return(direction)

# a function to return a point perpendicular to a line and passing
# through a certain point
# point is where the perpendicular line is passing
# lineAB is the line to be perpendicular
def pointPerpendicularToLine(point, lineAB, distance):
	if (point): # if lines are pallel, point equals to None
		xPoint = point[0]
		yPoint = point[1]

		vertA = lineAB[0]
		vertB = lineAB[1]

		xA = vertA[0]
		yA = vertA[1]

		m = getLineSlope(vertA, vertB)

		if (m != None): # when the line is not vertical
			if (m == 0): # if the line is horizontal
				perpLine = [[xPoint, yPoint], [xPoint, 0]]
			else: # in all the other cases
				yNewPoint = (-1 * (1/m)) * (0 - xPoint) + yPoint
				perpLine = [[xPoint, yPoint], [0, yNewPoint]]
		else: # when the line is vertical
			perpLine = [[xPoint, yPoint], [0, yPoint]]

		# intersection between the new line an the lineAB
		intersection = intersectionPoint(perpLine, lineAB)
		# plt.plot([xPoint, intersection[0]], [yPoint, intersection[1]], color="green")

		#to determine the direction of the line
		if (m != None):
			if (m == 0):
				if (yPoint >= yA):
					newPoint = [xPoint, yPoint - distance]
				else:
					newPoint = [xPoint, yPoint + distance]
			else:
				direction = getLineDirection(point, intersection, m)
				newPoint = pointFromCenter(point, (-1*(1/m)), direction, distance)
		else:
			if (xPoint >= xA):
				newPoint = [xPoint - distance, yPoint]
			else:
				newPoint = [xPoint + distance, yPoint]
		return(newPoint)


#a function to determine the vertices of the 2 parallel lines
def parallelLine(verts, distance):
	# print(verts, distance)
	vertA = verts[0]
	vertB = verts[1]

	xA = vertA[0]
	yA = vertA[1]

	xB = vertB[0]
	yB = vertB[1]

	#distance between 2 points (hypotenuse length)
	d = getDistance(vertA, vertB)

	#alpha angle (angle in the A corner)
	alphaSin = abs(yA-yB)/d
	alpha = math.asin(alphaSin)

	slope = getLineSlope(vertA, vertB) #if the slope is negative, the calculated angle is 180 - angle

	if (slope !=None and slope < 0):
		alpha = math.pi - alpha

	alphaPerp = alpha + math.pi /2

	a = distance * math.sin(alphaPerp)
	b = distance * math.cos(alphaPerp)

	# every line has 2 parallel lines

	#line AB
	xParA = xA + b
	yParA = yA + a

	xParB = xB + b
	yParB = yB + a

	# line CD
	xParC = xA - b
	yParC = yA - a

	xParD = xB - b
	yParD = yB - a

	tmpAB = [[xParA, yParA], [xParB, yParB]]
	tmpCD = [[xParC, yParC], [xParD, yParD]]

	tmp = []
	tmp.append(tmpAB)
	tmp.append(tmpCD)

	# plt.plot([xParA, xParB], [yParA, yParB], color="blue")
	# plt.plot([xParC, xParD], [yParC, yParD], color="blue")
	return(tmp)



# function to see if a given point is left or right of a line
def pointIsLeft(A, B, testPoint):
	xA = A[0]
	yA = A[1]

	xB = B[0]
	yB = B[1]

	xC = testPoint[0]
	yC = testPoint[1]

	result = ((xB - xA)*(yC - yA) - (yB - yA)*(xC - xA)) > 0
	return(result)


#function to test if a point is within two lines
def pointInsideCorner(P, O, vertices):
	# ref: http://www.cs.cmu.edu/%7Equake/robust.html
	# https://stackoverflow.com/questions/37600118/test-if-point-inside-angle?rq=1
	# NB: To check the orientation of 3 points,
	# the sign should be reversed here,
	# since in this coordinate system y extends downwards.
	# It will not matter for our purpose here though.

	def isCCW(a, b, c):
		return ((a[0] - c[0])*(b[1] - c[1]) - (a[1] - c[1])*(b[0] - c[0])) > 0;

	A = vertices[0]
	B = vertices[1]

	if (pointIsLeft(O, A, B)):
		result = isCCW(O, A, P) and not(isCCW(O, B, P))
	else:
		result = isCCW(O, B, P) and not(isCCW(O, A, P))

	# result = isCCW(O, A, P)
	# print(result)
	return(result)

#a function to sort a list of objects
def sortList(list):
	sorted = []
	for el in list:
		if el:
			sorted.append(sortVertices(el))
	return(sorted)



#a function to draw the final result
def drawStreets(list):
	xList = []
	yList = []

	for index, el in enumerate(list):
		if el:# if el[1]:
			for i, vert in enumerate(el):
				pointA = vert
				# plt.scatter(pointA[0], pointA[1],  color="red")
				# plt.text(pointA[0], pointA[1], i, fontsize = "large", color="red")
				xList.append(pointA[0])
				yList.append(pointA[1])
				if (i < (len(el) -1)):
					pointB = el[i+1]
				else:
					pointB = el[0]
				xList.append(pointB[0])
				yList.append(pointB[1])

			if debugMain:plt.fill(xList, yList, color="red")
			xList = []
			yList = []

# function to draw the initial lines
def drawGraph():
	# global lines
	for index, el in enumerate(lines):
		line = el[0]
		#the index of the vertices defining the line
		A = line[0]
		B = line[1]

		#the coordinates of vertices A and B
		xA = vertices[A][0]
		yA = vertices[A][1]
		xB = vertices[B][0]
		yB = vertices[B][1]

		plt.plot([xA, xB], [yA, yB], color='black')

		plt.text(xA, yA, A, fontsize = "large")
		plt.text(xB, yB, B, fontsize = "large")
		plt.text(((xA + xB) / 2), ((yA + yB) / 2), index, fontsize = "large", color="red")

# a function to sort the vertices which are defining a line
def sortLineVertices(list):
	tmpList = []
	for el in list:
		verts = el[0]
		A = verts[0]
		B = verts[1]
		type = el[1]
		vertices = [A, B]
		vertices.sort()
		# if (A > B):
			# tmp = ([B, A], type)
		# else:
			# tmp = ([A, B], type)
		tmp = (vertices, type)
		tmpList.append(tmp)
	return(tmpList)

# a function to get the offset of that street
def getStreetProperty(properties, type):
	results = []
	toHalf = ["width"]
	for street in root.iter("street"):
		streetType = street.get("type")
		if type == streetType:
			for segment in street.iter("segment"):
				if segment:
					try:
						id = float(segment.get("id"))
					except:
						id = 0
					for property in properties:
						try:
							value = float(segment.find(property).text)
						except:
							value = float(defaults["street"][property])
							# print("default value", value)
						if (id == 0 and property in toHalf):
							value = value / 2
						results.append(value)

	# if the type is not found, it is necessary to use the defaults
	if len(results) == 0:
		# print("using all defaults")
		type = defaults["street"]["type"]
		for property in properties:
			value = float(defaults["street"][property])
			if property in toHalf:
				value = value / 2
			results.append(value)
	return(results)


#function to get the angle between two lines, based on the carnot theorem
def carnot(center, list):
	vertB = list[0]
	vertC = list[1]

	a = getDistance(vertB, vertC)
	b = getDistance(center, vertC)
	c = getDistance(center, vertB)

	cosAlpha = (b**2 + c**2 - a**2)/(2*b*c)
	if cosAlpha < -1:
		cosAlpha = -1
	elif cosAlpha > 1:
		cosAlpha = 1
	alpha = math.acos(cosAlpha)

	return(alpha)

#the main function used to populate the vert list
#every vertex is parced in order to draw the streets
def populateVertices(lines, vertices):
	streetVerticesList = []
	streetCornerVertices = []

	#get the list of the vertices used in drawing the streets
	#format of usedVerticesList is [vert, [line A, line B, line C]]
	global usedVerticesList
	usedVerticesList = usedVertices(lines)

	#prepare an empty list for the streetVerticesList
	for el in lines:
		tmp = []
		streetVerticesList.append(tmp)

	#prepare an empty list for the streetCornerVertices
	for el in vertices:
		tmp = []
		streetCornerVertices.append(tmp)


	for el in usedVerticesList:
		sortedListOfVerts = []
		centerIndex = el[0]
		center = vertices[centerIndex]

		tmpLines = el[1] # the list of the lines belonging to that vertex
		unsortedVerts = []

		if len(tmpLines) == 1: # the line is a starting or a ending of a line
			# print(center, "starting or ending point of line", tmpLines)
			line = lines[tmpLines[0]]
			verts = line[0]
			vertA = vertices[verts[0]]
			vertB = vertices[verts[1]]

			streetType = line[1]
			width = getStreetProperty(["width"], streetType)[0]

			m = getLineSlope(vertA, vertB)
			direction = "none"
			points = []

			if (m and m != 0):
				points.append(pointFromCenter(center, (-1*(1/m)), direction, width))
				points.append(pointFromCenter(center, (-1*(1/m)), direction, -1 * width))
			elif (m == 0):
				points.append([center[0], center[1] + width])
				points.append([center[0], center[1] - width])
			else:
				points.append([center[0] + width, center[1]])
				points.append([center[0] - width, center[1]])
			for point in points:
				if debugMain: plt.plot(point[0], point[1], marker=".", markersize=10, color="blue")
				# plt.text(point[0], point[1], tmpLines, fontsize = "large", color="blue")

				# add the vertex to the point defining the linear streets
				streetVerticesList[tmpLines[0]].append(point)

		else: # the vertex is a corner (len==2) or a node of more than two lines
			if (len(tmpLines) == 2):
				# print(center, "corner between lines", tmpLines)
				type = "corner"
			else:
				# print(center, "node of lines", tmpLines)
				type = "node"

			# all the lines starting from that vertex are parsed
			# and their vertices added to a unsorted list
			for lineInd in tmpLines:
				line = lines[lineInd]

				tmpVertices = line[0] # vert A and B of that line
				vertA = vertices[tmpVertices[0]] #vert A coordinates
				vertB = vertices[tmpVertices[1]] #vert B coordinates

				streetType = line[1]
				propertyList = ["width", "radius"]
				properties = getStreetProperty(propertyList, streetType)
				# print(streetType, properties)

				# there is no reason to add the center to the vertices list
				# because one of the 2 vertices is the center!
				if (vertA != center):
					unsortedVerts.append([vertA, properties])
				else:
					unsortedVerts.append([vertB, properties])

			# the vertices are sorted around the center
			sortedListOfVerts = sortVertices(unsortedVerts, center, 0)

			# every vertex is parced
			for ind, el in enumerate(sortedListOfVerts):
				oppositeFilletCenter = None

				# to avoid to duplicate points when we are in a corner situation
				# this loop is run only once
				if (type == "corner") and (ind == (len(sortedListOfVerts) -1)):
					break

				else: #when it is a node or it the first time the loop is run
					#vertA, vertB and center define the "corner" around each node
					vertA = el
					if (ind < (len(sortedListOfVerts) -1)):
						vertB = sortedListOfVerts[ind+1]
					else:
						vertB = sortedListOfVerts[0]
					verts = [vertA, vertB]


					# check if lines are parallel: in this case a it is necessary to
					# join them with a "s"
					A = verts[0][0]
					B = verts[1][0]

					#when lines are parallel
					# print(linesAreParallel([A,center], [B,center]))
					if linesAreParallel([A,center], [B,center]):
						lineIndexA = findLineIndex(A, centerIndex)
						lineIndexB = findLineIndex(B, centerIndex)

						propA = verts[0][1]
						propB = verts[1][1]

						widthA = propA[0]
						radiusA = propA[1]

						widthB = propB[0]
						radiusB = propB[1]

						# check if lines are aligned
						if widthA == widthB:
							slope = getLineSlope(A, center)

							if slope != None:
								direction = getLineDirection(A, center, slope)
								if slope != 0:
									perpSlopeA = -1/slope
									tmpPointA = pointFromCenter(center, perpSlopeA, direction, widthA)
									tmpPointB = pointFromCenter(center, perpSlopeA, direction, -1 * widthA)
								else:
									tmpPointA = [center[0], center[1] + widthA]
									tmpPointB = [center[0], center[1] - widthA]

							else:
								direction = "up"
								perpSlopeA = 0
								tmpPointA = [center[0] + widthA, center[1]]
								tmpPointB = [center[0] - widthA, center[1]]


							streetVerticesList[lineIndexA].extend([tmpPointA])
							streetVerticesList[lineIndexA].extend([tmpPointB])

							streetVerticesList[lineIndexB].extend([tmpPointA])
							streetVerticesList[lineIndexB].extend([tmpPointB])

							# if type == "corner":
							# 	tmpPoint = pointFromCenter(center, perpSlopeA, oppositeDirection(direction), widthA)
							# 	streetVerticesList[lineIndexA].extend([tmpPoint])
							# 	streetVerticesList[lineIndexB].extend([tmpPoint])

						# else lines are not aligned
						else:
							widthDiff = abs(widthA-widthB) * 2

							# points relative to vert A
							slope = getLineSlope(A, center)
							if slope == None: #lines are vertical
								if A[1] < B[1]:
									factor = -1
								else:
									factor = 1

								perpSlope = 0
								directionA = "up"
								tmpPointA = [center[0], center[1] + factor * widthDiff]
								tmpPointB = [center[0], center[1] - factor * widthDiff]

							else:
								if slope != 0: #generic lines
									directionA = getLineDirection(A, center, slope)
									tmpPointA = pointFromCenter(center, slope, directionA, widthDiff)
									tmpPointB = pointFromCenter(center, slope, directionA, -1 * widthDiff)
									perpSlope = -1/slope
								else: # lines are horizontal
									if A[0] < B[0]:
										factor = -1
									else:
										factor = 1
									directionA = "up"
									tmpPointA = [center[0] + factor * widthDiff, center[1]]
									tmpPointB = [center[0] - factor * widthDiff, center[1]]
									perpSlope = None



							# plt.text(tmpPointA[0], tmpPointA[1], "tmpPointA")
							# plt.text(tmpPointB[0], tmpPointB[1], "tmpPointB")

							parallelLine([A, center], widthA)

							if slope != None and slope >= 0:
								factor = 1
							else:
								factor = -1

							if perpSlope != None:
								if perpSlope != 0:
									A1 = pointFromCenter(tmpPointA, perpSlope, directionA, widthA * factor)
									ausiliaryA1 = pointFromCenter(A, perpSlope, directionA, widthA * factor)

									B1 = pointFromCenter(tmpPointB, perpSlope, directionA, widthB * factor)
									ausiliaryB1 = pointFromCenter(B, perpSlope, directionA, widthB * factor)
								else: #perpendicular is horizontal
									if A[1] < B[1]:
										factor = -1
									else:
										factor = 1

									A1 = [tmpPointA[0] + widthA * factor, tmpPointA[1]]
									ausiliaryA1 = [A[0] + widthA * factor, A[1]]

									B1 = [tmpPointB[0] + widthB * factor, tmpPointB[1]]
									ausiliaryB1 = [B[0] + widthB * factor, B[1]]


							else:
								if A[0] < B[0]:
									factor = 1
								else:
									factor = -1

								A1 = [tmpPointA[0], tmpPointA[1] + widthA * factor]
								ausiliaryA1 = [A[0], A[1] + widthA * factor]

								B1 = [tmpPointB[0], tmpPointB[1] + widthB * factor]
								ausiliaryB1 = [B[0], B[1] + widthB * factor]



							# plt.text(A1[0], A1[1], "A1")
							# plt.text(B1[0], B1[1], "B1")


							dist = 0
							if radiusA >= radiusB:
								rad = radiusA
							else:
								rad = radiusB

							# if (pointIsLeft(center, A1, B1)) or slope == 0:
							# 	invert1 = True
							# 	invert2 = False
							# else:
							# 	invert1 = False
							# 	invert2 = True

							if widthA > widthB:
								if (pointIsLeft(center, A1, B1)):
									invert1 = True
									invert2 = False
								else:
									invert1 = False
									invert2 = True
							else:
								if (pointIsLeft(center, A1, B1)):
									invert1 = False
									invert2 = True
								else:
									invert1 = True
									invert2 = False





							filletCenterA1 = findFilletCenter(A1, [(ausiliaryA1,[dist, rad]), (B1,[dist, rad])], dist, rad)

							pointA = pointPerpendicularToLine(filletCenterA1, [A1, ausiliaryA1], rad)
							streetVerticesList[lineIndexA].extend([pointA])
							if debugMain: plt.plot(pointA[0], pointA[1], marker=".", markersize=10, color="orange")
							# plt.text(pointA[0], pointA[1], "AofA1")
							if debugMain: plt.plot([filletCenterA1[0], pointA[0]], [filletCenterA1[1], pointA[1]], color="green")

							pointB = pointPerpendicularToLine(filletCenterA1, [A1, B1], rad)
							if debugMain: plt.plot(pointB[0], pointB[1], marker=".", markersize=10, color="orange")
							# plt.text(pointB[0], pointB[1], "BofA1")
							if debugMain: plt.plot([filletCenterA1[0], pointB[0]], [filletCenterA1[1], pointB[1]], color="green")

							arcVertices = getArcVertices(centerIndex, filletCenterA1, pointA, pointB, minAngle, type, rad, invert1)
							streetCornerVertices[centerIndex].extend(arcVertices)

							filletCenterB1 = findFilletCenter(B1, [(ausiliaryB1,[dist, rad]), (A1,[dist, rad])], dist, rad)

							pointA = pointPerpendicularToLine(filletCenterB1, [B1, ausiliaryB1], rad)
							streetVerticesList[lineIndexB].extend([pointA])
							if debugMain: plt.plot(pointA[0], pointA[1], marker=".", markersize=10, color="orange")
							if debugMain: plt.plot([filletCenterB1[0], pointA[0]], [filletCenterB1[1], pointA[1]], color="green")
							# plt.text(pointA[0], pointA[1], "AofB1")

							pointB = pointPerpendicularToLine(filletCenterB1, [B1, A1], rad)
							if debugMain: plt.plot(pointB[0], pointB[1], marker=".", markersize=10, color="orange")
							if debugMain: plt.plot([filletCenterB1[0], pointB[0]], [filletCenterB1[1], pointB[1]], color="green")
							# plt.text(pointB[0], pointB[1], "BofB1")

							arcVertices = getArcVertices(centerIndex, filletCenterB1, pointA, pointB, minAngle, type, rad, invert2)
							streetCornerVertices[centerIndex].extend(arcVertices)


							if debugMain: plt.plot(A1[0], A1[1], marker=".", markersize=10, color="orange")
							if debugMain: plt.plot(ausiliaryA1[0], ausiliaryA1[1], marker=".", markersize=10, color="orange")
							if debugMain: plt.plot(B1[0], B1[1], marker=".", markersize=10, color="orange")
							if debugMain: plt.plot(ausiliaryB1[0], ausiliaryB1[1], marker=".", markersize=10, color="orange")
							if debugMain: plt.plot([A1[0], B1[0]], [A1[1], B1[1]], color = "orange")
							if debugMain: plt.plot([ausiliaryA1[0], A1[0]], [ausiliaryA1[1], A1[1]], color = "orange")
							if debugMain: plt.plot([ausiliaryB1[0], B1[0]], [ausiliaryB1[1], B1[1]], color = "orange")

							if type == "corner": # it is necessary to find also the opposite corners
								# vertices are calculated from B to A to have them sorted properly
								if perpSlope != None:
									if perpSlope == 0:
										B2 = pointFromCenter(tmpPointB, perpSlope, directionA, widthB * factor)
										ausiliaryB2 = pointFromCenter(B, perpSlope, directionA, widthB * factor)

										A2 = pointFromCenter(tmpPointA, perpSlope, directionA, widthA * factor)
										ausiliaryA2 = pointFromCenter(A, perpSlope, directionA, widthA * factor)
									else:
										B2 = pointFromCenter(tmpPointB, perpSlope, directionA, -1 * widthB * factor)
										ausiliaryB2 = pointFromCenter(B, perpSlope, directionA,  -1 * widthB * factor)

										A2 = pointFromCenter(tmpPointA, perpSlope, directionA, -1 * widthA * factor)
										ausiliaryA2 = pointFromCenter(A, perpSlope, directionA, -1 * widthA * factor)
								else:
									B2 = [tmpPointB[0], tmpPointB[1] - widthB * factor]
									ausiliaryB2 = [B[0], B[1] - widthB * factor]

									A2 = [tmpPointA[0], tmpPointA[1] - widthA * factor]
									ausiliaryA2 = [A[0], A[1] - widthA * factor]


								filletCenterB2 = findFilletCenter(B2, [(ausiliaryB2,[dist, rad]), (A2,[dist, rad])], dist, rad)

								pointA = pointPerpendicularToLine(filletCenterB2, [B2, ausiliaryB2], rad)
								streetVerticesList[lineIndexB].extend([pointA])
								if debugMain: plt.plot(pointA[0], pointA[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot([filletCenterB2[0], pointA[0]], [filletCenterB2[1], pointA[1]], color="green")

								pointB = pointPerpendicularToLine(filletCenterB2, [B2, A2], rad)
								if debugMain: plt.plot(pointB[0], pointB[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot([filletCenterB2[0], pointB[0]], [filletCenterB2[1], pointB[1]], color="green")

								arcVertices = getArcVertices(centerIndex, filletCenterB2, pointA, pointB, minAngle, type, rad, invert2)
								streetCornerVertices[centerIndex].extend(arcVertices)

								filletCenterA2 = findFilletCenter(A2, [(ausiliaryA2,[dist, rad]), (B2,[dist, rad])], dist, rad)

								pointA = pointPerpendicularToLine(filletCenterA2, [A2, ausiliaryA2], rad)
								streetVerticesList[lineIndexA].extend([pointA])
								if debugMain: plt.plot(pointA[0], pointA[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot([filletCenterA2[0], pointA[0]], [filletCenterA2[1], pointA[1]], color="green")

								pointB = pointPerpendicularToLine(filletCenterA2, [A2, B2], rad)
								if debugMain: plt.plot(pointB[0], pointB[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot([filletCenterA2[0], pointB[0]], [filletCenterA2[1], pointB[1]], color="green")

								arcVertices = getArcVertices(centerIndex, filletCenterA2, pointA, pointB, minAngle, type, rad, invert1)
								streetCornerVertices[centerIndex].extend(arcVertices)

								if debugMain: plt.plot(A2[0], A2[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot([A2[0], B2[0]], [A2[1], B2[1]], color = "orange")
								if debugMain: plt.plot(ausiliaryA2[0], ausiliaryA2[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot([ausiliaryA2[0], A2[0]], [ausiliaryA2[1], A2[1]], color = "orange")
								if debugMain: plt.plot(B2[0], B2[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot(ausiliaryB2[0], ausiliaryB2[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot([ausiliaryB2[0], B2[0]], [ausiliaryB2[1], B2[1]], color = "orange")




					#when lines are not parallel
					else:
						filletCenter = findFilletCenter(center, verts)

						tempVert = [None, None]
						extraVert = [None, None]


						# if radiuses are different, the smallest one is chosen
						rad = getMinimumProperty(verts, "radius")
						minWidth = getMinimumProperty(verts, "width")
						maxWidth = getMaximumProperty(verts, "width")

						#at verts A and B correspond two lines, and their perpendiculars
						for i, el in enumerate(verts):
							vert = el[0]
							# dim = minWidth + radius

							# finds the line index of the line related to that vertex and the center
							# the vertices could be stores either as [vert, center] or [center, vert]
							# but the vertices have been already sorted, so there is no line
							# which is defined as [4,2]
							# an this is why the next "if" is comparing the indices of the center and of the vert
							lineIndex = findLineIndex(vert, centerIndex)


							# finds a point perpendicular to a parallel of the line, starting
							# from the center of the fillet, at the given distance
							# but some nodes (with angle > 180) require to draw the external, not
							# the internal curve so the offset has to be changed
							radius = rad
							if type == "node":
								if (pointIsLeft(center, vertA[0], filletCenter)):
									radius = rad + maxWidth * 2


							point = pointPerpendicularToLine(filletCenter, [center, vert], radius)
							if (point):
								# add the vertex to the point defining the linear streets
								streetVerticesList[lineIndex].extend([point])

								#add the vertex to the list of the vertices defining the radial corners
								tempVert[i] = point

								# mainSlope and mainDirection are necessary to  calculate the "transfer line"
								# of the opposite vertex in case the streets have different widths
								mainSlope = getLineSlope(filletCenter, point)
								if mainSlope != None:
									mainDirection = getLineDirection(point, filletCenter, mainSlope)

								if debugMain: plt.plot(point[0], point[1], marker=".", markersize=10, color="orange")
								if debugMain: plt.plot([filletCenter[0], point[0]], [filletCenter[1], point[1]], color="green")

								# if it is a corner, "the other side" of the corner is to be found
								if type == "corner":
									# in case the street widths are the same
									if testEqualProperty(verts, "width"):
										oppositePoint = pointPerpendicularToLine(filletCenter, [center, vert], radius + minWidth*2)
										if (oppositePoint):
											oppositeFilletCenter = filletCenter
											if debugMain: plt.plot(oppositePoint[0], oppositePoint[1], marker=".", markersize=10, color="red")

									# in case street widths are different
									else:
										# it is necessary to find the opposite fillet center only once for each couple of points
										# first thing is to calculate the transfer line, and then locate the new fillet center
										if i == 0:
											halfAngle = (carnot(center, [A, B])) /2 # half size of the bisec
											angle = math.pi/2 - halfAngle # we need the opposite angle
											dist = getDistance(filletCenter, point)
											hypotenuse = dist / math.cos(angle) # length of the hypotenuse
											slopeOA = getLineSlope(filletCenter, point)

											if (slopeOA == None): # line is vertical
												slopeAngle = math.pi/2
											else: # all other cases
												slopeAngle = math.atan(slopeOA)

											newSlope = math.tan(slopeAngle + angle) # the slope of the hypotenuse

											if (pointIsLeft(center, A, B)):
												newSlope = math.tan(slopeAngle - angle) # the slope of the hypotenuse
												newPoint = pointFromCenter(filletCenter, newSlope, "down", hypotenuse)
											else:
												newSlope = math.tan(slopeAngle + angle)
												newPoint = pointFromCenter(filletCenter, newSlope, "up", hypotenuse) # is the intersection of the two lines to which we are applying the fillet
											if not(pointIsLeft(filletCenter, point, newPoint)):
												newPoint = pointFromCenter(filletCenter, newSlope, "down", hypotenuse)


											if debugMain: plt.plot(newPoint[0], newPoint[1], marker=".", markersize=20, color="green")

											slope = getLineSlope(newPoint, center) 	#the slope between the filletCenter and the corner
											dist = getDistance(newPoint, center) 	#the distance between the filletCenter and the corner

											if slope != None:
												direction = getLineDirection(center, newPoint, slope)
												# the newFilleCenter has twice distance between the filletCenter and the corner
												# and the same slope. It starts from the intersection of the two lines
												# we are applying the fillet
												oppositeFilletCenter = pointFromCenter(filletCenter, slope, direction, 2 * dist)

											else:
												oppositeFilletCenter = [filletCenter[0], filletCenter[1] + 2 * dist]

											if debugMain: plt.plot(oppositeFilletCenter[0], oppositeFilletCenter[1], marker=".", markersize=10, color="blue")
											if debugMain: plt.plot([filletCenter[0], oppositeFilletCenter[0]], [filletCenter[1], oppositeFilletCenter[1]], color="black")
											# plt.plot([newPoint[0], oppositeFilletCenter[0]], [newPoint[1], oppositeFilletCenter[1]], color="black")

										# then the new perpendicular points, starting from the new Fillet center are calculated
										# because it is a rigid translation, the new points are given by the location of the new
										# filleCenter plus the distance between the internal fillet center and the perpendicular point
										oppositePoint = [oppositeFilletCenter[0] + (point[0] - filletCenter[0]), oppositeFilletCenter[1] + (point[1] - filletCenter[1])]

										if debugMain: plt.plot(oppositePoint[0], oppositePoint[1], marker=".", markersize=10, color="orange")
										if debugMain: plt.plot([oppositeFilletCenter[0], oppositePoint[0]], [oppositeFilletCenter[1], oppositePoint[1]], color="green")
										# plt.text(oppositePoint[0], oppositePoint[1], "oppositePoint" + str(i), fontsize = "large", color="blue")

									# add the vertex to the point defining the linear streets
									streetVerticesList[lineIndex].extend([oppositePoint])

									#these are the points of the corners
									extraVert[i] = oppositePoint

						# now that we have the vertices defining the arcs, the point on the arc can be calculated
						pointA = tempVert[0]
						pointB = tempVert[1]
						# print(filletCenter, pointA, pointB, minAngle, radius, type)
						arcVertices = getArcVertices(centerIndex, filletCenter, pointA, pointB, minAngle, type, radius)

						if (extraVert != [None, None]):
							pointA = extraVert[0]
							pointB = extraVert[1]
							# print(oppositeFilletCenter, pointA, pointB, minAngle, type)
							if (testEqualProperty([vertA, vertB], "width")): # they share the same filletCenter, radius is radius + maxWidth *2
								arcExtraVertices = getArcVertices(centerIndex, filletCenter, pointA, pointB, minAngle, type, radius + (maxWidth * 2))
							else:
								arcExtraVertices = getArcVertices(centerIndex, oppositeFilletCenter, pointA, pointB, minAngle, type, radius)
							arcExtraVertices = arcExtraVertices[::-1]
							arcVertices.extend(arcExtraVertices)

						streetCornerVertices[centerIndex].extend(arcVertices)

	streetVerticesList = sortList(streetVerticesList)
	result = [streetVerticesList, streetCornerVertices]
	return(result)




#read the road property file
tree = ET.parse("description.xml")
root = tree.getroot()

# the internal vertices of a line are sorted [3,1] becomes [1,3]
# this is because it is necessary to have the vertices and lines
# sorted with consistency

lines = sortLineVertices(lines)

#sublines it the list of the only vertices, without the street description
# subLines = [item[0] for item in lines]

mainData = populateVertices(lines, vertices)

# plt.figure(figsize=(20,20))
# plt.axis([-20,20,-20,20])
plt.axis([0,15,0,15])

plt.grid(True)
plt.gca().set_aspect('equal') # to set the aspect ratio to 1

drawGraph()

# for el in mainData:
	# drawStreets(el)
drawStreets(mainData[0])
drawStreets(mainData[1])


# find the common point between the segment and the junctions, them extract
# the lines defining the straight segment of the streets. All data is collected
# in linesDict
for id, segment in enumerate(mainData[0]):
	try: #try it is needed because it is used to block all the for loop when the first common vertex is found
		for junction in mainData[1]:
			if len(junction) > 0:
				segment_as_set = set(tuple(i) for i in segment)
				junction_as_set = set(tuple(i) for i in junction)
				# finds the points in common
				intersection = segment_as_set.intersection(junction_as_set)
				#every segment can have only 2 points in common with a junction
				if len(intersection) == 2:
					#convert the set to a list
					intersection = list(intersection)
					# compares the first vertex in the list with the ones from the segment
					# in order to find its index
					vert = intersection[0]
					nextVert = intersection[1]
					for idEl, el in enumerate(segment):
						equal = map(lambda x,y: x == y, vert, el)
						result = reduce(lambda x, y: x and y, equal)
						# because every segment is drawn by 4 points, it
						# is enough to find the first common vert between segment and
						# junction to determine the vertices we want to keep
						if result:
							#check if the next common point is the one before or after the one found
							if idEl == len(segment) - 1:
								nextInd = 0
							else:
								nextInd = idEl + 1
							equal = map(lambda x,y: x == y, nextVert, segment[nextInd])
							result = reduce(lambda x, y: x and y, equal)


							# r = random.random()
							# b = random.random()
							# g = random.random()
							# color = (r, g, b)

							if result: #in case the other common vertex is the next
								endingA = idEl - 1
								endingB = nextInd +1
								if endingA < 0:
									endingA = len(segment) -1
								if endingB > len(segment) -1:
								 	endingB = 0

							else: #when it is the vertex before
								endingA = idEl + 1
								endingB = idEl - 2
								if endingA > len(segment) -1:
									endingA = 0
								if endingB < 0:
									endingB = len(segment) + endingB

							endingVertA = segment[endingA]
							endingVertB = segment[endingB]
							streetType = lines[id][1]

							# plt.plot([vert[0], endingVertA[0]], [vert[1], endingVertA[1]], color=color)
							# plt.plot([nextVert[0], endingVertB[0]], [nextVert[1], endingVertB[1]], color=color)
							# plt.text(vert[0], vert[1], (id, streetType), color=color)
							# plt.text(nextVert[0], nextVert[1], (lines[id][0][0], lines[id][0][1]), color=color)


							tmp = {
									"vertA" : list(vert),
									"vertB" : list(endingVertA),
									"streetType" : streetType,
									"sourceLine" : id,
									"relatedVertA" : lines[id][0][0],
									"relatedVertB" : lines[id][0][1]
							}
							linesDict.append(tmp)
							tmp = {
									"vertA" : list(nextVert),
									"vertB" : list(endingVertB),
									"streetType" : streetType,
									"sourceLine" : id,
									"relatedVertA" : lines[id][0][0],
									"relatedVertB" : lines[id][0][1]
							}
							linesDict.append(tmp)

							raise StopIteration # the loop can be blocked

	except StopIteration:
		pass

# for el in linesDict:
# 	print(el)

#collect all the arc which are defining the corners. Arcs are collected in arcsDict
for idVert, arc in enumerate(mainData[1]):
	if len(arc) > 0: # when the vertex is unused or a start/end of the line, there is no corresponding arc
		# look for the lines related to that vertex
		found = [x for x, y in enumerate(usedVerticesList) if y[0] == idVert][0]
		foundIds = []
		for idLine, line in enumerate(usedVerticesList[found][1]):

			# tmpLines = []
			vertToTest = []
			counter = 0
			# finds in linesDict the lines which have "line" as "sourceLine"
			for el in linesDict:
				sourceLine = el["sourceLine"]
				if sourceLine == line:
					counter += 1
					# tmpLines.append(el)
					vertToTest.append(el["vertA"])
					vertToTest.append(el["vertB"])
					# there can't be more than 2 lines
					if (counter == 2):
						break

			#look for the indices of the common points between arc and lines
			for elToTest in vertToTest:
				found = [x for x, y in enumerate(arc) if y == elToTest]
				if len(found) > 0:
					foundIds.append(found[0])
		foundIds.sort()
		numberOfArcs = len(foundIds)/2
		# print("numberOfArcs", numberOfArcs)
		i = 0
		splitIndex = 0
		if foundIds[0] == 0 and foundIds[1] != 1:  # split is between the last entry and the first
			splitIndex = 1

		#split the junctions in their relative arcs
		while i < numberOfArcs:
			if i == 0:
				splitFrom = foundIds[splitIndex + i * 2] + 1
				tmp = {"relatedVert" :idVert,
						"arc" : arc[:splitFrom]
						}
				# splitArcs.append(arc[:splitFrom])
				# print("splitting", splitFrom)
			elif i < numberOfArcs-1:
				if splitIndex + i * 2 + 1 > len(foundIds) -1:
					splitFrom = foundIds[splitIndex + i * 2 -1]
					splitTo = foundIds[len(foundIds) -1]
				else:
					splitFrom = foundIds[splitIndex + i * 2 -1]
					splitTo = foundIds[splitIndex + i * 2 + 1]
				# print("splitting", splitFrom,splitTo)
				tmp = {"relatedVert" :idVert,
						"arc" : arc[splitFrom:splitTo]
						}
				# splitArcs.append(arc[splitFrom:splitTo])
			else:
				if splitIndex + i * 2 + 1 > len(foundIds) -1:
					splitFrom = foundIds[splitIndex + i * 2 -1]
					# splitTo = foundIds[len(foundIds) -1]
				else:
					splitFrom = foundIds[splitIndex + i * 2]
					# splitTo = foundIds[splitIndex + i * 2 + 1]
				# print("splitting", splitFrom)
				tmp = {"relatedVert" :idVert,
						"arc" : arc[splitFrom:]
						}
				# splitArcs.append(arc[splitFrom:])
			arcsDict.append(tmp)
			i += 1

# for i, el in enumerate(arcsDict):
# 	arc = el["arc"]
# 	r = random.random()
# 	b = random.random()
# 	g = random.random()
# 	color = (r, g, b)
# 	# print(arc)
# 	for vert in arc:
# 		plt.plot(vert[0], vert[1], marker=".", markersize=10, color=color)

# for el in linesDict:
# 	print(el)
#
# for el in arcsDict:
# 	print(el)




# A function to find the common vertex between the line and the corresponding arc
# foundLineIndex is the index of the line we are creating with this function
# line is the line we are testing, sourceVert is the starting vert of that line,
# missingVert is the vertex that has not be tested: this happen when the routine starts
# because every line is defined by two vertices and the routing goes in one direction.
# In this way, when the routine finds the end of the line, it goes backwards to cover
# the missing part of the segment
def findNextArc(foundLineIndex, line, sourceVert="", missingVert=""):
	if len(newLines) == foundLineIndex:
		tmp = []
		newLines.append(tmp)
	color="red"
	verts = []
	relatedVerts = []

	vertA = line["vertA"]
	vertB = line["vertB"]
	relatedVerts.append(line["relatedVertA"])
	relatedVerts.append(line["relatedVertB"])

 	# verts are the vertices to test
	# if the one vert of the line has been tested, it is not added
	if vertA != sourceVert:
		verts.append(vertA)

	if vertB != sourceVert:
		verts.append(vertB)

	plt.plot([vertA[0], vertB[0]],[vertA[1], vertB[1]], color=color)

	# if missingVert is defined and it is not part of the current line, the current
	# line is removed from the list of the lines to parse in the next iteration
	if missingVert != "" and missingVert not in verts:
		linesToTest.remove(line)

	# vertices to test to find the common point with the arc
	for vertId in relatedVerts:
		# look for the vertices which are not either a start or a end
		for el in usedVerticesList:
			id = el[0]
			if vertId == id:
				tmpVerticesList = el[1]
				break #once it is found, there is no point to continue the loop
		if len(tmpVerticesList) > 1:
			# look for the arc related to that vertId
			for idArc, arc in enumerate(arcsDict):
				relatedVertInArc = arc["relatedVert"]
				if relatedVertInArc == vertId:
					# check if arc and line have a vertex in common
					# it can be either the first or the last of the list
					arcVertices = arc["arc"]
					vertToTest = []
					vertToTest.append(arcVertices[0])
					vertToTest.append(arcVertices[-1])
					#verts and relatedVerts are not corresponding (A doesn't correspond to relatedA) because
					# the way the vertices are extrapolated, it is necessary to check both
					for i, testingVert in enumerate(verts):
						foundId = [x for x, y in enumerate(vertToTest) if y == testingVert]
						if len(foundId) > 0:
							vertFound = vertToTest[foundId[0]]
							if vertFound == vertToTest[0]:
								nextVertex = vertToTest[1]
							else:
								nextVertex = vertToTest[0]


							for vert in arcVertices:
								plt.plot(vert[0], vert[1], marker=".", markersize=10, color=color)

							#lines and arcs are added to the newLines library
							newLines[foundLineIndex].extend([line])
							newLines[foundLineIndex].extend([arc])

							# the found arc can be removed from the arcsDict
							arcsDict.remove(arc)

							# once the common verts is found, it is necessary to find the line attached to that arc
							# the current line can be removed
							try:
								linesToTest.remove(line)
							except:
								pass
							for lineToFind in linesToTest:
								tmpVerts = []
								vertA = lineToFind["vertA"]
								vertB = lineToFind["vertB"]
								tmpVerts.append(vertA)
								tmpVerts.append(vertB)
								# if the vert correspond in that line, the line and other data is passed recursively to the function
								for vert in tmpVerts:
									if vert == nextVertex:
										# if verts has 2 vertices, which means that the loop is starting with that line
										# and if i == 0, which means that we found the vertex, but the other has been not tested
										# it is necessary, in this case, to save the missing vertex and then test it afterwards
										# in case the value was already set, it is not changed
										if missingVert == "":
											if len(verts) == 2:
												if i == 0: missingVert = verts[1]
												else: missingVert = verts[0]
										findNextArc(foundLineIndex, lineToFind, nextVertex, missingVert)
							if missingVert != "":
								findNextArc(foundLineIndex, line, missingVert)
							else:
								return()


linesToTest = linesDict
newLines = []
foundLineIndex = 0
while len(linesToTest) > 0:
	findNextArc(foundLineIndex, linesToTest[0])
	foundLineIndex += 1
	# print("lines to go ", len(linesToTest))

# for segment in newLines:
# 	for i, el in enumerate(segment):
# 		print(i, el)



plt.show()
