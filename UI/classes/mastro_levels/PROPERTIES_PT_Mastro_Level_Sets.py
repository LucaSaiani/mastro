from bpy.types import Panel


class PROPERTIES_PT_Mastro_Level_Sets(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Levels"
    bl_parent_id = "PROPERTIES_PT_Mastro_Sets"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

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
            idx = scene.mastro_level_set_list_index
            level_sets = scene.mastro_level_set_list
            active_set = level_sets[idx] if 0 <= idx < len(level_sets) else None
            is_all_levels = active_set.id == 0 if active_set else True

            row = layout.row()
            row.template_list("PROPERTIES_UL_Level_Set_Members", "level_set_members", scene,
                               "mastro_level_list", scene, "mastro_level_list_index", rows=4)
            col = row.column(align=True)
            # The "All Levels" set always contains everything, so the
            # filter would be a no-op; keep it visible but disabled.
            sub = col.column()
            sub.enabled = not is_all_levels
            sub.prop(scene, "mastro_level_set_filter_members_only", text="",
                     icon='FILTER', toggle=True)
