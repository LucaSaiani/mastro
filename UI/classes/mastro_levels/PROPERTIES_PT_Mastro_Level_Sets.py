from bpy.types import Panel


class PROPERTIES_PT_Mastro_Level_Sets(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Level Sets"
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        # ── Sets ────────────────────────────────────────────────────────────
        layout.label(text="Sets")
        row = layout.row()
        # rows=5 matches the 5 buttons in the column to the right (Add,
        # Remove, Duplicate, Move Up, Move Down); the list itself stays
        # user-resizable via Blender's own drag handle.
        row.template_list("PROPERTIES_UL_Level_Set", "level_set_list", scene,
                           "mastro_level_set_list", scene, "mastro_level_set_list_index", rows=5)

        col = row.column(align=True)
        col.operator("mastro_level_set_list.new_item", icon='ADD', text="")
        col.operator("mastro_level_set_list.remove_item", icon='REMOVE', text="")
        col.separator()
        col.operator("mastro_level_set_list.duplicate_item", icon='DUPLICATE', text="")
        col.separator()
        col.operator("mastro_level_set_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_level_set_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'

        if scene.mastro_level_list:
            layout.template_list("PROPERTIES_UL_Level_Set_Members", "level_set_members", scene,
                                  "mastro_level_list", scene, "mastro_level_list_index", rows=4)

        layout.separator()

        # ── Levels ──────────────────────────────────────────────────────────
        layout.label(text="Levels")
        row = layout.row()
        row.template_list("PROPERTIES_UL_Level", "level_list", scene,
                           "mastro_level_list", scene, "mastro_level_list_index", rows=3)

        col = row.column(align=True)
        col.operator("mastro_level_list.new_item", icon='ADD', text="")
        col.operator("mastro_level_list.remove_item", icon='REMOVE', text="")
        col.separator()
        col.menu("MASTRO_MT_Level_List_Specials", icon='DOWNARROW_HLT', text="")
