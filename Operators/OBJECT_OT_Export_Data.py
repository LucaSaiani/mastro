import bpy 
import bmesh
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty

import csv
from decimal import Decimal, ROUND_HALF_DOWN

header_aggregateData = ["Block Name", 
                        "Building Name", 
                        "Use", 
                        "Floor Number", 
                        "Number of Storeys", 
                        "Floor Area", 
                        "Perimeter", 
                        "Wall Area", 
                        "GEA"]

header_granularData = ["Block Name", 
                  "Building Name",
                  "Typology",
                  "Number of Storeys",
                  "Floor Number",
                  "Use", 
                  "Floor Area",
                  "Floor to Floor Height",
                  "Level", 
                  "Perimeter", 
                  "Wall Area"]

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
        objects = [obj for obj in bpy.context.scene.objects]
        data = []
        roughData = []
        # data = []
        # roughData = []
        # csvData = []
        # csvTemp = []
        
        for obj in objects:
            if obj.visible_get() and obj.type == "MESH" and "MaStro object" in obj.data:
                # csvTemp.append(get_mass_data(obj))
                roughData.append(get_mass_data(obj))
        # for sublist in csvTemp:
        #     roughData.extend(sublist)
        
        data = roughData[:]
        
        if self.text == "aggregate":
            dataDict = aggregateData(data)
            header = header_aggregateData
        else:
            dataDict = granularData(data)
            header = header_granularData
        
        tab = "\t"
        print("\n")
        print(tab.join(header))
        print("-" * 150)
        
        total_perimeter = 0
        total_wall = 0
        total_gea = 0
        
        for r, row in enumerate(dataDict):
            string = ""
            for key in header:
                el = row.get(key, "")
                if isinstance(el, float): # if the entry is a float, it is rounded
                     el = Decimal(el).quantize(Decimal('0.001'))
                     
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
            if r == 1: 
                print("--------------------------------------------------------------------------------------------------------------------------------------------------------------")
            print(f"{string}")
            
            # calculate the totals
            total_perimeter += row.get("Perimeter", 0)
            total_wall      += row.get("Wall Area", 0)
            total_gea       += row.get("GEA", 0)
            
        print("")
        
        print("\n")
        print("=== TOTALS ===")
        print(f"Perimeter:\t{Decimal(total_perimeter).quantize(Decimal('0.001'))}")
        print(f"Wall Area:\t{Decimal(total_wall).quantize(Decimal('0.001'))}")
        print(f"GEA:\t\t{Decimal(total_gea).quantize(Decimal('0.001'))}")
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
    # csvData = []
    data = []
    roughData = []

    objects = [obj for obj in bpy.context.scene.objects]

    for obj in objects:
        if obj.visible_get() and obj.type == "MESH" and "MaStro object" in obj.data:
            roughData.append(get_mass_data(obj))

    data = roughData[:]

    granularDataDict = granularData(data)

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header_granularData)
        writer.writeheader()
        writer.writerows(granularDataDict)

    print(f"Data saved to {filepath}")
    return {'FINISHED'}


def get_mass_data(obj):
    data = []
    # projectUses = bpy.context.scene.mastro_use_name_list
    
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    bMesh_typology = bm.faces.layers.int["mastro_typology_id"]
    bMesh_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
    bMesh_use_list_A   = bm.faces.layers.int["mastro_list_use_id_A"]
    bMesh_use_list_B   = bm.faces.layers.int["mastro_list_use_id_B"]
    bMesh_storey_list_A = bm.faces.layers.int["mastro_list_storey_A"]
    bMesh_storey_list_B = bm.faces.layers.int["mastro_list_storey_B"]
    bMesh_height_A = bm.faces.layers.int["mastro_list_height_A"]
    bMesh_height_B = bm.faces.layers.int["mastro_list_height_B"]
    bMesh_height_C = bm.faces.layers.int["mastro_list_height_C"]
    bMesh_height_D = bm.faces.layers.int["mastro_list_height_D"]
    bMesh_height_E = bm.faces.layers.int["mastro_list_height_E"]
    
    face_list = list(bm.faces)
    for face in face_list:
        edges = []
        block_name = ""
        building_name = ""
        typology_name = ""

        # block name
        for block in bpy.context.scene.mastro_block_name_list:
            if block.id == obj.mastro_props['mastro_block_attribute']:
                block_name = block.name
                break

        # building name
        for building in bpy.context.scene.mastro_building_name_list:
            if building.id == obj.mastro_props['mastro_building_attribute']:
                building_name = building.name
                break

        # typology name
        for typology in bpy.context.scene.mastro_typology_name_list:
            if typology.id == face[bMesh_typology]:
                typology_name = typology.name
                typology_id = typology.id
                # item = next(i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == typology_id)
                # use_list = item.useList
                # useSplit = use_list.split(";")    
                break

        # use list
        use_id_list_A = face[bMesh_use_list_A]
        use_id_list_B = face[bMesh_use_list_B]

        use_id_list_A = str(use_id_list_A)[1:]
        use_id_list_B = str(use_id_list_B)[1:]
        uses_list = [a + b for a, b in zip(use_id_list_A, use_id_list_B)]
        use_name_list = []
        for u in uses_list:
            use_id = int(u)
            use_name = ""
            for use in bpy.context.scene.mastro_use_name_list:
                if use.id == use_id:
                    use_name = use.name
                    break
            use_name_list.append(use_name)

        # storey list
        storey_list_A = face[bMesh_storey_list_A]
        storey_list_B = face[bMesh_storey_list_B]

        storey_list_A = str(storey_list_A)[1:]
        storey_list_B = str(storey_list_B)[1:]
        storey_list = [a + b for a, b in zip(storey_list_A, storey_list_B)]

        # height list
        height_list_A = face[bMesh_height_A]
        height_list_B = face[bMesh_height_B]
        height_list_C = face[bMesh_height_C]
        height_list_D = face[bMesh_height_D]
        height_list_E = face[bMesh_height_E]

        height_list_A = str(height_list_A)[1:]
        height_list_B = str(height_list_B)[1:]
        height_list_C = str(height_list_C)[1:]
        height_list_D = str(height_list_D)[1:]
        height_list_E = str(height_list_E)[1:]
        height_list = [a + b + c + d + e for a, b, c, d, e in zip(height_list_A, height_list_B, height_list_C, height_list_D, height_list_E)]

        # number of storeys
        number_of_storeys = face[bMesh_storeys]

        # Floor Area
        floor_area = face.calc_area()

        # GEA
        GEA = floor_area * number_of_storeys
        
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
        wall_area = perimeter * floorToFloorLevel *number_of_storeys
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
        
        GEA = Decimal(GEA)
        GEA = GEA.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        wall_area = Decimal(wall_area)
        wall_area = wall_area.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        perimeter = Decimal(perimeter)
        perimeter = perimeter.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        floor_area = Decimal(floor_area)
        floor_area = floor_area.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        level = Decimal(level)
        level = level.quantize(Decimal('0.001'))
        
        entry = {
            "Block Name": block_name,
            "Building Name": building_name,
            "Typology": typology_name,
            "Typology Id" : typology_id,
            "Number of Storeys": number_of_storeys,
            "Use List" : use_name_list,
            "Storey List" : storey_list,
            "Height List" : height_list,
            "Level": level,
            "Floor Area": floor_area,
            "Perimeter": perimeter,
            "Wall Area": wall_area,
            "GEA": GEA,
            "Edges": edges
        }
        data.append(entry)

    bm.free()
    return data


def aggregateData(roughData):
    roughData_flat = [entry for sublist in roughData for entry in sublist]
    roughData_sorted = sorted(
        roughData_flat,
        key=lambda x: (
            x["Block Name"],
            x["Building Name"],
            x["Typology"],
            x["Level"]
        )
    )
    
    data = [roughData_sorted[0]]
    
    for el in roughData_sorted[1:]:
        last = data[-1]
        if (
            el["Block Name"] == last["Block Name"] and
            el["Building Name"] == last["Building Name"] and
            el["Typology"] == last["Typology"] and
            el["Number of Storeys"] == last["Number of Storeys"] and
            el.get("Floor Number", None) == last.get("Floor Number", None)
        ):
            # update number of storeys, if necessary
            if el["Number of Storeys"] > last["Number of Storeys"]:
                last["Number of Storeys"] = el["Number of Storeys"]

            # summing floor area, perimeter, wall area, GEA
            last["Floor Area"] += el.get("Floor Area", 0)
            last["Perimeter"] += el.get("Perimeter", 0)
            last["Wall Area"] += el.get("Wall Area", 0)
            last["GEA"] += el.get("GEA", 0)
        else:
            data.append(el)

    # remove unwanted keys
    for el in data:
        el.pop("Edges", None)  
        el.pop("Level", None)  

    # Final sorting
    data_sorted = sorted(
        data,
        key=lambda x: (
            x["Block Name"],
            x["Building Name"],
            x["Typology"],
            x.get("Floor Number", x["Number of Storeys"])
        )
    )

    return data_sorted


def granularData(roughData):
    # Sorting
    # print(roughData)
    roughData_flat = [entry for sublist in roughData for entry in sublist]
    roughData = sorted(
        roughData_flat,
        key=lambda x: (
            x["Block Name"],
            x["Building Name"],
            x["Typology"],
            x["Level"]
        )
    )

    # firts aggregate
    data = [roughData[0]]

    for el in roughData[1:]:
        last = data[-1]
        if (el["Block Name"] == last["Block Name"] and
            el["Building Name"] == last["Building Name"] and
            el["Typology"] == last["Typology"] and
            el["Number of Storeys"] == last["Number of Storeys"] and
            el["Level"] == last["Level"] and
            el["Perimeter"] == last["Perimeter"]):

            last["Floor Area"] += el["Floor Area"]
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
            use_index = 0
            accumulate_floor = int(el["Storey List"][0])
            for floor in range(1, el["Number of Storeys"] + 1):
                floor_group = el["Storey List"][use_index]
                if accumulate_floor < floor:
                    use_index +=1
                    accumulate_floor += int(el["Storey List"][use_index])

                # use name
                use_name = el["Use List"][use_index]

                # floor to floor height
                floor_height = float(el["Height List"][use_index])

                # level
                level = el["Level"] + Decimal(floorToFloorLevel * floor)

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
                    "Typology": el["Typology"],
                    "Number of Storeys": el["Number of Storeys"],
                    "Floor Number" : floor,
                    "Use" : use_name,
                    "Floor to Floor Height" : floor_height,
                    "Level": level,
                    "Floor Area": el["Floor Area"],
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
            x["Typology"],
            x.get("Floor Number", x["Number of Storeys"]),
            x["Level"]
        )
    )

    granularData = [data[0]]

    for el in data[1:]:
        last = granularData[-1]

        if (el["Block Name"] == last["Block Name"] and
            el["Building Name"] == last["Building Name"] and
            el["Typology"] == last["Typology"] and
            el["Floor Number"] == last["Floor Number"] and
            el["Level"] == last["Level"]):

            last["Floor Area"] += el["Floor Area"]
            last["Perimeter"] += el["Perimeter"]
            last["Wall Area"] += el["Wall Area"]
        else:
            granularData.append(el)

    # print(granularData)
    return granularData
