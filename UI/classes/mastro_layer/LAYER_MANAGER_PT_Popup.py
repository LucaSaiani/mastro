import bpy
from bpy.types import Panel


class LAYER_MANAGER_PT_Popup(Panel):
    """Floating popup panel with the sortable view-layer list."""
    bl_label = "View Layers"
    bl_idname = "LAYER_MANAGER_PT_Popup"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'INSTANCED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.mastro_layer_manager_props

        row = layout.row()
        row.template_list(
            "LAYER_MANAGER_UL_layer_list", "",
            props, "layer_slots",
            props, "active_index",
            rows=6,
        )

        col = row.column(align=True)
        col.operator("layer_manager.add_layer_popup", text="", icon='DUPLICATE')

        col.separator()
        col.operator("layer_manager.move_item", icon='TRIA_UP_BAR',   text="").direction = 'TOP'
        col.operator("layer_manager.move_item", icon='TRIA_UP',       text="").direction = 'UP'
        col.operator("layer_manager.move_item", icon='TRIA_DOWN',     text="").direction = 'DOWN'
        col.operator("layer_manager.move_item", icon='TRIA_DOWN_BAR', text="").direction = 'BOTTOM'

        col.separator()
        col.operator_menu_enum("layer_manager.sort_layers", "direction", text="", icon='SORTALPHA')

        col.separator()
        col.operator("scene.view_layer_remove", icon="X", text="")
