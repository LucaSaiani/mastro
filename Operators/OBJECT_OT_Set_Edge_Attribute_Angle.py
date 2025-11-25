import bpy 
from bpy.types import Operator 

class OBJECT_OT_Set_Edge_Attribute_Angle(Operator):
    bl_idname = "object.set_edge_attribute_angle"
    bl_label = "Set the corner angle"
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
                selected_verts = [v for v in context.active_object.data.vertices if v.select]
                angle = bpy.context.scene.mastro_attribute_block_side_angle
                for vert in selected_verts:
                    vertIndex = vert.index
                    mesh.attributes["mastro_side_angle"].data[vertIndex].value = angle
                bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}