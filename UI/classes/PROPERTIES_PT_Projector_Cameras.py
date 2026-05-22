import bpy
from bpy.types import Panel



class PROPERTIES_PT_Projector_Cameras(Panel):
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "scene"
    bl_label       = "2D Projection"
    bl_parent_id   = "PROPERTIES_PT_Mastro_Project_Data"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        ssp    = scene.mastro_projector_props
        any_running = ssp.is_running or ssp.proj_is_running

        cameras = [
            obj for obj in sorted(scene.objects, key=lambda o: o.name)
            if obj.type == 'CAMERA'
            and obj.data is not None
            and obj.data.mastro_projector_cl.enabled
        ]

        # ── Camera list ───────────────────────────────────────────────────────
        if not cameras:
            layout.label(text="No cameras with projection enabled", icon='INFO')
        else:
            box = layout.box()
            col = box.column(align=True)
            for cam in cameras:
                props = cam.data.mastro_projector_cl
                row = col.row(align=True)
                row.enabled = not any_running

                row.prop(props, "active_for_batch", text="")

                icon = 'VIEW_ORTHO' if cam.data.type == 'ORTHO' else 'VIEW_PERSPECTIVE'
                row.label(text=cam.name, icon=icon)

                sub = row.row(align=True)
                sub.alignment = 'RIGHT'
                if props.run_projection:
                    sub.label(text="", icon='RENDER_STILL')
                if props.run_shadows:
                    sub.label(text="", icon='LIGHT_SUN')

        layout.separator()

        if any_running:
            col = layout.column()
            col.scale_y = 1.4
            col.alert = True
            col.operator("object.mastro_projector_cancel_all", icon='X')
        else:
            active_cams = [
                c for c in cameras
                if c.data.mastro_projector_cl.active_for_batch
            ] if cameras else []
            col = layout.column()
            col.scale_y = 1.4
            col.enabled = bool(active_cams)
            col.operator("object.mastro_projector_run_batch", icon='PLAY',
                         text=f"Calculate ({len(active_cams)})")

        # ── Camera Sets ───────────────────────────────────────────────────────
        if not cameras:
            return

        layout.separator()
        layout.label(text="Camera Sets", icon='RENDERLAYERS')

        if not ssp.camera_sets:
            layout.label(text="Initializing…", icon='INFO')
            return

        row = layout.row()
        row.template_list(
            "PROPERTIES_UL_Camera_Sets", "",
            ssp, "camera_sets",
            ssp, "active_set_index",
            rows=3,
        )

        col = row.column(align=True)
        col.operator("mastro.camera_set_add",       text="", icon='ADD')
        op_rem = col.operator("mastro.camera_set_remove",    text="", icon='REMOVE')
        col.separator()
        col.operator("mastro.camera_set_duplicate",  text="", icon='DUPLICATE')
        col.separator()
        col.operator("mastro.camera_set_move_up",    text="", icon='TRIA_UP')
        col.operator("mastro.camera_set_move_down",  text="", icon='TRIA_DOWN')

        # Disable Remove / MoveUp / MoveDown when Set 0 is selected
        idx = ssp.active_set_index
        if 0 <= idx < len(ssp.camera_sets):
            active_set = ssp.camera_sets[idx]

            # ── Members of the active set ──────────────────────────────────
            layout.separator()
            if active_set.is_default:
                layout.label(
                    text="Contains all enabled cameras (managed automatically)",
                    icon='INFO'
                )
            else:
                layout.label(text=f"Cameras in '{active_set.name}':")
                member_names = {item.camera_name for item in active_set.cameras}
                box = layout.box()
                col = box.column(align=True)
                for cam in cameras:
                    in_set = cam.name in member_names
                    row = col.row(align=True)
                    icon_check = 'CHECKBOX_HLT' if in_set else 'CHECKBOX_DEHLT'
                    op = row.operator(
                        "mastro.camera_set_toggle_camera",
                        text=cam.name,
                        icon=icon_check,
                        emboss=False,
                    )
                    op.camera_name = cam.name
