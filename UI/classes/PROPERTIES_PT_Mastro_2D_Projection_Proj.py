import bpy
from bpy.types import Panel


class PROPERTIES_PT_Mastro_2D_Projection_Proj(Panel):
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "data"
    bl_label       = "2D Projection"
    bl_parent_id   = "PROPERTIES_PT_Mastro_2D_Projection"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.camera is not None

    def draw_header(self, context):
        cam = context.camera
        props = cam.mastro_projector_cl
        self.layout.active = props.enabled
        self.layout.prop(props, "run_projection", text="")

    def draw(self, context):
        layout = self.layout
        cam    = context.camera
        if cam is None:
            return

        props = cam.mastro_projector_cl
        layout.use_property_split = True
        layout.active = props.enabled and props.run_projection

        # ── Quality ───────────────────────────────────────────────────────────
        col = layout.column(heading="Quality")
        col.prop(props, "segment_length")
        col.prop(props, "ray_offset")
        col.prop(props, "flat_angle_threshold")

        col = layout.column()
        col.prop(props, "source_collection")
        col.prop(props, "include_hidden")
        col.prop(props, "compute_silhouette", text="Silhouette")
        col.prop(props, "snap_orphans")
        row = col.row(align=True, heading="Merge by Distance")
        row.prop(props, "merge_by_distance", text="")
        sub = row.row()
        sub.active = props.merge_by_distance
        sub.prop(props, "merge_distance", text="")
        row = col.row()
        row.enabled = props.flat_angle_threshold > 0.0
        row.prop(props, "remove_overlapping_boundary")
