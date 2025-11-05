import bpy 
from bpy.types import Operator 

from ..Utils.read_use_attribute import read_use_attribute
from ..Utils.read_storey_attribute import read_storey_attribute

# Set the uses and their heights in the selected face attribute of the MaStro mass
class OBJECT_OT_Set_Face_Attribute_Uses(Operator):
    bl_idname = "object.set_face_attribute_uses"
    bl_label = "Set face attributes assigned to the MaStro mass"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_faces = [p for p in context.active_object.data.polygons if p.select]
        for face in selected_faces:
            faceIndex = face.index
            # data = read_mesh_attributes_uses(context, mesh, faceIndex)
            data = read_use_attribute(context)
            mesh.attributes["mastro_typology_id"].data[faceIndex].value = data["typology_id"]
            mesh.attributes["mastro_list_use_id_A"].data[faceIndex].value = data["use_id_list_A"]
            mesh.attributes["mastro_list_use_id_B"].data[faceIndex].value = data["use_id_list_B"]
            mesh.attributes["mastro_list_height_A"].data[faceIndex].value = data["height_A"]
            mesh.attributes["mastro_list_height_B"].data[faceIndex].value = data["height_B"]
            mesh.attributes["mastro_list_height_C"].data[faceIndex].value = data["height_C"]
            mesh.attributes["mastro_list_height_D"].data[faceIndex].value = data["height_D"]
            mesh.attributes["mastro_list_height_E"].data[faceIndex].value = data["height_E"]
            mesh.attributes["mastro_list_void"].data[faceIndex].value = data["void"]
            # number of storeys needs to be updated as well
            numberOfStoreys = mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value
            data = read_storey_attribute(context, mesh, faceIndex, element_type="FACE", storeysSet = numberOfStoreys)
            mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value = data["numberOfStoreys"]
            mesh.attributes["mastro_list_storey_A"].data[faceIndex].value = data["storey_list_A"]
            mesh.attributes["mastro_list_storey_B"].data[faceIndex].value = data["storey_list_B"]
           
        bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}