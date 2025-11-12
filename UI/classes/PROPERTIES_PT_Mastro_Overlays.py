import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Overlay(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = "Show Overlays"
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0
    
    def draw_header(self, context):
        self.layout.prop(context.window_manager, "toggle_show_overlays", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        layout.active = context.window_manager.toggle_show_overlays
        
        # flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        # col = flow.column()
        # col = flow.column(heading="Mass", align = True)
        col = layout.column(heading="Edit Mode Overlays", align=True)
        col.prop(context.window_manager, 'toggle_show_data_edit_mode', icon_only=False)
        col.separator()
        col = layout.column(heading="Block & Mass", align=True)
        col.prop(context.window_manager, 'toggle_storey_number', icon_only=False)
        col.separator()
        col.prop(context.window_manager, 'toggle_typology_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_block_typology_color', icon_only=False)
        col.separator()
        col.prop(context.window_manager, 'toggle_block_normal', icon_only=False)
        col.separator()
        col.prop(context.window_manager, 'toggle_building_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_block_name', icon_only=False)
        
        # col = layout.column(heading="Block", align=True)
        
        
        # col.prop(context.window_manager, 'toggle_storey_number', icon_only=False)
        # col.prop(context.window_manager, 'toggle_typology_name', icon_only=False)
        # col.prop(context.window_manager, 'toggle_building_name', icon_only=False)
        # col.prop(context.window_manager, 'toggle_block_name', icon_only=False)
        
        # col.separator()
        col = layout.column(heading="Wall", align = True)
        col.prop(context.window_manager, 'toggle_wall_type', icon_only=False)
        col.prop(context.window_manager, 'toggle_wall_normal', icon_only=False)
        # col.separator()
        col = layout.column(heading="Floor", align = True)
        col.prop(context.window_manager, 'toggle_floor_name', icon_only=False)
        col = layout.column(heading="Street", align=True)
        col.prop(context.window_manager, 'toggle_street_color', icon_only=False)