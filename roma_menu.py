import bpy
import bmesh 
from bpy.types import Menu, Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty
from decimal import Decimal, ROUND_HALF_DOWN
# from math import ceil as mathCeil

import csv #, os

header = ["Option", "Phase", "Plot Name", "Block Name", "Use", "N. of Storeys", "Footprint", "Perimeter", "Façade area", "GEA"]
    

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


class roma_MenuOperator_convert_to_RoMa_mesh(Operator):
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
            obj.roma_props['roma_option_attribute'] = 1
            obj.roma_props['roma_phase_attribute'] = 1
            # print("pippo")
            # bpy.types.Object.roma_props = bpy.props.PointerProperty(type=romaAddonProperties)
            # print("pippa", bpy.types.Object.roma_props)
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
            
     
        return {'FINISHED'}

# Definisci la classe per le proprietà personalizzate
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
    
class RoMa_MenuOperator_PrintData(Operator):
    bl_idname = "object.roma_print_data"
    bl_label = "Print the data of the mass"

    def execute(self, context):
        global header
        roughData = []
        csvData = []
        csvTemp = []
        objects = [obj for obj in bpy.context.scene.objects]
        for obj in objects:
            if obj.visible_get() and obj.type == "MESH" and "RoMa object" in obj.data:
                csvTemp.append(get_mass_data(obj))
        for sublist in csvTemp:
            roughData.extend(sublist)
        
        # roughData = sorted(roughData, key=lambda x:(x[0], x[1], x[2], x[3], x[4]))
        
        # csvData.append(roughData[0])
        # for el in roughData[1:]:
        #     if el[:5] == csvData[-1][:5]:
        #         prev_storeys = csvData[-1][5]
        #         # update number of storeys
        #         storeys = el[5]
        #         if storeys > prev_storeys:
        #             csvData[-1][5] = storeys
        #         # sum footprint
        #         csvData[-1][6] += el[6]
        #         # sum perimeter
        #         csvData[-1][7] += el[7]
        #         # sum facade
        #         csvData[-1][8] += el[8]
        #         # sum GEA
        #         csvData[-1][9] += el[9]
                
        #     else:
        #         csvData.append(el)
            
        # csvData.insert(0, header)
        
        csvData = aggregateData(roughData)
        
        print("")
        print("")
        tab = "\t"
        for r, row in enumerate(csvData):
            string = ""
            for el in row:
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
        
        
        
    
class RoMa_Menu(Menu):
    bl_idname = "VIEW3D_MT_custom_menu"
    bl_label = "RoMa"

    def draw(self, context):
        layout = self.layout
        #layout.active = bool(context.active_object.mode!='EDIT  ')
        layout.operator(roma_MenuOperator_convert_to_RoMa_mesh.bl_idname)
        layout.separator()
        layout.operator(RoMa_MenuOperator_PrintData.bl_idname)
        layout.operator(RoMa_MenuOperator_ExportCSV.bl_idname)
        layout.separator()
        layout.operator(RoMa_Operator_transformation_orientation.bl_idname)
        
        
def aggregateData(roughData):
    data = []

    roughData = sorted(roughData, key=lambda x:(x[0], x[1], x[2], x[3], x[4]))
    data.append(roughData[0])

    for el in roughData[1:]:
        if el[:5] == data[-1][:5]:
            prev_storeys = data[-1][5]
            # update number of storeys
            storeys = el[5]
            if storeys > prev_storeys:
                data[-1][5] = storeys
            # sum footprint
            data[-1][6] += el[6]
            # sum perimeter
            data[-1][7] += el[7]
            # sum facade
            data[-1][8] += el[8]
            # sum GEA
            data[-1][9] += el[9]
        else:
            data.append(el)
    data.insert(0, header)

    return(data)
    
   
def writeCSV(context, filepath):
    global header
    csvData = []
    data = []
    dataRough = []

    objects = [obj for obj in bpy.context.scene.objects]

    for obj in objects:
        if obj.type == "MESH" and "RoMa object" in obj.data:
            dataRough.append(get_mass_data(obj))

    for sublist in dataRough:
        data.extend(sublist)
        
    csvData = aggregateData(data)

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # writer.writerow(header)
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
        for n in bpy.context.scene.roma_plot_name_list:
            if n.id == f[bm_layer_plot]:
                plot = n.name
                break
        for n in bpy.context.scene.roma_block_name_list:
            if n.id == f[bm_layer_block]:
                block = n.name
                break
        for n in bpy.context.scene.roma_typology_name_list:
            if n.id == f[bm_layer_typology]:
                typology = n.name
                break
        storeys = f[bm_layer_storey]
        footprint = f.calc_area()
        
        GEA = footprint * storeys
        
        perimeter = 0
        common_edges = []
        for e in f.edges:
            # if there is no angle, then the edge is not a edge in common between faces
            try:
                angle = e.calc_face_angle()
                common_edges.append(e.index)
            except ValueError:
                perimeter += e.calc_length()
        
        # this is the area of the perimeter walls
        floorToFloor = 2
        facade_area = perimeter * floorToFloor * storeys
        # but if the faces having an edge in common have different storey numbers,
        # then the difference is added to the facade area
        for index in common_edges:
            for fa in bm.faces:
                for ed in fa.edges:
                    if ed.index == index and fa.index != f.index:
                        if f[bm_layer_storey] > fa[bm_layer_storey]:
                            diff = f[bm_layer_storey] - fa[bm_layer_storey]
                            length = ed.calc_length()
                            facade_area += length * diff * floorToFloor
                            
                            
        GEA = Decimal(GEA)
        GEA = GEA.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        facade_area = Decimal(facade_area)
        facade_area = facade_area.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        perimeter = Decimal(perimeter)
        perimeter = perimeter.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        footprint = Decimal(footprint)
        footprint = footprint.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
        data.append([option, phase, plot, block, typology, storeys, footprint, perimeter, facade_area, GEA])
            
    return(data)
