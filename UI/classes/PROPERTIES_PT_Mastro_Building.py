import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Building(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Building"
    bl_parent_id = "PROPERTIES_PT_Mastro_Mass"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        
        #row.label(text="Building")
        # row.prop(context.window_manager, 'mastro_toggle_building_name', toggle=True, icon="HIDE_OFF", icon_only=True)
        
        # is_sortable = len(scene.mastro_building_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("PROPERTIES_UL_Building", "building_list", scene,
                        "mastro_building_name_list", scene, "mastro_building_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_building_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("mastro_building_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_building_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        
        # if scene.mastro_building_name_list_index >= 0 and scene.mastro_building_name_list:
        #     item = scene.mastro_building_name_list[scene.mastro_building_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Building Name")