import bpy
from bpy.types import Operator

_POLL_INTERVAL = 0.25  # seconds between checks


def _tick_batch_queue():
    """Timer that advances the batch queue once the current camera finishes."""
    try:
        scene = bpy.context.scene
        ssp   = scene.mastro_projector_props
    except (AttributeError, TypeError):
        return None  # unregister

    if ssp.is_running or ssp.proj_is_running:
        return _POLL_INTERVAL  # still busy — keep waiting

    # Advance to next camera
    ssp.batch_cursor += 1
    idx = ssp.batch_cursor
    if idx >= len(ssp.batch_queue):
        ssp.batch_queue.clear()
        ssp.batch_cursor = 0
        return None  # queue exhausted — unregister

    cam_name = ssp.batch_queue[idx].camera_name
    cam_obj  = scene.objects.get(cam_name)
    if cam_obj is None or cam_obj.type != 'CAMERA':
        # Camera was removed — skip to next tick
        return 0.0

    scene.camera = cam_obj
    bpy.ops.object.mastro_projector_run_all()
    return _POLL_INTERVAL


class OBJECT_OT_RunBatch(Operator):
    bl_idname      = "object.mastro_projector_run_batch"
    bl_label       = "Calculate"
    bl_description = "Run projection and/or shadow for all active cameras"

    def execute(self, context):
        scene = context.scene
        ssp   = scene.mastro_projector_props

        cameras = [
            obj for obj in sorted(scene.objects, key=lambda o: o.name)
            if obj.type == 'CAMERA'
            and obj.data is not None
            and obj.data.mastro_projector_cl.enabled
            and obj.data.mastro_projector_cl.active_for_batch
        ]

        if not cameras:
            self.report({'WARNING'}, "No active cameras to process.")
            return {'CANCELLED'}

        # Build queue
        ssp.batch_queue.clear()
        for cam in cameras:
            item = ssp.batch_queue.add()
            item.camera_name = cam.name
        ssp.batch_cursor = 0

        # Start first camera
        scene.camera = cameras[0]
        bpy.ops.object.mastro_projector_run_all()

        if len(cameras) > 1:
            bpy.app.timers.register(_tick_batch_queue,
                                    first_interval=_POLL_INTERVAL,
                                    persistent=False)

        return {'FINISHED'}
