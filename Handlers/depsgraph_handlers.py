import time

import bpy
from bpy.app.handlers import persistent

from .utils.guard_light_sources import guard_light_sources
from .utils.mastro_projector.sync_camera_sets import sync_default_camera_set
from .utils.mastro_pdf.sync_pdf_frames import sync_pdf_frames
from .mastro_cad.depsgraph_handlers_cad import _check_drawing_objects, _update_scale_header

# Name of the last active node seen in the node editor — used to detect
# selection changes without re-running the full sync every depsgraph tick.
_prev_active_note_name = None

# Timestamp of the last schedule auto-refresh, for throttling.
_last_schedule_refresh = 0.0


def _refresh_schedules():
    """Re-evaluate every open MaStro Schedule node tree, but only recompute
    the currently selected objects' mass data - everything else stays in
    mastro_export_utils._mass_data_cache untouched. Throttled by
    schedule_auto_refresh_interval so dragging a vertex doesn't re-run the
    tree on every single depsgraph tick."""
    global _last_schedule_refresh

    from ..Utils.mastro_preferences.get_preferences import get_prefs
    prefs = get_prefs()
    if not prefs.schedule_auto_refresh:
        return

    now = time.monotonic()
    if now - _last_schedule_refresh < prefs.schedule_auto_refresh_interval:
        return
    _last_schedule_refresh = now

    selected = bpy.context.selected_objects
    if not selected:
        return
    # mastro_number_of_storeys/mastro_undercroft are only ever set
    # explicitly through the Mass panel's own fields (Utils/getter_setter.py),
    # never recomputed live while editing the mesh itself - a topology
    # change (extrude, duplicate, ...) creates new BMesh faces that don't
    # yet carry these values (they default to 0) until the user
    # re-applies the panel. Refreshing the Schedule while a selected
    # object is mid-edit would read those still-zero faces and show the
    # Viewer's area shrinking, then recovering once the user leaves Edit
    # Mode - confirmed as the actual cause of a "the area disappears
    # while editing" report, not a bug in the area calculation itself
    # (Evaluate Attribute already reads the correct, live edit-mode BMesh
    # via mastro_export_utils.get_mass_data's own EDIT-mode branch). The
    # fix is to simply not refresh at all while editing - the last good
    # Viewer result (from before Edit Mode was entered) stays in
    # mastro_export_utils._mass_data_cache and on screen untouched,
    # exactly the same way every OTHER non-selected object's cached data
    # already does.
    if any(obj.mode == 'EDIT' for obj in selected):
        return

    from ..Utils.import_export.mastro_export_utils import clear_mass_data_cache
    selected_names = [obj.name for obj in selected]
    clear_mass_data_cache(selected_names)

    for tree in bpy.data.node_groups:
        if tree.bl_idname == 'MaStroScheduleTreeType':
            tree.execute()

    from ..Nodes.schedule.execution import tag_redraw_node_editors
    tag_redraw_node_editors()


def _sync_active_note(context):
    """Mirror the active sticky note's bpy.data.texts block into text_content.

    The panel textbox writes to text_content (StringProperty) and the update
    callback pushes that back to the text block. This function handles the
    reverse direction: when the user selects a different note, load the text
    block content into text_content so the textbox shows the right text.

    Written via props["text_content"] (item assignment) instead of
    props.text_content = ... to bypass the update callback and avoid an
    infinite write loop.
    """
    global _prev_active_note_name
    space = getattr(context, 'space_data', None)
    if space is None or space.type != 'NODE_EDITOR':
        return
    node_tree = getattr(space, 'edit_tree', None)
    if node_tree is None:
        return
    active = node_tree.nodes.active
    name = active.name if active else None
    # Only act when the active node actually changed.
    if name == _prev_active_note_name:
        return
    _prev_active_note_name = name
    if (active is None
            or not getattr(active, 'select', False)
            or not hasattr(active, 'mastro_sticky_note_props')
            or not active.mastro_sticky_note_props.customNote
            or not active.text):
        return
    current = active.text.as_string()
    props = active.mastro_sticky_note_props
    if props.text_content != current:
        props["text_content"] = current


@persistent
def _on_depsgraph_update(scene, depsgraph):
    guard_light_sources(scene)
    sync_default_camera_set(scene)
    sync_pdf_frames(scene)
    _sync_active_note(bpy.context)
    _check_drawing_objects(bpy.context)
    _refresh_schedules()


def _apply_clip_range_to_open_viewports():
    """Apply the clip range to every VIEW_3D already in Top/Bottom ortho
    when the file is opened.

    monitor_view_rotation's timer (Utils/monitor_view_rotation.py) only
    reacts to a view CHANGE - if a viewport is already in Top/Bottom at
    load time, there's no "change" for it to detect on the very first
    tick (it has nothing yet to compare the current view matrix against),
    so the clip range would otherwise never get applied, and the
    original clip_start/clip_end/view_location.z would never get saved
    for restoring later. This runs once at load instead, covering exactly
    that gap.
    """
    from ..Utils.mastro_levels.clip_range import (
        is_top_bottom_ortho, get_view_side, sync_clip_range_on_view_change,
        apply_clip_to_space,
    )
    scene = bpy.context.scene
    if scene is None:
        return
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            space = area.spaces.active
            region_3d = space.region_3d
            if is_top_bottom_ortho(region_3d):
                # Same two calls _on_view_changed makes on a real view
                # change (monitor_view_rotation.py): rebuild the range if
                # this side has never been set up yet, then push it to
                # clip_start/end - covering both "never initialized" and
                # "already has a range from a previous session" cases.
                sync_clip_range_on_view_change(scene, get_view_side(region_3d))
                apply_clip_to_space(scene, space)


@persistent
def _on_load_post(filepath):
    scene = bpy.context.scene
    if scene:
        sync_default_camera_set(scene)
        sync_pdf_frames(scene)
        _apply_clip_range_to_open_viewports()


def register():
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)
    bpy.app.handlers.load_post.append(_on_load_post)


def unregister():
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
