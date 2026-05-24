import bpy
from bpy.types import Panel


class PROPERTIES_PT_Mastro_2D_Projection(Panel):
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "data"
    bl_label       = "MaStro Projection"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.camera is not None

    def draw_header(self, context):
        cam = context.camera
        if cam is not None:
            self.layout.prop(cam.mastro_projector_cl, "enabled", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        cam    = context.camera
        if cam is None:
            return

        props = cam.mastro_projector_cl
        layout.active = props.enabled
        col   = layout.column()
        col.prop(props, "source_collection")
        col.prop(props, "camera_clipping")
        col.prop(props, "compute_intersections")
        col.prop(props, "convert_to_grease_pencil")
        col.prop(props, "place_on_camera_plane")
