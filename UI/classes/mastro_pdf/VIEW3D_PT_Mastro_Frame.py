import bpy
from bpy.types import Panel


class VIEW3D_PT_Mastro_Frame(Panel):
    """Sidebar counterpart of PROPERTIES_PT_Mastro_Frame, shown nested
    under the main MaStro tab when the active object is a MaStro frame."""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "MaStro"
    bl_label       = "Frame"
    bl_parent_id   = "VIEW3D_PT_Mastro_Panel"
    bl_order       = 0

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
