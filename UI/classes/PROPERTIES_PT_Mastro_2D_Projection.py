import bpy
from bpy.types import Panel


class PROPERTIES_PT_Mastro_2D_Projection(Panel):
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "data"
    bl_label       = "MaStro 2D Projection"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.camera is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        cam    = context.camera
        if cam is None:
            return

        props = cam.mastro_projector_cl
        col   = layout.column()
        col.prop(props, "place_on_camera_plane")
        col.prop(props, "camera_clipping")
        col.prop(props, "projection_suffix")
