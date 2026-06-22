import bpy
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Custom_Properties(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Custom Properties"
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3

    def draw(self, context):
        scene = context.scene

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row()
        row.template_list("PROPERTIES_UL_Custom_property", "custom_property_list", scene,
                        "mastro_custom_property_name_list", scene, "mastro_custom_property_name_list_index", rows=3)

        index = scene.mastro_custom_property_name_list_index
        has_item = len(scene.mastro_custom_property_name_list) > 0

        col = row.column(align=True)
        col.operator("mastro_custom_property_name_list.new_item", icon='ADD', text="")
        if has_item:
            item_check = scene.mastro_custom_property_name_list[index]
            if item_check.committed:
                remove_op = col.operator("object.mastro_remove_custom_property", icon='REMOVE', text="")
                remove_op.property_id = item_check.id
                remove_op.object_type  = "all"
            else:
                col.operator("mastro_custom_property_name_list.remove_item", icon='REMOVE', text="")
        col.separator()
        col.operator("mastro_custom_property_name_list.move_item", icon='TRIA_UP',   text="").direction = 'UP'
        col.operator("mastro_custom_property_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'

        if not has_item:
            return

        item = scene.mastro_custom_property_name_list[index]

        type_row = layout.row()
        type_row.enabled = not item.committed
        type_row.prop(item, "property_type")

        if item.property_type == 'INT':
            layout.prop(item, "default_int",  text="Default")
            layout.prop(item, "min_int",      text="Min")
            layout.prop(item, "max_int",      text="Max")
            layout.prop(item, "step_int",     text="Step")
        elif item.property_type == 'FLOAT':
            layout.prop(item, "default_float",   text="Default")
            layout.prop(item, "min_float",       text="Min")
            layout.prop(item, "max_float",       text="Max")
            layout.prop(item, "step_float",      text="Step")
            layout.prop(item, "precision_float", text="Precision")
        elif item.property_type == 'BOOL':
            layout.prop(item, "default_bool", text="Default")
        elif item.property_type == 'STRING':
            row = layout.row()
            row.template_list(
                "PROPERTIES_UL_Custom_property_string", "",
                item, "string_options",
                item, "string_options_index",
                rows=3,
            )
            col = row.column(align=True)
            col.operator("mastro_string_options.new_item",    icon='ADD',        text="")
            col.operator("mastro_string_options.remove_item", icon='REMOVE',     text="")
            col.separator()
            col.operator("mastro_string_options.move_item",   icon='TRIA_UP',    text="").direction = 'UP'
            col.operator("mastro_string_options.move_item",   icon='TRIA_DOWN',  text="").direction = 'DOWN'

        layout.prop(item, "description")

        assign_col = layout.column(heading="Assign to")
        assign_col.enabled = not item.committed
        assign_col.prop(item, "assign_to_mass",   text="Mass/Block")
        assign_col.prop(item, "assign_to_street", text="Street")

