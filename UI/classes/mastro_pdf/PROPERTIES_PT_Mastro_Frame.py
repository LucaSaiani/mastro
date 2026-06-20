import bpy
from bpy.types import Panel


class PROPERTIES_PT_Mastro_Frame(Panel):
    """Object Data panel for editing a MaStro frame's paper size without
    requiring the user to find/edit obj.scale manually."""
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "data"
    bl_label       = "MaStro Frame"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == 'EMPTY' and obj.get("MaStro frame")

    def draw(self, context):
        layout = self.layout
        settings = context.object.mastro_frame_settings

        layout.prop(settings, "format")
        layout.prop(settings, "orientation")
        col = layout.column()
        col.enabled = settings.format == 'CUSTOM'
        col.prop(settings, "width")
        col.prop(settings, "height")
