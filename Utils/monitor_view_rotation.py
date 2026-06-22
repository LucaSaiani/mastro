import bpy
import math
# import mathutils

# Keyed by region_3d.as_pointer() (a stable per-region identifier) rather
# than a single global matrix, so every open VIEW_3D viewport is tracked
# independently instead of only whichever one happened to be first.
_last_view_matrices = {}

def matrices_differ(m1, m2, tol=1e-6):
    """Return True if any element of two 4x4 matrices differs beyond the given tolerance."""
    for i in range(4):
        for j in range(4):
            if not math.isclose(m1[i][j], m2[i][j], abs_tol=tol):
                return True
    return False

# Called every 0.1s via a timer; detects 3D viewport rotation across every
# open viewport (not just one) to trigger GN dimension updates and the
# per-viewport clip-range sync below.
def monitor_view_rotation():
    seen_keys = set()
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            space = area.spaces.active
            region_3d = space.region_3d
            key = region_3d.as_pointer()
            seen_keys.add(key)
            current_view = region_3d.view_matrix.copy()

            last_view = _last_view_matrices.get(key)
            if last_view is not None and matrices_differ(current_view, last_view):
                _on_view_changed(area, space, region_3d)
                # _on_view_changed may itself write view_location.z (see
                # apply_clip_to_space), which changes view_matrix again -
                # re-read it so next tick doesn't see that as a further
                # "the user moved the view" change and loop one extra tick.
                current_view = region_3d.view_matrix.copy()

            _last_view_matrices[key] = current_view

    # Drop entries for viewports that no longer exist (closed area/window),
    # so this dict doesn't grow unbounded over a long session.
    for key in list(_last_view_matrices):
        if key not in seen_keys:
            del _last_view_matrices[key]

    from .mastro_levels.clip_range import forget_clip_state
    forget_clip_state(seen_keys)

    return 0.1


def _on_view_changed(area, space, region_3d):
    """Run side effects that need to react to one viewport's rotation/
    movement (e.g. flipping between Top and Bottom ortho, or leaving it).

    Safe to write to Scene here (unlike inside a Panel.draw()), since this
    runs from a timer callback with a normal, unrestricted context.
    """
    scene = bpy.context.scene
    if scene is None:
        return

    from .mastro_levels.clip_range import (
        sync_clip_range_on_view_change, apply_clip_to_space,
        is_top_bottom_ortho, get_view_side, restore_original_clip_state,
    )
    if not is_top_bottom_ortho(region_3d):
        # Left Top/Bottom ortho (rotated away, or switched to perspective/
        # another ortho side) - restore whatever clip_start/clip_end/
        # view_location.z were before we started overriding them, rather
        # than leaving the override stuck in place.
        restore_original_clip_state(scene, space, region_3d)
        area.tag_redraw()
        return

    # Clip-range state is per-side now (top/bottom each independent - see
    # clip_range.py), so only this viewport's own side needs rebuilding;
    # a Top viewport elsewhere is unaffected by a Bottom viewport's change.
    side = get_view_side(region_3d)
    sync_clip_range_on_view_change(scene, side)
    # apply_clip_to_space writes region_3d.view_location.z, which doesn't
    # auto-redraw the viewport (unlike Scene/ID property changes).
    apply_clip_to_space(scene, space)
    area.tag_redraw()

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
