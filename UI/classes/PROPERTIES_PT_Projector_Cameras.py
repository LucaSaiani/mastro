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

        if not cameras:
            layout.label(text="No cameras with projection enabled", icon='INFO')
        else:
            box = layout.box()
            col = box.column(align=True)
            for cam in cameras:
                props = cam.data.mastro_projector_cl
                row = col.row(align=True)
                row.enabled = not any_running

                # Active-for-batch toggle
                row.prop(props, "active_for_batch", text="")

                # Camera type icon + name
                icon = 'VIEW_ORTHO' if cam.data.type == 'ORTHO' else 'VIEW_PERSPECTIVE'
                row.label(text=cam.name, icon=icon)

                # Method indicators (right-aligned)
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
