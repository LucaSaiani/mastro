import bpy
from bpy.types import Operator, Panel

class VIEW3D_PT_RoMa_Facade(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Building"
    
    def draw(self, context):
        obj = context.active_object 
        if obj is not None and obj.type == "MESH":
            mode = obj.mode
            if mode == "EDIT" and "RoMa object" in obj.data:
                scene = context.scene
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                ################ FACADE ######################
                row = layout.row()
                row = layout.row(align=True)
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
                    row.enabled = True
                else:
                    row.enabled = False
                
                row.prop(context.scene, "roma_facade_names", icon="NODE_TEXTURE", icon_only=True, text="Façade Type")
                if len(scene.roma_plot_name_list) >0:
                    row.label(text = scene.roma_facade_name_current[0].name)
                else:
                    row.label(text = "")
                row.prop(context.scene, 'attribute_facade_normal', toggle=True, icon="ARROW_LEFTRIGHT", icon_only=True)
                
                ################ FLOOR ######################
                row = layout.row()
                row = layout.row(align=True)
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting edges
                    row.enabled = True
                else:
                    row.enabled = False
                
                row.prop(context.scene, "roma_floor_names", icon="VIEW_PERSPECTIVE", icon_only=True, text="Floor Type")
                if len(scene.roma_floor_name_list) >0:
                    row.label(text = scene.roma_floor_name_current[0].name)
                else:
                    row.label(text = "")
                
############################        ############################
############################ FACADE ############################
############################        ############################

class OBJECT_OT_SetFacadeId(Operator):
    """Set Face Attribute as use of the block"""
    bl_idname = "object.set_attribute_facade_id"
    bl_label = "Set Edge Attribute as Façade type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_facade_id = context.scene.attribute_facade_id
        
        try:
            mesh.attributes["roma_facade_id"]
            attribute_facade_id = context.scene.attribute_facade_id

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
            mesh_attributes_id = mesh.attributes["roma_facade_id"].data.items()
            for edge in selected_edges:
                index = edge.index
                for mesh_attribute in mesh_attributes_id:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_facade_id
                
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_SetFacadeNormal(Operator):
    """Invert the normal of the selected façade"""
    bl_idname = "object.set_attribute_facade_normal"
    bl_label = "Flip the normal of the selected edge"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_facade_normal = context.scene.attribute_facade_normal
        
        try:
            mesh.attributes["roma_facade_id"]
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
            mesh_attributes_normals = mesh.attributes["roma_inverted_normal"].data.items()
            
            for edge in selected_edges:
                index = edge.index
                for mesh_attribute in mesh_attributes_normals:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_facade_normal*1 # convert boolean to 0 or 1
                
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
def update_facade_normal(self, context):
    bpy.ops.object.set_attribute_facade_normal()

def update_attribute_facade_id(self, context):
    bpy.ops.object.set_attribute_facade_id()
    
def update_facade_name_label(self, context):
    scene = context.scene
    name = scene.roma_facade_names
    scene.roma_facade_name_current[0].name = " " + name
    for n in scene.roma_facade_name_list:
        if n.name == name:
            scene.attribute_facade_id = n.id
            scene.roma_facade_name_current[0].id = n.id
            break 
        
############################        ############################
############################ FLOOR  ############################
############################        ############################

class OBJECT_OT_SetFloorId(Operator):
    """Set Face Attribute as floor type"""
    bl_idname = "object.set_attribute_floor_id"
    bl_label = "Set Face Attribute as Floor Type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_floor_id = context.scene.attribute_floor_id
        
        try:
            mesh.attributes["roma_floor_id"]
            attribute_floor_id = context.scene.attribute_floor_id

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [f for f in bpy.context.active_object.data.polygons if f.select]
            mesh_attributes_id = mesh.attributes["roma_floor_id"].data.items()
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes_id:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_floor_id
                
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        

def update_attribute_floor_id(self, context):
    bpy.ops.object.set_attribute_floor_id()
    
def update_floor_name_label(self, context):
    scene = context.scene
    name = scene.roma_floor_names
    scene.roma_floor_name_current[0].name = " " + name
    for n in scene.roma_floor_name_list:
        if n.name == name:
            scene.attribute_floor_id = n.id
            scene.roma_floor_name_current[0].id = n.id
            break 
