import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Wall(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Wall"
    bl_parent_id = "PROPERTIES_PT_Mastro_Architecture"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0    
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.  
        
        row = layout.row()
        rows = 3
            
        row = layout.row()
        row.template_list("PROPERTIES_UL_Wall", "wall_list", scene,
                        "mastro_wall_name_list", scene, "mastro_wall_name_list_index", rows = rows)
        
        col = row.column(align=True)
        col.operator("mastro_wall_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("mastro_wall_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_wall_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # index = context.scene.mastro_wall_name_list_index
        # if len(context.scene.mastro_wall_name_list) > 0:
        #     layout.prop(context.scene.mastro_wall_name_list[index], "wallThickness", text="Thickness")
        #     layout.prop(context.scene.mastro_wall_name_list[index], "wallOffset", text="Offset")
