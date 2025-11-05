import bpy 
from bpy.types import Operator 

class OBJECT_OT_Set_Edge_Attribute_Angle(Operator):
    bl_idname = "object.set_edge_attribute_angle"
    bl_label = "Set the corner angle"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_verts = [v for v in context.active_object.data.vertices if v.select]
        angle = bpy.context.scene.attribute_block_side_angle
        for vert in selected_verts:
            vertIndex = vert.index
            mesh.attributes["mastro_side_angle"].data[vertIndex].value = angle
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}