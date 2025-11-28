import bpy
from bpy.types import Operator

class OBJECT_OT_Set_Floor_Id(Operator):
    """Set Face Attribute as floor type"""
    bl_idname = "object.set_attribute_floor_id"
    bl_label = "Set Face Attribute as Floor Type"
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
                "MaStro mass" in context.object.data):
                print(obj.name)
                # obj = context.active_object
                mesh = obj.data
                mode = obj.mode

                mesh.attributes["mastro_floor_id"]
                mastro_attribute_floor_id = context.scene.mastro_attribute_floor_id

                
                bpy.ops.object.mode_set(mode='OBJECT')
            
                selected_faces = [f for f in bpy.context.active_object.data.polygons if f.select]
                mesh_attributes_id = mesh.attributes["mastro_floor_id"].data.items()
                for face in selected_faces:
                    index = face.index
                    for mesh_attribute in mesh_attributes_id:
                        if mesh_attribute[0] == index:
                            mesh_attribute[1].value = mastro_attribute_floor_id
                    
                bpy.ops.object.mode_set(mode=mode)
                        
                    # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
                    #return {'FINISHED'}
        return {'FINISHED'}