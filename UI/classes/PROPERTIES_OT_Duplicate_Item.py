import bpy 
from bpy.types import Operator 

import random

class PROPERTIES_OT_Typology_List_Duplicate_Item(Operator):
    '''Make a duplicate of the current typology and its uses'''
    bl_idname = "mastro_typology_name_list.duplicate_item"
    bl_label = "Duplicate typology"

    def execute(self, context): 
        # get the index of the current element
        index = context.scene.mastro_typology_name_list_index
        nameToCopy = context.scene.mastro_typology_name_list[index].name
        usesToCopy = context.scene.mastro_typology_name_list[index].useList
        # create a new entry
        context.scene.mastro_typology_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_typology_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_typology_name_list)-1
        context.scene.mastro_typology_name_list[last].id = max(temp_list)+1
        # copy data to the new entry
        context.scene.mastro_typology_name_list[last].name = nameToCopy + " copy"
        context.scene.mastro_typology_name_list[last].useList = usesToCopy
        context.scene.mastro_typology_name_list[last].typologyEdgeColor = [random.random(), random.random(), random.random()]
        
        bpy.ops.node.mastro_gn_filter_by(filter_name="typology")
        bpy.ops.node.mastro_shader_filter_by(filter_name="typology")
        return{'FINISHED'}