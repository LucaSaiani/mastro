import bpy
import bmesh 
from bpy.types import Menu, Operator
from bpy_extras.io_utils import ExportHelper
from bpy_extras.object_utils import AddObjectHelper
from bpy.props import StringProperty

import random
# import decimal
from decimal import Decimal #, ROUND_HALF_DOWN
from datetime import datetime
# from math import ceil as mathCeil

import csv #, os
from bpy.utils import resource_path
from pathlib import Path

header_aggregateData = ["Option", "Phase", "Plot Name", "Block Name", "Use", "N. of Storeys", "Footprint", "Perimeter", "Façade area", "GEA"]
header_granularData = ["Option", "Phase", "Plot Name", "Block Name", "Use", "Floor", "Level", "GEA", "Perimeter", "Façade area"]
    
floorToFloorLevel = 4.2

attribute_set = [

            {
            "attr" : "roma_vertex_custom_attribute",
            "attr_type" :  "INT",
            "attr_domain" :  "POINT",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_facade_id",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_inverted_normal",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 1
            },
            # {
            # "attr" :  "roma_number_of_storeys_per_face",
            # "attr_type" :  "INT",
            # "attr_domain" :  "EDGE"
            # },
            {
            "attr" :  "roma_plot_id",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_plot_RND",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_block_id",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_block_RND",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            # {
            # "attr" :  "roma_use_id",
            # "attr_type" :  "INT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # },
            # {
            # "attr" :  "roma_use_RND",
            # "attr_type" :  "FLOAT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # },
            {
            "attr" :  "roma_typology_id",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_typology_RND",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_floor_id",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_number_of_storeys",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 1
            },
            # {
            # "attr" :  "roma_GEA",
            # "attr_type" :  "FLOAT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # }
]

# Defines class for custom properties
class romaAddonProperties(bpy.types.PropertyGroup):
    roma_option_attribute: bpy.props.IntProperty(
        name="RoMa Option Attribute",
        default=1,
        min=1,
        description="The project option of the building"
    )
    
    roma_phase_attribute: bpy.props.IntProperty(
        name="RoMa Phase Attribute",
        default=1,
        min=1,
        description="The construction phase of the building"
    )
    
    roma_plot_attribute: bpy.props.IntProperty(
        name="RoMa Plot Attribute",
        default=1,
        min=1,
        description="Plot name"
    )
    
    roma_block_attribute: bpy.props.IntProperty(
        name="RoMa Block Attribute",
        default=1,
        min=1,
        description="Block name"
    )
    
class faceEdge():
     def __init__(self, index = None, face = None, storeys = None, topStorey = None, length = None, perimeter = None):
        #  self.objName = objName
         self.index = index
         self.face = face
         self.storeys = storeys
         self.topStorey = topStorey
         self.length = length
         self.perimeter = perimeter
         

class RoMa_Menu(Menu):
    bl_idname = "VIEW3D_MT_custom_menu"
    bl_label = "RoMa"

    def draw(self, context):
        layout = self.layout
        #layout.active = bool(context.active_object.mode!='EDIT  ')
        layout.operator(RoMa_MenuOperator_add_RoMa_mesh.bl_idname)
        layout.operator(RoMa_MenuOperator_convert_to_RoMa_mesh.bl_idname)
        layout.separator()
        printAggregate = layout.operator(RoMa_MenuOperator_PrintData.bl_idname, text="Print the data of the mass in compact form")
        printAggregate.text = "aggregate"
        printGranular = layout.operator(RoMa_MenuOperator_PrintData.bl_idname, text="Print the data of the mass in extended form")
        printGranular.text = "granular"
        layout.operator(RoMa_MenuOperator_ExportCSV.bl_idname)
        layout.separator()
        layout.operator(RoMa_Operator_transformation_orientation.bl_idname)

class RoMa_MenuOperator_add_RoMa_mesh(Operator, AddObjectHelper):
    """Add a RoMa mesh"""
    bl_idname = "object.roma_add_roma_mesh"
    bl_label = "RoMa mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    width: bpy.props.FloatProperty(
        name="Width",
        description="RoMa mesh width",
        # min=0.01, max=100.0,
        min=0,
        default=10,
    )
    
    depth: bpy.props.FloatProperty(
        name="Depth",
        description="RoMa mesh depth",
        # min=0.01, max=100.0,
        min=0,
        default=10,
    )
    
    def execute(self, context):

        verts_loc, faces = add_roma_mesh(
            self.width,
            self.depth,
        )

        mesh = bpy.data.meshes.new("RoMa mesh")

        bm = bmesh.new()

        for v_co in verts_loc:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for f_idx in faces:
            bm.faces.new([bm.verts[i] for i in f_idx])

        bm.to_mesh(mesh)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        from bpy_extras import object_utils
        object_utils.object_data_add(context, mesh, operator=self)
        
        obj = bpy.context.active_object
        obj.select_set(True)
        
        addAttributes(obj)
        addNodes()
        initLists()
        # add roma mass geo node to the created object
        geoName = "RoMa Mass"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["Roma Mass"]
        obj.modifiers[geoName].node_group = group
        return {'FINISHED'}
    
def add_roma_mesh(width, depth):
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    verts = [
        (+0.0, +0.0,  +0.0),
        (+1.0, +0.0,  +0.0),
        (+1.0, +1.0,  +0.0),
        (+0.0, +1.0,  +0.0),
        ]

    faces = [
        (0, 1, 2, 3),
    ]

    # apply size
    for i, v in enumerate(verts):
        verts[i] = v[0] * width, v[1] * depth, v[2]

    return verts, faces

# add the entri to the add menu
def roma_add_menu_func(self, context):
    self.layout.operator(RoMa_MenuOperator_add_RoMa_mesh.bl_idname, icon='MESH_CUBE')
    
class RoMa_MenuOperator_convert_to_RoMa_mesh(Operator):
    bl_idname = "object.roma_convert_to_roma"
    bl_label = "Convert the selected mesh to a RoMa mesh"
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        selected_meshes = [obj for obj in selected_objects if obj.type == 'MESH']
        # mode = None
        for obj in selected_meshes:
            addAttributes(obj)
            
        addNodes()
        initLists()
        return {'FINISHED'}

# assign the roma attributes to the selected object
def addAttributes(obj):
    obj.roma_props['roma_option_attribute'] = 1
    obj.roma_props['roma_phase_attribute'] = 1
    obj.roma_props['roma_plot_attribute'] = 0
    obj.roma_props['roma_block_attribute'] = 0
    mesh = obj.data
    mesh["RoMa object"] = True
    for a in attribute_set:
        try:
            mesh.attributes[a["attr"]]
        except:
            if a["attr_domain"] is None: # to set custom attributes to the object, not to vertex, edge or face
                obj[a["attr"]] = a["attr_default"]
            else:
                mesh.attributes.new(name=a["attr"], type=a["attr_type"], domain=a["attr_domain"])
                if a["attr_domain"] == 'FACE':
                    attribute = mesh.attributes[a["attr"]].data.items()
                    for face in mesh.polygons:
                        index = face.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                mesh_attribute[1].value = a["attr_default"]
                                break
                elif a["attr_domain"] == 'EDGE':
                    attribute = mesh.attributes[a["attr"]].data.items()
                    for edge in mesh.edges:
                        index = edge.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                mesh_attribute[1].value = a["attr_default"]
                                break
                #     
                #     attribute[0][1].value = None
    
# import the roma nodes in the file
def addNodes():
    USER = Path(resource_path('USER'))
    src = USER / "scripts/addons" / "roma"

    file_path = src / "roma.blend"
    inner_path = "NodeTree"
    geoNodes_list = ("Roma Mass", "Roma Mullions")

    for group in geoNodes_list:
        if group not in bpy.data.node_groups:
            bpy.ops.wm.append(
                filepath=str(file_path / inner_path / group),
                directory=str(file_path / inner_path),
                filename = group
                )   
    
def initLists():
    # if bpy.context.preferences.addons['roma'].preferences.toggleSelectionOverlay:
    #     bpy.data.window_managers["WinMan"].toggle_selection_overlay = True
    
    
    if len(bpy.context.scene.roma_plot_name_current) == 0:
        bpy.context.scene.roma_plot_name_current.add()
        bpy.context.scene.roma_plot_name_current[0].id = 0
        bpy.context.scene.roma_plot_name_current[0].name = " "
        # print("roma_plot_name_current",len(bpy.context.scene.roma_plot_name_current))
    
    if len(bpy.context.scene.roma_block_name_current) == 0:
        bpy.context.scene.roma_block_name_current.add()
        bpy.context.scene.roma_block_name_current[0].id = 0
        bpy.context.scene.roma_block_name_current[0].name = " "
        # print("roma_block_name_current)", len(bpy.context.scene.roma_block_name_current))
        
    if len(bpy.context.scene.roma_use_name_current) == 0:
        bpy.context.scene.roma_use_name_current.add()
        bpy.context.scene.roma_use_name_current[0].id = 0
        bpy.context.scene.roma_use_name_current[0].name = " "
        # print("roma_use_name_current",len(bpy.context.scene.roma_use_name_current))
        
    if len(bpy.context.scene.roma_typology_name_current) == 0:
        bpy.context.scene.roma_typology_name_current.add()
        bpy.context.scene.roma_typology_name_current[0].id = 0
        bpy.context.scene.roma_typology_name_current[0].name = " "
        # print("roma_use_name_current",len(bpy.context.scene.roma_use_name_current))
        
    if len(bpy.context.scene.roma_facade_name_current) == 0:
        bpy.context.scene.roma_facade_name_current.add()
        bpy.context.scene.roma_facade_name_current[0].id = 0
        bpy.context.scene.roma_facade_name_current[0].name = " "
        # print("roma_facade_name_current",len(bpy.context.scene.roma_facade_name_current))
        
    if len(bpy.context.scene.roma_floor_name_current) == 0:
        bpy.context.scene.roma_floor_name_current.add()
        bpy.context.scene.roma_floor_name_current[0].id = 0
        bpy.context.scene.roma_floor_name_current[0].name = " "
    
    if len(bpy.context.scene.roma_plot_name_list) == 0:
        bpy.context.scene.roma_plot_name_list.add()
        bpy.context.scene.roma_plot_name_list[0].id = 0
        bpy.context.scene.roma_plot_name_list[0].name = ""
        random.seed(datetime.now().timestamp())
        rndNumber = float(Decimal(random.randrange(0,10000000))/10000000)
        bpy.context.scene.roma_plot_name_list[0].RND = rndNumber
        
    if len(bpy.context.scene.roma_block_name_list) == 0:
        bpy.context.scene.roma_block_name_list.add()
        bpy.context.scene.roma_block_name_list[0].id = 0
        bpy.context.scene.roma_block_name_list[0].name = ""
        random.seed(datetime.now().timestamp())
        rndNumber = float(Decimal(random.randrange(0,10000000))/10000000)
        bpy.context.scene.roma_block_name_list[0].RND = rndNumber
        
    if len(bpy.context.scene.roma_use_name_list) == 0:
        bpy.context.scene.roma_use_name_list.add()
        bpy.context.scene.roma_use_name_list[0].id = 0
        bpy.context.scene.roma_use_name_list[0].name = ""
        # random.seed(datetime.now().timestamp())
        # rndNumber = float(Decimal(random.randrange(0,10000000))/10000000)
        # bpy.context.scene.roma_use_name_list[0].RND = rndNumber
    
    if len(bpy.context.scene.roma_typology_name_list) == 0:
        bpy.context.scene.roma_typology_name_list.add()
        bpy.context.scene.roma_typology_name_list[0].id = 0
        bpy.context.scene.roma_typology_name_list[0].name = ""
        random.seed(datetime.now().timestamp())
        rndNumber = float(Decimal(random.randrange(0,10000000))/10000000)
        bpy.context.scene.roma_typology_name_list[0].RND = rndNumber
        
    if len(bpy.context.scene.roma_facade_name_list) == 0:
        bpy.context.scene.roma_facade_name_list.add()
        bpy.context.scene.roma_facade_name_list[0].id = 0
        bpy.context.scene.roma_facade_name_list[0].name = ""
        bpy.context.scene.roma_facade_name_list[0].normal = 0
      
    if len(bpy.context.scene.roma_floor_name_list) == 0:
        bpy.context.scene.roma_floor_name_list.add()
        bpy.context.scene.roma_floor_name_list[0].id = 0
        bpy.context.scene.roma_floor_name_list[0].name = ""

   
        
    
    
    
class RoMa_MenuOperator_PrintData(Operator):
    bl_idname = "object.roma_print_data"
    bl_label = "Print the data of the mass"
    
    text : bpy.props.StringProperty (
        name = "text",
        default = "aggregate"
    )

    def execute(self, context):
        roughData = []
        csvData = []
        csvTemp = []
        objects = [obj for obj in bpy.context.scene.objects]
        for obj in objects:
            if obj.visible_get() and obj.type == "MESH" and "RoMa object" in obj.data:
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
    
class RoMa_MenuOperator_ExportCSV(Operator, ExportHelper):
    """Export the data of the visibile RoMa Objects as a CSV file"""
    bl_idname = "object.roma_export_csv"
    bl_label = "Export data as CSV"
    
    filename_ext = ".csv"
    filter_glob: StringProperty(
        default="*.csv",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        return writeCSV(context, self.filepath)

class RoMa_Operator_transformation_orientation(Operator):
    """Create transformation orientation from selection"""
    bl_idname = "object.roma_transformation_orientation"
    bl_label = "Create transformation orientation from selection"
    
    def execute(self, context):
        try:
            bpy.ops.transform.delete_orientation()
        except:
            pass
        bpy.ops.transform.create_orientation(use=True)
        return {'FINISHED'} 
        
        
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
            # sum facade
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
    roughData = sorted(roughData, key=lambda x:(x[0], x[1], x[2], x[3], x[4], x[6]))
    
    data = []
    data.append(roughData[0])

    for el in roughData[1:]:
        if el[:6] == data[-1][:6]:
            # prev_storeys = data[-1][5]
            # # update number of storeys
            # storeys = el[5]
            # if storeys > prev_storeys:
            #     data[-1][5] = storeys
            # sum footprint
            data[-1][7] += el[7]
            # sum perimeter
            data[-1][8] += el[8]
            # sum facade
            data[-1][9] += el[9]
        else:
           data.append(el)
           
    expandedData = []
    for index, el in reversed(list(enumerate(data))):
        # if there is more than one floor,
        # it is necessary to unwrap data
        if el[5] > 1:
            edges = el[11]
            
            for i, e in enumerate(range(el[5]), 1):
                floor = i
                level = el[6] + (floorToFloorLevel * i)
                
                perimeter = 0
                for edge in edges:
                    if edge.perimeter == True:
                        perimeter += edge.length
                    else:
                        # check if the current storey is in the range of that edge. 
                        # The range is the maximum number of storey for that edge minus the number of the visible storey
                        if floor >= (edge.topStorey - edge.storeys +1):
                            perimeter += edge.length
                            # print(edge.index, edge.face, edge.length, edge.storeys, edge.topStorey)
                # perimeter = None
                facadeArea = perimeter * floorToFloorLevel
                expandedData.append([el[0], el[1], el[2], el[3], el[4], floor, level, el[7], perimeter, facadeArea])
            del data[index]
            
    data.extend(expandedData)
    
    # remove unwanted elements
    for index, el in enumerate(data):
        if len(data[index]) == 12: # only some entryes have the element we want to delete
            del data[index][11] #edge
        if len(data[index]) == 11: # only some entryes have the element we want to delete
            del data[index][10] #GEA
    
    #once all the levels are set, it is necessary to group the ones with the same features
    data = sorted(data, key=lambda x:(x[0], x[1], x[2], x[3], x[4], x[5]))
    
    granularData = []
    granularData.append(data[0])

    for el in data[1:]:
        if el[:6] == granularData[-1][:6]:
            # sum footprint
            granularData[-1][7] += el[7]
            # sum perimeter
            granularData[-1][8] += el[8]
            # sum facade
            granularData[-1][9] += el[9]
        else:
           granularData.append(el)
        
    granularData.insert(0, header_granularData)

    return(granularData)
    
   
def writeCSV(context, filepath):
    csvData = []
    data = []
    dataRough = []

    objects = [obj for obj in bpy.context.scene.objects]

    for obj in objects:
        if obj.visible_get() and obj.type == "MESH" and "RoMa object" in obj.data:
            dataRough.append(get_mass_data(obj))

    for sublist in dataRough:
        data.extend(sublist)
        
    csvData = granularData(data)

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csvData)

    print(f"Data saved to {filepath}")
    return {'FINISHED'}
    
    
# Callback function to add drop down menu
def roma_menu(self, context):
    layout = self.layout
    layout.menu(RoMa_Menu.bl_idname)


def get_mass_data(obj):
    #mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    if "roma_option_attribute" in obj.roma_props.keys():
        option = obj.roma_props['roma_option_attribute']
    else:
        option = None
        
    if "roma_phase_attribute" in obj.roma_props.keys():
        phase = obj.roma_props['roma_phase_attribute']
    else:
        phase = None
    
    phase = obj.roma_props['roma_phase_attribute']
    
    mesh = obj.data
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
        
    data = []
    
    bm_layer_plot = bm.faces.layers.int["roma_plot_id"]
    bm_layer_block = bm.faces.layers.int["roma_block_id"]
    bm_layer_typology = bm.faces.layers.int["roma_typology_id"]
    bm_layer_storey = bm.faces.layers.int["roma_number_of_storeys"]
    
    for f in bm.faces:
        edges = []
        #plot
        for n in bpy.context.scene.roma_plot_name_list:
            if n.id == f[bm_layer_plot]:
                plot = n.name
                break

        #block
        for n in bpy.context.scene.roma_block_name_list:
            if n.id == f[bm_layer_block]:
                block = n.name
                break

        #typology
        for n in bpy.context.scene.roma_typology_name_list:
            if n.id == f[bm_layer_typology]:
                typology = n.name
                break

        storeys = f[bm_layer_storey]

        footprint = f.calc_area()

        GEA = footprint * storeys
        
        #perimeter        
        perimeter = 0
        common_edges = []
        for e in f.edges:
            edge = faceEdge()
            # edge.objName = obj.name
            edge.index = e.index
            edge.face = f.index
            edge.length = e.calc_length()
            edge.topStorey = storeys
            edge.storeys = None
            # if there is no angle, then the edge is not a edge in common between faces
            try:
                angle = e.calc_face_angle()
                common_edges.append(e.index)
                edge.perimeter = False
            except ValueError:
                perimeter += edge.length
                edge.perimeter = True
                edge.storeys = storeys
            edges.append(edge)
        
        #facade area
        # this is the area of the perimeter walls
       
        facade_area = perimeter * floorToFloorLevel * storeys
        # but if the faces having an edge in common have different storey numbers,
        # then the difference is added to the facade area
        for index in common_edges:
            for fa in bm.faces: 
                if f.index != fa.index: #there is no point in evaluating the same face
                    for ed in fa.edges:
                        if index == ed.index:
                            if f[bm_layer_storey] > fa[bm_layer_storey]:
                                diff = f[bm_layer_storey] - fa[bm_layer_storey]
                                length = ed.calc_length()
                                facade_area += length * diff * floorToFloorLevel
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
        face_z = f.calc_center_median()[2]
        level = obj_origin_z + face_z
        
        # GEA = Decimal(GEA)
        # GEA = GEA.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        # facade_area = Decimal(facade_area)
        # facade_area = facade_area.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        # perimeter = Decimal(perimeter)
        # perimeter = perimeter.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        # footprint = Decimal(footprint)
        # footprint = footprint.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        # level = Decimal(level)
        # level = level.quantize(Decimal('0.001'))
        
        data.append([option, phase, plot, block, typology, storeys, level, footprint, perimeter, facade_area, GEA, edges])
            
    return(data)
