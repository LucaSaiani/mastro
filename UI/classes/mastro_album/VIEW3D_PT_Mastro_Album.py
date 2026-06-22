import bpy
from bpy.types import Panel


class VIEW3D_PT_Mastro_Album(Panel):
    """Sidebar counterpart of PROPERTIES_PT_Mastro_Album, shown nested
    under the main MaStro tab when the active object is a MaStro album."""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "MaStro"
    bl_label       = "Album"
    bl_parent_id   = "VIEW3D_PT_Mastro_Panel"
    bl_order       = 0

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
