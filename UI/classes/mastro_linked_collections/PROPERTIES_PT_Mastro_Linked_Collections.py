from bpy.types import Panel


class PROPERTIES_PT_Mastro_Linked_Collections(Panel):
    """Manage collections linked via the mastro Linked Collections workflow: link, unload, reload, remove."""
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Linked Collections"
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        props = context.scene.mastro_linked_collections_props
        layout = self.layout

        row = layout.row()
        row.template_list(
            "LINKED_COLLECTIONS_UL_List", "",
            props, "entries",
            props, "active_index",
            rows=5,
        )

        col = row.column(align=True)
        col.operator("mastro_linked_collections.link", icon='ADD', text="")
        col.operator("mastro_linked_collections.remove", icon='REMOVE', text="")

        if 0 <= props.active_index < len(props.entries):
            entry = props.entries[props.active_index]
            row = layout.row()
            if entry.status == 'LOADED':
                row.operator("mastro_linked_collections.unload", text="Unload", icon='HIDE_ON')
            else:
                row.operator("mastro_linked_collections.reload", text="Reload", icon='HIDE_OFF')

            box = layout.box()
            box.label(text=entry.filepath, icon='FILE_BLEND')
