import bpy 
from bpy.types import Operator 

from ..Utils.ss_read_use_attribute import read_use_attribute
from ..Utils.read_write_bmesh_storey_attribute import read_storey_attribute

# Set the uses and their heights in the selected edge attribute of the MaStro block
class OBJECT_OT_Set_Edge_Attribute_Uses(Operator):
    bl_idname = "object.set_edge_attribute_uses"
    bl_label = "Set edge attributes assigned to the MaStro block"
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
                "MaStro block" in context.object.data):
                # obj = context.active_object
                mesh = obj.data
                mode = obj.mode
                bpy.ops.object.mode_set(mode='OBJECT')
                selected_edges = [e for e in context.active_object.data.edges if e.select]
                for edge in selected_edges:
                    edgeIndex = edge.index
                    # data = read_mesh_attributes_uses(context, mesh, edgeIndex)
                    data = read_use_attribute(context)
                    mesh.attributes["mastro_typology_id_EDGE"].data[edgeIndex].value = data["typology_id"]
                    mesh.attributes["mastro_list_use_id_A_EDGE"].data[edgeIndex].value = data["use_id_list_A"]
                    mesh.attributes["mastro_list_use_id_B_EDGE"].data[edgeIndex].value = data["use_id_list_B"]
                    mesh.attributes["mastro_list_height_A_EDGE"].data[edgeIndex].value = data["height_A"]
                    mesh.attributes["mastro_list_height_B_EDGE"].data[edgeIndex].value = data["height_B"]
                    mesh.attributes["mastro_list_height_C_EDGE"].data[edgeIndex].value = data["height_C"]
                    mesh.attributes["mastro_list_height_D_EDGE"].data[edgeIndex].value = data["height_D"]
                    mesh.attributes["mastro_list_height_E_EDGE"].data[edgeIndex].value = data["height_E"]
                    mesh.attributes["mastro_list_void_EDGE"].data[edgeIndex].value = data["void"]
                    # number of storeys needs to be updated as well
                    numberOfStoreys = mesh.attributes["mastro_number_of_storeys_EDGE"].data[edgeIndex].value
                    data = read_storey_attribute(context, mesh, edgeIndex, element_type="EDGE", storeysSet = numberOfStoreys)
                    mesh.attributes["mastro_number_of_storeys_EDGE"].data[edgeIndex].value = data["numberOfStoreys"]
                    mesh.attributes["mastro_list_storey_A_EDGE"].data[edgeIndex].value = data["storey_list_A"]
                    mesh.attributes["mastro_list_storey_B_EDGE"].data[edgeIndex].value = data["storey_list_B"]
                
                bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}
