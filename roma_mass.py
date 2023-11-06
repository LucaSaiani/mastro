import bpy
# import bmesh

# from bpy.app.handlers import persistent

# selected_face_index = -1
# checkingFace = False
# plotName = {"id" : None, "name" : None}
# blockName = {"id" : None, "name" : None}
# useName = {"id" : None, "name" : None}
# changed_massAttribute = False

# from bpy.props import FloatVectorProperty
# from bpy_extras.object_utils import (
#         AddObjectHelper,
#         object_data_add
# )
# from mathutils import Vector
from bpy.types import Operator, Panel

# class OBJECT_OT_add_RoMa_Mass(Operator, AddObjectHelper):
#     """Create a new RoMa Mass"""
#     bl_idname = "mesh.add_roma_mass"
#     bl_label = "RoMa Mass"
#     bl_options = {'REGISTER', 'UNDO'}

#     scale: FloatVectorProperty(
#         name="scale",
#         default=(1.0, 1.0, 1.0),
#         subtype='TRANSLATION',
#         description="scaling",
#     )

#     def execute(self, context):
#         add_RoMa_Mass(self, context)
#         return {'FINISHED'}

class VIEW3D_PT_RoMa_Mass(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Mass"
    
    
    # global plotName
    
    # @classmethod
    # def poll(cls, context):
    #     return (context.object is not None)
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == "MESH" and "RoMa object" in context.object.data)
    
    def draw(self, context):
        # obj = context.active_object 
        obj = context.object
        if obj is not None and obj.type == "MESH":
        
            mode = obj.mode
            if mode == "OBJECT" and "RoMa object" in obj.data:
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                row = layout.row()
                row = layout.row(align=True)
                
                layout.prop(obj.roma_props, "roma_option_attribute", text="Option")
                layout.prop(obj.roma_props, "roma_phase_attribute", text="Phase")
            
            elif mode == "EDIT" and "RoMa object" in obj.data:
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
                    layout.enabled = True
                else:
                    layout.enabled = False
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
                if scene.roma_plot_name_list and len(scene.roma_plot_name_list) >0:
                    # item = scene.roma_plot_name_list[scene.roma_plot_name_list_index]
                    # value = ""
                    # for n in scene.roma_plot_name_list:
                    #     if n.index == index:
                    #         value = str(n.index) + n.name
                    # row.label(text=" "+ str(item.index) + " " + item.name)
                    row.label(text = scene.roma_plot_name_current[0].name)
                # row.prop(item, "name", text="")
                # layout.prop(context.scene, "attribute_mass_plot_id", text="Plot Index")
                
                ################ BLOCK ######################
                row = layout.row()
                row = layout.row(align=True)
                row.prop(context.scene, "roma_block_names", icon="HOME", icon_only=True, text="Block")
                if len(scene.roma_block_name_list) >0:
                    row.label(text=scene.roma_block_name_current[0].name)
                # layout.prop(context.scene, "attribute_mass_block_id", text="Block Name")
                ################ TYPOLOGY ######################
                row = layout.row()
                row = layout.row(align=True)
                row.prop(context.scene, "roma_typology_names", icon="ASSET_MANAGER", icon_only=True, text="Typology")
                if len(scene.roma_typology_name_list) >0:
                    row.label(text=scene.roma_typology_name_current[0].name)
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
            mesh_attributes_id = mesh.attributes["roma_plot_id"].data.items()
            mesh_attributes_RND = mesh.attributes["roma_plot_RND"].data.items()
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes_id:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_plot_id
                for mesh_attribute in mesh_attributes_RND:
                    if mesh_attribute[0] == index:
                        for el in context.scene.roma_plot_name_list:
                            if el["id"] == attribute_mass_plot_id:
                                mesh_attribute[1].value = el["RND"]
                                break
           
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
            mesh_attributes_id = mesh.attributes["roma_block_id"].data.items()
            mesh_attributes_RND = mesh.attributes["roma_block_RND"].data.items()
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes_id:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_block_id
                for mesh_attribute in mesh_attributes_RND:
                    if mesh_attribute[0] == index:
                        for el in context.scene.roma_block_name_list:
                            if el["id"] == attribute_mass_block_id:
                                mesh_attribute[1].value = el["RND"]
                                break
           
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, block: "+str(attribute_mass_block_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_SetTypologyId(Operator):
    """Set Face Attribute as typology of the block"""
    bl_idname = "object.set_attribute_mass_typology_id"
    bl_label = "Set Face Attribute as Typology of the Block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_typology_id = context.scene.attribute_mass_typology_id
        
        try:
            mesh.attributes["roma_typology_id"]
            attribute_mass_typology_id = context.scene.attribute_mass_typology_id

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes_id = mesh.attributes["roma_typology_id"].data.items()
            mesh_attributes_RND = mesh.attributes["roma_typology_RND"].data.items()
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes_id:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_typology_id
                for mesh_attribute in mesh_attributes_RND:
                    if mesh_attribute[0] == index:
                        for el in context.scene.roma_block_name_list:
                            if el["id"] == attribute_mass_typology_id:
                                mesh_attribute[1].value = el["RND"]
                                break
           
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_SetTypologyId(Operator):
    """Set Face Attribute as typology of the block"""
    bl_idname = "object.set_attribute_mass_typology_id"
    bl_label = "Set Face Attribute as Typology of the Block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_typology_id = context.scene.attribute_mass_typology_id
        
        try:
            mesh.attributes["roma_typology_id"]
            attribute_mass_typology_id = context.scene.attribute_mass_typology_id

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes_id = mesh.attributes["roma_typology_id"].data.items()
            mesh_attributes_RND = mesh.attributes["roma_typology_RND"].data.items()
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes_id:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_typology_id
                for mesh_attribute in mesh_attributes_RND:
                    if mesh_attribute[0] == index:
                        for el in context.scene.roma_block_name_list:
                            if el["id"] == attribute_mass_typology_id:
                                mesh_attribute[1].value = el["RND"]
                                break
           
            bpy.ops.object.mode_set(mode=mode)
                    
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
        

            
# class OBJECT_OT_SetObjOption(Operator):
#     """Set Obj Attribute as project option"""
#     bl_idname = "object.set_attribute_obj_option"
#     bl_label = "Set the project option for the selected object"
#     bl_options = {'REGISTER', 'UNDO'}
    
#     def execute(self, context):
#         obj = context.active_object
#         try:
#             obj["roma_option_attribute"] = context.scene.attribute_obj_option
#             return {'FINISHED'}
#         except:
#             return {'FINISHED'}
        
# class OBJECT_OT_SetObjPhase(Operator):
#     """Set Obj Attribute as project phase"""
#     bl_idname = "object.set_attribute_obj_phase"
#     bl_label = "Set the project phase for the selected object"
#     bl_options = {'REGISTER', 'UNDO'}
    
#     def execute(self, context):
#         obj = context.active_object
#         try:
#             obj["roma_phase_attribute"] = context.scene.attribute_obj_phase
#             return {'FINISHED'}
#         except:
#             return {'FINISHED'}
        
    
# def add_RoMa_Mass(self, context):
#     scale_x = self.scale.x
#     scale_y = self.scale.y

#     verts = [
#         Vector((-2 * scale_x, -2 * scale_y, 0)),
#         Vector((2 * scale_x, -2 * scale_y, 0)),
#         Vector((2 * scale_x, 2 * scale_y, 0)),
#         Vector((-2 * scale_x, 2 * scale_y, 0))
#     ]

#     edges = []
#     faces = [[0,1,2,3]]

#     mesh = bpy.data.meshes.new(name="RoMa Mass")
#     mesh.from_pydata(verts, edges, faces)
#     mesh.update()
#     # useful for development when the mesh may be invalid.
#     # mesh.validate(verbose=True)
#     object_data_add(context, mesh, operator=self)
#     mesh.attributes.new(name="roma_facade_type", type="INT", domain="EDGE")
#     mesh.attributes.new(name="roma_number_of_storeys_per_face", type="INT", domain="EDGE")
    
#     mesh.attributes.new(name="roma_plot_id", type="INT", domain="FACE")
#     mesh.attributes.new(name="roma_block_id", type="INT", domain="FACE")
#     mesh.attributes.new(name="roma_use_id", type="INT", domain="FACE")
#     mesh.attributes.new(name="roma_number_of_storeys", type="INT", domain="FACE")
#     mesh.attributes.new(name="roma_GEA", type="FLOAT", domain="FACE")
    
#     obj = bpy.data.objects.new("RoMa Mass", mesh)
    
#     for face in obj.data.polygons:
#         mesh_plot = mesh.attributes["roma_plot_id"].data.items()
#         mesh_plot[0][1].value = 0
        
#         mesh_block = mesh.attributes["roma_block_id"].data.items()
#         mesh_block[0][1].value = 0
        
#         mesh_use = mesh.attributes["roma_use_id"].data.items()
#         mesh_typology[0][1].value = 0
    
#         mesh_storeys = mesh.attributes["roma_number_of_storeys"].data.items()
#         mesh_storeys[0][1].value = 3
        
#         mesh_GEA = mesh.attributes["roma_GEA"].data.items()
#         mesh_GEA[0][1].value = 0
    
    
# def add_RoMa_Mass_button(self, context):
#     self.layout.operator(
#         OBJECT_OT_add_RoMa_Mass.bl_idname,
#         text="RoMa Mass",
#         icon='PLUGIN')
    
def update_attribute_mass_plot_id(self,context):
    bpy.ops.object.set_attribute_mass_plot_id()
    
def update_attribute_mass_block_id(self, context):
    bpy.ops.object.set_attribute_mass_block_id()
    
# def update_attribute_mass_use_id(self, context):
#     bpy.ops.object.set_attribute_mass_typology_id()
    
def update_attribute_mass_typology_id(self, context):
    bpy.ops.object.set_attribute_mass_typology_id()
        
def update_attribute_mass_storeys(self, context):
    bpy.ops.object.set_attribute_mass_storeys()
    
# def update_attribute_obj_option(self, context):
#     bpy.ops.object.set_attribute_obj_option()
    
# def update_attribute_obj_phase(self, context):
#     bpy.ops.object.set_attribute_obj_phase()

def update_plot_name_label(self, context):
    # global plotName
    scene = context.scene
    name = scene.roma_plot_names
    scene.roma_plot_name_current[0].name = " " + name
    for n in scene.roma_plot_name_list:
        if n.name == name:
            scene.attribute_mass_plot_id = n.id
            scene.roma_plot_name_current[0].id = n.id
            break 

def update_block_name_label(self, context):
    # global blockName
    scene = context.scene
    name = scene.roma_block_names
    scene.roma_block_name_current[0].name = " " + name
    for n in scene.roma_block_name_list:
        if n.name == name:
            scene.attribute_mass_block_id = n.id
            scene.roma_block_name_current[0].id = n.id
            break   
        
def update_typology_name_label(self, context):
    # global useName
    scene = context.scene
    name = scene.roma_typology_names
    scene.roma_typology_name_current[0].name = " " + name
    for n in scene.roma_typology_name_list:
        if n.name == name:
            scene.attribute_mass_typology_id = n.id
            scene.roma_typology_name_current[0].id = n.id
            break  
        
    

       