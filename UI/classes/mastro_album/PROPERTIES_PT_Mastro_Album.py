import bpy
from bpy.types import Panel


class PROPERTIES_PT_Mastro_Album(Panel):
    """Object Data panel for editing a MaStro album's drawing scale without
    requiring the user to find/edit a custom property manually."""
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "data"
    bl_label       = "MaStro Album"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == 'EMPTY' and obj.get("MaStro album")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        obj = context.object
        settings = obj.mastro_album_settings

        col = layout.column(align=True)
        col.prop(settings, "scale", text="Scale 1:")

        row = layout.row()
        row.template_list(
            "PROPERTIES_UL_Album_Children", "album_children_list",
            settings, "children_display",
            settings, "children_display_index",
            rows=5,
        )
        row.operator("object.mastro_parent_to_album", text="", icon='ADD')

        layout.prop(settings, "icon_size")
