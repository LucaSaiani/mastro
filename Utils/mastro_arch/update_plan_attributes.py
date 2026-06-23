import bpy

# Floor to floor height used when a plan's bottom level has no level above
# it in mastro_level_list (it is the topmost level, or the only one).
_DEFAULT_FLOOR_TO_FLOOR_HEIGHT = 3.0


def update_plan_attributes(context):
    """Recompute every MaStro plan's level-derived data against the current
    mastro_level_list: its FFL (which drives obj.location.z, see
    plan_drivers.link_all_plan_drivers) and its floor to floor height,
    derived from the level above its bottom level (by current list order -
    not by id, which is not derivable/stored, only used transiently here).

    Called whenever a level's elevation/name changes or the list gets
    re-sorted, since either can change which level ends up "above" a given
    plan and what its floor to floor height should be."""
    level_list = context.scene.mastro_level_list
    if not level_list:
        return

    by_id = {lvl.id: lvl.level for lvl in level_list}
    index_by_id = {lvl.id: i for i, lvl in enumerate(level_list)}

    for obj in bpy.data.objects:
        if obj is None or obj.type != "MESH":
            continue
        if "MaStro plan" not in obj.data:
            continue
        if not obj.mastro_props.mastro_lock_to_level:
            continue

        bottom_level_id = obj.mastro_props.mastro_bottom_level_id
        if bottom_level_id not in by_id:
            continue

        obj.mastro_props.mastro_ffl = by_id[bottom_level_id]

        bottom_index = index_by_id[bottom_level_id]
        if bottom_index == 0:
            obj.mastro_props.mastro_floor_to_floor_height = _DEFAULT_FLOOR_TO_FLOOR_HEIGHT
        else:
            top_level = level_list[bottom_index - 1]
            obj.mastro_props.mastro_floor_to_floor_height = top_level.level - by_id[bottom_level_id]
