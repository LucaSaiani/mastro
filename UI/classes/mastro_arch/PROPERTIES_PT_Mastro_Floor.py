import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Floor(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Floor"
    bl_parent_id = "PROPERTIES_PT_Mastro_Architecture"
    bl_options = {'DEFAULT_CLOSED'}      
    bl_order = 1
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        #row.label(text="Floor")
        
        # is_sortable = len(scene.mastro_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("PROPERTIES_UL_Floor", "floor_list", scene,
                        "mastro_floor_name_list", scene, "mastro_floor_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_floor_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("mastro_floor_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_floor_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        
        # if scene.mastro_floor_name_list_index >= 0 and scene.mastro_floor_name_list:
        #     item = scene.mastro_floor_name_list[scene.mastro_floor_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Floor Name")