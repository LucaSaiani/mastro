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

    # Guards against re-entering shift_clip_range_to_position's update
    # callback (on mastro_clip_range_list_index_<side>) when this write is
    # itself what that callback is in the middle of applying.
    scene[_key("updating_index", side)] = True
    for i, lvl in enumerate(scene.mastro_level_list):
        if lvl.id == ids_in_order[current_position]:
            setattr(scene, f"mastro_clip_range_list_index_{side}", i)
            break
    scene[_key("updating_index", side)] = False


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


def reset_clip_range_for_set_change(scene, side):
    """Rebuild the clip range for `side` against its currently chosen level
    set, instead of leaving stale level ids from a previously chosen set
    in place - which, once compared against the new set's levels (see
    filter_items/in_clip_range), would show an inconsistent selection
    (e.g. the active row pointing at a level that "survived" only by id
    coincidence, not because it's meaningfully selected for the new set).

    Defaults to a single active level (the top of the list for "top", the
    bottom for "bottom" - same convention as the very first time a side is
    used, see sync_clip_range_on_view_change), or to Unlimited's "every
    level" if Unlimited was already on for this side.
    """
    level_set = get_active_clip_range_set(scene, side)
    ids_in_order = [lvl.id for lvl in get_set_levels(scene, level_set)]
    if not ids_in_order:
        return

    default_position = len(ids_in_order) - 1 if side == "bottom" else 0
    count = len(ids_in_order) if is_clip_range_unlimited(scene, side) else 1
    _set_clip_range_from_current(scene, side, ids_in_order, default_position, count)


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


def set_active_level_by_index(scene, side, level_list_index):
    """Make the level at mastro_level_list[level_list_index] the active
    one for `side`, keeping the same count - i.e. clicking a row in the
    clip-range UIList behaves like shift_clip_range, just jumping straight
    to the clicked position instead of moving by ±1 step. Works the same
    whether Unlimited is on or off (count is whatever it currently is in
    either case).

    No-op (returns False) if called while _set_clip_range_from_current is
    itself in the middle of writing mastro_clip_range_list_index_<side> -
    see its "updating_index" guard - to avoid re-entering this from that
    write's own update callback.
    """
    if scene.get(_key("updating_index", side)):
        return False

    if not (0 <= level_list_index < len(scene.mastro_level_list)):
        return False
    clicked_id = scene.mastro_level_list[level_list_index].id

    level_set = get_active_clip_range_set(scene, side)
    ids_in_order = [lvl.id for lvl in get_set_levels(scene, level_set)]
    if clicked_id not in ids_in_order:
        return False
    new_position = ids_in_order.index(clicked_id)

    current = scene.get(_key("level_ids", side), [])
    positions = [ids_in_order.index(lid) for lid in current if lid in ids_in_order]
    if positions:
        lo, hi = min(positions), max(positions)
        count = scene.get(_key("count", side), hi - lo + 1)
    else:
        count = 1

    _set_clip_range_from_current(scene, side, ids_in_order, new_position, count)
    return True


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


# Original clip_start/clip_end/view_location.z, saved per-region (keyed by
# region_3d.as_pointer()) the first time apply_clip_to_space overrides them,
# so leaving Top/Bottom can restore exactly what the user had before -
# rather than leaving the override in place once the user rotates away.
# Module-level cache, not Scene data: this is purely about this Blender
# session's viewport state, not something that should be saved in the
# .blend file or shared between scenes.
_saved_clip_state = {}


def _save_original_clip_state(space, region_3d):
    key = region_3d.as_pointer()
    if key not in _saved_clip_state:
        _saved_clip_state[key] = (space.clip_start, space.clip_end, region_3d.view_location.z)


def restore_original_clip_state(space, region_3d):
    """Restore clip_start/clip_end/view_location.z to what they were
    before apply_clip_to_space first overrode them for this region, then
    forget the saved state (so a later re-entry into Top/Bottom saves a
    fresh "original" rather than restoring a stale one)."""
    key = region_3d.as_pointer()
    saved = _saved_clip_state.pop(key, None)
    if saved is None:
        return
    clip_start, clip_end, view_location_z = saved
    space.clip_start = clip_start
    space.clip_end = clip_end
    region_3d.view_location.z = view_location_z


def forget_clip_state(region_keys):
    """Drop saved-original-clip entries for regions that no longer exist
    (closed area/window) - without this, a region closed while its
    Top/Bottom override was still active would leave a permanently
    orphaned entry in _saved_clip_state."""
    for key in list(_saved_clip_state):
        if key not in region_keys:
            del _saved_clip_state[key]


def apply_clip_to_space(scene, space):
    """Push the current clip-range selection's elevation span to a given
    VIEW_3D space, using whichever side (top/bottom) matches that space's
    own view direction.

    IMPORTANT: in orthographic mode Blender's actual near/far clip planes
    do NOT come from clip_start/clip_end the way they do in perspective.
    Per BKE_camera_params_from_view3d (source/blender/blenkernel/intern/
    camera.cc): for RV3D_ORTHO, clip_start is discarded entirely and the
    effective near/far are computed as a *symmetric* range around the
    view's eye point:
        clip_end_eff   = clip_end * 0.5
        clip_start_eff = -clip_end_eff
    i.e. the visible Z-slab is always centered on the eye point, with
    clip_end controlling its total thickness. There is no way to get an
    asymmetric near/far pair without moving the eye point itself.

    The eye point equals view_location exactly in orthographic mode
    (verified empirically: eye.z - view_location.z == 0.0 for both Top
    and Bottom ortho, regardless of view_distance - unlike perspective
    mode, where the eye sits view_distance away from the pivot). So
    moving the eye point along Z is simply writing region_3d.view_location.z
    directly - which, for an orthographic Top/Bottom view, does NOT
    change anything on screen in X/Y (the framing/pan/zoom is untouched):
    it only changes which world-Z slab is inside the clip range.

    To make [near, far] (world Z, near < far) the visible slab:
        clip_end = far - near
        view_location.z = (near + far) / 2

    Before that, the end of the selection closest to the camera is pushed
    out by the "Cutting Plane Height" preference (default 1.2m, the
    standard architectural section height above a floor/below a ceiling):
    the drawing sits AT the active level's elevation, so showing exactly
    up to that elevation and no further would clip the drawing itself
    away. This applies regardless of how many levels are selected - only
    the camera-facing end moves; the far end stays exactly at its level's
    elevation.
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
    near, far = span

    _save_original_clip_state(space, region_3d)

    from ..mastro_preferences.get_preferences import get_prefs
    cutting_plane_height = get_prefs().clip_range_cutting_plane_height
    if side == "bottom":
        near -= cutting_plane_height  # near (lowest elevation) faces the camera
    else:
        far += cutting_plane_height  # far (highest elevation) faces the camera

    region_3d.view_location.z = (near + far) / 2.0
    space.clip_end = max(1e-5, far - near)


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
        # Nothing has ever been selected for this side yet (e.g. the very
        # first time a Top or Bottom viewport is opened) - default to a
        # single active level instead of leaving the range empty, which
        # would skip writing view_location.z/clip_end entirely and leave
        # the viewport showing no clip range at all (see get_view_side's
        # active-level convention: lo for "top", hi for "bottom").
        default_position = 0 if side != "bottom" else len(ids_in_order) - 1
        _set_clip_range_from_current(scene, side, ids_in_order, default_position, 1)
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
