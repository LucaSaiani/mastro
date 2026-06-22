from bpy.types import Panel


class PROPERTIES_PT_Mastro_Levels(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Level List"
    bl_parent_id = "PROPERTIES_PT_Mastro_Level_Sets"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        row = layout.row()
        row.template_list("PROPERTIES_UL_Level", "level_list", scene,
                           "mastro_level_list", scene, "mastro_level_list_index", rows=3)

        col = row.column(align=True)
        col.operator("mastro_level_list.new_item", icon='ADD', text="")
        col.operator("mastro_level_list.remove_item", icon='REMOVE', text="")
        col.separator()
        col.menu("MASTRO_MT_Level_List_Specials", icon='DOWNARROW_HLT', text="")
