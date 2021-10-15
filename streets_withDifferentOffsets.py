import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
import math
from functools import reduce
import operator
from operator import itemgetter

usedVerticesList = []
streetVerticesList = []
streetCornersList = []
streetCornerVertices = []
# subLines= []
bVerts = [] # vertices for blender
bFaces = [] # faces for blender

vertices = [[1,1], [4,3], [5,6], [3,8], [2,10], [1,9], [5,10], [6,8], [8,8], [8,6], [6,4], [2,8], [4,6], [6,0], [10,4], [7,8], [5,11], [9,5]]
lines = [([1,0],"A"), ([1,2],"B"), ([2,3],"B"), ([3,4],"B"), ([3,5],"A"), ([2,6],"A"), ([2,7],"B"), ([7,15],"A"), ([8,9],"A"), ([9,10],"A"), ([10,2],"A"), ([9,17],"B"), ([17,14],"B"), ([15,8],"B"), ([6,16],"B")]
# lines = [([0,1],"A"), ([1,2],"B"), ([3,2],"B"), ([3,4],"A")]
# lines = [([0,1],"A"), ([1,2],"B")]

# lines = [[3,5], [2,3] ]
# lines = [[1,2], [0,1], [2,7], [7,15], [15,8]]
# lines = [[15,8],[8,9]]
# lines = [[2,10],[2,16], [2,7]]
# lines = [[0,1], [1,2], [2,3], [4,3]  ]

minAngle = 5

# a function to collect data for blender
def blenderize(list, bVerts, bFaces):
	vertCounter = len(bVerts)
	for i, el in enumerate(list):
		tmp = []
		for y, verts in enumerate(el):
			newVert = (verts[0], verts[1], 0)
			bVerts.append(newVert)
			tmp.append(vertCounter)
			vertCounter = vertCounter + 1
		if len(tmp) > 0:
			bFaces.append(tmp)
	result = [bVerts, bFaces]
	return(result)

# a function to sort vertices around a center clockwise
# if center is not passed, it is calculated
# index is necessary when the verList contains other information append
# index is the index where the vertices are
# for example if vertList has the vertex, streetWidth and streetRaius,
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
			ind = findVertIndex(el, vertlist, 0)
			data = vertlist[ind][1]
			result.append([el, data])
	else:
		result = list

	return(result)

# a function to find the index of the given point
# index is needed when the lists is similar to
# [[4.8, 11], [5.2, 11], [5.2, 10], [4.8, 10]]
# and we want to look only at the first element

def findVertIndex(el, list, index = "Null"):
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
		line = [index for index, lines in enumerate(lines) if vert in lines[0]]
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

#function to find the center of the fillet
def findFilletCenter(center, vertList):
	indexO = findVertIndex(center, vertices)

	#it is necessary to select the minimun radius between the two lines
	radius = getMinimumProperty(vertList, "radius")

	#first finds all the parallel lines which are around the center
	parallelList = []
	verts = []
	# print(vertList)
	for i, el in enumerate(vertList):
		vert = el[0]
		verts.append(vert)
		indexVert = findVertIndex(vert, vertices)
		tmpAO = [center, vert]
		# tmpLine = [indexO, indexVert]
		# tmpLine.sort()
		# indexTmpLine = findVertIndex(tmpLine, lines, 0)
		# type = lines[indexTmpLine][1]
		# properties = ["width", "radius"]
		# result = getStreetProperty(properties, type)
		width = el[1][0]
		# print("W/R", vert, width, radius)
		parallelList.append(parallelLine(tmpAO, (width + radius)))

	firstSet = parallelList[0]
	secondSet = parallelList[1]

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
					plt.plot(intersection[0], intersection[1], marker=".", markersize=10, color="red")
					return(intersection)
			else: # lines are parallels
				int = pointPerpendicularToLine(center, lineB, width+radius)
				return(int)
				break


# function to get a point once an origin and the slope are given
# if the distance is not specified, value is 1
# direction from the center need to be indicated
def pointFromCenter(center, slope, direction, distance=1):
	angle = math.atan(slope)
	if (direction == "up"):
		angle = angle + math.pi
	xA = distance * math.cos(angle) + center[0]
	yA = distance * math.sin(angle) + center[1]
	tmp = [xA, yA]
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
				xList.append(pointA[0])
				yList.append(pointA[1])
				if (i < (len(el) -1)):
					pointB = el[i+1]
				else:
					pointB = el[0]
				xList.append(pointB[0])
				yList.append(pointB[1])

			plt.fill(xList, yList, color="red")
			xList = []
			yList = []

# function to draw the initial lines
def drawGraph():
	global lines
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

		plt.plot([xA, xB], [yA, yB], color='orange')

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
				id = float(segment.get("id"))
				for property in properties:
					value = float(segment.find(property).text)
					if (id == 0 and property in toHalf):
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


#read the road property file
tree = ET.parse("description.xml")
root = tree.getroot()

# the internal vertices of a line are sorted [3,1] becomes [1,3]
# this is because it is necessary to have the vertices and lines
# sort with consistency

lines = sortLineVertices(lines)

#sublines it the list of the only vertices, without the street description
# subLines = [item[0] for item in lines]


# for i,el in enumerate(lines):
# 	print(i, el)

#get the list of the vertices used in drawing the streets
#format of usedVerticesList is [vert, [line A, line B, line C]]
usedVerticesList = usedVertices(lines)


#prepare an empty list for the streetVerticesList
for el in lines:
	tmp = []
	streetVerticesList.append(tmp)

#prepare an empty list for the streetCornerVertices
for el in vertices:
	tmp = []
	streetCornerVertices.append(tmp)

#every vertex is parced in order to draw the streets
for el in usedVerticesList:
	# print(el)
	sortedListOfVerts = []
	centerIndex = el[0]
	center = vertices[centerIndex]

	tmpLines = el[1] # the list of the lines belonging to that vertex
	unsortedVerts = []

	if len(tmpLines) == 1: # the line is a start or a end of a line
		# print(center, "starting or ending point of line", tmpLines)
		line = lines[tmpLines[0]]
		streetType = line[1]
		width = getStreetProperty(["width"], streetType)[0]
		verts = line[0]
		vertA = vertices[verts[0]]
		vertB = vertices[verts[1]]
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
			plt.plot(point[0], point[1], marker=".", markersize=10, color="blue")
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
		# and their vertices added to a list
		for lineInd in tmpLines:
			line = lines[lineInd]
			streetType = line[1]
			propertyList = ["width", "radius"]
			properties = getStreetProperty(propertyList, streetType)
			# print(streetType, properties)
			tmpVertices = line[0] # vert A and B of that line
			vertA = vertices[tmpVertices[0]] #vert A coordinates
			vertB = vertices[tmpVertices[1]] #vert B coordinates

			# there is no reason to add the center to the vertices list
			# but one of the 2 vertices is the center!
			if (vertA != center):
				unsortedVerts.append([vertA, properties])
			else:
				unsortedVerts.append([vertB, properties])

		# print("unsorted", unsortedVerts)

		# the vertices are sorted around the center
		sortedListOfVerts = sortVertices(unsortedVerts, center, 0)

		# print("sorted", sortedListOfVerts)

		# every vertex is parced
		for vertIndex, el in enumerate(sortedListOfVerts):
			newFilletCenter = None
			# to avoid to duplicate points when we are in a corner situation
			# this is run only once (if it is a corner)
			if (len(tmpLines) == 2) and (vertIndex == (len(sortedListOfVerts) -1)):
				break
			else: #when it is a node
				#vertA, vertB and center are defining the "corner" around each node
				vertA = el
				if (vertIndex < (len(sortedListOfVerts) -1)):
					vertB = sortedListOfVerts[vertIndex+1]
				else:
					vertB = sortedListOfVerts[0]
				verts = [vertA, vertB]

				# print("verts", verts)
				# look for the center of the fillet
				filletCenter = findFilletCenter(center, verts)
				# plt.text(filletCenter[0], filletCenter[1], "FilletCenter", fontsize = "large", color="Black")
				# filletCenter = filletCenters[0]
				# if len(filletCenters) > 1:
				# 	print("uno extra")
				# else:
				# 	print("nope")


				tempVert = [None, None]
				extraVert = [None, None]


				# if radiuses are different, the smallest one is chosen
				radius = getMinimumProperty(verts, "radius")
				width = getMinimumProperty(verts, "width")

				#at verts A and B correspond two lines, and their perpendiculars
				for i, el in enumerate(verts):
					vert = el[0]
					# width = el[1][0]
					# radius = el[1][1]
					dim = width + radius

					# finds the line index of the line related to that vertex and the center
					# the vertices could be stores either as [vert, center] or [center, vert]
					# but the vertices have been already sorted, so there is no line
					# which is defined as [4,2]
					# an this is why the next if is comparing the indices of the center and of the vert
					elIndex = findVertIndex(vert, vertices)
					toFind = [centerIndex, elIndex]
					toFind.sort()
					lineIndex = findVertIndex(toFind, lines, 0)
					# # finds the street type
					# streetType = lines[lineIndex][1]
					# properties = ["width", "radius"]
					# result = getStreetProperty(properties, streetType)



					# finds a point perpendicular to a parallel of the line, starting
					# from the center of the fillet, at the given distance
					# but some nodes (with angle > 180) require to draw the external, not
					# the internal curve so the offset has to be changed
					# dist = offset
					if type == "node":
						# print(center, vertA, vertB, radiusCenter)
						# print(pointIsLeft(center, vertA, radiusCenter))
						if (pointIsLeft(center, vertA[0], filletCenter)):
						 	# print(pointIsLeft(center, vertA, radiusCenter))
						 	dist = width * 2

					point = pointPerpendicularToLine(filletCenter, [center, vert], radius)
					mainSlope = getLineSlope(filletCenter, point)
					if mainSlope != None:
						mainDirection = getLineDirection(point, filletCenter, mainSlope)



					if (point):
						plt.plot(point[0], point[1], marker=".", markersize=10, color="orange")
						# plt.text(point[0], point[1], "p" + str(i), fontsize = "large", color="Black")
						plt.plot([filletCenter[0], point[0]], [filletCenter[1], point[1]], color="green")

						# add the vertex to the point defining the linear streets
						streetVerticesList[lineIndex].extend([point])

						#these are the points of the corners
						tempVert[i] = point

						# if it is a corner, "the other side" of the corner is to be found
						if type == "corner":
							if testEqualProperty(verts, "width"): # when the 2 widths are the same
								otherSidePoint = pointPerpendicularToLine(filletCenter, [center, vert], radius + width*2)
								if (otherSidePoint):
									plt.plot(otherSidePoint[0], otherSidePoint[1], marker=".", markersize=10, color="blue")
									# plt.text(otherSidePoint[0], otherSidePoint[1], "otherSidePoint", fontsize = "large", color="blue")


							else: # when street sizes are different
								# it is necessary to find this point only once for each couple of points
								if i == 0:
									A = verts[0][0]
									B = verts[1][0]

									halfAngle = (carnot(center, [A, B])) /2 # half size of the bisec
									angle = math.pi/2 - halfAngle # we need the opposite angle
									dist = getDistance(filletCenter, point)
									hypotenuse = dist / math.cos(angle) # length of the hypotenuse
									slopeOA = getLineSlope(filletCenter, point)

									# print(dist, hypotenuse, slopeOA)

									if (slopeOA == None): # line is vertical
										slopeAngle = math.pi/2
										# print("vertical at", centerIndex)
									else: # all other cases
										slopeAngle = math.atan(slopeOA)

									newSlope = math.tan(slopeAngle + angle) # the slope of the hypotenuse
									# print("NewSlope", math.degrees(newSlope), math.degrees(slopeAngle), math.degrees(angle))
									# lineSlope=getLineSlope(A, center)
									# print("lineSlope", A, center, lineSlope)
									# lineSlope=getLineSlope(B, center)
									# print("lineSlope", B, center, lineSlope)

									if (pointIsLeft(center, A, B)):
										newSlope = math.tan(slopeAngle - angle) # the slope of the hypotenuse
										newPoint = pointFromCenter(filletCenter, newSlope, "down", hypotenuse)
									else:
										newSlope = math.tan(slopeAngle + angle)

										newPoint = pointFromCenter(filletCenter, newSlope, "up", hypotenuse) # is the intersection of the two lines we are applying the fillet
									if not(pointIsLeft(filletCenter, point, newPoint)):
										newPoint = pointFromCenter(filletCenter, newSlope, "down", hypotenuse)
										# print("pippo")


									plt.plot(newPoint[0], newPoint[1], marker=".", markersize=10, color="blue")
									# plt.text(newPoint[0], newPoint[1], "NP" + str(lineIndex), fontsize = "large", color="blue")

									slope = getLineSlope(newPoint, center) #the slope between the filletCenter and the corner
									dist = getDistance(newPoint, center) #the distance between the filletCenter and the corner
									if slope != None:
										direction = getLineDirection(center, newPoint, slope)
										newFilletCenter = pointFromCenter(filletCenter, slope, direction, 2 * dist) 	# the newFilleCenter has twice distance between the filletCenter and the corner
																													# and the same slope. It starts from the intersection of the two lines
																													# we are applying the fillet
									else:
										newFilletCenter = [filletCenter[0], filletCenter[1] + 2 * dist]




									plt.plot(newFilletCenter[0], newFilletCenter[1], marker=".", markersize=10, color="blue")
									plt.plot([filletCenter[0], newFilletCenter[0]], [filletCenter[1], newFilletCenter[1]], color="black")
									# plt.plot([newPoint[0], newFilletCenter[0]], [newPoint[1], newFilletCenter[1]], color="black")

								# then the new perpendicular points, starting from the new Fillet center are calculated
								if mainSlope != None:
									if mainSlope == 0:
										otherSidePoint = [newFilletCenter[0] + radius, newFilletCenter[1]]
									else:
										otherSidePoint = pointFromCenter(newFilletCenter, mainSlope, mainDirection, radius)
								else:
									otherSidePoint = [newFilletCenter[0], newFilletCenter[1] + radius]
								plt.plot(otherSidePoint[0], otherSidePoint[1], marker=".", markersize=10, color="orange")
								plt.plot([newFilletCenter[0], otherSidePoint[0]], [newFilletCenter[1], otherSidePoint[1]], color="green")
								# plt.text(otherSidePoint[0], otherSidePoint[1], "otherSidePoint" + str(i), fontsize = "large", color="blue")

							# add the vertex to the point defining the linear streets
							streetVerticesList[lineIndex].extend([otherSidePoint])

							#these are the points of the corners
							extraVert[i] = otherSidePoint


				#corners are tricky and they need a lot of values
				# they are drawn in the next for loop
				# tmpValue = [filletCenter, tempVert[0], tempVert[1], centerIndex, vertA, vertB, type, extraVert[0], extraVert[1], width, radius]
				# streetCornersList.append(tmpValue)

				revertVertices = False
				tmpVertices = []
				tmpExtraVertices = []
				radiusCenter = filletCenter # the center of the fillet
				tmpA = tempVert[0] # point A definig one side of the triangle
				tmpB = tempVert[1] # point B definig one side of the triangle
				# centerIndex = el[3] # the index of the corner
				# vertA = el[4] # vertex A
				# vertB = el[5] # vertex B
				# type = el[6] # if it is a corner or a node
				tmpExtraA = extraVert[0] # when it is a corner, two extra vertices are required
				tmpExtraB = extraVert[1] # when it is a corner, two extra vertices are required
				# width = el[9]
				# radius = el[10] #radius + offset

				#vertices A and B need to be in the correct order
				if (pointIsLeft(radiusCenter, tmpA, tmpB)):
					A = tmpB
					B = tmpA
					extraA = tmpExtraB
					extraB = tmpExtraA
				else:
					A = tmpA
					B = tmpB
					extraA = tmpExtraA
					extraB = tmpExtraB



				# the angle between A, B and the corner
				angle = carnot(radiusCenter, [A, B])

				# the slope of line OA
				slopeOA = getLineSlope(radiusCenter, A)

				if (slopeOA == None): # line is vertical
					slopeAngle = math.pi/2
				else: # all other cases
					slopeAngle = math.atan(slopeOA)

				ind = 1
				#how many times to divide the corner AOB
				divisions = math.ceil(math.degrees(angle) / minAngle)
				if (divisions <= 0):
					divisions = 1

				# the resulting angle
				partialAngle = angle / divisions

				# some nodes (with angle > 180) require to draw the external, not
				# the internal curve
				rad = radius
				if type == "node":
			            center = vertices[centerIndex]
			            # print(center, vertA, vertB, radiusCenter)
			            # print(pointIsLeft(center, vertA, radiusCenter))
			            if (pointIsLeft(center, vertA[0], radiusCenter)):
			                # print(pointIsLeft(center, vertA, radiusCenter))
			                revertVertices = True
			                rad = radius * 2


				# all the vertices defining the curve between A and B are found
				while (ind < divisions):
					# the increased angle
					newAngle = partialAngle * ind

					newSlope = math.tan(slopeAngle - newAngle)
					newPointA = pointFromCenter(radiusCenter, newSlope, "up", rad)
					# newPointB is necessary only in the corner situations
					if type == "corner":
						if newFilletCenter != None:
							newPointB = pointFromCenter(newFilletCenter, newSlope, "up", rad)
						else:
							newPointB = pointFromCenter(radiusCenter, newSlope, "up", rad + width *2)

					if not(pointInsideCorner(newPointA, radiusCenter, [A, B])):
						newPointA = pointFromCenter(radiusCenter, newSlope, "up", -1 * rad)
						if type == "corner":
							if newFilletCenter != None:
								newPointB = pointFromCenter(newFilletCenter, newSlope, "up", -1 * rad)
							else:
								newPointB = pointFromCenter(radiusCenter, newSlope, "up", -1 * (rad + width*2))
					# plt.plot([radiusCenter[0], newPointA[0]], [radiusCenter[1], newPointA[1]], marker=".", markersize=10, color="red")
					# plt.plot([radiusCenter[0], newPointB[0]], [radiusCenter[1], newPointB[1]], marker=".", markersize=10, color="red")

					# vertices are added to the list
					tmpVertices.append(newPointA)
					if type == "corner":
						tmpExtraVertices.append(newPointB)
					ind = ind + 1

				# in case the node has an angle > 180
				if revertVertices:
					tmpVertices = tmpVertices[::-1]
					tmpVertices.insert(0, (B))
					tmpVertices.append(A)
				else:
					tmpVertices.insert(0, A)
					tmpVertices.append(B)

				# the vertices need to be sorted to
				# avoid intersections
				if type == "corner":
					tmpVertices.append(extraB)
					tmpExtraVertices = tmpExtraVertices[::-1]
					tmpVertices.extend(tmpExtraVertices)
					tmpVertices.append(extraA)

				tmpVertices = tmpVertices[::-1]

				# the data of that specific vertes is extended
				streetCornerVertices[centerIndex].extend(tmpVertices)







streetVerticesList = sortList(streetVerticesList)

# data = blenderize(streetVerticesList, bVerts, bFaces)
# finalData = blenderize(streetCornerVertices, data[0], data[1])

drawGraph()
drawStreets(streetVerticesList)
drawStreets(streetCornerVertices)
#
#
#
plt.axis([0, 15, 0, 15])
plt.grid(True)
plt.gca().set_aspect('equal') # to set the aspect ratio to 1

plt.show()
