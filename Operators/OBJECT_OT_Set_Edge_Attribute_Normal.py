import bpy 
from bpy.types import Operator 

class OBJECT_OT_Set_Edge_Attribute_Normal(Operator):
    """Set the value which will set to reverse or not reverse the edge in the block GN"""
    bl_idname = "object.set_edge_attribute_normal"
    bl_label = "Set the normal of the selected edges to be evaluated in geometry nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = context.selected_objects
        # if the active object is not selected, it is added to the list of the selected objects
        if len(selected_objects) == 0:
            active_object = context.view_layer.objects.active
            if active_object and not active_object.select_get(): 
                selected_objects.append(active_object)

        for obj in selected_objects:
            if (obj.type == "MESH" and 
                "MaStro object" in context.object.data and
                ("MaStro mass" in context.object.data or
                 "MaStro block" in context.object.data)):
                print("piero")
                mesh = obj.data
                mode = obj.mode
                bpy.ops.object.mode_set(mode='OBJECT')
                selected_edges = [e for e in context.active_object.data.edges if e.select]
                normal = bpy.context.scene.mastro_attribute_wall_normal
                for edge in selected_edges:
                    edgeIndex = edge.index
                    mesh.attributes["mastro_inverted_normal"].data[edgeIndex].value = normal
                bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}