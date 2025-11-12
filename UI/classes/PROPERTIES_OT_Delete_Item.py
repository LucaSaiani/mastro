import bpy 
from bpy.types import Operator

from ...Utils.update_attributes import update_typology_uses_list
class PROPERTIES_OT_Typology_Uses_List_Delete_Item(Operator):
    '''Remove the use from the current typology'''
    bl_idname = "mastro_typology_uses_name_list.delete_item"
    bl_label = "Remove"
    
    @classmethod
    def poll(cls, context):
        return context.scene.mastro_typology_uses_name_list
        
    def execute(self, context):
        my_list = context.scene.mastro_typology_uses_name_list
        index = context.scene.mastro_typology_uses_name_list_index

        my_list.remove(index)
        context.scene.mastro_typology_uses_name_list_index = min(max(0, index - 1), len(my_list) - 1)
        
        update_typology_uses_list(context)
        return{'FINISHED'}