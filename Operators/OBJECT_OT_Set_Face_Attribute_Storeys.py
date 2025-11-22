import bpy 
from bpy.types import Operator

from ..Utils.read_storey_attribute import read_storey_attribute

'''Set the number of storeys of the selected face attribute of the MaStro mesh'''
class OBJECT_OT_Set_Face_Attribute_Storeys(Operator):
    bl_idname = "object.set_face_attribute_storeys"
    bl_label = "Set face attributes assigned to the MaStro mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        for obj in selected_objects:
            if (obj.type == "MESH" and 
                "MaStro object" in context.object.data and
                "MaStro mass" in context.object.data):
                # obj = context.active_object
                mesh = obj.data
                mode = obj.mode
                
                bpy.ops.object.mode_set(mode='OBJECT')
                            
                selected_faces = [p for p in context.active_object.data.polygons if p.select]
                if len(selected_faces) > 0:
                    for face in selected_faces:
                        faceIndex = face.index
                        data = read_storey_attribute(context, mesh, faceIndex, element_type ="FACE")
                        mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value = data["numberOfStoreys"]
                        mesh.attributes["mastro_list_storey_A"].data[faceIndex].value = data["storey_list_A"]
                        mesh.attributes["mastro_list_storey_B"].data[faceIndex].value = data["storey_list_B"]
                bpy.ops.object.mode_set(mode=mode)
        
        return {'FINISHED'}