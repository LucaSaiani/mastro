import bpy 
from bpy.types import Operator

class OBJECT_OT_Set_Floor_Id(Operator):
    """Set Face Attribute as floor type"""
    bl_idname = "object.set_attribute_floor_id"
    bl_label = "Set Face Attribute as Floor Type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_floor_id = context.scene.attribute_floor_id
        
        try:
            mesh.attributes["mastro_floor_id"]
            attribute_floor_id = context.scene.attribute_floor_id

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [f for f in bpy.context.active_object.data.polygons if f.select]
            mesh_attributes_id = mesh.attributes["mastro_floor_id"].data.items()
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