UNLIMITED_CLIP_DISTANCE = 1000.0  # 1 km, used for the "Unlimited" clip end/start

_level_set_enum_cache = {}


def get_level_set_enum_items(scene, context):
    """EnumProperty items callback for picking a level set, in list order
    (not alphabetical, so "All Levels" stays first).

    The list is cached at module level so Python doesn't garbage-collect
    the label/description strings while Blender still holds raw C
    pointers to them (see feedback_blender_bmesh_gotchas memory, point 3).
    """
    items = [
        (str(level_set.id), level_set.name, f"Id. {level_set.id} - {level_set.name}")
        for level_set in scene.mastro_level_set_list
    ]
    _level_set_enum_cache["items"] = items
    return items


def get_set_levels(scene, level_set):
    """Levels belonging to level_set, in mastro_level_list order (already
    sorted by descending level - see sort_level_list)."""
    if level_set is None:
        return []
    if level_set.id == 0:
        return list(scene.mastro_level_list)
    member_ids = {el.level_id for el in level_set.levels}
    return [lvl for lvl in scene.mastro_level_list if lvl.id in member_ids]


def get_active_clip_range_set(scene):
    """The level set chosen for clip-range purposes (mastro_clip_range_set_id),
    independent from the Sets panel's own mastro_level_set_list_index.

    Reads the property itself (not scene.get(), which only sees a value
    once the user has explicitly changed it) so the EnumProperty's default
    - the first item, "All Levels" - is picked up correctly on first use.
    """
    if not scene.mastro_level_set_list:
        return None
    try:
        set_id = int(scene.mastro_clip_range_set_id)
    except (TypeError, ValueError):
        return None
    for level_set in scene.mastro_level_set_list:
        if level_set.id == set_id:
            return level_set
    return None


def _set_clip_range_from_current(scene, ids_in_order, current_position, count, is_bottom):
    """Build the clip range from a current/active position plus a count of
    levels, extending towards the bottom of the list (lower elevations)
    for Top view, or towards the top of the list (higher elevations) for
    Bottom view - then store it and update mastro_clip_range_list_index to
    current_position.

    This is the single source of truth for the range: there's no separate
    "shrink/regrow" logic. The range is always exactly [current_position,
    current_position + count - 1] (Top) or [current_position - count + 1,
    current_position] (Bottom), truncated to however many levels actually
    exist on that side - so it shrinks/grows for free whenever
    current_position or count change, with no special-casing.
    """
    last_index = len(ids_in_order) - 1
    current_position = max(0, min(current_position, last_index))

    if is_bottom:
        lo = max(0, current_position - count + 1)
        hi = current_position
    else:
        lo = current_position
        hi = min(last_index, current_position + count - 1)

    scene["mastro_clip_range_level_ids"] = ids_in_order[lo:hi + 1]
    scene["mastro_clip_range_count"] = count

    for i, lvl in enumerate(scene.mastro_level_list):
        if lvl.id == ids_in_order[current_position]:
            scene.mastro_clip_range_list_index = i
            break


def apply_clip_range_toggle(scene, level_id, value, is_bottom=False):
    """Toggle level_id's membership in the clip range, then collapse the
    selection to a single contiguous block of list-indices spanning every
    currently-selected level (see in_clip_range's docstring for why).

    Updates mastro_clip_range_count to the resulting number of levels, so
    future arrow-key shifts (see shift_clip_range) keep using this new
    count instead of whatever it was before this manual edit.

    No-op while Unlimited is active: the selection is then driven entirely
    by the active level and the level-list bounds, not by individual
    checkboxes (see toggle_unlimited_clip_range and
    PROPERTIES_UL_Clip_Range_Levels, which disables the checkboxes too).
    """
    if is_clip_range_unlimited(scene):
        return

    level_set = get_active_clip_range_set(scene)
    levels = get_set_levels(scene, level_set)
    ids_in_order = [lvl.id for lvl in levels]
    if level_id not in ids_in_order:
        return

    current = set(scene.get("mastro_clip_range_level_ids", []))
    if value:
        current.add(level_id)
    else:
        # Never allow emptying the range: ignore the toggle if it was the
        # only level selected.
        if current == {level_id}:
            return
        current.discard(level_id)

    selected_positions = [i for i, lid in enumerate(ids_in_order) if lid in current]
    if not selected_positions:
        selected_positions = [ids_in_order.index(level_id)]

    lo, hi = min(selected_positions), max(selected_positions)
    current_position = hi if is_bottom else lo
    _set_clip_range_from_current(scene, ids_in_order, current_position, hi - lo + 1, is_bottom)


def shift_clip_range(scene, steps, is_bottom=False):
    """Move the active level by `steps` list-positions, then rebuild the
    range as [active, active + count - 1] (Top) or [active - count + 1,
    active] (Bottom) using the level count from mastro_clip_range_count
    (set by the last manual toggle, see apply_clip_range_toggle) -
    truncated for free at whichever end runs out of levels.
    """
    level_set = get_active_clip_range_set(scene)
    levels = get_set_levels(scene, level_set)
    ids_in_order = [lvl.id for lvl in levels]
    if not ids_in_order:
        return

    current = scene.get("mastro_clip_range_level_ids", [])
    positions = [ids_in_order.index(lid) for lid in current if lid in ids_in_order]
    if not positions:
        return

    lo, hi = min(positions), max(positions)
    current_position = hi if is_bottom else lo
    count = scene.get("mastro_clip_range_count", hi - lo + 1)

    new_position = current_position + steps
    _set_clip_range_from_current(scene, ids_in_order, new_position, count, is_bottom)


def get_clip_range_elevations(scene):
    """(min_level, max_level) elevation of the current clip-range
    selection, or None if nothing is selected yet."""
    ids = scene.get("mastro_clip_range_level_ids", [])
    if not ids:
        return None
    by_id = {lvl.id: lvl.level for lvl in scene.mastro_level_list}
    elevations = [by_id[lid] for lid in ids if lid in by_id]
    if not elevations:
        return None
    return min(elevations), max(elevations)


def _view_forward_z(region_3d):
    """Z component of the view's forward direction (the direction the
    camera looks along), in world space.

    Computed from view_matrix instead of comparing view_rotation against
    hardcoded quaternions: view_matrix's third row is the view-space Z
    axis expressed in world space, and Blender's view convention has the
    camera looking down its own -Z, so this row's world-space Z gives a
    value of -1 for Top (looking straight down -Z) and +1 for Bottom
    (looking straight up +Z) regardless of the exact quaternion Blender
    happens to store for those views.
    """
    return -region_3d.view_matrix[2][2]


def is_top_bottom_ortho(region_3d):
    """True if region_3d is an orthographic Top or Bottom view (looking
    straight down or up the world Z axis), with some tolerance for
    numerical drift after repeated view nudges."""
    if region_3d is None or region_3d.view_perspective != 'ORTHO':
        return False
    return abs(abs(_view_forward_z(region_3d)) - 1.0) < 1e-4


def is_bottom_ortho(region_3d):
    if region_3d is None:
        return False
    return _view_forward_z(region_3d) > 0


def _camera_world_z(region_3d):
    """World-space Z of the virtual ortho camera position.

    clip_start/clip_end are distances measured from this point along the
    view direction, not absolute world Z - and Blender requires
    clip_start > 0, so an elevation of 0 or negative (e.g. a basement
    level) cannot be written directly. view_matrix's inverse translation
    is the camera's world-space position; for Top/Bottom views only its Z
    component matters since the view direction is the world Z axis.
    """
    return region_3d.view_matrix.inverted().translation.z


def _elevation_to_clip_distance(region_3d, elevation):
    """Distance from the virtual ortho camera to a given world-Z
    elevation, along the view direction (always positive for any
    elevation the camera is actually looking towards)."""
    camera_z = _camera_world_z(region_3d)
    if is_bottom_ortho(region_3d):
        return elevation - camera_z  # camera below, looking up +Z
    return camera_z - elevation  # camera above, looking down -Z


def update_clip_from_selection(context):
    """Push the current clip-range selection's elevation span to the
    active viewport's clip start/end.

    clip_start/clip_end live on SpaceView3D (the "Clip Start"/"Clip End"
    fields in the View panel), not on RegionView3D, and are distances from
    the virtual ortho camera (see _elevation_to_clip_distance) rather than
    absolute elevations - the near side of the range (the level closest to
    the camera) is always clip_start, the far side clip_end.
    """
    space = getattr(context, "space_data", None)
    if space is None or space.type != 'VIEW_3D':
        return
    region_3d = space.region_3d
    if not is_top_bottom_ortho(region_3d):
        return

    span = get_clip_range_elevations(context.scene)
    if span is None:
        return
    lo, hi = span

    # Top: camera above, hi (closer to camera) is the near side. Bottom:
    # camera below, lo is the near side - matches _elevation_to_clip_distance.
    near, far = (lo, hi) if is_bottom_ortho(region_3d) else (hi, lo)
    space.clip_start = max(1e-5, _elevation_to_clip_distance(region_3d, near))
    space.clip_end = max(space.clip_start + 1e-5, _elevation_to_clip_distance(region_3d, far))


def sync_clip_range_on_view_change(scene, region_3d):
    """Rebuild the clip range when the view has just switched between Top
    and Bottom ortho.

    Only safe to call from a context where writing to Scene is allowed
    (e.g. a timer callback) - NOT from a Panel.draw(), where Blender
    raises AttributeError on any ID write. See monitor_view_rotation.py,
    which calls this once per tick after detecting the view matrix changed.

    The active level itself never changes when the view flips - it's read
    straight from mastro_clip_range_list_index, the single source of
    truth for "which level is active" - only the direction the count
    extends in does (forward for Top, backward for Bottom; see
    _set_clip_range_from_current). Re-applying the same active level and
    count with the new is_bottom alone produces the right range.

    No-op once mastro_clip_range_last_is_bottom already matches the
    current view, so repeated calls while the view doesn't change are cheap.
    """
    is_bottom = is_bottom_ortho(region_3d)
    if scene.get("mastro_clip_range_last_is_bottom") == is_bottom:
        return
    scene["mastro_clip_range_last_is_bottom"] = is_bottom

    level_set = get_active_clip_range_set(scene)
    levels = get_set_levels(scene, level_set)
    ids_in_order = [lvl.id for lvl in levels]
    if not ids_in_order:
        return

    current = scene.get("mastro_clip_range_level_ids", [])
    positions = [ids_in_order.index(lid) for lid in current if lid in ids_in_order]
    if not positions:
        return

    index = scene.mastro_clip_range_list_index
    if not (0 <= index < len(scene.mastro_level_list)):
        return
    active_id = scene.mastro_level_list[index].id
    if active_id not in ids_in_order:
        return
    current_position = ids_in_order.index(active_id)

    lo, hi = min(positions), max(positions)
    count = scene.get("mastro_clip_range_count", hi - lo + 1)

    _set_clip_range_from_current(scene, ids_in_order, current_position, count, is_bottom)


def is_clip_range_unlimited(scene):
    return bool(scene.get("mastro_clip_range_unlimited", False))


def toggle_unlimited_clip_range(scene, is_bottom):
    """Toggle "Unlimited": extends the clip range from the active level to
    whichever end of the set's level list is on the far side (top for
    Bottom view, bottom for Top view), covering every level in between.

    The count in effect before toggling on is remembered
    (mastro_clip_range_saved_count) and restored when toggling back off,
    so Unlimited behaves as a persistent override rather than a one-shot
    action - re-pressing it returns to exactly the previous selection.
    """
    level_set = get_active_clip_range_set(scene)
    levels = get_set_levels(scene, level_set)
    ids_in_order = [lvl.id for lvl in levels]
    if not ids_in_order:
        return

    current = scene.get("mastro_clip_range_level_ids", [])
    positions = [ids_in_order.index(lid) for lid in current if lid in ids_in_order]
    if not positions:
        return

    lo, hi = min(positions), max(positions)
    current_position = hi if is_bottom else lo

    now_unlimited = not is_clip_range_unlimited(scene)
    scene["mastro_clip_range_unlimited"] = now_unlimited

    if now_unlimited:
        scene["mastro_clip_range_saved_count"] = hi - lo + 1
        count = len(ids_in_order)  # more than enough; truncated for free
    else:
        count = scene.get("mastro_clip_range_saved_count", hi - lo + 1)

    _set_clip_range_from_current(scene, ids_in_order, current_position, count, is_bottom)
