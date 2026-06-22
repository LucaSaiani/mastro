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


# All clip-range state is duplicated per side ("top" or "bottom"), so a Top
# viewport and a Bottom viewport open at the same time each keep their own
# chosen set, range and active level instead of fighting over one shared
# state - see properties_levels.py for the two real registered properties
# (mastro_clip_range_set_id_<side>, mastro_clip_range_list_index_<side>)
# and _key() below for the rest, stored as plain Scene id-properties.
def _key(name, side):
    return f"mastro_clip_range_{name}_{side}"


def get_active_clip_range_set(scene, side):
    """The level set chosen for clip-range purposes on the given side
    (mastro_clip_range_set_id_<side>), independent from the Sets panel's
    own mastro_level_set_list_index.

    Reads the property itself (not scene.get(), which only sees a value
    once the user has explicitly changed it) so the EnumProperty's default
    - the first item, "All Levels" - is picked up correctly on first use.
    """
    if not scene.mastro_level_set_list:
        return None
    try:
        set_id = int(getattr(scene, f"mastro_clip_range_set_id_{side}"))
    except (TypeError, ValueError):
        return None
    for level_set in scene.mastro_level_set_list:
        if level_set.id == set_id:
            return level_set
    return None


def _set_clip_range_from_current(scene, side, ids_in_order, current_position, count):
    """Build the clip range from a current/active position plus a count of
    levels, extending towards the bottom of the list (lower elevations)
    for the "top" side, or towards the top of the list (higher elevations)
    for the "bottom" side - then store it and update
    mastro_clip_range_list_index_<side> to current_position.

    This is the single source of truth for the range: there's no separate
    "shrink/regrow" logic. The range is always exactly [current_position,
    current_position + count - 1] ("top") or [current_position - count + 1,
    current_position] ("bottom"), truncated to however many levels actually
    exist on that side - so it shrinks/grows for free whenever
    current_position or count change, with no special-casing.
    """
    last_index = len(ids_in_order) - 1
    current_position = max(0, min(current_position, last_index))

    if side == "bottom":
        lo = max(0, current_position - count + 1)
        hi = current_position
    else:
        lo = current_position
        hi = min(last_index, current_position + count - 1)

    scene[_key("level_ids", side)] = ids_in_order[lo:hi + 1]
    scene[_key("count", side)] = count

    for i, lvl in enumerate(scene.mastro_level_list):
        if lvl.id == ids_in_order[current_position]:
            setattr(scene, f"mastro_clip_range_list_index_{side}", i)
            break


def apply_clip_range_toggle(scene, side, level_id, value):
    """Toggle level_id's membership in the clip range for the given side,
    then collapse the selection to a single contiguous block of
    list-indices spanning every currently-selected level (see
    in_clip_range's docstring for why).

    Updates mastro_clip_range_count_<side> to the resulting number of
    levels, so future arrow-key shifts (see shift_clip_range) keep using
    this new count instead of whatever it was before this manual edit.

    No-op while Unlimited is active on this side: the selection is then
    driven entirely by the active level and the level-list bounds, not by
    individual checkboxes (see toggle_unlimited_clip_range and
    PROPERTIES_UL_Clip_Range_Levels, which disables the checkboxes too).
    """
    if is_clip_range_unlimited(scene, side):
        return

    level_set = get_active_clip_range_set(scene, side)
    levels = get_set_levels(scene, level_set)
    ids_in_order = [lvl.id for lvl in levels]
    if level_id not in ids_in_order:
        return

    current = set(scene.get(_key("level_ids", side), []))
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
    current_position = hi if side == "bottom" else lo
    _set_clip_range_from_current(scene, side, ids_in_order, current_position, hi - lo + 1)


def shift_clip_range(scene, side, steps):
    """Move the active level by `steps` list-positions, then rebuild the
    range as [active, active + count - 1] ("top") or [active - count + 1,
    active] ("bottom") using the level count from
    mastro_clip_range_count_<side> (set by the last manual toggle, see
    apply_clip_range_toggle) - truncated for free at whichever end runs
    out of levels.
    """
    level_set = get_active_clip_range_set(scene, side)
    levels = get_set_levels(scene, level_set)
    ids_in_order = [lvl.id for lvl in levels]
    if not ids_in_order:
        return

    current = scene.get(_key("level_ids", side), [])
    positions = [ids_in_order.index(lid) for lid in current if lid in ids_in_order]
    if not positions:
        return

    lo, hi = min(positions), max(positions)
    current_position = hi if side == "bottom" else lo
    count = scene.get(_key("count", side), hi - lo + 1)

    new_position = current_position + steps
    _set_clip_range_from_current(scene, side, ids_in_order, new_position, count)


def get_clip_range_elevations(scene, side):
    """(min_level, max_level) elevation of the current clip-range
    selection for the given side, or None if nothing is selected yet."""
    ids = scene.get(_key("level_ids", side), [])
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


def get_view_side(region_3d):
    """"top" or "bottom", matching the side-keyed clip-range state. Only
    meaningful when is_top_bottom_ortho(region_3d) is True."""
    return "bottom" if is_bottom_ortho(region_3d) else "top"


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


def apply_clip_to_space(scene, space):
    """Push the current clip-range selection's elevation span to a given
    VIEW_3D space's clip start/end, using whichever side (top/bottom)
    matches that space's own view direction.

    clip_start/clip_end live on SpaceView3D (the "Clip Start"/"Clip End"
    fields in the View panel), not on RegionView3D, and are distances from
    the virtual ortho camera (see _elevation_to_clip_distance) rather than
    absolute elevations - the near side of the range (the level closest to
    the camera) is always clip_start, the far side clip_end.

    Takes space/scene directly rather than a context, so it can be
    applied to any VIEW_3D space found while iterating every window/area
    (see monitor_view_rotation.py), not just whichever one happens to be
    context.space_data.
    """
    if space is None or space.type != 'VIEW_3D':
        return
    region_3d = space.region_3d
    if not is_top_bottom_ortho(region_3d):
        return
    side = get_view_side(region_3d)

    span = get_clip_range_elevations(scene, side)
    if span is None:
        return
    lo, hi = span

    # Top: camera above, hi (closer to camera) is the near side. Bottom:
    # camera below, lo is the near side - matches _elevation_to_clip_distance.
    near, far = (lo, hi) if side == "bottom" else (hi, lo)
    space.clip_start = max(1e-5, _elevation_to_clip_distance(region_3d, near))
    space.clip_end = max(space.clip_start + 1e-5, _elevation_to_clip_distance(region_3d, far))


def update_clip_from_selection(context):
    """Context-based wrapper around apply_clip_to_space, for callers that
    only care about the active viewport (operators, panels)."""
    apply_clip_to_space(getattr(context, "scene", None), getattr(context, "space_data", None))


def is_clip_range_unlimited(scene, side):
    return bool(scene.get(_key("unlimited", side), False))


def toggle_unlimited_clip_range(scene, side):
    """Toggle "Unlimited" for the given side: extends the clip range from
    the active level to whichever end of the set's level list is on the
    far side ("top" of the list for "bottom" view, "bottom" of the list
    for "top" view), covering every level in between.

    The count in effect before toggling on is remembered
    (mastro_clip_range_saved_count_<side>) and restored when toggling back
    off, so Unlimited behaves as a persistent override rather than a
    one-shot action - re-pressing it returns to exactly the previous
    selection.
    """
    level_set = get_active_clip_range_set(scene, side)
    levels = get_set_levels(scene, level_set)
    ids_in_order = [lvl.id for lvl in levels]
    if not ids_in_order:
        return

    current = scene.get(_key("level_ids", side), [])
    positions = [ids_in_order.index(lid) for lid in current if lid in ids_in_order]
    if not positions:
        return

    lo, hi = min(positions), max(positions)
    current_position = hi if side == "bottom" else lo

    now_unlimited = not is_clip_range_unlimited(scene, side)
    scene[_key("unlimited", side)] = now_unlimited

    if now_unlimited:
        scene[_key("saved_count", side)] = hi - lo + 1
        count = len(ids_in_order)  # more than enough; truncated for free
    else:
        count = scene.get(_key("saved_count", side), hi - lo + 1)

    _set_clip_range_from_current(scene, side, ids_in_order, current_position, count)


def sync_clip_range_on_view_change(scene, side):
    """Rebuild the clip range for the given side.

    Called whenever a viewport showing that side has just had its view
    matrix change (see monitor_view_rotation.py) - cheap and safe even if
    nothing relevant actually changed, since each side's state is fully
    independent now (no more cross-side "last is bottom" flag to
    invalidate): this simply re-derives the range from the side's own
    active level and count, which is already correct unless the level set
    or level list itself changed underneath it.

    Only safe to call from a context where writing to Scene is allowed
    (e.g. a timer callback) - NOT from a Panel.draw(), where Blender
    raises AttributeError on any ID write.
    """
    level_set = get_active_clip_range_set(scene, side)
    levels = get_set_levels(scene, level_set)
    ids_in_order = [lvl.id for lvl in levels]
    if not ids_in_order:
        return

    current = scene.get(_key("level_ids", side), [])
    positions = [ids_in_order.index(lid) for lid in current if lid in ids_in_order]
    if not positions:
        return

    index = getattr(scene, f"mastro_clip_range_list_index_{side}")
    if not (0 <= index < len(scene.mastro_level_list)):
        return
    active_id = scene.mastro_level_list[index].id
    if active_id not in ids_in_order:
        return
    current_position = ids_in_order.index(active_id)

    lo, hi = min(positions), max(positions)
    count = scene.get(_key("count", side), hi - lo + 1)

    _set_clip_range_from_current(scene, side, ids_in_order, current_position, count)
