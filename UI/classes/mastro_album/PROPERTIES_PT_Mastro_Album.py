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
        obj = context.object
        settings = obj.mastro_album_settings

        layout.prop(settings, "scale")

        layout.operator("object.mastro_parent_to_album", icon='LINKED')

        box = layout.box()
        if not obj.children:
            box.label(text="No objects parented to this album.")
        else:
            col = box.column(align=True)
            for child in obj.children:
                row = col.row()
                row.operator(
                    "object.mastro_album_select_child",
                    text=child.name,
                    icon='OBJECT_DATA',
                    emboss=False,
                ).object_name = child.name
