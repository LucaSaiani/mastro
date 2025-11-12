import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Block(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Block"
    bl_parent_id = "PROPERTIES_PT_Mastro_Mass"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        # row.label(text="Block")
        
        rows = 3
        
        row = layout.row()
        row.template_list("PROPERTIES_UL_Block", "block_list", scene,
                        "mastro_block_name_list", scene, "mastro_block_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_block_name_list.new_item", icon='ADD', text="")
        # col.operator("mastro_wall_type_list.delete_item", icon='REMOVE', text="")
        col.separator()
        col.operator("mastro_block_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_block_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        # row.prop(context.scene, "mastro_block_names", icon="MOD_BOOLEAN", icon_only=True, text="")
        # row.operator("scene.add_block_name", icon="ADD", text="New")
        
        # if scene.mastro_block_name_list_index >= 0 and scene.mastro_block_name_list:
        #     item = scene.mastro_block_name_list[scene.mastro_block_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Block Name")
            
        # row.prop(item, "index")