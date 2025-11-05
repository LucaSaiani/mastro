import bpy 
from bpy.types import Operator 

from ..Utils.read_storey_attribute import read_storey_attribute

'''Set the number of storeys of the selected edfe attribute of the MaStro block'''
class OBJECT_OT_Set_Edge_Attribute_Storeys(Operator):
    bl_idname = "object.set_edge_attribute_storeys"
    bl_label = "Set edge storey attributes assigned to the MaStro block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        # mesh.attributes["mastro_number_of_storeys"]
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_edges = [e for e in context.active_object.data.edges if e.select]
        
        for edge in selected_edges:
            edgeIndex = edge.index
            data = read_storey_attribute(context, mesh, edgeIndex, element_type="EDGE")
            # data = update_mesh_edge_attributes_storeys(context, mesh, edgeIndex)
            mesh.attributes["mastro_number_of_storeys_EDGE"].data[edgeIndex].value = data["numberOfStoreys"]
            mesh.attributes["mastro_list_storey_A_EDGE"].data[edgeIndex].value = data["storey_list_A"]
            mesh.attributes["mastro_list_storey_B_EDGE"].data[edgeIndex].value = data["storey_list_B"]
        # else:
        #     active_vert = bpy.context.scene.previous_selection_vert_id
        #     active_edges =  [e for e in mesh.edges if active_vert in e.vertices]
        #     for edge in active_edges:
        #         edgeIndex = edge.index
        #         data = update_mesh_edge_attributes_storeys(context, mesh, edgeIndex)
        #         mesh.attributes["mastro_number_of_storeys_EDGE"].data[edgeIndex].value = data["numberOfStoreys"]
        #         mesh.attributes["mastro_list_storey_A_EDGE"].data[edgeIndex].value = data["storey_list_A"]
        #         mesh.attributes["mastro_list_storey_B_EDGE"].data[edgeIndex].value = data["storey_list_B"]
        bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}