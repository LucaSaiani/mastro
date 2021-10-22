import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
import math
from functools import reduce
import operator
from operator import itemgetter

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
lines = [([23,25],"B"), ([24,25],"A") , ([25,27],"A"), ([26,27], "B"),  ([27,28], "B"), ([29,30], "B"), ([30,31], "A"), ([30,32], "B"), ([0,18],"A"), ([18,19],"B"), ([19,21],"A"), ([21,2],"B"), ([2,3],"B"), ([3,4],"B"), ([3,5],"A"), ([2,6],"A"), ([2,7],"B"), ([7,15],"A"), ([8,9],"A"), ([9,10],"B"), ([10,2],"B"), ([9,17],"B"), ([17,14],"A"), ([15,8],"B"), ([6,16],"B"), ([22,17], "B")]

# vertices = [[-10.718745231628418, -10.718745231628418], [10.718745231628418, -10.718745231628418], [-10.718745231628418, 10.718745231628418], [10.718745231628418, 10.718745231628418]]
# lines = [([2, 0], 'A'), ([0, 1], 'B'), ([3, 2], 'B'), ([3,1], 'A')]

minAngle = 5

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

    #how many times to divide the corner AOB
    divisions = math.ceil(math.degrees(angle) / minAngle)
    if (divisions <= 0):
        divisions = 1

    # the resulting angle
    partialAngle = angle / divisions

    # some nodes (with angle > 180) require to draw the external, not
    # the internal curve: the radius value is multiplied by 2
    # rad = radius
    # if type == "node":
    # 		center = vertices[centerIndex]
    # 		# print(center, A, filletCenter)
    # 		if pointIsLeft(center, vertA, filletCenter):
    # 			revertVertices = True
    # 			print(center, vertA, filletCenter)


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

    if revert == False:
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

    if (slopeA == slopeB):
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
    indexO = findElementIndex(center, vertices)

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
        indexVert = findElementIndex(vert, vertices)
        tmpAO = [center, vert]
        if givenWidth == None:
            width = el[1][0]
        else:
            width = givenWidth
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

#the main function used to populate the vert list
#every vertex is parced in order to draw the streets
def populateVertices(lines, vertices):
    streetVerticesList = []
    streetCornerVertices = []

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


    for el in usedVerticesList:
        # print(el)
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

                            if type == "corner":
                                tmpPoint = pointFromCenter(center, perpSlopeA, oppositeDirection(direction), widthA)
                                streetVerticesList[lineIndexA].extend([tmpPoint])
                                streetVerticesList[lineIndexB].extend([tmpPoint])

                        else:
                            widthDiff = abs(widthA-widthB) * 2

                            # points relative to vert A
                            slope = getLineSlope(A, center)
                            if slope == None:
                                perpSlope = 0
                                directionA = "up"
                                tmpPointA = [center[0], center[1] + widthDiff]
                                tmpPointB = [center[0], center[1] - widthDiff]
                            else:
                                directionA = getLineDirection(A, center, slope)
                                tmpPointA = pointFromCenter(center, slope, directionA, widthDiff)
                                tmpPointB = pointFromCenter(center, slope, directionA, -1 * widthDiff)
                                if slope == 0:
                                    perpSlope = None
                                else:
                                    perpSlope = -1/slope

                            parallelLine([A, center], widthA)

                            if slope != None and slope >= 0:
                                factor = 1
                            else:
                                factor = -1

                            if perpSlope != None:
                                A1 = pointFromCenter(tmpPointA, perpSlope, directionA, widthA * factor)
                                ausiliaryA1 = pointFromCenter(A, perpSlope, directionA, widthA * factor)

                                B1 = pointFromCenter(tmpPointB, perpSlope, directionA, widthB * factor)
                                ausiliaryB1 = pointFromCenter(B, perpSlope, directionA, widthB * factor)
                            else:
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
                                    invert1 = False
                                    invert2 = True
                                else:
                                    invert1 = True
                                    invert2 = False
                            else:
                                if (pointIsLeft(center, A1, B1)):
                                    invert1 = True
                                    invert2 = False
                                else:
                                    invert1 = False
                                    invert2 = True





                            filletCenterA1 = findFilletCenter(A1, [(ausiliaryA1,[dist, rad]), (B1,[dist, rad])], dist, rad)

                            pointA = pointPerpendicularToLine(filletCenterA1, [A1, ausiliaryA1], rad)
                            streetVerticesList[lineIndexA].extend([pointA])
                            plt.plot(pointA[0], pointA[1], marker=".", markersize=10, color="orange")
                            # plt.text(pointA[0], pointA[1], "AofA1")
                            plt.plot([filletCenterA1[0], pointA[0]], [filletCenterA1[1], pointA[1]], color="green")

                            pointB = pointPerpendicularToLine(filletCenterA1, [A1, B1], rad)
                            plt.plot(pointB[0], pointB[1], marker=".", markersize=10, color="orange")
                            # plt.text(pointB[0], pointB[1], "BofA1")
                            plt.plot([filletCenterA1[0], pointB[0]], [filletCenterA1[1], pointB[1]], color="green")

                            arcVertices = getArcVertices(centerIndex, filletCenterA1, pointA, pointB, minAngle, type, rad, invert1)
                            streetCornerVertices[centerIndex].extend(arcVertices)

                            filletCenterB1 = findFilletCenter(B1, [(ausiliaryB1,[dist, rad]), (A1,[dist, rad])], dist, rad)

                            pointA = pointPerpendicularToLine(filletCenterB1, [B1, ausiliaryB1], rad)
                            streetVerticesList[lineIndexB].extend([pointA])
                            plt.plot(pointA[0], pointA[1], marker=".", markersize=10, color="orange")
                            plt.plot([filletCenterB1[0], pointA[0]], [filletCenterB1[1], pointA[1]], color="green")
                            # plt.text(pointA[0], pointA[1], "AofB1")

                            pointB = pointPerpendicularToLine(filletCenterB1, [B1, A1], rad)
                            plt.plot(pointB[0], pointB[1], marker=".", markersize=10, color="orange")
                            plt.plot([filletCenterB1[0], pointB[0]], [filletCenterB1[1], pointB[1]], color="green")
                            # plt.text(pointB[0], pointB[1], "BofB1")

                            arcVertices = getArcVertices(centerIndex, filletCenterB1, pointA, pointB, minAngle, type, rad, invert2)
                            streetCornerVertices[centerIndex].extend(arcVertices)


                            plt.plot(A1[0], A1[1], marker=".", markersize=10, color="orange")
                            plt.plot(ausiliaryA1[0], ausiliaryA1[1], marker=".", markersize=10, color="orange")
                            plt.plot(B1[0], B1[1], marker=".", markersize=10, color="orange")
                            plt.plot(ausiliaryB1[0], ausiliaryB1[1], marker=".", markersize=10, color="orange")
                            plt.plot([A1[0], B1[0]], [A1[1], B1[1]], color = "orange")
                            plt.plot([ausiliaryA1[0], A1[0]], [ausiliaryA1[1], A1[1]], color = "orange")
                            plt.plot([ausiliaryB1[0], B1[0]], [ausiliaryB1[1], B1[1]], color = "orange")

                            if type == "corner": # it is necessary to find also the opposite corners
                                # vertices are calculated from B to A to have them sorted properly
                                if perpSlope != None:
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
                                plt.plot(pointA[0], pointA[1], marker=".", markersize=10, color="orange")
                                plt.plot([filletCenterB2[0], pointA[0]], [filletCenterB2[1], pointA[1]], color="green")

                                pointB = pointPerpendicularToLine(filletCenterB2, [B2, A2], rad)
                                plt.plot(pointB[0], pointB[1], marker=".", markersize=10, color="orange")
                                plt.plot([filletCenterB2[0], pointB[0]], [filletCenterB2[1], pointB[1]], color="green")

                                arcVertices = getArcVertices(centerIndex, filletCenterB2, pointA, pointB, minAngle, type, rad, invert2)
                                streetCornerVertices[centerIndex].extend(arcVertices)

                                filletCenterA2 = findFilletCenter(A2, [(ausiliaryA2,[dist, rad]), (B2,[dist, rad])], dist, rad)

                                pointA = pointPerpendicularToLine(filletCenterA2, [A2, ausiliaryA2], rad)
                                streetVerticesList[lineIndexA].extend([pointA])
                                plt.plot(pointA[0], pointA[1], marker=".", markersize=10, color="orange")
                                plt.plot([filletCenterA2[0], pointA[0]], [filletCenterA2[1], pointA[1]], color="green")

                                pointB = pointPerpendicularToLine(filletCenterA2, [A2, B2], rad)
                                plt.plot(pointB[0], pointB[1], marker=".", markersize=10, color="orange")
                                plt.plot([filletCenterA2[0], pointB[0]], [filletCenterA2[1], pointB[1]], color="green")

                                arcVertices = getArcVertices(centerIndex, filletCenterA2, pointA, pointB, minAngle, type, rad, invert1)
                                streetCornerVertices[centerIndex].extend(arcVertices)

                                plt.plot(A2[0], A2[1], marker=".", markersize=10, color="orange")
                                plt.plot([A2[0], B2[0]], [A2[1], B2[1]], color = "orange")
                                plt.plot(ausiliaryA2[0], ausiliaryA2[1], marker=".", markersize=10, color="orange")
                                plt.plot([ausiliaryA2[0], A2[0]], [ausiliaryA2[1], A2[1]], color = "orange")
                                plt.plot(B2[0], B2[1], marker=".", markersize=10, color="orange")
                                plt.plot(ausiliaryB2[0], ausiliaryB2[1], marker=".", markersize=10, color="orange")
                                plt.plot([ausiliaryB2[0], B2[0]], [ausiliaryB2[1], B2[1]], color = "orange")




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

                                plt.plot(point[0], point[1], marker=".", markersize=10, color="orange")
                                plt.plot([filletCenter[0], point[0]], [filletCenter[1], point[1]], color="green")

                                # if it is a corner, "the other side" of the corner is to be found
                                if type == "corner":
                                    # in case the street widths are the same
                                    if testEqualProperty(verts, "width"):
                                        oppositePoint = pointPerpendicularToLine(filletCenter, [center, vert], radius + minWidth*2)
                                        if (oppositePoint):
                                            oppositeFilletCenter = filletCenter
                                            plt.plot(oppositePoint[0], oppositePoint[1], marker=".", markersize=10, color="red")

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


                                            plt.plot(newPoint[0], newPoint[1], marker=".", markersize=20, color="green")

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

                                            plt.plot(oppositeFilletCenter[0], oppositeFilletCenter[1], marker=".", markersize=10, color="blue")
                                            plt.plot([filletCenter[0], oppositeFilletCenter[0]], [filletCenter[1], oppositeFilletCenter[1]], color="black")
                                            # plt.plot([newPoint[0], oppositeFilletCenter[0]], [newPoint[1], oppositeFilletCenter[1]], color="black")

                                        # then the new perpendicular points, starting from the new Fillet center are calculated
                                        if mainSlope != None:
                                            if mainSlope == 0:
                                                oppositePoint = [oppositeFilletCenter[0] + radius, oppositeFilletCenter[1]]
                                                if (oppositeFilletCenter[0] > filletCenter[0]):
                                                    centerLocation = "left"
                                                else:
                                                    centerLocation = "right"

                                                if (oppositeFilletCenter[0] > oppositePoint[0]):
                                                    pointLocation = "left"
                                                else:
                                                    pointLocation = "right"

                                                if centerLocation == pointLocation:
                                                    oppositePoint = [oppositeFilletCenter[0] - radius, oppositeFilletCenter[1]]

                                            else:
                                                oppositePoint = pointFromCenter(oppositeFilletCenter, mainSlope, mainDirection, radius)
                                        else:
                                            oppositePoint = [oppositeFilletCenter[0], oppositeFilletCenter[1] + radius]
                                            if (oppositeFilletCenter[1] > filletCenter[1]):
                                                centerLocation = "down"
                                            else:
                                                centerLocation = "up"

                                            if (oppositeFilletCenter[1] > oppositePoint[1]):
                                                pointLocation = "down"
                                            else:
                                                pointLocation = "up"

                                            if centerLocation == pointLocation:
                                                oppositePoint = [oppositeFilletCenter[0], oppositeFilletCenter[1] - radius]

                                        plt.plot(oppositePoint[0], oppositePoint[1], marker=".", markersize=10, color="orange")
                                        plt.plot([oppositeFilletCenter[0], oppositePoint[0]], [oppositeFilletCenter[1], oppositePoint[1]], color="green")
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


# for i,el in enumerate(lines):
# 	print(i, el)

mainData = populateVertices(lines, vertices)

# plt.figure(figsize=(20,20))
plt.axis([-15, 15, -15, 15])

plt.grid(True)
plt.gca().set_aspect('equal') # to set the aspect ratio to 1

drawGraph()

for el in mainData:
    drawStreets(el)

# drawStreets(mainData[0])
# drawStreets(mainData[1])


plt.show()
