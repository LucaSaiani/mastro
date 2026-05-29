import bpy
from bpy.types import Panel


class VIEW3D_PT_Mastro_Overlay(Panel):
    """MaStro overlay toggles in Viewport Overlays."""
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label       = "MaStro"
    bl_parent_id   = "VIEW3D_PT_overlay"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.prop(context.window_manager, "mastro_toggle_show_overlays", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split    = True
        layout.use_property_decorate = False
        layout.active = context.window_manager.mastro_toggle_show_overlays

        col = layout.column(heading="Edit Mode Overlays", align=True)
        col.prop(context.window_manager, 'mastro_toggle_show_data_edit_mode')
        col.separator()
        col = layout.column(heading="Block & Mass", align=True)
        col.prop(context.window_manager, 'mastro_toggle_storey_number')
        col.separator()
        col.prop(context.window_manager, 'mastro_toggle_typology_name')
        col.prop(context.window_manager, 'mastro_toggle_block_typology_color')
        col.separator()
        col.prop(context.window_manager, 'mastro_toggle_block_normal')
        col.separator()
        col.prop(context.window_manager, 'mastro_toggle_building_name')
        col.prop(context.window_manager, 'mastro_toggle_block_name')
        col = layout.column(heading="Wall", align=True)
        col.prop(context.window_manager, 'mastro_toggle_wall_type')
        col.prop(context.window_manager, 'mastro_toggle_wall_normal')
        col = layout.column(heading="Floor", align=True)
        col.prop(context.window_manager, 'mastro_toggle_floor_name')
        col = layout.column(heading="Street", align=True)
        col.prop(context.window_manager, 'mastro_toggle_street_color')
