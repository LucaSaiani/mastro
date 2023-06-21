import bpy
import bmesh

from bpy.app.handlers import persistent

# selected_face_index = -1
checkingFace = False
plotName = {"id" : None, "name" : None}
blockName = {"id" : None, "name" : None}
useName = {"id" : None, "name" : None}
# changed_massAttribute = False

from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import (
        AddObjectHelper,
        object_data_add
)
from mathutils import Vector
from bpy.types import Operator, Panel

class OBJECT_OT_add_RoMa_Mass(Operator, AddObjectHelper):
    """Create a new RoMa Mass"""
    bl_idname = "mesh.add_roma_mass"
    bl_label = "RoMa Mass"
    bl_options = {'REGISTER', 'UNDO'}

    scale: FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    def execute(self, context):
        add_RoMa_Mass(self, context)
        return {'FINISHED'}
    
class OBJECT_OT_SetPlotId(Operator):
    """Set Face Attribute as name of the plot"""
    bl_idname = "object.set_attribute_mass_plot_id"
    bl_label = "Set the Id of the plot"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_plot_id = context.scene.attribute_mass_plot_id
        
        # a custom attribute is assigned to the edges
       
        try:
            mesh.attributes["roma_plot_id"]
            attribute_mass_plot_id = context.scene.attribute_mass_plot_id
           
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_plot_id"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_plot_id
           
            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, plot: "+str(attribute_mass_plot_id))
            # global changed_massAttribute
            # changed_massAttribute = True
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_SetBlockId(Operator):
    """Set Face Attribute as name of the block"""
    bl_idname = "object.set_attribute_mass_block_id"
    bl_label = "Set the Id of the block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_block_id = context.scene.attribute_mass_block_id
        try:
            mesh.attributes["roma_block_id"]
            attribute_mass_block_id = context.scene.attribute_mass_block_id
           
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_block_id"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_block_id
           
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, block: "+str(attribute_mass_block_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_SetUseId(Operator):
    """Set Face Attribute as use of the block"""
    bl_idname = "object.set_attribute_mass_use_id"
    bl_label = "Set Face Attribute as Use of the Block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_use_id = context.scene.attribute_mass_use_id
        
        try:
            mesh.attributes["roma_use_id"]
            attribute_mass_use_id = context.scene.attribute_mass_use_id

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_use_id"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_use_id
           
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
    
class OBJECT_OT_SetMassStoreys(Operator):
    """Set Face Attribute as Number of Mass Storeys"""
    bl_idname = "object.set_attribute_mass_storeys"
    bl_label = "Set Face Attribute as number of Mass Storeys"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_storeys = context.scene.attribute_mass_storeys
        
        # a custom attribute is assigned to the edges
       
        try:
            mesh.attributes["roma_number_of_storeys"]
            attribute_mass_storeys = context.scene.attribute_mass_storeys
           
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_number_of_storeys"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_storeys
           
            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, number of storeys: "+str(attribute_mass_storeys))
            
            # read_face_attribute(obj)
            
            
            # changed_massAttribute = True
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class VIEW3D_PT_RoMa_Mass(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Mass"
    
    global plotName
    
    def draw(self, context):
        obj = context.active_object 
        if obj is not None and obj.type == "MESH":
        
            mode = obj.mode
            
            if mode == "EDIT" and "RoMa object" in obj.data:
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                # col = layout.column()
                # subcol = col.column()
                
                # layout.active = bool(context.active_object.mode=='EDIT')
                row = layout.row()
                row = layout.row(align=True)
                
                # split = row.split(factor=0.5)
                # split.label(text="Id: %d" % (item.id)) 
                # split.label(text=item.name, icon=custom_icon) 
                
                ################ PLOT ######################
                row.prop(context.scene, "roma_plot_names", icon="MOD_BOOLEAN", icon_only=True, text="Plot")
                if len(scene.roma_plot_name_list) >0:
                    # item = scene.roma_plot_name_list[scene.roma_plot_name_list_index]
                    # value = ""
                    # for n in scene.roma_plot_name_list:
                    #     if n.index == index:
                    #         value = str(n.index) + n.name
                    # row.label(text=" "+ str(item.index) + " " + item.name)
                    row.label(text=plotName["name"])
                # row.prop(item, "name", text="")
                # layout.prop(context.scene, "attribute_mass_plot_id", text="Plot Index")
                
                ################ BLOCK ######################
                row = layout.row()
                row = layout.row(align=True)
                row.prop(context.scene, "roma_block_names", icon="HOME", icon_only=True, text="Block")
                if len(scene.roma_block_name_list) >0:
                    row.label(text=blockName["name"])
                # layout.prop(context.scene, "attribute_mass_block_id", text="Block Name")
                ################ USE ######################
                row = layout.row()
                row = layout.row(align=True)
                row.prop(context.scene, "roma_use_names", icon="COMMUNITY", icon_only=True, text="Use")
                if len(scene.roma_use_name_list) >0:
                    row.label(text=useName["name"])
                # layout.prop(context.scene, "attribute_mass_use_id", text="Use Name")
                ################ STOREYS ######################
                layout.prop(context.scene, "attribute_mass_storeys", text="N° of storeys")

                # row = layout.row()
                # row.prop(context.scene, "attribute_mass_storeys", text="Number of Storeys")
                # if context.active_object.mode=='EDIT':
                #     row.enabled = True
                # else:
                #     row.enabled = False
                # if context.active_object.mode=='EDIT':
                #     print("pippa")
                    #bpy.ops.wm.mouse_position('INVOKE_DEFAULT')
                #     obj = context.active_object 
                #     obj.update_from_editmode()
                #     mesh = obj.data
                #     activeFace = mesh.polygons[mesh.polygons.active]
                #     print("cappero", activeFace.index)
                    #bpy.ops.object.mode_set(mode='OBJECT')
                    #context.scene.attribute_mass_storeys = activeFace.index
                    #       bpy.ops.object.mode_set(mode='EDIT')
            

    
def add_RoMa_Mass(self, context):
    scale_x = self.scale.x
    scale_y = self.scale.y

    verts = [
        Vector((-2 * scale_x, -2 * scale_y, 0)),
        Vector((2 * scale_x, -2 * scale_y, 0)),
        Vector((2 * scale_x, 2 * scale_y, 0)),
        Vector((-2 * scale_x, 2 * scale_y, 0))
    ]

    edges = []
    faces = [[0,1,2,3]]

    mesh = bpy.data.meshes.new(name="RoMa Mass")
    mesh.from_pydata(verts, edges, faces)
    mesh.update()
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    object_data_add(context, mesh, operator=self)
    mesh.attributes.new(name="roma_facade_type", type="INT", domain="EDGE")
    mesh.attributes.new(name="roma_number_of_storeys_per_face", type="INT", domain="EDGE")
    
    mesh.attributes.new(name="roma_plot_id", type="INT", domain="FACE")
    mesh.attributes.new(name="roma_block_id", type="INT", domain="FACE")
    mesh.attributes.new(name="roma_use_id", type="INT", domain="FACE")
    mesh.attributes.new(name="roma_number_of_storeys", type="INT", domain="FACE")
    mesh.attributes.new(name="roma_GEA", type="FLOAT", domain="FACE")
    
    obj = bpy.data.objects.new("RoMa Mass", mesh)
    
    for face in obj.data.polygons:
        mesh_plot = mesh.attributes["roma_plot_id"].data.items()
        mesh_plot[0][1].value = 0
        
        mesh_block = mesh.attributes["roma_block_id"].data.items()
        mesh_block[0][1].value = 0
        
        mesh_use = mesh.attributes["roma_use_id"].data.items()
        mesh_use[0][1].value = 0
    
        mesh_storeys = mesh.attributes["roma_number_of_storeys"].data.items()
        mesh_storeys[0][1].value = 3
        
        mesh_GEA = mesh.attributes["roma_GEA"].data.items()
        mesh_GEA[0][1].value = 0
    
    
def add_RoMa_Mass_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_RoMa_Mass.bl_idname,
        text="RoMa Mass",
        icon='PLUGIN')
    
def update_attribute_mass_plot_id(self,context):
    bpy.ops.object.set_attribute_mass_plot_id()
    
def update_attribute_mass_block_id(self, context):
    bpy.ops.object.set_attribute_mass_block_id()
    
def update_attribute_mass_use_id(self, context):
    bpy.ops.object.set_attribute_mass_use_id()
        
def update_attribute_mass_storeys(self, context):
    bpy.ops.object.set_attribute_mass_storeys()

def update_plot_name_label(self, context):
    global plotName
    scene = context.scene
    name = scene.roma_plot_names
    plotName["name"] = " " + name
    for n in scene.roma_plot_name_list:
        if n.name == name:
            scene.attribute_mass_plot_id = n.id
            plotName["id"] = n.id
            break 

def update_block_name_label(self, context):
    global blockName
    scene = context.scene
    name = scene.roma_block_names
    blockName["name"] = " " + name
    for n in scene.roma_block_name_list:
        if n.name == name:
            scene.attribute_mass_block_id = n.id
            blockName["id"] = n.id
            break   

def update_use_name_label(self, context):
    global useName
    scene = context.scene
    name = scene.roma_use_names
    useName["name"] = " " + name
    for n in scene.roma_use_name_list:
        if n.name == name:
            scene.attribute_mass_use_id = n.id
            useName["id"] = n.id
            break   
        
    
def read_face_attribute():
    global plotName
    global blockName
    global useName
    global checkingFace 
    checkingFace = True
    
    obj = bpy.context.active_object
    if obj.type == "MESH" and "RoMa object" in obj.data:
        mode = obj.mode
    
        if mode == "EDIT" and tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are in edit mode and selectin faces
            obj.update_from_editmode()
            mesh = obj.data

            # activeFace = mesh.polygons[mesh.polygons.active]
            # print("faccia attiva", activeFace)
            selected_faces = [p for p in mesh.polygons if p.select]
                
            if len(selected_faces) > 0:
                selected_indices = []
                for f in selected_faces:
                    selected_indices.append(f.index)
                    
                scene = bpy.context.scene
             
                bm = bmesh.from_edit_mesh(mesh)
                bm.faces.ensure_lookup_table()

                bMesh_plot = bm.faces.layers.int["roma_plot_id"]
                bMesh_block = bm.faces.layers.int["roma_block_id"]
                bMesh_use = bm.faces.layers.int["roma_use_id"]
                bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]

                selected_bmFaces = [face for face in bm.faces if face.select]
                if bm.faces.active is not None:
                    # print("NONE FACES !!!!!!!!!!!!!")
                # else:
                    bMesh_active_index = bm.faces.active.index
                    
                    for face in selected_faces:
                        bm.faces[face.index].select = False
                        
                    for bmFace in selected_bmFaces:
                        plot = bmFace[bMesh_plot]
                        block = bmFace[bMesh_block]
                        use = bmFace[bMesh_use] 
                        storey = bmFace[bMesh_storeys]
                        # if bm.faces.active is not None and bmFace.index ==  bMesh_active_index:
                        if bmFace.index ==  bMesh_active_index:
                            ############# PLOT ####################
                            if scene.attribute_mass_plot_id != plot:
                                scene.attribute_mass_plot_id = plot
                            if plotName["id"] != plot:
                                plotName["id"] = plot
                                # if plotName["id"] == 0:
                                #     plotName["name"] = None
                                # else:
                                for n in scene.roma_plot_name_list:
                                    if n.id == plotName["id"]:
                                        plotName["name"] = " " + n.name 
                                        break
                            ############# BLOCK ####################
                            if scene.attribute_mass_block_id != block:
                                scene.attribute_mass_block_id = block
                            if blockName["id"] != block:
                                blockName["id"] = block
                                for n in scene.roma_block_name_list:
                                    if n.id == blockName["id"]:
                                        blockName["name"] = " " + n.name 
                                        break
                            ############# USE ####################
                            if scene.attribute_mass_use_id != use:
                                scene.attribute_mass_use_id = use
                            if useName["id"] != use:
                                useName["id"] = use
                                for n in scene.roma_use_name_list:
                                    if n.id == useName["id"]:
                                        useName["name"] = " " + n.name 
                                        break
                            ############# STOREYS ####################
                            if scene.attribute_mass_storeys != storey:
                                scene.attribute_mass_storeys = storey
                            bmesh.update_edit_mesh(mesh)
                            bm.free()
                            break

                    bm = bmesh.from_edit_mesh(mesh)
                    bm.faces.ensure_lookup_table()
                    for index in selected_indices:
                            bm.faces[index].select = True
                            
                    bmesh.update_edit_mesh(mesh)
                bm.free() 
    checkingFace = False


@persistent
def get_face_attribute(dummy):
    global checkingFace
    if checkingFace is False:
        read_face_attribute()

           
       