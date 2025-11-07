import bpy 
from bpy.types import Operator 

class OBJECT_OT_Set_Block_Edge_Attribute_Normal(Operator):
    """Set the value which will set to reverse or not reverse the block edge in the block GN"""
    bl_idname = "object.set_edge_attribute_normal"
    bl_label = "Set to normal of the block edge in the block GN"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_edges = [e for e in context.active_object.data.edges if e.select]
        normal = bpy.context.scene.attribute_wall_normal
        for edge in selected_edges:
            edgeIndex = edge.index
            mesh.attributes["mastro_inverted_normal"].data[edgeIndex].value = normal
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}