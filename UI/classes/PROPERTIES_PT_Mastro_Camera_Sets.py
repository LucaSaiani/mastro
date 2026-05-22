import bpy
from bpy.types import Panel


class PROPERTIES_PT_Mastro_Camera_Sets(Panel):
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "scene"
    bl_label       = "Camera Sets"
    bl_parent_id   = "PROPERTIES_PT_Mastro_Project_Data"
    bl_options     = {"DEFAULT_CLOSED"}
    bl_order       =  4

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        ssp    = scene.mastro_projector_props
        any_running = ssp.is_running or ssp.proj_is_running

        has_cameras = any(
            obj.type == 'CAMERA'
            and obj.data is not None
            and obj.data.mastro_projector_cl.enabled
            for obj in scene.objects
        )

        if not has_cameras:
            layout.label(text="No cameras with projection enabled", icon='INFO')
            return

        if not ssp.camera_sets:
            layout.label(text="Initializing…", icon='INFO')
            return

        row = layout.row()
        row.template_list(
            "PROPERTIES_UL_Camera_Sets", "",
            ssp, "camera_sets",
            ssp, "active_set_index",
            rows=5,
        )
        col = row.column(align=True)
        col.operator("mastro.camera_set_add",        text="", icon='ADD')
        col.operator("mastro.camera_set_remove",     text="", icon='REMOVE')
        col.separator()
        col.operator("mastro.camera_set_duplicate",  text="", icon='DUPLICATE')
        col.separator()
        col.operator("mastro.camera_set_move_up",    text="", icon='TRIA_UP')
        col.operator("mastro.camera_set_move_down",  text="", icon='TRIA_DOWN')

        # ── Camera list for the active set ────────────────────────────────────
        idx = ssp.active_set_index
        if not (0 <= idx < len(ssp.camera_sets)):
            return

        # Always use Set 0 as data source (it mirrors all enabled cameras)
        default_set = ssp.camera_sets[0]
        if not default_set.cameras:
            return

        active_set = ssp.camera_sets[idx]

        row = layout.row()
        row.enabled = not any_running
        row.template_list(
            "PROPERTIES_UL_Set_Cameras", "",
            default_set, "cameras",
            ssp, "active_camera_index",
            rows=4,
        )

        # ── Calculate button for current set ──────────────────────────────────
        layout.separator()
        if active_set.is_default:
            member_names = {item.camera_name for item in default_set.cameras}
        else:
            member_names = {item.camera_name for item in active_set.cameras}

        active_count = sum(
            1 for name in member_names
            if (obj := bpy.data.objects.get(name)) is not None
            and obj.data is not None
            and obj.data.mastro_projector_cl.active_for_batch
        )

        if any_running:
            col = layout.column()
            col.alert = True
            col.operator("object.mastro_projector_cancel_all", icon='X')
        else:
            col = layout.column()
            col.enabled = active_count > 0
            op = col.operator("object.mastro_projector_run_batch", icon='RENDER_STILL',
                              text="Bake")
            op.set_index = idx
