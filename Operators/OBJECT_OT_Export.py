import bpy 
import bmesh
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty

import csv
from decimal import Decimal

header_aggregateData = ["Option", "Phase", "Block Name", "Building Name", "Use", "N. of Storeys", "Footprint", "Perimeter", "Wall area", "GEA"]
header_granularData = ["Block Name", "Building Name", "Use", "Floor", "Level", "GEA", "Perimeter", "Wall area"]
floorToFloorLevel = 4.5
 
class OBEJCT_OT_Mastro_Export_CSV(Operator, ExportHelper):
    """Export the data of the visibile MaStro Objects as a CSV file"""
    bl_idname = "object.mastro_export_csv"
    bl_label = "Export data as CSV"
    
    filename_ext = ".csv"
    filter_glob: StringProperty(
        default="*.csv",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        return writeCSV(context, self.filepath)
    
    
class OBJECT_OT_MaStro_Print_Data(Operator):
    bl_idname = "object.mastro_print_data"
    bl_label = "Print the data of the mass"
    
    text : StringProperty (
        name = "text",
        default = "aggregate"
    )

    def execute(self, context):
        roughData = []
        csvData = []
        csvTemp = []
        objects = [obj for obj in bpy.context.scene.objects]
        for obj in objects:
            if obj.visible_get() and obj.type == "MESH" and "MaStro object" in obj.data:
                csvTemp.append(get_mass_data(obj))
        for sublist in csvTemp:
            roughData.extend(sublist)
            
        if self.text == "aggregate":
            csvData = aggregateData(roughData)
        else:
            csvData = granularData(roughData)
        
        print("")
        print("")
        tab = "\t"
        for r, row in enumerate(csvData):
            string = ""
            for el in row:
                if isinstance(el, float): # if the entry is a float, it is rounded
                     el = Decimal(el)
                     el = el.quantize(Decimal('0.001'))
                     
                i = 1
                tabs = tab
                while i < 3:
                    if len(str(el) + tabs) >= 9:
                        break
                    else:
                        i += 1
                        t = 1
                        while t < i-1:
                            tabs = tabs + tab
                            t += 1
                
        
        # level = Decimal(level)
        # level = level.quantize(Decimal('0.001'))
        
                    
                string = string + str(el) + tabs
            if r == 1: print("--------------------------------------------------------------------------------------------------------------------------------------------------------------")
            print(f"{string}")
        print("")
        
        return {'FINISHED'}
    
class faceEdge():
     def __init__(self, index = None, face = None, storeys = None, topStorey = None, length = None, perimeter = None):
        #  self.objName = objName
         self.index = index
         self.face = face
         self.storeys = storeys
         self.topStorey = topStorey
         self.length = length
         self.perimeter = perimeter
    
def writeCSV(context, filepath):
    csvData = []
    data = []
    dataRough = []

    objects = [obj for obj in bpy.context.scene.objects]

    for obj in objects:
        if obj.visible_get() and obj.type == "MESH" and "MaStro object" in obj.data:
            dataRough.append(get_mass_data(obj))

    # for sublist in dataRough:
    #     data.extend(sublist)
    data = dataRough[:]

    granularDataDict = granularData(data)
    
    fieldnames = ["Block Name", 
                  "Building Name",
                  "Typology Name",
                  "Number of Storeys",
                  "Use", 
                  "Floor", 
                  "Level", 
                  "GEA",
                  "Footprint",
                  "Perimeter", 
                  "Wall Area"]


    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(granularDataDict)

    print(f"Data saved to {filepath}")
    return {'FINISHED'}


def get_mass_data(obj):
    data = []
    
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bMesh_typology = bm.faces.layers.int["mastro_typology_id"]
    bMesh_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
    
    for face in bm.faces:
        edges = []
        
        #block
        for block in bpy.context.scene.mastro_block_name_list:
            if block.id == obj.mastro_props['mastro_block_attribute']:
                block_name = block.name
                break

        #building
        for building in bpy.context.scene.mastro_building_name_list:
            if building.id == obj.mastro_props['mastro_building_attribute']:
                building_name = building.name
                break

        #typology
        for typology in bpy.context.scene.mastro_typology_name_list:
            if typology.id == face[bMesh_typology]:
                typology_name = typology.name
                break

        number_of_storeys = face[bMesh_storeys]

        footprint = face.calc_area()

        GEA = footprint * number_of_storeys
        
        #perimeter        
        perimeter = 0
        common_edges = []
        for edge in face.edges:
            edge_of_face = faceEdge()
            # edge_of_face.objName = obj.name
            edge_of_face.index = edge.index
            edge_of_face.face = face.index
            edge_of_face.length = edge.calc_length()
            edge_of_face.topStorey = number_of_storeys
            edge_of_face.storeys = None
            # if there is no angle, then the edge_of_face is not a edge in common between faces
            try:
                angle = edge.calc_face_angle()
                common_edges.append(edge.index)
                edge_of_face.perimeter = False
            except ValueError:
                perimeter += edge_of_face.length
                edge_of_face.perimeter = True
                edge_of_face.storeys = number_of_storeys
            edges.append(edge_of_face)
        
        #wall area
        # this is the area of the perimeter walls
        wall_area = perimeter * floorToFloorLevel * number_of_storeys
        # but if the faces having an edge in common have different storey numbers,
        # then the difference is added to the wall area
        for index in common_edges:
            for fa in bm.faces: 
                if face.index != fa.index: #there is no point in evaluating the same face
                    for ed in fa.edges:
                        if index == ed.index:
                            if face[bMesh_storeys] > fa[bMesh_storeys]:
                                diff = face[bMesh_storeys] - fa[bMesh_storeys]
                                length = ed.calc_length()
                                wall_area += length * diff * floorToFloorLevel
                                for ed in edges:
                                    if ed.index == index:
                                        ed.storeys = diff 
                                        break
        
        # removes the edges marked as not perimeter 
        # and are duplicates of the edges that are visibile
        for index, edge in reversed(list(enumerate(edges))):
            if edge.storeys == None:
                edges.pop(index)
        
        #lowest Z coordinate of the face
        obj_origin_z = obj.location[2]
        face_z = face.calc_center_median()[2]
        level = obj_origin_z + face_z
        
        # GEA = Decimal(GEA)
        # GEA = GEA.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        # wall_area = Decimal(wall_area)
        # wall_area = wall_area.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        # perimeter = Decimal(perimeter)
        # perimeter = perimeter.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        # footprint = Decimal(footprint)
        # footprint = footprint.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        # level = Decimal(level)
        # level = level.quantize(Decimal('0.001'))
        
        # data.append([block_name, building_name, typology_name, number_of_storeys, level, footprint, perimeter, wall_area, GEA, edges])
        entry = {
            "Block Name": block_name,
            "Building Name": building_name,
            "Typology Name": typology_name,
            "Number of Storeys": number_of_storeys,
            "Level": level,
            "Footprint": footprint,
            "Perimeter": perimeter,
            "Wall Area": wall_area,
            "GEA": GEA,
            "Edges": edges
        }
        data.append(entry)
    return data


def aggregateData(roughData):
    roughData = sorted(roughData, key=lambda x:(x[0], x[1], x[2], x[3], x[4]))
        
    data = []
    data.append(roughData[0])

    for el in roughData[1:]:
        if el[:5] == data[-1][:5]:
            prev_storeys = data[-1][5]
            # update number of storeys
            storeys = el[5]
            if storeys > prev_storeys:
                data[-1][5] = storeys
            # sum footprint
            data[-1][7] += el[7]
            # sum perimeter
            data[-1][8] += el[8]
            # sum wall
            data[-1][9] += el[9]
            # sum GEA
            data[-1][10] += el[10]
        else:
            data.append(el)
            
    # remove unwanted elements
    for index, el in enumerate(data):
        del data[index][11] #edge
        del data[index][6] #level
        
    data = sorted(data, key=lambda x:(x[0], x[1], x[2], x[3], x[4]))
    data.insert(0, header_aggregateData)

    return(data)


def granularData(roughData):
    # Sorting
    # print(roughData)
    roughData_flat = [entry for sublist in roughData for entry in sublist]
    roughData = sorted(
        roughData_flat,
        key=lambda x: (
            x["Block Name"],
            x["Building Name"],
            x["Typology Name"],
            x["Level"]
        )
    )

    # firts aggregate
    data = [roughData[0]]

    for el in roughData[1:]:
        last = data[-1]
        if (el["Block Name"] == last["Block Name"] and
            el["Building Name"] == last["Building Name"] and
            el["Typology Name"] == last["Typology Name"] and
            el["Number of Storeys"] == last["Number of Storeys"] and
            el["Level"] == last["Level"] and
            el["Perimeter"] == last["Perimeter"]):

            last["Footprint"] += el["Footprint"]
            last["Perimeter"] += el["Perimeter"]
            last["Wall Area"] += el["Wall Area"]

        else:
            data.append(el)

    # Unwrap multi-storey
    expandedData = []

    for index in reversed(range(len(data))):
        el = data[index]

        if el["Number of Storeys"] > 1:
            edges = el["Edges"]
            for floor in range(1, el["Number of Storeys"] + 1):
                level = el["Level"] + (floorToFloorLevel * floor)
                # Perimeter for each floor
                perimeter = 0
                for edge in edges:
                    if edge.perimeter is True:
                        perimeter += edge.length
                    else:
                        # edge.storeys is the number of visibile storeys
                        if floor >= (edge.topStorey - edge.storeys + 1):
                            perimeter += edge.length

                wallArea = perimeter * floorToFloorLevel

                expandedData.append({
                    "Block Name": el["Block Name"],
                    "Building Name": el["Building Name"],
                    "Typology Name": el["Typology Name"],
                    "Number of Storeys": el["Number of Storeys"],
                    "Level": level,
                    "Floor": floor,
                    "Footprint": el["Footprint"],
                    "Perimeter": perimeter,
                    "Wall Area": wallArea
                })

            del data[index]

    # add expanded data
    data.extend(expandedData)

    # second aggregate
    data = sorted(
        data,
        key=lambda x: (
            x["Block Name"],
            x["Building Name"],
            x["Typology Name"],
            x.get("Floor", x["Number of Storeys"]),
            x["Level"]
        )
    )

    granularData = [data[0]]

    for el in data[1:]:
        last = granularData[-1]

        if (el["Block Name"] == last["Block Name"] and
            el["Building Name"] == last["Building Name"] and
            el["Typology Name"] == last["Typology Name"] and
            el["Floor"] == last["Floor"] and
            el["Level"] == last["Level"]):

            last["Footprint"] += el["Footprint"]
            last["Perimeter"] += el["Perimeter"]
            last["Wall Area"] += el["Wall Area"]
        else:
            granularData.append(el)

    # print(granularData)
    return granularData

# def granularData(roughData):
#     roughData = sorted(roughData, key=lambda x:(x[0], x[1], x[2], x[3], x[4], x[6]))
    
#     data = []
#     data.append(roughData[0])

#     for el in roughData[1:]:
#         if el[:6] == data[-1][:6]:
#             # prev_storeys = data[-1][5]
#             # # update number of storeys
#             # storeys = el[5]
#             # if storeys > prev_storeys:
#             #     data[-1][5] = storeys
#             # sum footprint
#             data[-1][7] += el[7]
#             # sum perimeter
#             data[-1][8] += el[8]
#             # sum wall
#             data[-1][9] += el[9]
#         else:
#            data.append(el)
           
#     expandedData = []
#     for index, el in reversed(list(enumerate(data))):
#         # if there is more than one floor,
#         # it is necessary to unwrap data
#         if el[5] > 1:
#             edges = el[11]
            
#             for i, e in enumerate(range(el[5]), 1):
#                 floor = i
#                 level = el[6] + (floorToFloorLevel * i)
                
#                 perimeter = 0
#                 for edge in edges:
#                     if edge.perimeter == True:
#                         perimeter += edge.length
#                     else:
#                         # check if the current storey is in the range of that edge. 
#                         # The range is the maximum number of storey for that edge minus the number of the visible storey
#                         if floor >= (edge.topStorey - edge.storeys +1):
#                             perimeter += edge.length
#                             # print(edge.index, edge.face, edge.length, edge.storeys, edge.topStorey)
#                 # perimeter = None
#                 wallArea = perimeter * floorToFloorLevel
#                 expandedData.append([el[0], el[1], el[2], el[3], el[4], floor, level, el[7], perimeter, wallArea])
#             del data[index]
            
#     data.extend(expandedData)
    
#     # remove unwanted elements
#     for index, el in enumerate(data):
#         if len(data[index]) == 12: # only some entryes have the element we want to delete
#             del data[index][11] #edge
#         if len(data[index]) == 11: # only some entryes have the element we want to delete
#             del data[index][10] #GEA
    
#     #once all the levels are set, it is necessary to group the ones with the same features
#     data = sorted(data, key=lambda x:(x[0], x[1], x[2], x[3], x[4], x[5]))
    
#     granularData = []
#     granularData.append(data[0])

#     for el in data[1:]:
#         if el[:6] == granularData[-1][:6]:
#             # sum footprint
#             granularData[-1][7] += el[7]
#             # sum perimeter
#             granularData[-1][8] += el[8]
#             # sum wall
#             granularData[-1][9] += el[9]
#         else:
#            granularData.append(el)
        
#     granularData.insert(0, header_granularData)

#     return(granularData)