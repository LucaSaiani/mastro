import bpy
import math
# import mathutils

_last_view_matrix = None

def matrices_differ(m1, m2, tol=1e-6):
    """Return True if any element of two 4x4 matrices differs beyond the given tolerance."""
    for i in range(4):
        for j in range(4):
            if not math.isclose(m1[i][j], m2[i][j], abs_tol=tol):
                return True
    return False

# Called every 0.1s via a timer; detects 3D viewport rotation to trigger GN dimension updates
def monitor_view_rotation():
    global _last_view_matrix
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            region_3d = area.spaces.active.region_3d
            current_view = region_3d.view_matrix.copy()

            if _last_view_matrix is not None and matrices_differ(current_view, _last_view_matrix):
                # print("✅ La vista 3D è stata ruotata o spostata!")
                _on_view_changed(region_3d)

            _last_view_matrix = current_view
            break
    return 0.1


def _on_view_changed(region_3d):
    """Run side effects that need to react to viewport rotation/movement.

    Safe to write to Scene here (unlike inside a Panel.draw()), since this
    runs from a timer callback with a normal, unrestricted context.
    """
    scene = bpy.context.scene
    if scene is None:
        return

    from .mastro_levels.clip_range import sync_clip_range_on_view_change, update_clip_from_selection
    sync_clip_range_on_view_change(scene, region_3d)
    update_clip_from_selection(bpy.context)

def start_monitoring():
    if not bpy.app.timers.is_registered(monitor_view_rotation):
        bpy.app.timers.register(monitor_view_rotation)
        print("MaStro: viewport monitoring started.")

def stop_monitoring():
    if bpy.app.timers.is_registered(monitor_view_rotation):
        bpy.app.timers.unregister(monitor_view_rotation)
        print("MaStro: viewport monitoring stopped.")
    
def register():
    start_monitoring()

def unregister():
    stop_monitoring()