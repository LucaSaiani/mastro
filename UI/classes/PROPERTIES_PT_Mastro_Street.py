import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Street(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = "Street"
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.  
        
        row = layout.row()
        
        # is_sortable = len(scene.mastro_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("PROPERTIES_UL_Street", "street_list", scene,
                        "mastro_street_name_list", scene, "mastro_street_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_street_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("mastro_street_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_street_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        index = context.scene.mastro_street_name_list_index
        if len(context.scene.mastro_street_name_list) > 0:
            layout.prop(context.scene.mastro_street_name_list[index], "streetWidth", text="Width")
            layout.prop(context.scene.mastro_street_name_list[index], "streetRadius", text="Radius")
      