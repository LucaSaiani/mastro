import bpy
from bpy.types import Panel


class PROPERTIES_PT_Mastro_2D_Projection_Shadow(Panel):
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "data"
    bl_label       = "Shadow"
    bl_parent_id   = "PROPERTIES_PT_Mastro_2D_Projection"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.camera is not None

    def draw_header(self, context):
        self.layout.prop(context.camera.mastro_projector_cl, "run_shadows", text="")

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        ssp    = scene.mastro_projector_props if scene else None
        cam    = context.camera
        if cam is None:
            return

        props       = cam.mastro_projector_cl
        light       = props.light_source
        any_running = ssp.is_running or ssp.proj_is_running if ssp else False

        layout.use_property_split = True
        layout.active = props.run_shadows

        # ── Light source ──────────────────────────────────────────────────────
        col = layout.column()
        col.enabled = not any_running
        col.prop(props, "light_source")
        if not light:
            col.label(text="Select a Sun or Area light", icon='ERROR')

        layout.separator()

        # ── Quality ───────────────────────────────────────────────────────────
        col = layout.column(heading="Quality")
        col.enabled = not any_running
        col.prop(props, "grid_subdivisions")
        col.prop(props, "render_boundary_res")
        col.prop(props, "render_interior_res")
