import bpy 
from bpy.types import Operator

# # when a typology is selected, it is necessary to update the
# # uses in the UIList using the ones stored in Scene.mastro_typology_uses_name_list 
class PROPERTIES_OT_Update_Use_List(Operator):
    bl_idname = "ui.mastro_update_use_list"
    bl_label = "Update Use List"
    
    def execute(self, context):
        scene = context.scene
        # previous = scene.mastro_previous_selected_typology
        # current = scene.mastro_typology_name_list_index
        # if previous != current:
        scene.mastro_previous_selected_typology = scene.mastro_typology_name_list_index
        use_name_list = scene.mastro_typology_uses_name_list
        while len(use_name_list) > 0:
            index = scene.mastro_typology_uses_name_list_index
            use_name_list.remove(index)
            scene.mastro_typology_uses_name_list_index = min(max(0, index - 1), len(use_name_list) - 1)
        # add the uses stored in the typology to the current typology use UIList        
        selected_typology_index = scene.mastro_typology_name_list_index
        if len(scene.mastro_typology_name_list) > 0:
            list = scene.mastro_typology_name_list[selected_typology_index].useList    
            split_list = list.split(";")
            for el in split_list:
                scene.mastro_typology_uses_name_list.add()
                temp_list = []    
                temp_list.append(int(el))
                last = len(scene.mastro_typology_uses_name_list)-1
                # look for the correspondent use name in mastro_use_name_list
                for use in scene.mastro_use_name_list:
                    if int(el) == use.id:
                        scene.mastro_typology_uses_name_list[last].id = use.id
                        scene.mastro_typology_uses_name_list[last].name = use.name 
                        break
        return{'FINISHED'}