import bpy
from bpy.types import Operator

import random

from ...Utils.update_attributes import update_typology_uses_list

class PROPERTIES_OT_New_Item(Operator):
    """Generic operator to add a new item to a list."""
    bl_idname = "properties.new_item"
    bl_label = "Generic operator to add a new item to a list."
    list_name: str
    filter_name: str = None
    color_attr: str = None

    def execute(self, context):
        scene = context.scene
        collection = getattr(scene, self.list_name)

        # Add new entry
        collection.add()
        last = len(collection) - 1

        # Assign progressive ID
        ids = [el.id for el in collection if hasattr(el, 'id')]
        collection[last].id = max(ids) + 1 if ids else 1

        # Optional random color attribute
        if self.color_attr and hasattr(collection[last], self.color_attr):
            setattr(collection[last], self.color_attr, [random.random() for _ in range(3)])

        # Optional shader filter operator
        if self.filter_name:
            try:
                bpy.ops.node.mastro_shader_filter_by(filter_name=self.filter_name)
            except:
                print(f"[WARN] Could not execute shader filter for {self.filter_name}")

        return {'FINISHED'}
    
# Add a new use to the list of uses of the selected typology. 
# Uses are limited to seven uses for each typology
class PROPERTIES_OT_Typology_Uses_List_New_Item(Operator):
    '''Add a new use to the typology. 
The number of uses is limited to 7 for each typology'''
    bl_idname = "mastro_typology_uses_name_list.new_item"
    bl_label = "Add use"
    
    @classmethod
    def poll(cls, context):
        return len(context.scene.mastro_typology_uses_name_list) <7

    def execute(self, context): 
        context.scene.mastro_typology_uses_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_typology_uses_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_typology_uses_name_list)-1
        
        context.scene.mastro_typology_uses_name_list[last].id = max(temp_list)+1
        context.scene.mastro_typology_uses_name_list[last].typologyEdgeColor = [random.random(), random.random(), random.random()]
        return{'FINISHED'}
    
# Add a new use to the list of the uses for the current project
class PROPERTIES_OT_Use_List_New_Item(Operator):
    '''Add a new use'''
    bl_idname = "mastro_use_name_list.new_item"
    bl_label = "New use"

    def execute(self, context): 
        context.scene.mastro_use_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_use_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_use_name_list)-1
        
        id = max(temp_list)+1
        context.scene.mastro_use_name_list[last].id = id
        
        subIndex = context.scene.mastro_typology_uses_name_list_index
        context.scene.mastro_typology_uses_name_list[subIndex].name = context.scene.mastro_use_name_list[last].name
        context.scene.mastro_typology_uses_name_list[subIndex].id = id
        update_typology_uses_list(context)
        
        bpy.ops.node.mastro_gn_filter_by(filter_name="use")
        bpy.ops.node.mastro_shader_filter_by(filter_name="use")
        return{'FINISHED'}

