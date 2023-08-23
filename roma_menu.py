import bpy
from bpy.types import Menu, Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty
# from math import ceil as mathCeil

import csv #, os

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
            {
            "attr" :  "roma_use_id",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "roma_use_RND",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
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
            "attr_default" : 0
            },
            {
            "attr" :  "roma_GEA",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            }
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
        # roma_list = []
        csvData = []
        csvTemp = []
        # header = ["Plot Name", "Block Name", "Use", "N. of Storeys", "GEA"]
        # csvData.append(header)
        objects = [obj for obj in bpy.context.scene.objects]
        for obj in objects:
            if obj.visible_get() and obj.type == "MESH" and "RoMa object" in obj.data:
                csvTemp.append(get_mass_data(obj))
        for sublist in csvTemp:
            csvData.extend(sublist)
        
        csvData = sorted(csvData, key=lambda x:(x[0], x[1]))
        header = ["Plot Name", "Block Name", "Use", "N. of Storeys", "GEA"]
        csvData.insert(0,header)
        
        print("")
        print("")
        tab = "\t"
        for r, row in enumerate(csvData):
            string = ""
            for el in row:
                i = 1
                tabs = tab
                while i < 3:
                    if len(str(el) + tabs) >= 10:
                        break
                    else:
                        i += 1
                        t = 1
                        while t < i-1:
                            tabs = tabs + tab
                            t += 1
                string = string + str(el) + tabs
            if r == 1: print("-------------------------------------------------------------------------")
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
        
   
def writeCSV(context, filepath):
    csvData = []
    csvTemp = []
    header = [["Plot Name", "Block Name", "Use", "Number of Storeys", "GEA"]]
    csvTemp.append(header)
    objects = [obj for obj in bpy.context.scene.objects]

    for obj in objects:
        if obj.type == "MESH" and "RoMa object" in obj.data:
            csvTemp.append(get_mass_data(obj))

    for sublist in csvTemp:
        csvData.extend(sublist)

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
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    data = []
    plot = None
    block = None
    use = None
    
    plotAttributes = mesh.attributes["roma_plot_id"].data
    blockAttributes = mesh.attributes["roma_block_id"].data
    useAttributes = mesh.attributes["roma_use_id"].data
    storeysAttributes = mesh.attributes["roma_number_of_storeys"].data
    GEAAttributes = mesh.attributes["roma_GEA"].data
    
    
    
    for index, attr in enumerate(plotAttributes):
        #print(plotNameAttributes[index].value, blockNameAttributes[index].value,useAttributes[index].value,storeysAttributes[index].value  )
        ############ PLOT ############
        plotId = plotAttributes[index].value
        if plotId == 0:
            plot = None
        else:
            for n in bpy.context.scene.roma_plot_name_list:
                if n.id == plotId:
                    plot = n.name
                    break
        ############ BLOCK ############
        blockId = blockAttributes[index].value
        if blockId == 0:
            block = None
        else:
            for n in bpy.context.scene.roma_block_name_list:
                if n.id == blockId:
                    block = n.name
                    break
        ############ USE ############
        useId = useAttributes[index].value
        if useId == 0:
            use = None
        else:
            for n in bpy.context.scene.roma_use_name_list:
                if n.id == useId:
                    use = n.name
                    break
        ########### STOREYS ##############
        storeys = storeysAttributes[index].value
        ########### GEA ##############
        GEA = GEAAttributes[index].value
        
        if GEA != None and GEA > 0 and plot != None and block != None and use != None:
            data.append([plot, block, use, storeys, GEA])
    
            
    return(data)
