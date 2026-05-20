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

        # ── Output ────────────────────────────────────────────────────────────
        col = layout.column(heading="Output")
        col.prop(props, "only_selected_objects")
        col.prop(props, "include_hidden")
        col.prop(props, "flat_angle_threshold")
        col.prop(props, "compute_silhouette")
        col.prop(props, "compute_intersections")

        # ── Cleanup ───────────────────────────────────────────────────────────
        col = layout.column(heading="Cleanup")
        col.prop(props, "snap_orphans")
        col.prop(props, "merge_by_distance")
        if props.merge_by_distance:
            col.prop(props, "merge_distance")
        row = col.row()
        row.enabled = props.flat_angle_threshold > 0.0
        row.prop(props, "remove_overlapping_boundary")
