import bpy
from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       StringProperty,
                       CollectionProperty,
                       BoolProperty,
)


def update_level_list(self, context):
    """Keep the level list sorted by descending level, then by name, then
    refresh every MaStro plan's level-derived data (FFL, floor to floor
    height) - either field can change which level ends up "above" a given
    plan and what its floor to floor height should be.

    Skipped while a batch operation (new_item, batch_add) is writing
    several fields/items in sequence; those operators call
    sort_level_list() (and the plan refresh) once themselves after all
    writes are done.
    """
    if context.scene.get("mastro_level_list_batch_update"):
        return
    from ...Utils.mastro_levels.sort_level_list import sort_level_list
    from ...Utils.update_attributes import update_all_mastro_plans_level
    sort_level_list(context.scene)
    update_all_mastro_plans_level(context)


class mastro_CL_level_set_item(PropertyGroup):
    """Reference to a mastro_level_list entry, by id, that belongs to a set."""
    level_id: IntProperty(name="Level Id", default=0)


class mastro_CL_level_set(PropertyGroup):
    """A named group of levels.

    Set id 0 is the default "All Levels" set: its members are not stored
    here but derived live from mastro_level_list (see
    PROPERTIES_UL_Level_Set_Members), so it always reflects every level
    that currently exists and cannot be edited or removed.
    """
    id: IntProperty(name="Id", default=0)
    name: StringProperty(name="Name", default="Level Set")
    levels: CollectionProperty(type=mastro_CL_level_set_item)


def _get_active_level_set(context):
    scene = context.scene
    level_sets = scene.mastro_level_set_list
    idx = scene.mastro_level_set_list_index
    return level_sets[idx] if 0 <= idx < len(level_sets) else None


def _get_in_active_set(self):
    # Blender's BoolProperty get/set callbacks only receive self, never
    # context, so the active scene must be read from bpy.context here.
    context = bpy.context
    active_set = _get_active_level_set(context)
    if active_set is None:
        return False
    # The "All Levels" set (id 0) always contains every level.
    if active_set.id == 0:
        return True
    return any(el.level_id == self.id for el in active_set.levels)


def _set_in_active_set(self, value):
    context = bpy.context
    active_set = _get_active_level_set(context)
    # Membership of the virtual "All Levels" set cannot be edited.
    if active_set is None or active_set.id == 0:
        return

    for i, el in enumerate(active_set.levels):
        if el.level_id == self.id:
            if not value:
                active_set.levels.remove(i)
            return
    if value:
        active_set.levels.add().level_id = self.id


def _get_active_clip_range_side(context):
    """"top" or "bottom" matching the active viewport, or None if it isn't
    a Top/Bottom ortho view (e.g. the UIList is being drawn somewhere
    else, like a popup, where there's no clip range to show/edit)."""
    from ...Utils.mastro_levels.clip_range import is_top_bottom_ortho, get_view_side
    space = getattr(context, "space_data", None)
    if space is None or space.type != 'VIEW_3D' or not is_top_bottom_ortho(space.region_3d):
        return None
    return get_view_side(space.region_3d)


def _get_in_clip_range(self):
    side = _get_active_clip_range_side(bpy.context)
    if side is None:
        return False
    scene = bpy.context.scene
    return self.id in scene.get(f"mastro_clip_range_level_ids_{side}", [])


def _set_in_clip_range(self, value):
    """Toggling a level's clip-range checkbox always leaves a single,
    non-empty, contiguous range selected.

    Levels are shown in mastro_level_list order (already sorted by
    descending level), so "contiguous" means contiguous list indices, not
    contiguous elevations. After applying the requested toggle, the
    selection is collapsed to [min(selected_index), max(selected_index)] -
    so clicking anywhere between the current extremes, or outside them,
    grows or shrinks the range from the correct end, and clicking the only
    remaining selected level is a no-op (can't empty the range). The
    resulting elevation range is then pushed to the active 3D viewport's
    clip start/end (see update_clip_from_selection).
    """
    from ...Utils.mastro_levels.clip_range import apply_clip_range_toggle, update_clip_from_selection
    context = bpy.context
    side = _get_active_clip_range_side(context)
    if side is None:
        return
    apply_clip_range_toggle(context.scene, side, self.id, value)
    # Writes region_3d.view_location.z (see apply_clip_to_space), which -
    # unlike a Scene/ID property change - doesn't auto-redraw the viewport.
    update_clip_from_selection(context)
    if context.screen is not None:
        for area in context.screen.areas:
            area.tag_redraw()


class mastro_CL_level_list(PropertyGroup):
    """One project level, defined by its elevation.

    id 0 is the default "AOD" (ground/datum) level created by init_lists and
    can never be renamed; see PROPERTIES_UL_Level for where that is enforced.
    Levels in general can never be removed (no remove operator exists, like
    Block/Typology), to avoid breaking references to them elsewhere.
    """
    id: IntProperty(
        name="Id",
        description="Level id",
        default=0,
    )
    name: StringProperty(
        name="Name",
        description="The name of the level",
        default="Level",
        update=update_level_list,
    )
    level: FloatProperty(
        name="Level",
        description="Elevation of the level",
        # precision=5 so sub-millimetre elevations stay visible in the
        # compact UIList row, where Blender would otherwise round the
        # displayed value more aggressively than the stored precision.
        precision=5,
        subtype="DISTANCE",
        update=update_level_list,
    )
    # Backed by the active level set's `levels` collection (see get/set
    # above), not stored data. Exposing membership as a real toggle prop
    # (rather than an operator button) lets Blender's native click-drag
    # over multiple UIList rows assign/unassign several levels in one
    # gesture, the same way drag-toggling works on modifier/layer icons.
    in_active_set: BoolProperty(
        name="In Active Set",
        get=_get_in_active_set,
        set=_set_in_active_set,
    )
    # Backed by scene["mastro_clip_range_level_ids_top"/"_bottom"] (per the
    # active viewport's side - see _get_active_clip_range_side), not stored
    # as a real property, so it can be a plain id list shared across every
    # level without a parallel BoolProperty per item to keep in sync.
    in_clip_range: BoolProperty(
        name="In Clip Range",
        get=_get_in_clip_range,
        set=_set_in_clip_range,
    )
