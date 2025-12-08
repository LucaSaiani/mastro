import bpy 
from bpy.types import Operator

from ..Utils.update_bmesh_attributes import update_bmesh_attributes

# Operator to update the attributes of all the MaStro meshes in the scene
# Operated vie the button in the scene pannel        
class OBJECT_OT_Update_Mastro_Mesh_Attributes(Operator):
    '''Update the attributes of all the existing MaStro meshes'''
    bl_idname = "object.update_mastro_mesh_attributes"
    # bl_label = "Update the attributes of all the MaStro meshes in the scene"
    bl_label = "Update"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        update_bmesh_attributes(context, "all")   
        
        bpy.context.view_layer.update()
        for obj in bpy.data.objects:
            if obj.type == "MESH" and "MaStro object" in obj.data:
                obj.data.update()         
                
        return {'FINISHED'}