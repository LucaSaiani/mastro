import bpy 
from bpy.types import Operator

class OBJECT_OT_Set_Wall_Id(Operator):
    """Set Face Attribute as use of the building"""
    bl_idname = "object.set_attribute_wall_id"
    bl_label = "Set Edge Attribute as Wall type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        for obj in selected_objects:
            if (obj.type == "MESH" and 
                "MaStro object" in context.object.data and
                ("MaStro mass" in context.object.data or
                "MaStro block" in context.object.data)):
                
                mesh = obj.data

                mesh.attributes["mastro_wall_id"]
                attribute_wall_id = context.scene.attribute_wall_id
                thickness = context.scene.mastro_wall_name_list[attribute_wall_id].wallThickness

                mode = obj.mode
                bpy.ops.object.mode_set(mode='OBJECT')
            
                selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
                mesh_attributes_id = mesh.attributes["mastro_wall_id"].data.items()
                mesh_attributes_thickness = mesh.attributes["mastro_wall_thickness"].data.items()
                for edge in selected_edges:
                    index = edge.index
                    for ind, mesh_attribute in enumerate(mesh_attributes_id):
                        if mesh_attribute[0] == index:
                            mesh_attribute[1].value = attribute_wall_id
                            mesh_attributes_thickness[ind][1].value = thickness
                bpy.ops.object.mode_set(mode=mode)
                    
        return {'FINISHED'}
