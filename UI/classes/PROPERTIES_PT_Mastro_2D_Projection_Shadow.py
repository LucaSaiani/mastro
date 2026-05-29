import math

import bpy
from bpy.types import Panel

from ...Utils.projection.shadow_silhouette import _CACHE_PREFIX


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
        cam = context.camera
        props = cam.mastro_projector_cl
        self.layout.active = props.enabled
        self.layout.prop(props, "run_shadows", text="")

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
        layout.active = props.enabled and props.run_shadows

        # ── Light source ──────────────────────────────────────────────────────
        col = layout.column()
        col.enabled = not any_running
        col.prop(props, "light_source")
        sub = col.column()
        sub.active = not bool(light)   # disabled (greyed) when a real light is assigned
        sub.prop(props, "virtual_azimuth",    text="Azimuth")
        sub.prop(props, "virtual_elevation",  text="Elevation")
        sub.prop(props, "light_camera_lock",  text="Camera Lock")

        layout.separator()

        # ── Method ────────────────────────────────────────────────────────────
        col = layout.column()
        col.enabled = not any_running
        col.prop(props, "shadow_method")

        layout.separator()

        # ── Quality ───────────────────────────────────────────────────────────
        if props.shadow_method == 'TRACE':
            col = layout.column(heading="Quality")
            col.enabled = not any_running
            col.prop(props, "grid_subdivisions")
        else:
            col = layout.column(heading="Quality")
            col.enabled = not any_running
            col.prop(props, "cutter_detection")
            if props.light_source:
                light_key = props.light_source.name
            elif not props.light_camera_lock:
                az_deg = round(math.degrees(props.virtual_azimuth))
                el_deg = round(math.degrees(props.virtual_elevation))
                light_key = f"virtual_world_{az_deg}_{el_deg}"
            else:
                light_key = None
            cache_name = (_CACHE_PREFIX + light_key) if light_key else None
            cache_exists = cache_name and bpy.data.objects.get(cache_name) is not None
            row = col.row(align=True)
            row.prop(props, "use_cast_shadow_cache")
            if cache_exists:
                op = row.operator(
                    "object.mastro_clear_shadow_cache",
                    text="", icon="TRASH"
                )
                op.cache_name = cache_name
