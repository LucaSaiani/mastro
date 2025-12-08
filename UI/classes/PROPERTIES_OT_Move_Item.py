import bpy
from bpy.types import Operator
from bpy.props import EnumProperty

from ...Utils.update_attributes import update_typology_uses_list, update_all_mastro_meshes_useList

class PROPERTIES_OT_Move_Item(Operator):
    """Generic operator to move items up or down."""
    bl_idname = "generic.move_item"
    bl_label = "Generic operator to move items in a UI list"
    
    direction: EnumProperty(
        items=(('UP', 'Up', ''), ('DOWN', 'Down', ''))
    )
    list_name: str
    index_name: str
    filter_name: str = None
    node_type: str = None

    def execute(self, context):
        scene = context.scene
        my_list = getattr(scene, self.list_name)
        index = getattr(scene, self.index_name)
       
        neighbor = index + (-1 if self.direction == 'UP' else 1)
        if 0 <= neighbor < len(my_list):
            my_list.move(neighbor, index)
            setattr(scene, self.index_name, neighbor)
            
            if self.filter_name:
                if "gn" in self.node_type:
                    bpy.ops.node.mastro_gn_separate_geometry_by(filter_name=self.filter_name, 
                                                                output_id = my_list[neighbor].id, 
                                                                output_direction=self.direction)
                    bpy.ops.node.mastro_gn_filter_by(filter_name=self.filter_name,
                                                    output_id = my_list[neighbor].id, 
                                                    output_direction=self.direction)
                if "shader" in self.node_type:
                    bpy.ops.node.mastro_shader_filter_by(filter_name=self.filter_name,
                                                        output_id = my_list[neighbor].id, 
                                                        output_direction=self.direction)

            
            
        return {'FINISHED'}

# Move the selected use up or down in the list
class PROPERTIES_OT_Typology_Uses_List_Move_Item(Operator):
    '''Move the selected use up or down in the list'''
    bl_idname = "mastro_typology_uses_name_list.move_item"
    bl_label = "Move use"

    direction: EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.mastro_typology_uses_name_list

    def move_index(self):
        index = bpy.context.scene.mastro_typology_uses_name_list_index
        list_length = len(bpy.context.scene.mastro_typology_uses_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.mastro_typology_uses_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mastro_typology_uses_name_list = context.scene.mastro_typology_uses_name_list
        index = context.scene.mastro_typology_uses_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mastro_typology_uses_name_list.move(neighbor, index)
        self.move_index()
        
        update_typology_uses_list(context)
        update_all_mastro_meshes_useList(self, context)
        return{'FINISHED'}