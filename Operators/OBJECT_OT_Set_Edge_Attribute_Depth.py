import bpy 
from bpy.types import Operator

from ..Utils.read_depth_attribute import read_depth_attribute

'''Set the depth of the building of the selected edge attribute of the MaStro block'''
class OBJECT_OT_Set_Edge_Attribute_Depth(Operator):
    bl_idname = "object.set_edge_attribute_depth"
    bl_label = "Set edge depth attributes assigned to the MaStro block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        for obj in selected_objects:
            if (obj.type == "MESH" and 
                "MaStro object" in context.object.data and
                "MaStro block" in context.object.data):
                mesh = obj.data
                # mesh.attributes["mastro_number_of_storeys"]
                mode = obj.mode
                bpy.ops.object.mode_set(mode='OBJECT')
                selected_edges = [e for e in context.active_object.data.edges if e.select]
                
                for edge in selected_edges:
                    edgeIndex = edge.index
                    # data = update_mesh_edge_attributes_depth(context, mesh, edgeIndex)
                    data = read_depth_attribute(context)
                    mesh.attributes["mastro_block_depth"].data[edgeIndex].value = data["blockDepth"]
                # else:
                #     active_vert = bpy.context.scene.previous_selection_vert_id
                #     active_edges =  [e for e in mesh.edges if active_vert in e.vertices]
                #     for edge in active_edges:
                #         edgeIndex = edge.index
                #         data = update_mesh_edge_attributes_depth(context)
                #         mesh.attributes["mastro_block_depth_EDGE"].data[edgeIndex].value = data["blockDepth"]

                bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}